# Agent Preflight Configuration

> Purpose: Centralized configuration for AI agent preflight behavior
> Updated: 2026-04-07
> Source of Truth: `tools/ct-cognize/agent-config.json`

## Overview

The preflight system runs parallel health checks on all configured AI agents before analysis. Agents race to respond first; the fastest available agents become the primary execution chain.

## Configuration File

All preflight "magic numbers" and command arguments live in:
```
tools/ct-cognize/agent-config.json
```

This file defines:
- Agent names and CLI commands
- Preflight command arguments
- Runtime command arguments
- Timeouts (preflight and runtime)
- File modes (how agents read input files)
- Capabilities (web search support)

## Agent Specifications

### kimi
- **CLI**: `kimi`
- **Mode**: `stdin` (prompt + data via stdin)
- **Preflight**: `--print --final-message-only -p`
- **Runtime**: `--print --final-message-only --thinking`
- **Timeouts**: 45s preflight / 600s runtime
- **Special**: Only agent with web search capability
- **Use case**: Best for unknown movies requiring external research

### gemini
- **CLI**: `gemini`
- **Mode**: `cwd` (reads files from working directory)
- **Preflight**: `-p`
- **Runtime**: `--approval-mode yolo`
- **Timeouts**: 45s preflight / 600s runtime
- **Special**: File-reading via agent's own tools
- **Use case**: General-purpose analysis

### qwen
- **CLI**: `qwen`
- **Mode**: `cwd` (reads files from working directory)
- **Preflight**: `-p`
- **Runtime**: `--approval-mode yolo`
- **Timeouts**: 45s preflight / 600s runtime
- **Special**: File-reading via agent's own tools
- **Use case**: General-purpose analysis, often fastest

### pi
- **CLI**: `pi`
- **Mode**: `at_file` (@file syntax to inject content)
- **Preflight**: `--no-session --provider zai --model glm-5-turbo --thinking off --no-tools -p`
- **Runtime**: `--print --no-tools --thinking high --provider zai --model glm-5-turbo`
- **Timeouts**: 45s preflight / 600s runtime
- **Special**: Deterministic, no-tools mode; as of 2026-04-07 `glm-5-turbo` beat `glm-5` and `glm-5.1` on the local one-token harness
- **Use case**: Reliable fallback, consistent behavior

### claude
- **CLI**: `claude`
- **Mode**: `cwd` (reads files from working directory)
- **Preflight**: `-p --model MiniMax-M2.5 --no-session-persistence`
- **Runtime**: `--permission-mode bypassPermissions --model MiniMax-M2.5 --no-session-persistence`
- **Timeouts**: 45s preflight / 600s runtime
- **Special**: Uses MiniMax-M2.5 model
- **Use case**: Alternative general-purpose agent

Claude Code `2.1.72` does not expose `--approval-mode`; the supported non-interactive flag is `--permission-mode`.

### qodercli
- **CLI**: `qodercli`
- **Mode**: `cwd` (reads files from working directory)
- **Preflight**: `-q -p`
- **Runtime**: `-q --dangerously-skip-permissions`
- **Timeouts**: 45s preflight / 600s runtime
- **Special**: non-interactive Qoder harness; model selection stays on the CLI default unless explicitly changed in config
- **Use case**: extra general-purpose fallback when qwen/pi/claude are unavailable

### kimi_wp
- **CLI**: `kimi_wp`
- **Mode**: `cwd` (reads files from working directory)
- **Preflight**: `-s read-only -p`
- **Runtime**: `-s read-only`
- **Timeouts**: 45s preflight / 600s runtime
- **Special**: wrapper locked to Kimi K2.5; read-only by default
- **Use case**: Kimi-backed fallback without direct kimi CLI integration

### codex_wp
- **CLI**: `codex_wp`
- **Mode**: `headless exec` (runs `codex_wp exec` in the temp workdir)
- **Preflight**: `exec --skip-git-repo-check "1+2=? Reply with exactly one token: three"`
- **Runtime**: `exec --skip-git-repo-check "<analysis prompt>"`
- **Timeouts**: 90s preflight / 600s runtime
- **Special**: auto-boots the local proxy and runs headless Codex without requiring the temp workdir to be a Git repo
- **Use case**: deep fallback when the other configured CLIs are down but proxy-backed Codex is still healthy

## Preflight Prompt

Default preflight prompt for most agents:
```
Ответь одним словом: ok
```

Default success tokens: `ok`, `ок` (Cyrillic variant)

Agent-specific override:
- `codex_wp` uses `1+2=? Reply with exactly one token: three`
- accepted success tokens: `three`, `3`

## Timeout Strategy

| Phase | Timeout | Rationale |
|-------|---------|-----------|
| Preflight | 45s by default | Long enough for slow APIs, short enough to fail fast; individual agents can override |
| Runtime | 600s | 10 minutes allows analysis of 20+ movies |
| Pipeline | 720s | Default in `./run`, configurable via `--timeout` |

## Fallback Chain

Default behavior (`--agent auto`):
1. All agents run preflight in parallel
2. Results ordered by completion time (fastest first)
3. Runtime uses first available agent
4. On failure, falls back to next available agent
5. If all fail, exits with agent error

## Environment Variables

Optional overrides via `.env` or environment:

```bash
# Agent timeouts (seconds)
CT_COGNIZE_PREFLIGHT_TIMEOUT=45
CT_COGNIZE_RUNTIME_TIMEOUT=600

# Pipeline timeout
CT_PIPELINE_TIMEOUT=720

# Agent selection
CT_COGNIZE_AGENT=auto        # or: pi, qwen, claude, qodercli, kimi_wp, codex_wp
CT_COGNIZE_AGENTS=pi,codex_wp,qodercli
```

## Modifying Configuration

To change agent behavior:

1. **Edit config file**: `tools/ct-cognize/agent-config.json`
2. **Update this card**: Keep documentation in sync
3. **Test preflight**: `./ct-cognize --list-agents --verbose`
4. **Verify pipeline**: `./run --dry-run --verbose`

**Do NOT hardcode changes in** `main.py` - all configuration belongs in the JSON file.

## Quick Reference

```bash
# Test preflight for all agents
./ct-cognize --list-agents --verbose

# Run with specific agent
./ct-cognize --input scheduled.json --taste taste/profile.yaml --agent pi

# Run with fallback chain
./ct-cognize --input scheduled.json --taste taste/profile.yaml --agents pi,codex_wp,qodercli

# Pipeline with extended timeout
./run --timeout 1200
```

## Troubleshooting

**All agents failing preflight:**
- Check network connectivity
- Verify API keys in environment
- Check agent CLI tools are installed and in PATH

**One agent consistently slow:**
- Consider removing from default chain
- Increase preflight timeout in config
- Use `--agents` to specify faster subset

**Runtime timeout:**
- Increase runtime timeout in config
- Reduce movie batch size upstream
- Use agent with faster response time
