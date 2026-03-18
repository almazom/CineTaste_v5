#!/usr/bin/env python3
"""
ct-filter/main.py — CLI Entry Point

Filters analyzed movies by recommendation threshold.
Contract: analysis-result@1.0.0 → filter-result@1.0.0

Pure function: no external dependencies, no state.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from port import enforce_input, enforce_output

EXIT_OK = 0
EXIT_INTERNAL = 1
EXIT_INVALID_ARGS = 2
EXIT_DATAERR = 65
EXIT_NOINPUT = 66
EXIT_CANTCREAT = 73
EXIT_NOPERM = 77


class InvalidArgumentsError(ValueError):
    """Raised when CLI flags are syntactically valid but semantically invalid."""


def _load_tool_version() -> str:
    manifest_path = Path(__file__).with_name("MANIFEST.json")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return str(manifest.get("version", "unknown"))
    except Exception:
        return "unknown"


TOOL_VERSION = _load_tool_version()
VALID_FILTER_RECOMMENDATIONS = {"must_see", "recommended"}
STDOUT_SENTINELS = {"-", "stdout"}


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog=Path(sys.argv[0]).name,
        description="Filter movies by recommendation threshold",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ct-filter --input analyzed.json
  ct-filter -i analyzed.json --recommendation must_see,recommended
  ct-filter -i analyzed.json --min-score 70 --output filtered.json
"""
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input analysis-result JSON file"
    )

    parser.add_argument(
        "--recommendation", "-r",
        default="must_see,recommended",
        help="Comma-separated recommendation types to keep (default: must_see,recommended)"
    )

    parser.add_argument(
        "--min-score", "-m",
        type=int,
        default=0,
        help="Minimum relevance score (0-100, default: 0)"
    )

    parser.add_argument(
        "--output", "-o",
        default="-",
        help="Output file path (default: stdout)"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument("--version", action="version", version=f"ct-filter {TOOL_VERSION}")

    return parser.parse_args()


def parse_recommendations(recommendation_arg: str) -> list[str]:
    """Parse and validate comma-separated recommendations from CLI flag."""
    values = [item.strip() for item in recommendation_arg.split(",") if item.strip()]
    if not values:
        raise InvalidArgumentsError("--recommendation must contain at least one value")

    invalid = [value for value in values if value not in VALID_FILTER_RECOMMENDATIONS]
    if invalid:
        allowed = ", ".join(sorted(VALID_FILTER_RECOMMENDATIONS))
        joined = ", ".join(invalid)
        raise InvalidArgumentsError(f"Unknown recommendation value(s): {joined}; allowed: {allowed}")

    return values


def validate_args(args: argparse.Namespace) -> None:
    if not 0 <= args.min_score <= 100:
        raise InvalidArgumentsError("--min-score must be between 0 and 100")


def load_input(input_path: str, verbose: bool) -> dict:
    """Load input JSON payload from file."""
    if input_path == "-":
        if verbose:
            print("Loading analysis from stdin...", file=sys.stderr)
        raw = sys.stdin.read()
        if not raw.strip():
            raise ValueError("stdin is empty; expected analysis-result JSON payload")
        source = "stdin"
    else:
        if verbose:
            print(f"Loading analysis from {input_path}...", file=sys.stderr)
        raw = Path(input_path).read_text(encoding="utf-8")
        source = input_path

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"invalid JSON input in {source} (line {exc.lineno}, column {exc.colno}: {exc.msg})"
        ) from exc

    if not isinstance(payload, dict):
        raise ValueError("input payload must be a JSON object")

    return payload


def build_filtered_item(item: dict, recommendation: str, score: int) -> dict:
    """Build a filter-result item from analysis item."""
    movie = item.get("movie", {})
    return {
        "movie": {
            "id": movie.get("id", ""),
            "title": movie.get("title", ""),
            "original_title": movie.get("original_title", ""),
            "director": movie.get("director", ""),
            "actors": movie.get("actors", []),
            "genres": movie.get("genres", []),
            "year": movie.get("year"),
            "duration_min": movie.get("duration_min"),
            "source": movie.get("source", ""),
            "url": movie.get("url", ""),
            "showtimes": movie.get("showtimes", []),
            "available_days": movie.get("available_days", []),
            "available_days_accurate": movie.get("available_days_accurate", []),
        },
        "relevance_score": score,
        "recommendation": recommendation,
        "reasoning": item.get("reasoning", "")
    }


def write_output(output: dict, output_path: str, verbose: bool) -> None:
    """Write output JSON either to stdout or a file."""
    json_output = json.dumps(output, ensure_ascii=False, indent=2)

    if output_path in STDOUT_SENTINELS:
        print(json_output)
        return

    Path(output_path).write_text(json_output, encoding="utf-8")
    if verbose:
        print(f"Wrote filtered results to {output_path}", file=sys.stderr)


def filter_movies(
    analyzed: list,
    allowed_recommendations: list,
    min_score: int
) -> list:
    """
    Filter movies by recommendation and score.

    Pure function: no side effects.

    Args:
        analyzed: List of analyzed movie dicts
        allowed_recommendations: List of allowed recommendation types
        min_score: Minimum score threshold

    Returns:
        Filtered list of movies
    """
    filtered = [
        build_filtered_item(item, item.get("recommendation", ""), item.get("relevance_score", 0))
        for item in analyzed
        if item.get("recommendation", "") in allowed_recommendations
        and item.get("relevance_score", 0) >= min_score
    ]

    # Sort by score descending
    filtered.sort(key=lambda x: x["relevance_score"], reverse=True)

    return filtered


def build_output(
    filtered: list,
    total_input: int,
    allowed_recommendations: list,
    min_score: int
) -> dict:
    """Build output conforming to filter-result@1.0.0 contract."""
    return {
        "filtered": filtered,
        "meta": {
            "total_input": total_input,
            "matched": len(filtered),
            "thresholds": {
                "recommendations": allowed_recommendations,
                "min_score": min_score
            },
            "filtered_at": datetime.now(timezone.utc).isoformat()
        }
    }


def main():
    """Main entry point."""
    args = parse_args()

    try:
        data = load_input(args.input, args.verbose)
        enforce_input(data)

        analyzed = data.get("analyzed", [])
        if args.verbose:
            print(f"Loaded {len(analyzed)} analyzed movies", file=sys.stderr)

        validate_args(args)
        allowed_recs = parse_recommendations(args.recommendation)
        filtered = filter_movies(analyzed, allowed_recs, args.min_score)

        output = build_output(
            filtered,
            total_input=len(analyzed),
            allowed_recommendations=allowed_recs,
            min_score=args.min_score
        )
        enforce_output(output)
        write_output(output, args.output, args.verbose)

        if args.verbose:
            print(f"Filtered: {len(analyzed)} → {len(filtered)} movies", file=sys.stderr)

        if len(filtered) == 0:
            print("Warning: No movies matched filter criteria", file=sys.stderr)

        return EXIT_OK

    except InvalidArgumentsError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return EXIT_INVALID_ARGS
    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return EXIT_DATAERR
    except FileNotFoundError as e:
        print(f"Input path error: {e}", file=sys.stderr)
        return EXIT_NOINPUT
    except PermissionError as e:
        print(f"Permission error: {e}", file=sys.stderr)
        return EXIT_NOPERM
    except OSError as e:
        print(f"Filesystem error: {e}", file=sys.stderr)
        return EXIT_CANTCREAT
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return EXIT_INTERNAL


if __name__ == "__main__":
    main()
