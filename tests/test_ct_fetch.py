"""
Test ct-fetch tool contract validation.
"""

import json
import pytest
import sys
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "_shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "ct-fetch"))

from validate import validate_against_contract
from adapter_kinoteatr import fetch_movies, parse_html


class TestKinoteatrAdapter:
    """Test kinoteatr.ru adapter."""

    def test_fetch_movies_returns_list(self):
        """Should return a list of movies."""
        movies = fetch_movies("naberezhnie-chelni")
        assert isinstance(movies, list)
        assert len(movies) > 0

    def test_movie_has_required_fields(self):
        """Each movie should have required fields."""
        movies = fetch_movies("naberezhnie-chelni")
        for movie in movies[:5]:  # Check first 5
            assert "id" in movie
            assert "title" in movie
            assert "source" in movie
            assert movie["source"] == "kinoteatr.ru"

    def test_movie_titles_not_empty(self):
        """Movie titles should not be empty."""
        movies = fetch_movies("naberezhnie-chelni")
        for movie in movies:
            assert movie["title"], f"Empty title for movie {movie['id']}"

    def test_movie_urls_valid(self):
        """Movie URLs should be valid."""
        movies = fetch_movies("naberezhnie-chelni")
        for movie in movies:
            if movie.get("url"):
                assert movie["url"].startswith("https://kinoteatr.ru/film/")

    def test_invalid_city_raises_error(self):
        """Invalid city should raise ValueError."""
        with pytest.raises(ValueError):
            fetch_movies("invalid-city-name")


class TestMovieBatchContract:
    """Test movie-batch contract validation."""

    def test_sample_valid(self):
        """Sample file should validate."""
        sample_path = Path(__file__).parent.parent / "contracts" / "examples" / "movie-batch.sample.json"
        with open(sample_path) as f:
            data = json.load(f)
        is_valid, errors = validate_against_contract(data, "movie-batch")
        assert is_valid, f"Validation errors: {errors}"

    def test_missing_movies_field(self):
        """Missing movies field should fail."""
        data = {"meta": {"city": "test"}}
        is_valid, errors = validate_against_contract(data, "movie-batch")
        assert not is_valid

    def test_missing_meta_field(self):
        """Missing meta field should fail."""
        data = {"movies": []}
        is_valid, errors = validate_against_contract(data, "movie-batch")
        assert not is_valid


class TestFetchIntegration:
    """Integration tests for ct-fetch."""

    def test_full_fetch_produces_valid_contract(self):
        """Full fetch should produce valid movie-batch."""
        movies = fetch_movies("naberezhnie-chelni")

        from datetime import datetime
        data = {
            "movies": movies,
            "meta": {
                "city": "naberezhnie-chelni",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "fetched_at": datetime.now().isoformat()
            }
        }

        is_valid, errors = validate_against_contract(data, "movie-batch")
        assert is_valid, f"Validation errors: {errors}"
