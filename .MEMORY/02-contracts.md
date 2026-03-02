# 📋 Contracts — CineTaste v5

## What Are Contracts?

Contracts are **JSON Schema** files that define the shape of data at every boundary.

**Rule:** Every tool input/output MUST have a contract.

## Contract Chain

```
ct-fetch ──→ movie-batch.schema.json ──→ ct-analyze
ct-analyze ──→ analysis-result.schema.json ──→ ct-filter
ct-filter ──→ filter-result.schema.json ──→ ct-format
ct-format ──→ message-text.schema.json ──→ t2me
t2me ──→ send-confirmation.schema.json ──→ done
```

## Contract Summary

| Contract | Producer | Consumer | Key Fields |
|----------|----------|----------|------------|
| `movie-batch` | ct-fetch | ct-analyze | movies[], meta |
| `analysis-result` | ct-analyze | ct-filter | analyzed[], relevance_score, recommendation |
| `filter-result` | ct-filter | ct-format | filtered[], matched count |
| `message-text` | ct-format | t2me | text (markdown) |
| `send-confirmation` | t2me | — | success, message_id |

## Contract Structure

Every contract follows this template:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "contract-name.schema.json",
  "title": "Human Readable Title",
  "version": "1.0.0",
  "description": "What this contract represents",
  "type": "object",
  "required": ["field1", "field2"],
  "properties": {
    "field1": { "type": "string", "description": "Purpose" }
  },
  "additionalProperties": false
}
```

## Validation Rules

1. **additionalProperties: false** — No extra fields allowed
2. **required fields** — Must be present
3. **type checking** — Enforced at runtime
4. **enum values** — Limited to declared options

## Adding a New Contract

1. Create `contracts/new-contract.schema.json`
2. Add to PROTOCOL.json under `contracts`
3. Update producer/consumer tools' MANIFEST.json
4. Add validation to port.py

## Contract Versioning

| Change Type | Action |
|-------------|--------|
| Add required field | New version (breaking) |
| Remove field | New version (breaking) |
| Change type | New version (breaking) |
| Add optional field | In-place (non-breaking) |

---
*Last updated: 2026-03-02*
