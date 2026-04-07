"""
Test ct-filter tool contract validation.
"""

import json
import importlib.util
import sys
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "_shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "ct-filter"))

from validate import validate_against_contract

FILTER_MAIN_SPEC = importlib.util.spec_from_file_location(
    "ct_filter_main",
    Path(__file__).parent.parent / "tools" / "ct-filter" / "main.py",
)
FILTER_MAIN = importlib.util.module_from_spec(FILTER_MAIN_SPEC)
assert FILTER_MAIN_SPEC.loader is not None
FILTER_MAIN_SPEC.loader.exec_module(FILTER_MAIN)
build_filtered_item = FILTER_MAIN.build_filtered_item


def make_filter_result_item(
    movie_id: str = "1",
    title: str = "Test",
    url: str | None = "https://example.com",
    score: int = 85,
    recommendation: str = "recommended",
    **movie_overrides
) -> dict:
    """Create a minimal filter-result item for contract tests."""
    movie = {"id": movie_id, "title": title}
    if url is not None:
        movie["url"] = url
    movie.update(movie_overrides)
    return {
        "movie": movie,
        "relevance_score": score,
        "recommendation": recommendation
    }


class TestFilterResultContract:
    """Test filter-result contract validation."""

    def test_sample_valid(self):
        """Sample file should validate."""
        sample_path = Path(__file__).parent.parent / "contracts" / "examples" / "filter-result.sample.json"
        with open(sample_path) as f:
            data = json.load(f)
        is_valid, errors = validate_against_contract(data, "filter-result")
        assert is_valid, f"Validation errors: {errors}"

    def test_missing_filtered_field(self):
        """Missing filtered field should fail."""
        data = {"meta": {"total_input": 10, "matched": 5, "thresholds": {}}}
        is_valid, errors = validate_against_contract(data, "filter-result")
        assert not is_valid

    def test_invalid_recommendation(self):
        """Invalid recommendation should fail."""
        data = {
            "filtered": [make_filter_result_item(recommendation="invalid_value")],
            "meta": {"total_input": 1, "matched": 1, "thresholds": {"recommendations": ["must_see"]}}
        }
        is_valid, errors = validate_against_contract(data, "filter-result")
        assert not is_valid


class TestFilterLogic:
    """Test filtering logic."""

    def test_filter_must_see_and_recommended(self):
        """Should filter to only must_see and recommended."""
        # This would test the actual filter logic if we import it
        # For now, just verify the contract accepts valid data
        data = {
            "filtered": [
                make_filter_result_item(
                    movie_id="1",
                    title="Movie 1",
                    url="https://example.com/1",
                    score=95,
                    recommendation="must_see"
                ),
                make_filter_result_item(
                    movie_id="2",
                    title="Movie 2",
                    url="https://example.com/2",
                    score=75,
                    recommendation="recommended"
                )
            ],
            "meta": {
                "total_input": 5,
                "matched": 2,
                "thresholds": {
                    "recommendations": ["must_see", "recommended"],
                    "min_score": 60
                }
            }
        }
        is_valid, errors = validate_against_contract(data, "filter-result")
        assert is_valid, f"Validation errors: {errors}"

    def test_null_year_allowed(self):
        """Null year should be allowed."""
        data = {
            "filtered": [make_filter_result_item(year=None)],
            "meta": {"total_input": 1, "matched": 1, "thresholds": {}}
        }
        is_valid, errors = validate_against_contract(data, "filter-result")
        assert is_valid, f"Validation errors: {errors}"

    def test_showtimes_allowed(self):
        """Movie showtimes with price should validate."""
        data = {
            "filtered": [
                make_filter_result_item(
                    showtimes=[
                        {
                            "time": "21:10",
                            "datetime_iso": "2026-03-10T21:10:00+03:00",
                            "price": "от 250 ₽",
                            "hall": "Стандарт",
                            "booking_url": "https://example.com/film",
                        }
                    ]
                )
            ],
            "meta": {"total_input": 1, "matched": 1, "thresholds": {}}
        }
        is_valid, errors = validate_against_contract(data, "filter-result")
        assert is_valid, f"Validation errors: {errors}"

    def test_build_filtered_item_preserves_quality_fields(self):
        item = {
            "movie": {
                "id": "1",
                "title": "Test",
                "url": "https://example.com",
                "showtimes": [],
                "available_days": [],
                "available_days_accurate": [],
            },
            "relevance_score": 88,
            "confidence": 0.76,
            "recommendation": "recommended",
            "reasoning": "Rules-first result",
            "key_matches": ["аниме"],
            "red_flags": ["скудные метаданные"],
            "rule_score": 90,
            "llm_delta": -2,
            "review_required": True,
            "decision_basis": ["rule:anime_floor", "quality:review_required"],
        }

        filtered = build_filtered_item(item, "recommended", 88)

        assert filtered["confidence"] == 0.76
        assert filtered["key_matches"] == ["аниме"]
        assert filtered["rule_score"] == 90
        assert filtered["llm_delta"] == -2
        assert filtered["review_required"] is True
