"""
Pipeline and flow-level regression tests.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

sys.path.insert(0, str(ROOT / "tools" / "_shared"))
from validate import validate_against_contract  # noqa: E402


def test_local_wrappers_exist_and_are_executable():
    for name in ("ct-fetch", "ct-schedule", "ct-analyze", "ct-filter", "ct-format"):
        wrapper = ROOT / name
        assert wrapper.exists(), f"missing wrapper: {wrapper}"
        assert os.access(wrapper, os.X_OK), f"wrapper is not executable: {wrapper}"


def test_flow_template_path_exists():
    flow_path = ROOT / "flows" / "latest" / "FLOW.md"
    template_line = None
    for line in flow_path.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("template_path:"):
            template_line = line.strip().split(":", 1)[1].strip()
            break

    assert template_line is not None, "template_path must be present in FLOW config"
    template_path = (ROOT / template_line).resolve()
    assert template_path.exists(), f"template_path does not exist: {template_path}"


@pytest.mark.skip(reason="--dry-run removed from pipeline; dry-run now at t2me level only")
def test_run_dry_run_with_cached_input_produces_send_confirmation():
    sample_input = ROOT / "contracts" / "examples" / "analysis-result.sample.json"
    result = subprocess.run(
        ["./run", "--dry-run", "--input", str(sample_input)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr
    assert "Preview validated via send-confirmation" in result.stdout
    assert '"success": true' in result.stdout


def test_map_send_confirmation_success(tmp_path: Path):
    raw = {
        "command": "send",
        "status": "ok",
        "result": {
            "mode": "text",
            "dry_run": True,
            "target": "@demo",
            "message": "hello",
        },
        "route": {"target_locked": "@demo"},
    }
    raw_path = tmp_path / "raw.json"
    out_path = tmp_path / "send-confirmation.json"
    raw_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    result = subprocess.run(
        [
            PYTHON,
            str(ROOT / "tools" / "t2me" / "map_send_confirmation.py"),
            "--input",
            str(raw_path),
            "--output",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    ok, errors = validate_against_contract(payload, "send-confirmation")
    assert ok, errors
    assert payload["success"] is True
    assert payload["meta"]["target"] == "@demo"


def test_map_send_confirmation_failure(tmp_path: Path):
    raw = {
        "command": "send",
        "status": "error",
        "error": "auth failed",
        "result": {"target": "@demo"},
    }
    raw_path = tmp_path / "raw.json"
    out_path = tmp_path / "send-confirmation.json"
    raw_path.write_text(json.dumps(raw, ensure_ascii=False), encoding="utf-8")

    result = subprocess.run(
        [
            PYTHON,
            str(ROOT / "tools" / "t2me" / "map_send_confirmation.py"),
            "--input",
            str(raw_path),
            "--output",
            str(out_path),
        ],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    ok, errors = validate_against_contract(payload, "send-confirmation")
    assert ok, errors
    assert payload["success"] is False
    assert "error" in payload
    assert "auth" in payload["error"]
