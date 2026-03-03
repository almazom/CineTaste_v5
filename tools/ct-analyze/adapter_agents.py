#!/usr/bin/env python3
"""
ct-analyze/adapter_agents.py — Multi-Agent AI Adapter (вилка)

Supports multiple agents with automatic fallback: kimi → gemini → qwen → pi

Agent Priority:
  1. kimi (preferred — web search capabilities)
  2. gemini (fallback — strong reasoning)
  3. qwen (fallback — fast reasoning)
  4. pi (fallback — fast reasoning)

Pipeline aborts if no agent is available (cognitive layer is mandatory).
"""

import json
import re
import subprocess
import shutil
import sys
import yaml
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Agent Configuration ───────────────────────────────────────────────

AGENTS = [
    {
        "name": "kimi",
        "cmd": "kimi",
        "args": ["--print", "--final-message-only", "--thinking"],
        "uses_stdin": True,
        "timeout": 300,
        "supports_web_search": True
    },
    {
        "name": "gemini",
        "cmd": "gemini",
        "args": ["--approval-mode", "plan"],
        "uses_stdin": True,
        "timeout": 120,
        "supports_web_search": False,
        "run_from_tmp": True
    },
    {
        "name": "qwen",
        "cmd": "qwen",
        "args": ["--approval-mode", "plan"],
        "uses_stdin": True,
        "timeout": 120,
        "supports_web_search": False
    },
    {
        "name": "pi",
        "cmd": "pi",
        "args": ["--print", "--no-tools", "--thinking", "high"],
        "uses_stdin": True,
        "timeout": 120,
        "supports_web_search": False
    },
]

PREFLIGHT_PROMPT = "1+1=...[ONLY NUMBER, NO WORDS]"


def preflight_check(agent: dict) -> bool:
    """Check if an agent is available and responding."""
    cmd = agent["cmd"]
    if not shutil.which(cmd):
        print(f"[preflight] {cmd} not found in PATH", file=sys.stderr)
        return False

    preflight_prompt = "1+2=...[ONLY NUMBER IN WORDS]"
    valid_responses = ["three", "три"]

    try:
        if cmd == "kimi":
            test_args = ["--print", "--final-message-only", "-p", preflight_prompt]
        elif cmd in ("gemini", "qwen"):
            test_args = ["--approval-mode", "plan", "-p", preflight_prompt]
        else:  # pi
            test_args = ["--no-tools", "-p", preflight_prompt]

        cwd = "/tmp" if agent.get("run_from_tmp") else None

        result = subprocess.run(
            [cmd] + test_args,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=cwd,
        )
        output = result.stdout.strip().lower()

        if result.returncode == 0 and output in valid_responses:
            print(f"[preflight] {cmd} ✓ ({output})", file=sys.stderr)
            return True
        else:
            print(f"[preflight] {cmd} ✗ (got: {output[:20]})", file=sys.stderr)
            return False

    except Exception as e:
        print(f"[preflight] {cmd} ✗ ({e})", file=sys.stderr)
        return False


def get_agent(name: str) -> Optional[dict]:
    """Get configured agent by name."""
    for agent in AGENTS:
        if agent["name"] == name:
            return agent
    return None


def select_agent(candidates: Optional[list[str]] = None) -> Optional[dict]:
    """Select first available agent via preflight check."""
    if candidates:
        pool = [a for a in AGENTS if a["name"] in candidates]
    else:
        pool = AGENTS

    for agent in pool:
        if preflight_check(agent):
            return agent
    return None


# ── Taste Profile ─────────────────────────────────────────────────────

def load_taste_profile(taste_path: str) -> dict:
    """Load taste profile from YAML file."""
    with open(taste_path) as f:
        return yaml.safe_load(f)


# ── Prompt Construction ────────────────────────────────────────────────

def build_prompt(movies: list, taste: dict, agent: Optional[dict] = None) -> str:
    """Build analysis prompt for AI agent."""
    agent_name = agent.get("name", "pi") if agent else "pi"

    likes = taste.get("likes", {})
    dislikes = taste.get("dislikes", {})

    instructions = """Ты — кинокритик с утонченным вкусом. Проанализируй фильмы и оцени их соответствие вкусу пользователя.

ВКУС ПОЛЬЗОВАТЕЛЯ:

Нравится:
- Режиссеры: {directors}
- Жанры: {genres}
- Ключевые слова: {keywords}

НЕ нравится:
- Жанры: {dislike_genres}
- Ключевые слова: {dislike_keywords}

ПРАВИЛА:
- Будь СТРОГ! Большинство фильмов — skip
- Канонический режиссёр (из профиля) = автоматический must_see
- Аниме = автоматический must_see
- Не угадывай по названию — исследуй каждый фильм""".format(
        directors=", ".join(likes.get("directors", [])),
        genres=", ".join(likes.get("genres", [])),
        keywords=", ".join(likes.get("keywords", [])),
        dislike_genres=", ".join(dislikes.get("genres", [])),
        dislike_keywords=", ".join(dislikes.get("keywords", [])),
    )

    if agent_name == "kimi" and agent.get("supports_web_search"):
        instructions += "\n- ИСПОЛЬЗУЙ WEB SEARCH для исследования неизвестных фильмов!"

    json_format = """
ФИЛЬМЫ ДЛЯ АНАЛИЗА:
{movies_list}

ВЕРНИ ТОЛЬКО ВАЛИДНЫЙ JSON-МАССИВ, БЕЗ MARKDOWN, БЕЗ ОБЪЯСНЕНИЙ:
[
  {{
    "movie_id": "id из списка",
    "relevance_score": 85,
    "recommendation": "must_see|recommended|maybe|skip",
    "reasoning": "Краткое объяснение 1-2 предложения",
    "key_matches": ["совпадение с профилем"],
    "red_flags": ["проблема"]
  }}
]""".format(movies_list=format_movies_for_prompt(movies))

    return instructions + json_format


def format_movies_for_prompt(movies: list) -> str:
    """Format movies list for prompt."""
    lines = []
    for i, m in enumerate(movies, 1):
        line = f"{i}. [{m.get('id', '?')}] {m.get('title', '?')}"
        if m.get("director"):
            line += f" | Реж: {m['director']}"
        if m.get("genres"):
            line += f" | Жанры: {', '.join(m['genres'])}"
        if m.get("year"):
            line += f" | {m['year']}"
        lines.append(line)
    return "\n".join(lines)


# ── Agent Invocation ───────────────────────────────────────────────────

def call_agent(prompt: str, agent: dict) -> str:
    """Call AI agent with prompt via stdin."""
    cmd = [agent["cmd"]] + agent["args"]
    timeout = agent.get("timeout", 120)
    cwd = "/tmp" if agent.get("run_from_tmp") else None

    print(f"[agent] Using {agent['name']}...", file=sys.stderr)

    try:
        result = subprocess.run(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )

        if result.returncode != 0:
            raise RuntimeError(f"{agent['name']} failed: {result.stderr[:200]}")

        return result.stdout.strip()

    except subprocess.TimeoutExpired:
        raise TimeoutError(f"{agent['name']} timeout after {timeout}s")
    except FileNotFoundError:
        raise RuntimeError(f"{agent['name']} not found: {agent['cmd']}")


def parse_ai_response(response: str) -> list:
    """Parse JSON array from AI response."""
    # Try direct JSON parse first
    try:
        data = json.loads(response)
        if isinstance(data, dict) and "analyzed" in data:
            return data["analyzed"]
        return data
    except json.JSONDecodeError:
        pass

    # Try extracting JSON array
    json_match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass

    # Try markdown code block
    code_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if code_match:
        try:
            return json.loads(code_match.group(1))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from AI response (len={len(response)})")


# ── Main API ───────────────────────────────────────────────────────────

def merge_analysis(movies: list, analyses: list, agent: dict) -> tuple[list, dict]:
    """Merge model analysis entries with movie data and build output meta."""
    movie_map = {m["id"]: m for m in movies}
    result = []

    for analysis in analyses:
        movie_id = analysis.get("movie_id")
        movie = movie_map.get(movie_id)

        # Fuzzy fallback: AI may return slightly different IDs
        if movie is None:
            for mid, m in movie_map.items():
                if mid in str(movie_id) or str(movie_id) in mid:
                    print(f"[warn] fuzzy ID match: '{movie_id}' → '{mid}'", file=sys.stderr)
                    movie = m
                    break

        if movie is None:
            print(f"[warn] no movie found for ID: '{movie_id}'", file=sys.stderr)
            movie = {}

        result.append({
            "movie": {
                "id": movie.get("id", movie_id),
                "title": movie.get("title", "Unknown"),
                "original_title": movie.get("original_title", ""),
                "director": movie.get("director", ""),
                "actors": movie.get("actors", []),
                "genres": movie.get("genres", []),
                "year": movie.get("year"),
                "source": movie.get("source", ""),
                "url": movie.get("url", "")
            },
            "relevance_score": analysis.get("relevance_score", 50),
            "confidence": 0.8 if agent["name"] == "kimi" else 0.7,
            "recommendation": analysis.get("recommendation", "maybe"),
            "reasoning": analysis.get("reasoning", ""),
            "key_matches": analysis.get("key_matches", []),
            "red_flags": analysis.get("red_flags", [])
        })

    meta = {
        "analyzer": f"agent:{agent['name']}",
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "taste_profile": "1.0",
        "agent": agent["name"],
        "web_search_used": agent.get("supports_web_search", False)
    }
    return result, meta


def analyze_with_agent(movies: list, taste: dict, agent: dict) -> tuple[list, dict]:
    """Run full analyze flow with a specific agent."""
    prompt = build_prompt(movies, taste, agent)
    response = call_agent(prompt, agent)
    analyses = parse_ai_response(response)
    return merge_analysis(movies, analyses, agent)


def analyze_movies(
    movies: list,
    taste_path: str,
    dry_run: bool = False,
    agent_name: str = "auto",
) -> tuple[list, dict]:
    """
    Analyze movies against taste profile.

    Policy:
      - dry_run=True or agent_name=dry_run -> mock output
      - agent_name=auto -> fallback chain kimi -> pi -> dry_run
      - agent_name=kimi|pi -> strict explicit mode (no fallback)
    """
    if dry_run or agent_name == "dry_run":
        return mock_analyze(movies)

    taste = load_taste_profile(taste_path)

    if agent_name == "auto":
        for agent in AGENTS:
            if not preflight_check(agent):
                continue
            try:
                return analyze_with_agent(movies, taste, agent)
            except (RuntimeError, TimeoutError, ValueError) as e:
                print(
                    f"[agent] {agent['name']} failed ({e}); trying next fallback",
                    file=sys.stderr,
                )

        print("[agent] All agents failed — aborting", file=sys.stderr)
        raise RuntimeError("No AI agent available. Pipeline cannot proceed without cognitive layer.")

    agent = get_agent(agent_name)
    if agent is None:
        raise RuntimeError(f"Unknown agent: {agent_name}")

    if not preflight_check(agent):
        raise RuntimeError(f"Requested agent unavailable: {agent_name}")

    return analyze_with_agent(movies, taste, agent)


def mock_analyze(movies: list) -> tuple[list, dict]:
    """Generate mock analysis for dry-run mode."""
    result = []

    for movie in movies[:3]:  # Only first 3 for dry-run
        score = 70 + (hash(movie.get("id", "")) % 25)
        rec = "recommended" if score >= 60 else "maybe"

        result.append({
            "movie": {
                "id": movie.get("id", ""),
                "title": movie.get("title", "Unknown"),
                "original_title": movie.get("original_title", ""),
                "director": movie.get("director", ""),
                "actors": movie.get("actors", []),
                "genres": movie.get("genres", []),
                "year": movie.get("year"),
                "source": movie.get("source", ""),
                "url": movie.get("url", "")
            },
            "relevance_score": score,
            "confidence": 0.9,
            "recommendation": rec,
            "reasoning": "Dry run — no AI analysis performed",
            "key_matches": ["dry-run"],
            "red_flags": []
        })

    meta = {
        "analyzer": "dry_run",
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "taste_profile": "1.0",
        "agent": "dry_run",
        "web_search_used": False
    }

    return result, meta


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = json.load(f)

        movies = data.get("movies", [])
        taste_path = sys.argv[2] if len(sys.argv) > 2 else "taste/profile.yaml"

        result, meta = analyze_movies(movies, taste_path, dry_run=True)
        output = {"analyzed": result, "meta": meta}
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print("Usage: python adapter_agents.py <movies.json> [taste.yaml]")
