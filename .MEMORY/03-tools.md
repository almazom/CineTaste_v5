# 🔧 Tools — CineTaste v5

## Tool Philosophy

| Principle | Rule |
|-----------|------|
| **One verb per tool** | ct-fetch, ct-analyze, ct-filter, ct-format |
| **Self-contained** | Each tool has its own folder, no shared code |
| **Contract-bound** | Input/output validated against schemas |
| **Stateless** | Data in → data out, no side effects (except t2me) |

## Tool Inventory

| Tool | Verb | Position | Input | Output | Adapter |
|------|------|----------|-------|--------|---------|
| ct-fetch | fetch | 1 | — | movie-batch | kinoteatr |
| ct-analyze | analyze | 2 | movie-batch | analysis-result | pi |
| ct-filter | filter | 3 | analysis-result | filter-result | — (pure) |
| ct-format | format | 4 | filter-result | message-text | telegram |
| t2me | send | 5 | message-text | send-confirmation | — (external) |

## Tool Structure

```
tools/ct-<verb>/
├── MANIFEST.json      # Specification (CLI, contracts, adapters)
├── main.py            # CLI entry point
├── port.py            # Input/output validation
└── adapter_*.py       # External integrations (optional)
```

## MANIFEST.json Schema

Every tool MUST have a MANIFEST.json with:

```json
{
  "identity": { "name", "verb", "position", "description" },
  "contracts": { "input", "output" },
  "cli": { "usage", "flags[]", "exit_codes" },
  "adapters": { ... },
  "files": { "required[]", "optional[]" }
}
```

## CLI Interface Rules

1. **--input, -i** — Input file (or stdin)
2. **--output, -o** — Output file (or stdout)
3. **--dry-run, -n** — Preview without side effects
4. **--help, -h** — Show usage
5. **Exit codes** — 0=success, 1=error, 2=bad args, 3=network, 4=parse

## Adding a New Tool

1. Define contracts (input/output)
2. Create `tools/ct-<verb>/MANIFEST.json`
3. Add to PROTOCOL.json under `tools`
4. Implement: main.py, port.py, adapter_*.py
5. Update flow in `flows/latest/FLOW.md`

## Adapter Pattern

Adapters handle external integrations:

```python
# adapter_kinoteatr.py
def fetch_movies(city: str, when: str) -> list[dict]:
    """Fetch movies from kinoteatr.ru"""
    # Implementation
    return movies
```

The main.py wires adapter → port → output.

---
*Last updated: 2026-03-02*
