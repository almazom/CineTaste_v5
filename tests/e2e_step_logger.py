#!/usr/bin/env python3
"""
CineTaste E2E Step Logger
==========================

Captures detailed step-by-step logs with:
- Timestamped entries
- Command output capture
- Artifact collection
- Error context preservation
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class StepLogger:
    """Detailed step-by-step logger with artifact collection."""

    def __init__(self, run_id: str, output_dir: Optional[Path] = None):
        self.run_id = run_id
        self.output_dir = output_dir or Path(f"reports/e2e/{run_id}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.steps_dir = self.output_dir / "steps"
        self.steps_dir.mkdir(exist_ok=True)

        self.artifacts_dir = self.output_dir / "artifacts"
        self.artifacts_dir.mkdir(exist_ok=True)

        self.log_file = self.output_dir / "step-log.jsonl"
        self.summary_file = self.output_dir / "summary.json"

        self.steps: List[Dict[str, Any]] = []
        self.current_step: Optional[Dict[str, Any]] = None

    def start_step(self, name: str, command: str, description: str = "") -> Dict[str, Any]:
        """Start logging a new step."""
        self.current_step = {
            "step_id": f"step-{len(self.steps) + 1:03d}",
            "name": name,
            "command": command,
            "description": description,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": "running",
            "exit_code": None,
            "stdout": "",
            "stderr": "",
            "duration_ms": 0,
            "artifacts": [],
            "metadata": {},
        }
        return self.current_step

    def complete_step(
        self,
        result: subprocess.CompletedProcess,
        artifacts: Optional[List[Path]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Complete the current step with results."""
        if not self.current_step:
            raise ValueError("No current step to complete")

        step = self.current_step
        step["end_time"] = datetime.now().isoformat()
        step["exit_code"] = result.returncode
        step["stdout"] = result.stdout
        step["stderr"] = result.stderr
        step["status"] = "success" if result.returncode == 0 else "failed"

        # Calculate duration
        start = datetime.fromisoformat(step["start_time"])
        end = datetime.fromisoformat(step["end_time"])
        step["duration_ms"] = int((end - start).total_seconds() * 1000)

        # Collect artifacts
        if artifacts:
            for artifact_path in artifacts:
                if artifact_path.exists():
                    dest = self.artifacts_dir / f"{step['step_id']}_{artifact_path.name}"
                    shutil.copy2(artifact_path, dest)
                    step["artifacts"].append(str(dest))

        # Add metadata
        if metadata:
            step["metadata"].update(metadata)

        # Write to JSONL log
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(step, ensure_ascii=False) + "\n")

        self.steps.append(step)
        self.current_step = None

        return step

    def collect_artifact(self, source: Path, name: Optional[str] = None) -> Path:
        """Collect an artifact from a source path."""
        if not source.exists():
            return None

        artifact_name = name or source.name
        dest = self.artifacts_dir / f"{artifact_name}"
        shutil.copy2(source, dest)
        return dest

    def save_summary(self) -> Path:
        """Save run summary."""
        total_steps = len(self.steps)
        passed = sum(1 for s in self.steps if s["status"] == "success")
        failed = sum(1 for s in self.steps if s["status"] == "failed")

        summary = {
            "run_id": self.run_id,
            "total_steps": total_steps,
            "passed": passed,
            "failed": failed,
            "pass_rate": round(passed / max(total_steps, 1) * 100, 2),
            "steps": self.steps,
            "generated_at": datetime.now().isoformat(),
        }

        with open(self.summary_file, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        return self.summary_file

    def print_step_summary(self, step: Dict[str, Any]) -> None:
        """Print a formatted step summary."""
        colors = {
            "success": "\033[92m",
            "failed": "\033[91m",
            "running": "\033[93m",
            "reset": "\033[0m",
        }

        status = step["status"]
        color = colors.get(status, colors["reset"])
        icon = "✓" if status == "success" else "✗" if status == "failed" else "▶"

        print(f"\n{color}{icon} {step['name']} ({step['duration_ms']}ms){colors['reset']}", file=sys.stderr)

        if step.get("command"):
            print(f"  Command: {step['command'][:100]}{'...' if len(step['command']) > 100 else ''}", file=sys.stderr)

        if status == "failed" and step.get("stderr"):
            print(f"  Error: {step['stderr'][:200]}{'...' if len(step['stderr']) > 200 else ''}", file=sys.stderr)

        if step.get("artifacts"):
            print(f"  Artifacts: {', '.join(Path(a).name for a in step['artifacts'])}", file=sys.stderr)


def run_step_with_logging(
    logger: StepLogger,
    name: str,
    command: str,
    description: str = "",
    cwd: Optional[Path] = None,
    capture_artifacts: Optional[List[Path]] = None,
) -> Dict[str, Any]:
    """Run a command with full logging."""
    step = logger.start_step(name, command, description)

    print(f"▶ {name}", file=sys.stderr)

    result = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        cwd=str(cwd or Path.cwd()),
        timeout=300,
    )

    artifacts = []
    if capture_artifacts:
        for artifact_path in capture_artifacts:
            if artifact_path.exists():
                artifacts.append(artifact_path)

    step = logger.complete_step(result, artifacts=artifacts)
    logger.print_step_summary(step)

    return step


def main():
    """CLI entry point for standalone step logging."""
    import argparse

    parser = argparse.ArgumentParser(description="E2E Step Logger")
    parser.add_argument("--run-id", required=True, help="Run ID")
    parser.add_argument("--output", type=Path, help="Output directory")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("--name", default="Unnamed step", help="Step name")
    parser.add_argument("--description", default="", help="Step description")

    args = parser.parse_args()

    logger = StepLogger(args.run_id, args.output)
    step = run_step_with_logging(
        logger,
        args.name,
        args.command,
        args.description,
    )

    logger.save_summary()

    sys.exit(0 if step["status"] == "success" else 1)


if __name__ == "__main__":
    main()
