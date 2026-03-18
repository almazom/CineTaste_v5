"""
Test ct-provider-latest tool contract validation and CLI behavior.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT / "tools" / "_shared"))
from validate import validate_against_contract


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file_obj:
        for row in rows:
            file_obj.write(json.dumps(row, ensure_ascii=False))
            file_obj.write("\n")


def touch_mtime(path: Path, ts: int) -> None:
    os.utime(path, (ts, ts))


def make_fake_home(tmp_path: Path, project_dir: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()

    claude_dir = home / ".claude" / "projects" / "-tmp-project"
    write_jsonl(
        claude_dir / "old.jsonl",
        [
            {
                "type": "user",
                "cwd": str(project_dir),
                "sessionId": "claude-old",
                "timestamp": "2026-03-09T10:00:00Z",
                "message": {"role": "user", "content": "old"},
            }
        ],
    )
    write_jsonl(
        claude_dir / "new.jsonl",
        [
            {
                "type": "user",
                "cwd": str(project_dir),
                "sessionId": "claude-new",
                "timestamp": "2026-03-10T10:00:00Z",
                "message": {"role": "user", "content": "new"},
            },
            {
                "type": "assistant",
                "cwd": str(project_dir),
                "sessionId": "claude-new",
                "timestamp": "2026-03-10T10:00:01Z",
                "message": {"role": "assistant", "model": "claude-test"},
            },
        ],
    )
    touch_mtime(claude_dir / "old.jsonl", 100)
    touch_mtime(claude_dir / "new.jsonl", 200)

    qwen_dir = home / ".qwen" / "projects" / "-tmp-project" / "chats"
    write_jsonl(
        qwen_dir / "qwen-a.jsonl",
        [
            {
                "type": "user",
                "cwd": str(project_dir),
                "sessionId": "qwen-a",
                "timestamp": "2026-03-10T09:00:00Z",
                "message": {"role": "user", "parts": [{"text": "a"}]},
            }
        ],
    )
    write_jsonl(
        qwen_dir / "qwen-b.jsonl",
        [
            {
                "type": "user",
                "cwd": str(project_dir),
                "sessionId": "qwen-b",
                "timestamp": "2026-03-10T11:00:00Z",
                "message": {"role": "user", "parts": [{"text": "b"}]},
            },
            {
                "type": "assistant",
                "cwd": str(project_dir),
                "sessionId": "qwen-b",
                "timestamp": "2026-03-10T11:00:01Z",
                "model": "qwen-test",
                "message": {"role": "model", "parts": [{"text": "ok"}]},
            },
        ],
    )
    touch_mtime(qwen_dir / "qwen-a.jsonl", 110)
    touch_mtime(qwen_dir / "qwen-b.jsonl", 210)

    pi_dir = home / ".pi" / "agent" / "sessions" / "--tmp-project--"
    write_jsonl(
        pi_dir / "2026-03-10T10-00-old.jsonl",
        [
            {
                "type": "session",
                "id": "pi-old",
                "timestamp": "2026-03-10T10:00:00Z",
                "cwd": str(project_dir),
            }
        ],
    )
    write_jsonl(
        pi_dir / "2026-03-10T12-00-new.jsonl",
        [
            {
                "type": "session",
                "id": "pi-new",
                "timestamp": "2026-03-10T12:00:00Z",
                "cwd": str(project_dir),
            },
            {
                "type": "model_change",
                "timestamp": "2026-03-10T12:00:00Z",
                "provider": "zai",
                "modelId": "glm-5",
            },
            {
                "type": "message",
                "timestamp": "2026-03-10T12:00:05Z",
                "message": {"role": "assistant", "model": "glm-5", "provider": "zai"},
            },
        ],
    )
    touch_mtime(pi_dir / "2026-03-10T10-00-old.jsonl", 120)
    touch_mtime(pi_dir / "2026-03-10T12-00-new.jsonl", 220)

    gemini_history = home / ".gemini" / "history" / "tmp-project"
    gemini_history.mkdir(parents=True, exist_ok=True)
    (gemini_history / ".project_root").write_text(str(project_dir), encoding="utf-8")
    gemini_chats = home / ".gemini" / "tmp" / "tmp-project" / "chats"
    gemini_chats.mkdir(parents=True, exist_ok=True)
    (gemini_chats / "session-old.json").write_text(
        json.dumps(
            {
                "sessionId": "gem-old",
                "startTime": "2026-03-10T08:00:00Z",
                "lastUpdated": "2026-03-10T08:05:00Z",
                "messages": [{"type": "user", "content": [{"text": "old"}]}],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (gemini_chats / "session-new.json").write_text(
        json.dumps(
            {
                "sessionId": "gem-new",
                "startTime": "2026-03-10T13:00:00Z",
                "lastUpdated": "2026-03-10T13:05:00Z",
                "messages": [
                    {"type": "user", "content": [{"text": "new"}]},
                    {"type": "gemini", "content": "ok", "model": "gemini-3-flash-preview"},
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    touch_mtime(gemini_chats / "session-old.json", 130)
    touch_mtime(gemini_chats / "session-new.json", 230)

    return home


class TestProviderLatestContract:
    def test_sample_valid(self):
        sample_path = ROOT / "contracts" / "examples" / "provider-latest.sample.json"
        data = json.loads(sample_path.read_text(encoding="utf-8"))
        is_valid, errors = validate_against_contract(data, "provider-latest")
        assert is_valid, f"Validation errors: {errors}"


class TestProviderLatestCli:
    def test_ct_provider_latest_emits_valid_contract(self, tmp_path: Path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        home = make_fake_home(tmp_path, project_dir)
        output_file = tmp_path / "latest.json"

        env = os.environ.copy()
        env["HOME"] = str(home)

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "ct-provider-latest" / "main.py"),
                "--project-dir",
                str(project_dir),
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            env=env,
        )

        assert result.returncode == 0, result.stderr
        payload = json.loads(output_file.read_text(encoding="utf-8"))
        is_valid, errors = validate_against_contract(payload, "provider-latest")
        assert is_valid, errors
        assert payload["meta"]["providers_found"] == 4

        by_name = {item["provider"]: item for item in payload["providers"]}
        assert by_name["claude"]["session_id"] == "claude-new"
        assert by_name["qwen"]["session_id"] == "qwen-b"
        assert by_name["pi"]["session_id"] == "pi-new"
        assert by_name["pi"]["model"] == "glm-5"
        assert by_name["pi"]["api_provider"] == "zai"
        assert by_name["gemini"]["session_id"] == "gem-new"

    def test_ct_provider_latest_provider_filter(self, tmp_path: Path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()
        home = make_fake_home(tmp_path, project_dir)

        env = os.environ.copy()
        env["HOME"] = str(home)

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "ct-provider-latest" / "main.py"),
                "--project-dir",
                str(project_dir),
                "--provider",
                "pi",
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
            env=env,
        )

        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["meta"]["providers_requested"] == ["pi"]
        assert len(payload["providers"]) == 1
        assert payload["providers"][0]["provider"] == "pi"

    def test_ct_provider_latest_invalid_provider_returns_invalid_args(self, tmp_path: Path):
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools" / "ct-provider-latest" / "main.py"),
                "--project-dir",
                str(project_dir),
                "--provider",
                "unknown",
            ],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )

        assert result.returncode == 2
        assert "Unknown provider" in result.stderr
