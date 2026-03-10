# Pipeline Run Logging System

> Purpose: Structured artifact and log preservation for every `./run` execution
> Updated: 2026-03-10
> Status: Proposed implementation

## Current State Analysis

### Existing Patterns

**`logs/failed_*`** (on failure only):
- Preserves temp artifacts from failed runs
- Contains: `analyzed.json`, `message.txt`, `failure.txt`, `RECOVER.md`
- Problem: Only on failure, no success history

**`runs/`** (for swarm review flows):
- Complex multi-phase execution tracking
- Over-engineered for simple pipeline runs

**`logs/errors.log`** and **`logs/sends.log`**:
- Append-only text logs
- No structured metadata
- Hard to correlate with specific runs

## Proposed System: `runs/YYYY-MM-DD/` Structure

### Directory Layout

```
runs/
├── latest -> 2026-03-10T065504Z/    # Symlink to most recent
├── 2026-03-10/
│   ├── 2026-03-10T065504Z/          # ISO8601 timestamp
│   │   ├── run.yaml                  # Run metadata (contract)
│   │   ├── run.log                   # Full stdout/stderr
│   │   ├── artifacts/                # All intermediate files
│   │   │   ├── movies.json
│   │   │   ├── scheduled.json
│   │   │   ├── analyzed.json
│   │   │   ├── filtered.json
│   │   │   ├── message.txt
│   │   │   └── send-confirmation.json
│   │   ├── logs/                     # Structured logs
│   │   │   ├── preflight.log         # Agent preflight results
│   │   │   ├── stages.log            # Stage timing and status
│   │   │   └── errors.log            # Errors only (if any)
│   │   └── summary.json              # Quick overview (for listing)
│   │
│   └── 2026-03-10T035504Z/
│       └── ...
│
└── 2026-03-09/
    └── ...
```

### Run Contract (`run.yaml`)

```yaml
run_id: 2026-03-10T065504Z
pipeline_version: 5.4.0
started_at: 2026-03-10T06:55:04Z
completed_at: 2026-03-10T06:57:32Z
status: success  # success | failed | timeout
mode: dry-run  # production | dry-run

# Input parameters
params:
  city: naberezhnie-chelni
  when: now
  timeout: 900
  agent: auto
  input_file: null
  resend_file: null

# Results
results:
  movies_fetched: 17
  movies_scheduled: 17
  movies_analyzed: 17
  movies_matched: 1
  message_lines: 12
  sent: false  # dry-run

# Agent selection
agent_preflight:
  - name: pi
    model: glm-5
    status: ok
    response_time_ms: 7100
  - name: claude
    model: MiniMax-M2.5
    status: ok
    response_time_ms: 9610
  - name: qwen
    status: ok
    response_time_ms: 12290
  - name: kimi
    status: fail
    error: "Error code: 402"
  - name: gemini
    status: fail
    error: "EACCES: permission denied"

agent_selected: pi

# Stage timings
stages:
  - name: ct-fetch
    status: success
    duration_ms: 2340
  - name: ct-schedule
    status: success
    duration_ms: 890
  - name: ct-cognize
    status: success
    duration_ms: 45230
  - name: ct-filter
    status: success
    duration_ms: 120
  - name: ct-format
    status: success
    duration_ms: 340
  - name: t2me
    status: success
    duration_ms: 560

# System info
system:
  hostname: pets-zoo
  user: pets
  python_version: 3.10.12
  node_version: null
```

### Summary JSON (`summary.json`)

```json
{
  "run_id": "2026-03-10T065504Z",
  "status": "success",
  "mode": "dry-run",
  "started_at": "2026-03-10T06:55:04Z",
  "duration_seconds": 148,
  "movies": {
    "fetched": 17,
    "matched": 1
  },
  "agent": "pi",
  "artifacts": [
    "artifacts/movies.json",
    "artifacts/analyzed.json",
    "artifacts/message.txt"
  ]
}
```

## Implementation Plan

### Phase 1: Add Run Logger to `./run`

```bash
# In ./run script, add:
# 1. Create run directory at start
# 2. Tee all output to run.log
# 3. Copy artifacts at each stage
# 4. Write run.yaml on completion
# 5. Update runs/latest symlink
```

### Phase 2: Structured Logging Functions

```bash
log_run_metadata() {
    # Write run.yaml header
}

log_stage_start() {
    # Log stage start with timestamp
}

log_stage_complete() {
    # Log stage completion with duration
}

log_preflight_results() {
    # Capture ct-cognize preflight output
}

preserve_artifacts() {
    # Copy from TMPDIR to runs/<id>/artifacts/
}

finalize_run() {
    # Write run.yaml, summary.json, update symlink
}
```

### Phase 3: Run Listing Command

```bash
# New command: ./run --list
./run --list         # Show recent runs
./run --list --json  # Machine-readable

# Output:
# RUN ID                  STATUS    MODE      MOVIES    AGENT    DURATION
# 2026-03-10T065504Z     success   dry-run   17→1      pi       2m28s
# 2026-03-10T035504Z     success   dry-run   17→1      pi       2m15s
# 2026-03-09T220451Z     failed    prod      17→0      -        1m45s
```

### Phase 4: Rerun From Existing Run

```bash
# Rerun with same parameters
./run --rerun 2026-03-10T065504Z

# Rerun from specific artifact
./run --input runs/2026-03-10/2026-03-10T065504Z/artifacts/analyzed.json
```

## Benefits

1. **Full History**: Every run preserved, not just failures
2. **Debugging**: Compare successful vs failed runs
3. **Performance Tracking**: Stage timings over time
4. **Agent Analytics**: Which agents win preflight races
5. **Audit Trail**: What was sent to Telegram and when
6. **Recovery**: Rerun from any previous state
7. **Metrics**: Success rate, average duration, movie match rate

## Migration

- Keep existing `logs/failed_*` for backward compatibility
- New runs go to `runs/YYYY-MM-DD/` structure
- `logs/errors.log` and `logs/sends.log` continue as summary indexes
