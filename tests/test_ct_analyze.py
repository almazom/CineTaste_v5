"""
Test ct-analyze tool contract validation and adapter behavior.
"""

import json
import subprocess
import pytest
import sys
from pathlib import Path
from types import SimpleNamespace

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "_shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "ct-analyze"))

from validate import validate_against_contract
from adapter_agents import (
    AGENTS,
    analyze_movies,
    analyze_with_agent,
    build_prompt,
    call_agent,
    format_movies_for_prompt,
    get_agent,
    load_taste_profile,
    merge_analysis,
    mock_analyze,
    parse_ai_response,
    preflight_check,
    select_agent,
)


class TestTasteProfile:
    """Test taste profile loading."""

    def test_load_taste_profile(self):
        taste_path = Path(__file__).parent.parent / "taste" / "profile.yaml"
        taste = load_taste_profile(str(taste_path))
        assert "likes" in taste
        assert "dislikes" in taste

    def test_taste_has_directors(self):
        taste_path = Path(__file__).parent.parent / "taste" / "profile.yaml"
        taste = load_taste_profile(str(taste_path))
        assert "directors" in taste.get("likes", {})


class TestPromptBuilder:
    """Test prompt construction."""

    def test_build_prompt_includes_movies(self):
        movies = [{"id": "1", "title": "Test Movie", "director": "Director", "genres": ["drama"]}]
        taste = {"likes": {"directors": ["Nolan"]}, "dislikes": {}}
        prompt = build_prompt(movies, taste, {"name": "pi"})
        assert "Test Movie" in prompt
        assert "Nolan" in prompt

    def test_build_prompt_instructions(self):
        movies = [{"id": "1", "title": "Test"}]
        taste = {"likes": {}, "dislikes": {}}
        prompt = build_prompt(movies, taste, {"name": "pi"})
        assert "JSON" in prompt
        assert "recommendation" in prompt.lower()

    def test_build_prompt_kimi_mentions_web_search(self):
        movies = [{"id": "1", "title": "Test"}]
        taste = {"likes": {}, "dislikes": {}}
        prompt = build_prompt(movies, taste, {"name": "kimi", "supports_web_search": True})
        assert "WEB SEARCH" in prompt

    def test_format_movies_for_prompt_renders_fields(self):
        movies = [{"id": "m1", "title": "Movie", "director": "Dir", "genres": ["drama"], "year": 2026}]
        out = format_movies_for_prompt(movies)
        assert "[m1]" in out
        assert "Реж: Dir" in out
        assert "Жанры: drama" in out


class TestMockAnalyze:
    def test_mock_analyze_returns_results(self):
        movies = [{"id": "1", "title": "Test Movie", "url": "https://example.com"}]
        analyzed, meta = mock_analyze(movies)
        assert len(analyzed) == 1
        assert analyzed[0]["movie"]["title"] == "Test Movie"
        assert meta["agent"] == "dry_run"

    def test_mock_analyze_limited_to_3(self):
        movies = [{"id": str(i), "title": f"Movie {i}", "url": f"https://example.com/{i}"} for i in range(10)]
        analyzed, meta = mock_analyze(movies)
        assert len(analyzed) == 3
        assert meta["analyzer"] == "dry_run"


class TestParseAIResponse:
    def test_parse_json_array(self):
        response = '[{"movie_id": "1", "relevance_score": 85}]'
        result = parse_ai_response(response)
        assert len(result) == 1
        assert result[0]["movie_id"] == "1"

    def test_parse_json_with_markdown(self):
        response = '```json\n[{"movie_id": "1", "relevance_score": 85}]\n```'
        result = parse_ai_response(response)
        assert len(result) == 1

    def test_parse_embedded_json(self):
        response = 'Here is the result: [{"movie_id": "1", "relevance_score": 85}] Done.'
        result = parse_ai_response(response)
        assert len(result) == 1

    def test_parse_dict_with_analyzed_key(self):
        response = '{"analyzed":[{"movie_id":"1"}]}'
        result = parse_ai_response(response)
        assert result[0]["movie_id"] == "1"

    def test_parse_invalid_raises(self):
        with pytest.raises(ValueError):
            parse_ai_response("not-json")


class TestAnalysisResultContract:
    def test_sample_valid(self):
        sample_path = Path(__file__).parent.parent / "contracts" / "examples" / "analysis-result.sample.json"
        data = json.loads(sample_path.read_text(encoding="utf-8"))
        is_valid, errors = validate_against_contract(data, "analysis-result")
        assert is_valid, f"Validation errors: {errors}"

    def test_mock_output_valid(self):
        movies = [{"id": "1", "title": "Test", "director": "", "genres": [], "url": "https://example.com"}]
        analyzed, meta = mock_analyze(movies)
        data = {"analyzed": analyzed, "meta": meta}
        is_valid, errors = validate_against_contract(data, "analysis-result")
        assert is_valid, f"Validation errors: {errors}"


class TestAgentHelpers:
    def test_get_agent_known(self):
        agent = get_agent("pi")
        assert agent is not None
        assert agent["cmd"] == "pi"

    def test_get_agent_unknown(self):
        assert get_agent("unknown") is None

    def test_select_agent_with_candidates(self, monkeypatch):
        def fake_preflight(agent):
            return agent["name"] == "pi"

        monkeypatch.setattr("adapter_agents.preflight_check", fake_preflight)
        selected = select_agent(["kimi", "pi"])
        assert selected["name"] == "pi"


class TestPreflight:
    def test_preflight_not_found(self, monkeypatch):
        agent = {"name": "pi", "cmd": "pi"}
        monkeypatch.setattr("adapter_agents.shutil.which", lambda _: None)
        assert not preflight_check(agent)

    def test_preflight_success(self, monkeypatch):
        agent = {"name": "pi", "cmd": "pi"}
        monkeypatch.setattr("adapter_agents.shutil.which", lambda _: "/usr/bin/pi")

        result = SimpleNamespace(returncode=0, stdout="three", stderr="")
        monkeypatch.setattr("adapter_agents.subprocess.run", lambda *a, **k: result)
        assert preflight_check(agent)

    def test_preflight_bad_response(self, monkeypatch):
        agent = {"name": "pi", "cmd": "pi"}
        monkeypatch.setattr("adapter_agents.shutil.which", lambda _: "/usr/bin/pi")

        result = SimpleNamespace(returncode=0, stdout="unexpected", stderr="")
        monkeypatch.setattr("adapter_agents.subprocess.run", lambda *a, **k: result)
        assert not preflight_check(agent)

    def test_preflight_exception(self, monkeypatch):
        agent = {"name": "pi", "cmd": "pi"}
        monkeypatch.setattr("adapter_agents.shutil.which", lambda _: "/usr/bin/pi")
        monkeypatch.setattr("adapter_agents.subprocess.run", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
        assert not preflight_check(agent)


class TestCallAgent:
    def test_call_agent_success(self, monkeypatch):
        agent = {"name": "pi", "cmd": "pi", "args": ["--print"], "timeout": 10}
        result = SimpleNamespace(returncode=0, stdout='[{"movie_id":"1"}]', stderr="")
        monkeypatch.setattr("adapter_agents.subprocess.run", lambda *a, **k: result)
        out = call_agent("prompt", agent)
        assert "movie_id" in out

    def test_call_agent_nonzero(self, monkeypatch):
        agent = {"name": "pi", "cmd": "pi", "args": ["--print"], "timeout": 10}
        result = SimpleNamespace(returncode=1, stdout="", stderr="fail")
        monkeypatch.setattr("adapter_agents.subprocess.run", lambda *a, **k: result)
        with pytest.raises(RuntimeError):
            call_agent("prompt", agent)

    def test_call_agent_timeout(self, monkeypatch):
        agent = {"name": "pi", "cmd": "pi", "args": ["--print"], "timeout": 10}

        def boom(*args, **kwargs):
            raise subprocess.TimeoutExpired(cmd="pi", timeout=10)

        monkeypatch.setattr("adapter_agents.subprocess.run", boom)
        with pytest.raises(TimeoutError):
            call_agent("prompt", agent)

    def test_call_agent_missing_binary(self, monkeypatch):
        agent = {"name": "pi", "cmd": "pi", "args": ["--print"], "timeout": 10}

        def boom(*args, **kwargs):
            raise FileNotFoundError("no pi")

        monkeypatch.setattr("adapter_agents.subprocess.run", boom)
        with pytest.raises(RuntimeError):
            call_agent("prompt", agent)


class TestAnalyzeMovies:
    @staticmethod
    def sample_movies():
        return [
            {
                "id": "m1",
                "title": "Movie One",
                "original_title": "",
                "director": "Dir",
                "actors": [],
                "genres": ["drama"],
                "year": 2026,
                "source": "kinoteatr.ru",
                "url": "https://example.com/m1",
            }
        ]

    def test_merge_analysis(self):
        agent = {"name": "pi", "supports_web_search": False}
        analyses = [{"movie_id": "m1", "relevance_score": 77, "recommendation": "recommended"}]
        merged, meta = merge_analysis(self.sample_movies(), analyses, agent)
        assert merged[0]["movie"]["id"] == "m1"
        assert meta["agent"] == "pi"

    def test_analyze_with_agent(self, monkeypatch):
        movies = self.sample_movies()
        taste = {"likes": {}, "dislikes": {}}
        agent = {"name": "pi", "supports_web_search": False}
        monkeypatch.setattr("adapter_agents.call_agent", lambda prompt, agent: '[{"movie_id":"m1","relevance_score":88,"recommendation":"must_see"}]')
        out, meta = analyze_with_agent(movies, taste, agent)
        assert out[0]["recommendation"] == "must_see"
        assert meta["agent"] == "pi"

    def test_analyze_movies_dry_run_flag(self):
        out, meta = analyze_movies(self.sample_movies(), "taste/profile.yaml", dry_run=True, agent_name="auto")
        assert meta["agent"] == "dry_run"
        assert len(out) == 1

    def test_analyze_movies_explicit_dry_run(self):
        out, meta = analyze_movies(self.sample_movies(), "taste/profile.yaml", dry_run=False, agent_name="dry_run")
        assert meta["agent"] == "dry_run"

    def test_analyze_movies_auto_fallback(self, monkeypatch, tmp_path):
        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes: {}\ndislikes: {}\n", encoding="utf-8")

        def fake_preflight(agent):
            return True

        calls = {"n": 0}

        def fake_analyze_with_agent(movies, taste, agent):
            calls["n"] += 1
            if agent["name"] == "kimi":
                raise RuntimeError("kimi fail")
            return ([{"movie": {"id": "m1", "title": "Movie"}, "relevance_score": 70, "recommendation": "recommended"}],
                    {"analyzer": "agent:pi", "analyzed_at": "2026-03-02T00:00:00+00:00", "taste_profile": "1.0", "agent": "pi", "web_search_used": False})

        monkeypatch.setattr("adapter_agents.preflight_check", fake_preflight)
        monkeypatch.setattr("adapter_agents.analyze_with_agent", fake_analyze_with_agent)

        out, meta = analyze_movies(self.sample_movies(), str(taste_file), dry_run=False, agent_name="auto")
        assert calls["n"] >= 2
        assert meta["agent"] == "pi"
        assert out

    def test_analyze_movies_auto_all_fail_raises(self, monkeypatch, tmp_path):
        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes: {}\ndislikes: {}\n", encoding="utf-8")

        monkeypatch.setattr("adapter_agents.preflight_check", lambda agent: False)
        with pytest.raises(RuntimeError, match="No AI agent available"):
            analyze_movies(self.sample_movies(), str(taste_file), dry_run=False, agent_name="auto")

    def test_analyze_movies_explicit_unavailable(self, monkeypatch, tmp_path):
        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes: {}\ndislikes: {}\n", encoding="utf-8")
        monkeypatch.setattr("adapter_agents.preflight_check", lambda agent: False)

        with pytest.raises(RuntimeError):
            analyze_movies(self.sample_movies(), str(taste_file), dry_run=False, agent_name="pi")

    def test_analyze_movies_explicit_success(self, monkeypatch, tmp_path):
        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes: {}\ndislikes: {}\n", encoding="utf-8")
        monkeypatch.setattr("adapter_agents.preflight_check", lambda agent: True)
        monkeypatch.setattr(
            "adapter_agents.analyze_with_agent",
            lambda movies, taste, agent: (
                [{"movie": {"id": "m1", "title": "Movie"}, "relevance_score": 65, "recommendation": "recommended"}],
                {"analyzer": "agent:pi", "analyzed_at": "2026-03-02T00:00:00+00:00", "taste_profile": "1.0", "agent": "pi", "web_search_used": False},
            ),
        )

        out, meta = analyze_movies(self.sample_movies(), str(taste_file), dry_run=False, agent_name="pi")
        assert meta["agent"] == "pi"
        assert out[0]["relevance_score"] == 65


class TestAgentConfig:
    def test_pi_agent_config(self):
        pi_agent = next((a for a in AGENTS if a["name"] == "pi"), None)
        assert pi_agent is not None
        assert pi_agent["cmd"] == "pi"

    def test_kimi_agent_config(self):
        kimi_agent = next((a for a in AGENTS if a["name"] == "kimi"), None)
        assert kimi_agent is not None
        assert kimi_agent["cmd"] == "kimi"
