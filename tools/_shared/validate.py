#!/usr/bin/env python3
"""
tools/_shared/validate.py — Shared Contract Validation

Uses jsonschema library for proper JSON Schema validation.
All tools should use this for I/O validation.
"""

import json
from pathlib import Path
from typing import Optional

try:
    from jsonschema import Draft7Validator, FormatChecker, ValidationError
except ImportError:
    print("ERROR: jsonschema not installed. Run: pip install jsonschema")
    raise

# Base path for contracts
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"


def load_contract(contract_name: str) -> dict:
    """Load a contract schema by name (without .schema.json suffix)."""
    path = CONTRACTS_DIR / f"{contract_name}.schema.json"
    if not path.exists():
        raise FileNotFoundError(f"Contract not found: {path}")
    with open(path) as f:
        return json.load(f)


def validate_against_contract(data: dict, contract_name: str) -> tuple[bool, list[str]]:
    """
    Validate data against a named contract.

    Args:
        data: Data to validate
        contract_name: Contract name (e.g., "movie-batch")

    Returns:
        (is_valid, errors) tuple
    """
    try:
        schema = load_contract(contract_name)
        validator = Draft7Validator(schema, format_checker=FormatChecker())
        errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))

        if not errors:
            return True, []

        formatted = []
        for e in errors:
            path = ".".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            formatted.append(f"{path}: {e.message}")
        return False, formatted

    except ValidationError as e:
        path = ".".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
        return False, [f"{path}: {e.message}"]
    except Exception as e:
        return False, [str(e)]


def enforce_contract(data: dict, contract_name: str, direction: str = "output") -> dict:
    """
    Validate and return data, or raise detailed error.

    Args:
        data: Data to validate
        contract_name: Contract name
        direction: "input" or "output" for error message

    Returns:
        The validated data

    Raises:
        ValueError: If validation fails
    """
    is_valid, errors = validate_against_contract(data, contract_name)
    if not is_valid:
        error_list = "\n".join(f"  - {e}" for e in errors)
        raise ValueError(f"Contract violation ({contract_name}@1.0.0 {direction}):\n{error_list}")
    return data


# Convenience functions for each contract
def validate_movie_batch(data: dict) -> tuple[bool, list[str]]:
    return validate_against_contract(data, "movie-batch")

def validate_analysis_result(data: dict) -> tuple[bool, list[str]]:
    return validate_against_contract(data, "analysis-result")

def validate_filter_result(data: dict) -> tuple[bool, list[str]]:
    return validate_against_contract(data, "filter-result")

def validate_message_text(data: dict) -> tuple[bool, list[str]]:
    return validate_against_contract(data, "message-text")

def validate_send_confirmation(data: dict) -> tuple[bool, list[str]]:
    return validate_against_contract(data, "send-confirmation")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python validate.py <contract_name> <file.json>")
        print("Contracts: movie-batch, analysis-result, filter-result, message-text, send-confirmation")
        sys.exit(1)

    contract = sys.argv[1]
    file_path = sys.argv[2]

    with open(file_path) as f:
        data = json.load(f)

    is_valid, errors = validate_against_contract(data, contract)

    if is_valid:
        print(f"✓ Valid {contract}")
        sys.exit(0)
    else:
        print(f"✗ Invalid {contract}:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
