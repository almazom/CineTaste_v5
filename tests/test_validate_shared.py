"""
Tests for shared contract validator.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "_shared"))

from validate import (
    enforce_contract,
    load_contract,
    validate_against_contract,
    validate_analysis_result,
    validate_filter_result,
    validate_message_text,
    validate_movie_batch,
    validate_send_confirmation,
)


ROOT = Path(__file__).parent.parent


def load_sample(name: str) -> dict:
    sample = ROOT / "contracts" / "examples" / f"{name}.sample.json"
    return json.loads(sample.read_text(encoding="utf-8"))


class TestValidateShared:
    def test_load_contract_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_contract("missing-contract")

    def test_enforce_contract_raises_with_context(self):
        data = {"bad": "shape"}
        with pytest.raises(ValueError) as exc:
            enforce_contract(data, "movie-batch", "output")
        assert "movie-batch@1.0.0 output" in str(exc.value)

    def test_enforce_contract_passes_valid_data(self):
        data = load_sample("filter-result")
        out = enforce_contract(data, "filter-result", "output")
        assert out["meta"]["matched"] == data["meta"]["matched"]

    def test_convenience_wrappers(self):
        movie_batch = load_sample("movie-batch")
        analysis_result = load_sample("analysis-result")
        filter_result = load_sample("filter-result")
        message_text = load_sample("message-text")

        # send-confirmation has no sample, create a valid minimal payload.
        send_confirmation = {
            "success": True,
            "meta": {"sent_at": "2026-03-02T12:00:00+00:00"},
        }

        assert validate_movie_batch(movie_batch)[0]
        assert validate_analysis_result(analysis_result)[0]
        assert validate_filter_result(filter_result)[0]
        assert validate_message_text(message_text)[0]
        assert validate_send_confirmation(send_confirmation)[0]
