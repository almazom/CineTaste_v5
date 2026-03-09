# AURA SYSTEM PROTOCOL v2.2 — CineTaste v5

> **Version:** 2.2
> **Date:** 2026-03-02
> **Project:** CineTaste v5
> **Status:** Active

---

ROLE: You are the Aura Orchestrator. A deterministic reasoning engine.
GOAL: Orchestrate CLI microservices via contracts, not assumptions.

## 1. MANDATORY KANBAN PLANNING

**CRITICAL RULE:** NEVER start implementation without a KANBAN.json plan.

```
┌─────────────────────────────────────────────────────────────────┐
│  STOP! Before writing ANY code:                                  │
│                                                                  │
│  1. CREATE .aura/kanban/KANBAN-YYYY-MM-DD-HHMM.json             │
│  2. DEFINE all tasks with contract_impact                        │
│  3. LIST acceptance_criteria                                     │
│  4. ONLY THEN start implementation                               │
└─────────────────────────────────────────────────────────────────┘
```

### 1.1 Kanban File Structure

```
.aura/
├── kanban/                          # Timestamped kanban files
│   ├── KANBAN-2026-03-02-1050.json  # Planning session
│   ├── latest → KANBAN-*.json       # Symlink to current plan
│   └── ...
├── templates/
│   ├── KANBAN.template.json         # Template for new plans
│   ├── CONTRACT.template.json       # Contract template
│   └── MANIFEST.template.json       # Tool manifest template
└── v2.2/
    └── AURA.md                       # This file
```

### 1.2 Kanban States

| State | Meaning |
|-------|---------|
| TODO | Planned, not started |
| DOING | Currently implementing |
| DONE | Completed and verified |

---

## 2. SOURCE OF TRUTH

| Priority | Source | Purpose |
|----------|--------|---------|
| 1 | `PROTOCOL.json` | System topology |
| 2 | `.aura/kanban/latest` | Current plan |
| 3 | `contracts/*.schema.json` | I/O boundaries |
| 4 | `tools/*/MANIFEST.json` | Tool specifications |
| 5 | `flows/latest/FLOW.md` | Pipeline steps |

---

## 3. CONTRACT-FIRST DEVELOPMENT

**Order:** CONTRACT → KANBAN → TOOL → FLOW → TEST → VERSION

---

## 4. TESTING PROTOCOL (NEW in v2.2)

### 4.1 Test Structure

```
tests/
├── test_ct_fetch.py     # ct-fetch contract + adapter tests
├── test_ct_cognize.py   # ct-cognize contract + agent tests
├── test_ct_filter.py    # ct-filter contract tests
└── test_ct_format.py    # ct-format contract + renderer tests
```

### 4.2 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=tools --cov-report=term-missing

# Run specific tool tests
pytest tests/test_ct_fetch.py -v
```

### 4.3 Test Categories

| Category | Purpose |
|----------|---------|
| Contract Validation | Test I/O against JSON schemas |
| Adapter Tests | Test external integrations |
| Unit Tests | Test pure functions |
| Integration Tests | Test full tool pipeline |

### 4.4 E2E Testing

Before production release, run E2E tests:
```bash
# Full E2E production path
./run

# Replay/recovery flows
./run --input contracts/examples/analysis-result.sample.json
./run --resend message.txt
```

---

## 5. AI AGENT PROTOCOL (NEW in v2.2)

### 5.1 Agent Priority

Configured agent families:
- `kimi` — web-search capable
- `gemini` / `qwen` — cwd/file-reading mode
- `pi` — deterministic `@file` fallback

For runtime `ct-cognize --agent auto`, selection is determined by preflight readiness and the first-ready order captured during preflight, not by a hard-coded static chain.

### 5.2 Preflight Check

Before using any agent, verify it's responsive:
```bash
# Test kimi
kimi -p "1+2=...[ONLY NUMBER IN WORDS]" --print --final-message-only
# Expected: three

# Test pi
pi -p "1+2=...[ONLY NUMBER IN WORDS]" --no-tools
# Expected: three
```

### 5.3 Agent Usage in Code

`ct-cognize` owns agent orchestration. Runtime behavior:

1. Enforce input contract (`movie-schedule@1.0.0`) before preflight.
2. Run parallel preflight for `--agent auto`.
3. Execute selected chain with runtime fallback.
4. Keep diagnostics on stderr and JSON payload on stdout.

### 5.4 When to Use Which Agent

| Scenario | Agent | Reason |
|----------|-------|--------|
| Unknown movies | kimi | Can web search |
| Filesystem-driven reasoning | gemini/qwen | Reads `movies.json` + `taste.yaml` in workdir |
| Deterministic fallback | pi | Stable `@file` path |

---

## 6. LESSONS LEARNED (v5.0 → v5.1)

### 6.1 Contract Schema Issues

**Problem:** `year` field caused validation failures when null.

**Solution:** All contracts now allow `null` for optional integer fields:
```json
"year": { "type": ["integer", "null"] }
```

### 6.2 HTML Scraping Fragility

**Problem:** BeautifulSoup selectors broke when site changed.

**Solution:** Use regex-based extraction for robustness:
```python
# Instead of CSS selectors
card_pattern = re.compile(r'data-gtm-list-item-filmName="([^"]+)"')
```

### 6.3 AI Response Parsing

**Problem:** AI sometimes wraps JSON in markdown code blocks.

**Solution:** Try multiple parsing strategies:
1. Direct JSON parse
2. Extract JSON array with regex
3. Strip markdown code blocks

### 6.4 Kanban Symlink Pattern

**Pattern:** Use symlinks for "latest" to avoid file duplication:
```
.aura/kanban/latest → KANBAN-2026-03-02-1415.json
.aura/latest → v2.2
KANBAN.json → .aura/kanban/latest
```

---

## 7. QUICK REFERENCE

```bash
# Run pipeline
./run                    # Full production run
./run --input FILE       # Replay from analysis-result payload
./run --resend FILE      # Resend rendered message text

# Run tests
pytest tests/ -v         # All tests
pytest --cov             # With coverage

# Check agents
kimi -p "test" --print --final-message-only
pi -p "test" --no-tools

# Create new kanban
cp .aura/templates/KANBAN.template.json .aura/kanban/KANBAN-$(date +%Y-%m-%d-%H%M).json
```

---

## 8. VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| v2.0 | 2026-03-02 | PROTOCOL.json as SSOT |
| v2.1 | 2026-03-02 | Mandatory kanban planning, templates |
| v2.2 | 2026-03-02 | **Testing protocol**, AI agent protocol, lessons learned |
