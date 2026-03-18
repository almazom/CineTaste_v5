# AI Agents — `ct-cognize`

> Purpose: runtime behavior of cognitive analysis stage (`ct-cognize`)
> Updated: 2026-03-18
> Source of Truth: `tools/ct-cognize/agent-config.json`

Related card:
- [13-ct-cognize.md](13-ct-cognize.md) for the full stage-level flow

## Enabled Agents

| Agent | CLI | Mode | Timeout | Preflight | Notes |
|------|-----|------|---------|-----------|-------|
| qwen | `qwen` | cwd | 600s | `-p` | file-reading in workdir |
| pi | `pi` | @file | 600s | `--no-session --provider zai --model glm-5 --thinking off --no-tools -p` | deterministic fallback path; runtime pinned to `--provider zai --model glm-5` |
| claude | `claude` | cwd | 600s | `-p --model MiniMax-M2.5 --no-session-persistence` | alternative general-purpose agent; runtime uses `--permission-mode bypassPermissions` |

`ct-cognize --list-agents` shows only enabled agents.

## Disabled Agents

| Agent | Status | Reason |
|------|--------|--------|
| kimi | disabled | Consistently fails with 402 membership error |
| gemini | disabled | Consistently fails with EACCES permission error |

## Selection Policy

- `--agent auto` (default):
  - parallel preflight checks ALL configured agents simultaneously;
  - agents race to respond first with "ok";
  - runtime fallback order follows the first-ready agents discovered at preflight;
  - if all agents fail, the command exits with agent failure (no silent dry-run fallback).
- `--agent <name>`:
  - strict single-agent mode (no fallback).
- `--agents a,b,c`:
  - user-defined ordered fallback chain.

## Preflight Behavior

All agents run preflight in parallel with prompt: `"Ответь одним словом: ok"`

Preflight timeout: 45s per agent. First responders become primary candidates.

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
./ct-cognize --list-agents

# Version
./ct-cognize --version

# Stdin mode
cat scheduled.json | ./ct-cognize --input - --taste taste/profile.yaml

# Explicit chain
./ct-cognize --input scheduled.json --taste taste/profile.yaml --agents qwen,pi,claude
```

## Diagnostics Controls

- `--trace-id <id>`: tag all stderr diagnostics
- `--timings`: print stage timings to stderr
- `--quiet`: suppress non-error diagnostics
- `--verbose`: richer diagnostics

Diagnostics never contaminate JSON payload on stdout.
