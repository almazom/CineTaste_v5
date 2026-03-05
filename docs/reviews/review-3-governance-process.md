# 1) Executive Summary
Governance intent is strong, but enforcement is weak. The project clearly defines SSOT (`PROTOCOL.json`), execution discipline (`AURA.md`), architectural intent (`PROFILE.md`), and runtime behavior (`flows/latest/FLOW.md`), yet there are no hard gates that prevent drift between them.

Current process risk is not missing philosophy; it is missing mechanization. The highest priority is to convert process rules into automated checks that fail fast before merge and before `./run`.

# 2) Missing Governance Mechanics
1. No machine gate for cross-document consistency.
Missing: automated validation that `PROTOCOL.flow.stages` equals FLOW step sequence and that each stage has matching contracts.

2. No canonical precedence for conflicts.
`AURA.md` defines source priority, but no explicit conflict-resolution policy exists for contradictory statements across PROFILE/AURA/PROTOCOL/FLOW.

3. No required traceability from plan to change.
KANBAN template has `contract_impact`, but no required `files_changed`, `evidence`, `tests_run`, or `protocol_refs` fields.

4. No state-transition enforcement for Kanban.
`TODO -> DOING -> DONE` exists conceptually, but nothing validates legal transitions or blocks direct TODO->DONE jumps.

5. No governance checkpoint before pipeline execution.
`./run` does not appear to enforce preflight checks for protocol/flow/schema/manifests alignment.

6. No semver governance policy.
There is no strict rule mapping change type (contract/tool/flow) to required version bump scope and changelog obligations.

7. No deprecation lifecycle policy.
Legacy markers exist (e.g., `ct-analyze`), but there is no defined lifecycle (announce, freeze, remove-by-date, migration owner).

8. No exception/waiver process.
No formal way to temporarily bypass governance with owner, expiry date, and remediation plan.

# 3) Role Boundary Clarity: PROFILE vs AURA vs PROTOCOL vs FLOW
Recommended hard boundary contract:

1. `PROFILE.md` (Why)
Owns goals, non-goals, quality priorities, architectural values, and review rubric.
Must not contain operational step sequence, CLI flags, or stage-level topology.

2. `AURA.md` (How work is performed)
Owns contributor/agent execution protocol: planning rules, order-of-operations, testing protocol, behavior constraints.
Must not redefine runtime stage topology or duplicate detailed pipeline semantics.

3. `PROTOCOL.json` (What exists)
Owns machine-readable topology: tools, contracts, stage ordering, versions, test commands, status markers.
Must be the only authoritative source for stage graph and tool-contract mapping.

4. `FLOW.md` (What runs)
Owns executable orchestration: concrete command chain, step metadata, runtime behavior.
Must be derivable from PROTOCOL topology and fail validation if diverged.

Current ambiguity to remove:
- Development order appears in both PROFILE and AURA with slightly different sequencing emphasis.
- Runtime mode semantics are not consistently modeled across AURA/PROTOCOL/FLOW (e.g., dry-run expectations vs declared flow modes).

# 4) Enforcement Gaps (What Can Drift)
High drift vectors:

1. Stage chain drift.
`PROTOCOL.flow.stages` can diverge from FLOW step blocks without automatic detection.

2. Contract IO drift.
Tool manifest input/output contracts can diverge from PROTOCOL contract map and FLOW annotations.

3. CLI surface drift.
FLOW options and real CLI behavior can diverge (e.g., flags present in docs but absent in protocol model).

4. Version drift.
`project.version`, FLOW changelog/version headers, and actual tool manifests can change independently.

5. Process drift.
KANBAN can be skipped or under-specified with no enforced precondition to implementation.

6. Testing drift.
AURA test protocol can drift from executable checks in CI and from actual `./run` preflight.

7. Legacy drift.
Deprecated tools can remain indefinitely because there is no policy deadline or blocking rule.

# 5) Concrete Additions (Policies/Checklists)
## A. Policy Additions (normative)
1. `GOV-001 Canonical Conflict Rule`
If documents conflict: runtime topology = PROTOCOL, runtime commands = FLOW, process = AURA, intent = PROFILE.
Any conflict requires either document patch or temporary waiver.

2. `GOV-002 Merge Gate`
No merge unless `governance-check` passes all consistency checks.

3. `GOV-003 Run Preflight Gate`
`./run` must execute `governance-check --runtime` and abort on critical mismatch.

4. `GOV-004 Version Discipline`
- Contract breaking change -> major contract version + affected tool manifest update + flow compatibility note.
- Non-breaking schema/tool/flow change -> minor/patch with changelog entry.
- Version mismatch across PROTOCOL/FLOW/manifests -> block.

5. `GOV-005 KANBAN Minimum Fields`
KANBAN tasks must include: `contract_impact`, `files_changed`, `verification_steps`, `evidence_paths`, `owner`.

6. `GOV-006 Deprecation Lifecycle`
Statuses: `active -> deprecated -> blocked -> removed` with target dates and migration owner.

7. `GOV-007 Waiver Process`
Any governance bypass requires `waiver_id`, approver, reason, expiration date, rollback/remediation plan.

## B. Checklist Additions (operational)
Pre-implementation checklist:
- KANBAN file created from template and linked as `.aura/kanban/latest`.
- Contract impact declared for every task.
- Affected authority files identified (PROFILE/AURA/PROTOCOL/FLOW).
- Required version bump type decided.

Pre-merge checklist:
- `PROTOCOL.flow.stages` == FLOW step order.
- For each stage: manifest path exists, input/output contracts match protocol.
- FLOW step `@contract` annotations match declared contracts.
- CLI options documented in FLOW are represented in protocol (or explicitly marked FLOW-only).
- Changelog entries updated with date and rationale.

Pre-run checklist:
- `governance-check --runtime` pass.
- Contract schemas validate sample artifacts.
- `./run --dry-run` behavior is explicitly declared and tested, or deliberately unsupported and documented consistently.

## C. Minimal Implementable Enforcement Package
1. Add `scripts/governance_check.py` with checks:
- parse PROTOCOL
- parse FLOW step metadata
- compare stage order
- compare contracts per stage
- compare version fields
- validate KANBAN required fields on latest plan

2. Add CI target:
- `make governance-check`
- Run on every PR/merge.

3. Add runtime hook:
- `./run` calls governance check before execution.

4. Add schema for KANBAN:
- `contracts/kanban.schema.json`
- validate `.aura/kanban/latest`.

# 6) Priority Matrix (High/Medium/Low)
| Priority | Gap | Impact | Concrete Action | Owner |
|---|---|---|---|---|
| High | No automated consistency gate | Silent topology/process drift | Implement `scripts/governance_check.py` + CI hard fail | Maintainer |
| High | No run-time governance preflight | Production run with invalid governance state | Call governance check from `./run` before Step 1 | Maintainer |
| High | No KANBAN schema/required evidence fields | Planning SSOT becomes decorative | Introduce `contracts/kanban.schema.json` + validate latest plan | Maintainer |
| Medium | Ambiguous conflict precedence across docs | Review disputes and inconsistent decisions | Add `GOV-001` canonical conflict rule in AURA | Maintainer |
| Medium | Versioning policy not enforceable | Untraceable breaking changes | Add semver policy + automated version alignment check | Maintainer |
| Medium | Deprecation lifecycle undefined | Legacy tooling accumulates indefinitely | Add status lifecycle with deadlines in PROTOCOL | Maintainer |
| Low | Missing waiver mechanism | Ad-hoc exceptions, weak auditability | Add waiver template and expiry enforcement | Maintainer |
| Low | Checklist not encoded in PR workflow | Inconsistent manual compliance | Add PR template with governance checklist | Maintainer |
