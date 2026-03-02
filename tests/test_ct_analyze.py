"""
Test ct-analyze tool contract validation.
"""

import json
import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "_shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "ct-analyze"))

from validate import validate_against_contract
from adapter_agents import (
    load_taste_profile,
    build_prompt,
    parse_ai_response,
    mock_analyze,
    preflight_check,
    select_agent,
    AGENTS
)


class TestTasteProfile:
    """Test taste profile loading."""

    def test_load_taste_profile(self):
        """Should load taste profile from YAML."""
        taste_path = Path(__file__).parent.parent / "taste" / "profile.yaml"
        taste = load_taste_profile(str(taste_path))
        assert "likes" in taste
        assert "dislikes" in taste

    def test_taste_has_directors(self):
        """Taste profile should have directors."""
        taste_path = Path(__file__).parent.parent / "taste" / "profile.yaml"
        taste = load_taste_profile(str(taste_path))
        assert "directors" in taste.get("likes", {})


class TestPromptBuilder:
    """Test prompt construction."""

    def test_build_prompt_includes_movies(self):
        """Prompt should include movie titles."""
        movies = [
            {"id": "1", "title": "Test Movie", "director": "Director", "genres": ["drama"]}
        ]
        taste = {"likes": {"directors": ["Nolan"]}, "dislikes": {}}
        prompt = build_prompt(movies, taste, {"name": "pi"})

        assert "Test Movie" in prompt
        assert "Nolan" in prompt

    def test_build_prompt_instructions(self):
        """Prompt should include analysis instructions."""
        movies = [{"id": "1", "title": "Test"}]
        taste = {"likes": {}, "dislikes": {}}
        prompt = build_prompt(movies, taste, {"name": "pi"})

        assert "JSON" in prompt
        assert "recommendation" in prompt.lower()


class TestMockAnalyze:
    """Test mock analysis for dry-run."""

    def test_mock_analyze_returns_results(self):
        """Mock analyze should return results."""
        movies = [
            {"id": "1", "title": "Test Movie", "url": "https://example.com"}
        ]
        analyzed, meta = mock_analyze(movies)

        assert len(analyzed) == 1
        assert analyzed[0]["movie"]["title"] == "Test Movie"
        assert meta["agent"] == "dry_run"

    def test_mock_analyze_limited_to_3(self):
        """Mock analyze should limit to 3 movies."""
        movies = [
            {"id": str(i), "title": f"Movie {i}", "url": f"https://example.com/{i}"}
            for i in range(10)
        ]
        analyzed, meta = mock_analyze(movies)

        assert len(analyzed) == 3


class TestParseAIResponse:
    """Test AI response parsing."""

    def test_parse_json_array(self):
        """Should parse plain JSON array."""
        response = '[{"movie_id": "1", "relevance_score": 85}]'
        result = parse_ai_response(response)
        assert len(result) == 1
        assert result[0]["movie_id"] == "1"

    def test_parse_json_with_markdown(self):
        """Should parse JSON from markdown code block."""
        response = '```json\n[{"movie_id": "1", "relevance_score": 85}]\n```'
        result = parse_ai_response(response)
        assert len(result) == 1

    def test_parse_embedded_json(self):
        """Should extract JSON from text."""
        response = 'Here is the result: [{"movie_id": "1", "relevance_score": 85}] Done.'
        result = parse_ai_response(response)
        assert len(result) == 1


class TestAnalysisResultContract:
    """Test analysis-result contract validation."""

    def test_sample_valid(self):
        """Sample file should validate."""
        sample_path = Path(__file__).parent.parent / "contracts" / "examples" / "analysis-result.sample.json"
        with open(sample_path) as f:
            data = json.load(f)
        is_valid, errors = validate_against_contract(data, "analysis-result")
        assert is_valid, f"Validation errors: {errors}"

    def test_mock_output_valid(self):
        """Mock analyze output should be valid."""
        movies = [
            {"id": "1", "title": "Test", "director": "", "genres": [], "url": "https://example.com"}
        ]
        analyzed, meta = mock_analyze(movies)

        data = {"analyzed": analyzed, "meta": meta}
        is_valid, errors = validate_against_contract(data, "analysis-result")
        assert is_valid, f"Validation errors: {errors}"


class TestAgentPreflight:
    """Test agent preflight checks."""

    def test_pi_agent_config(self):
        """Pi agent should be configured."""
        pi_agent = next((a for a in AGENTS if a["name"] == "pi"), None)
        assert pi_agent is not None
        assert pi_agent["cmd"] == "pi"

    def test_kimi_agent_config(self):
        """Kimi agent should be configured."""
        kimi_agent = next((a for a in AGENTS if a["name"] == "kimi"), None)
        assert kimi_agent is not None
        assert kimi_agent["cmd"] == "kimi"
