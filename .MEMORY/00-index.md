# CineTaste v5 Memory Bank — Index

> Quick navigation for resumed sessions

## Bootstrap Sequence

```
1. Read AURA.md (directives)
2. Read PROTOCOL.json (system topology)
3. Read this file (memory index)
4. Read flows/latest/FLOW.md (pipeline)
5. Execute
```

## Memory Cards

| Card | Topic | When to Read |
|------|-------|--------------|
| [01-architecture.md](01-architecture.md) | System design and boundaries | First time / major changes |
| [02-contracts.md](02-contracts.md) | Data contracts and schemas | Working with data flow |
| [03-tools.md](03-tools.md) | CLI tools and manifests | Building/using tools |
| [04-taste.md](04-taste.md) | Taste profile structure | Modifying preferences |
| [05-troubleshooting.md](05-troubleshooting.md) | Common failure paths | Something broke |
| [06-ai-agents.md](06-ai-agents.md) | `ct-cognize` agent execution | Working with cognitive stage |
| [07-agent-preflight.md](07-agent-preflight.md) | Agent preflight configuration | Modifying agent behavior |
| [08-docs-template-preference.md](08-docs-template-preference.md) | Preferred premium docs style | Publishing docs / HTML rendering |
| [09-run-logging.md](09-run-logging.md) | Pipeline run logging system | Understanding artifact preservation |
| [10-ct-fetch.md](10-ct-fetch.md) | Batch movie discovery from kinoteatr.ru | Working on stage 1 / week-vs-day behavior |
| [11-ct-schedule.md](11-ct-schedule.md) | Showtime collection into `movie-schedule` | Working on stage 2 / per-movie session enrichment |
| [12-ct-time-price.md](12-ct-time-price.md) | Single movie URL time/price checks | Debugging one page or presale date mismatch |
| [13-ct-cognize.md](13-ct-cognize.md) | Cognitive stage input, prompt rules, and output merge | Running or modifying stage 3 |
| [14-codex-proxy.md](14-codex-proxy.md) | Proxy-backed headless Codex operator flow | Running `codex`/`codex review` through the local round-robin proxy |
| [15-review-short-tips.md](15-review-short-tips.md) | Fast reviewer mental model | Quick repo review / safe modifications |
| [16-ct-format.md](16-ct-format.md) | Telegram rendering horizons and relative-date copy | Modifying message layout or delivery readability |

## Quick Start

```bash
# Full production pipeline (live send)
./run

# Replay from cached analysis-result payload
./run --input contracts/examples/analysis-result.sample.json

# Resend existing message text
./run --resend message.txt
```

## Current State

- Version: `5.4.0`
- Paradigm: Contract-first, protocol-driven
- SSOT: `PROTOCOL.json`
- Active stage chain: `ct-fetch -> ct-schedule -> ct-cognize -> ct-filter -> ct-format -> t2me`

## Key Files

```
PROTOCOL.json            # System topology SSOT
AURA.md                  # Agent execution directives
.aura/kanban/latest      # Active task board
contracts/               # JSON Schema boundaries
tools/*/MANIFEST.json    # Tool specifications
flows/latest/FLOW.md     # Executable pipeline
```

---
*Last updated: 2026-04-07*
