#!/usr/bin/env python3
"""
ct-provider-latest/port.py — Validation Port

Validates output (provider-latest@1.0.0).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "_shared"))

from validate import enforce_contract, validate_against_contract

OUTPUT_CONTRACT = "provider-latest"


def enforce_output(data: dict) -> dict:
    """Validate output data against provider-latest contract."""
    return enforce_contract(data, OUTPUT_CONTRACT, "output")


def validate_output(data: dict) -> tuple[bool, list[str]]:
    """Validate output against provider-latest contract."""
    return validate_against_contract(data, OUTPUT_CONTRACT)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python port.py <file.json>")
        sys.exit(1)

    with open(sys.argv[1], encoding="utf-8") as file_obj:
        data = json.load(file_obj)

    is_valid, errors = validate_output(data)
    if is_valid:
        print(f"✓ Valid {OUTPUT_CONTRACT}")
    else:
        print(f"✗ Invalid {OUTPUT_CONTRACT}:")
        for error in errors:
            print(f"  - {error}")
    sys.exit(0 if is_valid else 1)
