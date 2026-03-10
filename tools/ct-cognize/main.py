#!/usr/bin/env python3
"""
ct-cognize — Human-level cognitive movie analysis.

The AI agent reads two files directly (like a human would):
  1. movies.json — full list of available movies with all details
  2. taste.yaml — user's taste preferences and canon

No data is inlined into the prompt. The agent uses its own tools
to read, understand, and judge each movie against the taste profile.
"""

from __future__ import annotations

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
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(ROOT / "tools" / "_shared"))
from port import enforce_input, enforce_output  # noqa: E402


# ── Exit Taxonomy ───────────────────────────────────────────────────────

EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_INVALID_ARGS = 2
EXIT_PATH = 3
EXIT_AGENT = 4
EXIT_CONTRACT = 5


class CliUsageError(RuntimeError):
    """Invalid CLI usage (for example unknown values in --agents)."""


class PathError(RuntimeError):
    """Filesystem/stdin path and access problems."""


class AgentExecutionError(RuntimeError):
    """Agent preflight/runtime failures."""


class ContractError(ValueError):
    """Contract validation or JSON payload parsing failures."""


# ── Runtime Diagnostics ─────────────────────────────────────────────────

RUNTIME_DIAGNOSTICS = {
    "trace_id": "",
    "quiet": False,
    "verbose": False,
    "timings": False,
}


def _load_tool_version() -> str:
    manifest_path = ROOT / "tools" / "ct-cognize" / "MANIFEST.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return str(manifest.get("version", "unknown"))
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return "unknown"


TOOL_VERSION = _load_tool_version()


def _configure_diagnostics(trace_id: str | None, quiet: bool, verbose: bool, timings: bool) -> None:
    RUNTIME_DIAGNOSTICS["trace_id"] = (trace_id or "").strip()
    RUNTIME_DIAGNOSTICS["quiet"] = bool(quiet)
    RUNTIME_DIAGNOSTICS["verbose"] = bool(verbose)
    RUNTIME_DIAGNOSTICS["timings"] = bool(timings)


def _log(message: str, level: str = "info", channel: str = "cognize") -> None:
    if level != "error" and RUNTIME_DIAGNOSTICS["quiet"]:
        return
    if level == "debug" and not RUNTIME_DIAGNOSTICS["verbose"]:
        return

    trace_id = RUNTIME_DIAGNOSTICS["trace_id"]
    if trace_id:
        prefix = f"[{channel}][{trace_id}]"
    else:
        prefix = f"[{channel}]"
    print(f"{prefix} {message}", file=sys.stderr)


def _log_timing(name: str, started_at: float) -> None:
    if not RUNTIME_DIAGNOSTICS["timings"]:
        return
    elapsed = time.perf_counter() - started_at
    _log(f"{name} took {elapsed:.3f}s", channel="timing")


def _subprocess_env() -> dict[str, str]:
    """Force non-interactive, CI-safe defaults for agent subprocesses."""
    env = os.environ.copy()
    env.update(CONFIG["runtime"]["env"])
    return env


# ── Configuration Loader ────────────────────────────────────────────────

def _load_agent_config() -> dict:
    """Load agent configuration from external JSON file."""
    config_path = Path(__file__).parent / "agent-config.json"
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Failed to load agent-config.json: {exc}") from exc

    # Apply environment variable overrides for timeouts
    preflight_env = config["preflight"].get("timeout_env_var")
    if preflight_env:
        config["preflight"]["timeout_default"] = int(
            os.environ.get(preflight_env, config["preflight"]["timeout_default"])
        )

    runtime_env = config["runtime"].get("timeout_env_var")
    if runtime_env:
        config["runtime"]["timeout_default"] = int(
            os.environ.get(runtime_env, config["runtime"]["timeout_default"])
        )

    return config


CONFIG = _load_agent_config()
AGENTS = [a for a in CONFIG["agents"] if a.get("enabled", True)]
AGENT_NAMES = [agent["name"] for agent in AGENTS]
AGENT_BY_NAME = {agent["name"]: agent for agent in AGENTS}
PREFLIGHT_PROMPT = CONFIG["preflight"]["prompt"]
PREFLIGHT_OK_TOKENS = set(CONFIG["preflight"]["ok_tokens"])


# ── Preflight ──────────────────────────────────────────────────────────

def _extract_alpha_tokens(text: str) -> list[str]:
    """Extract lowercase alpha tokens from output text."""
    return re.findall(r"[a-zа-яё]+", text.lower())


def _compact_output(stdout: str, stderr: str, limit: int = 120) -> str:
    """Create short preview from command output."""
    raw = "\n".join(x for x in [stdout.strip(), stderr.strip()] if x).strip()
    if not raw:
        return "<empty>"
    raw = raw.replace("\n", " ")
    return raw[:limit]


def _run_preflight(agent: dict) -> dict:
    """Run one agent preflight probe and return structured result."""
    cmd = agent["cmd"]
    preflight_timeout = agent.get(
        "preflight_timeout", CONFIG["preflight"]["timeout_default"]
    )
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
            timeout=preflight_timeout,
            cwd="/tmp",
            env=_subprocess_env(),
        )
    except subprocess.TimeoutExpired:
        return {
            "agent": agent,
            "ok": False,
            "reply": "",
            "elapsed": time.perf_counter() - started,
            "error": f"preflight timeout after {preflight_timeout}s",
        }
    except Exception as exc:
        return {
            "agent": agent,
            "ok": False,
            "reply": "",
            "elapsed": time.perf_counter() - started,
            "error": str(exc),
        }

    preflight_tokens = _extract_alpha_tokens(
        "\n".join(x for x in [result.stdout, result.stderr] if x)
    )
    token = next((t for t in preflight_tokens if t in PREFLIGHT_OK_TOKENS), "")
    if not token and preflight_tokens:
        token = preflight_tokens[-1]

    ok = result.returncode == 0 and any(
        t in PREFLIGHT_OK_TOKENS for t in preflight_tokens
    )
    error = "" if ok else f"got: {_compact_output(result.stdout, result.stderr)}"

    return {
        "agent": agent,
        "ok": ok,
        "reply": token,
        "elapsed": time.perf_counter() - started,
        "error": error,
    }


def _log_preflight(result: dict) -> None:
    """Emit standardized preflight log line with transparency."""
    name = result["agent"]["name"]
    cmd = result["agent"]["cmd"]
    model = result["agent"].get("preflight_args", [])
    model_str = ""
    for i, arg in enumerate(model):
        if arg == "--model" and i + 1 < len(model):
            model_str = f" model={model[i+1]}"
            break
    if result["ok"]:
        _log(f"{name}{model_str} → ok ({result['reply']} in {result['elapsed']:.2f}s)", channel="preflight")
    else:
        _log(f"{name}{model_str} → fail ({result['error']})", channel="preflight")


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
        raise CliUsageError("Empty --agents list. Example: --agents pi,qwen,gemini")

    unknown = [name for name in names if name not in AGENT_BY_NAME]
    if unknown:
        raise CliUsageError(
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
        _log(f"requested agents unavailable: {', '.join(unavailable)}")

    if not available:
        raise AgentExecutionError(
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
                    raise AgentExecutionError(f"Requested agent unavailable: {name}")
                return [agent]
        raise CliUsageError(f"Unknown agent: {name}")

    results = parallel_preflight(AGENTS)
    available = [result["agent"] for result in results if result["ok"]]

    if not available:
        raise AgentExecutionError("No AI agent available. Cognitive layer cannot proceed.")

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
    timeout = agent.get("timeout", CONFIG["runtime"]["timeout_default"])
    mode = agent["file_mode"]
    movies_path = os.path.join(workdir, "movies.json")
    taste_path = os.path.join(workdir, "taste.yaml")
    started = time.perf_counter()

    # Extract model info for transparency
    model_info = ""
    run_args = agent.get("run_args", [])
    for i, arg in enumerate(run_args):
        if arg == "--model" and i + 1 < len(run_args):
            model_info = f" model={run_args[i+1]}"
            break

    _log(f"using {agent['name']}{model_info} ({mode} mode, timeout={timeout}s)")

    try:
        if mode == "cwd":
            result = subprocess.run(
                cmd_base + ["-p", INSTRUCTION],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=workdir,
                env=_subprocess_env(),
            )

        elif mode == "at_file":
            result = subprocess.run(
                cmd_base + [f"@{taste_path}", f"@{movies_path}"],
                input=INSTRUCTION,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=_subprocess_env(),
            )

        elif mode == "stdin":
            with open(movies_path, encoding="utf-8") as handle:
                movies_text = handle.read()
            with open(taste_path, encoding="utf-8") as handle:
                taste_text = handle.read()
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
                env=_subprocess_env(),
            )
        else:
            raise AgentExecutionError(f"Unknown file_mode: {mode}")
    except subprocess.TimeoutExpired as exc:
        raise AgentExecutionError(f"{agent['name']} timeout after {timeout}s") from exc
    except FileNotFoundError as exc:
        raise AgentExecutionError(f"{agent['name']} not found: {agent['cmd']}") from exc
    finally:
        _log_timing(f"agent.{agent['name']}", started)

    if result.returncode != 0:
        preview = _compact_output(result.stdout, result.stderr)
        raise AgentExecutionError(f"{agent['name']} failed (exit {result.returncode}): {preview}")

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
    ok, data = _try_json_load(response)
    if ok:
        return data if isinstance(data, list) else [data]

    match = re.search(r'\[\s*\{.*\}\s*\]', response, re.DOTALL)
    if match:
        ok, data = _try_json_load(match.group())
        if ok:
            return data

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

    for mid, item in movie_map.items():
        if mid in str(movie_id) or str(movie_id) in mid:
            _log(f"fuzzy ID match: '{movie_id}' -> '{mid}'", channel="warn")
            return item

    _log(f"no movie found for ID: '{movie_id}'", channel="warn")
    return {}


def merge(movies: list, analyses: list, agent: dict) -> dict:
    """Merge AI analyses with original movie data into analysis-result contract."""
    movie_map = {movie["id"]: movie for movie in movies}
    analyzed = []

    for analysis in analyses:
        movie_id = analysis.get("movie_id")
        movie = _find_movie(movie_id, movie_map)

        analyzed.append(
            {
                "movie": {
                    "id": movie.get("id", movie_id),
                    "title": movie.get("title", "Unknown"),
                    "original_title": movie.get("original_title", ""),
                    "director": movie.get("director", ""),
                    "actors": movie.get("actors", []),
                    "genres": movie.get("genres", []),
                    "year": movie.get("year"),
                    "source": movie.get("source", ""),
                    "url": movie.get("url", ""),
                },
                "relevance_score": analysis.get("relevance_score", 50),
                "confidence": 0.8,
                "recommendation": analysis.get("recommendation", "maybe"),
                "reasoning": analysis.get("reasoning", ""),
                "key_matches": analysis.get("key_matches", []),
                "red_flags": analysis.get("red_flags", []),
            }
        )

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


def _log_fallback_attempt(agent_name: str, error: Exception, remaining: int) -> None:
    """Log fallback transition after runtime failure or parse error."""
    if remaining <= 0:
        return

    status = "parse failed" if isinstance(error, ValueError) else "failed"
    _log(f"{agent_name} {status} ({error}); trying fallback ({remaining} left)...")


# ── Input/Output helpers ───────────────────────────────────────────────

def normalize_cli_path(value: str | None) -> str | None:
    """Allow optional @path syntax for convenience."""
    if value is None:
        return None
    if value == "-":
        return value
    return value[1:] if value.startswith("@") else value


def _read_json_payload(input_path: str) -> Any:
    if input_path == "-":
        raw = sys.stdin.read()
        if not raw.strip():
            raise PathError("stdin is empty; expected movie-schedule JSON payload")
        source = "stdin"
    else:
        try:
            raw = Path(input_path).read_text(encoding="utf-8")
        except OSError as exc:
            raise PathError(f"Cannot read input file '{input_path}': {exc}") from exc
        source = input_path

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContractError(
            f"Invalid JSON in {source}: line {exc.lineno}, column {exc.colno} ({exc.msg})"
        ) from exc


def _load_schedule_payload(input_path: str) -> dict:
    payload = _read_json_payload(input_path)
    if not isinstance(payload, dict):
        raise ContractError("Input payload must be a movie-schedule object with movies/meta")

    try:
        enforce_input(payload)
    except ValueError as exc:
        raise ContractError(str(exc)) from exc

    return payload


def _validate_fs_paths(input_path: str, taste_path: str, output_path: str) -> None:
    if input_path != "-" and not Path(input_path).is_file():
        raise PathError(f"input file not found: {input_path}")

    if not Path(taste_path).is_file():
        raise PathError(f"taste profile not found: {taste_path}")

    if output_path == "-":
        return

    target = Path(output_path)
    if target.exists() and target.is_dir():
        raise PathError(f"output path is a directory: {output_path}")

    parent = target.parent if str(target.parent) else Path(".")
    if not parent.exists():
        raise PathError(f"output directory not found: {parent}")
    if not parent.is_dir():
        raise PathError(f"output parent is not a directory: {parent}")


def _write_output(output_path: str, payload: str) -> None:
    if output_path == "-":
        print(payload)
        return

    try:
        Path(output_path).write_text(payload, encoding="utf-8")
    except OSError as exc:
        raise PathError(f"Cannot write output file '{output_path}': {exc}") from exc


# ── Main ───────────────────────────────────────────────────────────────

def cognize(
    schedule_input: dict | str,
    taste_path: str,
    agent_name: str = "auto",
    custom_agents: list[str] | None = None,
) -> dict:
    """
    Validate movie-schedule input, launch AI agent(s), parse and merge response.
    """
    if isinstance(schedule_input, dict):
        payload = schedule_input
        try:
            enforce_input(payload)
        except ValueError as exc:
            raise ContractError(str(exc)) from exc
    else:
        payload = _load_schedule_payload(str(schedule_input))

    movies = payload.get("movies", [])

    agents = select_agent_chain(agent_name, custom_agents)
    strict_single = custom_agents is None and agent_name != "auto"

    workdir = tempfile.mkdtemp(prefix="ct-cognize-")
    try:
        with open(os.path.join(workdir, "movies.json"), "w", encoding="utf-8") as handle:
            json.dump({"movies": movies}, handle, ensure_ascii=False, indent=2)
        try:
            shutil.copy2(taste_path, os.path.join(workdir, "taste.yaml"))
        except OSError as exc:
            raise PathError(f"Cannot read taste profile '{taste_path}': {exc}") from exc

        last_error: Exception | None = None
        for idx, agent in enumerate(agents):
            try:
                response = call_agent(agent, workdir)
                analyses = parse_response(response)
                return merge(movies, analyses, agent)
            except (AgentExecutionError, RuntimeError) as error:
                last_error = AgentExecutionError(str(error))
                if strict_single:
                    raise last_error
            except ValueError as error:
                last_error = ContractError(str(error))
                if strict_single:
                    raise ContractError(str(error)) from error

            remaining = len(agents) - idx - 1
            _log_fallback_attempt(agent["name"], last_error, remaining)

        if isinstance(last_error, ContractError):
            raise last_error
        if isinstance(last_error, AgentExecutionError):
            raise AgentExecutionError(f"All selected AI agents failed: {last_error}")
        raise AgentExecutionError("Cognitive analysis failed")
    finally:
        shutil.rmtree(workdir, ignore_errors=True)


def _build_parser() -> argparse.ArgumentParser:
    examples = """Examples:
  # Positional mode (shortest form)
  ct-cognize scheduled.json taste/profile.yaml

  # Read input from stdin
  cat scheduled.json | ct-cognize --input - --taste taste/profile.yaml

  # Automatic preflight race + fallback
  ct-cognize --input scheduled.json --taste taste/profile.yaml

  # Force one concrete agent
  ct-cognize --input scheduled.json --taste taste/profile.yaml --agent pi

  # Ordered fallback chain for shell workflows
  ct-cognize --input scheduled.json --taste taste/profile.yaml --agents pi,qwen,gemini

  # Print available agents
  ct-cognize --list-agents
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
        help="movie-schedule JSON file path (or '-' for stdin)",
    )
    parser.add_argument(
        "taste_path",
        nargs="?",
        help="Taste profile YAML file (positional alternative to --taste)",
    )
    parser.add_argument("--input", "-i", help="movie-schedule JSON file path (or '-' for stdin)")
    parser.add_argument("--taste", "-t", help="Taste profile YAML file")
    parser.add_argument("--output", "-o", default="-", help="Output file (default: stdout)")
    parser.add_argument("--list-agents", action="store_true", help="Print supported AI agent names and exit")
    parser.add_argument("--version", action="version", version=f"%(prog)s {TOOL_VERSION}")
    parser.add_argument("--trace-id", help="Trace ID for stderr diagnostics correlation")
    parser.add_argument("--timings", action="store_true", help="Emit stage timing diagnostics to stderr")

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

    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument("--quiet", "-q", action="store_true", help="Suppress non-error stderr diagnostics")
    verbosity.add_argument("--verbose", "-v", action="store_true", help="Verbose stderr diagnostics")

    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    started = time.perf_counter()

    _configure_diagnostics(
        trace_id=args.trace_id,
        quiet=args.quiet,
        verbose=args.verbose,
        timings=args.timings,
    )

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
            return EXIT_OK

        input_path = normalize_cli_path(args.input or args.input_path)
        taste_path = normalize_cli_path(args.taste or args.taste_path)

        if args.input and args.input_path and args.input != args.input_path:
            raise CliUsageError("conflicting input paths: use either --input or positional <input_json>")
        if args.taste and args.taste_path and args.taste != args.taste_path:
            raise CliUsageError("conflicting taste paths: use either --taste or positional <taste_yaml>")
        if not input_path or not taste_path:
            raise CliUsageError("missing required inputs: provide <input_json> <taste_yaml> or use --input/--taste")

        _validate_fs_paths(input_path, taste_path, args.output)
        custom_agents = parse_agent_list(args.agents) if args.agents else None

        result = cognize(input_path, taste_path, args.agent, custom_agents)
        try:
            enforce_output(result)
        except ValueError as exc:
            raise ContractError(str(exc)) from exc

        output = json.dumps(result, ensure_ascii=False, indent=2)
        _write_output(args.output, output)

        count = len(result["analyzed"])
        _log(f"{count} movies analyzed by {result['meta']['agent']}")
        _log_timing("total", started)
        return EXIT_OK

    except CliUsageError as exc:
        _log(f"Argument error: {exc}", level="error")
        return EXIT_INVALID_ARGS
    except PathError as exc:
        _log(f"Path error: {exc}", level="error")
        return EXIT_PATH
    except AgentExecutionError as exc:
        _log(f"Agent error: {exc}", level="error")
        return EXIT_AGENT
    except ContractError as exc:
        _log(f"Contract error: {exc}", level="error")
        return EXIT_CONTRACT
    except Exception as exc:
        _log(f"Internal error: {exc}", level="error")
        return EXIT_INTERNAL


if __name__ == "__main__":
    sys.exit(main())
