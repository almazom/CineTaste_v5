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


def resolve_template(template_arg: str) -> tuple[str, Callable[[list, str], str]]:
    """Normalize template name and resolve renderer."""
    normalized_template = template_arg.strip().lower()
    renderer = get_template_renderer(normalized_template)
    return normalized_template, renderer


def load_input(input_path: str, verbose: bool) -> dict:
    """Load input JSON payload from file."""
    if verbose:
        print(f"Loading filtered movies from {input_path}...", file=sys.stderr)

    with open(input_path) as input_file:
        return json.load(input_file)


def write_output(output: dict, output_path: str, verbose: bool) -> None:
    """Write output JSON either to stdout or a file."""
    json_output = json.dumps(output, ensure_ascii=False, indent=2)

    if output_path == "-":
        print(json_output)
        return

    Path(output_path).write_text(json_output, encoding="utf-8")
    if verbose:
        print(f"Wrote message JSON to {output_path}", file=sys.stderr)


def run(args: argparse.Namespace) -> int:
    """Execute formatting pipeline and return process exit code."""
    try:
        template, renderer = resolve_template(args.template)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2

    try:
        data = load_input(args.input, args.verbose)

        enforce_input(data)

        filtered = data.get("filtered", [])
        if args.verbose:
            print(f"Loaded {len(filtered)} filtered movies", file=sys.stderr)

        text = renderer(filtered, args.city)

        output = build_output(
            text=text,
            template=template,
            city_display=args.city,
            movie_count=len(filtered)
        )

        enforce_output(output)

        write_output(output, args.output, args.verbose)

        if args.verbose:
            print(f"Formatted {len(filtered)} movies", file=sys.stderr)

        return 0

    except ValueError as e:
        print(f"Validation error: {e}", file=sys.stderr)
        return 4

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


def main() -> None:
    """Main entry point."""
    args = parse_args()
    sys.exit(run(args))


if __name__ == "__main__":
    main()
