"""
Pipeline and flow-level regression tests.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path



ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

sys.path.insert(0, str(ROOT / "tools" / "_shared"))
from validate import validate_against_contract  # noqa: E402


def latest_failed_dir(before: set[Path]) -> Path:
    after = set((ROOT / "logs").glob("failed_*"))
    created = sorted(after - before)
    assert created, "expected a new failed_* artifact directory"
    return created[-1]


def test_local_wrappers_exist_and_are_executable():
    protocol = json.loads((ROOT / "PROTOCOL.json").read_text(encoding="utf-8"))
    names = []
    for name, spec in protocol["tools"].items():
        if spec.get("external"):
            continue
        if spec.get("status") == "legacy":
            continue
        names.append(name)

    for name in names:
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


def test_run_dry_run_with_cached_input_produces_send_confirmation():
    sample_input = ROOT / "contracts" / "examples" / "analysis-result.sample.json"
    fake_t2me = ROOT / ".testrun" / "fake_t2me_dry"
    fake_t2me.mkdir(parents=True, exist_ok=True)
    fake_t2me_bin = fake_t2me / "t2me"
    args_file = fake_t2me / "args.txt"
    fake_t2me_bin.write_text(
        f"""#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "$*" > "{args_file}"
cat >/dev/null
echo '{{"status":"ok","result":{{"target":"@dry-run-test","message":"preview","dry_run":true}}}}'
""",
        encoding="utf-8",
    )
    fake_t2me_bin.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_t2me}:{env.get('PATH', '')}"

    result = subprocess.run(
        ["./run", "--dry-run", "--input", str(sample_input)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env=env,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["meta"]["target"] == "@dry-run-test"
    assert payload["meta"]["dry_run"] is True
    assert "--dry-run" in args_file.read_text(encoding="utf-8")
    assert "Dry-run confirmation validated" in result.stderr


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
    assert payload["meta"]["dry_run"] is True


def test_run_resend_surfaces_mapped_send_confirmation_failure(tmp_path: Path):
    message_path = tmp_path / "message.md"
    message_path.write_text("hello", encoding="utf-8")
    fake_t2me = tmp_path / "bin"
    fake_t2me.mkdir(parents=True, exist_ok=True)
    fake_t2me_bin = fake_t2me / "t2me"
    fake_t2me_bin.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
cat >/dev/null
echo '{"status":"error","error":"auth failed","result":{"target":"@demo"}}'
""",
        encoding="utf-8",
    )
    fake_t2me_bin.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_t2me}:{env.get('PATH', '')}"

    result = subprocess.run(
        ["./run", "--resend", str(message_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env=env,
    )
    assert result.returncode != 0
    assert "auth failed" in result.stderr
    assert "send-confirmation indicates failure" in result.stderr


def test_run_resend_dry_run_emits_send_confirmation_stdout(tmp_path: Path):
    message_path = tmp_path / "message.md"
    message_path.write_text("hello", encoding="utf-8")
    fake_t2me = tmp_path / "bin"
    fake_t2me.mkdir(parents=True, exist_ok=True)
    fake_t2me_bin = fake_t2me / "t2me"
    fake_t2me_bin.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
cat >/dev/null
echo '{"status":"ok","result":{"target":"@demo","message":"hello","dry_run":true}}'
""",
        encoding="utf-8",
    )
    fake_t2me_bin.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_t2me}:{env.get('PATH', '')}"

    result = subprocess.run(
        ["./run", "--dry-run", "--resend", str(message_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env=env,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["meta"]["dry_run"] is True
    assert payload["meta"]["target"] == "@demo"


def test_run_resend_failure_preserves_message_and_recovery_hint(tmp_path: Path):
    message_path = tmp_path / "message.md"
    message_path.write_text("hello", encoding="utf-8")
    fake_t2me = tmp_path / "bin"
    fake_t2me.mkdir(parents=True, exist_ok=True)
    fake_t2me_bin = fake_t2me / "t2me"
    fake_t2me_bin.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
cat >/dev/null
exit 42
""",
        encoding="utf-8",
    )
    fake_t2me_bin.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_t2me}:{env.get('PATH', '')}"
    before = set((ROOT / "logs").glob("failed_*"))

    result = subprocess.run(
        ["./run", "--resend", str(message_path)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env=env,
    )
    failed_dir = latest_failed_dir(before)

    assert result.returncode != 0
    assert (failed_dir / "message.txt").read_text(encoding="utf-8") == "hello"
    recover = (failed_dir / "RECOVER.md").read_text(encoding="utf-8")
    failure = (failed_dir / "failure.txt").read_text(encoding="utf-8")
    assert "./run --resend" in recover
    assert "step: resend" in failure
    assert "t2me send --markdown" in failure


def test_live_send_mapping_failure_keeps_context_and_avoids_auto_resend(tmp_path: Path):
    sample_input = ROOT / "contracts" / "examples" / "analysis-result.sample.json"
    fake_t2me = tmp_path / "bin"
    fake_t2me.mkdir(parents=True, exist_ok=True)
    fake_t2me_bin = fake_t2me / "t2me"
    fake_t2me_bin.write_text(
        """#!/usr/bin/env bash
set -euo pipefail
cat >/dev/null
echo '{"status":"ok","result":{"target":"@demo","message":"preview"}}'
""",
        encoding="utf-8",
    )
    fake_t2me_bin.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{fake_t2me}:{env.get('PATH', '')}"
    before = set((ROOT / "logs").glob("failed_*"))

    result = subprocess.run(
        ["./run", "--input", str(sample_input)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
        env=env,
    )
    failed_dir = latest_failed_dir(before)

    assert result.returncode != 0
    assert "message_id" in result.stderr
    recover = (failed_dir / "RECOVER.md").read_text(encoding="utf-8")
    failure = (failed_dir / "failure.txt").read_text(encoding="utf-8")
    assert "Do not auto-resend" in recover
    assert "step: Step 6/6: t2me" in failure
    assert 'cat "$TMPDIR/message.txt" | t2me send --markdown' in failure or 't2me send --markdown' in failure


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
