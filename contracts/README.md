# Contracts — JSON Schema Boundaries

Every data boundary in CineTaste is defined by a JSON Schema contract.

## Contract Chain

```
ct-fetch ──→ movie-batch ──→ ct-analyze ──→ analysis-result ──→ ct-filter
                                                              │
                                                              ▼
t2me ←── message-text ←── ct-format ←── filter-result ←──────┘
```

## Contracts

| Contract | Producer | Consumer | Description |
|----------|----------|----------|-------------|
| `movie-batch` | ct-fetch | ct-analyze | Raw movies from cinema |
| `analysis-result` | ct-analyze | ct-filter | AI-scored movies |
| `filter-result` | ct-filter | ct-format | Filtered recommendations |
| `message-text` | ct-format | t2me | Telegram markdown |
| `send-confirmation` | t2me | — | Delivery status |

## Validation

All contracts use:
- `additionalProperties: false` — strict shapes
- Required fields — must be present
- Type checking — enforced at runtime

## Usage

```bash
# Validate data against schema
python3 -c "
import json, jsonschema
data = json.load(open('data.json'))
schema = json.load(open('contracts/movie-batch.schema.json'))
jsonschema.validate(data, schema)
print('Valid!')
"
```

## Adding a Contract

1. Create `contracts/new-name.schema.json`
2. Add to `PROTOCOL.json` under `contracts`
3. Update producer/consumer tool manifests
4. Implement validation in `port.py`
