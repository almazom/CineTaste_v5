# CineTaste v5.1.0

> AI-powered cinema recommendations delivered to Telegram

## What's New in v5.1.0

| Feature | Description |
|---------|-------------|
| **kimi Integration** | Web search for unknown movies |
| **Agent Fallback** | kimi → pi → dry_run chain |
| **pytest Suite** | 35 automated tests |
| **E2E Testing** | Full pipeline validation |
| **AURA v2.2** | Testing protocol documentation |

## Quick Start

```bash
# Preview recommendations (no AI, no Telegram)
./run --dry-run

# Full production run (kimi AI → Telegram)
./run

# Run tests
make test

# Run with coverage
make test-cov
```

## Architecture

```
PROTOCOL.json (SSOT)
       │
       ├── contracts/ ─── JSON Schema boundaries
       │
       ├── tools/ ─────── CLI microservices
       │     ├── ct-fetch/      # Kinoteatr.ru scraper
       │     ├── ct-analyze/    # AI analysis (kimi/pi)
       │     ├── ct-filter/     # Taste threshold filter
       │     ├── ct-format/     # Telegram markdown
       │     └── _shared/       # Shared validation
       │
       └── flows/ ─────── Pipeline steps
             └── latest/FLOW.md
```

## Pipeline

```
ct-fetch → ct-analyze → ct-filter → ct-format → t2me
    │           │           │           │        │
    ▼           ▼           ▼           ▼        ▼
movies      analyzed    filtered    message   Telegram
(47)        (46)        (6)         (text)    (sent)
```

## AI Agents

| Agent | Status | Best For |
|-------|--------|----------|
| **kimi** | ✅ Primary | Web search, unknown movies |
| **pi** | ✅ Fallback | Fast reasoning |
| **dry_run** | ✅ Testing | Mock analysis |

### Preflight Check

```bash
kimi -p "1+2=...[ONLY NUMBER IN WORDS]" --print --final-message-only
# Expected: three

pi -p "1+2=...[ONLY NUMBER IN WORDS]" --no-tools
# Expected: three
```

## Testing

```bash
# Unit tests
make test           # pytest tests/ -v

# Coverage report
make test-cov       # pytest --cov

# E2E dry-run
make dry-run        # ./run --dry-run

# Production run
make run            # ./run
```

## Key Files

| File | Purpose |
|------|---------|
| `PROTOCOL.json` | System manifest (SSOT) |
| `AURA.md` | Agent directives (v2.2) |
| `.aura/kanban/` | Planning history |
| `.MEMORY/` | Context cards |
| `contracts/` | JSON Schema boundaries |
| `tests/` | pytest test suite |

## Philosophy

Based on Rich Hickey's "Simple Made Easy":

- **Simple > Easy**: Artifact simplicity over authoring convenience
- **Uncomplect**: One responsibility per tool
- **Data > Logic**: Declarative over imperative
- **MVS**: Minimum Viable Solution

## Documentation

- [AURA.md](AURA.md) — System protocol (v2.2)
- [AGENTS.md](AGENTS.md) — AI agent instructions
- [.MEMORY/00-index.md](.MEMORY/00-index.md) — Context cards
- [.MEMORY/06-ai-agents.md](.MEMORY/06-ai-agents.md) — AI agent guide

---
*Version: 5.1.0*
