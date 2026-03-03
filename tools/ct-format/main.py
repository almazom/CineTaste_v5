#!/usr/bin/env python3
"""
ct-format/main.py — CLI Entry Point

Formats filtered movies to Telegram markdown.
Contract: filter-result@1.0.0 → message-text@1.0.0
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from adapter_telegram import render_message
from port import enforce_input, enforce_output

SUPPORTED_TEMPLATES = {
    "telegram": render_message,
}


def parse_args():
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Format filtered movies to Telegram markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ct-format --input filtered.json --template telegram
  ct-format -i filtered.json -t telegram --city "Набережные Челны" -o message.json
"""
    )

    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Input filter-result JSON file"
    )

    parser.add_argument(
        "--template", "-t",
        default="telegram",
        help="Template to use (default: telegram)"
    )

    parser.add_argument(
        "--city", "-c",
        default="",
        help="City display name for header"
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


def build_output(text: str, template: str, city_display: str, movie_count: int) -> dict:
    """Build output conforming to message-text@1.0.0 contract."""
    return {
        "text": text,
        "meta": {
            "template": template,
            "city_display": city_display,
            "movie_count": movie_count,
            "formatted_at": datetime.now(timezone.utc).isoformat()
        }
    }


def get_template_renderer(template: str) -> Callable[[list, str], str]:
    """Resolve renderer from --template flag."""
    renderer = SUPPORTED_TEMPLATES.get(template)
    if renderer is None:
        supported = ", ".join(sorted(SUPPORTED_TEMPLATES.keys()))
        raise ValueError(f"Unknown template: {template}. Supported: {supported}")
    return renderer


def main():
    """Main entry point."""
    args = parse_args()

    try:
        template = args.template.strip().lower()
        renderer = get_template_renderer(template)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    try:
        # Load input
        if args.verbose:
            print(f"Loading filtered movies from {args.input}...", file=sys.stderr)

        with open(args.input) as f:
            data = json.load(f)

        # Validate input
        enforce_input(data)

        filtered = data.get("filtered", [])
        if args.verbose:
            print(f"Loaded {len(filtered)} filtered movies", file=sys.stderr)

        # Render message
        text = renderer(filtered, args.city)

        # Build output
        output = build_output(
            text=text,
            template=template,
            city_display=args.city,
            movie_count=len(filtered)
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
                print(f"Wrote message JSON to {args.output}", file=sys.stderr)

        if args.verbose:
            print(f"Formatted {len(filtered)} movies", file=sys.stderr)

        sys.exit(0)

    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(4)

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
