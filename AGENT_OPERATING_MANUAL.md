# 🤖 AGENT OPERATING MANUAL — CineTaste v5 Blueprint
## Practical Engineering for AI Orchestrators

> **"If I can't explain it simply, I don't understand it."**
> This document is the "Memento" for agents. Use it to build, maintain, and scale CineTaste-like systems.

---

## 🏛️ 1. The Upside-Down Architecture

In standard projects, code is the center. In CineTaste, **Documentation is the Runtime**.
The system is built from the outside in: **Contract → Protocol → Tool → Flow**.

### 🔍 The Core Triad
1.  **PROFILE.md (The WHY):** The Intent. Defines what we are *actually* trying to achieve (e.g., "validate a hypothesis", not "build a product"). If an AI agent doesn't know *why*, it will over-engineer.
2.  **AURA.md (The HOW):** The Protocol. Strict directives for the agent. This is your "System Prompt" on a per-project basis. It defines the Kanban flow, the development order, and the testing mandatory.
3.  **PROTOCOL.json (The WHAT):** The Topology. The Single Source of Truth (SSOT). Every tool, every contract, every stage is mapped here. If it's not in the Protocol, it doesn't exist.

---

## 🏗️ 2. The Station Pattern (Modular CLIs)

The pipeline is not a monolithic script. It is a series of **Stations**.
Each station is a dedicated CLI tool in the `tools/` directory.

### 🧩 Anatomy of a Station (e.g., `ct-fetch`)
-   **MANIFEST.json:** The tool's "Identity Card". Defines its verb, its position, and its I/O contracts.
-   **Isolated Responsibility:** One tool does ONE thing (e.g., `ct-fetch` only fetches; it doesn't filter).
-   **Statelessness:** Tools take input (stdin/args) and produce output (stdout/files). No shared mutable state.
-   **Adapters:** If a tool interacts with the outside world (e.g., scraping a website or calling an AI), it uses an internal adapter to map the messy outside world into a clean **Contract**.

---

## 📜 3. Contract-First Development

**Never write code before you write the schema.**

1.  Define the **JSON Schema** in `contracts/`.
2.  Add the contract to `PROTOCOL.json`.
3.  Point the tool's `MANIFEST.json` to the contract.
4.  Implement the tool.
5.  **Validate:** The tool MUST fail if the output doesn't match the schema.

---

## 🌊 4. FLOW.md — The Executable Specification

`FLOW.md` is not just a description; it's the **Pipeline Definition**.
The `run` script parses the bash blocks in `FLOW.md` and executes them.

-   **Step-by-Step:** Each step has a header, a contract, and an output path.
-   **Dry Run Support:** Every step must support a `--dry-run` or equivalent validation mode.
-   **Self-Healing:** If Step 3 fails, the pipeline halts, preserves the state in `logs/failed_<timestamp>`, and tells you how to recover.

---

## 🧠 5. The "Memento" Memory Bank (`.MEMORY/`)

Agents have short-term memory. The `.MEMORY/` folder is your long-term storage.

-   **Context Cards:** Each card (e.g., `01-architecture.md`, `10-ct-fetch.md`) stores "hard-won" knowledge.
-   **Index-First:** Always read `.MEMORY/00-index.md` first.
-   **Write as you Learn:** When you fix a bug or learn a site's quirk, write it to a memory card. This is the "Memento" tattoo for the next session.

---

## 🚀 6. The 7-Step Development Loop for Agents

1.  **READ** `PROTOCOL.json` to understand the topology.
2.  **READ** `AURA.md` to see the "Rules of Engagement".
3.  **CREATE** a Kanban card in `.aura/kanban/`.
4.  **DEFINE** the contract in `contracts/`.
5.  **REGISTER** the tool in `PROTOCOL.json` and its `MANIFEST.json`.
6.  **IMPLEMENT** the tool logic with an adapter.
7.  **VERIFY** using `pytest` and `./run --dry-run`.

---

## ⚠️ 7. Agent Preflight & Fallbacks

When using AI agents within the pipeline (`ct-cognize`):
-   **Preflight:** Always check if the agent is "alive" before sending a 100KB payload.
-   **Chain of Fallbacks:** If `Kimi` fails (network), fallback to `Gemini`. If `Gemini` fails (safety), fallback to `Pi`. If all fail, **ABORT** the pipeline. Never send empty/broken data to the next station.

---

*“Simplicity is the ultimate sophistication. Keep the tools small, the contracts strict, and the memory sharp.”*
