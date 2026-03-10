#!/usr/bin/env python3
"""
E2E Report Summary Display
"""

import json
import sys
from pathlib import Path

def show_latest():
    """Show latest E2E run summary."""
    reports_dir = Path("reports/e2e")
    reports = sorted(reports_dir.glob("e2e-report-*.json"), reverse=True)
    
    if not reports:
        print("✗ No E2E reports found. Run 'make test-e2e' first.")
        sys.exit(1)
    
    with open(reports[0], "r", encoding="utf-8") as f:
        data = json.load(f)
    
    s = data["summary"]
    
    print("")
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║  Latest E2E Run Summary                                                  ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print("")
    print(f"Run ID: {data['run_id']}")
    print(f"Status: {data['status'].upper()}")
    print(f"Started: {data['start_time']}")
    print(f"Completed: {data.get('end_time', 'N/A')}")
    print("")
    print("RESULTS:")
    print(f"  ✓ Passed: {s['passed']}")
    print(f"  ✗ Failed: {s['failed']}")
    print(f"  ⚠ Skipped: {s['skipped']}")
    print(f"  Pass Rate: {s['pass_rate']}%")
    print("")
    print("SCENARIOS:")
    for sc in data["scenarios"][:5]:
        icon = "✓" if sc["status"] == "success" else "✗"
        name = sc["name"][:50] + "..." if len(sc["name"]) > 50 else sc["name"]
        print(f"  {icon} {sc['id']}: {name} ({sc['duration_ms']}ms)")

def show_history():
    """Show E2E run history."""
    reports_dir = Path("reports/e2e")
    reports = sorted(reports_dir.glob("e2e-report-*.json"), reverse=True)[:10]
    
    if not reports:
        print("✗ No E2E reports found.")
        sys.exit(1)
    
    print("")
    print("╔══════════════════════════════════════════════════════════════════════════╗")
    print("║  E2E Run History                                                         ║")
    print("╚══════════════════════════════════════════════════════════════════════════╝")
    print("")
    print(f"{'RUN ID':<25}  {'STATUS':<10}  {'PASS':<8}  {'FAIL':<8}  {'SKIP':<8}  {'PASS RATE':<10}")
    print("─" * 85)
    
    for report_path in reports:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        s = data["summary"]
        status = "✓" if s["failed"] == 0 else "✗"
        print(f"{data['run_id']:<25}  {status:<10}  {s['passed']:<8}  {s['failed']:<8}  {s['skipped']:<8}  {s['pass_rate']}%")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "history":
        show_history()
    else:
        show_latest()
