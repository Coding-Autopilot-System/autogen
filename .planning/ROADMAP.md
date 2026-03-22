# Roadmap: GSD Orchestration Platform

## Overview

This roadmap turns the current MAF-first local prototype into a trustworthy local operator workbench for autonomous repo work. The delivery order prioritizes stable repo context and durable run state first, then the manager-led orchestration loop, then specialist visibility and routing transparency, then autonomous execution guardrails, and finally the polished operator UI that makes the system feel product-grade.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions if needed later

- [x] **Phase 1: Workspace and Durable Run Foundation** - Establish repo selection, workspace context, and durable local run state
- [x] **Phase 2: Manager-Led Orchestration Core** - Deliver the manager workflow and explicit stage/state model
- [x] **Phase 3: Specialist Delegation and Routing Visibility** - Make specialist participation and provider routing fully visible
- [x] **Phase 4: Autonomous Repo Execution and Validation Guardrails** - Turn the system into a safe default-doer for repo work
- [x] **Phase 5: Polished Operator Workbench** - Replace prototype interaction with a durable operator-grade UI

## Phase Details

### Phase 1: Workspace and Durable Run Foundation
**Goal**: Create the run and workspace contract that all later orchestration builds on.
**Depends on**: Nothing (first phase)
**Requirements**: WKSP-01, WKSP-02, WKSP-03
**Success Criteria** (what must be TRUE):
  1. User can start a run by choosing a local repo or worktree and entering one engineering prompt.
  2. The run captures path, branch, dirty state, and a concise workspace summary.
  3. Transcript, artifacts, and repo context persist under a stable run identity.
  4. A previous run can be reopened, retried, or resumed with prior context intact.
**Plans**: 3 plans

Plans:
- [x] 01-01: Normalize repo selection, workspace discovery, and run identity creation
- [x] 01-02: Unify durable local state for sessions, checkpoints, transcripts, and artifacts
- [x] 01-03: Surface workspace context consistently across UI, runtime, and traces

### Phase 2: Manager-Led Orchestration Core
**Goal**: Deliver a usable one-prompt manager workflow with explicit stage and pause semantics.
**Depends on**: Phase 1
**Requirements**: ORCH-01, ORCH-02, ORCH-03, ORCH-04
**Success Criteria** (what must be TRUE):
  1. One prompt can drive a manager-led workflow through planning, research, implementation, review, and validation.
  2. The system exposes current stage, overall status, and structured pause/block/complete reasons for each run.
  3. A paused run can continue after approval, missing input, or retry without losing prior stage outputs.
  4. Routine GSD clarification and planning questions are answered automatically from project and repo context in common cases.
**Plans**: 3 plans

Plans:
- [x] 02-01: Build the manager workflow contract and stage machine
- [x] 02-02: Add structured pause, resume, and automatic GSD-question handling
- [x] 02-03: Align run outputs, stage events, and orchestration summaries across the active runtime

### Phase 3: Specialist Delegation and Routing Visibility
**Goal**: Make delegation and model/provider behavior auditable and understandable.
**Depends on**: Phase 2
**Requirements**: AGNT-01, AGNT-02, AGNT-03, ROUT-01, ROUT-02, ROUT-03
**Success Criteria** (what must be TRUE):
  1. User can see which specialist agents are participating in the run and what role each one owns.
  2. Each specialist exposes current task, latest output, and handoff status in structured run data.
  3. The manager can delegate repo work to specialists without manual prompt choreography by the user.
  4. User can choose a preferred model or route lane before the run starts.
  5. Each turn records provider, model, route tier, rationale, and any fallback event with capability changes clearly shown.
**Plans**: 3 plans

Plans:
- [x] 03-01: Formalize specialist roles, handoffs, and per-agent state
- [x] 03-02: Build route selection, route metadata, and fallback capability reporting
- [x] 03-03: Expose specialist and routing data cleanly in the operator surface

### Phase 4: Autonomous Repo Execution and Validation Guardrails
**Goal**: Enable autonomous repo work while containing execution risk.
**Depends on**: Phase 3
**Requirements**: EXEC-01, EXEC-02, EXEC-03, EXEC-04
**Success Criteria** (what must be TRUE):
  1. Autonomous runs can edit files inside the selected repo without per-step approval for routine safe actions.
  2. Each run attaches changed-file lists, diffs, or equivalent file-level output that the operator can inspect.
  3. The system runs targeted local validation commands and stores the results with the run artifacts.
  4. Destructive or externally visible actions always trigger an explicit approval step with clear scope and reason.
**Plans**: 3 plans

Plans:
- [x] 04-01: Add controlled write execution and change capture
- [x] 04-02: Add targeted validation runners and result recording
- [x] 04-03: Enforce explicit approval policy for destructive or externally visible actions

### Phase 5: Polished Operator Workbench
**Goal**: Deliver the professional, stylish operator experience over the stabilized orchestration contracts.
**Depends on**: Phase 4
**Requirements**: UI-01, UI-02, UI-03
**Success Criteria** (what must be TRUE):
  1. The primary UI presents visually distinct human, manager, and specialist messages in a polished operator-grade layout.
  2. The operator can switch cleanly between overall run view, per-agent view, traces, and artifacts.
  3. Traces, event timeline, approvals, and generated artifacts are inspectable without reading raw logs.
  4. The UI surfaces orchestration outcomes as product features rather than brittle DevUI-only internals.
**Plans**: 3 plans

Plans:
- [x] 05-01: Design the operator workbench shell, message surfaces, and layout system
- [x] 05-02: Build traces, per-agent tabs, and artifact views into the product UI
- [x] 05-03: Refine visual polish, interaction quality, and operator ergonomics

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Workspace and Durable Run Foundation | 3/3 | Complete | 2026-03-21 |
| 2. Manager-Led Orchestration Core | 3/3 | Complete | 2026-03-21 |
| 3. Specialist Delegation and Routing Visibility | 3/3 | Complete | 2026-03-21 |
| 4. Autonomous Repo Execution and Validation Guardrails | 3/3 | Complete | 2026-03-21 |
| 5. Polished Operator Workbench | 3/3 | Complete | 2026-03-22 |
