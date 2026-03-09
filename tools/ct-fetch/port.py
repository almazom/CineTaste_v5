#!/usr/bin/env python3
"""
ct-fetch/port.py — Validation Port (розетка)

Validates output against movie-batch@1.0.0 contract.
Uses shared jsonschema validation.
"""

import json
import sys
from pathlib import Path

# Add _shared to path
sys.path.insert(0, str(Path(__file__).parent.parent / "_shared"))

from validate import enforce_contract, validate_against_contract

CONTRACT = "movie-batch"


def enforce_output(data: dict) -> dict:
    """
    Validate output data against movie-batch contract.

    Raises:
        ValueError: If validation fails
    """
    return enforce_contract(data, CONTRACT, "output")


def validate(data: dict) -> tuple[bool, list[str]]:
    """
    Validate data against movie-batch contract.

    Returns:
        (is_valid, errors) tuple
    """
    return validate_against_contract(data, CONTRACT)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        with open(sys.argv[1]) as f:
            data = json.load(f)
        is_valid, errors = validate(data)
        if is_valid:
            print(f"✓ Valid {CONTRACT}")
        else:
            print(f"✗ Invalid {CONTRACT}:")
            for e in errors:
                print(f"  - {e}")
        sys.exit(0 if is_valid else 1)
    else:
        print("Usage: python port.py <file.json>")
        print(f"Validates against {CONTRACT}.schema.json")
