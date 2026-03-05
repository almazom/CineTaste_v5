# CineTaste — Project Profile

## Project Intent

CineTaste is an **internal R&D project**.

Primary goal is **not** to optimize a mass-user product.
Primary goal is to validate hypotheses and build a **gold standard architecture** for AI-assisted development based on:

1. **Markdown-driven orchestration** (Markdown file is the center of execution)
2. **Isolated CLI wrappers** (one tool = one responsibility)
3. **Strict contracts, protocols, conventions, and explicit APIs**

End-user utility exists, but it is secondary to architectural learning and reproducible engineering practice.

---

## Usage Model

| Dimension | Profile |
|-----------|---------|
| **Audience** | Internal use |
| **Operator model** | Single user / single maintainer |
| **Scale** | Daily batch pipeline, low throughput |
| **Product type** | Experimental architecture sandbox |
| **Enterprise scope** | Out of scope by default (multi-tenant, 10K rps, SSO, distributed infra) |

---

## Core Architectural Thesis

The system is intentionally **Markdown-centric**:

- Markdown defines orchestration behavior.
- CLI tools execute isolated responsibilities.
- Contracts define machine-checkable boundaries.
- Protocols and conventions define expected behavior before implementation.

In this project, environment discipline is not supporting context; it is the core product value.

---

## Development Order (Mandatory)

All substantial changes should follow this order:

1. **Conventions / Protocols** (`AURA.md`, `PROTOCOL.json`, execution rules)
2. **Contracts** (`contracts/*.schema.json`)
3. **Tool API specs** (`tools/*/MANIFEST.json`)
4. **Flow spec** (`flows/latest/FLOW.md`)
5. **Implementation** (tool code)
6. **Verification** (tests + schema validation + runnable flow)

---

## Review Expectations (Human + LLM)

Evaluate changes by architectural quality first:

1. Does this strengthen Markdown-centered orchestration?
2. Does this keep CLI tools isolated and composable?
3. Are contracts/protocols explicit, versioned, and enforceable?
4. Is behavior deterministic enough to debug and reproduce?
5. Does this avoid unnecessary enterprise complexity?

Prefer explicit, protocol-visible decisions over hidden “smart” behavior.

---

## Value Priorities

For this project, priority is:

1. **Architectural clarity and reproducibility**
2. **Contract/protocol integrity**
3. **Reviewability and verification discipline**
4. **Feature output speed**

If there is a conflict, preserve architecture and protocol integrity first.

---

## Constraints

| Constraint | Implication |
|------------|-------------|
| **Time** | Iterative progress; keep pipeline runnable at every stage |
| **Budget** | Local CLI-first approach; avoid costly platform complexity |
| **Architecture** | Markdown center + isolated CLIs + strict schemas/protocols |
| **Quality gate** | No change is “done” without contract and flow-level verification |

---

## Current Runtime Snapshot

- **SSOT:** `PROTOCOL.json`
- **Flow:** `ct-fetch -> ct-schedule -> ct-cognize -> ct-filter -> ct-format -> t2me`
- **Paradigm:** Contract-first, Markdown-driven orchestration

---

## Version

**v5.4.0**
