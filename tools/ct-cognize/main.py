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
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        "preflight_timeout": 20,
        "supports_web_search": True,
        "file_mode": "stdin",
    },
    {
        "name": "gemini",
        "cmd": "gemini",
        "preflight_args": ["-p"],
        "run_args": ["--approval-mode", "yolo"],
        "timeout": 300,
        "preflight_timeout": 20,
        "supports_web_search": False,
        "file_mode": "cwd",
    },
    {
        "name": "qwen",
        "cmd": "qwen",
        "preflight_args": ["-p"],
        "run_args": ["--approval-mode", "yolo"],
        "timeout": 300,
        "preflight_timeout": 20,
        "supports_web_search": False,
        "file_mode": "cwd",
    },
    {
        "name": "pi",
        "cmd": "pi",
        "preflight_args": [
            "--no-session",
            "--provider",
            "zai",
            "--model",
            "glm-5",
            "--thinking",
            "off",
            "--no-tools",
            "-p",
        ],
        "run_args": ["--print", "--no-tools", "--thinking", "high"],
        "timeout": 240,
        "preflight_timeout": 20,
        "supports_web_search": False,
        "file_mode": "at_file",
    },
]

AGENT_NAMES = [agent["name"] for agent in AGENTS]
AGENT_BY_NAME = {agent["name"]: agent for agent in AGENTS}

PREFLIGHT_PROMPT = "Ответь одним словом: ok. Не используй инструменты."
PREFLIGHT_OK_TOKENS = {"ok", "ок"}


# ── Preflight ──────────────────────────────────────────────────────────

def _extract_alpha_tokens(text: str) -> list[str]:
    """Extract lowercase alpha tokens from output text."""
    return re.findall(r"[a-zа-яё]+", text.lower())


def _compact_output(stdout: str, stderr: str, limit: int = 60) -> str:
    """Create short preview from command output."""
    raw = "\n".join(x for x in [stdout.strip(), stderr.strip()] if x).strip()
    if not raw:
        return "<empty>"
    raw = raw.replace("\n", " ")
    return raw[:limit]


def _run_preflight(agent: dict) -> dict:
    """Run one agent preflight probe and return structured result."""
    cmd = agent["cmd"]
    started = time.perf_counter()

    if not shutil.which(cmd):
        return {
            "agent": agent,
            "ok": False,
            "reply": "",
            "elapsed": time.perf_counter() - started,
            "error": "not found in PATH",
        }

    try:
        result = subprocess.run(
            [cmd] + agent["preflight_args"] + [PREFLIGHT_PROMPT],
            capture_output=True,
            text=True,
            timeout=agent.get("preflight_timeout", 20),
            cwd="/tmp",
        )

        preflight_tokens = _extract_alpha_tokens(
            "\n".join(x for x in [result.stdout, result.stderr] if x)
        )
        token = next((t for t in preflight_tokens if t in PREFLIGHT_OK_TOKENS), "")
        if not token and preflight_tokens:
            token = preflight_tokens[-1]

        ok = result.returncode == 0 and any(
            t in PREFLIGHT_OK_TOKENS for t in preflight_tokens
        )

        if ok:
            error = ""
        else:
            error = f"got: {_compact_output(result.stdout, result.stderr)}"

        return {
            "agent": agent,
            "ok": ok,
            "reply": token,
            "elapsed": time.perf_counter() - started,
            "error": error,
        }

    except subprocess.TimeoutExpired:
        return {
            "agent": agent,
            "ok": False,
            "reply": "",
            "elapsed": time.perf_counter() - started,
            "error": f"preflight timeout after {agent.get('preflight_timeout', 20)}s",
        }
    except Exception as e:
        return {
            "agent": agent,
            "ok": False,
            "reply": "",
            "elapsed": time.perf_counter() - started,
            "error": str(e),
        }


def _log_preflight(result: dict) -> None:
    """Emit standardized preflight log line."""
    name = result["agent"]["name"]
    if result["ok"]:
        print(f"[preflight] {name} ✓ ({result['reply']} in {result['elapsed']:.2f}s)", file=sys.stderr)
    else:
        print(f"[preflight] {name} ✗ ({result['error']})", file=sys.stderr)


def preflight_check(agent: dict) -> bool:
    """Backward-compatible single-agent preflight check."""
    result = _run_preflight(agent)
    _log_preflight(result)
    return result["ok"]


def parallel_preflight(candidates: list[dict]) -> list[dict]:
    """Run preflight checks in parallel; return results in completion order."""
    if not candidates:
        return []

    results = []
    with ThreadPoolExecutor(max_workers=len(candidates)) as executor:
        futures = [executor.submit(_run_preflight, agent) for agent in candidates]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            _log_preflight(result)

    return results


def parse_agent_list(spec: str) -> list[str]:
    """Parse comma-separated agent list preserving order and removing duplicates."""
    raw_items = [item.strip().lower() for item in spec.split(",")]
    names = [item for item in raw_items if item]
    if not names:
        raise RuntimeError("Empty --agents list. Example: --agents pi,qwen,gemini")

    unknown = [name for name in names if name not in AGENT_BY_NAME]
    if unknown:
        raise RuntimeError(
            f"Unknown agent(s): {', '.join(unknown)}. Known: {', '.join(AGENT_NAMES)}"
        )

    unique_names = []
    seen = set()
    for name in names:
        if name not in seen:
            seen.add(name)
            unique_names.append(name)

    return unique_names


def select_named_agent_chain(names: list[str]) -> list[dict]:
    """Select user-defined ordered fallback chain from --agents."""
    available = []
    unavailable = []

    for name in names:
        agent = AGENT_BY_NAME[name]
        result = _run_preflight(agent)
        _log_preflight(result)
        if result["ok"]:
            available.append(agent)
        else:
            unavailable.append(name)

    if unavailable:
        print(
            f"[cognize] requested agents unavailable: {', '.join(unavailable)}",
            file=sys.stderr,
        )

    if not available:
        raise RuntimeError(
            f"No requested AI agent available from --agents: {', '.join(names)}"
        )

    return available


def select_agent_chain(name: str = "auto", custom_names: list[str] | None = None) -> list[dict]:
    """
    Select ordered agent chain.

    - explicit agent: strict mode, one-element list if preflight passes
    - auto: parallel race, ordered by first successful response
    - custom_names: user-defined ordered fallback chain from --agents
    """
    if custom_names is not None:
        return select_named_agent_chain(custom_names)

    if name != "auto":
        for agent in AGENTS:
            if agent["name"] == name:
                if not preflight_check(agent):
                    raise RuntimeError(f"Requested agent unavailable: {name}")
                return [agent]
        raise RuntimeError(f"Unknown agent: {name}")

    results = parallel_preflight(AGENTS)
    available = [r["agent"] for r in results if r["ok"]]

    if not available:
        raise RuntimeError("No AI agent available. Cognitive layer cannot proceed.")

    return available


def select_agent(name: str = "auto") -> dict:
    """Compatibility helper: return the first selected agent."""
    return select_agent_chain(name)[0]


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

    try:
        if mode == "cwd":
            result = subprocess.run(
                cmd_base + ["-p", INSTRUCTION],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=workdir,
            )

        elif mode == "at_file":
            result = subprocess.run(
                cmd_base + [f"@{taste_path}", f"@{movies_path}"],
                input=INSTRUCTION,
                capture_output=True,
                text=True,
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
                cmd_base,
                input=full_prompt,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        else:
            raise RuntimeError(f"Unknown file_mode: {mode}")

    except subprocess.TimeoutExpired:
        raise RuntimeError(f"{agent['name']} timeout after {timeout}s")
    except FileNotFoundError:
        raise RuntimeError(f"{agent['name']} not found: {agent['cmd']}")

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

def cognize(
    movies_path: str,
    taste_path: str,
    agent_name: str = "auto",
    custom_agents: list[str] | None = None,
) -> dict:
    """
    Write movies + taste to temp workdir, launch AI agent, parse and merge response.
    """
    with open(movies_path, encoding="utf-8") as f:
        input_data = json.load(f)
    if isinstance(input_data, list):
        movies = input_data
    elif isinstance(input_data, dict):
        movies = input_data.get("movies", input_data.get("scheduled", []))
    else:
        raise ValueError(
            "Invalid input JSON format: expected array of movies or object with movies/scheduled key"
        )

    agents = select_agent_chain(agent_name, custom_agents)
    strict_single = custom_agents is None and agent_name != "auto"

    workdir = tempfile.mkdtemp(prefix="ct-cognize-")
    try:
        with open(os.path.join(workdir, "movies.json"), "w", encoding="utf-8") as f:
            json.dump({"movies": movies}, f, ensure_ascii=False, indent=2)
        shutil.copy2(taste_path, os.path.join(workdir, "taste.yaml"))

        last_error = None
        for idx, agent in enumerate(agents):
            try:
                response = call_agent(agent, workdir)
                analyses = parse_response(response)
                return merge(movies, analyses, agent)

            except ValueError as e:
                last_error = e
                if strict_single:
                    raise
                remaining = len(agents) - idx - 1
                if remaining > 0:
                    print(
                        f"[cognize] {agent['name']} parse failed ({e}); trying fallback ({remaining} left)...",
                        file=sys.stderr,
                    )

            except RuntimeError as e:
                last_error = e
                if strict_single:
                    raise
                remaining = len(agents) - idx - 1
                if remaining > 0:
                    print(
                        f"[cognize] {agent['name']} failed ({e}); trying fallback ({remaining} left)...",
                        file=sys.stderr,
                    )

        if not strict_single:
            raise RuntimeError(f"All selected AI agents failed: {last_error}")

        if isinstance(last_error, ValueError):
            raise last_error
        raise RuntimeError(str(last_error) if last_error else "Cognitive analysis failed")

    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def main():
    examples = f"""Examples:
  # Positional mode (shortest form)
  ct-cognize scheduled.json taste/profile.yaml

  # Automatic preflight race + fallback
  ct-cognize --input scheduled.json --taste taste/profile.yaml

  # Force one concrete agent
  ct-cognize --input scheduled.json --taste taste/profile.yaml --agent pi

  # Ordered fallback chain for shell workflows
  ct-cognize --input scheduled.json --taste taste/profile.yaml --agents pi,qwen,gemini

  # Print available agents
  ct-cognize --list-agents

  # Alias command
  ct-cognetive scheduled.json taste/profile.yaml
"""
    parser = argparse.ArgumentParser(
        prog=os.environ.get("CT_COGNIZE_PROG", "ct-cognize"),
        description="ct-cognize — Human-level cognitive movie analysis",
        epilog=examples,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        help="Movie data JSON file (array or object with movies/scheduled; positional alternative to --input)",
    )
    parser.add_argument("taste_path", nargs="?", help="Taste profile YAML file (positional alternative to --taste)")
    parser.add_argument("--input", "-i", help="Movie data JSON file (array or object with movies/scheduled)")
    parser.add_argument("--taste", "-t", help="Taste profile YAML file")
    parser.add_argument("--output", "-o", default="-", help="Output file (default: stdout)")
    parser.add_argument("--list-agents", action="store_true", help="Print supported AI agent names and exit")
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--agent",
        "-a",
        default="auto",
        choices=["auto"] + AGENT_NAMES,
        help="Single agent mode: auto (race) or explicit agent name",
    )
    group.add_argument(
        "--agents",
        help="Comma-separated ordered fallback chain (example: pi,qwen,gemini)",
    )
    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    try:
        if args.list_agents:
            if args.verbose:
                print("name\tcmd\tmode\ttimeout\tweb_search")
                for agent in AGENTS:
                    print(
                        f"{agent['name']}\t{agent['cmd']}\t{agent['file_mode']}\t"
                        f"{agent['timeout']}\t{str(agent.get('supports_web_search', False)).lower()}"
                    )
            else:
                for name in AGENT_NAMES:
                    print(name)
            return

        def normalize_cli_path(value: str | None) -> str | None:
            """Allow optional @path syntax for convenience."""
            if not value:
                return value
            return value[1:] if value.startswith("@") else value

        input_path = normalize_cli_path(args.input or args.input_path)
        taste_path = normalize_cli_path(args.taste or args.taste_path)

        if args.input and args.input_path and args.input != args.input_path:
            parser.error("conflicting input paths: use either --input or positional <input_json>")
        if args.taste and args.taste_path and args.taste != args.taste_path:
            parser.error("conflicting taste paths: use either --taste or positional <taste_yaml>")
        if not input_path or not taste_path:
            parser.error(
                "missing required inputs: provide <input_json> <taste_yaml> or use --input/--taste"
            )
        if not os.path.isfile(input_path):
            parser.error(f"input file not found: {input_path}")
        if not os.path.isfile(taste_path):
            parser.error(f"taste profile not found: {taste_path}")

        custom_agents = parse_agent_list(args.agents) if args.agents else None

        result = cognize(input_path, taste_path, args.agent, custom_agents)

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
