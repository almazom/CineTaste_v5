# CineTaste v5.4.0

> AI-powered cinema recommendations delivered to Telegram

## What's New in v5.4.0

| Feature | Description |
|---------|-------------|
| **Cognitive Stage** | `ct-cognize` is active at position 3 (`ct-analyze` is legacy) |
| **Flow v1.3** | Runtime chain is `ct-fetch → ct-schedule → ct-cognize → ct-filter → ct-format → t2me` |
| **Strict SSOT Runtime** | `./run` parses `PROTOCOL.json` + `flows/latest/FLOW.md` on every execution |
| **Safe Pipeline Dry-Run** | `./run --dry-run` executes all stages and validates send with `t2me --dry-run` (no live delivery) |
| **Contract Enforcement** | Input/output contracts validated with JSON Schema format checks |

## Quick Start

```bash
# Full production pipeline (sends to Telegram)
./run

# Re-run format/send from cached analysis-result payload
./run --input contracts/examples/analysis-result.sample.json

# Full pipeline without live Telegram send
./run --dry-run

# Resend an existing rendered message text file
./run --resend message.txt

# Run tests
make test

# Coverage
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
       │     ├── ct-schedule/   # Showtime enrichment
       │     ├── ct-cognize/    # Cognitive AI analysis
       │     ├── ct-filter/     # Recommendation filter
       │     ├── ct-format/     # Telegram markdown renderer
       │     └── _shared/       # Shared validation utilities
       │
       └── flows/ ─────── Pipeline steps
             └── latest/FLOW.md
```

## Pipeline

```
ct-fetch → ct-schedule → ct-cognize → ct-filter → ct-format → t2me
```

## AI Agents for `ct-cognize`

| Agent | Status | Mode |
|-------|--------|------|
| **kimi** | ✅ Active | `stdin` |
| **gemini** | ✅ Active | `cwd` |
| **qwen** | ✅ Active | `cwd` |
| **pi** | ✅ Active | `@file` |

Default selection mode:
`auto` = parallel preflight race, then ordered runtime fallback.

## Testing

```bash
# Unit and contract tests
make test

# Coverage report
make test-cov

# Network integration subset
python3 -m pytest tests/ -m network -v
```

## Key Files

| File | Purpose |
|------|---------|
| `PROTOCOL.json` | System manifest (SSOT) |
| `AURA.md` | Agent directives (execution discipline) |
| `.aura/kanban/latest` | Active task board |
| `.MEMORY/` | Context cards |
| `flows/latest/FLOW.md` | Executable runtime pipeline |

## Documentation

- [AURA.md](AURA.md) — System protocol
- [AGENTS.md](AGENTS.md) — Agent operating rules
- [.MEMORY/00-index.md](.MEMORY/00-index.md) — Memory bank index
- [.MEMORY/06-ai-agents.md](.MEMORY/06-ai-agents.md) — `ct-cognize` agent execution notes

---
*Version: 5.4.0*
