# Troubleshooting — CineTaste v5

## 1. Input Contract Failures

Symptom:
- `Contract violation (movie-schedule@1.0.0 input)` from `ct-cognize`.

Checks:
```bash
python3 tools/_shared/validate.py movie-schedule <your_file.json>
```

Fix:
- Ensure payload has both `movies` and `meta`.
- Remove undeclared fields (contracts enforce `additionalProperties: false`).

## 2. Agent Availability Failures

Symptom:
- `Agent error: No AI agent available...`
- `preflight ... fail` diagnostics.

Checks:
```bash
ct-cognize --list-agents
kimi -p "ok" --print --final-message-only
pi -p "ok" --no-tools
```

Fix:
- Install/configure at least one supported agent CLI.
- Use explicit ordered chain when needed:
```bash
ct-cognize --input scheduled.json --taste taste/profile.yaml --agents pi,qwen,gemini
```

## 3. Path / Output Errors

Symptom:
- exit code `3` and `Path error: ...`.

Checks:
- Confirm `--input` file exists (or use `--input -` for stdin).
- Confirm `--taste` file exists.
- Confirm output directory exists for `--output`.

## 4. Stderr/Stdout Discipline in Automation

If parsers fail on output, verify diagnostics did not leak into stdout:

```bash
cat scheduled.json | ct-cognize --input - --taste taste/profile.yaml --quiet > analyzed.json
```

- JSON payload should be in `analyzed.json`.
- Diagnostics stay on stderr.

## 5. Pipeline Recovery

```bash
# Re-run from cached analysis payload
./run --input contracts/examples/analysis-result.sample.json

# Resend existing rendered text
./run --resend message.txt
```

## 6. Useful Logs

| File | Purpose |
|------|---------|
| `logs/errors.log` | pipeline/runtime failures |
| `logs/failed_*` | preserved failure artifacts |
| `.aura/kanban/latest` | active task state |

---
*Last updated: 2026-03-05*
