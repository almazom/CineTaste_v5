#!/usr/bin/env python3
"""
CineTaste E2E Dashboard Generator
==================================

Creates a comprehensive dashboard with:
- Run history comparison
- Trend analysis
- Scenario breakdown
- Performance metrics
- Interactive charts
"""

from __future__ import annotations
import sys

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def find_all_reports(reports_dir: Path) -> List[Path]:
    """Find all E2E JSON reports."""
    return sorted(reports_dir.glob("e2e-report-*.json"), reverse=True)


def load_reports(reports_dir: Path) -> List[Dict[str, Any]]:
    """Load all E2E reports."""
    reports = []
    for report_path in find_all_reports(reports_dir):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                reports.append(json.load(f))
        except (json.JSONDecodeError, IOError):
            continue
    return reports


def calculate_trends(reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate trends from historical data."""
    if not reports:
        return {}

    trends = {
        "total_runs": len(reports),
        "pass_rates": [],
        "durations": [],
        "failed_counts": [],
        "labels": [],
    }

    for report in reversed(reports[-10:]):  # Last 10 runs
        s = report.get("summary", {})
        trends["pass_rates"].append(s.get("pass_rate", 0))
        trends["durations"].append(
            int((datetime.fromisoformat(report.get("end_time", report["start_time"])) -
                 datetime.fromisoformat(report["start_time"])).total_seconds())
        )
        trends["failed_counts"].append(s.get("failed", 0))
        trends["labels"].append(report["run_id"][-8:])  # Last 8 chars

    # Calculate averages
    trends["avg_pass_rate"] = sum(trends["pass_rates"]) / len(trends["pass_rates"]) if trends["pass_rates"] else 0
    trends["avg_duration"] = sum(trends["durations"]) / len(trends["durations"]) if trends["durations"] else 0
    trends["best_pass_rate"] = max(trends["pass_rates"]) if trends["pass_rates"] else 0
    trends["worst_pass_rate"] = min(trends["pass_rates"]) if trends["pass_rates"] else 0

    return trends


def generate_dashboard_html(
    reports: List[Dict[str, Any]],
    trends: Dict[str, Any],
    output_path: Path,
) -> Path:
    """Generate dashboard HTML."""

    latest = reports[0] if reports else None
    latest_summary = latest.get("summary", {}) if latest else {}

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CineTaste E2E Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary: #6366f1;
            --success: #22c55e;
            --failure: #ef4444;
            --warning: #f59e0b;
            --bg: #f8fafc;
            --card-bg: white;
            --text: #1e293b;
            --text-muted: #64748b;
            --border: #e2e8f0;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            padding: 2rem;
        }}

        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}

        .header {{
            background: linear-gradient(135deg, var(--primary) 0%, #8b5cf6 100%);
            color: white;
            padding: 2rem;
            border-radius: 1rem;
            margin-bottom: 2rem;
        }}

        .header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}

        .header p {{
            opacity: 0.9;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .stat-card {{
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }}

        .stat-card .label {{
            font-size: 0.875rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }}

        .stat-card .value {{
            font-size: 2rem;
            font-weight: bold;
            color: var(--text);
        }}

        .stat-card .trend {{
            font-size: 0.875rem;
            margin-top: 0.5rem;
        }}

        .stat-card .trend.up {{
            color: var(--success);
        }}

        .stat-card .trend.down {{
            color: var(--failure);
        }}

        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .chart-card {{
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }}

        .chart-card h3 {{
            font-size: 1.125rem;
            margin-bottom: 1rem;
            color: var(--text);
        }}

        .chart-container {{
            position: relative;
            height: 250px;
        }}

        .runs-table {{
            background: var(--card-bg);
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}

        .runs-table h3 {{
            font-size: 1.125rem;
            margin-bottom: 1rem;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
        }}

        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        th {{
            background: var(--bg);
            font-weight: 600;
            color: var(--text-muted);
            font-size: 0.875rem;
            text-transform: uppercase;
        }}

        tr:hover {{
            background: var(--bg);
        }}

        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: 500;
        }}

        .status-badge.success {{
            background: #dcfce7;
            color: #16a34a;
        }}

        .status-badge.failure {{
            background: #fee2e2;
            color: #dc2626;
        }}

        .progress-mini {{
            width: 100px;
            height: 8px;
            background: var(--border);
            border-radius: 4px;
            overflow: hidden;
        }}

        .progress-mini .fill {{
            height: 100%;
            background: var(--success);
            transition: width 0.3s;
        }}

        .scenario-breakdown {{
            margin-top: 2rem;
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }}

        .scenario-breakdown h3 {{
            font-size: 1.125rem;
            margin-bottom: 1rem;
        }}

        .scenario-list {{
            display: grid;
            gap: 1rem;
        }}

        .scenario-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 1rem;
            background: var(--bg);
            border-radius: 0.5rem;
        }}

        .scenario-item .name {{
            font-weight: 500;
        }}

        .scenario-item .stats {{
            display: flex;
            gap: 1rem;
            align-items: center;
        }}

        .footer {{
            text-align: center;
            margin-top: 2rem;
            padding: 2rem;
            color: var(--text-muted);
            font-size: 0.875rem;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}

            .charts-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 CineTaste E2E Dashboard</h1>
            <p>Phase 7.5 Integration Testing — Prometheus-Vassa Methodology</p>
        </div>

        {generate_stats_cards(latest_summary, trends)}

        <div class="charts-grid">
            {generate_pass_rate_chart(trends)}
            {generate_duration_chart(trends)}
        </div>

        {generate_runs_table(reports)}

        {generate_scenario_breakdown(latest)}

        <div class="footer">
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>CineTaste v5.5.0 — E2E Integration Test Suite</p>
        </div>
    </div>

    {generate_chart_scripts(trends)}
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


def generate_stats_cards(summary: Dict[str, Any], trends: Dict[str, Any]) -> str:
    """Generate statistics cards HTML."""
    if not summary:
        return ""

    cards = [
        ("Total Runs", str(trends.get("total_runs", 0)), ""),
        ("Avg Pass Rate", f"{trends.get('avg_pass_rate', 0):.1f}%", "trend"),
        ("Avg Duration", f"{trends.get('avg_duration', 0):.1f}s", "trend"),
        ("Last Pass Rate", f"{summary.get('pass_rate', 0)}%", "trend"),
    ]

    html = '<div class="stats-grid">'
    for label, value, trend_class in cards:
        html += f"""
            <div class="stat-card">
                <div class="label">{label}</div>
                <div class="value">{value}</div>
            </div>
        """
    html += '</div>'

    return html


def generate_pass_rate_chart(trends: Dict[str, Any]) -> str:
    """Generate pass rate chart HTML."""
    return """
        <div class="chart-card">
            <h3>📈 Pass Rate Trend</h3>
            <div class="chart-container">
                <canvas id="passRateChart"></canvas>
            </div>
        </div>
    """


def generate_duration_chart(trends: Dict[str, Any]) -> str:
    """Generate duration chart HTML."""
    return """
        <div class="chart-card">
            <h3>⏱️ Execution Duration</h3>
            <div class="chart-container">
                <canvas id="durationChart"></canvas>
            </div>
        </div>
    """


def generate_runs_table(reports: List[Dict[str, Any]]) -> str:
    """Generate runs history table HTML."""
    if not reports:
        return ""

    rows = ""
    for report in reports[:10]:  # Last 10 runs
        s = report.get("summary", {})
        status_class = "success" if s.get("failed", 0) == 0 else "failure"
        status_icon = "✓" if s.get("failed", 0) == 0 else "✗"

        rows += f"""
            <tr>
                <td><code>{report.get('run_id', 'unknown')[-12:]}</code></td>
                <td>
                    <span class="status-badge {status_class}">
                        {status_icon} {report.get('status', 'unknown').upper()}
                    </span>
                </td>
                <td>{s.get('passed', 0)}</td>
                <td>{s.get('failed', 0)}</td>
                <td>{s.get('skipped', 0)}</td>
                <td>
                    <div class="progress-mini">
                        <div class="fill" style="width: {s.get('pass_rate', 0)}%"></div>
                    </div>
                </td>
                <td>{s.get('pass_rate', 0)}%</td>
                <td>{report.get('start_time', 'N/A')[:16]}</td>
            </tr>
        """

    return f"""
        <div class="runs-table">
            <h3>📋 Run History</h3>
            <table>
                <thead>
                    <tr>
                        <th>Run ID</th>
                        <th>Status</th>
                        <th>Pass</th>
                        <th>Fail</th>
                        <th>Skip</th>
                        <th>Progress</th>
                        <th>Pass Rate</th>
                        <th>Started</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
    """


def generate_scenario_breakdown(report: Optional[Dict[str, Any]]) -> str:
    """Generate scenario breakdown HTML."""
    if not report:
        return ""

    scenarios = report.get("scenarios", [])
    if not scenarios:
        return ""

    items = ""
    for scenario in scenarios:
        status_class = "success" if scenario.get("status") == "success" else "failure"
        status_icon = "✓" if scenario.get("status") == "success" else "✗"

        tags = "".join(
            f'<span class="status-badge {tag.lower()}">{tag}</span>'
            for tag in scenario.get("tags", [])[:3]
        )

        items += f"""
            <div class="scenario-item">
                <div>
                    <div class="name">
                        <span class="status-badge {status_class}">{status_icon}</span>
                        {scenario.get('id', 'Unknown')}: {scenario.get('name', 'Unnamed')}
                    </div>
                    <div style="margin-top: 0.5rem;">{tags}</div>
                </div>
                <div class="stats">
                    <span>{scenario.get('duration_ms', 0)}ms</span>
                    <span>{len(scenario.get('steps', []))} steps</span>
                </div>
            </div>
        """

    return f"""
        <div class="scenario-breakdown">
            <h3>📊 Scenario Breakdown</h3>
            <div class="scenario-list">
                {items}
            </div>
        </div>
    """


def generate_chart_scripts(trends: Dict[str, Any]) -> str:
    """Generate Chart.js scripts."""
    labels = json.dumps(trends.get("labels", []))
    pass_rates = json.dumps(trends.get("pass_rates", []))
    durations = json.dumps(trends.get("durations", []))

    return f"""
    <script>
        // Pass Rate Chart
        new Chart(document.getElementById('passRateChart'), {{
            type: 'line',
            data: {{
                labels: {labels},
                datasets: [{{
                    label: 'Pass Rate (%)',
                    data: {pass_rates},
                    borderColor: '#22c55e',
                    backgroundColor: 'rgba(34, 197, 94, 0.1)',
                    fill: true,
                    tension: 0.4,
                }}],
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100,
                    }},
                }},
            }},
        }});

        // Duration Chart
        new Chart(document.getElementById('durationChart'), {{
            type: 'bar',
            data: {{
                labels: {labels},
                datasets: [{{
                    label: 'Duration (seconds)',
                    data: {durations},
                    backgroundColor: '#6366f1',
                }}],
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                }},
            }},
        }});
    </script>
    """


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate E2E Dashboard")
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=Path("reports/e2e"),
        help="Input directory with E2E reports",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("reports/e2e/dashboard.html"),
        help="Output HTML file",
    )

    args = parser.parse_args()

    # Load reports
    reports = load_reports(args.input)

    if not reports:
        print("✗ No E2E reports found. Run 'make test-e2e' first.")
        sys.exit(1)

    # Calculate trends
    trends = calculate_trends(reports)

    # Generate dashboard
    args.output.parent.mkdir(parents=True, exist_ok=True)
    generate_dashboard_html(reports, trends, args.output)

    print(f"✓ Dashboard generated: {args.output}")
    print(f"  Total runs: {trends['total_runs']}")
    print(f"  Avg pass rate: {trends['avg_pass_rate']:.1f}%")


if __name__ == "__main__":
    main()
