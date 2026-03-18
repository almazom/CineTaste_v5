# 🤖 Agent Instructions — CineTaste v5

> **READ THIS FIRST** when working with this project as an AI agent.

---

## 🧠 Memory Bank System

This project uses a **Memory Bank** (`.MEMORY/` folder) to maintain context across sessions.

### Bootstrap Sequence

```
1. Read AURA.md (directives)
2. Read PROTOCOL.json (system topology) ← SSOT
3. Read .MEMORY/00-index.md (context)
4. Read flows/latest/FLOW.md (pipeline)
5. Execute
```

## 🧭 How to Use `@aura.md`

Treat `@aura.md` as the runtime protocol (`AURA.md` symlink in repo root).

1. Read `@aura.md` first on every session.
2. Before any code change, create `.aura/kanban/KANBAN-YYYY-MM-DD-HHMM.json`, update `.aura/kanban/latest`, and work in `TODO/DOING/DONE`.
3. Use `PROTOCOL.json` as topology SSOT; use `@aura.md` for execution discipline (planning, order, testing).
4. Follow AURA order strictly: `CONTRACT → KANBAN → TOOL → FLOW → TEST → VERSION`.

### Memory Cards

| Card | When to Read |
|------|--------------|
| `01-architecture.md` | First time / major changes |
| `02-contracts.md` | Working with data flow |
| `03-tools.md` | Tool inventory / choosing the right CLI |
| `04-taste.md` | Modifying preferences |
| `05-troubleshooting.md` | Something broke |
| `06-ai-agents.md` | Working with `ct-cognize --agent auto` |
| `10-ct-fetch.md` | Batch discovery from kinoteatr.ru |
| `11-ct-schedule.md` | Collecting showtimes into `movie-schedule` |
| `12-ct-time-price.md` | Checking one movie URL for times and prices |
| `13-ct-cognize.md` | Running the cognitive layer on `movie-schedule` |

---

## 📋 PROTOCOL.json is SSOT

The `PROTOCOL.json` file defines the **entire system topology**:

```json
{
  "contracts": { ... },  // What data shapes exist
  "tools": { ... },      // What CLI tools exist
  "flow": { ... }        // How they connect
}
```

**Rule:** Read PROTOCOL.json BEFORE assuming anything about the system.

---

## 🎯 Project Context

### What is CineTaste?

AI-powered movie recommendation system that:
1. **Fetches** today's movies from kinoteatr.ru
2. **Analyzes** them against user's taste profile using AI
3. **Filters** to keep only good matches
4. **Formats** as Telegram message
5. **Sends** via t2me CLI

### Key Philosophy (v5)

| Principle | Application |
|-----------|-------------|
| **Contract-first** | Define schema before code |
| **PROTOCOL.json** | Single source of truth |
| **Simple > Easy** | Artifact simplicity over authoring convenience |
| **Uncomplect** | One responsibility per tool |
| **Stateless** | Pure functions, effects at boundaries |

---

## 🚀 Quick Start for Agents

### Step 1: Read SSOT
```bash
cat PROTOCOL.json
```

### Step 2: Understand Contracts
```bash
ls contracts/
cat contracts/movie-batch.schema.json
```

### Step 3: Check Active Tool Manifests
```bash
cat tools/ct-fetch/MANIFEST.json
cat tools/ct-schedule/MANIFEST.json
cat tools/ct-time-price/MANIFEST.json
cat tools/ct-cognize/MANIFEST.json
```

### Step 4: Read Active Flow
```bash
cat flows/latest/FLOW.md   # Current flow file (Version: 1.3.1)
```

### Step 5: Run Pipeline
```bash
./run --dry-run    # Preview / validates send via t2me --dry-run
./run              # Production (sends to Telegram)
```

## 🔧 Tool Drill-Down

### `./ct-fetch` — batch discovery

Use `./ct-fetch` for city-level movie discovery and for checking whether a title appears in today's or the weekly batch.

```bash
./ct-fetch --city naberezhnie-chelni --when now
./ct-fetch --city naberezhnie-chelni --when week --output /tmp/movies.json
./ct-fetch --city naberezhnie-chelni --when 2026-03-29 --output /tmp/movies.json
```

Quick facts:
- Output contract: `movie-batch@1.0.0`
- `--when now` = today's listing
- `--when week` = 7-day aggregation with `available_days`
- `available_days_accurate` comes from per-movie detail pages and is the better source of truth when it disagrees with the aggregated week listing

Details: `.MEMORY/10-ct-fetch.md`

### `./ct-schedule` — collect showtimes

Use `./ct-schedule` to turn `movie-batch` into `movie-schedule` by attaching showtimes.

```bash
./ct-schedule --input /tmp/movies.json --output /tmp/scheduled.json
./ct-schedule --input /tmp/movies.json --date 2026-03-29 --output /tmp/scheduled.json
./ct-schedule --input /tmp/movies.json --best-effort --output /tmp/scheduled.json
```

Quick facts:
- Input contract: `movie-batch@1.0.0`
- Output contract: `movie-schedule@1.0.0`
- Default date comes from `input.meta.date`
- `--best-effort` keeps partial results when some movie pages fail to resolve showtimes

Details: `.MEMORY/11-ct-schedule.md`

### `./ct-time-price` — single movie probe

Use `./ct-time-price` for one Kinoteatr movie URL when you need the exact page date, session times, and prices.

```bash
./ct-time-price --url https://kinoteatr.ru/film/.../naberezhnie-chelni/
./ct-time-price --url https://kinoteatr.ru/film/.../naberezhnie-chelni/ --date 2026-03-29
./ct-time-price --url https://kinoteatr.ru/film/.../naberezhnie-chelni/ --output /tmp/showtimes.json
```

Quick facts:
- Output contract: `movie-showtimes@1.0.0`
- Not part of the main `./run` chain; it is an auxiliary inspection tool
- It returns showtimes only, not full movie metadata
- For advance sales / presale pages, pass the explicit page date instead of assuming local today

Details: `.MEMORY/12-ct-time-price.md`

### `./ct-cognize` — cognitive stage

Use `./ct-cognize` only with a valid `movie-schedule` payload. It validates the contract, prepares a temp workdir, runs agent preflight, then scores each movie against the taste profile.

```bash
./ct-cognize --input /tmp/scheduled.json --taste taste/profile.yaml --agent auto
./ct-cognize --input /tmp/scheduled.json --taste taste/profile.yaml --agents qwen,pi,claude
./ct-cognize --input /tmp/scheduled.json --taste taste/profile.yaml --timings --verbose
```

Quick facts:
- Input contract: `movie-schedule@1.0.0`
- Output contract: `analysis-result@1.0.0`
- `--agent auto` = parallel preflight + ordered fallback
- `--list-agents` shows only currently enabled agents from `tools/ct-cognize/agent-config.json`

Details: `.MEMORY/13-ct-cognize.md`, `.MEMORY/06-ai-agents.md`

---

## 📁 File Structure

```
CineTaste_v5/
├── AURA.md                    # Agent directives (symlink)
├── PROTOCOL.json              # ★ SSOT — system manifest
├── AGENTS.md                  # This file
│
├── .aura/                     # Versioned protocols
│   ├── v2.2/AURA.md
│   └── latest → v2.2/
│
├── .MEMORY/                   # Context cards
│   ├── 00-index.md
│   ├── 01-architecture.md
│   ├── 02-contracts.md
│   ├── 03-tools.md
│   ├── 04-taste.md
│   ├── 05-troubleshooting.md
│   ├── 06-ai-agents.md
│   ├── 10-ct-fetch.md
│   ├── 11-ct-schedule.md
│   ├── 12-ct-time-price.md
│   └── 13-ct-cognize.md
│
├── contracts/                 # JSON Schema boundaries
│   ├── movie-batch.schema.json
│   ├── movie-schedule.schema.json
│   ├── analysis-result.schema.json
│   ├── filter-result.schema.json
│   ├── message-text.schema.json
│   └── send-confirmation.schema.json
│
├── tools/                     # CLI microservices
│   ├── ct-fetch/MANIFEST.json
│   ├── ct-schedule/MANIFEST.json
│   ├── ct-time-price/MANIFEST.json
│   ├── ct-cognize/MANIFEST.json
│   ├── ct-analyze/MANIFEST.json   # legacy
│   ├── ct-filter/MANIFEST.json
│   ├── ct-format/MANIFEST.json
│   └── t2me/MANIFEST.json
│
├── flows/                     # Pipeline versions
│   ├── v1.3/FLOW.md           # Current file, header version 1.3.1
│   └── latest → v1.3/
│
├── run                        # Pipeline entrypoint
├── taste/profile.yaml         # User preferences
├── .aura/templates/           # Output templates
└── logs/                      # Execution logs
```

---

## ⚠️ Critical Knowledge

### Contract-First Development

**ALWAYS** define contracts before code:

```
1. DEFINE contract in contracts/*.schema.json
2. SPECIFY tool in tools/*/MANIFEST.json
3. DESCRIBE flow in flows/vX.X/FLOW.md
4. TEST
5. IMPLEMENT
```

### Tool Manifests

Every tool MUST have a `MANIFEST.json` with:
- `identity`: name, verb, position
- `contracts`: input/output schemas
- `cli`: flags, usage, exit codes
- `adapters`: external integrations

### Telegram Send Method

```bash
# Correct (pipe)
cat message.txt | t2me send --markdown

# Wrong (file flag can timeout)
t2me send --file message.txt
```

---

## 🛠️ Common Tasks

### Add a New Tool

1. Define output contract in `contracts/`
2. Create `tools/ct-<verb>/MANIFEST.json`
3. Add to `PROTOCOL.json` under `tools`
4. Implement: main.py, port.py, adapter_*.py
5. Update `flows/latest/FLOW.md`

### Modify a Contract

1. Check impact in PROTOCOL.json (who produces/consumes)
2. Create new version if breaking
3. Update all affected tools' MANIFEST.json
4. Update flow version

### Debug Pipeline

```bash
./run --dry-run --verbose
ls -1 logs/failed_* | tail -n 1
```

### Debug One Movie

```bash
# 1. Find the movie in batch context
./ct-fetch --city naberezhnie-chelni --when week --output /tmp/movies.json

# 2. Verify one page's exact session date/time/price
./ct-time-price --url https://kinoteatr.ru/film/.../naberezhnie-chelni/ --date 2026-03-29

# 3. Build or extract a one-movie movie-schedule payload
#    then run cognitive analysis on that payload
./ct-cognize --input /tmp/one-movie-scheduled.json --taste taste/profile.yaml --agent auto
```

---

## 🆘 Getting Help

1. Read `PROTOCOL.json` for system topology
2. Check `.MEMORY/05-troubleshooting.md`
3. Read tool `MANIFEST.json` for CLI options
4. Check `logs/errors.log`

---

*Last updated: 2026-03-18*
*Version: 5.4.0*
