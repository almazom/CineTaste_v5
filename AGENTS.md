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
| `03-tools.md` | Building/using tools |
| `04-taste.md` | Modifying preferences |
| `05-troubleshooting.md` | Something broke |
| `06-ai-agents.md` | Working with `ct-analyze --agent` |

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

### Step 3: Check Tool Manifests
```bash
cat tools/ct-fetch/MANIFEST.json
```

### Step 4: Run Pipeline
```bash
./run --dry-run    # Preview
./run              # Production (sends to Telegram)
```

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
│   └── 05-troubleshooting.md
│
├── contracts/                 # JSON Schema boundaries
│   ├── movie-batch.schema.json
│   ├── analysis-result.schema.json
│   ├── filter-result.schema.json
│   ├── message-text.schema.json
│   └── send-confirmation.schema.json
│
├── tools/                     # CLI microservices
│   ├── ct-fetch/MANIFEST.json
│   ├── ct-analyze/MANIFEST.json
│   ├── ct-filter/MANIFEST.json
│   ├── ct-format/MANIFEST.json
│   └── t2me/MANIFEST.json
│
├── flows/                     # Pipeline versions
│   ├── v1.2/FLOW.md
│   └── latest → v1.2/
│
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

---

## 🆘 Getting Help

1. Read `PROTOCOL.json` for system topology
2. Check `.MEMORY/05-troubleshooting.md`
3. Read tool `MANIFEST.json` for CLI options
4. Check `logs/errors.log`

---

*Last updated: 2026-03-02*
*Version: 5.2.0*
