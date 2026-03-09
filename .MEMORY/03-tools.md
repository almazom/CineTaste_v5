# Tools — CineTaste v5

## Tool Philosophy

| Principle | Rule |
|-----------|------|
| One verb per tool | Each tool owns one pipeline responsibility |
| Contract-bound | Every input/output validated against schema |
| Stateless by default | No hidden shared mutable state |
| Observable CLI | Stable flags, stable exit taxonomy, stderr diagnostics |

## Active Tool Inventory

| Tool | Verb | Position | Input | Output | Status |
|------|------|----------|-------|--------|--------|
| ct-fetch | fetch | 1 | — | movie-batch | active |
| ct-schedule | schedule | 2 | movie-batch | movie-schedule | active |
| ct-cognize | cognize | 3 | movie-schedule | analysis-result | active |
| ct-filter | filter | 4 | analysis-result | filter-result | active |
| ct-format | format | 5 | filter-result | message-text | active |
| t2me | send | 6 | message-text | send-confirmation | external |
| ct-analyze | analyze | 3 | movie-schedule | analysis-result | legacy |

## `ct-cognize` CLI Surface

Key flags:

- `--input|-i <FILE|->`
- `--taste|-t <FILE>`
- `--output|-o <FILE|->`
- `--agent|-a <auto|kimi|gemini|qwen|pi>`
- `--agents <LIST>`
- `--list-agents`
- `--version`
- `--trace-id <ID>`
- `--timings`
- `--quiet|-q` / `--verbose|-v`

Exit taxonomy:

- `0` success
- `1` internal unexpected error
- `2` invalid args
- `3` path/stdin/output filesystem error
- `4` agent availability/runtime failure
- `5` contract or JSON parse error

## Tool Structure

```
tools/ct-<verb>/
├── MANIFEST.json
├── main.py
├── port.py
└── adapter_*.py (if needed)
```

## Tool Update Workflow

1. Update contract schema(s)
2. Update tool `MANIFEST.json`
3. Update `PROTOCOL.json` references
4. Update `flows/latest/FLOW.md` execution path
5. Add/adjust tests
6. Verify runtime and contracts

---
*Last updated: 2026-03-05*
