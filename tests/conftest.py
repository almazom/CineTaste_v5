"""
Pytest-bdd configuration for CineTaste integration tests.

This conftest.py provides:
- Gherkin step definitions for feature files
- Shared fixtures for test data
- Pipeline execution helpers
- Contract validation utilities
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import yaml

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
PYTHON = subprocess.list2cmdline([__import__("sys").executable])

# ─────────────────────────────────────────────────────────────────────────────
# Pytest-bdd Configuration
# ─────────────────────────────────────────────────────────────────────────────

pytest_plugins = ["pytest_bdd"]


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "critical: mark test as critical priority (P0)",
    )
    config.addinivalue_line(
        "markers",
        "network: mark test as requiring network connectivity",
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow-running",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="session")
def root_dir() -> Path:
    """Return the project root directory."""
    return ROOT


@pytest.fixture(scope="session")
def fixtures_dir(root_dir: Path) -> Path:
    """Return the test fixtures directory."""
    return root_dir / "tests" / "fixtures"


@pytest.fixture(scope="session")
def sample_data(fixtures_dir: Path) -> Dict[str, Any]:
    """Load sample_data.yaml fixtures."""
    data_path = fixtures_dir / "sample_data.yaml"
    with open(data_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def taste_profile(root_dir: Path) -> Path:
    """Return the path to the default taste profile."""
    return root_dir / "taste" / "profile.yaml"


@pytest.fixture
def fake_t2me_script(temp_dir: Path) -> Path:
    """Create a fake t2me script for dry-run testing."""
    fake_bin = temp_dir / "t2me"
    args_file = temp_dir / "t2me_args.txt"

    fake_bin.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
printf '%s\\n' "$*" > "{args_file}"
cat >/dev/null
echo '{{"status":"ok","result":{{"target":"@test","message":"preview","dry_run":true}}}}'
""",
        encoding="utf-8",
    )
    fake_bin.chmod(0o755)
    return fake_bin


@pytest.fixture
def fake_t2me_with_failure(temp_dir: Path) -> Path:
    """Create a fake t2me script that simulates auth failure."""
    fake_bin = temp_dir / "t2me"

    fake_bin.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
cat >/dev/null
echo '{"status":"error","error":"auth failed","result":{"target":"@test"}}'
""",
        encoding="utf-8",
    )
    fake_bin.chmod(0o755)
    return fake_bin


@pytest.fixture
def pipeline_env(fake_t2me_script: Path) -> Dict[str, str]:
    """Create environment with fake t2me in PATH."""
    env = os.environ.copy()
    fake_bin_dir = str(fake_t2me_script.parent)
    env["PATH"] = f"{fake_bin_dir}:{env.get('PATH', '')}"
    return env


@pytest.fixture
def analysis_result_sample(root_dir: Path) -> Path:
    """Return the path to the sample analysis-result file."""
    return root_dir / "contracts" / "examples" / "analysis-result.sample.json"


@pytest.fixture
def create_test_message(temp_dir: Path) -> Path:
    """Create a test message file for resend testing."""
    message_path = temp_dir / "test-message.txt"
    message_path.write_text(
        """🎬 **Кино на сегодня — Набережные Челны**

**Тестовый фильм** (2026)
Режиссёр: Test Director
⭐ 90/100 — Обязательно к просмотру

🕐 Показ: 19:00
📍 Тестовый кинотеатр

_Тестовое описание для проверки resend._
""",
        encoding="utf-8",
    )
    return message_path


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────


def run_pipeline(
    args: List[str],
    env: Optional[Dict[str, str]] = None,
    cwd: Optional[Path] = None,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """
    Execute the pipeline with given arguments.

    Args:
        args: Command line arguments (e.g., ["--dry-run", "--input", "file.json"])
        env: Environment variables (default: os.environ)
        cwd: Working directory (default: ROOT)
        capture_output: Capture stdout/stderr (default: True)

    Returns:
        CompletedProcess with returncode, stdout, stderr
    """
    cmd = [str(ROOT / "run")] + args
    return subprocess.run(
        cmd,
        capture_output=capture_output,
        text=True,
        cwd=str(cwd or ROOT),
        env=env or os.environ,
    )


def load_json_file(path: Path) -> Dict[str, Any]:
    """Load and parse a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_contract(payload: Dict[str, Any], contract_name: str) -> tuple[bool, List[str]]:
    """
    Validate payload against a contract schema.

    Args:
        payload: JSON payload to validate
        contract_name: Name of the contract (e.g., "send-confirmation")

    Returns:
        Tuple of (is_valid, error_messages)
    """
    import sys

    sys.path.insert(0, str(ROOT / "tools" / "_shared"))
    from validate import validate_against_contract  # noqa: E402

    return validate_against_contract(payload, contract_name)


def get_failed_artifact_dir(before: set[Path]) -> Optional[Path]:
    """
    Find the most recently created failed_* directory.

    Args:
        before: Set of failed_* directories that existed before the test

    Returns:
        Path to the new failed_* directory, or None if not found
    """
    logs_dir = ROOT / "logs"
    if not logs_dir.exists():
        return None

    after = set(logs_dir.glob("failed_*"))
    created = sorted(after - before)
    return created[-1] if created else None


# ─────────────────────────────────────────────────────────────────────────────
# Gherkin Step Definitions (Shared)
# ─────────────────────────────────────────────────────────────────────────────
#
# Note: Full step definitions would be implemented here for pytest-bdd.
# For now, we provide helper fixtures that tests can use directly.
#
# Example usage in test files:
#
#   from pytest_bdd import scenarios, given, when, then
#   scenarios("features/golden_paths.feature")
#
#   @given("the pipeline is configured with taste profile")
#   def pipeline_config(taste_profile):
#       return {"taste": taste_profile}
#
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def pipeline_context(
    root_dir: Path,
    taste_profile: Path,
    temp_dir: Path,
) -> Dict[str, Any]:
    """
    Provide a shared context for pipeline tests.

    Contains:
        - root_dir: Project root
        - taste_profile: Path to taste profile
        - temp_dir: Temporary directory for artifacts
        - TMPDIR: Environment variable for pipeline
        - env: Environment with fake t2me
    """
    return {
        "root_dir": root_dir,
        "taste_profile": taste_profile,
        "temp_dir": temp_dir,
        "TMPDIR": str(temp_dir),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test Data Builders
# ─────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def movie_batch_builder() -> MovieBatchBuilder:
    """Return a builder for movie-batch contract payloads."""
    return MovieBatchBuilder()


class MovieBatchBuilder:
    """Builder for movie-batch contract payloads."""

    def __init__(self):
        self.movies: List[Dict[str, Any]] = []
        self.meta: Dict[str, Any] = {
            "city": "naberezhnie-chelni",
            "date": "2026-03-10",
            "source": "kinoteatr",
        }

    def with_movie(
        self,
        title: str = "Test Movie",
        year: Optional[int] = None,
        director: str = "Test Director",
        genres: Optional[List[str]] = None,
        showtimes: Optional[List[str]] = None,
        cinema: str = "Test Cinema",
    ) -> "MovieBatchBuilder":
        """Add a movie to the batch."""
        movie = {
            "title": title,
            "year": year,
            "director": director,
            "genres": genres or [],
            "showtimes": showtimes or [],
            "cinema": cinema,
        }
        self.movies.append(movie)
        return self

    def with_meta(self, **kwargs: Any) -> "MovieBatchBuilder":
        """Update meta fields."""
        self.meta.update(kwargs)
        return self

    def build(self) -> Dict[str, Any]:
        """Build the movie-batch payload."""
        return {"movies": self.movies, "meta": self.meta}


@pytest.fixture
def analysis_result_builder() -> AnalysisResultBuilder:
    """Return a builder for analysis-result contract payloads."""
    return AnalysisResultBuilder()


class AnalysisResultBuilder:
    """Builder for analysis-result contract payloads."""

    def __init__(self):
        self.analyzed: List[Dict[str, Any]] = []
        self.meta: Dict[str, Any] = {
            "agent": "test",
            "timestamp": "2026-03-10T12:00:00Z",
        }

    def with_movie(
        self,
        title: str = "Test Movie",
        year: Optional[int] = None,
        director: str = "Test Director",
        score: int = 75,
        recommendation: str = "recommended",
        reasoning: str = "Test reasoning",
    ) -> "AnalysisResultBuilder":
        """Add an analyzed movie."""
        movie = {
            "movie": {
                "title": title,
                "year": year,
                "director": director,
            },
            "score": score,
            "recommendation": recommendation,
            "reasoning": reasoning,
        }
        self.analyzed.append(movie)
        return self

    def with_meta(self, **kwargs: Any) -> "AnalysisResultBuilder":
        """Update meta fields."""
        self.meta.update(kwargs)
        return self

    def build(self) -> Dict[str, Any]:
        """Build the analysis-result payload."""
        return {"analyzed": self.analyzed, "meta": self.meta}
