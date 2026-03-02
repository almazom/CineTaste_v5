"""
Test ct-format tool contract validation.
"""

import json
import pytest
import sys
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "_shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "ct-format"))

from validate import validate_against_contract
from adapter_telegram import render_message, render_movie_line, render_detailed


class TestTelegramRenderer:
    """Test Telegram markdown rendering."""

    def test_render_message_basic(self):
        """Should render basic message."""
        filtered = [
            {
                "movie": {"id": "1", "title": "Test Movie", "url": "https://example.com"},
                "relevance_score": 85,
                "recommendation": "recommended"
            }
        ]
        message = render_message(filtered, "Test City")

        assert "Test Movie" in message
        assert "Test City" in message

    def test_render_message_must_see(self):
        """Should render must_see section."""
        filtered = [
            {
                "movie": {"id": "1", "title": "Must See", "url": "https://example.com"},
                "relevance_score": 95,
                "recommendation": "must_see"
            }
        ]
        message = render_message(filtered, "Test City")

        assert "ОБЯЗАТЕЛЬНО" in message

    def test_render_movie_line(self):
        """Should render movie line with markdown."""
        item = {
            "movie": {"id": "1", "title": "Test", "url": "https://example.com"},
            "relevance_score": 85,
            "recommendation": "recommended"
        }
        line = render_movie_line(item, 1)

        assert "Test" in line
        assert "85%" in line
        assert "https://example.com" in line

    def test_render_movie_line_without_url(self):
        """Should render plain title when URL is missing."""
        item = {
            "movie": {"id": "1", "title": "Test"},
            "relevance_score": 70,
            "recommendation": "recommended"
        }
        line = render_movie_line(item, 2)
        assert "Test" in line
        assert "https://" not in line

    def test_render_movie_line_over_20_index(self):
        """Should fallback to numeric prefix for large indexes."""
        item = {
            "movie": {"id": "1", "title": "Test"},
            "relevance_score": 70,
            "recommendation": "recommended"
        }
        line = render_movie_line(item, 21)
        assert line.startswith("21.")

    def test_render_message_with_explicit_date(self):
        """Should use provided date instead of current date."""
        filtered = []
        message = render_message(filtered, "Test City", date="10.03.2026")
        assert "10.03.2026" in message

    def test_render_detailed(self):
        """Detailed renderer should include optional fields."""
        item = {
            "movie": {
                "id": "1",
                "title": "Detailed Movie",
                "director": "Director",
                "genres": ["drama"]
            },
            "relevance_score": 90,
            "reasoning": "Strong match"
        }
        text = render_detailed(item)
        assert "Detailed Movie" in text
        assert "Director" in text
        assert "Strong match" in text

    def test_render_empty_filtered(self):
        """Should handle empty filtered list."""
        message = render_message([], "Test City")
        assert "Test City" in message
        assert "0 фильмов" in message


class TestMessageTextContract:
    """Test message-text contract validation."""

    def test_sample_valid(self):
        """Sample file should validate."""
        sample_path = Path(__file__).parent.parent / "contracts" / "examples" / "message-text.sample.json"
        with open(sample_path) as f:
            data = json.load(f)
        is_valid, errors = validate_against_contract(data, "message-text")
        assert is_valid, f"Validation errors: {errors}"

    def test_missing_text_field(self):
        """Missing text field should fail."""
        data = {"meta": {"template": "telegram", "formatted_at": "2026-03-02T00:00:00"}}
        is_valid, errors = validate_against_contract(data, "message-text")
        assert not is_valid

    def test_text_must_be_string(self):
        """Text must be a string type."""
        data = {
            "text": 123,  # Not a string
            "meta": {"template": "telegram", "formatted_at": "2026-03-02T00:00:00"}
        }
        is_valid, errors = validate_against_contract(data, "message-text")
        assert not is_valid


class TestFormatIntegration:
    """Integration tests for ct-format."""

    def test_full_format_produces_valid_contract(self):
        """Full format should produce valid message-text."""
        from datetime import datetime

        filtered = [
            {
                "movie": {"id": "1", "title": "Test Movie", "url": "https://example.com"},
                "relevance_score": 85,
                "recommendation": "recommended"
            }
        ]

        text = render_message(filtered, "Test City")

        data = {
            "text": text,
            "meta": {
                "template": "telegram",
                "city_display": "Test City",
                "movie_count": 1,
                "formatted_at": datetime.now().isoformat()
            }
        }

        is_valid, errors = validate_against_contract(data, "message-text")
        assert is_valid, f"Validation errors: {errors}"
