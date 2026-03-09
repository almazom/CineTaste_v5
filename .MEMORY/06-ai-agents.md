# AI Agents — `ct-cognize`

> Purpose: runtime behavior of cognitive analysis stage (`ct-cognize`)
> Updated: 2026-03-05

## Active Agents

| Agent | CLI | Mode | Notes |
|------|-----|------|-------|
| kimi | `kimi` | stdin | strongest for unknown movies / web search |
| gemini | `gemini` | cwd | file-reading in workdir |
| qwen | `qwen` | cwd | file-reading in workdir |
| pi | `pi` | @file | deterministic fallback path |

## Selection Policy

- `--agent auto` (default):
  - parallel preflight checks the configured agents for readiness;
  - runtime fallback order follows the first-ready agents discovered at preflight;
  - if all agents fail, the command exits with agent failure (no silent dry-run fallback).
- `--agent <name>`:
  - strict single-agent mode.
- `--agents a,b,c`:
  - user-defined ordered fallback chain.

## Contract Gate

`ct-cognize` validates `movie-schedule@1.0.0` input before any preflight/agent call.
Invalid payloads fail fast with contract error exit code.

## Non-Interactive Runtime Semantics

Agent subprocesses run with CI-safe defaults:

- `CI=1`
- `NO_COLOR=1`
- `TERM=dumb`

This prevents interactive UI output in automation pipelines.

## Quick Commands

```bash
# Supported agents
ct-cognize --list-agents

# Version
ct-cognize --version

# Stdin mode
cat scheduled.json | ct-cognize --input - --taste taste/profile.yaml

# Explicit chain
ct-cognize --input scheduled.json --taste taste/profile.yaml --agents pi,qwen,gemini
```

## Diagnostics Controls

- `--trace-id <id>`: tag all stderr diagnostics
- `--timings`: print stage timings to stderr
- `--quiet`: suppress non-error diagnostics
- `--verbose`: richer diagnostics

Diagnostics never contaminate JSON payload on stdout.

