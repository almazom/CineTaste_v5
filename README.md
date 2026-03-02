# CineTaste v5

> AI-powered cinema recommendations delivered to Telegram

## What's New in v5

| Feature | Description |
|---------|-------------|
| **PROTOCOL.json** | Single source of truth for system topology |
| **Contract-first** | All data boundaries defined before code |
| **Tool manifests** | JSON specs for every CLI tool |
| **Simplification** | Built on "Simple Made Easy" principles |

## Quick Start

```bash
# Preview recommendations
./run --dry-run

# Send to Telegram
./run
```

## Architecture

```
PROTOCOL.json (SSOT)
       │
       ├── contracts/ ─── JSON Schema boundaries
       │
       ├── tools/ ─────── CLI microservices
       │     └── */MANIFEST.json
       │
       └── flows/ ─────── Pipeline steps
             └── latest/FLOW.md
```

## Key Files

| File | Purpose |
|------|---------|
| `PROTOCOL.json` | System manifest (SSOT) |
| `AURA.md` | Agent directives |
| `AGENTS.md` | AI agent instructions |
| `.MEMORY/` | Context cards |
| `contracts/` | JSON Schema boundaries |
| `tools/*/MANIFEST.json` | Tool specifications |

## Pipeline

```
ct-fetch → ct-analyze → ct-filter → ct-format → t2me
    │           │           │           │        │
    ▼           ▼           ▼           ▼        ▼
movies      analyzed    filtered    message   Telegram
```

## Philosophy

Based on Rich Hickey's "Simple Made Easy":

- **Simple > Easy**: Artifact simplicity over authoring convenience
- **Uncomplect**: One responsibility per tool
- **Data > Logic**: Declarative over imperative
- **MVS**: Minimum Viable Solution

## Documentation

- [AGENTS.md](AGENTS.md) — AI agent instructions
- [AURA.md](AURA.md) — System protocol
- [.MEMORY/](.MEMORY/00-index.md) — Context cards

---
*Version: 5.0.0*
