"""
Test ct-schedule tool contract validation and adapter behavior.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "_shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "ct-schedule"))

from validate import validate_against_contract
from adapter_showtimes import (
    dry_run_showtimes,
    fetch_showtimes,
    parse_showtimes_html,
    to_datetime_iso,
)


ROOT = Path(__file__).resolve().parent.parent


class TestScheduleAdapter:
    def test_to_datetime_iso(self):
        assert to_datetime_iso("2026-03-03", "13:40") == "2026-03-03T13:40:00+03:00"

    def test_parse_showtimes_html_extracts_unique_times(self):
        html = "<div>Сеансы: 10:10, 12:40, 10:10, 22:55</div>"
        out = parse_showtimes_html(html, "2026-03-03", booking_url="https://example.com/film")
        assert [item["time"] for item in out] == ["10:10", "12:40", "22:55"]
        assert all(item["booking_url"] == "https://example.com/film" for item in out)

    def test_parse_showtimes_html_prefers_real_seance_blocks(self):
        html = """
        <meta itemprop="uploadDate" content="2026-03-10 03:01:50" />
        <div class="item buy_seance">
          <div class="time">21:10</div>
          <p class="price">от 250 ₽</p>
          <p class="hall"><span>Стандарт</span></p>
        </div>
        """
        out = parse_showtimes_html(html, "2026-03-10", booking_url="https://example.com/film")
        assert out == [
            {
                "time": "21:10",
                "datetime_iso": "2026-03-10T21:10:00+03:00",
                "price": "от 250 ₽",
                "hall": "Стандарт",
                "booking_url": "https://example.com/film",
            }
        ]

    def test_dry_run_showtimes_is_deterministic(self):
        first = dry_run_showtimes("movie-1", "2026-03-03")
        second = dry_run_showtimes("movie-1", "2026-03-03")
        assert first == second
        assert len(first) >= 1
        assert all("datetime_iso" in item for item in first)

    def test_fetch_showtimes_request_error(self, monkeypatch):
        import requests

        def boom(*args, **kwargs):
            raise requests.RequestException("network fail")

        monkeypatch.setattr("adapter_showtimes.requests.get", boom)

        with pytest.raises(ConnectionError):
            fetch_showtimes("https://example.com/film", "2026-03-03")

    def test_fetch_showtimes_success(self, monkeypatch):
        response = SimpleNamespace(
            text="""
            <div class="item buy_seance">
              <div class="time">09:30</div>
              <p class="price">от 300 ₽</p>
              <p class="hall"><span>Стандарт</span></p>
            </div>
            <div class="item buy_seance">
              <div class="time">14:00</div>
              <p class="price">от 450 ₽</p>
              <p class="hall"><span>IMAX</span></p>
            </div>
            """,
            raise_for_status=lambda: None,
        )

        monkeypatch.setattr("adapter_showtimes.requests.get", lambda *a, **k: response)

        out = fetch_showtimes("https://example.com/film", "2026-03-03")
        assert [item["time"] for item in out] == ["09:30", "14:00"]
        assert [item["price"] for item in out] == ["от 300 ₽", "от 450 ₽"]


class TestMovieScheduleContract:
    def test_sample_valid(self):
        sample_path = ROOT / "contracts" / "examples" / "movie-schedule.sample.json"
        data = json.loads(sample_path.read_text(encoding="utf-8"))
        is_valid, errors = validate_against_contract(data, "movie-schedule")
        assert is_valid, f"Validation errors: {errors}"


class TestScheduleCli:
    def test_ct_schedule_dry_run_emits_valid_contract(self, tmp_path: Path):
        input_file = ROOT / "contracts" / "examples" / "movie-batch.sample.json"
        output_file = tmp_path / "scheduled.json"

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "ct-schedule" / "main.py"),
                "--input",
                str(input_file),
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
        is_valid, errors = validate_against_contract(payload, "movie-schedule")
        assert is_valid, errors
        assert payload["meta"]["movies_total"] == len(payload["movies"])
