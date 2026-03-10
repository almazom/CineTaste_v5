#!/usr/bin/env python3
"""
ct-time-price/port.py — Validation Port

Validates output (movie-showtimes@1.0.0).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "_shared"))

from validate import enforce_contract, validate_against_contract

OUTPUT_CONTRACT = "movie-showtimes"


def enforce_output(data: dict) -> dict:
    """Validate output data against movie-showtimes contract."""
    return enforce_contract(data, OUTPUT_CONTRACT, "output")


def validate_output(data: dict) -> tuple[bool, list[str]]:
    """Validate output against movie-showtimes contract."""
    return validate_against_contract(data, OUTPUT_CONTRACT)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python port.py <file.json>")
        sys.exit(1)

    file_path = sys.argv[1]

    with open(file_path, encoding="utf-8") as file_obj:
        data = json.load(file_obj)

    is_valid, errors = validate_output(data)
    if is_valid:
        print(f"✓ Valid {OUTPUT_CONTRACT}")
    else:
        print(f"✗ Invalid {OUTPUT_CONTRACT}:")
        for error in errors:
            print(f"  - {error}")
    sys.exit(0 if is_valid else 1)
