# AI Agents — `ct-cognize`

> Purpose: runtime behavior of cognitive analysis stage (`ct-cognize`)
> Updated: 2026-04-07
> Source of Truth: `tools/ct-cognize/agent-config.json`

Related card:
- [13-ct-cognize.md](13-ct-cognize.md) for the full stage-level flow
- [14-codex-proxy.md](14-codex-proxy.md) for manual headless `codex` / `codex review` runs through the local proxy

Manual operator note:

- manual `codex_wp review` / `codex_wp exec` workflows still live in [14-codex-proxy.md](14-codex-proxy.md)
- `ct-cognize` may also use `codex_wp` as an optional fallback candidate when it is enabled in `tools/ct-cognize/agent-config.json`

## Enabled Agents

| Agent | CLI | Mode | Timeout | Preflight | Notes |
|------|-----|------|---------|-----------|-------|
| qwen | `qwen` | cwd | 600s | `-p` | file-reading in workdir |
| pi | `pi` | @file | 600s | `--no-session --provider zai --model glm-5-turbo --thinking off --no-tools -p` | deterministic fallback path; runtime pinned to `--provider zai --model glm-5-turbo` |
| claude | `claude` | cwd | 600s | `-p --model MiniMax-M2.5 --no-session-persistence` | alternative general-purpose agent; runtime uses `--permission-mode bypassPermissions` |
| qodercli | `qodercli` | cwd | 600s | `-q -p` | Qoder non-interactive prompt mode in the temp workdir |
| kimi_wp | `kimi_wp` | cwd | 600s | `-s read-only -p` | Qoder wrapper pinned to Kimi K2.5 with read-only tools |
| codex_wp | `codex_wp` | headless exec | 600s | `exec --skip-git-repo-check "1+2=? ..."` | proxy-backed Codex wrapper using the temp workdir as execution root |

`ct-cognize --list-agents` shows only enabled agents.

## Disabled Agents

| Agent | Status | Reason |
|------|--------|--------|
| kimi | disabled | Consistently fails with 402 membership error |
| gemini | disabled | Consistently fails with EACCES permission error |

## Selection Policy

- `--agent auto` (default):
  - parallel preflight checks ALL configured agents simultaneously;
  - agents race to satisfy their configured health probe (`ok` for most CLIs, `three` for `codex_wp`);
  - runtime fallback order follows the first-ready agents discovered at preflight;
  - if all agents fail, the command exits with agent failure (no silent dry-run fallback).
- `--agent <name>`:
  - strict single-agent mode (no fallback).
- `--agents a,b,c`:
  - user-defined ordered fallback chain.

## Preflight Behavior

Agents run preflight in parallel using their configured probe prompt.
Most CLIs use `"Ответь одним словом: ok"`, while `codex_wp` uses a simple `1+2=?` harness.

Preflight timeout defaults to 45s per agent, with per-agent overrides allowed in config. First responders become primary candidates.

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
./ct-cognize --input scheduled.json --taste taste/profile.yaml --agents pi,codex_wp,qodercli
```

## Diagnostics Controls

- `--trace-id <id>`: tag all stderr diagnostics
- `--timings`: print stage timings to stderr
- `--quiet`: suppress non-error diagnostics
- `--verbose`: richer diagnostics

Diagnostics never contaminate JSON payload on stdout.
