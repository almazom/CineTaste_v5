# CineTaste — Project Profile

## Project Size: **M** (Medium)

| Metric | Count |
|--------|-------|
| Python files | ~30 |
| JSON schemas | ~42 |
| Markdown docs | ~30 |
| Total LOC (Python) | ~1,400 |
| CLI tools | 6 |
| Contracts | 5 |

---

## User Scope: **Single User**

This is a **personal** movie recommendation system, not an enterprise application.

| Aspect | CineTaste | Enterprise |
|--------|-----------|------------|
| **Users** | 1 (default) | Multi-tenant |
| **Auth** | None | OAuth, SSO |
| **Database** | File-based (YAML/JSON) | PostgreSQL, Redis |
| **Deployment** | Local CLI | Kubernetes, Docker |
| **API** | None | REST, GraphQL |
| **Scale** | Daily batch | Real-time streaming |

---

## Architecture Style

**Pipeline-based CLI** with contract-first design:

```
PROTOCOL.json (SSOT)
       │
       ├── contracts/  ── JSON Schema boundaries
       ├── tools/      ── CLI microservices
       └── flows/      ── Pipeline versions
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Language** | Python 3 |
| **Testing** | pytest |
| **Contracts** | JSON Schema |
| **Config** | YAML |
| **Output** | Telegram (via t2me CLI) |
| **AI Agents** | kimi, pi (via aura) |

---

## Pipeline Stages

```
ct-fetch → ct-schedule → ct-analyze → ct-filter → ct-format → t2me
   │            │             │           │           │        │
   ▼            ▼             ▼           ▼           ▼        ▼
 movies     scheduled      analyzed    filtered    message   Telegram
```

---

## Key Design Principles

1. **Simple > Easy** — Artifact simplicity over authoring convenience
2. **Uncomplect** — One responsibility per tool
3. **Contract-first** — Define schema before code
4. **Stateless** — Pure functions, effects at boundaries
5. **MVS** — Minimum Viable Solution

---

## Version

**v5.3.0** — AI-powered cinema recommendations delivered to Telegram
