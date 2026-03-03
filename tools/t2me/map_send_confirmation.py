#!/usr/bin/env python3
"""
Map raw `t2me send` JSON output into `send-confirmation@1.0.0`.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "_shared"))
from validate import enforce_contract  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Map raw t2me JSON output to send-confirmation contract",
    )
    parser.add_argument("--input", "-i", required=True, help="Path to raw t2me JSON")
    parser.add_argument("--output", "-o", required=True, help="Path to send-confirmation JSON")
    return parser.parse_args()


def _first_int(*values: Any) -> int | None:
    for value in values:
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def map_confirmation(raw: dict[str, Any]) -> dict[str, Any]:
    status = str(raw.get("status", "")).lower()
    success = status == "ok"

    result = raw.get("result")
    if not isinstance(result, dict):
        result = {}

    route = raw.get("route")
    if not isinstance(route, dict):
        route = {}

    message = result.get("message")
    char_count = len(message) if isinstance(message, str) else 0
    target = (
        result.get("target")
        or route.get("target_locked")
        or route.get("target")
        or ""
    )

    payload: dict[str, Any] = {
        "success": success,
        "meta": {
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "target": str(target),
            "char_count": char_count,
        },
    }

    message_id = _first_int(
        result.get("message_id"),
        result.get("id"),
        raw.get("message_id"),
    )
    if message_id is not None:
        payload["message_id"] = message_id

    if not success:
        err = raw.get("error") or result.get("error") or raw.get("message")
        payload["error"] = str(err) if err else "t2me returned non-ok status"

    return payload


def main() -> int:
    args = parse_args()

    try:
        raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Raw t2me output must be a JSON object")
    except Exception as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 4

    try:
        confirmation = map_confirmation(raw)
        enforce_contract(confirmation, "send-confirmation", "output")
    except ValueError as exc:
        print(f"Contract violation: {exc}", file=sys.stderr)
        return 4
    except Exception as exc:
        print(f"Unexpected mapping error: {exc}", file=sys.stderr)
        return 1

    Path(args.output).write_text(
        json.dumps(confirmation, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
