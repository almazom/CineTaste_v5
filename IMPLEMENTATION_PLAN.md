# Implementation Plan: Project Root Reorganization

**Date:** 2026-03-27
**Repo:** `/home/pets/zoo/CineTaste_v5`
**Status:** Ready for execution
**Scope:** Project-root cleanup and normalization only

## 1. Objective

Reorganize the repository root so it reflects CineTaste's real architecture instead of accumulated runtime debris.

The root should expose only:

- governance and SSOT files,
- stable operator entrypoints,
- stable CLI wrappers,
- permanent project directories.

Everything else should either be moved under a more specific home or removed as ignored/generated clutter.

## 2. Ground Truth

As of 2026-03-27 the repo root contains:

- `46` visible top-level entries
- `12` hidden top-level entries

This includes several classes of items mixed together:

- **Governance / SSOT:** `AGENTS.md`, `AURA.md`, `PROTOCOL.json`, `PROFILE.md`, `README.md`, `KANBAN.json`
- **Execution entrypoints:** `run`, `pipeline`, `Makefile`, `requirements.txt`, `pytest.ini`
- **Active wrappers:** `ct-fetch`, `ct-schedule`, `ct-cognize`, `ct-filter`, `ct-format`, `ct-time-price`, `ct-provider-latest`
- **Legacy compatibility wrappers:** `ct-analyze`, `ct-cognetive`, `ct-showtimes`
- **Secondary documentation at root:** `AGENT_OPERATING_MANUAL.md`
- **Permanent directories:** `contracts/`, `docs/`, `flows/`, `logs/`, `ops/`, `taste/`, `tests/`, `tools/`
- **Ignored/generated clutter:** `.coverage`, `.pytest_cache/`, `.ruff_cache/`, `.testrun/`, `.codex-review/`, `archive/`, `bio/`, `cards/`, `colony_memory/`, `final/`, `reports/`, `runs/`, `sdd_package_*`, `ssot/`, `temp/`, `t2me`

Important repo-specific constraints:

1. `PROFILE.md` should stay at root.
Evidence: project docs describe it as part of the governance intent layer, not as incidental documentation.

2. `ct-analyze` is not safe to delete in a blind cleanup.
Evidence: the root wrapper points to missing `tools/ct-analyze/main.py`, but `PROTOCOL.json`, contracts, tests, and multiple docs still intentionally reference `ct-analyze` as a legacy surface.

3. `ct-cognetive` is also not safe to remove in a blind cleanup.
Evidence: `tests/test_ct_cognize.py` asserts the alias exists, and `tools/ct-cognize/MANIFEST.json` documents it.

4. `ct-showtimes` is a likely cleanup candidate, but it still represents a compatibility decision.
Evidence: it is only a thin proxy to `ct-time-price`; current repo references are absent, but external operator usage is unknown.

5. `AGENT_OPERATING_MANUAL.md` is the strongest move candidate among tracked root files.
Evidence: it is explanatory documentation, not a runtime entrypoint, and no active code/tests reference it.

## 3. Reorganization Principles

1. **Preserve runtime truth first.**
   Root cleanup must not break `./run`, wrapper discovery, or current compatibility surfaces by accident.

2. **Keep root intentional, not minimal for its own sake.**
   CineTaste legitimately uses several top-level wrappers. A clean root here is not "15 files"; it is "only architecture-facing files remain."

3. **Delete ignored/generated artifacts before changing tracked files.**
   This yields the biggest clarity improvement with the lowest risk.

4. **Treat legacy wrappers as API surfaces until explicitly deprecated.**
   If a wrapper is referenced by tests, manifests, docs, or `PROTOCOL.json`, retire it in a dedicated compatibility change, not as incidental cleanup.

5. **Sync SSOT and docs whenever a tracked root file moves or disappears.**
   For CineTaste, structure is part of the contract.

## 4. Target Root Contract

### 4.1 Keep In Root

**Governance / SSOT**

- `AGENTS.md`
- `AURA.md`
- `PROTOCOL.json`
- `PROFILE.md`
- `README.md`
- `KANBAN.json`
- `IMPLEMENTATION_PLAN.md` while this effort is active

**Operator / build entrypoints**

- `run`
- `pipeline`
- `Makefile`
- `requirements.txt`
- `pytest.ini`

**Stable wrappers**

- `ct-fetch`
- `ct-schedule`
- `ct-cognize`
- `ct-filter`
- `ct-format`
- `ct-time-price`
- `ct-provider-latest`

**Permanent project directories**

- `.MEMORY/`
- `.aura/`
- `.pi/`
- `contracts/`
- `docs/`
- `flows/`
- `logs/`
- `ops/`
- `taste/`
- `tests/`
- `tools/`

### 4.2 Move Out Of Root

- `AGENT_OPERATING_MANUAL.md` -> `docs/legacy/agent-operating-manual.md`

Rationale:

- it is descriptive reference material,
- it is not part of the execution bootstrap,
- it dilutes root-level signal.

### 4.3 Remove From Root Only After Compatibility Retirement

- `ct-analyze`
- `ct-cognetive`
- `ct-showtimes`

These should be handled in a separate deprecation step with explicit acceptance criteria.

### 4.4 Remove As Ignored / Generated Clutter

- `.coverage`
- `.pytest_cache/`
- `.ruff_cache/`
- `.testrun/`
- `.codex-review/`
- `archive/`
- `bio/`
- `cards/`
- `colony_memory/`
- `final/`
- `reports/`
- `runs/`
- `sdd_package_20260310_083249/`
- `sdd_package_20260310_083358/`
- `ssot/`
- `temp/`
- `t2me`

Expected result:

- Immediate cleanup path reduces visible root entries from `46` to roughly `33` without touching compatibility wrappers.
- Optional legacy-wrapper retirement can reduce visible root entries further to roughly `30`.

## 5. Execution Plan

### Phase 0: Freeze And Classify

- Create a fresh kanban session and keep `KANBAN.json` pointed at it.
- Capture current `git status --short`.
- Snapshot the root inventory before deleting anything.
- Confirm that the current user-owned dirty files are not part of the cleanup unless explicitly intended.

Acceptance gate:

- Planned change list distinguishes tracked files from ignored/generated artifacts.

### Phase 1: Purge Ignored And Generated Root Clutter

- Remove the ignored/generated entries listed in section 4.4.
- Keep `logs/` itself.
- If pruning log contents, preserve tracked subtrees and only remove ignored runtime spill such as `logs/failed_*` and `logs/deep_run_*`.

Acceptance gate:

- Root no longer shows disposable runtime clutter.
- `git status --short` does not expand unexpectedly because ignored directories were removed rather than tracked files edited.

### Phase 2: Relocate Secondary Root Documentation

- Create `docs/legacy/` if it does not already exist.
- Move `AGENT_OPERATING_MANUAL.md` to `docs/legacy/agent-operating-manual.md`.
- Run a repo-wide search for `AGENT_OPERATING_MANUAL.md` and update references only if any appear.

Acceptance gate:

- Root contains only governance docs, not supplementary manuals.

### Phase 3: Keep `PROFILE.md` In Root

- Do not move `PROFILE.md`.
- If desired, add a short note in `README.md` or `AGENTS.md` clarifying that `PROFILE.md` is part of the governance/intent layer.

Acceptance gate:

- Root still exposes the governance triad clearly: `PROFILE.md`, `AURA.md`, `PROTOCOL.json`.

### Phase 4: Legacy Wrapper Decision Pass

Do not bundle this into the low-risk cleanup commit unless all gates pass.

**`ct-analyze`**

- Choose one path:
- Path A: restore or keep legacy compatibility intentionally
- Path B: retire it fully

If retiring:

- remove the root wrapper,
- remove or update stale tests such as `tests/test_ct_analyze.py`,
- update `PROTOCOL.json`,
- update contract docs and memory notes that still mention the legacy mapping,
- update review docs only if they claim it is still present rather than historically discussed.

**`ct-cognetive`**

- Keep until alias support is intentionally retired.
- If retiring, update `tests/test_ct_cognize.py` and `tools/ct-cognize/MANIFEST.json` in the same change.

**`ct-showtimes`**

- Run one final reference audit.
- If still unused, remove it as part of the same compatibility/deprecation batch or keep it documented as an alias.

Acceptance gate:

- No compatibility wrapper is removed unless docs, tests, and protocol ownership agree on the retirement.

### Phase 5: SSOT And Docs Sync

Only required if tracked root files move or if legacy wrappers are retired.

Update as needed:

- `AGENTS.md`
- `README.md`
- `PROTOCOL.json`
- `.MEMORY/01-architecture.md`
- `.MEMORY/02-contracts.md`
- `.MEMORY/03-tools.md`
- `contracts/README.md`
- `contracts/viz/*`
- tests that encode legacy assumptions

Acceptance gate:

- Structure claims and runtime truth match again.

### Phase 6: Verification

Run these checks after each change batch:

1. `git status --short`
2. `python3 -m pytest tests/test_docs_sync.py -q`
3. `python3 -m pytest tests/test_pipeline_flow.py -q`
4. `python3 -m pytest tests/test_ct_cognize.py -q`
   Only required if alias/wrapper behavior changes.
5. `python3 -m pytest tests/test_ct_analyze.py -q`
   Only required if `ct-analyze` is retained or deliberately retired.
6. `make test`
7. `./run --dry-run --input contracts/examples/analysis-result.sample.json`
   Run when wrapper or root entrypoint changes could affect operator flow.

## 6. Recommended Change Sets

### Change Set A: Low-Risk Root Cleanup

- purge ignored/generated clutter,
- move `AGENT_OPERATING_MANUAL.md` into `docs/legacy/`,
- keep `PROFILE.md` in root,
- leave legacy wrappers untouched.

Recommended commit:

- `chore: clean root artifacts and relocate legacy manual`

### Change Set B: Compatibility Wrapper Retirement

- retire `ct-showtimes` if confirmed unused,
- decide whether `ct-cognetive` remains a supported alias,
- either restore or fully retire `ct-analyze`,
- sync tests/docs/protocol in the same change.

Recommended commit:

- `chore: retire legacy root wrappers`

## 7. Risks

| Risk | Why it matters | Mitigation |
|------|----------------|------------|
| Deleting legacy wrappers too early | Tests, docs, and operator habits still encode them | Split wrapper retirement into a dedicated change set |
| Moving governance docs incorrectly | Root loses architectural clarity | Keep `PROFILE.md` in root; move only the operating manual |
| Deleting tracked runtime evidence inside `logs/` | May erase useful reproducibility artifacts | Remove only ignored failure/debug spill unless explicitly archiving |
| Treating root-count minimization as the goal | Legitimate wrappers would get removed for aesthetics | Use category-based cleanup, not an arbitrary count target |

## 8. Definition Of Done

- Root contains only intentional governance files, operator entrypoints, wrappers, and permanent directories.
- Ignored/generated clutter is gone from the root.
- `AGENT_OPERATING_MANUAL.md` no longer sits at root.
- `PROFILE.md` remains at root.
- Legacy wrappers are either explicitly preserved or explicitly retired with synced docs/tests.
- Verification commands pass for the chosen change set.
