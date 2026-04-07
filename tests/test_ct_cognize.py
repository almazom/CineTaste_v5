"""
Test ct-cognize tool: port validation, response parsing, merge, and CLI.
"""

import json
import io
import subprocess
import time
import pytest
import sys
from types import SimpleNamespace
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "_shared"))
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "ct-cognize"))

from port import enforce_input, enforce_output, validate_input, validate_output
from main import (
    parse_response,
    merge,
    AGENTS,
    AGENT_NAMES,
    INSTRUCTION,
    call_agent,
    main as cli_main,
    _run_preflight,
    parse_agent_list,
    parallel_preflight,
    select_agent_chain,
)
from rule_engine import build_rule_map, bounded_merge_analysis


ROOT = Path(__file__).parent.parent


# ── Fixtures ───────────────────────────────────────────────────────────


def sample_movies():
    return [
        {
            "id": "kt-test-movie",
            "title": "Test Movie",
            "original_title": "Test Film",
            "director": "Test Director",
            "actors": ["Actor One", "Actor Two"],
            "genres": ["drama", "thriller"],
            "year": 2026,
            "source": "kinoteatr.ru",
            "url": "https://kinoteatr.ru/film/test-movie/city/",
            "showtimes": [{"time": "14:00", "datetime_iso": "2026-03-03T14:00:00+03:00"}],
            "raw_description": "Character-driven psychological drama with intense performances.",
        },
        {
            "id": "kt-another-film",
            "title": "Another Film",
            "original_title": "",
            "director": "",
            "actors": [],
            "genres": ["comedy"],
            "year": 2025,
            "source": "kinoteatr.ru",
            "url": "https://kinoteatr.ru/film/another-film/city/",
            "showtimes": [{"time": "18:00", "datetime_iso": "2026-03-03T18:00:00+03:00"}],
            "raw_description": "Broad mainstream comedy sequel.",
        },
    ]


def sample_taste_profile():
    return {
        "version": "1.2",
        "likes": {
            "directors": ["Test Director"],
            "actors": ["Actor One"],
            "genres": ["drama", "anime", "japanese anime"],
            "keywords": ["character-driven", "psychological"],
        },
        "dislikes": {
            "genres": ["horror", "slasher", "mainstream comedy"],
            "keywords": ["blockbuster", "franchise", "sequel", "remake"],
        },
        "canon": [
            {"director": "Test Director", "weight": 1.0},
        ],
        "thresholds": {
            "must_see": 85,
            "recommended": 60,
            "maybe": 40,
            "skip": 0,
        },
    }


def sample_schedule_input():
    return {
        "movies": sample_movies(),
        "meta": {
            "city": "naberezhnie-chelni",
            "date": "2026-03-03",
            "fetched_at": "2026-03-03T12:00:00+00:00",
            "scheduled_at": "2026-03-03T12:00:00+00:00",
            "schedule_source": "kinoteatr.ru",
            "movies_with_showtimes": 2,
        },
    }


def sample_analysis_result(agent_name="gemini"):
    movies = sample_movies()
    agent = {"name": agent_name, "supports_web_search": False}
    rule_map = build_rule_map(movies, sample_taste_profile())
    analyses = [
        {
            "movie_id": "kt-test-movie",
            "relevance_score": 85,
            "recommendation": "must_see",
            "reasoning": "Great drama",
            "key_matches": ["drama"],
            "red_flags": [],
        },
        {
            "movie_id": "kt-another-film",
            "relevance_score": 30,
            "recommendation": "skip",
            "reasoning": "Not a match",
            "key_matches": [],
            "red_flags": ["comedy"],
        },
    ]
    return merge(movies, analyses, agent, rule_map, sample_taste_profile()["thresholds"], "1.2")


# ── Port Validation ────────────────────────────────────────────────────


class TestPortValidation:
    """Test port.py contract validation."""

    def test_validate_input_valid(self):
        data = sample_schedule_input()
        is_valid, errors = validate_input(data)
        assert is_valid, f"Validation errors: {errors}"

    def test_validate_input_missing_movies(self):
        data = {"meta": {}}
        is_valid, errors = validate_input(data)
        assert not is_valid


class TestAgentConfig:
    def test_pi_runtime_pins_glm5_turbo(self):
        pi = next(agent for agent in AGENTS if agent["name"] == "pi")

        assert "--provider" in pi["run_args"]
        assert "zai" in pi["run_args"]
        assert "--model" in pi["run_args"]
        assert "glm-5-turbo" in pi["run_args"]

    def test_claude_runtime_uses_permission_mode(self):
        claude = next(agent for agent in AGENTS if agent["name"] == "claude")

        assert "--permission-mode" in claude["run_args"]
        assert "bypassPermissions" in claude["run_args"]
        assert "--approval-mode" not in claude["run_args"]

    def test_validate_output_valid(self):
        data = sample_analysis_result()
        is_valid, errors = validate_output(data)
        assert is_valid, f"Validation errors: {errors}"

    def test_validate_output_missing_analyzed(self):
        data = {"meta": {}}
        is_valid, errors = validate_output(data)
        assert not is_valid

    def test_enforce_input_valid(self):
        data = sample_schedule_input()
        result = enforce_input(data)
        assert result == data

    def test_enforce_input_invalid_raises(self):
        with pytest.raises(ValueError):
            enforce_input({"bad": "data"})

    def test_enforce_output_valid(self):
        data = sample_analysis_result()
        result = enforce_output(data)
        assert result == data

    def test_enforce_output_invalid_raises(self):
        with pytest.raises(ValueError):
            enforce_output({"bad": "data"})


# ── Response Parsing ───────────────────────────────────────────────────


class TestParseResponse:
    """Test parse_response extracting JSON from AI output."""

    def test_parse_clean_json(self):
        raw = json.dumps([{"movie_id": "m1", "relevance_score": 70}])
        result = parse_response(raw)
        assert len(result) == 1
        assert result[0]["movie_id"] == "m1"

    def test_parse_with_markdown_wrapper(self):
        raw = '```json\n[{"movie_id": "m1", "relevance_score": 70}]\n```'
        result = parse_response(raw)
        assert result[0]["movie_id"] == "m1"

    def test_parse_with_surrounding_text(self):
        raw = 'Here are the results:\n[{"movie_id": "m1", "relevance_score": 70}]\nDone.'
        result = parse_response(raw)
        assert result[0]["movie_id"] == "m1"

    def test_parse_invalid_raises(self):
        with pytest.raises(ValueError, match="Could not parse"):
            parse_response("This is not JSON at all")

    def test_parse_empty_raises(self):
        with pytest.raises(ValueError):
            parse_response("")

    def test_parse_single_object(self):
        raw = '{"movie_id": "m1", "relevance_score": 90}'
        result = parse_response(raw)
        assert isinstance(result, list)
        assert result[0]["movie_id"] == "m1"


# ── Merge ──────────────────────────────────────────────────────────────


class TestMerge:
    """Test merge of AI analyses with original movie data."""

    def test_merge_exact_id(self):
        movies = sample_movies()
        rule_map = build_rule_map(movies, sample_taste_profile())
        analyses = [{"movie_id": "kt-test-movie", "relevance_score": 85, "recommendation": "must_see"}]
        agent = {"name": "test", "supports_web_search": False}
        result = merge(movies, analyses, agent, rule_map, sample_taste_profile()["thresholds"], "1.2")
        assert len(result["analyzed"]) == 1
        assert result["analyzed"][0]["movie"]["title"] == "Test Movie"
        assert result["analyzed"][0]["relevance_score"] >= 85
        assert result["meta"]["agent"] == "test"
        assert result["analyzed"][0]["rule_score"] >= 85

    def test_merge_fuzzy_id(self):
        movies = sample_movies()
        rule_map = build_rule_map(movies, sample_taste_profile())
        # AI returns a longer ID — should fuzzy-match
        analyses = [{"movie_id": "kt-test-movie-extended", "relevance_score": 75, "recommendation": "recommended"}]
        agent = {"name": "test", "supports_web_search": False}
        result = merge(movies, analyses, agent, rule_map, sample_taste_profile()["thresholds"], "1.2")
        assert result["analyzed"][0]["movie"]["title"] == "Test Movie"

    def test_merge_missing_id(self):
        movies = sample_movies()
        rule_map = build_rule_map(movies, sample_taste_profile())
        analyses = [{"movie_id": "nonexistent-movie", "relevance_score": 50, "recommendation": "skip"}]
        agent = {"name": "test", "supports_web_search": False}
        result = merge(movies, analyses, agent, rule_map, sample_taste_profile()["thresholds"], "1.2")
        assert result["analyzed"][0]["movie"]["title"] == "Unknown"

    def test_merge_preserves_meta(self):
        movies = sample_movies()
        rule_map = build_rule_map(movies, sample_taste_profile())
        analyses = [{"movie_id": "kt-test-movie", "relevance_score": 90, "recommendation": "must_see"}]
        agent = {"name": "gemini", "supports_web_search": False}
        result = merge(movies, analyses, agent, rule_map, sample_taste_profile()["thresholds"], "1.2")
        assert result["meta"]["analyzer"] == "cognize:gemini"
        assert "analyzed_at" in result["meta"]
        assert result["meta"]["quality_policy"] == "rules_first_v1"
        assert result["meta"]["taste_profile"] == "1.2"

    def test_merge_multiple_movies(self):
        movies = sample_movies()
        rule_map = build_rule_map(movies, sample_taste_profile())
        analyses = [
            {"movie_id": "kt-test-movie", "relevance_score": 90, "recommendation": "must_see"},
            {"movie_id": "kt-another-film", "relevance_score": 30, "recommendation": "skip"},
        ]
        agent = {"name": "qwen", "supports_web_search": False}
        result = merge(movies, analyses, agent, rule_map, sample_taste_profile()["thresholds"], "1.2")
        assert len(result["analyzed"]) == 2
        titles = [a["movie"]["title"] for a in result["analyzed"]]
        assert "Test Movie" in titles
        assert "Another Film" in titles


class TestRuleScoring:
    def test_build_rule_map_marks_anime_as_must_see(self):
        movies = [
            {
                "id": "anime-1",
                "title": "Anime Film",
                "director": "",
                "actors": [],
                "genres": ["аниме", "фэнтези"],
                "raw_description": "Japanese anime feature film.",
            }
        ]

        rule_map = build_rule_map(movies, sample_taste_profile())
        rule_info = rule_map["anime-1"]

        assert rule_info["rule_score"] >= 90
        assert rule_info["recommendation_floor"] == "must_see"
        assert "аниме" in rule_info["key_rule_matches"]

    def test_build_rule_map_marks_known_anime_creator_as_recommended(self):
        movies = [
            {
                "id": "anime-creator-1",
                "title": "Labyrinth",
                "director": "Сё\u200cдзи Кавамо\u200cри",
                "actors": [],
                "genres": [],
                "raw_description": (
                    "Застенчивая старшеклассница Сиори Маэдзава попадает в таинственный мир "
                    "внутри своего смартфона."
                ),
            }
        ]

        rule_map = build_rule_map(movies, sample_taste_profile())
        rule_info = rule_map["anime-creator-1"]

        assert rule_info["rule_score"] >= 62
        assert rule_info["recommendation_floor"] == "recommended"
        assert "аниме-автор: Shoji Kawamori" in rule_info["key_rule_matches"]

    def test_bounded_merge_demotes_low_confidence_must_see(self):
        movie = {
            "id": "sparse-1",
            "title": "Sparse Film",
            "director": "",
            "actors": [],
            "genres": [],
            "raw_description": "",
            "source": "kinoteatr.ru",
            "url": "",
        }
        thresholds = sample_taste_profile()["thresholds"]
        rule_info = {
            "rule_score": 58,
            "recommendation_floor": None,
            "recommendation_ceiling": None,
            "key_rule_matches": [],
            "key_rule_penalties": ["скудные метаданные"],
            "decision_basis": ["quality:sparse_metadata"],
            "metadata_confidence": 0.25,
            "strong_positive": False,
            "hard_negative": False,
        }
        analysis = {
            "movie_id": "sparse-1",
            "relevance_score": 97,
            "recommendation": "must_see",
            "reasoning": "Model overreached.",
            "confidence": 0.55,
        }

        merged = bounded_merge_analysis(movie, analysis, rule_info, thresholds)

        assert merged["review_required"] is True
        assert merged["recommendation"] != "must_see"
        assert merged["confidence"] < 0.78

    def test_bounded_merge_preserves_anime_creator_floor(self):
        movie = {
            "id": "anime-creator-1",
            "title": "Labyrinth",
            "director": "Сёдзи Кавамори",
            "actors": [],
            "genres": [],
            "raw_description": "Таинственный цифровой мир и японский режиссёр-аниматор.",
            "source": "kinoteatr.ru",
            "url": "",
        }
        thresholds = sample_taste_profile()["thresholds"]
        rule_info = {
            "rule_score": 62,
            "recommendation_floor": "recommended",
            "recommendation_ceiling": None,
            "key_rule_matches": ["аниме-автор: Shoji Kawamori"],
            "key_rule_penalties": [],
            "decision_basis": ["rule:anime_creator"],
            "metadata_confidence": 0.57,
            "strong_positive": False,
            "hard_negative": False,
        }
        analysis = {
            "movie_id": "anime-creator-1",
            "relevance_score": 30,
            "recommendation": "maybe",
            "reasoning": "Model was too conservative.",
            "confidence": 0.52,
        }

        merged = bounded_merge_analysis(movie, analysis, rule_info, thresholds)

        assert merged["recommendation"] == "recommended"
        assert merged["relevance_score"] >= thresholds["recommended"]


# ── Agent Registry ─────────────────────────────────────────────────────


class TestAgentRegistry:
    """Test agent registry structure."""

    def test_agents_not_empty(self):
        assert len(AGENTS) > 0

    def test_each_agent_has_required_fields(self):
        required = {"name", "cmd", "preflight_args", "run_args", "timeout", "file_mode"}
        for agent in AGENTS:
            missing = required - set(agent.keys())
            assert not missing, f"Agent {agent.get('name', '?')} missing fields: {missing}"

    def test_file_modes_valid(self):
        valid_modes = {"cwd", "at_file", "stdin", "codex_exec"}
        for agent in AGENTS:
            assert agent["file_mode"] in valid_modes, f"{agent['name']} has invalid file_mode: {agent['file_mode']}"

    def test_instruction_prompt_non_empty(self):
        assert len(INSTRUCTION) > 100


class TestAgentSelectionAndFallback:
    """Test parallel preflight ordering and auto fallback behavior."""

    def test_parallel_preflight_returns_completion_order(self, monkeypatch):
        agents = [
            {"name": "slow", "cmd": "slow"},
            {"name": "fast", "cmd": "fast"},
        ]

        def fake_run(agent):
            delay = 0.03 if agent["name"] == "slow" else 0.01
            time.sleep(delay)
            return {
                "agent": agent,
                "ok": True,
                "reply": "ok",
                "elapsed": delay,
                "error": "",
            }

        monkeypatch.setattr("main._run_preflight", fake_run)
        results = parallel_preflight(agents)
        ordered = [r["agent"]["name"] for r in results]

        assert ordered == ["fast", "slow"]

    def test_select_agent_chain_auto_uses_preflight_order(self, monkeypatch):
        fast = {"name": "fast"}
        slow = {"name": "slow"}

        monkeypatch.setattr(
            "main.parallel_preflight",
            lambda _: [
                {"agent": fast, "ok": True, "reply": "ok", "elapsed": 0.01, "error": ""},
                {"agent": slow, "ok": True, "reply": "ok", "elapsed": 0.02, "error": ""},
            ],
        )

        chain = select_agent_chain("auto")
        assert [a["name"] for a in chain] == ["fast", "slow"]

    def test_parse_agent_list_preserves_order_and_uniques(self):
        parsed = parse_agent_list("pi, qwen,pi,claude")
        assert parsed == ["pi", "qwen", "claude"]

    def test_parse_agent_list_unknown_raises(self):
        with pytest.raises(RuntimeError, match="Unknown agent"):
            parse_agent_list("pi,unknown")

    def test_preflight_accepts_ok_token_not_last(self, monkeypatch):
        agent = {
            "name": "pi",
            "cmd": "pi",
            "preflight_args": ["-p"],
            "preflight_timeout": 5,
        }
        monkeypatch.setattr("main.shutil.which", lambda _: "/usr/bin/pi")
        monkeypatch.setattr(
            "main.subprocess.run",
            lambda *a, **k: SimpleNamespace(
                returncode=0,
                stdout='Я ответил "ok" и продублировал это в Telegram. rewritten: true',
                stderr="",
            ),
        )

        result = _run_preflight(agent)
        assert result["ok"] is True
        assert result["reply"] == "ok"

    def test_preflight_still_checks_exit_code(self, monkeypatch):
        agent = {
            "name": "pi",
            "cmd": "pi",
            "preflight_args": ["-p"],
            "preflight_timeout": 5,
        }
        monkeypatch.setattr("main.shutil.which", lambda _: "/usr/bin/pi")
        monkeypatch.setattr(
            "main.subprocess.run",
            lambda *a, **k: SimpleNamespace(returncode=1, stdout="ok", stderr=""),
        )

        result = _run_preflight(agent)
        assert result["ok"] is False

    def test_preflight_uses_agent_specific_prompt_and_tokens(self, monkeypatch):
        agent = {
            "name": "codex_wp",
            "cmd": "codex_wp",
            "preflight_args": ["exec", "--skip-git-repo-check"],
            "preflight_prompt": "1+2=? Reply with exactly one token: three",
            "preflight_ok_tokens": ["three", "3"],
            "preflight_timeout": 5,
        }
        recorded = {}

        def fake_run(args, **kwargs):
            recorded["args"] = args
            return SimpleNamespace(returncode=0, stdout="three", stderr="")

        monkeypatch.setattr("main.shutil.which", lambda _: "/usr/bin/codex_wp")
        monkeypatch.setattr("main.subprocess.run", fake_run)

        result = _run_preflight(agent)

        assert result["ok"] is True
        assert result["reply"] == "three"
        assert recorded["args"] == [
            "codex_wp",
            "exec",
            "--skip-git-repo-check",
            "1+2=? Reply with exactly one token: three",
        ]


# ── CLI ────────────────────────────────────────────────────────────────


class TestCLI:
    """Test ct-cognize CLI entry point."""

    def test_help(self):
        result = subprocess.run(
            [str(ROOT / "ct-cognize"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "ct-cognize" in result.stdout
        assert "--input" in result.stdout
        assert "--taste" in result.stdout
        assert "--agents" in result.stdout
        assert "--list-agents" in result.stdout

    def test_list_agents(self):
        result = subprocess.run(
            [str(ROOT / "ct-cognize"), "--list-agents"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        listed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
        assert set(AGENT_NAMES).issubset(listed)

    def test_version(self):
        result = subprocess.run(
            [str(ROOT / "ct-cognize"), "--version"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0
        assert "ct-cognize" in result.stdout

    def test_alias_help(self):
        result = subprocess.run(
            [str(ROOT / "ct-cognetive"), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert result.returncode == 0
        assert "ct-cognetive" in result.stdout
        assert "--input" in result.stdout
        assert "--taste" in result.stdout

    def test_missing_args(self):
        result = subprocess.run(
            [str(ROOT / "ct-cognize")],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0

    def test_nonexistent_input_file(self):
        result = subprocess.run(
            [str(ROOT / "ct-cognize"), "--input", "/nonexistent.json", "--taste", "/nonexistent.yaml"],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode != 0


# ── Integration (mocked agent) ────────────────────────────────────────


class TestCognizeIntegration:
    """Integration test with mocked subprocess (no real AI agent)."""

    def test_cognize_with_mock_agent(self, monkeypatch, tmp_path):
        from main import cognize

        # Write input files
        movies_file = tmp_path / "movies.json"
        movies_file.write_text(json.dumps(sample_schedule_input()), encoding="utf-8")

        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes:\n  genres: [drama]\ndislikes:\n  genres: [horror]\n", encoding="utf-8")

        # Mock select_agent to return a known agent
        mock_agent = {
            "name": "mock",
            "cmd": "echo",
            "run_args": [],
            "timeout": 10,
            "file_mode": "cwd",
            "supports_web_search": False,
        }
        monkeypatch.setattr("main.select_agent_chain", lambda *args, **kwargs: [mock_agent])

        # Mock call_agent to return JSON
        mock_response = json.dumps([
            {"movie_id": "kt-test-movie", "relevance_score": 90, "recommendation": "must_see",
             "reasoning": "Great drama", "key_matches": ["drama"], "red_flags": []},
            {"movie_id": "kt-another-film", "relevance_score": 20, "recommendation": "skip",
             "reasoning": "Not interesting", "key_matches": [], "red_flags": ["comedy"]},
        ])
        monkeypatch.setattr("main.call_agent", lambda agent, workdir: mock_response)

        result = cognize(str(movies_file), str(taste_file), agent_name="auto")

        assert "analyzed" in result
        assert "meta" in result
        assert len(result["analyzed"]) == 2
        assert result["meta"]["agent"] == "mock"

        # Validate against contract
        is_valid, errors = validate_output(result)
        assert is_valid, f"Output validation failed: {errors}"

    def test_cognize_auto_runtime_fallback(self, monkeypatch, tmp_path):
        from main import cognize

        movies_file = tmp_path / "movies.json"
        movies_file.write_text(json.dumps(sample_schedule_input()), encoding="utf-8")

        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes: {}\ndislikes: {}\n", encoding="utf-8")

        primary = {
            "name": "primary",
            "cmd": "primary",
            "run_args": [],
            "timeout": 10,
            "file_mode": "cwd",
            "supports_web_search": False,
        }
        fallback = {
            "name": "fallback",
            "cmd": "fallback",
            "run_args": [],
            "timeout": 10,
            "file_mode": "cwd",
            "supports_web_search": False,
        }

        monkeypatch.setattr("main.select_agent_chain", lambda *args, **kwargs: [primary, fallback])

        def fake_call(agent, workdir):
            if agent["name"] == "primary":
                raise RuntimeError("primary timeout")
            return json.dumps([
                {
                    "movie_id": "kt-test-movie",
                    "relevance_score": 88,
                    "recommendation": "recommended",
                    "reasoning": "fallback used",
                    "key_matches": ["drama"],
                    "red_flags": [],
                }
            ])

        monkeypatch.setattr("main.call_agent", fake_call)

        result = cognize(str(movies_file), str(taste_file), agent_name="auto")
        assert result["meta"]["agent"] == "fallback"
        assert len(result["analyzed"]) == 1

    def test_call_agent_codex_exec_uses_positional_prompt(self, monkeypatch, tmp_path):
        workdir = tmp_path / "workdir"
        workdir.mkdir()
        (workdir / "movies.json").write_text(json.dumps({"movies": sample_movies()}), encoding="utf-8")
        (workdir / "taste.yaml").write_text("likes: {}\n", encoding="utf-8")

        agent = {
            "name": "codex_wp",
            "cmd": "codex_wp",
            "run_args": ["exec", "--skip-git-repo-check"],
            "timeout": 10,
            "file_mode": "codex_exec",
        }
        recorded = {}

        def fake_run(args, **kwargs):
            recorded["args"] = args
            recorded["cwd"] = kwargs["cwd"]
            return SimpleNamespace(returncode=0, stdout='[{"movie_id":"kt-test-movie"}]', stderr="")

        monkeypatch.setattr("main.subprocess.run", fake_run)

        response = call_agent(agent, str(workdir))

        assert response == '[{"movie_id":"kt-test-movie"}]'
        assert recorded["cwd"] == str(workdir)
        assert recorded["args"][:3] == ["codex_wp", "exec", "--skip-git-repo-check"]
        assert recorded["args"][-1] == INSTRUCTION

    def test_cognize_rejects_raw_movie_array(self, monkeypatch, tmp_path):
        from main import cognize

        movies_file = tmp_path / "movies.json"
        movies_file.write_text(json.dumps(sample_movies()), encoding="utf-8")

        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes: {}\ndislikes: {}\n", encoding="utf-8")

        agent = {
            "name": "mock",
            "cmd": "mock",
            "run_args": [],
            "timeout": 10,
            "file_mode": "cwd",
            "supports_web_search": False,
        }
        monkeypatch.setattr("main.select_agent_chain", lambda *args, **kwargs: [agent])
        monkeypatch.setattr(
            "main.call_agent",
            lambda *args, **kwargs: json.dumps(
                [
                    {
                        "movie_id": "kt-test-movie",
                        "relevance_score": 80,
                        "recommendation": "recommended",
                        "reasoning": "raw array accepted",
                        "key_matches": ["drama"],
                        "red_flags": [],
                    }
                ]
            ),
        )

        with pytest.raises(ValueError, match="movie-schedule"):
            cognize(str(movies_file), str(taste_file), agent_name="auto")

    def test_cognize_agent_failure_raises(self, monkeypatch, tmp_path):
        from main import cognize

        movies_file = tmp_path / "movies.json"
        movies_file.write_text(json.dumps(sample_schedule_input()), encoding="utf-8")

        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes: {}\ndislikes: {}\n", encoding="utf-8")

        def no_agent(*args, **kwargs):
            raise RuntimeError("No AI agent available")

        monkeypatch.setattr("main.select_agent_chain", no_agent)

        with pytest.raises(RuntimeError, match="No AI agent available"):
            cognize(str(movies_file), str(taste_file))

    def test_cli_positional_args(self, monkeypatch, tmp_path):
        movies_file = tmp_path / "movies.json"
        movies_file.write_text(json.dumps(sample_schedule_input()), encoding="utf-8")

        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes: {}\ndislikes: {}\n", encoding="utf-8")

        output_file = tmp_path / "out.json"

        monkeypatch.setattr(
            "main.cognize",
            lambda *args, **kwargs: sample_analysis_result(agent_name="mock"),
        )
        monkeypatch.setattr("main.enforce_output", lambda payload: payload)
        monkeypatch.setattr(
            "main.sys.argv",
            [
                "ct-cognize",
                str(movies_file),
                str(taste_file),
                "--output",
                str(output_file),
            ],
        )

        assert cli_main() == 0

        payload = json.loads(output_file.read_text(encoding="utf-8"))
        assert payload["meta"]["agent"] == "mock"

    def test_cli_accepts_at_prefixed_paths(self, monkeypatch, tmp_path):
        movies_file = tmp_path / "movies.json"
        movies_file.write_text(json.dumps(sample_schedule_input()), encoding="utf-8")

        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes: {}\ndislikes: {}\n", encoding="utf-8")

        output_file = tmp_path / "out.json"

        monkeypatch.setattr(
            "main.cognize",
            lambda *args, **kwargs: sample_analysis_result(agent_name="mock"),
        )
        monkeypatch.setattr("main.enforce_output", lambda payload: payload)
        monkeypatch.setattr(
            "main.sys.argv",
            [
                "ct-cognize",
                f"@{movies_file}",
                f"@{taste_file}",
                "--output",
                str(output_file),
            ],
        )

        assert cli_main() == 0

        payload = json.loads(output_file.read_text(encoding="utf-8"))
        assert payload["meta"]["agent"] == "mock"

    def test_cognize_rejects_invalid_contract_before_preflight(self, monkeypatch, tmp_path):
        from main import cognize

        movies_file = tmp_path / "invalid.json"
        movies_file.write_text(json.dumps({"movies": sample_movies()}), encoding="utf-8")

        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes: {}\ndislikes: {}\n", encoding="utf-8")

        called = {"preflight": False}

        def fail_if_called(*args, **kwargs):
            called["preflight"] = True
            raise AssertionError("select_agent_chain must not run before input contract validation")

        monkeypatch.setattr("main.select_agent_chain", fail_if_called)

        with pytest.raises(ValueError, match="Contract violation"):
            cognize(str(movies_file), str(taste_file), agent_name="auto")

        assert called["preflight"] is False

    def test_cli_stdin_mode_keeps_stdout_json_only(self, monkeypatch, tmp_path, capsys):
        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes: {}\ndislikes: {}\n", encoding="utf-8")

        mock_agent = {
            "name": "mock",
            "cmd": "mock",
            "run_args": [],
            "timeout": 10,
            "file_mode": "cwd",
            "supports_web_search": False,
        }

        monkeypatch.setattr("main.select_agent_chain", lambda *args, **kwargs: [mock_agent])
        monkeypatch.setattr(
            "main.call_agent",
            lambda *args, **kwargs: json.dumps(
                [
                    {
                        "movie_id": "kt-test-movie",
                        "relevance_score": 82,
                        "recommendation": "recommended",
                        "reasoning": "stdin mode",
                        "key_matches": ["drama"],
                        "red_flags": [],
                    }
                ]
            ),
        )
        monkeypatch.setattr("main.sys.stdin", io.StringIO(json.dumps(sample_schedule_input())))
        monkeypatch.setattr(
            "main.sys.argv",
            [
                "ct-cognize",
                "--input",
                "-",
                "--taste",
                str(taste_file),
                "--quiet",
            ],
        )

        code = cli_main()
        captured = capsys.readouterr()

        assert code == 0
        payload = json.loads(captured.out)
        assert payload["meta"]["agent"] == "mock"
        assert captured.err == ""

    def test_cli_invalid_agents_exit_code(self, monkeypatch, tmp_path):
        movies_file = tmp_path / "movies.json"
        movies_file.write_text(json.dumps(sample_schedule_input()), encoding="utf-8")

        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes: {}\ndislikes: {}\n", encoding="utf-8")

        monkeypatch.setattr(
            "main.sys.argv",
            [
                "ct-cognize",
                "--input",
                str(movies_file),
                "--taste",
                str(taste_file),
                "--agents",
                "pi,unknown",
            ],
        )

        assert cli_main() == 2

    def test_cli_unreadable_taste_file_exit_code(self, monkeypatch, tmp_path, capsys):
        movies_file = tmp_path / "movies.json"
        movies_file.write_text(json.dumps(sample_schedule_input()), encoding="utf-8")

        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes: {}\ndislikes: {}\n", encoding="utf-8")
        taste_file.chmod(0)

        monkeypatch.setattr("main.select_agent_chain", lambda *args, **kwargs: [{"name": "mock"}])
        monkeypatch.setattr(
            "main.sys.argv",
            [
                "ct-cognize",
                "--input",
                str(movies_file),
                "--taste",
                str(taste_file),
                "--agent",
                "pi",
            ],
        )

        try:
            code = cli_main()
        finally:
            taste_file.chmod(0o600)

        captured = capsys.readouterr()
        assert code == 3
        assert "Cannot read taste profile" in captured.err

    def test_cli_output_path_error_exit_code(self, monkeypatch, tmp_path):
        movies_file = tmp_path / "movies.json"
        movies_file.write_text(json.dumps(sample_schedule_input()), encoding="utf-8")

        taste_file = tmp_path / "taste.yaml"
        taste_file.write_text("likes: {}\ndislikes: {}\n", encoding="utf-8")

        bad_output = tmp_path / "missing" / "out.json"

        monkeypatch.setattr(
            "main.sys.argv",
            [
                "ct-cognize",
                "--input",
                str(movies_file),
                "--taste",
                str(taste_file),
                "--output",
                str(bad_output),
            ],
        )

        assert cli_main() == 3
