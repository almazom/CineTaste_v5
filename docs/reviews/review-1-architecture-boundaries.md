# Independent Architecture/Boundaries Review — CineTaste v5

## 1) Executive Summary
The architecture direction is strong and coherent (Markdown-centered orchestration, contract-first boundaries, CLI isolation). The current problem is not architecture intent, but **boundary drift across control documents**.

The most serious drift is around runtime mode semantics: some documents still imply preview behavior (`--dry-run`), while runtime architecture documents assert “always send”. This is a side-effect boundary issue and must be resolved first.

Second-order drift exists in agent policy and legacy tool ownership (`ct-analyze` vs `ct-cognize`), which weakens determinism and reviewability.

## 2) What is missing (architecture-level)
1. **Explicit runtime mode contract (side effects policy).**
The system lacks one authoritative statement describing which modes exist, which steps execute per mode, and whether Telegram sending is allowed.

2. **Explicit agent policy SSOT section (runtime + fallback + failure semantics).**
Agent strategy is not owned in one place. Current docs mix old and new chains.

3. **Legacy lifecycle boundary for tools.**
`ct-analyze` is marked legacy, but boundary ownership (supported scope, sunset criteria, allowed producers) is not formalized.

4. **Publication parity contract (`golden-standard.md` vs `golden-standard.html`).**
There is no rule that generated/published HTML must be semantically equivalent to markdown source.

5. **Failure artifact contract.**
Self-healing is described operationally, but no formal schema exists for failure output consumed by humans/tools.

6. **Cross-file synchronization invariants.**
No declared invariants enforce alignment for version and behavior across `AURA.md`, `PROTOCOL.json`, and `FLOW.md`.

## 3) Inconsistencies or ambiguous boundaries
1. **Mode boundary conflict (`--dry-run` vs always-send).**
- `AURA.md` still prescribes `./run --dry-run` as preview (`AURA.md:111`, `AURA.md:206`).
- `PROTOCOL.json` defines only `production` and `resend` modes (`PROTOCOL.json:158-167`).
- `FLOW.md` says Step 6 is mandatory and pipeline always sends (`FLOW.md:49`, `FLOW.md:140`).
Impact: side-effects are not predictably controlled by architecture documents.

2. **Agent policy conflict (old chain vs current chain).**
- `AURA.md` states `kimi -> pi -> dry_run` (`AURA.md:122`) and old adapter API (`AURA.md:141-148`).
- `PROTOCOL.json` v5.4 notes `gemini` and `qwen` added and no silent dry-run fallback (`PROTOCOL.json:202-205`).
Impact: cognitive boundary is ambiguous; test and failure expectations are unstable.

3. **Legacy ownership ambiguity (`ct-analyze` still appears as active boundary participant).**
- `PROTOCOL.json` marks `ct-analyze` legacy (`PROTOCOL.json:100-110`) but contracts still list both producers/consumers (`PROTOCOL.json:47`, `PROTOCOL.json:53`).
- `FLOW.md` runs only `ct-cognize` (`FLOW.md:86-99`).
- `AURA.md` test structure still centers `test_ct_analyze.py` (`AURA.md:79`).
Impact: unclear compatibility surface; reviewers cannot tell what must still be preserved.

4. **Golden Standard source parity drift.**
- Markdown has Principle E “Aura as Runtime Discipline” and Principle F “Replaceability” (`golden-standard.md:93-116`).
- HTML omits the Aura principle and renumbers replaceability as E (`golden-standard.html:188-190`).
Impact: two architectural doctrines exist depending on rendering.

5. **Flow versioning principle is declared but not operationalized as invariant.**
- Standard requires versioned flow changes (`golden-standard.md:33-37`).
- Protocol points to `flows/latest/FLOW.md` (`PROTOCOL.json:156`) but does not require immutable path concordance check.
Impact: no machine-checkable guard against silent drift.

## 4) Concrete proposed additions (ready-to-paste lines/sections)
### A) Add runtime mode contract to `PROTOCOL.json` (`flow` section)
```json
"flow": {
  "current_version": "1.3.0",
  "file": "flows/latest/FLOW.md",
  "stages": ["ct-fetch", "ct-schedule", "ct-cognize", "ct-filter", "ct-format", "t2me"],
  "mode_contract": {
    "authoritative_owner": "PROTOCOL.json",
    "default_mode": "production",
    "modes": {
      "production": {
        "flags": [],
        "steps": [1, 2, 3, 4, 5, 6],
        "telegram_send": true
      },
      "resend": {
        "flags": ["--resend", "<file>"],
        "steps": [6],
        "telegram_send": true
      }
    }
  }
}
```

### B) Add explicit legacy boundary policy to `PROTOCOL.json`
```json
"lifecycle": {
  "legacy_tools": {
    "ct-analyze": {
      "allowed_in_active_flow": false,
      "contract_compat_role": "legacy producer/consumer for migration only",
      "must_have_tests": true,
      "deletion_policy": "remove only after contract consumers/producers no longer reference it"
    }
  }
}
```

### C) Replace stale agent section in `AURA.md` with v5.4-compatible boundary statement
```md
### 5.1 Agent Policy (Aligned with PROTOCOL v5.4.0)

Authoritative runtime agent policy lives in `PROTOCOL.json` and tool manifests.
AURA must not define an alternate fallback chain.

Current production rule:
- `ct-cognize --agent auto` uses runtime-selected available agents.
- If all agents fail, pipeline fails (no implicit `dry_run` fallback).
```

### D) Add mode clarity block to `FLOW.md` (near CLI options)
```md
## Runtime Mode Contract

- `./run` = production mode (steps 1-6, Telegram send is mandatory).
- `./run --resend <file>` = resend mode (send existing message).
- `--dry-run` is not a supported orchestrator mode in flow v1.3.0.

If mode semantics change, update `PROTOCOL.json` first, then bump flow version.
```

### E) Add publication parity principle to `docs/golden-standard.md`
```md
### Principle G: Publication Parity Is Mandatory

`docs/golden-standard.md` is the normative source.
`docs/golden-standard.html` is a rendered artifact and must be semantically equivalent.
No principle/requirement may exist in one and be absent in the other.
```

### F) Add failure artifact boundary to contracts/protocol
```json
"failure-report": {
  "file": "contracts/failure-report.schema.json",
  "version": "1.0.0",
  "description": "Structured orchestrator failure artifact",
  "produced_by": ["run-orchestrator"],
  "consumed_by": ["humans", "postmortem-tools"]
}
```

## 5) Priorities (High/Medium/Low) and rationale
- **High:** Resolve runtime mode boundary conflict (`--dry-run` vs mandatory send).
Rationale: this is a side-effect safety issue; architecture currently cannot guarantee send behavior from docs alone.

- **High:** Align agent policy across AURA/PROTOCOL/FLOW and remove stale fallback assumptions.
Rationale: cognitive stage is central and highest-variance; drift here breaks reproducibility.

- **High:** Formalize `ct-analyze` legacy lifecycle boundary.
Rationale: mixed legacy/active ownership causes accidental dependency preservation or accidental removal.

- **Medium:** Enforce golden-standard source parity (`.md` vs `.html`).
Rationale: doctrine split causes review disagreement and onboarding mistakes.

- **Medium:** Add failure-report contract.
Rationale: improves deterministic incident handling and toolability, but does not block core runtime immediately.

- **Low:** Add explicit cross-file sync invariants (version/mode coherence checks).
Rationale: important governance improvement, but lower immediate risk than side-effect and agent ambiguity.

## 6) Keep/safeguard list (what should not be changed)
1. Keep `PROTOCOL.json` as architecture SSOT.
2. Keep executable `FLOW.md` model and versioned flow directories with `flows/latest` pointer.
3. Keep contract-first development order and manifest-driven CLI boundaries.
4. Keep strict CLI isolation (one tool, one responsibility) and stateless-by-default tool design.
5. Keep explicit send path via pipe to `t2me send --markdown` (this boundary is already clear and correct).
6. Keep architecture-first review culture from `PROFILE.md` (reproducibility over feature speed).
