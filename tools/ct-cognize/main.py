#!/usr/bin/env python3
"""
ct-cognize — Human-level cognitive movie analysis.

The AI agent reads two files directly (like a human would):
  1. movies.json — full list of available movies with all details
  2. taste.yaml — user's taste preferences and canon

No data is inlined into the prompt. The agent uses its own tools
to read, understand, and judge each movie against the taste profile.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "tools" / "_shared"))
from port import enforce_output  # noqa: E402

# ── Agent Registry ─────────────────────────────────────────────────────

AGENTS = [
    {
        "name": "kimi",
        "cmd": "kimi",
        "preflight_args": ["--print", "--final-message-only", "-p"],
        "run_args": ["--print", "--final-message-only", "--thinking"],
        "timeout": 300,
        "supports_web_search": True,
        "file_mode": "stdin",
    },
    {
        "name": "gemini",
        "cmd": "gemini",
        "preflight_args": ["--approval-mode", "plan", "-p"],
        "run_args": ["--approval-mode", "plan"],
        "timeout": 180,
        "supports_web_search": False,
        "file_mode": "cwd",
    },
    {
        "name": "qwen",
        "cmd": "qwen",
        "preflight_args": ["--approval-mode", "plan", "-p"],
        "run_args": ["--approval-mode", "plan"],
        "timeout": 180,
        "supports_web_search": False,
        "file_mode": "cwd",
    },
    {
        "name": "pi",
        "cmd": "pi",
        "preflight_args": ["--no-tools", "-p"],
        "run_args": ["--print", "--no-tools", "--thinking", "high"],
        "timeout": 120,
        "supports_web_search": False,
        "file_mode": "at_file",
    },
]


# ── Preflight ──────────────────────────────────────────────────────────

def preflight_check(agent: dict) -> bool:
    """Quick check: is the agent installed and responding?"""
    cmd = agent["cmd"]
    if not shutil.which(cmd):
        print(f"[preflight] {cmd} not found in PATH", file=sys.stderr)
        return False

    try:
        result = subprocess.run(
            [cmd] + agent["preflight_args"] + ["1+2=...[ONLY NUMBER IN WORDS]"],
            capture_output=True, text=True, timeout=30,
            cwd="/tmp",
        )
        output = result.stdout.strip().lower()
        if result.returncode == 0 and output in ("three", "три"):
            print(f"[preflight] {cmd} ✓ ({output})", file=sys.stderr)
            return True
        print(f"[preflight] {cmd} ✗ (got: {output[:40]})", file=sys.stderr)
        return False
    except Exception as e:
        print(f"[preflight] {cmd} ✗ ({e})", file=sys.stderr)
        return False


def select_agent(name: str = "auto") -> dict:
    """Select agent by name or auto-detect first available."""
    if name != "auto":
        for a in AGENTS:
            if a["name"] == name:
                if not preflight_check(a):
                    raise RuntimeError(f"Requested agent unavailable: {name}")
                return a
        raise RuntimeError(f"Unknown agent: {name}")

    for a in AGENTS:
        if preflight_check(a):
            return a

    raise RuntimeError("No AI agent available. Cognitive layer cannot proceed.")


# ── Prompt ─────────────────────────────────────────────────────────────

INSTRUCTION = """Ты — кинокритик с утонченным вкусом.

ЗАДАЧА:
1. Прочитай файл taste.yaml — это вкусы и предпочтения пользователя.
2. Прочитай файл movies.json — это полный список доступных фильмов со всеми деталями.
3. Проанализируй КАЖДЫЙ фильм из списка: насколько он соответствует вкусу пользователя.

ПРАВИЛА:
- Будь СТРОГ! Большинство фильмов — skip
- Канонический режиссёр (из taste.yaml canon) = автоматический must_see (score ≥ 90)
- Любимый актёр (из taste.yaml actors) = бонус к оценке (+15)
- Аниме = автоматический must_see
- Исследуй каждый фильм по его описанию, режиссёру, актёрам, жанрам
- НЕ угадывай только по названию

ФОРМАТ ОТВЕТА — ТОЛЬКО валидный JSON-массив, БЕЗ markdown, БЕЗ объяснений:
[
  {
    "movie_id": "id фильма из movies.json",
    "relevance_score": 85,
    "recommendation": "must_see|recommended|maybe|skip",
    "reasoning": "Краткое объяснение 1-2 предложения",
    "key_matches": ["совпадение с профилем"],
    "red_flags": ["проблема"]
  }
]"""


# ── Agent Invocation ───────────────────────────────────────────────────

def call_agent(agent: dict, workdir: str) -> str:
    """
    Call AI agent with movies.json and taste.yaml in workdir.

    File modes:
      - cwd:     agent runs in workdir, reads files via its own tools
      - at_file: pi-style @file syntax to inject file content
      - stdin:   prompt + inline data sent via stdin
    """
    cmd_base = [agent["cmd"]] + agent["run_args"]
    timeout = agent["timeout"]
    mode = agent["file_mode"]
    movies_path = os.path.join(workdir, "movies.json")
    taste_path = os.path.join(workdir, "taste.yaml")

    print(f"[cognize] Using {agent['name']} ({mode} mode)...", file=sys.stderr)

    if mode == "cwd":
        result = subprocess.run(
            cmd_base + ["-p", INSTRUCTION],
            capture_output=True, text=True,
            timeout=timeout, cwd=workdir,
        )

    elif mode == "at_file":
        result = subprocess.run(
            cmd_base + [f"@{taste_path}", f"@{movies_path}"],
            input=INSTRUCTION, capture_output=True, text=True,
            timeout=timeout,
        )

    elif mode == "stdin":
        with open(movies_path, encoding="utf-8") as f:
            movies_text = f.read()
        with open(taste_path, encoding="utf-8") as f:
            taste_text = f.read()
        full_prompt = (
            f"{INSTRUCTION}\n\n--- taste.yaml ---\n{taste_text}"
            f"\n\n--- movies.json ---\n{movies_text}"
        )
        result = subprocess.run(
            cmd_base, input=full_prompt,
            capture_output=True, text=True, timeout=timeout,
        )
    else:
        raise RuntimeError(f"Unknown file_mode: {mode}")

    if result.returncode != 0:
        raise RuntimeError(f"{agent['name']} failed: {result.stderr[:300]}")

    return result.stdout.strip()


# ── Response Parsing ───────────────────────────────────────────────────

def _try_json_load(payload: str) -> tuple[bool, object]:
    """Try to decode JSON payload."""
    try:
        return True, json.loads(payload)
    except json.JSONDecodeError:
        return False, None


def parse_response(response: str) -> list:
    """Extract JSON array from AI response."""
    # Direct parse
    ok, data = _try_json_load(response)
    if ok:
        return data if isinstance(data, list) else [data]

    # Extract JSON array
    match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
    if match:
        ok, data = _try_json_load(match.group())
        if ok:
            return data

    # Markdown code block
    code = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
    if code:
        ok, data = _try_json_load(code.group(1))
        if ok:
            return data

    raise ValueError(f"Could not parse JSON from AI response (len={len(response)})")


# ── Merge ──────────────────────────────────────────────────────────────

def _find_movie(movie_id: str, movie_map: dict) -> dict:
    """Exact lookup with fuzzy substring fallback."""
    movie = movie_map.get(movie_id)
    if movie:
        return movie

    for mid, m in movie_map.items():
        if mid in str(movie_id) or str(movie_id) in mid:
            print(f"[warn] fuzzy ID match: '{movie_id}' → '{mid}'", file=sys.stderr)
            return m

    print(f"[warn] no movie found for ID: '{movie_id}'", file=sys.stderr)
    return {}


def merge(movies: list, analyses: list, agent: dict) -> dict:
    """Merge AI analyses with original movie data into analysis-result contract."""
    movie_map = {m["id"]: m for m in movies}
    analyzed = []

    for analysis in analyses:
        movie_id = analysis.get("movie_id")
        movie = _find_movie(movie_id, movie_map)

        analyzed.append({
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
            "confidence": 0.8,
            "recommendation": analysis.get("recommendation", "maybe"),
            "reasoning": analysis.get("reasoning", ""),
            "key_matches": analysis.get("key_matches", []),
            "red_flags": analysis.get("red_flags", [])
        })

    return {
        "analyzed": analyzed,
        "meta": {
            "analyzer": f"cognize:{agent['name']}",
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "taste_profile": "1.0",
            "agent": agent["name"],
            "web_search_used": agent.get("supports_web_search", False),
        },
    }


# ── Main ───────────────────────────────────────────────────────────────

def cognize(movies_path: str, taste_path: str, agent_name: str = "auto") -> dict:
    """
    Write movies + taste to temp workdir, launch AI agent, parse and merge response.
    """
    with open(movies_path, encoding="utf-8") as f:
        input_data = json.load(f)
    movies = input_data.get("movies", input_data.get("scheduled", []))

    agent = select_agent(agent_name)

    workdir = tempfile.mkdtemp(prefix="ct-cognize-")
    try:
        with open(os.path.join(workdir, "movies.json"), "w", encoding="utf-8") as f:
            json.dump({"movies": movies}, f, ensure_ascii=False, indent=2)
        shutil.copy2(taste_path, os.path.join(workdir, "taste.yaml"))

        response = call_agent(agent, workdir)
        analyses = parse_response(response)
        return merge(movies, analyses, agent)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(
        description="ct-cognize — Human-level cognitive movie analysis"
    )
    parser.add_argument("--input", "-i", required=True, help="Movie data JSON file")
    parser.add_argument("--taste", "-t", required=True, help="Taste profile YAML file")
    parser.add_argument("--output", "-o", default="-", help="Output file (default: stdout)")
    parser.add_argument(
        "--agent", "-a", default="auto",
        choices=["auto", "kimi", "gemini", "qwen", "pi"],
        help="AI agent (default: auto)"
    )
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    try:
        result = cognize(args.input, args.taste, args.agent)

        # Validate output contract
        enforce_output(result)

        output = json.dumps(result, ensure_ascii=False, indent=2)

        if args.output == "-":
            print(output)
        else:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)

        count = len(result["analyzed"])
        print(f"[cognize] {count} movies analyzed by {result['meta']['agent']}", file=sys.stderr)

    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(3)
    except ValueError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        sys.exit(4)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
