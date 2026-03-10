#!/usr/bin/env python3
"""
ct-time-price/main.py — CLI Entry Point

Fetches showtimes for one selected movie URL.
Contract: no structured input -> movie-showtimes@1.0.0
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
TOOLS_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(1, str(TOOLS_DIR / "ct-schedule"))

from adapter_showtimes import dry_run_showtimes, fetch_showtimes  # noqa: E402
from port import enforce_output  # noqa: E402

SUPPORTED_SOURCES: dict[str, Callable[[str, str], list[dict]]] = {
    "kinoteatr": fetch_showtimes,
}

EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_INVALID_ARGS = 2
EXIT_DATAERR = 65
EXIT_UNAVAILABLE = 69
EXIT_CANTCREAT = 73
EXIT_NOPERM = 77


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
        description="Fetch session times and prices for one selected movie URL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ct-time-price --url https://kinoteatr.ru/film/postoronniy-2/naberezhnie-chelni/
  ct-time-price --url https://kinoteatr.ru/film/postoronniy-2/naberezhnie-chelni/ --date 2026-03-10
  ct-time-price --url https://kinoteatr.ru/film/postoronniy-2/naberezhnie-chelni/ --dry-run
""",
    )
    parser.add_argument("--url", "-u", required=True, help="Movie page URL")
    parser.add_argument(
        "--date",
        "-d",
        default="",
        help="Schedule date: YYYY-MM-DD (default: local today)",
    )
    parser.add_argument(
        "--source",
        "-s",
        default="kinoteatr",
        help="Schedule source adapter (default: kinoteatr)",
    )
    parser.add_argument("--output", "-o", default="-", help="Output file path (default: stdout)")
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Generate deterministic mock showtimes",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--version", action="version", version=f"ct-time-price {TOOL_VERSION}")
    return parser.parse_args()


def validate_date(value: str) -> str:
    if not value:
        return datetime.now().astimezone().strftime("%Y-%m-%d")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("--date must be YYYY-MM-DD") from exc
    return value


def validate_url(value: str) -> str:
    parsed = urlparse(value)
    if not (parsed.scheme and parsed.netloc):
        raise ValueError("--url must be an absolute URI")
    return value


def resolve_source(source: str) -> Callable[[str, str], list[dict]]:
    adapter = SUPPORTED_SOURCES.get(source)
    if adapter is None:
        supported = ", ".join(sorted(SUPPORTED_SOURCES.keys()))
        raise ValueError(f"Unknown source: {source}. Supported: {supported}")
    return adapter


def build_output(movie_url: str, date_value: str, source: str, showtimes: list[dict], dry_run: bool) -> dict:
    source_name = "kinoteatr.ru" if source == "kinoteatr" else source
    return {
        "movie_url": movie_url,
        "date": date_value,
        "showtimes": showtimes,
        "meta": {
            "source": source_name,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "showtimes_count": len(showtimes),
            "dry_run": dry_run,
        },
    }


def write_output(payload: str, output_ref: str) -> None:
    if output_ref in {"-", "stdout"}:
        print(payload)
        return
    Path(output_ref).write_text(payload, encoding="utf-8")


def main() -> None:
    args = parse_args()

    try:
        movie_url = validate_url(args.url)
        date_value = validate_date(args.date)
        source_adapter = resolve_source(args.source)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(EXIT_INVALID_ARGS)

    try:
        if args.verbose:
            print(f"Resolving showtimes for {movie_url}", file=sys.stderr)
            print(f"Date: {date_value}", file=sys.stderr)
            if args.dry_run:
                print("DRY RUN: Generating mock showtimes", file=sys.stderr)

        if args.dry_run:
            showtimes = dry_run_showtimes(movie_url, date_value)
        else:
            showtimes = source_adapter(movie_url, date_value)

        output = build_output(
            movie_url=movie_url,
            date_value=date_value,
            source=args.source,
            showtimes=showtimes,
            dry_run=args.dry_run,
        )
        enforce_output(output)

        payload = json.dumps(output, ensure_ascii=False, indent=2)
        write_output(payload, args.output)

        if args.verbose:
            print(f"Resolved {len(showtimes)} showtime(s)", file=sys.stderr)
            if args.output not in {"-", "stdout"}:
                print(f"Wrote showtimes to {args.output}", file=sys.stderr)

        sys.exit(EXIT_OK)

    except ConnectionError as exc:
        print(f"Upstream unavailable: {exc}", file=sys.stderr)
        sys.exit(EXIT_UNAVAILABLE)
    except PermissionError as exc:
        print(f"Permission error: {exc}", file=sys.stderr)
        sys.exit(EXIT_NOPERM)
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
