#!/usr/bin/env python3
"""
CineTaste E2E HTML Report Generator
====================================

Generates rich HTML reports with:
- Interactive dashboard
- Timeline visualization
- Step-by-step breakdown
- Color-coded status
- Metrics charts
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


def generate_html_report(
    report_data: Dict[str, Any],
    output_path: Path,
) -> Path:
    """Generate an HTML report from E2E test results."""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CineTaste E2E Test Report — {report_data['run_id']}</title>
    <style>
        :root {{
            --success: #22c55e;
            --success-bg: #dcfce7;
            --failure: #ef4444;
            --failure-bg: #fee2e2;
            --warning: #f59e0b;
            --warning-bg: #fef3c7;
            --info: #3b82f6;
            --info-bg: #dbeafe;
            --gray: #6b7280;
            --gray-light: #f3f4f6;
            --border: #e5e7eb;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}

        .header {{
            background: white;
            border-radius: 1rem;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            font-size: 2rem;
            color: #1f2937;
            margin-bottom: 0.5rem;
        }}

        .header .subtitle {{
            color: var(--gray);
            font-size: 1rem;
        }}

        .header .meta {{
            display: flex;
            gap: 2rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }}

        .header .meta-item {{
            background: var(--gray-light);
            padding: 0.5rem 1rem;
            border-radius: 0.5rem;
            font-size: 0.875rem;
        }}

        .header .meta-item strong {{
            color: #1f2937;
        }}

        .status-banner {{
            padding: 1.5rem 2rem;
            border-radius: 1rem;
            margin-bottom: 2rem;
            font-size: 1.5rem;
            font-weight: bold;
            text-align: center;
        }}

        .status-banner.success {{
            background: var(--success-bg);
            color: var(--success);
            border: 2px solid var(--success);
        }}

        .status-banner.failure {{
            background: var(--failure-bg);
            color: var(--failure);
            border: 2px solid var(--failure);
        }}

        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}

        .metric-card {{
            background: white;
            border-radius: 1rem;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .metric-card .value {{
            font-size: 3rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }}

        .metric-card .label {{
            color: var(--gray);
            font-size: 0.875rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .metric-card.success .value {{ color: var(--success); }}
        .metric-card.failure .value {{ color: var(--failure); }}
        .metric-card.warning .value {{ color: var(--warning); }}
        .metric-card.info .value {{ color: var(--info); }}

        .progress-bar {{
            background: var(--gray-light);
            border-radius: 1rem;
            height: 2rem;
            overflow: hidden;
            margin-bottom: 2rem;
        }}

        .progress-bar .fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--success) 0%, #16a34a 100%);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}

        .scenarios {{
            background: white;
            border-radius: 1rem;
            padding: 2rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}

        .scenarios h2 {{
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            color: #1f2937;
        }}

        .scenario {{
            border: 1px solid var(--border);
            border-radius: 0.75rem;
            margin-bottom: 1.5rem;
            overflow: hidden;
        }}

        .scenario-header {{
            padding: 1rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: pointer;
            transition: background 0.2s;
        }}

        .scenario-header:hover {{
            background: var(--gray-light);
        }}

        .scenario-header.success {{
            background: var(--success-bg);
        }}

        .scenario-header.failure {{
            background: var(--failure-bg);
        }}

        .scenario-title {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .scenario-icon {{
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
        }}

        .scenario-icon.success {{
            background: var(--success);
            color: white;
        }}

        .scenario-icon.failure {{
            background: var(--failure);
            color: white;
        }}

        .scenario-id {{
            font-weight: bold;
            color: #1f2937;
        }}

        .scenario-name {{
            color: var(--gray);
        }}

        .scenario-meta {{
            display: flex;
            gap: 1rem;
            align-items: center;
        }}

        .scenario-duration {{
            background: white;
            padding: 0.25rem 0.75rem;
            border-radius: 0.5rem;
            font-size: 0.875rem;
            color: var(--gray);
        }}

        .scenario-body {{
            display: none;
            padding: 1.5rem;
            border-top: 1px solid var(--border);
        }}

        .scenario.expanded .scenario-body {{
            display: block;
        }}

        .steps-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .steps-table th,
        .steps-table td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}

        .steps-table th {{
            background: var(--gray-light);
            font-weight: 600;
            color: #1f2937;
        }}

        .steps-table tr:last-child td {{
            border-bottom: none;
        }}

        .step-status {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0.75rem;
            border-radius: 0.5rem;
            font-size: 0.875rem;
            font-weight: 500;
        }}

        .step-status.success {{
            background: var(--success-bg);
            color: var(--success);
        }}

        .step-status.failure {{
            background: var(--failure-bg);
            color: var(--failure);
        }}

        .step-error {{
            background: var(--failure-bg);
            color: var(--failure);
            padding: 0.75rem;
            border-radius: 0.5rem;
            font-family: monospace;
            font-size: 0.875rem;
            margin-top: 0.5rem;
            white-space: pre-wrap;
            word-break: break-all;
        }}

        .tags {{
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            margin-top: 0.5rem;
        }}

        .tag {{
            background: var(--info-bg);
            color: var(--info);
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.75rem;
            font-weight: 500;
        }}

        .tag.critical {{
            background: #fecaca;
            color: #dc2626;
        }}

        .tag.golden {{
            background: #fef3c7;
            color: #d97706;
        }}

        .tag.boundary {{
            background: #dbeafe;
            color: #2563eb;
        }}

        .tag.recovery {{
            background: #dcfce7;
            color: #16a34a;
        }}

        .timeline {{
            background: white;
            border-radius: 1rem;
            padding: 2rem;
            margin-top: 2rem;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}

        .timeline h2 {{
            font-size: 1.5rem;
            margin-bottom: 1.5rem;
            color: #1f2937;
        }}

        .timeline-bar {{
            display: flex;
            gap: 0.5rem;
            height: 3rem;
            border-radius: 0.5rem;
            overflow: hidden;
        }}

        .timeline-segment {{
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.75rem;
            transition: opacity 0.2s;
        }}

        .timeline-segment:hover {{
            opacity: 0.8;
        }}

        .timeline-segment.success {{
            background: var(--success);
        }}

        .timeline-segment.failure {{
            background: var(--failure);
        }}

        .footer {{
            text-align: center;
            margin-top: 2rem;
            padding: 2rem;
            color: white;
        }}

        .footer a {{
            color: white;
            text-decoration: underline;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 1rem;
            }}

            .header h1 {{
                font-size: 1.5rem;
            }}

            .metrics-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 CineTaste E2E Test Report</h1>
            <p class="subtitle">Phase 7.5 — Prometheus-Vassa Integration Testing</p>
            <div class="meta">
                <div class="meta-item">
                    <strong>Run ID:</strong> {report_data['run_id']}
                </div>
                <div class="meta-item">
                    <strong>Started:</strong> {report_data['start_time']}
                </div>
                <div class="meta-item">
                    <strong>Completed:</strong> {report_data.get('end_time', 'N/A')}
                </div>
                <div class="meta-item">
                    <strong>Project:</strong> {report_data.get('project', {}).get('name', 'CineTaste v5')}
                </div>
            </div>
        </div>

        {generate_status_banner(report_data)}

        <div class="metrics-grid">
            {generate_metric_cards(report_data)}
        </div>

        <div class="progress-bar">
            <div class="fill" style="width: {report_data['summary']['pass_rate']}%">
                {report_data['summary']['pass_rate']}% Pass Rate
            </div>
        </div>

        <div class="scenarios">
            <h2>📋 Test Scenarios</h2>
            {generate_scenarios(report_data)}
        </div>

        <div class="timeline">
            <h2>⏱️ Execution Timeline</h2>
            {generate_timeline(report_data)}
        </div>

        <div class="footer">
            <p>Generated by CineTaste E2E Report Generator</p>
            <p>Phase 7.5 — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>

    <script>
        // Toggle scenario expansion
        document.querySelectorAll('.scenario-header').forEach(header => {{
            header.addEventListener('click', () => {{
                const scenario = header.parentElement;
                scenario.classList.toggle('expanded');
            }});
        }});
    </script>
</body>
</html>
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return output_path


def generate_status_banner(report_data: Dict[str, Any]) -> str:
    """Generate status banner HTML."""
    s = report_data["summary"]

    if s["failed"] == 0:
        css_class = "success"
        icon = "✓"
        text = "ALL TESTS PASSED"
    else:
        css_class = "failure"
        icon = "✗"
        text = f"{s['failed']} TESTS FAILED"

    return f"""
        <div class="status-banner {css_class}">
            {icon} {text}
        </div>
    """


def generate_metric_cards(report_data: Dict[str, Any]) -> str:
    """Generate metric cards HTML."""
    s = report_data["summary"]

    cards = [
        ("Total Scenarios", s["total_scenarios"], "info"),
        ("Total Steps", s["total_steps"], "info"),
        ("Passed", s["passed"], "success"),
        ("Failed", s["failed"], "failure"),
        ("Skipped", s["skipped"], "warning"),
        ("Pass Rate", f"{s['pass_rate']}%", "success"),
    ]

    html = ""
    for label, value, css_class in cards:
        html += f"""
            <div class="metric-card {css_class}">
                <div class="value">{value}</div>
                <div class="label">{label}</div>
            </div>
        """

    return html


def generate_scenarios(report_data: Dict[str, Any]) -> str:
    """Generate scenarios list HTML."""
    html = ""

    for scenario in report_data["scenarios"]:
        status_class = "success" if scenario["status"] == "success" else "failure"
        icon = "✓" if scenario["status"] == "success" else "✗"

        tags_html = ""
        for tag in scenario.get("tags", []):
            tag_class = ""
            if "critical" in tag.lower():
                tag_class = "critical"
            elif "golden" in tag.lower():
                tag_class = "golden"
            elif "boundary" in tag.lower():
                tag_class = "boundary"
            elif "recovery" in tag.lower():
                tag_class = "recovery"
            tags_html += f'<span class="tag {tag_class}">{tag}</span>'

        steps_html = ""
        for step in scenario["steps"]:
            step_class = "success" if step["status"] == "success" else "failure"
            step_icon = "✓" if step["status"] == "success" else "✗"

            error_html = ""
            if step.get("error"):
                error_html = f'<div class="step-error">{step["error"][:500]}</div>'

            steps_html += f"""
                <tr>
                    <td>
                        <span class="step-status {step_class}">
                            {step_icon} {step['status'].upper()}
                        </span>
                    </td>
                    <td>{step['name']}</td>
                    <td>{step['duration_ms']}ms</td>
                </tr>
                {f"<tr><td colspan='3'>{error_html}</td></tr>" if error_html else ""}
            """

        html += f"""
            <div class="scenario">
                <div class="scenario-header {status_class}">
                    <div class="scenario-title">
                        <div class="scenario-icon {status_class}">{icon}</div>
                        <div>
                            <div class="scenario-id">{scenario['id']}</div>
                            <div class="scenario-name">{scenario['name']}</div>
                            <div class="tags">{tags_html}</div>
                        </div>
                    </div>
                    <div class="scenario-meta">
                        <div class="scenario-duration">{scenario['duration_ms']}ms</div>
                    </div>
                </div>
                <div class="scenario-body">
                    <table class="steps-table">
                        <thead>
                            <tr>
                                <th>Status</th>
                                <th>Step</th>
                                <th>Duration</th>
                            </tr>
                        </thead>
                        <tbody>
                            {steps_html}
                        </tbody>
                    </table>
                </div>
            </div>
        """

    return html


def generate_timeline(report_data: Dict[str, Any]) -> str:
    """Generate timeline visualization HTML."""
    total_duration = sum(s["duration_ms"] for s in report_data["scenarios"])

    segments_html = ""
    for scenario in report_data["scenarios"]:
        width = (scenario["duration_ms"] / max(total_duration, 1)) * 100
        status_class = "success" if scenario["status"] == "success" else "failure"
        segments_html += f"""
            <div class="timeline-segment {status_class}" style="width: {width}%" title="{scenario['id']}: {scenario['duration_ms']}ms">
                {scenario['id']}
            </div>
        """

    return f"""
        <div class="timeline-bar">
            {segments_html}
        </div>
        <p style="margin-top: 1rem; color: var(--gray); font-size: 0.875rem;">
            Total execution time: {total_duration}ms
        </p>
    """


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate HTML report from E2E JSON results")
    parser.add_argument("input", type=Path, help="Input JSON report file")
    parser.add_argument("-o", "--output", type=Path, help="Output HTML file path")

    args = parser.parse_args()

    # Load JSON report
    with open(args.input, "r", encoding="utf-8") as f:
        report_data = json.load(f)

    # Determine output path
    output_path = args.output or args.input.with_suffix(".html")

    # Generate report
    generate_html_report(report_data, output_path)

    print(f"✓ HTML report generated: {output_path}")


if __name__ == "__main__":
    main()
