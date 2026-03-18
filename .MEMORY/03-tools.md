# Tools — CineTaste v5

> Purpose: quick inventory and routing guide for the CLI layer
> Updated: 2026-03-18

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
| ct-time-price | time-price | 2 | — | movie-showtimes | active, auxiliary |
| ct-cognize | cognize | 3 | movie-schedule | analysis-result | active |
| ct-filter | filter | 4 | analysis-result | filter-result | active |
| ct-format | format | 5 | filter-result | message-text | active |
| t2me | send | 6 | message-text | send-confirmation | external |
| ct-provider-latest | provider-latest | 7 | — | provider-latest | active, auxiliary |
| ct-analyze | analyze | 3 | movie-schedule | analysis-result | legacy |

## Wrapper Paths

Agents normally invoke the repo-root wrappers, not `python3 tools/.../main.py` directly:

```bash
./ct-fetch
./ct-schedule
./ct-time-price
./ct-cognize
./ct-filter
./ct-format
```

## Which Tool To Use

| Need | Tool | Why |
|------|------|-----|
| Get the current movie list for a city | `ct-fetch` | Produces the canonical `movie-batch` payload |
| Attach showtimes to a movie batch | `ct-schedule` | Produces the canonical `movie-schedule` payload |
| Check one movie page for time/price without batch context | `ct-time-price` | Smallest valid probe for a single URL |
| Judge fit against the taste profile | `ct-cognize` | Produces the canonical `analysis-result` payload |
| Inspect the latest local provider session file | `ct-provider-latest` | Auxiliary debugging / artifact lookup |

## Dedicated Tool Cards

Open the specific card when you need stage-level detail:

- [10-ct-fetch.md](10-ct-fetch.md)
- [11-ct-schedule.md](11-ct-schedule.md)
- [12-ct-time-price.md](12-ct-time-price.md)
- [13-ct-cognize.md](13-ct-cognize.md)

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

Related cards:

- [06-ai-agents.md](06-ai-agents.md) for agent selection and preflight
- [13-ct-cognize.md](13-ct-cognize.md) for cognitive-stage behavior and prompt rules

## Batch and Single-Movie Probes

Quick routing:

```bash
# Batch discovery
./ct-fetch --city naberezhnie-chelni --when week --output /tmp/movies.json

# Schedule enrichment
./ct-schedule --input /tmp/movies.json --output /tmp/scheduled.json

# Single movie URL probe
./ct-time-price --url https://kinoteatr.ru/film/.../naberezhnie-chelni/ --date 2026-03-29
```

Rule of thumb:

- `ct-time-price` is a single-page probe, not a replacement for `ct-schedule`
- use it to confirm exact page date/time/price before building or extracting a one-movie `movie-schedule` payload for `ct-cognize`

## `ct-provider-latest` CLI Surface

Key flags:

- `--project-dir|-p <DIR>`
- `--provider|-r <all|claude|qwen|pi|gemini>`
- `--latest`
- `--output|-o <FILE|->`
- `--version`

Purpose:

- locate the newest project-scoped `json/jsonl` session file per local AI provider;
- bind provider history to a real project folder instead of a guessed slug;
- produce machine-readable JSON that downstream extraction tooling can consume.

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
*Last updated: 2026-03-18*
