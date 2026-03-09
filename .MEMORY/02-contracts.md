# Contracts — CineTaste v5

## Purpose

Contracts are JSON Schemas defining every tool boundary.
Each stage must emit payloads that validate against its declared output contract.

## Active Contract Chain

```
ct-fetch     -> movie-batch
ct-schedule  -> movie-schedule
ct-cognize   -> analysis-result
ct-filter    -> filter-result
ct-format    -> message-text
t2me         -> send-confirmation
```

## Contract Summary

| Contract | Producer | Consumer | Required Top-Level Fields |
|----------|----------|----------|---------------------------|
| `movie-batch` | ct-fetch | ct-schedule | `movies`, `meta` |
| `movie-schedule` | ct-schedule | ct-cognize | `movies`, `meta` |
| `analysis-result` | ct-cognize | ct-filter | `analyzed`, `meta` |
| `filter-result` | ct-filter | ct-format | `filtered`, `meta` |
| `message-text` | ct-format | t2me | `text`, `meta` |
| `send-confirmation` | t2me | — | `success`, `meta` |

Legacy compatibility note:
- `ct-analyze` still appears in `PROTOCOL.json` as a legacy consumer/producer for migration boundaries around `movie-schedule` and `analysis-result`.

## Validation Rules

1. `additionalProperties: false` is enforced in contracts.
2. Runtime validation is mandatory at tool boundaries (`port.py`).
3. Format checks (`uri`, `date-time`) are active in shared validator.

## Versioning

| Change Type | Rule |
|-------------|------|
| Breaking shape change | Create new contract version and update all producers/consumers |
| Optional additive field | Backward-compatible update permitted |
| Producer/consumer swap | Update `PROTOCOL.json` + manifests + flow |

## Practical Checks

```bash
# Validate contract examples quickly
python3 tools/_shared/validate.py movie-schedule contracts/examples/movie-schedule.sample.json
python3 tools/_shared/validate.py analysis-result contracts/examples/analysis-result.sample.json
```

---
*Last updated: 2026-03-05*
