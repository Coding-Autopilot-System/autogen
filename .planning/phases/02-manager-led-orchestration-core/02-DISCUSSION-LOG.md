# Phase 2: Manager-Led Orchestration Core - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-03-21
**Phase:** 02-manager-led-orchestration-core
**Areas discussed:** Manager workflow and stage model, Pause/resume semantics, Automatic GSD clarification handling, Operator-visible orchestration state

---

## Manager workflow and stage model

### Question 1

| Option | Description | Selected |
|--------|-------------|----------|
| Canonical manager stage flow | Use one explicit `planning -> research -> implementation -> review -> validation` sequence for normal engineering runs | yes |
| Freeform manager orchestration | Let the manager improvise stage order from prompt to prompt | |
| Specialist-first direct mode | Expose specialist handoffs without a stable manager stage contract | |

**User's choice:** [auto] Selected: Canonical manager stage flow
**Notes:** Recommended because `ORCH-01` needs one trustworthy workflow that operators can understand and resume.

### Question 2

| Option | Description | Selected |
|--------|-------------|----------|
| One run with nested stage records | Preserve one durable run while stage outputs live under that run as artifacts and events | yes |
| Separate run per stage | Easier isolation but fragments the operator history | |
| Loose transcript-only stage tracking | Minimal effort but too brittle for pause and resume semantics | |

**User's choice:** [auto] Selected: One run with nested stage records
**Notes:** Recommended because Phase 1 already locked one durable run identity with artifacts and attempt history.

### Question 3

| Option | Description | Selected |
|--------|-------------|----------|
| Manager-controlled transitions from structured outputs | The manager advances stages based on explicit stage results and state | yes |
| Human-controlled transitions at every stage | Safe but too manual for the product goal | |
| Transcript-text-driven transitions | Fast but brittle and hard to debug | |

**User's choice:** [auto] Selected: Manager-controlled transitions from structured outputs
**Notes:** Recommended because the platform should feel autonomous while remaining auditable.

### Question 4

| Option | Description | Selected |
|--------|-------------|----------|
| Keep specialists behind the manager boundary for now | Expose stage progress now, defer full specialist visibility to Phase 3 | yes |
| Expose every specialist in Phase 2 | More transparency immediately but scope overlaps Phase 3 | |
| Use manager only with no specialist seam | Simplifies implementation but weakens the later delegation path | |

**User's choice:** [auto] Selected: Keep specialists behind the manager boundary for now
**Notes:** Recommended because Phase 2 is about the manager contract, while specialist visibility has its own phase.

---

## Pause/resume semantics

### Question 1

| Option | Description | Selected |
|--------|-------------|----------|
| Structured orchestration pause reasons | Use `needs_input`, `needs_approval`, `blocked`, `retryable_error`, `completed`, and `stopped` | yes |
| Simple waiting/running split | Easier now but too vague for operators | |
| Tool-approval-only pause model | Leaves too many workflow states implicit | |

**User's choice:** [auto] Selected: Structured orchestration pause reasons
**Notes:** Recommended because `ORCH-02` requires operators to know why the run paused, blocked, or completed.

### Question 2

| Option | Description | Selected |
|--------|-------------|----------|
| Resume the paused stage with prior outputs intact | Best continuity and lowest operator surprise | yes |
| Replay the full workflow on resume | Simpler implementation but wasteful and confusing | |
| Start a fresh attempt automatically on every resume | Too destructive to prior work | |

**User's choice:** [auto] Selected: Resume the paused stage with prior outputs intact
**Notes:** Recommended because Phase 1 already established durable stage and run artifacts.

### Question 3

| Option | Description | Selected |
|--------|-------------|----------|
| Stage-level gates plus risky action approvals | Pause after planning or review when meaningful operator decisions are needed, while keeping tool-level approval underneath | yes |
| Approval after every stage | Safer but too chatty and slow | |
| Risky action approvals only | Faster, but leaves orchestration decisions too opaque | |

**User's choice:** [auto] Selected: Stage-level gates plus risky action approvals
**Notes:** Recommended because the operator wants one-prompt flow, not continuous manual steering.

### Question 4

| Option | Description | Selected |
|--------|-------------|----------|
| Stage-scoped retry by default | Re-run the failed or blocked stage while preserving successful prior stages | yes |
| Full-run retry only | Easier but wastes completed work | |
| Manual prompt rewrite for every retry | Too much operator work for a core orchestration system | |

**User's choice:** [auto] Selected: Stage-scoped retry by default
**Notes:** Recommended because it aligns with durable run identity and minimizes needless repetition.

---

## Automatic GSD clarification handling

### Question 1

| Option | Description | Selected |
|--------|-------------|----------|
| Answer from project, phase, repo, and workspace context first | Use planning docs plus repo facts before asking the operator | yes |
| Ask the operator for every GSD question | Accurate but defeats the automation goal | |
| Guess from the prompt alone | Fast but too error-prone | |

**User's choice:** [auto] Selected: Answer from project, phase, repo, and workspace context first
**Notes:** Recommended because `ORCH-04` explicitly calls for automatic answers to routine GSD questions.

### Question 2

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-answer only routine clarification and planning defaults | Leave product-direction changes and destructive approvals to the operator | yes |
| Auto-answer everything possible | Aggressive but risky around scope and approvals | |
| Disable auto-answering and only summarize context | Too weak for the desired one-prompt workflow | |

**User's choice:** [auto] Selected: Auto-answer only routine clarification and planning defaults
**Notes:** Recommended because the product should stay autonomous without erasing real human checkpoints.

### Question 3

| Option | Description | Selected |
|--------|-------------|----------|
| Persist auto-answered GSD decisions as structured artifacts and events | Best traceability for later review and debugging | yes |
| Keep auto-answers only in transcript text | Human-readable but weak for tooling | |
| Keep auto-answers ephemeral only | Fastest but invisible to the operator | |

**User's choice:** [auto] Selected: Persist auto-answered GSD decisions as structured artifacts and events
**Notes:** Recommended because the operator wants to see how orchestration decisions were made.

### Question 4

| Option | Description | Selected |
|--------|-------------|----------|
| Pause with a concise missing-info summary and suggested options | Keeps ambiguity visible and actionable | yes |
| Silently guess when confidence is low | Faster but weakens trust | |
| Dump the raw GSD question to the operator unchanged | Accurate but less useful than a curated question pack | |

**User's choice:** [auto] Selected: Pause with a concise missing-info summary and suggested options
**Notes:** Recommended because the platform should ask for help only when it can explain what is missing.

---

## Operator-visible orchestration state

### Question 1

| Option | Description | Selected |
|--------|-------------|----------|
| Shared orchestration contract in the active runtime, mirrored into the operator API | One source of truth across MAF execution and operator state | yes |
| DevUI-only orchestration logic | Quickest local path but too brittle and local-console-specific | |
| Legacy dashboard-only orchestration logic | Strong UI seam, but would bypass the active runtime | |

**User's choice:** [auto] Selected: Shared orchestration contract in the active runtime, mirrored into the operator API
**Notes:** Recommended because Phase 2 should strengthen the runtime contract, not bind core behavior to one UI shell.

### Question 2

| Option | Description | Selected |
|--------|-------------|----------|
| Compact explicit orchestration surface now | Show current stage, overall status, pause reason, and stage outputs without trying to finish the full product UI | yes |
| Raw events and traces only | Low effort but too opaque for normal operation | |
| Full polished workbench now | Valuable later, but overlaps Phase 5 | |

**User's choice:** [auto] Selected: Compact explicit orchestration surface now
**Notes:** Recommended because Phase 2 is the right time to make state visible, but not the right time to finish visual polish.

### Question 3

| Option | Description | Selected |
|--------|-------------|----------|
| Structured run and stage events | Emit `run.*` and `stage.*` events alongside transcript and route metadata | yes |
| Transcript-only status reporting | Too weak for automation and later UI tabs | |
| Provider traces only | Good for debugging, not enough for orchestration state | |

**User's choice:** [auto] Selected: Structured run and stage events
**Notes:** Recommended because later phases need auditable orchestration history, not just model traces.

### Question 4

| Option | Description | Selected |
|--------|-------------|----------|
| One canonical run and stage vocabulary everywhere | Reuse the same statuses across runtime, storage, API, and UI | yes |
| Separate status vocabularies per runtime surface | Adds translation complexity and drift | |
| Let each UI derive status from raw events | Too brittle for a core operator tool | |

**User's choice:** [auto] Selected: One canonical run and stage vocabulary everywhere
**Notes:** Recommended because a professional orchestration platform needs one understandable state model.

---

## the agent's Discretion

- Exact stage artifact file names and summary schemas
- Exact confidence heuristics for automatic GSD answering
- Exact temporary presentation of the stage banner and timeline before the polished workbench phase

## Deferred Ideas

- Rich per-agent tabs and live specialist panes - Phase 3 and Phase 5
- Final stylish conversation shell and fully polished operator UI - Phase 5
- Autonomous repo editing and validation-by-default behavior - Phase 4
- Azure Function and REST exposure - later cloud phase
