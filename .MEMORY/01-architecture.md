# Architecture — CineTaste v5

## Design Principles

| Principle | Application |
|-----------|-------------|
| Contract-first | Define schema boundaries before implementation |
| Simple > Easy | Keep artifacts deterministic and inspectable |
| Stateless tools | Data in → data out, effects only at boundaries |
| SSOT runtime | `PROTOCOL.json` and `flows/latest/FLOW.md` drive execution |

## Core Pattern: PROTOCOL.json as SSOT

`PROTOCOL.json` declares:

- contracts (data boundaries),
- tools (CLI interfaces),
- flow (active stage ordering and modes).

No tool/runtime assumptions are valid unless they match `PROTOCOL.json`.

## Current Data Flow

```
ct-fetch -> movie-batch
ct-schedule -> movie-schedule
ct-cognize -> analysis-result
ct-filter -> filter-result
ct-format -> message-text
t2me -> send-confirmation
```

## Tool Boundary Model (Ports & Adapters)

```
adapter_* (integration) -> main.py (wiring/CLI) -> port.py (contract gate)
```

Shared domain logic across tools is avoided. Shared infra utilities are limited to `tools/_shared` (for example contract validation).

## Active Runtime Topology

```
ct-fetch -> ct-schedule -> ct-cognize -> ct-filter -> ct-format -> t2me
```

- `ct-analyze` remains in repository as a legacy compatibility tool.
- Active flow stage at position 3 is `ct-cognize`.
- Pipeline supports `--dry-run`: the full flow still runs, and Step 6 validates delivery via `t2me --dry-run` without live send.

## File Map

```
PROTOCOL.json             # Topology SSOT
contracts/*.schema.json   # Contract boundaries
tools/*/MANIFEST.json     # Tool specs + CLI API
flows/latest/FLOW.md      # Executable pipeline definition
.aura/kanban/latest       # Current implementation plan
```

---
*Last updated: 2026-03-05*
