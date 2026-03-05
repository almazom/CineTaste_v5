# Review 5 — Reliability / Testing / Verification

## 1) Executive Summary

Current test baseline is healthy but not reliability-complete.

Measured current state (from `pytest` runs on 2026-03-04):
- `132 passed, 1 skipped, 5 deselected` (`pytest tests/` with default `-m "not network"`).
- Coverage gate is not met: `TOTAL 71%` vs `PROTOCOL.json` target `80%`.
- Critical active stage is under-covered: `tools/ct-cognize/main.py` at `49%`, `tools/ct-cognize/port.py` at `43%`.
- Flow-level reliability gate is weakened: pipeline dry-run regression test is explicitly skipped.

Conclusion: functional correctness is decent for happy paths and basic error paths, but reliability guarantees are not yet defined as enforceable quality gates.

## 2) Missing reliability requirements

1. No explicit reliability SLO/SLA per pipeline stage.
- Missing requirement: define success-rate target and timeout budget for each stage (`ct-fetch`, `ct-schedule`, `ct-cognize`, `ct-filter`, `ct-format`, `t2me`).

2. No retry/fallback policy as a contract requirement.
- Missing requirement: for network/agent steps, define max retries, backoff policy, and fail-fast conditions with exit-code semantics.

3. No deterministic-output requirement for non-network mode.
- Missing requirement: for fixed input fixtures, output hash/signature should be stable for `ct-schedule`, `ct-filter`, `ct-format` (excluding timestamps).

4. No idempotency requirement for delivery boundary.
- Missing requirement: resend behavior must prevent duplicate sends for same message ID/run ID.

5. No reliability requirement for topology alignment.
- Missing requirement: tests must track active flow (`PROTOCOL.flow.stages`), not legacy-only tooling.

6. No explicit MTTR-oriented requirement for failure recovery.
- Missing requirement: failure artifacts must be sufficient to reproduce the failed run in one command.

## 3) Missing verification gates and evidence model

1. Coverage gate is defined but not enforced as release blocker.
- Evidence: target is 80 in `PROTOCOL.json`; measured total is 71.

2. No mandatory gate for active pipeline E2E path.
- Evidence: `tests/test_pipeline_flow.py` includes a skipped dry-run test; no enforced non-sending E2E regression for current flow behavior.

3. Topology-test mismatch gate is missing.
- Evidence: flow uses `ct-cognize`; wrapper/executable checks still center on legacy `ct-analyze` in some tests.

4. Fault-injection gate is missing for critical adapters.
- Missing checks: HTTP 429/5xx retry behavior, malformed upstream payloads, partial AI output, t2me transient failures.

5. Flakiness gate is missing.
- Missing checks: repeated-run stability for agent selection/fallback and parser branches.

6. Evidence model is console-heavy, artifact-light.
- Missing requirement: standardized run artifacts with machine-readable gate outcomes.

## 4) Missing observability/debug standards

1. No mandatory `run_id` correlation across all stage outputs/logs.

2. No standard step-level telemetry artifact.
- Missing fields: `step_name`, `start_ts`, `end_ts`, `duration_ms`, `status`, `error_code`, `input_contract`, `output_contract`.

3. No error taxonomy standard.
- Missing mapping: validation errors vs transient dependency failures vs permanent configuration errors.

4. No standard capture of agent decision trace.
- Missing fields: preflight results, selected agent chain, fallback attempts, per-attempt error reason.

5. No defined retention and triage policy for failed run artifacts.

## 5) Concrete additions (DoD checks, evidence artifacts)

### DoD checks (blocking)

| Check | Command / Method | Threshold | Block release if fail |
|---|---|---|---|
| Contract + unit regression | `pytest tests/ -m "not network"` | 100% pass | Yes |
| Network reliability regression | `pytest tests/ -m network -v` | 100% pass on CI schedule | Yes |
| Coverage enforcement | `pytest tests/ --cov=tools --cov-report=term-missing` | Total >= 80%, `ct-cognize/main.py >= 70%`, `ct-cognize/port.py >= 70%` | Yes |
| Active flow alignment | Auto-check: every `PROTOCOL.flow.stages` entry has CLI smoke + contract test | 0 missing stages | Yes |
| E2E verification (safe mode) | Add non-send E2E mode and run full flow with fixtures | 1 full pass, valid `send-confirmation`-shape preview artifact | Yes |
| Failure-injection suite | Simulate adapter/network/agent failures | All expected exit codes + recovery artifacts produced | Yes |
| Flake detector (critical tests) | Repeat selected tests N=20 | 0 intermittent failures | Yes |

### Evidence artifacts (required per CI run)

Store under: `artifacts/reliability/<run_id>/`

| Artifact | Purpose |
|---|---|
| `summary.json` | Protocol version, flow version, commit SHA, gate results, final status |
| `pytest_not_network.xml` | Deterministic regression evidence |
| `pytest_network.xml` | External dependency reliability evidence |
| `coverage.txt` | Human-readable coverage report |
| `coverage.json` | Machine-evaluable gate input |
| `flow_e2e.log` | Full pipeline execution trace |
| `step_metrics.json` | Per-step latency/status telemetry |
| `failure_bundle/` (on fail) | Preserved inputs/outputs/errors needed for one-command replay |

## 6) Priority matrix (High / Medium / Low)

| Priority | Item | Why now |
|---|---|---|
| High | Enforce coverage gate to protocol target (80%) | Current measured 71% violates SSOT target |
| High | Add mandatory active-flow E2E verification gate (safe non-send mode) | Current flow reliability is not continuously proven |
| High | Add topology alignment gate (`PROTOCOL.flow.stages` vs tests) | Prevents drift between implemented flow and tested flow |
| High | Raise coverage for `ct-cognize` critical path | Active cognitive stage is under-tested (49%/43%) |
| Medium | Add adapter fault-injection suite (429/5xx/timeouts/malformed) | Improves resilience confidence under real failures |
| Medium | Standardize run artifacts (`summary.json`, metrics, bundles) | Enables reproducible debugging and auditability |
| Medium | Add flakiness detection for agent fallback tests | Catches non-deterministic failures early |
| Low | Define retention/TTL policy for reliability artifacts | Operational hygiene and storage control |
| Low | Add trend dashboard for pass-rate/latency/coverage over time | Useful for governance, not immediate blocker |
