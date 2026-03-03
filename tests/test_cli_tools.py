"""
Black-box CLI tests for CineTaste toolchain.

These tests validate that each CLI tool:
1) exposes a working `--help`,
2) surfaces declared MANIFEST flags in help text,
3) handles key success/error paths with stable exit codes,
4) emits JSON payloads matching contract schemas.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = ROOT / "tools"

sys.path.insert(0, str(TOOLS_DIR / "_shared"))
from validate import validate_against_contract  # noqa: E402


CT_TOOLS = ("ct-fetch", "ct-schedule", "ct-analyze", "ct-filter", "ct-format")


def run_tool(tool: str, args: list[str]) -> subprocess.CompletedProcess[str]:
    script = ROOT / tool
    return subprocess.run(
        [str(script), *args],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )


def manifest_flags(tool: str) -> list[str]:
    manifest_path = TOOLS_DIR / tool / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return [flag["name"] for flag in manifest["cli"]["flags"]]


class TestCliHelp:
    @pytest.mark.parametrize("tool", CT_TOOLS)
    def test_help_contains_manifest_flags(self, tool: str):
        result = run_tool(tool, ["--help"])
        assert result.returncode == 0, result.stderr
        for flag in manifest_flags(tool):
            assert flag in result.stdout

    def test_t2me_help_available(self):
        if shutil.which("t2me") is None:
            pytest.skip("t2me is not installed in PATH")

        result = subprocess.run(
            ["t2me", "--help"],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        assert result.returncode == 0
        assert "send" in result.stdout
        assert "status" in result.stdout


class TestCliRequiredArgs:
    def test_ct_fetch_requires_city(self):
        result = run_tool("ct-fetch", [])
        assert result.returncode == 2
        assert "--city" in result.stderr

    def test_ct_analyze_requires_taste(self, tmp_path: Path):
        sample = ROOT / "contracts" / "examples" / "movie-schedule.sample.json"
        result = run_tool("ct-analyze", ["--input", str(sample)])
        assert result.returncode == 2
        assert "--taste" in result.stderr

    def test_ct_schedule_requires_input(self):
        result = run_tool("ct-schedule", [])
        assert result.returncode == 2
        assert "--input" in result.stderr

    def test_ct_filter_requires_input(self):
        result = run_tool("ct-filter", [])
        assert result.returncode == 2
        assert "--input" in result.stderr

    def test_ct_format_requires_input(self):
        result = run_tool("ct-format", [])
        assert result.returncode == 2
        assert "--input" in result.stderr


class TestCliSuccessPaths:
    def test_ct_fetch_dry_run_emits_movie_batch_contract(self, tmp_path: Path):
        output_path = tmp_path / "movies.json"
        result = run_tool(
            "ct-fetch",
            [
                "--city",
                "naberezhnie-chelni",
                "--dry-run",
                "--output",
                str(output_path),
            ],
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        is_valid, errors = validate_against_contract(payload, "movie-batch")
        assert is_valid, errors

    def test_ct_analyze_dry_run_emits_analysis_result_contract(self, tmp_path: Path):
        sample = ROOT / "contracts" / "examples" / "movie-schedule.sample.json"
        taste = ROOT / "taste" / "profile.yaml"
        output_path = tmp_path / "analyzed.json"
        result = run_tool(
            "ct-analyze",
            [
                "--input",
                str(sample),
                "--taste",
                str(taste),
                "--dry-run",
                "--output",
                str(output_path),
            ],
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        is_valid, errors = validate_against_contract(payload, "analysis-result")
        assert is_valid, errors

    def test_ct_schedule_dry_run_emits_movie_schedule_contract(self, tmp_path: Path):
        sample = ROOT / "contracts" / "examples" / "movie-batch.sample.json"
        output_path = tmp_path / "scheduled.json"
        result = run_tool(
            "ct-schedule",
            [
                "--input",
                str(sample),
                "--dry-run",
                "--output",
                str(output_path),
            ],
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        is_valid, errors = validate_against_contract(payload, "movie-schedule")
        assert is_valid, errors

    def test_ct_filter_emits_filter_result_contract(self, tmp_path: Path):
        sample = ROOT / "contracts" / "examples" / "analysis-result.sample.json"
        output_path = tmp_path / "filtered.json"
        result = run_tool(
            "ct-filter",
            [
                "--input",
                str(sample),
                "--recommendation",
                "must_see,recommended",
                "--output",
                str(output_path),
            ],
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        is_valid, errors = validate_against_contract(payload, "filter-result")
        assert is_valid, errors

    def test_ct_format_emits_message_text_contract(self, tmp_path: Path):
        sample = ROOT / "contracts" / "examples" / "filter-result.sample.json"
        output_path = tmp_path / "message.json"
        result = run_tool(
            "ct-format",
            [
                "--input",
                str(sample),
                "--template",
                "telegram",
                "--city",
                "Набережные Челны",
                "--output",
                str(output_path),
            ],
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        is_valid, errors = validate_against_contract(payload, "message-text")
        assert is_valid, errors


class TestCliErrorPaths:
    def test_ct_fetch_unknown_source_returns_invalid_args(self):
        result = run_tool(
            "ct-fetch",
            [
                "--city",
                "naberezhnie-chelni",
                "--source",
                "unknown-source",
                "--dry-run",
            ],
        )
        assert result.returncode == 2
        assert "Unknown source" in result.stderr

    def test_ct_analyze_missing_taste_file_returns_invalid_args(self, tmp_path: Path):
        sample = ROOT / "contracts" / "examples" / "movie-schedule.sample.json"
        missing_taste = tmp_path / "missing.yaml"
        result = run_tool(
            "ct-analyze",
            [
                "--input",
                str(sample),
                "--taste",
                str(missing_taste),
                "--dry-run",
            ],
        )
        assert result.returncode == 2
        assert "Taste profile not found" in result.stderr

    def test_ct_analyze_invalid_agent_returns_invalid_args(self):
        sample = ROOT / "contracts" / "examples" / "movie-schedule.sample.json"
        taste = ROOT / "taste" / "profile.yaml"
        result = run_tool(
            "ct-analyze",
            [
                "--input",
                str(sample),
                "--taste",
                str(taste),
                "--agent",
                "invalid-agent",
            ],
        )
        assert result.returncode == 2

    def test_ct_schedule_invalid_date_returns_invalid_args(self):
        sample = ROOT / "contracts" / "examples" / "movie-batch.sample.json"
        result = run_tool(
            "ct-schedule",
            [
                "--input",
                str(sample),
                "--date",
                "invalid-date",
                "--dry-run",
            ],
        )
        assert result.returncode == 2
        assert "--date must be YYYY-MM-DD" in result.stderr

    def test_ct_format_unknown_template_returns_invalid_args(self):
        sample = ROOT / "contracts" / "examples" / "filter-result.sample.json"
        result = run_tool(
            "ct-format",
            [
                "--input",
                str(sample),
                "--template",
                "unknown-template",
            ],
        )
        assert result.returncode == 2
        assert "Unknown template" in result.stderr
