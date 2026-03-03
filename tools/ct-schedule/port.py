#!/usr/bin/env python3
"""
ct-schedule/port.py — Validation port.

Validates input (movie-batch@1.0.0) and output (movie-schedule@1.0.0).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "_shared"))

from validate import enforce_contract, validate_against_contract

INPUT_CONTRACT = "movie-batch"
OUTPUT_CONTRACT = "movie-schedule"


def enforce_input(data: dict) -> dict:
    return enforce_contract(data, INPUT_CONTRACT, "input")


def enforce_output(data: dict) -> dict:
    return enforce_contract(data, OUTPUT_CONTRACT, "output")


def validate_input(data: dict) -> tuple[bool, list[str]]:
    return validate_against_contract(data, INPUT_CONTRACT)


def validate_output(data: dict) -> tuple[bool, list[str]]:
    return validate_against_contract(data, OUTPUT_CONTRACT)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python port.py <input|output> <file.json>")
        sys.exit(1)

    direction = sys.argv[1]
    file_path = sys.argv[2]

    with open(file_path, encoding="utf-8") as file_obj:
        data = json.load(file_obj)

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
        for error in errors:
            print(f"  - {error}")
    sys.exit(0 if is_valid else 1)
