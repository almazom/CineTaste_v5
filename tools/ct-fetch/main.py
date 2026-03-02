#!/usr/bin/env python3
"""
ct-fetch/main.py — CLI Entry Point

Fetches movies from cinema sources.
Contract: movie-batch@1.0.0
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable

from adapter_kinoteatr import fetch_movies, CITY_URLS
from port import enforce_output

SUPPORTED_SOURCES = {
    "kinoteatr": fetch_movies,
}


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Fetch movies from cinema sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ct-fetch --city naberezhnie-chelni
  ct-fetch --city naberezhnie-chelni --when 2026-03-15 --output movies.json
  ct-fetch --city naberezhnie-chelni --dry-run
"""
    )

    parser.add_argument(
        "--city", "-c",
        required=True,
        help="City code (e.g., naberezhnie-chelni)"
    )

    parser.add_argument(
        "--when", "-w",
        default="now",
        help="Date filter: 'now' or YYYY-MM-DD (default: now)"
    )

    parser.add_argument(
        "--output", "-o",
        default="-",
        help="Output file path (default: stdout)"
    )

    parser.add_argument(
        "--source", "-s",
        default="kinoteatr",
        help="Source adapter to use (default: kinoteatr)"
    )

    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Skip actual fetch, return test data"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    return parser.parse_args()


def build_output(movies: list, city: str, city_display: str, when: str) -> dict:
    """Build output conforming to movie-batch@1.0.0 contract."""
    date_value = datetime.now().strftime("%Y-%m-%d")
    if when != "now":
        date_value = when

    return {
        "movies": movies,
        "meta": {
            "city": city,
            "city_display": city_display,
            "date": date_value,
            "source_url": CITY_URLS.get(city, ""),
            "fetched_at": datetime.now().isoformat()
        }
    }


def validate_when(when: str) -> str:
    """Validate --when value and normalize it."""
    if when == "now":
        return when

    try:
        datetime.strptime(when, "%Y-%m-%d")
    except ValueError:
        raise ValueError("--when must be 'now' or YYYY-MM-DD")

    return when


def get_source_adapter(source: str) -> Callable[[str, str], list]:
    """Resolve source adapter from --source value."""
    adapter = SUPPORTED_SOURCES.get(source)
    if adapter is None:
        supported = ", ".join(sorted(SUPPORTED_SOURCES.keys()))
        raise ValueError(f"Unknown source: {source}. Supported: {supported}")
    return adapter


def get_city_display(city: str) -> str:
    """Get display name for city."""
    city_names = {
        "naberezhnie-chelni": "Набережные Челны",
        "kazan": "Казань",
        "moscow": "Москва"
    }
    return city_names.get(city, city)


def dry_run_data(city: str) -> list:
    """Return test data for dry-run mode."""
    return [
        {
            "id": "kt-test-1",
            "title": "Тестовый фильм 1",
            "original_title": "Test Movie 1",
            "director": "Тестовый режиссер",
            "actors": ["Актер 1", "Актер 2"],
            "genres": ["драма", "триллер"],
            "year": 2026,
            "duration_min": 120,
            "source": "kinoteatr.ru",
            "url": "https://kinoteatr.ru/film/test-1/",
            "raw_description": "Тестовое описание фильма"
        },
        {
            "id": "kt-test-2",
            "title": "Тестовый фильм 2",
            "original_title": "Test Movie 2",
            "director": "",
            "actors": [],
            "genres": ["комедия"],
            "year": 2025,
            "duration_min": 95,
            "source": "kinoteatr.ru",
            "url": "https://kinoteatr.ru/film/test-2/",
            "raw_description": ""
        }
    ]


def main():
    """Main entry point."""
    args = parse_args()

    try:
        when = validate_when(args.when)
        source_adapter = get_source_adapter(args.source)

        # Fetch or use dry-run data
        if args.dry_run:
            if args.verbose:
                print("DRY RUN: Using test data", file=sys.stderr)
            movies = dry_run_data(args.city)
        else:
            if args.verbose:
                print(
                    f"Fetching movies for {args.city} from {args.source} (when={when})...",
                    file=sys.stderr,
                )
            movies = source_adapter(args.city, when)

        # Build output
        city_display = get_city_display(args.city)
        output = build_output(movies, args.city, city_display, when)

        # Validate output against contract
        try:
            enforce_output(output)
        except ValueError as e:
            print(f"Contract violation: {e}", file=sys.stderr)
            sys.exit(4)

        # Output
        json_output = json.dumps(output, ensure_ascii=False, indent=2)

        if args.output == "-":
            print(json_output)
        else:
            Path(args.output).write_text(json_output, encoding="utf-8")
            if args.verbose:
                print(f"Wrote {len(movies)} movies to {args.output}", file=sys.stderr)

        if args.verbose:
            print(f"Fetched {len(movies)} movies", file=sys.stderr)

        sys.exit(0)

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    except ConnectionError as e:
        print(f"Network error: {e}", file=sys.stderr)
        sys.exit(3)

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
