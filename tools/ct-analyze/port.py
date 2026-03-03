#!/usr/bin/env python3
"""
ct-analyze/port.py — Validation Port (розетка)

Validates input (movie-schedule@1.0.0) and output (analysis-result@1.0.0).
Uses shared jsonschema validation.
"""

import json
import sys
from pathlib import Path

# Add _shared to path
sys.path.insert(0, str(Path(__file__).parent.parent / "_shared"))

from validate import enforce_contract, validate_against_contract

INPUT_CONTRACT = "movie-schedule"
OUTPUT_CONTRACT = "analysis-result"


def enforce_input(data: dict) -> dict:
    """
    Validate input data against movie-schedule contract.

    Raises:
        ValueError: If validation fails
    """
    return enforce_contract(data, INPUT_CONTRACT, "input")


def enforce_output(data: dict) -> dict:
    """
    Validate output data against analysis-result contract.

    Raises:
        ValueError: If validation fails
    """
    return enforce_contract(data, OUTPUT_CONTRACT, "output")


def validate_input(data: dict) -> tuple[bool, list[str]]:
    """Validate input against movie-schedule contract."""
    return validate_against_contract(data, INPUT_CONTRACT)


def validate_output(data: dict) -> tuple[bool, list[str]]:
    """Validate output against analysis-result contract."""
    return validate_against_contract(data, OUTPUT_CONTRACT)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python port.py <input|output> <file.json>")
        sys.exit(1)

    direction = sys.argv[1]
    file_path = sys.argv[2]

    with open(file_path) as f:
        data = json.load(f)

    if direction == "input":
        is_valid, errors = validate_input(data)
        contract = INPUT_CONTRACT
    elif direction == "output":
        is_valid, errors = validate_output(data)
        contract = OUTPUT_CONTRACT
    else:
        print(f"Unknown direction: {direction}")
        sys.exit(2)

    if is_valid:
        print(f"✓ Valid {contract}")
    else:
        print(f"✗ Invalid {contract}:")
        for e in errors:
            print(f"  - {e}")
    sys.exit(0 if is_valid else 1)
