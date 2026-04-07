# Kanban-First Planning Standard for AI Agents

Status: active transfer reference  
Scope: reusable operating standard derived from CineTaste v5  
Audience: AI agents, agent maintainers, and repository owners  
Last synchronized: 2026-04-07

## Purpose

This file extracts the practical planning discipline used in CineTaste into one standalone reference that can be shown to another AI agent.

The intent is simple:

- do not start implementation from intuition;
- create a timestamped kanban plan before changing the repository;
- keep that plan as the session SSOT while work is in progress;
- close the loop with verification and evidence, not only code edits.

This document is written so that another agent can understand both the rule and the operating mechanics after reading a single file.

## Inputs

Use this standard when the target repository has, or should have, these elements:

- `AURA.md` or another runtime protocol file
- `AGENTS.md` or another repository instruction file
- `PROTOCOL.json` or another topology/config SSOT
- `.aura/kanban/` for timestamped plans
- `.aura/templates/KANBAN.template.json` for plan bootstrapping

The minimum task inputs are:

- the user request
- the current repository state
- the active instruction files
- the current active kanban, if one already exists

## Sources Used for This Extraction

This standard is derived from these CineTaste sources:

- `AURA.md`
- `AGENTS.md`
- `PROTOCOL.json`
- `docs/golden-standard.md`
- `.aura/templates/KANBAN.template.json`
- `.aura/kanban/KANBAN-2026-04-07-0808.json`
- `.aura/kanban/KANBAN-2026-04-07-0851.json`
- `.aura/kanban/KANBAN-2026-04-07-0936.json`
- `.MEMORY/00-index.md`
- `.MEMORY/01-architecture.md`
- `.MEMORY/02-contracts.md`
- `.MEMORY/03-tools.md`
- `.MEMORY/05-troubleshooting.md`

## Pre-checks

Before implementation, do this in order:

1. Read `AURA.md`.
2. Read `PROTOCOL.json`.
3. Read the nearest applicable `AGENTS.md`.
4. Inspect `.aura/kanban/latest` if it exists.
5. Decide whether the request is:
   - a no-edit question,
   - a documentation-only change,
   - an implementation change,
   - or a mixed task.
6. If the task will change repository files or operational state in a meaningful way, require a kanban plan before proceeding.

## Precedence Model

Use this precedence when applying the standard:

1. Explicit user goal
2. Nearest `AGENTS.md`
3. `AURA.md`
4. `PROTOCOL.json`
5. Active `.aura/kanban/latest`
6. Contracts, manifests, and active `FLOW.md`
7. This transfer standard

Important distinction:

- `PROTOCOL.json` answers what exists.
- `AURA.md` answers how to work.
- `.aura/kanban/latest` answers what this session is doing now.

## Non-Negotiable Rules

These are the core invariants of the CineTaste planning discipline.

1. Do not start implementation before a kanban file exists for the current scope.
2. The plan file must be timestamped, not overwritten in place under a generic name.
3. `.aura/kanban/latest` must point to the active plan.
4. Work must be expressed through `TODO`, `DOING`, and `DONE`.
5. Acceptance criteria must exist before implementation starts.
6. Every meaningful task must say what boundary it affects.
7. The kanban must be updated as work progresses; it is not a dead planning artifact.
8. A task is not `DONE` until the relevant verification has happened.
9. If scope changes materially, update the kanban before continuing implementation.
10. Final handoff should mention the active kanban and the evidence that closed it.

## Why This Works

This pattern gives the repository four things that ad hoc coding does not:

- visible intent before code
- bounded scope during the session
- auditable progress state
- a reproducible handoff point for the next human or agent

In practice, it prevents these common failures:

- hidden scope growth
- code-first changes without contract updates
- vague “almost done” sessions
- lost context when another agent resumes work later

## File-System Contract

The minimal layout is:

```text
.aura/
├── kanban/
│   ├── KANBAN-YYYY-MM-DD-HHMM.json
│   ├── latest -> KANBAN-YYYY-MM-DD-HHMM.json
│   └── archive/                 # optional
└── templates/
    └── KANBAN.template.json
```

Required conventions:

- one active `latest` symlink
- timestamp in filename
- JSON as the machine-readable canonical format
- no hidden planning state outside the file

## Kanban JSON Contract

At minimum, a plan should contain:

- plan identity
- planning session metadata
- state columns
- task objects
- acceptance criteria
- stats

Recommended structure:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "KANBAN-YYYY-MM-DD-HHMM.json",
  "title": "Kanban Plan",
  "description": "One-sentence summary of the session goal.",
  "planning_session": {
    "id": "KANBAN-YYYY-MM-DD-HHMM",
    "created_at": "2026-04-07T09:36:00+03:00",
    "author": "codex",
    "goal": "What this session aims to achieve."
  },
  "states": ["TODO", "DOING", "DONE"],
  "columns": {
    "TODO": [
      {
        "id": "task-01",
        "task": "Describe one verifiable unit of work.",
        "contract_impact": ["analysis-result@1.0.0"],
        "priority": 1,
        "estimated_complexity": "medium",
        "notes": "Constraints, risks, or scope boundaries."
      }
    ],
    "DOING": [],
    "DONE": []
  },
  "acceptance_criteria": [
    "Observable outcome 1",
    "Observable outcome 2"
  ],
  "stats": {
    "total": 1,
    "todo": 1,
    "doing": 0,
    "done": 0,
    "progress_percent": 0
  }
}
```

## Task Field Semantics

Use the task fields strictly.

### `id`

Use stable local identifiers such as `task-01`, `task-02`.

### `task`

Describe one verifiable outcome, not a vague area of work.

Good:

- `Add a month horizon to fetch and render upcoming movies`
- `Propagate rule_score and confidence through ct-filter`

Bad:

- `Improve project`
- `Fix some issues`

### `contract_impact`

Use this to declare what interface boundary the task touches.

Examples:

- `["movie-batch@1.0.0"]`
- `["analysis-result@1.0.0", "filter-result@1.0.0"]`
- `[]` for documentation-only work

This field is critical because it forces the agent to think in boundaries, not just files.

### `priority`

Use small integers. In CineTaste, `1` is highest priority.

### `estimated_complexity`

Use only stable labels:

- `low`
- `medium`
- `high`

### `notes`

Use notes for constraints, risk factors, and reminders.

Good notes describe why a task is shaped the way it is.

## State Semantics

The state machine is intentionally simple.

### `TODO`

Planned work that is not yet active.

### `DOING`

Work that is currently in progress in this session.

Strong recommendation:

- keep `DOING` small;
- prefer one active task unless the task is naturally parallel;
- if multiple tasks are in `DOING`, ownership must still be explicit.

### `DONE`

Completed and verified work.

`DONE` means:

- the implementation or document change exists,
- the claimed verification happened,
- the task no longer needs active execution.

## State Transition Rules

Use these transitions:

1. `TODO -> DOING` when active work begins.
2. `DOING -> DONE` only after verification.
3. `TODO -> DONE` is allowed only for trivial administrative items that genuinely required no active execution.
4. Do not leave finished work in `DOING`.
5. Do not mark blocked work as `DONE`.

If blocked, keep the task in `DOING` or move it back to `TODO` with an explicit blocker note.

## Session Lifecycle

This is the operational loop the agent should follow.

### Phase 1. Bootstrap

1. Read the governing files.
2. Inspect whether a relevant active plan already exists.
3. If not, create a new timestamped kanban file.
4. Update `.aura/kanban/latest`.

### Phase 2. Plan Before Code

1. Write the goal and description.
2. Break the work into verifiable tasks.
3. Add acceptance criteria before implementation.
4. Fill initial stats correctly.

### Phase 3. Execute Against the Plan

1. Move the current task into `DOING`.
2. Implement only work that belongs to a listed task.
3. If the task expands, update the plan first.
4. Keep notes accurate when discoveries change the real scope.

### Phase 4. Verify

Run the appropriate evidence for the task type:

- tests
- contract validation
- dry-run pipeline
- live pipeline
- documentation review
- delivery confirmation

### Phase 5. Close

1. Move verified tasks to `DONE`.
2. Update stats to match reality.
3. Ensure `progress_percent` is coherent.
4. Mention the kanban path and verification evidence in the final handoff.

## Acceptance Criteria Rules

Acceptance criteria should be:

- observable
- user-meaningful
- binary enough to verify
- written before implementation

Good criteria:

- `The pipeline can run in --dry-run without live Telegram delivery`
- `The rendered message has explicit sections for today, next 7 days, and next 30 days`
- `The resulting file is delivered through Telegram with confirmation`

Bad criteria:

- `Looks good`
- `Should be better`
- `Mostly works`

## Stats Discipline

The `stats` block must match the columns.

Required rules:

- `total = todo + doing + done`
- `todo` equals the number of tasks in `TODO`
- `doing` equals the number of tasks in `DOING`
- `done` equals the number of tasks in `DONE`
- `progress_percent` should reflect actual completion, not optimism

When all tasks are complete, use:

- `todo = 0`
- `doing = 0`
- `done = total`
- `progress_percent = 100`

## Planning Granularity

A good kanban task is:

- big enough to matter
- small enough to verify
- explicit about the boundary it changes

Prefer:

- 3 to 7 tasks for a medium session
- one major outcome per task
- one verification story per task or tightly related task cluster

Avoid:

- one giant task for the whole session
- dozens of tiny bookkeeping tasks
- tasks that describe files instead of outcomes

## What Must Trigger a Kanban Update

Update the kanban immediately when:

- you discover additional scope
- a task affects more contracts than expected
- the verification plan changes
- you split one task into several smaller tasks
- you complete or unblock a task

Do not wait until the end of the session to make the plan truthful again.

## What Counts as Verification

Verification must match the task.

### For code changes

Use at least one of:

- targeted tests
- full test suite
- contract validation
- dry-run command
- live command if the task is delivery-critical

### For documentation changes

Use:

- source cross-checking
- structural review
- path confirmation
- delivery confirmation if the user requested notification

### For operational changes

Use:

- command output
- run artifact inspection
- delivery logs
- confirmation IDs where applicable

## Derived CineTaste-Specific Practices

These are not generic guesses. They are patterns repeatedly used in this repository.

1. Plans live in `.aura/kanban/`.
2. `latest` is a symlink, not a copy.
3. The canonical state model is `TODO`, `DOING`, `DONE`.
4. `AURA.md` explicitly says the order is `CONTRACT -> KANBAN -> TOOL -> FLOW -> TEST -> VERSION`.
5. `AGENTS.md` explicitly says to create a kanban before code changes.
6. `docs/golden-standard.md` treats Kanban JSON as planning SSOT.
7. Real project kanbans keep `contract_impact`, `priority`, `estimated_complexity`, `notes`, and `acceptance_criteria`.

## Transferable Practices You Can Reuse in Another Repo

If another repository wants the same behavior, copy these rules first:

1. Create a timestamped kanban file before meaningful implementation.
2. Maintain one active `latest` pointer.
3. Use explicit `TODO`, `DOING`, `DONE`.
4. Require acceptance criteria before implementation.
5. Require updates as scope changes.
6. Require verification before `DONE`.
7. Mention the active plan in the final handoff.

If the target repo does not already have `.aura/`, create it.

## Minimal Adoption Recipe for Another Repository

1. Add `.aura/templates/KANBAN.template.json`.
2. Add `.aura/kanban/`.
3. Add a repository instruction file that says planning is mandatory before implementation.
4. Add a runtime protocol file that defines the order of work.
5. Teach agents to update `.aura/kanban/latest`.
6. Require final handoffs to mention both the active plan and the verification evidence.

## Copyable Instruction Block for Another AI Agent

Show the block below to another agent if you want it to operate in this style.

### Output Format

Follow this format precisely.

```text
You must work kanban-first.

Before any meaningful implementation or repository modification:
1. Read AURA.md.
2. Read PROTOCOL.json.
3. Inspect .aura/kanban/latest.
4. If no active plan fits the current scope, create .aura/kanban/KANBAN-YYYY-MM-DD-HHMM.json.
5. Update .aura/kanban/latest to point to that file.
6. Define tasks in TODO, DOING, and DONE.
7. Add acceptance_criteria before implementation.
8. Declare contract_impact for each task, or [] for docs-only work.
9. Keep stats synchronized with the actual task counts.
10. Do not implement work that is not represented in the active kanban.
11. If scope changes, update the kanban before continuing.
12. Mark a task DONE only after verification.
13. In your final handoff, name the kanban file you worked under and summarize the verification evidence.
```

## Copyable Maintainer Prompt

Use this if you are teaching a repository owner or agent maintainer what to install.

```text
Install a kanban-first execution discipline in this repository.

Required behavior:
- A timestamped kanban JSON must exist before implementation starts.
- .aura/kanban/latest must point to the active plan.
- Work must be tracked through TODO, DOING, DONE.
- Acceptance criteria must be written before implementation.
- The agent must update the kanban during execution, not only at the end.
- Verification evidence is required before DONE.
- Final handoff must mention the active plan and the evidence.

Required filesystem:
- .aura/kanban/
- .aura/templates/KANBAN.template.json

Required instruction files:
- AGENTS.md or equivalent repository rule file
- AURA.md or equivalent runtime protocol file
```

## Exceptions

These are the only reasonable exceptions.

1. Pure conversation with no repository action does not require a kanban.
2. A simple factual answer with no file changes does not require a kanban.
3. If an active plan already matches the scope, continue it instead of creating a duplicate.
4. Emergency production repair can begin with a minimal one-task kanban, but it still needs a kanban.

Do not treat “I will only make a small change” as an exception.

## Notes

This standard is intentionally stronger than normal ad hoc coding habits.

Its purpose is not ceremony. Its purpose is to make AI work:

- resumable
- reviewable
- bounded
- verifiable

If another agent reads only one file, this should be enough to explain both the philosophy and the mechanics of the system.
