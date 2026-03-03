# FLOW.md — Executable Pipeline Specification
# Version: 1.3.0
# Project: CineTaste v5
# Paradigm: Contract-First, Protocol-Driven

> **This file IS the pipeline.** The orchestrator script parses this,
> extracts shell blocks, and executes them.
>
> **FOR AI AGENTS — READ PROTOCOL.json FIRST**

---

## Meta

```yaml
name: CineTaste
version: "5.4.0"
paradigm: contract-first
architecture: ports-and-adapters
root: ~/zoo/CineTaste_v5
tagline: "Cinema recommendations delivered to Telegram"
```

---

## Config

```yaml
city: naberezhnie-chelni
city_display: Набережные Челны
template: telegram
template_path: .aura/templates/telegram.md
taste_profile: taste/profile.yaml
```

---

## Pipeline

```
┌─────────┐    ┌────────────┐    ┌───────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────┐
│ct-fetch │───→│ct-schedule │───→│ct-cognize │───→│ct-filter│───→│ct-format│───→│    t2me     │
└────┬────┘    └─────┬──────┘    └─────┬─────┘    └────┬────┘    └────┬────┘    └──────┬──────┘
     │               │                │               │              │                │
     ▼               ▼                ▼               ▼              ▼                ▼
movie-batch    movie-schedule   analysis-result  filter-result   message-text    Telegram ✓
```

**ALWAYS SEND:** Step 6 is mandatory. Pipeline always runs live with cognitive layer.

---

## Step 1 — ct-fetch

> **Verb:** fetch | **Contract:** `movie-batch@1.0.0`

```bash
# @step: 1
# @contract: movie-batch
# @output: $TMPDIR/movies.json

"$ROOT/ct-fetch" \
    --city "$CITY" \
    --when "$WHEN" \
    --output "$TMPDIR/movies.json"
```

---

## Step 2 — ct-schedule

> **Verb:** schedule | **Input:** `movie-batch` | **Output:** `movie-schedule@1.0.0`

```bash
# @step: 2
# @contract: movie-schedule
# @output: $TMPDIR/scheduled.json

"$ROOT/ct-schedule" \
    --input "$TMPDIR/movies.json" \
    --output "$TMPDIR/scheduled.json"
```

---

## Step 3 — ct-cognize

> **Verb:** cognize | **Input:** `movie-schedule` | **Output:** `analysis-result@1.0.0`

```bash
# @step: 3
# @contract: analysis-result
# @output: $TMPDIR/analyzed.json

"$ROOT/ct-cognize" \
    --input "$TMPDIR/scheduled.json" \
    --taste "$ROOT/taste/profile.yaml" \
    --output "$TMPDIR/analyzed.json"
```

---

## Step 4 — ct-filter

> **Verb:** filter | **Input:** `analysis-result` | **Output:** `filter-result@1.0.0`

```bash
# @step: 4
# @contract: filter-result
# @output: $TMPDIR/filtered.json

"$ROOT/ct-filter" \
    --input "$TMPDIR/analyzed.json" \
    --recommendation must_see,recommended \
    --output "$TMPDIR/filtered.json"
```

---

## Step 5 — ct-format

> **Verb:** format | **Input:** `filter-result` | **Output:** `message-text@1.0.0`

```bash
# @step: 5
# @contract: message-text
# @output: $TMPDIR/message.json

"$ROOT/ct-format" \
    --input "$TMPDIR/filtered.json" \
    --template telegram \
    --city "$CITY_DISPLAY" \
    --output "$TMPDIR/message.json"

python3 -c "import json; print(json.load(open('$TMPDIR/message.json'))['text'])" > "$TMPDIR/message.txt"
```

---

## Step 6 — t2me (MANDATORY)

> **Verb:** send | **Input:** `message-text` | **Output:** `send-confirmation@1.0.0`

```bash
# @step: 6
# @contract: send-confirmation
# @output: $TMPDIR/send-confirmation.json

cat "$TMPDIR/message.txt" | t2me send --markdown > "$TMPDIR/t2me-raw.json"
python3 "$ROOT/tools/t2me/map_send_confirmation.py" \
    --input "$TMPDIR/t2me-raw.json" \
    --output "$TMPDIR/send-confirmation.json"
cat "$TMPDIR/send-confirmation.json" | tee "$TMPDIR/send.log"
```

---

## CLI Options

```text
Usage: ./run [OPTIONS]

CineTaste v5 — Cinema recommendations to Telegram

Options:
  --when DATE       Date filter (default: now)
  --input FILE      Skip fetch/analyze, use cached
  --resend FILE     Resend existing message
  --verbose, -v     Show details
  --help, -h        Show help
```

---

## Self-Healing

When ANY step fails:

1. **HALT** — No partial sends
2. **LOG** — Write to `logs/errors.log`
3. **PRESERVE** — Copy TMPDIR to `logs/failed_<timestamp>/`
4. **RECOVER** — Use `--resend` or `--input` to retry

---

## File Map

```
CineTaste_v5/
├── AURA.md                    Agent directives
├── PROTOCOL.json              ★ SSOT — system manifest
├── contracts/                 JSON Schema boundaries
├── tools/*/MANIFEST.json      Tool specifications
├── flows/latest/FLOW.md       This file
├── .MEMORY/                   Context cards
├── taste/profile.yaml         User preferences
└── logs/                      Execution logs
```

---

## Changelog

### [1.3.0] — 2026-03-03

- Replaced `ct-analyze` with `ct-cognize` at Step 3 (cognitive layer)
- ct-cognize uses file-based agent invocation (movies.json + taste.yaml)
- Pipeline version bumped to 5.4.0

### [1.2.0] — 2026-03-03

- Added `ct-schedule` stage between fetch and analyze
- Added `movie-schedule` contract to executable flow annotations
- Routed `ct-analyze` input to `$TMPDIR/scheduled.json`

### [1.1.0] — 2026-03-02

- Added complete step annotations (`@step`, `@contract`, `@output`) for parser execution
- Aligned `ct-format` step to output `message-text` JSON (`message.json`) and extract `message.txt`
- Added explicit step metadata to dry-run conditional blocks
- Added send log artifacts for `t2me` step outputs

### [1.0.0] — 2026-03-02

- Initial v5 flow
- Contract-first design
- PROTOCOL.json as SSOT
