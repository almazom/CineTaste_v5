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


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
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

    return parser.parse_args()


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
    filtered = []

    for item in analyzed:
        rec = item.get("recommendation", "")
        score = item.get("relevance_score", 0)

        # Check recommendation type
        if rec not in allowed_recommendations:
            continue

        # Check minimum score
        if score < min_score:
            continue

        # Build filtered item (strip extra fields)
        movie = item.get("movie", {})

        filtered.append({
            "movie": {
                "id": movie.get("id", ""),
                "title": movie.get("title", ""),
                "original_title": movie.get("original_title", ""),
                "director": movie.get("director", ""),
                "actors": movie.get("actors", []),
                "genres": movie.get("genres", []),
                "year": movie.get("year"),
                "source": movie.get("source", ""),
                "url": movie.get("url", "")
            },
            "relevance_score": score,
            "recommendation": rec,
            "reasoning": item.get("reasoning", "")
        })

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
        # Load input
        if args.verbose:
            print(f"Loading analysis from {args.input}...", file=sys.stderr)

        with open(args.input) as f:
            data = json.load(f)

        # Validate input
        enforce_input(data)

        analyzed = data.get("analyzed", [])
        if args.verbose:
            print(f"Loaded {len(analyzed)} analyzed movies", file=sys.stderr)

        # Parse allowed recommendations
        allowed_recs = [r.strip() for r in args.recommendation.split(",")]

        # Filter
        filtered = filter_movies(analyzed, allowed_recs, args.min_score)

        # Build output
        output = build_output(
            filtered,
            total_input=len(analyzed),
            allowed_recommendations=allowed_recs,
            min_score=args.min_score
        )

        # Validate output
        enforce_output(output)

        # Output
        json_output = json.dumps(output, ensure_ascii=False, indent=2)

        if args.output == "-":
            print(json_output)
        else:
            Path(args.output).write_text(json_output, encoding="utf-8")
            if args.verbose:
                print(f"Wrote filtered results to {args.output}", file=sys.stderr)

        if args.verbose:
            print(f"Filtered: {len(analyzed)} → {len(filtered)} movies", file=sys.stderr)

        # Warning if nothing matched
        if len(filtered) == 0:
            print("Warning: No movies matched filter criteria", file=sys.stderr)

        sys.exit(0)

    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(4)

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
