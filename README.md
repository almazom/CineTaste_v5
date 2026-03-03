# CineTaste v5.3.0

> AI-powered cinema recommendations delivered to Telegram

## What's New in v5.3.0

| Feature | Description |
|---------|-------------|
| **New Stage** | Added `ct-schedule` with `movie-schedule` contract between fetch and analyze |
| **SSOT Runtime** | `./run` parses `PROTOCOL.json` + `flows/latest/FLOW.md` at execution |
| **Self-Healing** | Any failure halts, logs, and preserves artifacts with recovery hints |
| **Strict CLI Flags** | `ct-analyze --agent`, `ct-fetch --source`, `ct-format --template` now enforced |
| **Contract Enforcement** | JSON Schema `format` (`uri`, `date-time`) checks are active |
| **Deterministic Tests** | Network tests are marked and excluded by default (`-m "not network"`) |

## Quick Start

```bash
# Preview recommendations (dry-run path from FLOW, no Telegram send)
./run --dry-run

# Full production run
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
       │     ├── ct-schedule/   # Showtime enrichment stage
       │     ├── ct-analyze/    # AI analysis (auto|kimi|pi|dry_run)
       │     ├── ct-filter/     # Taste threshold filter
       │     ├── ct-format/     # Telegram markdown
       │     └── _shared/       # Shared infra utilities (validation only)
       │
       └── flows/ ─────── Pipeline steps
             └── latest/FLOW.md
```

## Pipeline

```
ct-fetch → ct-schedule → ct-analyze → ct-filter → ct-format → t2me
    │            │             │           │           │        │
    ▼            ▼             ▼           ▼           ▼        ▼
movies      scheduled      analyzed    filtered    message   Telegram
(47)        (47)           (46)        (6)         (text)    (sent)
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

# Deterministic suite (default)
make test

# Optional network integration tests
python3 -m pytest tests/ -m network -v

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
*Version: 5.3.0*
