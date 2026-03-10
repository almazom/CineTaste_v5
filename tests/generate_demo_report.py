#!/usr/bin/env python3
"""
Generate demo E2E report for testing visualization.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

REPORTS_DIR = Path("reports/e2e")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

run_id = datetime.now().strftime("%Y%m%d-%H%M%S")

# Create demo report data
demo_report = {
    "run_id": run_id,
    "start_time": (datetime.now() - timedelta(seconds=45)).isoformat(),
    "end_time": datetime.now().isoformat(),
    "status": "completed",
    "project": {
        "name": "CineTaste v5",
        "phase": "7.5",
        "methodology": "Prometheus-Vassa Plamenny",
    },
    "summary": {
        "total_scenarios": 8,
        "total_steps": 23,
        "passed": 21,
        "failed": 2,
        "skipped": 0,
        "pass_rate": 91.3,
    },
    "scenarios": [
        {
            "id": "GP-001",
            "name": "Full pipeline happy path — fetch to Telegram delivery",
            "feature_file": "tests/features/golden_paths.feature",
            "tags": ["@critical", "@golden-path", "@P0", "@happy-path"],
            "status": "success",
            "duration_ms": 4523,
            "steps": [
                {"name": "Validate pipeline configuration", "status": "success", "duration_ms": 12, "error": ""},
                {"name": "Execute pipeline dry-run", "status": "success", "duration_ms": 4200, "error": ""},
                {"name": "Validate send-confirmation", "status": "success", "duration_ms": 89, "error": ""},
                {"name": "Check artifacts preserved", "status": "success", "duration_ms": 222, "error": ""},
            ],
        },
        {
            "id": "GP-002",
            "name": "Cached analysis replay — skip to format and send",
            "feature_file": "tests/features/golden_paths.feature",
            "tags": ["@critical", "@golden-path", "@P0"],
            "status": "success",
            "duration_ms": 2134,
            "steps": [
                {"name": "Validate cached analysis file", "status": "success", "duration_ms": 5, "error": ""},
                {"name": "Execute pipeline with --input", "status": "success", "duration_ms": 1890, "error": ""},
                {"name": "Verify stages skipped", "status": "success", "duration_ms": 239, "error": ""},
            ],
        },
        {
            "id": "GP-003",
            "name": "Resend existing message — recovery workflow",
            "feature_file": "tests/features/golden_paths.feature",
            "tags": ["@critical", "@golden-path", "@P0", "@resend"],
            "status": "failed",
            "duration_ms": 1523,
            "steps": [
                {"name": "Create test message file", "status": "success", "duration_ms": 8, "error": ""},
                {"name": "Execute resend dry-run", "status": "failed", "duration_ms": 1450, "error": "Command failed with exit code 1: ./run --dry-run --resend /tmp/test-message.txt\nError: Message file not found"},
                {"name": "Validate resend confirmation", "status": "success", "duration_ms": 65, "error": ""},
            ],
        },
        {
            "id": "BC-001",
            "name": "Zero movies from source",
            "feature_file": "tests/features/boundary_cases.feature",
            "tags": ["@boundary", "@P1"],
            "status": "success",
            "duration_ms": 890,
            "steps": [
                {"name": "Create empty movie batch", "status": "success", "duration_ms": 3, "error": ""},
                {"name": "Process empty batch through pipeline", "status": "success", "duration_ms": 887, "error": ""},
            ],
        },
        {
            "id": "BC-005",
            "name": "Score threshold boundaries",
            "feature_file": "tests/features/boundary_cases.feature",
            "tags": ["@boundary", "@P1"],
            "status": "success",
            "duration_ms": 234,
            "steps": [
                {"name": "Run filter threshold validation", "status": "success", "duration_ms": 234, "error": ""},
            ],
        },
        {
            "id": "RP-001",
            "name": "Source unavailable — graceful failure",
            "feature_file": "tests/features/recovery_paths.feature",
            "tags": ["@recovery", "@P1"],
            "status": "success",
            "duration_ms": 156,
            "steps": [
                {"name": "Test ct-fetch error handling", "status": "success", "duration_ms": 156, "error": ""},
            ],
        },
        {
            "id": "RP-006",
            "name": "Contract violation detection",
            "feature_file": "tests/features/recovery_paths.feature",
            "tags": ["@recovery", "@P2"],
            "status": "failed",
            "duration_ms": 89,
            "steps": [
                {"name": "Validate contract checking", "status": "failed", "duration_ms": 89, "error": "ModuleNotFoundError: No module named 'tools.ct_filter.main'"},
            ],
        },
    ],
}

# Save JSON report
json_path = REPORTS_DIR / f"e2e-report-{run_id}.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(demo_report, f, indent=2, ensure_ascii=False)

print(f"✓ Demo JSON report: {json_path}")

# Save text summary
txt_path = REPORTS_DIR / f"e2e-summary-{run_id}.txt"
with open(txt_path, "w", encoding="utf-8") as f:
    f.write("=" * 72 + "\n")
    f.write("  CineTaste v5 — E2E Integration Test Summary\n")
    f.write("=" * 72 + "\n\n")
    f.write(f"Run ID: {run_id}\n")
    f.write(f"Status: COMPLETED\n\n")
    s = demo_report["summary"]
    f.write("RESULTS:\n")
    f.write(f"  ✓ Passed: {s['passed']}\n")
    f.write(f"  ✗ Failed: {s['failed']}\n")
    f.write(f"  ⚠ Skipped: {s['skipped']}\n")
    f.write(f"  Pass Rate: {s['pass_rate']}%\n")

print(f"✓ Demo text summary: {txt_path}")

# Generate HTML report
import subprocess
html_path = REPORTS_DIR / f"e2e-report-{run_id}.html"
subprocess.run(
    ["python3", "tests/e2e_html_report.py", str(json_path), "-o", str(html_path)],
    capture_output=True,
    text=True,
)
print(f"✓ Demo HTML report: {html_path}")

# Generate dashboard
subprocess.run(
    ["python3", "tests/e2e_dashboard.py"],
    capture_output=True,
    text=True,
)
print(f"✓ Dashboard: reports/e2e/dashboard.html")

print("\n✓ Demo reports generated successfully!")
print(f"  Run ID: {run_id}")
print(f"  Pass Rate: {demo_report['summary']['pass_rate']}%")
print(f"  Scenarios: {demo_report['summary']['total_scenarios']}")
print(f"  Steps: {demo_report['summary']['total_steps']}")
