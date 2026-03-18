# Agent Preflight Configuration

> Purpose: Centralized configuration for AI agent preflight behavior
> Updated: 2026-03-10
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
- **Preflight**: `--no-session --provider zai --model glm-5 --thinking off --no-tools -p`
- **Runtime**: `--print --no-tools --thinking high --provider zai --model glm-5`
- **Timeouts**: 45s preflight / 600s runtime
- **Special**: Deterministic, no-tools mode
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

## Preflight Prompt

All agents receive the same prompt (in Russian for consistency):
```
Ответь одним словом: ok
```

Expected response tokens: `ok`, `ок` (Cyrillic variant)

## Timeout Strategy

| Phase | Timeout | Rationale |
|-------|---------|-----------|
| Preflight | 45s | Long enough for slow APIs, short enough to fail fast |
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
CT_COGNIZE_AGENT=auto        # or: pi, qwen, gemini, kimi, claude
CT_COGNIZE_AGENTS=pi,qwen    # ordered fallback chain
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
./ct-cognize --input scheduled.json --taste taste/profile.yaml --agents qwen,pi,claude

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
