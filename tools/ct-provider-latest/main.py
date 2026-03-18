#!/usr/bin/env python3
"""
ct-provider-latest/main.py — CLI Entry Point

Finds the latest local AI provider session file for a project directory.
Contract: no structured input -> provider-latest@1.0.0
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
TOOLS_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from port import enforce_output  # noqa: E402

EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_INVALID_ARGS = 2
EXIT_DATAERR = 65
EXIT_CANTCREAT = 73

PROVIDERS = ("claude", "qwen", "pi", "gemini")


def _load_tool_version() -> str:
    manifest_path = Path(__file__).with_name("MANIFEST.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return str(manifest.get("version", "unknown"))
    except Exception:
        return "unknown"


TOOL_VERSION = _load_tool_version()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog=Path(sys.argv[0]).name,
        description="Find the latest local AI provider session file for a project directory",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  ct-provider-latest
  ct-provider-latest --project-dir ~/zoo/CineTaste_v5
  ct-provider-latest --project-dir ~/zoo/CineTaste_v5 --provider pi
  ct-provider-latest --project-dir ~/zoo/CineTaste_v5 --latest
""",
    )
    parser.add_argument(
        "--project-dir",
        "-p",
        default=".",
        help="Project directory used to match provider histories (default: current working directory)",
    )
    parser.add_argument(
        "--provider",
        "-r",
        default="all",
        help="Provider to inspect: all, claude, qwen, pi, gemini",
    )
    parser.add_argument(
        "--latest",
        action="store_true",
        default=True,
        help="Return only the newest matching file per provider (currently the only supported mode)",
    )
    parser.add_argument("--output", "-o", default="-", help="Output file path (default: stdout)")
    parser.add_argument("--version", action="version", version=f"ct-provider-latest {TOOL_VERSION}")
    return parser.parse_args()


def validate_project_dir(value: str) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.exists():
        raise ValueError(f"--project-dir does not exist: {candidate}")
    if not candidate.is_dir():
        raise ValueError(f"--project-dir is not a directory: {candidate}")
    return candidate.resolve()


def parse_provider_arg(value: str) -> tuple[str, ...]:
    if value == "all":
        return PROVIDERS
    requested = [part.strip() for part in value.split(",") if part.strip()]
    if not requested:
        raise ValueError("--provider must be one of: all, claude, qwen, pi, gemini")
    invalid = [name for name in requested if name not in PROVIDERS]
    if invalid:
        supported = ", ".join(("all",) + PROVIDERS)
        raise ValueError(f"Unknown provider(s): {', '.join(invalid)}. Supported: {supported}")
    deduped: list[str] = []
    for name in requested:
        if name not in deduped:
            deduped.append(name)
    return tuple(deduped)


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def iso_from_mtime(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()


def write_output(payload: str, output_ref: str) -> None:
    if output_ref in {"-", "stdout"}:
        print(payload)
        return
    Path(output_ref).write_text(payload, encoding="utf-8")


def empty_record(provider: str, status: str, project_key: str | None = None, error: str | None = None) -> dict:
    return {
        "provider": provider,
        "status": status,
        "project_key": project_key,
        "file": None,
        "format": None,
        "session_id": None,
        "cwd": None,
        "model": None,
        "api_provider": None,
        "message_count": None,
        "last_timestamp": None,
        "mtime": None,
        "error": error,
    }


def qwen_claude_slug(project_dir: Path) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]+", "-", str(project_dir)).strip("-")
    return f"-{normalized}"


def pi_slug(project_dir: Path) -> str:
    return f"--{str(project_dir).strip('/').replace('/', '-')}--"


def sorted_by_mtime_desc(paths: Iterable[Path]) -> list[Path]:
    existing = [path for path in paths if path.is_file()]
    return sorted(existing, key=lambda path: path.stat().st_mtime, reverse=True)


def load_jsonl_objects(path: Path) -> list[dict]:
    objects: list[dict] = []
    with path.open(encoding="utf-8") as file_obj:
        for line in file_obj:
            stripped = line.strip()
            if not stripped:
                continue
            objects.append(json.loads(stripped))
    return objects


def scan_jsonl_latest(
    *,
    provider: str,
    project_dir: Path,
    project_key: str,
    preferred_dir: Path,
    fallback_root: Path,
    parser: Callable[[Path], dict],
) -> dict:
    if preferred_dir.exists():
        candidates = sorted_by_mtime_desc(preferred_dir.glob("*.jsonl"))
    else:
        candidates = []

    if not candidates and fallback_root.exists():
        candidates = sorted_by_mtime_desc(fallback_root.rglob("*.jsonl"))

    if not candidates:
        return empty_record(provider, "not_found", project_key=project_key)

    errors: list[str] = []
    for path in candidates:
        try:
            parsed = parser(path)
        except Exception as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        if parsed.get("cwd") != str(project_dir):
            continue
        parsed["project_key"] = project_key
        return parsed

    if errors:
        return empty_record(provider, "error", project_key=project_key, error="; ".join(errors[:3]))
    return empty_record(provider, "not_found", project_key=project_key)


def parse_claude_file(path: Path) -> dict:
    objects = load_jsonl_objects(path)
    cwd = None
    model = None
    session_id = path.stem
    last_timestamp = None
    message_count = 0

    for obj in objects:
        if obj.get("cwd") and cwd is None:
            cwd = obj["cwd"]
        if obj.get("sessionId"):
            session_id = obj["sessionId"]
        timestamp = obj.get("timestamp")
        if timestamp:
            last_timestamp = timestamp
        if obj.get("type") in {"user", "assistant"}:
            message_count += 1
        message = obj.get("message")
        if isinstance(message, dict) and message.get("model"):
            model = message.get("model")

    return {
        "provider": "claude",
        "status": "found",
        "project_key": None,
        "file": str(path),
        "format": "jsonl",
        "session_id": session_id,
        "cwd": cwd,
        "model": model,
        "api_provider": None,
        "message_count": message_count,
        "last_timestamp": last_timestamp,
        "mtime": iso_from_mtime(path),
        "error": None,
    }


def parse_qwen_file(path: Path) -> dict:
    objects = load_jsonl_objects(path)
    cwd = None
    model = None
    session_id = path.stem
    last_timestamp = None
    message_count = 0

    for obj in objects:
        if obj.get("cwd") and cwd is None:
            cwd = obj["cwd"]
        if obj.get("sessionId"):
            session_id = obj["sessionId"]
        timestamp = obj.get("timestamp")
        if timestamp:
            last_timestamp = timestamp
        if obj.get("type") in {"user", "assistant"}:
            message_count += 1
        if obj.get("model"):
            model = obj.get("model")
        system_payload = obj.get("systemPayload", {})
        ui_event = system_payload.get("uiEvent", {})
        if ui_event.get("model"):
            model = ui_event.get("model")

    return {
        "provider": "qwen",
        "status": "found",
        "project_key": None,
        "file": str(path),
        "format": "jsonl",
        "session_id": session_id,
        "cwd": cwd,
        "model": model,
        "api_provider": None,
        "message_count": message_count,
        "last_timestamp": last_timestamp,
        "mtime": iso_from_mtime(path),
        "error": None,
    }


def parse_pi_file(path: Path) -> dict:
    objects = load_jsonl_objects(path)
    cwd = None
    model = None
    api_provider = None
    session_id = path.stem
    last_timestamp = None
    message_count = 0

    for obj in objects:
        if obj.get("type") == "session":
            session_id = obj.get("id", session_id)
            cwd = obj.get("cwd", cwd)
        if obj.get("type") == "model_change":
            model = obj.get("modelId", model)
            api_provider = obj.get("provider", api_provider)
        if obj.get("type") == "message":
            message_count += 1
            last_timestamp = obj.get("timestamp", last_timestamp)
            payload = obj.get("message", {})
            model = payload.get("model", model)
            api_provider = payload.get("provider", api_provider)

    return {
        "provider": "pi",
        "status": "found",
        "project_key": None,
        "file": str(path),
        "format": "jsonl",
        "session_id": session_id,
        "cwd": cwd,
        "model": model,
        "api_provider": api_provider,
        "message_count": message_count,
        "last_timestamp": last_timestamp,
        "mtime": iso_from_mtime(path),
        "error": None,
    }


def parse_gemini_file(path: Path, project_dir: Path, project_key: str) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    messages = payload.get("messages", [])
    model = None
    for message in messages:
        candidate = message.get("model")
        if candidate:
            model = candidate
    return {
        "provider": "gemini",
        "status": "found",
        "project_key": project_key,
        "file": str(path),
        "format": "json",
        "session_id": payload.get("sessionId"),
        "cwd": str(project_dir),
        "model": model,
        "api_provider": None,
        "message_count": len(messages),
        "last_timestamp": payload.get("lastUpdated") or payload.get("startTime"),
        "mtime": iso_from_mtime(path),
        "error": None,
    }


def scan_claude(project_dir: Path) -> dict:
    root = Path.home() / ".claude" / "projects"
    project_key = qwen_claude_slug(project_dir)
    return scan_jsonl_latest(
        provider="claude",
        project_dir=project_dir,
        project_key=project_key,
        preferred_dir=root / project_key,
        fallback_root=root,
        parser=parse_claude_file,
    )


def scan_qwen(project_dir: Path) -> dict:
    root = Path.home() / ".qwen" / "projects"
    project_key = qwen_claude_slug(project_dir)
    return scan_jsonl_latest(
        provider="qwen",
        project_dir=project_dir,
        project_key=project_key,
        preferred_dir=root / project_key / "chats",
        fallback_root=root,
        parser=parse_qwen_file,
    )


def scan_pi(project_dir: Path) -> dict:
    root = Path.home() / ".pi" / "agent" / "sessions"
    project_key = pi_slug(project_dir)
    return scan_jsonl_latest(
        provider="pi",
        project_dir=project_dir,
        project_key=project_key,
        preferred_dir=root / project_key,
        fallback_root=root,
        parser=parse_pi_file,
    )


def scan_gemini(project_dir: Path) -> dict:
    history_root = Path.home() / ".gemini" / "history"
    tmp_root = Path.home() / ".gemini" / "tmp"
    if not history_root.exists():
        return empty_record("gemini", "not_found")

    for project_root_file in history_root.glob("*/.project_root"):
        try:
            stored_project_dir = project_root_file.read_text(encoding="utf-8").strip()
        except OSError as exc:
            return empty_record("gemini", "error", project_key=project_root_file.parent.name, error=str(exc))
        if stored_project_dir != str(project_dir):
            continue

        project_key = project_root_file.parent.name
        chat_dir = tmp_root / project_key / "chats"
        candidates = sorted_by_mtime_desc(chat_dir.glob("*.json")) if chat_dir.exists() else []
        if not candidates:
            return empty_record("gemini", "not_found", project_key=project_key)
        path = candidates[0]
        try:
            return parse_gemini_file(path, project_dir=project_dir, project_key=project_key)
        except Exception as exc:
            return empty_record("gemini", "error", project_key=project_key, error=str(exc))

    return empty_record("gemini", "not_found")


SCANNERS: dict[str, Callable[[Path], dict]] = {
    "claude": scan_claude,
    "qwen": scan_qwen,
    "pi": scan_pi,
    "gemini": scan_gemini,
}


def build_output(project_dir: Path, requested_providers: tuple[str, ...], latest_only: bool) -> dict:
    providers = [SCANNERS[name](project_dir) for name in requested_providers]
    return {
        "project_dir": str(project_dir),
        "providers": providers,
        "meta": {
            "scanned_at": iso_now(),
            "providers_requested": list(requested_providers),
            "providers_found": sum(1 for item in providers if item["status"] == "found"),
            "latest_only": latest_only,
        },
    }


def main() -> None:
    args = parse_args()

    try:
        project_dir = validate_project_dir(args.project_dir)
        requested_providers = parse_provider_arg(args.provider)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)

    try:
        output = build_output(
            project_dir=project_dir,
            requested_providers=requested_providers,
            latest_only=bool(args.latest),
        )
        enforce_output(output)
        payload = json.dumps(output, ensure_ascii=False, indent=2)
        write_output(payload, args.output)
        sys.exit(EXIT_OK)
    except ValueError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        sys.exit(EXIT_DATAERR)
    except OSError as exc:
        print(f"Filesystem error: {exc}", file=sys.stderr)
        sys.exit(EXIT_CANTCREAT)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(EXIT_INTERNAL)


if __name__ == "__main__":
    main()
