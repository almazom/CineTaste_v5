#!/usr/bin/env python3
"""
ct-analyze/main.py — CLI Entry Point

Analyzes movies against taste profile using AI.
Contract: movie-batch@1.0.0 → analysis-result@1.0.0
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from adapter_agents import analyze_movies
from port import enforce_input, enforce_output


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Analyze movies against taste profile using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ct-analyze --input movies.json --taste taste/profile.yaml
  ct-analyze -i movies.json -t taste/profile.yaml --output analyzed.json
  ct-analyze -i movies.json -t taste/profile.yaml --dry-run
"""
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input movie-batch JSON file"
    )

    parser.add_argument(
        "--taste", "-t",
        required=True,
        help="Taste profile YAML file"
    )

    parser.add_argument(
        "--output", "-o",
        default="-",
        help="Output file path (default: stdout)"
    )

    parser.add_argument(
        "--agent", "-a",
        default="auto",
        choices=["auto", "kimi", "pi", "dry_run"],
        help="AI agent to use: auto|kimi|pi|dry_run (default: auto)"
    )

    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Skip AI call, return mock analysis"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    return parser.parse_args()


def build_output(analyzed: list, analyzer: str) -> dict:
    """Build output conforming to analysis-result@1.0.0 contract."""
    return {
        "analyzed": analyzed,
        "meta": {
            "analyzer": analyzer,
            "analyzed_at": datetime.now().isoformat(),
            "taste_profile": "1.0"
        }
    }


def main():
    """Main entry point."""
    args = parse_args()

    try:
        # Load input
        if args.verbose:
            print(f"Loading movies from {args.input}...", file=sys.stderr)

        with open(args.input) as f:
            data = json.load(f)

        # Validate input
        enforce_input(data)

        movies = data.get("movies", [])
        if args.verbose:
            print(f"Loaded {len(movies)} movies", file=sys.stderr)

        # Check taste profile exists
        if not Path(args.taste).exists():
            print(f"Error: Taste profile not found: {args.taste}", file=sys.stderr)
            sys.exit(2)

        # Analyze
        if args.verbose:
            if args.dry_run:
                print("DRY RUN: Using mock analysis", file=sys.stderr)
            else:
                print(f"Analyzing with {args.agent}...", file=sys.stderr)

        analyzed, agent_meta = analyze_movies(
            movies,
            args.taste,
            dry_run=args.dry_run,
            agent_name=args.agent,
        )

        # Build output (merge meta from agent)
        output = {
            "analyzed": analyzed,
            "meta": agent_meta
        }

        # Validate output
        enforce_output(output)

        # Output
        json_output = json.dumps(output, ensure_ascii=False, indent=2)

        if args.output == "-":
            print(json_output)
        else:
            Path(args.output).write_text(json_output, encoding="utf-8")
            if args.verbose:
                print(f"Wrote analysis to {args.output}", file=sys.stderr)

        if args.verbose:
            # Summary stats
            recs = {}
            for a in analyzed:
                r = a.get("recommendation", "unknown")
                recs[r] = recs.get(r, 0) + 1
            print(f"Analysis complete: {dict(recs)}", file=sys.stderr)

        sys.exit(0)

    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(4)

    except TimeoutError as e:
        print(f"Timeout: {e}", file=sys.stderr)
        sys.exit(3)

    except RuntimeError as e:
        print(f"AI agent error: {e}", file=sys.stderr)
        sys.exit(3)

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
