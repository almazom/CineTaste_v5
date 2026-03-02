# KANBAN SSOT — Architecture Review Actions

Version: 1.0  
Date: 2026-03-02  
Scope: Convert 12 architecture/CLI/MD-orchestration findings into tracked work

## Status Model (3 States)

- TODO: planned, not started
- DOING: currently being implemented
- DONE: completed and verified

## Snapshot

- Total: 12
- TODO: 11
- DOING: 1
- DONE: 0

## Kanban Items (SSOT)

| ID | Task | Area | Priority | Status |
|---|---|---|---|---|
| AR-01 | Make pipeline runtime truly SSOT-driven (parse `PROTOCOL.json` + `flows/latest/FLOW.md` instead of hardcoded stages). | Orchestration | P0 | DOING |
| AR-02 | Align `FLOW.md` step contracts with actual tool behavior (especially `ct-format` output semantics). | Flow/Contracts | P0 | TODO |
| AR-03 | Enforce `ct-analyze --agent` behavior (explicit selection + documented fallback policy). | CLI/Analyze | P0 | TODO |
| AR-04 | Implement real self-healing on any pipeline failure (halt, log, preserve artifacts, recover path). | Reliability | P0 | TODO |
| AR-05 | Raise test coverage from current level to `PROTOCOL.json` target (80%+). | Testing | P1 | TODO |
| AR-06 | Remove CLI no-op flags or implement them fully (`ct-fetch --source`, `ct-format --template`). | CLI UX | P1 | TODO |
| AR-07 | Fix `ct-fetch` metadata so `meta.date` reflects requested `--when` value when provided. | Data Contract | P1 | TODO |
| AR-08 | Enforce JSON Schema `format` checks (URI/date-time) in shared validator. | Validation | P1 | TODO |
| AR-09 | Resolve documentation drift across SSOT files (`PROTOCOL`, `FLOW`, `.MEMORY`, `AGENTS`, version/state alignment). | Docs/SSOT | P1 | TODO |
| AR-10 | Reconcile architecture principle “no shared code” with actual shared module strategy (`tools/_shared`). | Architecture | P2 | TODO |
| AR-11 | Make tests deterministic by isolating network-dependent fetch tests (mock/integration split). | Testing | P2 | TODO |
| AR-12 | Unify `t2me` send guidance (`pipe` vs `--file`) across manifests and agent docs. | Docs/CLI | P2 | TODO |

## Execution Order (Recommended)

1. AR-01
2. AR-02
3. AR-03
4. AR-04
5. AR-08
6. AR-07
7. AR-06
8. AR-09
9. AR-05
10. AR-11
11. AR-12
12. AR-10

## Notes

- This Markdown file is the SSOT for review remediation tracking.
- Status updates should be applied here first, then mirrored into any JSON kanban/reporting format if needed.
- If a task is blocked, keep it in `DOING` and add a short blocker note inline until unblocked.
