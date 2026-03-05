# Independent CLI/API/Contracts Review — CineTaste v5

## 1) Executive Summary
The architecture intent is strong, but the CLI/API contract surface is not yet operationally strict enough for safe replaceability. The biggest gaps are: inconsistent exit-code semantics, manifest-to-runtime drift, missing input-boundary enforcement in `ct-cognize`, and weak schema governance for conditional fields and threshold metadata.

If these are not tightened, tool swaps will remain risky because consumers cannot rely on stable behavior from CLI flags, exit codes, and contract semantics.

## 2) Missing CLI/API standardization details

### 2.1 Exit-code taxonomy is declared, but not uniformly enforced
Observed:
- Manifests define `2 = invalid arguments` and `4 = parse/contract error`.
- Runtime: missing `--input` file returns `1` in multiple tools (`ct-schedule`, `ct-analyze`, `ct-filter`, `ct-format`, `ct-cognize`).

Missing standard:
- Required file-path arguments must be prevalidated before execution.
- Non-existent required file path must always return `2`.

Operational acceptance check:
```bash
./ct-filter --input /tmp/no-such.json
# expected: exit 2
```

### 2.2 Manifest/runtime drift for agent API (`ct-analyze`)
Observed:
- Manifest usage/adapters describe `auto|kimi|pi|dry_run`.
- Runtime parser accepts `auto|kimi|gemini|qwen|pi|dry_run`.
- Runtime adapter chain includes `gemini` and `qwen`.

Missing standard:
- `MANIFEST.json` must be the executable API truth for accepted values.
- CI must fail if runtime arg choices differ from manifest declaration.

Operational acceptance check:
```bash
pytest tests/test_cli_manifest_runtime_sync.py -k ct_analyze_agents
```

### 2.3 Active-stage CLI conformance tests are not stage-driven
Observed:
- `tests/test_cli_tools.py` excludes `ct-cognize` from `CT_TOOLS`.
- `tests/test_pipeline_flow.py` wrapper check still centers legacy `ct-analyze`.
- Active stage in `PROTOCOL.json`/`FLOW.md` is `ct-cognize`.

Missing standard:
- CLI conformance tests must derive tool list from `PROTOCOL.json` active tools (`status != legacy`).

Operational acceptance check:
```bash
python3 - <<'PY'
import json
p=json.load(open('PROTOCOL.json'))
print([k for k,v in p['tools'].items() if v.get('status')!='legacy'])
PY
# expected list must be exactly what CLI conformance tests iterate
```

### 2.4 Input boundary enforcement is not mandatory at tool entrypoint
Observed:
- `ct-cognize` declares input contract `movie-schedule@1.0.0` but does not call `enforce_input`.
- Runtime demo: `ct-cognize` accepts `{}` and exits `0` with `analyzed=[]`.

Missing standard:
- Any tool with declared input contract must run `enforce_input(...)` before adapter/network/agent calls.

Operational acceptance check:
```bash
echo '{}' > /tmp/bad.json
./ct-cognize --input /tmp/bad.json --taste taste/profile.yaml --agent pi
# expected: exit 4 with Contract violation(movie-schedule input)
```

### 2.5 Flag domain validation is underspecified (`ct-filter`)
Observed:
- Manifest/help says `--min-score` is `0-100`, but runtime accepts `-5` and exits `0`.
- `--recommendation` accepts arbitrary tokens, producing permissive `meta.thresholds` values.

Missing standard:
- Parse-time validation for numeric ranges and enum domains.
- Invalid domain value must exit `2`.

Operational acceptance check:
```bash
./ct-filter --input contracts/examples/analysis-result.sample.json --min-score -5
# expected: exit 2
```

### 2.6 CLI error message envelope is not standardized
Observed:
- Error prefixes vary (`Error:`, `Unexpected error:`, `Validation error:`), making machine parsing brittle.

Missing standard:
- Define stderr envelope: `ERROR_CODE`, `CLASS`, `MESSAGE`.

Operational acceptance check:
```bash
./ct-format --input /tmp/no-such.json 2>err.log
# expected first line matches regex: ^\[E[0-9]{3}\]\s+[A-Z_]+:\s+
```

## 3) Missing contract governance details

### 3.1 `send-confirmation` lacks conditional invariants
Observed:
- Schema allows `{"success": true, "meta": {"sent_at": ...}}` with no `message_id`.

Missing governance:
- If `success=true`, require `message_id` and forbid `error`.
- If `success=false`, require `error`.

Operational acceptance check:
```bash
python3 - <<'PY'
import sys
sys.path.insert(0,'tools/_shared')
from validate import validate_against_contract
ok,err=validate_against_contract({'success':True,'meta':{'sent_at':'2026-03-04T12:00:00+00:00'}},'send-confirmation')
print(ok,err)
PY
# expected: False
```

### 3.2 `filter-result.meta.thresholds` is weakly constrained
Observed:
- `thresholds.recommendations` is `array[string]` (no enum).
- `thresholds.min_score` has no min/max.

Missing governance:
- Contract must constrain metadata to valid runtime domain (`must_see|recommended`, `0..100`).

Operational acceptance check:
```bash
python3 tools/_shared/validate.py filter-result /tmp/payload-with-min-score-999.json
# expected: invalid
```

### 3.3 Version governance is present in metadata, but not enforced in validator behavior
Observed:
- Schemas and protocol carry version fields.
- Shared validator hardcodes `@1.0.0` in error text.

Missing governance:
- Validator should read schema version dynamically and report actual contract version.

Operational acceptance check:
```bash
pytest tests/test_validate_shared.py -k "version_message"
# expected: error mentions effective schema version, not hardcoded constant
```

### 3.4 No schema governance for `MANIFEST.json`
Observed:
- Tool manifests are critical API docs but no manifest schema gate is present.

Missing governance:
- Add `contracts/tool-manifest.schema.json` and validate every `tools/*/MANIFEST.json` in CI.

Operational acceptance check:
```bash
python3 scripts/validate_manifests.py
# expected: validates all manifests, fails on missing required keys/invalid enum
```

### 3.5 Contract docs are not governed against topology SSOT
Observed:
- `contracts/README.md` and `contracts/viz/README.md` still describe `ct-analyze` stage chain.
- Active flow/protocol uses `ct-cognize`.

Missing governance:
- Documentation must be generated from or verified against `PROTOCOL.json`.

Operational acceptance check:
```bash
python3 scripts/check_contract_docs_sync.py
# expected: pass only when producer/consumer names match PROTOCOL
```

### 3.6 Sample artifact policy is incomplete
Observed:
- `send-confirmation` has schema but no canonical sample file in `contracts/examples/`.

Missing governance:
- Require `*.sample.json` for every contract plus one invalid fixture per contract.

Operational acceptance check:
```bash
python3 scripts/check_contract_fixtures.py
# expected: all contracts have valid and invalid fixtures
```

## 4) Replaceability guarantees: gaps and risks

| Gap | Replaceability Risk | Concrete Failure Mode |
|---|---|---|
| Manifest/runtime drift | Replacement tool built from manifest behaves differently in production | Agent option accepted by runtime but undocumented in manifest-driven integrator |
| Missing input enforcement (`ct-cognize`) | Upstream contract swap can silently degrade quality without failing fast | Invalid input shape still returns success (`analyzed=[]`) |
| Exit code inconsistency | Orchestrator cannot route failures deterministically | Missing input file treated as generic error instead of invalid-arg class |
| Weak conditional schema (`send-confirmation`) | Different adapters emit incompatible success/failure semantics | `success=true` without `message_id` passes contract gate |
| Active/legacy test drift | Replaced active stage may ship untested CLI conformance | `ct-cognize` not covered by same manifest/help contract checks |
| Weak threshold contract | Filters can be replaced with incompatible threshold metadata semantics | `min_score=-5` accepted and propagated |

## 5) Concrete additions (snippets/checklists)

### 5.1 Snippet: strict CLI exit-code contract (to place in Golden Standard / AURA)
```md
CLI Exit Code Contract
- 0: success
- 2: invalid CLI arguments or invalid file paths provided by user
- 3: dependency/runtime adapter failure (network/agent/external CLI)
- 4: JSON parse or contract validation failure
- 1: internal unexpected error only
```

### 5.2 Snippet: `send-confirmation` conditional schema hardening
```json
"allOf": [
  {
    "if": { "properties": { "success": { "const": true } } },
    "then": { "required": ["message_id"], "not": { "required": ["error"] } },
    "else": { "required": ["error"] }
  }
]
```

### 5.3 Snippet: `filter-result` threshold constraints
```json
"thresholds": {
  "type": "object",
  "required": ["recommendations", "min_score"],
  "properties": {
    "recommendations": {
      "type": "array",
      "items": { "type": "string", "enum": ["must_see", "recommended"] },
      "minItems": 1
    },
    "min_score": { "type": "number", "minimum": 0, "maximum": 100 }
  },
  "additionalProperties": false
}
```

### 5.4 Checklist: CLI/API conformance gate
- Load active tools from `PROTOCOL.json` where `status != legacy`.
- For each active tool, assert wrapper exists and `--help` includes all manifest flags.
- For each required file arg (`--input`, `--taste`), missing path must return exit `2`.
- For each tool with input contract, malformed input must return exit `4` before side effects.
- For each enum/range flag, invalid domain must return exit `2`.

### 5.5 Checklist: contract governance gate
- Validate each `contracts/*.schema.json` with draft-07 parser.
- Validate each `tools/*/MANIFEST.json` against `tool-manifest.schema.json`.
- Assert every contract has `examples/<name>.sample.json` valid fixture.
- Assert every contract has `examples-invalid/<name>.invalid.json` invalid fixture.
- Assert docs producer/consumer chains match `PROTOCOL.json`.
- Assert validator error message uses actual schema version.

## 6) Priority table (High/Medium/Low)

| Priority | Item | Why it matters now | Operational gate |
|---|---|---|---|
| High | Enforce input-contract check in `ct-cognize` | Silent acceptance of malformed upstream payload breaks boundary guarantees | `ct-cognize` with `{}` must fail with exit `4` |
| High | Normalize missing-file exit behavior to `2` | Orchestrator and tests cannot reliably classify user/input errors | all tools return `2` for missing required input files |
| High | Fix manifest/runtime agent drift (`ct-analyze`) | API docs cannot be trusted for replacement tooling | manifest choices == argparse choices == adapter registry |
| High | Add conditional invariants to `send-confirmation` | Delivery success semantics currently ambiguous | `success=true` without `message_id` must fail schema validation |
| Medium | Constrain `filter-result.meta.thresholds` | Threshold metadata currently allows invalid operational states | invalid `min_score` and recommendation token fail contract |
| Medium | Make CLI conformance tests derive active tools from protocol | Active stage (`ct-cognize`) currently under-gated in generic CLI checks | test list auto-derived from `PROTOCOL.tools` |
| Medium | Add manifest schema validation gate | Prevent structural drift in machine-readable API definitions | `scripts/validate_manifests.py` required in CI |
| Low | Standardize stderr error envelope | Improves machine parsing and incident triage | stderr first line format gate |
| Low | Require contract invalid fixtures per schema | Improves governance completeness and negative-case confidence | fixture completeness check script passes |
