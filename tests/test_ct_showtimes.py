"""
Test ct-showtimes tool contract validation and CLI behavior.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "_shared"))

from validate import validate_against_contract


ROOT = Path(__file__).resolve().parent.parent


def load_showtimes_main():
    path = ROOT / "tools" / "ct-showtimes" / "main.py"
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location("ct_showtimes_main", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TestMovieShowtimesContract:
    def test_sample_valid(self):
        sample_path = ROOT / "contracts" / "examples" / "movie-showtimes.sample.json"
        data = json.loads(sample_path.read_text(encoding="utf-8"))
        is_valid, errors = validate_against_contract(data, "movie-showtimes")
        assert is_valid, f"Validation errors: {errors}"


class TestShowtimesCli:
    def test_ct_showtimes_dry_run_emits_valid_contract(self, tmp_path: Path):
        output_file = tmp_path / "showtimes.json"

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "ct-showtimes" / "main.py"),
                "--url",
                "https://kinoteatr.ru/film/postoronniy-2/naberezhnie-chelni/",
                "--date",
                "2026-03-10",
                "--dry-run",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )

        assert result.returncode == 0, result.stderr
        payload = json.loads(output_file.read_text(encoding="utf-8"))
        is_valid, errors = validate_against_contract(payload, "movie-showtimes")
        assert is_valid, errors
        assert payload["meta"]["showtimes_count"] == len(payload["showtimes"])
        assert payload["meta"]["dry_run"] is True

    def test_ct_showtimes_without_date_uses_local_today(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "ct-showtimes" / "main.py"),
                "--url",
                "https://kinoteatr.ru/film/postoronniy-2/naberezhnie-chelni/",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )

        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        expected = datetime.now().astimezone().strftime("%Y-%m-%d")
        assert payload["date"] == expected

    def test_ct_showtimes_fetch_failure_returns_unavailable_exit(self, monkeypatch, capsys):
        module = load_showtimes_main()

        def boom(movie_url: str, date_value: str):
            raise ConnectionError(f"boom for {movie_url} on {date_value}")

        monkeypatch.setitem(module.SUPPORTED_SOURCES, "kinoteatr", boom)
        monkeypatch.setattr(
            sys,
            "argv",
            [
                "ct-showtimes",
                "--url",
                "https://kinoteatr.ru/film/postoronniy-2/naberezhnie-chelni/",
                "--date",
                "2026-03-10",
            ],
        )

        with pytest.raises(SystemExit) as exc:
            module.main()

        captured = capsys.readouterr()
        assert exc.value.code == module.EXIT_UNAVAILABLE
        assert "Upstream unavailable" in captured.err
