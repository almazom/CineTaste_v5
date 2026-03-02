# 🏗️ Architecture — CineTaste v5

## Design Philosophy

Based on Rich Hickey's "Simple Made Easy":

| Principle | Application |
|-----------|-------------|
| **Simple ≠ Easy** | Choose simple artifacts over easy authoring |
| **Uncomplect** | Each tool has ONE responsibility |
| **Data > Logic** | PROTOCOL.json declares, code executes |
| **MVS** | Minimum Viable Solution — no premature abstraction |
| **Stateless** | Pure functions, effects at boundaries only |

## Core Patterns

### 1. PROTOCOL.json as SSOT

Single file declares the entire system:

```json
{
  "contracts": { ... },  // Data boundaries
  "tools": { ... },      // CLI interfaces
  "flow": { ... }        // Pipeline stages
}
```

**Rule:** Read PROTOCOL.json FIRST. It defines what exists.

### 2. Contract-First Development

```
DEFINE contract → SPECIFY tool → DESCRIBE flow → TEST → VERSION
```

Never write code without a contract.

### 3. Ports & Adapters (Вилка-Розетка)

```
┌─────────────────────────────────────────┐
│              ct-fetch                    │
│                                          │
│  adapter_kinoteatr.py ─→ main.py ─→ port.py
│  (plug / вилка)          (wiring)  (socket / розетка)
│                                          │
│  Adapter: HOW to get data                │
│  Port:    WHAT shape data must be        │
└─────────────────────────────────────────┘
```

### 4. Vertical Slicing

Each tool is self-contained:

```
tools/ct-fetch/
├── MANIFEST.json      # Specification
├── main.py            # CLI entry
├── port.py            # Validation
└── adapter_*.py       # External integrations
```

**Zero shared code between tools.**

## Data Flow

```
ct-fetch ──→ movie-batch ──→ ct-analyze ──→ analysis-result
                                         │
                                         ▼
t2me ←── message-text ←── ct-format ←── filter-result
```

## File Map

```
CineTaste_v5/
├── AURA.md                    # Agent directives
├── PROTOCOL.json              # ★ SSOT — system manifest
├── contracts/                 # JSON Schema boundaries
│   ├── movie-batch.schema.json
│   ├── analysis-result.schema.json
│   ├── filter-result.schema.json
│   ├── message-text.schema.json
│   └── send-confirmation.schema.json
├── tools/                     # CLI microservices
│   ├── ct-fetch/MANIFEST.json
│   ├── ct-analyze/MANIFEST.json
│   ├── ct-filter/MANIFEST.json
│   ├── ct-format/MANIFEST.json
│   └── t2me/MANIFEST.json
├── flows/                     # Pipeline versions
│   └── v1.0/FLOW.md
├── .MEMORY/                   # Context cards
├── taste/profile.yaml         # User preferences
├── templates/                 # Output templates
└── logs/                      # Execution logs
```

## Anti-Patterns (Avoid)

| Anti-Pattern | Why It's Bad |
|--------------|--------------|
| Shared `internal/` code | Creates hidden coupling |
| Mutable global state | Unpredictable behavior |
| Magic strings/numbers | Unclear intent |
| Deep nesting | Hard to reason about |
| Premature abstraction | Adds complexity without value |

---
*Last updated: 2026-03-02*
