# AURA SYSTEM PROTOCOL v2.1 — CineTaste v5

> **Version:** 2.1
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
│   ├── KANBAN-2026-03-02-1135.json  # Another session
│   └── ...
├── templates/
│   ├── KANBAN.template.json         # Template for new plans
│   ├── CONTRACT.template.json       # Contract template
│   └── MANIFEST.template.json       # Tool manifest template
└── v2.1/
    └── AURA.md                       # This file
```

### 1.2 Kanban Task Format

Every task MUST include:
- `id`: Unique identifier
- `task`: Description
- `contract_impact`: Which contracts are affected (empty if none)
- `priority`: 1-10
- `estimated_complexity`: low/medium/high

### 1.3 Kanban States

| State | Meaning |
|-------|---------|
| TODO | Planned, not started |
| DOING | Currently implementing |
| DONE | Completed and verified |
| BLOCKED | Waiting for dependency |

---

## 2. SOURCE OF TRUTH

| Priority | Source | Purpose |
|----------|--------|---------|
| 1 | `PROTOCOL.json` | System topology |
| 2 | `.aura/kanban/KANBAN-*.json` | Current plan + history |
| 3 | `contracts/*.schema.json` | I/O boundaries |
| 4 | `tools/*/MANIFEST.json` | Tool specifications |
| 5 | `flows/latest/FLOW.md` | Pipeline steps |

**Rule 2.1:** Read `PROTOCOL.json` FIRST.
**Rule 2.2:** Check `.aura/kanban/` for active plans before starting.
**Rule 2.3:** If no plan exists, CREATE ONE before implementing.

---

## 3. CONTRACT-FIRST DEVELOPMENT

**Order:** CONTRACT → KANBAN → TOOL → FLOW → TEST → VERSION

```
┌─────────────────────────────────────────────────────────────┐
│  1. DEFINE contract in contracts/*.schema.json              │
│  2. CREATE kanban in .aura/kanban/KANBAN-TIMESTAMP.json     │
│  3. IMPLEMENT tool in tools/ct-<verb>/                      │
│  4. UPDATE flow in flows/vX.X/FLOW.md                       │
│  5. TEST via --dry-run                                      │
│  6. VERSION bump if breaking                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. SIMPLIFICATION PRINCIPLES

From Rich Hickey's "Simple Made Easy":

| Principle | Rule |
|-----------|------|
| **Simple ≠ Easy** | Choose simple artifacts, not easy authoring |
| **Uncomplect** | Each tool = ONE responsibility |
| **Data > Logic** | Replace if/else with data structures |
| **Readability > Brevity** | Guard clauses, clear names, no magic |
| **MVS** | Minimum Viable Solution |
| **State Isolation** | Pure functions, effects at boundaries |

---

## 5. BOOTSTRAP SEQUENCE

```
1. Read AURA.md (this file)
2. Check .aura/kanban/ for active plans
3. Read PROTOCOL.json (system topology)
4. Read .MEMORY/00-index.md (context)
5. Read flows/latest/FLOW.md (pipeline)
6. Load contracts as needed
7. Execute (following kanban if exists)
```

---

## 6. KEY FILES

| File | Purpose |
|------|---------|
| `AURA.md` | This file — agent directives |
| `PROTOCOL.json` | System manifest |
| `.aura/kanban/KANBAN-*.json` | Planning history |
| `.aura/templates/` | Templates for kanban, contracts, manifests |
| `.MEMORY/` | Context cards |
| `contracts/` | JSON Schema boundaries |
| `tools/*/MANIFEST.json` | Tool specs |
| `flows/latest/FLOW.md` | Pipeline |

---

## 7. TEMPLATES

All templates live in `.aura/templates/`:

| Template | Purpose |
|----------|---------|
| `KANBAN.template.json` | New plan template |
| `CONTRACT.template.json` | New contract template |
| `MANIFEST.template.json` | New tool manifest template |

**Usage:**
```bash
# Create new kanban plan
cp .aura/templates/KANBAN.template.json .aura/kanban/KANBAN-$(date +%Y-%m-%d-%H%M).json

# Create new contract
cp .aura/templates/CONTRACT.template.json contracts/new-name.schema.json
```

---

## 8. VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| v2.0 | 2026-03-02 | PROTOCOL.json as SSOT |
| v2.1 | 2026-03-02 | **Mandatory kanban planning**, timestamped kanban files, templates folder |
