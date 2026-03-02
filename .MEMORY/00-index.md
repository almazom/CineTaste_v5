# 🧠 CineTaste v5 Memory Bank — Index

> **QUICK NAVIGATION** — Start here when returning to this project

## 📋 Bootstrap Sequence

```
1. Read AURA.md (directives)
2. Read PROTOCOL.json (system topology)
3. Read this file (memory index)
4. Read flows/latest/FLOW.md (pipeline)
5. Execute
```

## 📁 Memory Cards

| Card | Topic | When to Read |
|------|-------|--------------|
| [01-architecture.md](01-architecture.md) | System design, patterns | First time / major changes |
| [02-contracts.md](02-contracts.md) | Data contracts, schemas | Working with data flow |
| [03-tools.md](03-tools.md) | CLI tools, manifests | Building/using tools |
| [04-taste.md](04-taste.md) | Taste profile structure | Modifying preferences |
| [05-troubleshooting.md](05-troubleshooting.md) | Common issues | Something broke |
| [06-ai-agents.md](06-ai-agents.md) | pi/kimi CLI usage | Working with ct-analyze |

## 🚀 Quick Start

```bash
# Run full pipeline (production)
./run

# Preview without sending
./run --dry-run

# Resend existing message
./run --resend message.txt
```

## 🎯 Current State

- **Version**: 5.2.0
- **Paradigm**: Contract-first, protocol-driven
- **SSOT**: PROTOCOL.json
- **City**: Набережные Челны (Cinema Park)
- **Status**: 🟢 Architecture remediation in progress (SSOT runtime active)

## 🔑 Key Files

```
PROTOCOL.json      ★ System manifest (SSOT)
AURA.md            ★ Agent directives
contracts/         ★ JSON Schema boundaries
tools/*/MANIFEST.json  ★ Tool specifications
flows/latest/FLOW.md   ★ Pipeline steps
```

## 🏗️ Architecture Summary

```
PROTOCOL.json (SSOT)
       │
       ├── contracts/ ─── defines data shapes
       │
       ├── tools/ ─────── defines CLI interfaces
       │     └── */MANIFEST.json
       │
       └── flows/ ─────── defines execution steps
             └── latest/FLOW.md
```

---
*Last updated: 2026-03-02*
*Version: 5.2.0*
