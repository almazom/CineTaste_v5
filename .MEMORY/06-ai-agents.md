# 06-ai-agents.md — AI Agent Usage for CineTaste

> **Purpose:** Guide for using kimi and pi CLI agents in ct-analyze
> **Updated:** 2026-03-02

---

## Quick Reference

| Agent | Status | Best For | Command |
|-------|--------|----------|---------|
| **kimi** | ✅ Active | Web search, research | `kimi -p "prompt" --print --final-message-only --thinking` |
| **pi** | ✅ Active | LLM reasoning, no web | `pi -p "prompt" --no-tools --thinking high` |

---

## kimi CLI — Primary Agent (Web Search!)

### Status: ✅ WORKING
```bash
# Preflight test
kimi -p "1+2=...[ONLY NUMBER IN WORDS]" --print --final-message-only
# Output: three ✓
```

### Recommended Command
```bash
kimi -p "PROMPT" --print --final-message-only --thinking
```

### Key Flags for CineTaste

| Flag | Purpose | Required |
|------|---------|----------|
| `-p` / `--prompt` | Non-interactive prompt | ✅ Yes |
| `--print` | Non-interactive mode | ✅ Yes |
| `--final-message-only` | Clean output (no UI) | ✅ Yes |
| `--thinking` | Better reasoning | ⚠️ Recommended |

### Example: Movie Analysis
```bash
kimi -p "Analyze these movies and research them online: [list]. Return JSON." --print --final-message-only --thinking
```

### Strengths
- **Web search capabilities** — can research unknown movies
- Better for films not in training data
- Can fetch ratings/reviews
- Good reasoning with `--thinking`

### Weaknesses
- Slower than pi (30-60s)
- May timeout on large batches
- CLI changed from v4 expectations

---

## pi CLI — Fallback Agent

### Recommended Command
```bash
pi -p "PROMPT" --no-tools --thinking high
```

### Key Flags

| Flag | Purpose | Required |
|------|---------|----------|
| `-p` / `--print` | Non-interactive mode | ✅ Yes |
| `--no-tools` | Disable file tools (safety) | ✅ Yes |
| `--thinking high` | Better reasoning quality | ⚠️ Recommended |

### Strengths
- Fast response (10-30s)
- Reliable CLI interface
- Good JSON extraction

### Weaknesses
- **No web search** — can't research movies
- May hallucinate movie details

---

## Agent Priority for v5

```python
AGENTS = [
    {"name": "kimi", "cmd": "kimi", "args": ["--print", "--final-message-only", "--thinking"], "uses_stdin": True},
    {"name": "pi", "cmd": "pi", "args": ["--print", "--no-tools", "--thinking", "high"], "uses_stdin": True},
]
```

### Fallback Chain
```
kimi (web search) → pi (fast reasoning) → dry_run (mock)
```

---

## Preflight Check

```bash
# Test kimi
kimi -p "1+2=...[ONLY NUMBER IN WORDS]" --print --final-message-only
# Expected: three ✓

# Test pi
pi -p "1+2=...[ONLY NUMBER IN WORDS]" --no-tools
# Expected: three ✓
```

---

## Related Files
- `tools/ct-analyze/adapter_pi.py` — current adapter (needs kimi support)
- `taste/profile.yaml` — taste data passed to agent
