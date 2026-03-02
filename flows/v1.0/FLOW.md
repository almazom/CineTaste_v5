# FLOW.md — Executable Pipeline Specification
# Version: 1.1.0
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
version: "5.2.0"
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
template_path: templates/telegram.md
taste_profile: taste/profile.yaml
```

---

## Pipeline

```
┌─────────┐    ┌──────────┐    ┌─────────┐    ┌─────────┐    ┌─────────────┐
│ct-fetch │───→│ct-analyze│───→│ct-filter│───→│ct-format│───→│    t2me     │
└────┬────┘    └────┬─────┘    └────┬────┘    └────┬────┘    └──────┬──────┘
     │              │               │              │                │
     ▼              ▼               ▼              ▼                ▼
movie-batch   analysis-result  filter-result   message-text    Telegram ✓
```

**ALWAYS SEND:** Step 5 is mandatory. Pipeline exists to deliver.

---

## Step 1 — ct-fetch

> **Verb:** fetch | **Contract:** `movie-batch@1.0.0`

```bash
# @step: 1
# @contract: movie-batch
# @output: $TMPDIR/movies.json

ct-fetch \
    --city "$CITY" \
    --when "$WHEN" \
    --output "$TMPDIR/movies.json"
```

---

## Step 2 — ct-analyze

> **Verb:** analyze | **Input:** `movie-batch` | **Output:** `analysis-result@1.0.0`

```bash
# @step: 2
# @contract: analysis-result
# @output: $TMPDIR/analyzed.json

ct-analyze \
    --input "$TMPDIR/movies.json" \
    --taste "$ROOT/taste/profile.yaml" \
    --output "$TMPDIR/analyzed.json"
```

**Dry-run mode:**
```bash
# @step: 2
# @contract: analysis-result
# @output: $TMPDIR/analyzed.json
# @condition: DRY_RUN=true
ct-analyze \
    --input "$TMPDIR/movies.json" \
    --taste "$ROOT/taste/profile.yaml" \
    --dry-run \
    --output "$TMPDIR/analyzed.json"
```

---

## Step 3 — ct-filter

> **Verb:** filter | **Input:** `analysis-result` | **Output:** `filter-result@1.0.0`

```bash
# @step: 3
# @contract: filter-result
# @output: $TMPDIR/filtered.json

ct-filter \
    --input "$TMPDIR/analyzed.json" \
    --recommendation must_see,recommended \
    --output "$TMPDIR/filtered.json"
```

---

## Step 4 — ct-format

> **Verb:** format | **Input:** `filter-result` | **Output:** `message-text@1.0.0`

```bash
# @step: 4
# @contract: message-text
# @output: $TMPDIR/message.json

ct-format \
    --input "$TMPDIR/filtered.json" \
    --template telegram \
    --city "$CITY_DISPLAY" \
    --output "$TMPDIR/message.json"

python3 -c "import json; print(json.load(open('$TMPDIR/message.json'))['text'])" > "$TMPDIR/message.txt"
```

---

## Step 5 — t2me (MANDATORY)

> **Verb:** send | **Input:** `message-text` | **Output:** `send-confirmation@1.0.0`

```bash
# @step: 5
# @contract: send-confirmation
# @output: $TMPDIR/send.log
# @condition: DRY_RUN=false

cat "$TMPDIR/message.txt" | t2me send --markdown | tee "$TMPDIR/send.log"
```

**Dry-run mode:**
```bash
# @step: 5
# @contract: send-confirmation
# @output: $TMPDIR/send-preview.log
# @condition: DRY_RUN=true
{
echo "=== PREVIEW (message NOT sent) ==="
cat "$TMPDIR/message.txt"
echo "=== END PREVIEW ==="
} | tee "$TMPDIR/send-preview.log"
```

---

## CLI Options

```bash
Usage: ./run [OPTIONS]

CineTaste v5 — Cinema recommendations to Telegram

Options:
  --dry-run, -n     Preview without sending
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

### [1.0.0] — 2026-03-02

- Initial v5 flow
- Contract-first design
- PROTOCOL.json as SSOT

### [1.1.0] — 2026-03-02

- Added complete step annotations (`@step`, `@contract`, `@output`) for parser execution
- Aligned `ct-format` step to output `message-text` JSON (`message.json`) and extract `message.txt`
- Added explicit step metadata to dry-run conditional blocks
- Added send log artifacts for `t2me` step outputs
