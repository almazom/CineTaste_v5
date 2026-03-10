# E2E Integration Test Suite — User Guide

**Phase:** 7.5 — Universal Integration Testing  
**Version:** 5.5.0  
**Methodology:** Prometheus-Vassa Plamenny (Fire-Testing Architect)

---

## 🚀 Quick Start

```bash
# Run E2E tests with rich transparency
make test-e2e

# Run with verbose output
make test-e2e-verbose

# Run and generate HTML report
make test-e2e-html

# Open dashboard in browser
make e2e-dashboard

# View latest run summary
make e2e-latest
```

---

## 📋 Available Commands

### Make Targets

| Command | Description |
|---------|-------------|
| `make test-e2e` | Run E2E suite with rich transparency |
| `make test-e2e-verbose` | Run with detailed step-by-step output |
| `make test-e2e-html` | Run E2E and generate HTML report |
| `make test-e2e-golden` | Run only Golden Path tests |
| `make test-e2e-boundary` | Run only Boundary Case tests |
| `make test-e2e-recovery` | Run only Recovery Path tests |
| `make e2e-dashboard` | Open latest HTML report in browser |
| `make e2e-latest` | Show latest run summary |
| `make e2e-history` | Show last 10 runs history |

### Quick Aliases

| Alias | Full Command |
|-------|--------------|
| `make e2e` | `make test-e2e` |
| `make e2e-v` | `make test-e2e-verbose` |
| `make e2e-h` | `make test-e2e-html` |
| `make dash` | `make e2e-dashboard` |
| `make latest` | `make e2e-latest` |

---

## 🎯 Features

### 1. Step Transparency

Each test step is logged with:
- ✅ Timestamp (start/end)
- ✅ Duration in milliseconds
- ✅ Command executed
- ✅ stdout/stderr capture
- ✅ Exit code
- ✅ Artifacts collected

**Example output:**
```
╔══════════════════════════════════════════════════════════════════╗
║  GP-001: Full pipeline happy path — fetch to Telegram delivery  ║
╚══════════════════════════════════════════════════════════════════╝

  ▶ Validate pipeline configuration
  ✓ Validate pipeline configuration (12ms)

  ▶ Execute pipeline dry-run
  ✓ Execute pipeline dry-run (4523ms)

  ▶ Validate send-confirmation
  ✓ Validate send-confirmation (89ms)
```

### 2. HTML Reports

Rich interactive HTML reports with:
- 📊 Status banner (success/failure)
- 📈 Metrics cards (pass/fail/skip counts)
- 📉 Progress bar visualization
- 📋 Expandable scenario details
- ⏱️ Timeline visualization
- 🔍 Step-by-step breakdown with errors

**Location:** `reports/e2e/e2e-report-<RUN_ID>.html`

### 3. Dashboard

Comprehensive dashboard with:
- 📊 Pass rate trend chart (last 10 runs)
- ⏱️ Execution duration chart
- 📋 Run history table
- 📊 Scenario breakdown
- 🏆 Statistics (avg pass rate, best/worst)

**Location:** `reports/e2e/dashboard.html`

### 4. Artifact Collection

Each run preserves:
- JSON report (`e2e-report-<RUN_ID>.json`)
- Text summary (`e2e-summary-<RUN_ID>.txt`)
- HTML report (`e2e-report-<RUN_ID>.html`)
- Step logs (JSONL format)
- Collected artifacts (screenshots, outputs)

---

## 📁 Output Structure

```
reports/e2e/
├── e2e-report-20260310-120000.json    # Full JSON report
├── e2e-report-20260310-120000.html    # HTML report
├── e2e-summary-20260310-120000.txt    # Text summary
├── dashboard.html                      # Aggregated dashboard
│
└── 20260310-120000/                   # Run-specific directory
    ├── step-log.jsonl                  # Step-by-step logs
    ├── summary.json                    # Run summary
    └── artifacts/                      # Collected artifacts
        ├── step-001_movies.json
        ├── step-002_send-confirmation.json
        └── ...
```

---

## 🧪 Test Categories

### Golden Paths (@P0, @P1)

Critical end-to-end scenarios that verify the main user journeys:

| ID | Name | Description |
|----|------|-------------|
| GP-001 | Full pipeline happy path | Fetch → Telegram delivery |
| GP-002 | Cached analysis replay | Skip to format/send |
| GP-003 | Resend existing message | Recovery workflow |

**Run:** `make test-e2e-golden`

### Boundary Cases (@P1)

Edge cases and system limits:

| ID | Name | Description |
|----|------|-------------|
| BC-001 | Zero movies from source | Empty source handling |
| BC-005 | Score threshold boundaries | Boundary value analysis |

**Run:** `make test-e2e-boundary`

### Recovery Paths (@P1, @P2)

Error handling and self-healing:

| ID | Name | Description |
|----|------|-------------|
| RP-001 | Source unavailable | Graceful failure |
| RP-006 | Contract violation | Schema validation failure |

**Run:** `make test-e2e-recovery`

---

## 📊 Understanding Reports

### JSON Report Structure

```json
{
  "run_id": "20260310-120000",
  "start_time": "2026-03-10T12:00:00",
  "end_time": "2026-03-10T12:05:00",
  "status": "completed",
  "summary": {
    "total_scenarios": 8,
    "total_steps": 23,
    "passed": 22,
    "failed": 1,
    "skipped": 0,
    "pass_rate": 95.65
  },
  "scenarios": [
    {
      "id": "GP-001",
      "name": "Full pipeline happy path",
      "status": "success",
      "duration_ms": 5234,
      "steps": [...]
    }
  ]
}
```

### Status Codes

| Status | Color | Meaning |
|--------|-------|---------|
| `success` | Green | All steps passed |
| `failed` | Red | One or more steps failed |
| `skipped` | Yellow | Step was skipped |

---

## 🔧 Customization

### Custom Output Directory

```bash
python3 tests/e2e_runner.py --output ./custom-reports
```

### Custom Run ID

```bash
python3 tests/e2e_runner.py --run-id my-custom-run-001
```

### Verbose Mode

```bash
python3 tests/e2e_runner.py --verbose
```

Shows full command output for each step.

---

## 📈 Metrics & Trends

### Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| **Pass Rate** | Percentage of passed steps | ≥95% |
| **Avg Duration** | Average run time | <5 min |
| **Scenario Coverage** | Scenarios executed | 100% |
| **Artifact Preservation** | Artifacts saved | 100% |

### Trend Analysis

The dashboard tracks:
- Pass rate over last 10 runs
- Execution duration trends
- Failure patterns
- Scenario stability

---

## 🐛 Troubleshooting

### No Reports Found

```
✗ No E2E reports found. Run 'make test-e2e' first.
```

**Solution:** Run `make test-e2e` to generate reports.

### Dashboard Won't Open

```
make e2e-dashboard
```

**Solution:** Manually open `reports/e2e/dashboard.html` in a browser.

### Step Timeout

If a step times out (5 min limit):
1. Check `reports/e2e/<RUN_ID>/step-log.jsonl` for details
2. Increase timeout in `tests/e2e_runner.py` (line 132)
3. Re-run with `--verbose` for more details

### Artifacts Missing

Artifacts are collected from:
- `runs/latest/` directory
- Temporary test files
- Pipeline outputs

Check `step-log.jsonl` for artifact paths.

---

## 📝 Examples

### Example 1: Full E2E Run

```bash
$ make test-e2e-html

╔══════════════════════════════════════════════════════════════════╗
║  E2E Integration Test Suite — HTML Report Generation            ║
╚══════════════════════════════════════════════════════════════════╝

▶ Running E2E tests...

╔══════════════════════════════════════════════════════════════════╗
║  GOLDEN PATHS — Critical End-to-End Scenarios                   ║
╚══════════════════════════════════════════════════════════════════╝

  ✓ Validate pipeline configuration (12ms)
  ✓ Execute pipeline dry-run (4523ms)
  ...

✓ JSON report saved: reports/e2e/e2e-report-20260310-120000.json
✓ Text summary saved: reports/e2e/e2e-summary-20260310-120000.txt

▶ Generating HTML report...
✓ HTML report generated: reports/e2e/e2e-report-20260310-120000.html
✓ Open with: make e2e-dashboard
```

### Example 2: View Dashboard

```bash
$ make e2e-dashboard

▶ Opening dashboard: reports/e2e/dashboard.html
```

### Example 3: Check History

```bash
$ make e2e-history

╔══════════════════════════════════════════════════════════════════╗
║  E2E Run History                                                 ║
╚══════════════════════════════════════════════════════════════════╝

RUN ID                   STATUS      PASS      FAIL      SKIP      PASS RATE
─────────────────────────────────────────────────────────────────────────────
20260310-120000          ✓           22        1         0         95.65%
20260310-110000          ✓           23        0         0         100.0%
20260310-100000          ✗           18        5         0         78.26%
...
```

---

## 🎓 Best Practices

### 1. Run Before Deployment

Always run E2E tests before deploying:
```bash
make test-e2e-html
make e2e-dashboard  # Review results
```

### 2. Monitor Trends

Check the dashboard regularly for:
- Declining pass rates
- Increasing durations
- Recurring failures

### 3. Preserve Artifacts

Keep reports for:
- Audit trails
- Debugging
- Performance analysis

### 4. Use Verbose for Debugging

When investigating failures:
```bash
make test-e2e-verbose
```

---

## 📚 Related Files

| File | Purpose |
|------|---------|
| `tests/e2e_runner.py` | Main E2E test runner |
| `tests/e2e_html_report.py` | HTML report generator |
| `tests/e2e_dashboard.py` | Dashboard generator |
| `tests/e2e_step_logger.py` | Step-by-step logger |
| `tests/features/*.feature` | Gherkin test scenarios |

---

## 🆘 Getting Help

1. **Check dashboard:** `make e2e-dashboard`
2. **View latest summary:** `make e2e-latest`
3. **Inspect step logs:** `reports/e2e/<RUN_ID>/step-log.jsonl`
4. **Review HTML report:** `reports/e2e/e2e-report-*.html`

---

*Generated for CineTaste v5.5.0*  
*Phase 7.5 — Prometheus-Vassa Integration Testing*
