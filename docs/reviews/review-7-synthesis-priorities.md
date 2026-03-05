# Synthesis Action Report — Prioritized

## 1) Synthesis Executive Summary
Six reports converge on one core issue: the architecture vision is strong, but enforcement and synchronization are weak. The highest-risk failures are control-plane drift (docs disagree on runtime truth), active-stage drift (`ct-cognize` runtime vs legacy `ct-analyze` guidance/tests), and missing hard gates for contracts, CLI behavior, and reliability thresholds.

Most urgent work is not new features. It is making boundaries executable: one authoritative runtime contract, mandatory consistency checks, strict input/exit-code semantics, and active-flow reliability gates. Once these are in place, documentation UX and typography improvements can safely follow.

## 2) Overlap map: recurring findings across multiple experts
| Recurring finding | Experts | Agreement strength | Why it matters |
|---|---|---|---|
| Cross-document drift (AURA/PROTOCOL/FLOW/README/Golden Standard not fully aligned) | 1, 3, 4, 6 | Very high | Creates contradictory operator behavior and review disputes |
| Active vs legacy stage mismatch (`ct-cognize` runtime, `ct-analyze` leftovers in docs/tests) | 1, 2, 4, 5, 6 | Very high | Test coverage and policy target the wrong component |
| Governance rules exist but are not mechanized into blockers | 2, 3, 5 | High | Drift reaches merge/runtime undetected |
| Contract and CLI boundary enforcement is incomplete | 1, 2, 5 | High | Invalid input or ambiguous failures propagate across stages |
| Reliability evidence model is insufficient (coverage gaps, missing E2E and artifacts) | 2, 5 | Medium-high | No strong proof that active flow is safe and repeatable |
| AgentOps quality controls are underspecified | 1, 4 | Medium | Stage-3 semantic errors can pass schema checks |
| Publication/readability drift (`golden-standard.md` vs `.html`, task-first UX gaps) | 1, 6 | Medium | Doctrine differs by format and onboarding slows down |

## 3) High-priority changes (must implement now)
1. **Unify runtime truth and remove contradictions**
- Declare one mode contract and side-effect policy (production/resend, send semantics, dry-run status).
- Remove stale chains and legacy stage wording where runtime already uses `ct-cognize`.
- Acceptance: no conflicting runtime statements across AURA/PROTOCOL/FLOW/README.

2. **Add hard governance gate (CI + pre-run)**
- Implement a mandatory consistency check: stage order, tool status (active/legacy), contract bindings, and version alignment.
- Run it both in CI and before `./run`.
- Acceptance: merge/run blocked on mismatch.

3. **Enforce strict CLI/API boundary behavior in active flow**
- Require entrypoint input contract enforcement for tools with declared input contracts (`ct-cognize` first).
- Normalize exit taxonomy (`2` invalid args/path, `4` parse/contract, `3` dependency failure, `1` unexpected).
- Acceptance: malformed input fails fast with deterministic exit codes.

4. **Restore reliability gates for the active pipeline**
- Enforce coverage target (80% total) and minimum coverage for active cognitive stage.
- Add mandatory active-flow E2E verification in safe non-send mode.
- Acceptance: release blocked when coverage or E2E gate fails.

5. **Harden critical delivery contracts now**
- Add conditional invariants to `send-confirmation` (success requires `message_id`, failure requires `error`).
- Acceptance: invalid success/failure payloads fail schema validation.

## 4) Medium-priority changes (next iteration)
1. Add bounded multi-agent review loop policy for stage 3 (disagreement thresholds, max passes, escalation).
2. Constrain `filter-result.meta.thresholds` domain (`recommendations` enum, `min_score` range).
3. Add manifest schema governance and manifest-runtime sync checks.
4. Standardize reliability artifacts (`run_id`, `step_metrics.json`, replayable failure bundle).
5. Add canonical severity taxonomy (P0-P4) for triage and release decisions.
6. Add deprecation lifecycle policy (`active -> deprecated -> blocked -> removed`) with owner/date.

## 5) Low-priority or optional changes (can defer)
1. HTML readability refinements: text measure, heading style tuning, print stylesheet.
2. Sticky/collapsible in-page ToC and additional navigational scaffolding.
3. Golden Standard glossary and expanded editorial examples.
4. Flakiness trend dashboard and artifact retention/TTL policy.
5. Non-critical prose/verbosity polish for agent reasoning output.

## 6) Minimal safe update set for current cycle (smallest set with highest impact)
1. **Control-plane sync patch**
- Align all runtime references to current active chain and mode semantics; remove contradictory dry-run assumptions.

2. **Single governance-check script (blocking)**
- Start with four checks only: stage order sync, active-tool sync, contract mapping sync, version sync.

3. **`ct-cognize` boundary hardening**
- Enforce input contract at entrypoint and apply strict exit-code mapping.

4. **One active-flow safe E2E gate + coverage block**
- Add one deterministic fixture-driven E2E non-send run and enforce 80% total coverage.

5. **`send-confirmation` conditional schema fix**
- Prevent ambiguous delivery success/failure payloads.

## 7) Exact patch intent for MD and HTML (bullet list by section)
### `docs/golden-standard.md` patch intent
- **Header metadata block**: add explicit `Last verified against PROTOCOL/FLOW` date field.
- **Section 2: Principles**: insert missing publication parity principle (`.md` is normative, `.html` must be semantically equivalent).
- **Section 3: Boundary Model**: add one-line canonical conflict rule (PROFILE=why, AURA=process, PROTOCOL=topology, FLOW=runtime).
- **Section 4: Operational Change Model**: add mandatory governance-check gate before merge and before runtime execution.
- **Section 6: Definition of Done**: include active-flow E2E pass + coverage threshold + artifact evidence requirement.
- **Section 7: Anti-Patterns**: add two anti-patterns: stale legacy stage guidance and contradictory mode semantics across control docs.
- **New appendix section**: add severity taxonomy P0-P4 for failure triage.

### `docs/golden-standard.html` patch intent
- **Head/metadata area**: mirror markdown metadata including `Last verified` and version alignment note.
- **Mission section**: keep content aligned with markdown wording updates (no doctrine-only divergence).
- **Principles section**: add the missing principle currently absent in HTML so principle count/order matches markdown.
- **Boundary Model section**: add the same canonical conflict rule text as markdown.
- **Definition of Done section**: mirror added reliability/governance evidence requirements.
- **Anti-Patterns section**: mirror the two newly added anti-patterns.
- **Navigation/UI structure**: add anchors/ToC only if section IDs exactly map to markdown headings; do not add extra normative content in HTML-only form.
- **Publication rule enforcement note**: add explicit footer note that HTML is a rendered artifact and must remain semantically equivalent to markdown.
