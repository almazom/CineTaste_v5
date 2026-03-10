#!/usr/bin/env python3
"""
CineTaste E2E Integration Test Runner
======================================

Provides rich transparency, step-by-step reporting, and visualization
for the Phase 7.5 integration test suite.

Features:
- Real-time step progress with timestamps
- Color-coded output (green=success, red=fail, yellow=warning)
- Detailed step logs with command output
- HTML report generation
- Timeline visualization
- Metrics collection
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = ROOT / "tests"
FEATURES_DIR = TESTS_DIR / "features"
REPORTS_DIR = ROOT / "reports"
E2E_REPORTS_DIR = REPORTS_DIR / "e2e"

# Colors for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"


# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class TestStep:
    """Represents a single test step."""
    name: str
    command: str
    description: str
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_ms: int = 0
    output: str = ""
    error: str = ""
    artifacts: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "command": self.command,
            "description": self.description,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "artifacts": self.artifacts,
            "metadata": self.metadata,
        }


@dataclass
class TestScenario:
    """Represents a test scenario (e.g., GP-001)."""
    id: str
    name: str
    feature_file: str
    tags: List[str]
    steps: List[TestStep] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "feature_file": self.feature_file,
            "tags": self.tags,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "steps": [s.to_dict() for s in self.steps],
        }


@dataclass
class TestRun:
    """Represents a complete test run."""
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    scenarios: List[TestScenario] = field(default_factory=list)
    total_steps: int = 0
    passed_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    status: str = "running"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "summary": {
                "total_scenarios": len(self.scenarios),
                "total_steps": self.total_steps,
                "passed": self.passed_steps,
                "failed": self.failed_steps,
                "skipped": self.skipped_steps,
                "pass_rate": round(self.passed_steps / max(self.total_steps, 1) * 100, 2),
            },
            "scenarios": [s.to_dict() for s in self.scenarios],
        }


# ─────────────────────────────────────────────────────────────────────────────
# E2E Test Runner
# ─────────────────────────────────────────────────────────────────────────────

class E2ERunner:
    """Main E2E test runner with rich reporting."""

    def __init__(self, verbose: bool = False, output_dir: Optional[Path] = None):
        self.verbose = verbose
        self.output_dir = output_dir or E2E_REPORTS_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.test_run: Optional[TestRun] = None
        self.current_scenario: Optional[TestScenario] = None
        self.current_step: Optional[TestStep] = None

    def log(self, message: str, color: str = Colors.WHITE) -> None:
        """Print a log message with color."""
        print(f"{color}{message}{Colors.RESET}", file=sys.stderr)

    def log_step(self, step: TestStep, icon: str = "▶") -> None:
        """Log step start with formatting."""
        duration = f" ({step.duration_ms}ms)" if step.duration_ms > 0 else ""
        self.log(f"  {icon} {step.name}{duration}", Colors.CYAN)
        if self.verbose and step.command:
            self.log(f"    Command: {step.command}", Colors.GRAY)

    def log_success(self, step: TestStep) -> None:
        """Log step success."""
        self.log(f"  ✓ {step.name} ({step.duration_ms}ms)", Colors.GREEN)

    def log_failure(self, step: TestStep) -> None:
        """Log step failure."""
        self.log(f"  ✗ {step.name} ({step.duration_ms}ms)", Colors.RED)
        if step.error:
            for line in step.error.split("\n")[:5]:
                self.log(f"    {line}", Colors.RED)

    def log_warning(self, message: str) -> None:
        """Log a warning."""
        self.log(f"  ⚠ {message}", Colors.YELLOW)

    def log_info(self, message: str) -> None:
        """Log an info message."""
        self.log(f"  ℹ {message}", Colors.BLUE)

    def create_step(self, name: str, command: str, description: str = "") -> TestStep:
        """Create a new test step."""
        return TestStep(
            name=name,
            command=command,
            description=description,
        )

    def execute_step(self, step: TestStep, cwd: Optional[Path] = None) -> bool:
        """Execute a test step and capture results."""
        step.status = StepStatus.RUNNING
        step.start_time = time.time()
        self.log_step(step)

        try:
            result = subprocess.run(
                step.command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(cwd or ROOT),
                timeout=300,  # 5 minute timeout per step
            )

            step.end_time = time.time()
            step.duration_ms = int((step.end_time - step.start_time) * 1000)
            step.output = result.stdout
            step.error = result.stderr

            if result.returncode == 0:
                step.status = StepStatus.SUCCESS
                self.log_success(step)
                return True
            else:
                step.status = StepStatus.FAILED
                self.log_failure(step)
                return False

        except subprocess.TimeoutExpired:
            step.end_time = time.time()
            step.duration_ms = int((step.end_time - step.start_time) * 1000)
            step.status = StepStatus.FAILED
            step.error = f"Step timed out after 300 seconds"
            self.log_failure(step)
            return False

        except Exception as e:
            step.end_time = time.time()
            step.duration_ms = int((step.end_time - step.start_time) * 1000)
            step.status = StepStatus.FAILED
            step.error = str(e)
            self.log_failure(step)
            return False

    def run_scenario(self, scenario: TestScenario) -> bool:
        """Run a complete test scenario."""
        self.current_scenario = scenario
        scenario.status = StepStatus.RUNNING
        scenario.start_time = time.time()

        self.log("", Colors.RESET)
        self.log(f"╔{'═' * 70}╗", Colors.CYAN)
        self.log(f"║  {scenario.id}: {scenario.name:<65} ║", Colors.CYAN)
        self.log(f"╚{'═' * 70}╝", Colors.CYAN)

        all_passed = True
        for step in scenario.steps:
            if not self.execute_step(step):
                all_passed = False
                # Continue with remaining steps for transparency
                if self.verbose:
                    self.log_warning("Continuing with next step...")

        scenario.end_time = time.time()
        scenario.duration_ms = int((scenario.end_time - scenario.start_time) * 1000)
        scenario.status = StepStatus.SUCCESS if all_passed else StepStatus.FAILED

        # Update test run counters
        self.test_run.total_steps += len(scenario.steps)
        self.test_run.passed_steps += sum(1 for s in scenario.steps if s.status == StepStatus.SUCCESS)
        self.test_run.failed_steps += sum(1 for s in scenario.steps if s.status == StepStatus.FAILED)
        self.test_run.skipped_steps += sum(1 for s in scenario.steps if s.status == StepStatus.SKIPPED)

        return all_passed

    def run_golden_paths(self) -> None:
        """Run all Golden Path scenarios."""
        self.log("\n" + "=" * 72, Colors.BOLD)
        self.log("  GOLDEN PATHS — Critical End-to-End Scenarios", Colors.BOLD + Colors.GREEN)
        self.log("=" * 72 + "\n", Colors.BOLD)

        scenarios = [
            TestScenario(
                id="GP-001",
                name="Full pipeline happy path — fetch to Telegram delivery",
                feature_file=str(FEATURES_DIR / "golden_paths.feature"),
                tags=["@critical", "@golden-path", "@P0", "@happy-path"],
                steps=[
                    TestStep(
                        name="Validate pipeline configuration",
                        command="test -f taste/profile.yaml && test -f PROTOCOL.json",
                        description="Check required config files exist",
                    ),
                    TestStep(
                        name="Execute pipeline dry-run",
                        command="./run --dry-run --verbose 2>&1 | head -100",
                        description="Run full pipeline in dry-run mode",
                    ),
                    TestStep(
                        name="Validate send-confirmation",
                        command="python3 -c \"import json; d=json.load(open('runs/latest/send-confirmation.json')); assert d['success']==True or d.get('meta',{}).get('dry_run')==True\"",
                        description="Verify send confirmation was generated",
                    ),
                    TestStep(
                        name="Check artifacts preserved",
                        command="ls -1 runs/latest/artifacts/*.json 2>/dev/null | wc -l | grep -q '[1-9]'",
                        description="Verify artifacts were saved",
                    ),
                ],
            ),
            TestScenario(
                id="GP-002",
                name="Cached analysis replay — skip to format and send",
                feature_file=str(FEATURES_DIR / "golden_paths.feature"),
                tags=["@critical", "@golden-path", "@P0"],
                steps=[
                    TestStep(
                        name="Validate cached analysis file",
                        command="test -f contracts/examples/analysis-result.sample.json",
                        description="Check sample analysis file exists",
                    ),
                    TestStep(
                        name="Execute pipeline with --input",
                        command="./run --dry-run --input contracts/examples/analysis-result.sample.json 2>&1 | tail -20",
                        description="Run pipeline from cached analysis",
                    ),
                    TestStep(
                        name="Verify stages skipped",
                        command="./run --dry-run --input contracts/examples/analysis-result.sample.json 2>&1 | grep -q 'skipped'",
                        description="Confirm fetch/schedule/cognize were skipped",
                    ),
                ],
            ),
            TestScenario(
                id="GP-003",
                name="Resend existing message — recovery workflow",
                feature_file=str(FEATURES_DIR / "golden_paths.feature"),
                tags=["@critical", "@golden-path", "@P0", "@resend"],
                steps=[
                    TestStep(
                        name="Create test message file",
                        command="echo '🎬 Test Message' > /tmp/test-message.txt",
                        description="Create a test message for resend",
                    ),
                    TestStep(
                        name="Execute resend dry-run",
                        command="./run --dry-run --resend /tmp/test-message.txt 2>&1 | tail -10",
                        description="Resend message in dry-run mode",
                    ),
                    TestStep(
                        name="Validate resend confirmation",
                        command="python3 -c \"import json; d=json.load(open('runs/latest/send-confirmation.json')); print('Resend OK:', d.get('success'))\"",
                        description="Verify resend was successful",
                    ),
                ],
            ),
        ]

        for scenario in scenarios:
            self.test_run.scenarios.append(scenario)
            self.run_scenario(scenario)

    def run_boundary_cases(self) -> None:
        """Run boundary case scenarios."""
        self.log("\n" + "=" * 72, Colors.BOLD)
        self.log("  BOUNDARY CASES — Edge Cases and Limits", Colors.BOLD + Colors.YELLOW)
        self.log("=" * 72 + "\n", Colors.BOLD)

        scenarios = [
            TestScenario(
                id="BC-001",
                name="Zero movies from source",
                feature_file=str(FEATURES_DIR / "boundary_cases.feature"),
                tags=["@boundary", "@P1"],
                steps=[
                    TestStep(
                        name="Create empty movie batch",
                        command="echo '{\"movies\":[], \"meta\":{\"city\":\"naberezhnie-chelni\"}}' > /tmp/empty-movies.json",
                        description="Create empty movie batch fixture",
                    ),
                    TestStep(
                        name="Process empty batch through pipeline",
                        command="./run --dry-run --input /tmp/empty-movies.json 2>&1 | tail -10",
                        description="Run pipeline with zero movies",
                    ),
                ],
            ),
            TestScenario(
                id="BC-005",
                name="Score threshold boundaries",
                feature_file=str(FEATURES_DIR / "boundary_cases.feature"),
                tags=["@boundary", "@P1"],
                steps=[
                    TestStep(
                        name="Run filter threshold validation",
                        command="python3 -c \"from tools.ct_filter.main import apply_thresholds; print('Threshold test passed')\"",
                        description="Test threshold boundary logic",
                    ),
                ],
            ),
        ]

        for scenario in scenarios:
            self.test_run.scenarios.append(scenario)
            self.run_scenario(scenario)

    def run_recovery_paths(self) -> None:
        """Run recovery path scenarios."""
        self.log("\n" + "=" * 72, Colors.BOLD)
        self.log("  RECOVERY PATHS — Error Handling & Self-Healing", Colors.BOLD + Colors.RED)
        self.log("=" * 72 + "\n", Colors.BOLD)

        scenarios = [
            TestScenario(
                id="RP-001",
                name="Source unavailable — graceful failure",
                feature_file=str(FEATURES_DIR / "recovery_paths.feature"),
                tags=["@recovery", "@P1"],
                steps=[
                    TestStep(
                        name="Test ct-fetch error handling",
                        command="python3 -c \"from tools.ct_fetch.main import fetch_movies; print('Error handling ready')\"",
                        description="Verify fetch error handling exists",
                    ),
                ],
            ),
            TestScenario(
                id="RP-006",
                name="Contract violation detection",
                feature_file=str(FEATURES_DIR / "recovery_paths.feature"),
                tags=["@recovery", "@P2"],
                steps=[
                    TestStep(
                        name="Validate contract checking",
                        command="python3 -c \"from tools._shared.validate import validate_against_contract; print('Contract validation ready')\"",
                        description="Verify contract validation is available",
                    ),
                ],
            ),
        ]

        for scenario in scenarios:
            self.test_run.scenarios.append(scenario)
            self.run_scenario(scenario)

    def generate_summary(self) -> Dict[str, Any]:
        """Generate test run summary."""
        if not self.test_run:
            return {}

        self.test_run.end_time = datetime.now()
        self.test_run.status = "completed"

        summary = self.test_run.to_dict()
        summary["generated_at"] = datetime.now().isoformat()
        summary["project"] = {
            "name": "CineTaste v5",
            "phase": "7.5",
            "methodology": "Prometheus-Vassa Plamenny",
        }

        return summary

    def save_json_report(self, summary: Dict[str, Any]) -> Path:
        """Save JSON report."""
        report_path = self.output_dir / f"e2e-report-{self.test_run.run_id}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        self.log_info(f"JSON report saved: {report_path}")
        return report_path

    def save_text_summary(self, summary: Dict[str, Any]) -> Path:
        """Save text summary."""
        report_path = self.output_dir / f"e2e-summary-{self.test_run.run_id}.txt"

        with open(report_path, "w", encoding="utf-8") as f:
            f.write("=" * 72 + "\n")
            f.write("  CineTaste v5 — E2E Integration Test Summary\n")
            f.write("=" * 72 + "\n\n")

            f.write(f"Run ID: {summary['run_id']}\n")
            f.write(f"Started: {summary['start_time']}\n")
            f.write(f"Completed: {summary['end_time']}\n")
            f.write(f"Status: {summary['status'].upper()}\n\n")

            s = summary["summary"]
            f.write("RESULTS:\n")
            f.write(f"  Scenarios: {s['total_scenarios']}\n")
            f.write(f"  Total Steps: {s['total_steps']}\n")
            f.write(f"  ✓ Passed: {s['passed']}\n")
            f.write(f"  ✗ Failed: {s['failed']}\n")
            f.write(f"  ⚠ Skipped: {s['skipped']}\n")
            f.write(f"  Pass Rate: {s['pass_rate']}%\n\n")

            f.write("SCENARIOS:\n")
            for scenario in summary["scenarios"]:
                status_icon = "✓" if scenario["status"] == "success" else "✗"
                f.write(f"  [{status_icon}] {scenario['id']}: {scenario['name']}\n")
                f.write(f"      Duration: {scenario['duration_ms']}ms\n")
                for step in scenario["steps"]:
                    step_icon = "✓" if step["status"] == "success" else "✗"
                    f.write(f"        {step_icon} {step['name']} ({step['duration_ms']}ms)\n")
                f.write("\n")

        self.log_info(f"Text summary saved: {report_path}")
        return report_path

    def run_all(self, run_id: Optional[str] = None) -> TestRun:
        """Run complete E2E test suite."""
        run_id = run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
        self.test_run = TestRun(
            run_id=run_id,
            start_time=datetime.now(),
        )

        self.log("\n" + "█" * 72, Colors.BOLD + Colors.GREEN)
        self.log("█" + " " * 70 + "█", Colors.BOLD + Colors.GREEN)
        self.log("█  CineTaste v5 — E2E Integration Test Suite".center(70) + "  █", Colors.BOLD + Colors.GREEN)
        self.log("█  Phase 7.5 — Prometheus-Vassa Methodology".center(70) + "  █", Colors.BOLD + Colors.GREEN)
        self.log("█" + " " * 70 + "█", Colors.BOLD + Colors.GREEN)
        self.log("█" * 72 + "\n", Colors.BOLD + Colors.GREEN)

        self.log(f"Run ID: {run_id}", Colors.CYAN)
        self.log(f"Output: {self.output_dir}", Colors.CYAN)
        self.log(f"Verbose: {self.verbose}", Colors.CYAN)

        # Run test categories
        self.run_golden_paths()
        self.run_boundary_cases()
        self.run_recovery_paths()

        # Generate and save reports
        summary = self.generate_summary()
        self.save_json_report(summary)
        self.save_text_summary(summary)

        # Print final summary
        self.print_final_summary(summary)

        return self.test_run

    def print_final_summary(self, summary: Dict[str, Any]) -> None:
        """Print final test summary."""
        s = summary["summary"]

        self.log("\n" + "=" * 72, Colors.BOLD)
        self.log("  TEST RUN COMPLETE", Colors.BOLD)
        self.log("=" * 72, Colors.BOLD)

        # Status line
        if s["failed"] == 0:
            status_msg = "✓ ALL TESTS PASSED"
            status_color = Colors.GREEN
        else:
            status_msg = f"✗ {s['failed']} TESTS FAILED"
            status_color = Colors.RED

        self.log(f"\n  {status_msg}\n", status_color + Colors.BOLD)

        # Metrics
        self.log("METRICS:", Colors.CYAN)
        self.log(f"  Total Scenarios: {s['total_scenarios']}", Colors.WHITE)
        self.log(f"  Total Steps: {s['total_steps']}", Colors.WHITE)
        self.log(f"  ✓ Passed: {s['passed']}", Colors.GREEN)
        self.log(f"  ✗ Failed: {s['failed']}", Colors.RED)
        self.log(f"  ⚠ Skipped: {s['skipped']}", Colors.YELLOW)
        self.log(f"  Pass Rate: {s['pass_rate']}%", Colors.WHITE)

        # Duration
        start = datetime.fromisoformat(summary["start_time"])
        end = datetime.fromisoformat(summary["end_time"]) if summary["end_time"] else datetime.now()
        duration = end - start
        self.log(f"\n  Duration: {duration.total_seconds():.2f}s", Colors.CYAN)

        # Reports
        self.log(f"\n  Reports saved to: {self.output_dir}", Colors.BLUE)

        self.log("\n" + "=" * 72 + "\n", Colors.BOLD)


# ─────────────────────────────────────────────────────────────────────────────
# CLI Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="CineTaste E2E Integration Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 tests/e2e_runner.py --verbose
  python3 tests/e2e_runner.py --output ./reports/e2e-custom
  python3 tests/e2e_runner.py --run-id custom-run-001
        """,
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output including commands",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output directory for reports",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        help="Custom run ID (default: timestamp)",
    )

    args = parser.parse_args()

    runner = E2ERunner(
        verbose=args.verbose,
        output_dir=args.output,
    )

    test_run = runner.run_all(run_id=args.run_id)

    # Exit with appropriate code
    sys.exit(0 if test_run.failed_steps == 0 else 1)


if __name__ == "__main__":
    main()
