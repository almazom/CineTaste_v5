#!/usr/bin/env python3
"""
ct-schedule/main.py — CLI Entry Point

Enriches fetched movies with showtime schedule.
Contract: movie-batch@1.0.0 -> movie-schedule@1.0.0
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from adapter_showtimes import dry_run_showtimes, fetch_showtimes
from port import enforce_input, enforce_output

SUPPORTED_SOURCES: dict[str, Callable[[str, str], list[dict]]] = {
    "kinoteatr": fetch_showtimes,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Enrich movie list with showtime schedule",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ct-schedule --input movies.json
  ct-schedule --input movies.json --date 2026-03-03 --output scheduled.json
  ct-schedule --input movies.json --dry-run
""",
    )

    parser.add_argument("--input", "-i", required=True, help="Input movie-batch JSON file")
    parser.add_argument(
        "--date",
        "-d",
        default="",
        help="Schedule date: YYYY-MM-DD (default: input meta.date)",
    )
    parser.add_argument(
        "--source",
        "-s",
        default="kinoteatr",
        help="Schedule source adapter (default: kinoteatr)",
    )
    parser.add_argument("--output", "-o", default="-", help="Output file path (default: stdout)")
    parser.add_argument("--dry-run", "-n", action="store_true", help="Generate deterministic mock showtimes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    return parser.parse_args()


def validate_date(value: str) -> str:
    if not value:
        return datetime.now().strftime("%Y-%m-%d")
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("--date must be YYYY-MM-DD") from exc
    return value


def resolve_source(source: str) -> Callable[[str, str], list[dict]]:
    adapter = SUPPORTED_SOURCES.get(source)
    if adapter is None:
        supported = ", ".join(sorted(SUPPORTED_SOURCES.keys()))
        raise ValueError(f"Unknown source: {source}. Supported: {supported}")
    return adapter


def resolve_showtimes_for_movie(
    movie_id: str,
    url: str,
    date_value: str,
    source_adapter: Callable[[str, str], list[dict]],
    dry_run: bool,
    verbose: bool,
) -> list[dict]:
    """Resolve showtimes for one movie using configured source policy."""
    if dry_run:
        return dry_run_showtimes(movie_id, date_value)

    if not url:
        return []

    try:
        return source_adapter(url, date_value)
    except ConnectionError as exc:
        if verbose:
            print(f"Warning: {exc}", file=sys.stderr)
        return []


def enrich_movies(
    movies: list[dict],
    date_value: str,
    source_adapter: Callable[[str, str], list[dict]],
    dry_run: bool,
    verbose: bool,
) -> tuple[list[dict], int]:
    """Attach showtimes to each movie."""
    enriched: list[dict] = []
    with_showtimes = 0

    for movie in movies:
        movie_data = dict(movie)
        movie_id = str(movie.get("id", ""))
        url = str(movie.get("url", "")).strip()

        showtimes = resolve_showtimes_for_movie(
            movie_id=movie_id,
            url=url,
            date_value=date_value,
            source_adapter=source_adapter,
            dry_run=dry_run,
            verbose=verbose,
        )

        movie_data["showtimes"] = showtimes
        if showtimes:
            with_showtimes += 1
        enriched.append(movie_data)

    return enriched, with_showtimes


def build_output(
    movies: list[dict],
    source: str,
    date_value: str,
    input_meta: dict,
    with_showtimes: int,
) -> dict:
    schedule_source = "kinoteatr.ru" if source == "kinoteatr" else source
    source_url = str(input_meta.get("source_url", "")).strip()
    if not source_url:
        city = str(input_meta.get("city", "")).strip()
        source_url = (
            f"https://kinoteatr.ru/kinoafisha/{city}/"
            if city
            else "https://kinoteatr.ru/kinoafisha/"
        )

    fetched_at = str(input_meta.get("fetched_at", "")).strip() or datetime.now(timezone.utc).isoformat()

    return {
        "movies": movies,
        "meta": {
            "city": input_meta.get("city", ""),
            "city_display": input_meta.get("city_display", ""),
            "date": date_value,
            "source_url": source_url,
            "fetched_at": fetched_at,
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
            "schedule_source": schedule_source,
            "movies_total": len(movies),
            "movies_with_showtimes": with_showtimes,
        },
    }


def main() -> None:
    args = parse_args()

    try:
        source_adapter = resolve_source(args.source)
        date_override = validate_date(args.date) if args.date else ""
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    try:
        if args.verbose:
            print(f"Loading movies from {args.input}...", file=sys.stderr)

        with open(args.input, encoding="utf-8") as file_obj:
            data = json.load(file_obj)

        enforce_input(data)

        input_meta = data.get("meta", {})
        date_value = date_override or validate_date(input_meta.get("date", ""))
        movies = data.get("movies", [])

        if args.verbose:
            print(f"Loaded {len(movies)} movies", file=sys.stderr)
            if args.dry_run:
                print("DRY RUN: Generating mock showtimes", file=sys.stderr)

        enriched, with_showtimes = enrich_movies(
            movies=movies,
            date_value=date_value,
            source_adapter=source_adapter,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )

        output = build_output(
            movies=enriched,
            source=args.source,
            date_value=date_value,
            input_meta=input_meta,
            with_showtimes=with_showtimes,
        )

        enforce_output(output)

        payload = json.dumps(output, ensure_ascii=False, indent=2)
        if args.output == "-":
            print(payload)
        else:
            Path(args.output).write_text(payload, encoding="utf-8")
            if args.verbose:
                print(f"Wrote schedule to {args.output}", file=sys.stderr)

        if args.verbose:
            print(
                f"Schedule enrichment complete: {with_showtimes}/{len(enriched)} movies with showtimes",
                file=sys.stderr,
            )

        sys.exit(0)

    except ValueError as exc:
        print(f"Validation error: {exc}", file=sys.stderr)
        sys.exit(4)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON input ({exc})", file=sys.stderr)
        sys.exit(2)
    except Exception as exc:
        print(f"Unexpected error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
