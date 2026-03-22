---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: cloud-api-and-azure-function-hosting
status: ready
stopped_at: Phase 6 context gathered
last_updated: "2026-03-22T19:11:41+02:00"
last_activity: 2026-03-22 - Phase 6 context gathered
progress:
  total_phases: 8
  completed_phases: 5
  total_plans: 24
  completed_plans: 15
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-22)

**Core value:** You can give one prompt and watch a trustworthy multi-agent coding system drive real repo work end-to-end with clear traces, specialist visibility, and minimal manual intervention.
**Current focus:** Phase 6 context gathered - ready for planning

## Current Position

Phase: 06 (api-boundary-and-control-plane-contract) - READY TO PLAN
Plan: -
Status: Phase context captured and ready for plan-phase
Last activity: 2026-03-22 - Phase 6 context gathered

## Performance Metrics

**Velocity:**

- Total plans completed: 15
- Average duration: 1 min
- Total execution time: 0.3 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 3 | 3 min | 1 min |
| 02 | 3 | 3 min | 1 min |
| 03 | 3 | 3 min | 1 min |
| 04 | 3 | 3 min | 1 min |
| 05 | 3 | 3 min | 1 min |

**Recent Trend:**

- Last 5 plans: 04-02 (1 min), 04-03 (1 min), 05-01 (1 min), 05-02 (1 min), 05-03 (1 min)
- Trend: Stable

| Phase 01 P01 | 1 min | 2 tasks | 8 files |
| Phase 01 P02 | 1 min | 3 tasks | 7 files |
| Phase 01 P03 | 1 min | 3 tasks | 15 files |
| Phase 02 P01 | 1 min | 3 tasks | 7 files |
| Phase 02 P02 | 1 min | 3 tasks | 7 files |
| Phase 02 P03 | 1 min | 3 tasks | 6 files |
| Phase 03 P01 | 1 min | 4 tasks | 4 files |
| Phase 03 P02 | 1 min | 4 tasks | 8 files |
| Phase 03 P03 | 1 min | 4 tasks | 6 files |
| Phase 04 P01 | 1 min | 3 tasks | 8 files |
| Phase 04 P02 | 1 min | 3 tasks | 8 files |
| Phase 04 P03 | 1 min | 3 tasks | 18 files |
| Phase 05 P01 | 1 min | 3 tasks | 4 files |
| Phase 05 P02 | 1 min | 3 tasks | 5 files |
| Phase 05 P03 | 1 min | 3 tasks | 6 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Initialization: Keep Microsoft Agent Framework as the active runtime base
- Initialization: Treat the product as a local-first orchestration workbench
- Initialization: Defer Azure Function and REST exposure until after the local runtime is stable
- Phase 01-01: Require an explicit repo or worktree root before any run can be created
- Phase 01-01: Use `/api/repos` as the source of truth for the preflight workspace summary card
- Phase 01-02: Retry stays attached to one stable run id and starts a fresh attempt directory instead of a fresh run
- Phase 01-02: Store original task, human notes, approval decisions, and retry seed as separate persisted fields
- Phase 01-03: MAF runtime defaults stay in env, but each run can override repo root and checkpoint dir immutably
- Phase 01-03: Workspace freshness is an explicit run contract with stale events and operator-facing warnings
- Phase 02 planning: Use one canonical manager stage sequence `planning -> research -> implementation -> review -> validation`
- Phase 02 planning: Make stage-scoped pause, resume, and retry part of the durable run contract instead of transcript-only behavior
- Phase 02 planning: Answer routine GSD clarification questions automatically from planning docs, phase context, workspace snapshot, and repo facts
- Phase 02-01: Canonical stage state lives in `maf_starter/orchestration.py` and is shared by workflow builders and dashboard runtime
- Phase 02-02: Planning pauses after plan output, while blocked or failed later stages resume from the same stage without replaying completed work
- Phase 02-03: Operator-facing orchestration visibility is exposed through dashboard cards and API payloads, not only raw traces
- Phase 03 context: Keep the manager as the only canonical run owner while surfacing `planner`, `researcher`, `implementer`, and `reviewer` as first-class visible specialists
- Phase 03 context: Route control should be lane-first with advanced model pinning, using API-first fallbacks and CLI providers last unless explicitly pinned
- Phase 03 context: Routing and specialist behavior should be exposed through dedicated operator views and route cards rather than transcript text or DevUI traces alone
- Phase 03 planning: Split execution into parallel wave 1 tracks for specialist-state contract (`03-01`) and route contract (`03-02`), then merge them in wave 2 through the operator surface (`03-03`)
- Phase 03 planning: Keep specialist and routing visibility on the dashboard product surface rather than deepening DevUI as the primary UI
- Phase 03 planning: Treat route lanes as the main operator control, with advanced model pinning and planned-versus-actual route history persisted per run
- Phase 03-01: Specialist state and handoff metadata live in the shared orchestration contract and are projected into workflow metadata directly
- Phase 03-02: Route lanes and fallback capability drift are durable run data, not transient trace-only output
- Phase 03-03: The dashboard operator surface is organized into Overview, Agents, Routing, and Artifacts tabs so operator context is visible without raw logs
- Phase 04 context: Autonomous runs should write directly inside the selected repo or worktree; automatic branch or worktree isolation stays deferred
- Phase 04 context: Each implementation-capable run should persist changed-file lists, operation records, and unified diff artifacts under the run manifest
- Phase 04 context: Validation should run as a targeted ladder and record command, cwd, exit code, duration, and output summary
- Phase 04 context: Approval is reserved for destructive or externally visible actions with explicit scope and reason
- Phase 04 planning: Execute the phase as a sequential safety chain of write capture, validation recording, then approval enforcement
- Phase 04 planning: Extend the existing run artifact manifest and pause semantics instead of creating a parallel execution store or approval queue
- Phase 04-01: Routine-safe writes execute through a shared repo-execution service that captures changed files, operation records, and unified diffs
- Phase 04-02: Validation runs as a bounded local ladder with durable command/result artifacts and retryable failure pauses
- Phase 04-03: Approval policy is now centralized and operator-visible, and the local MAF layer is aligned to the installed SDK primitives for reliable regression coverage
- Phase 05 context: `autogen_dashboard` is the primary product UI; DevUI remains useful only as a framework console
- Phase 05 planning: Preserve the warm rounded visual system and upgrade the existing shell instead of rewriting the frontend
- Phase 05-01: Route, model, and stage context now render in dedicated active-run strips and actor-specific message families
- Phase 05-02: Timeline, Agents, Routing, and Artifacts views are driven by structured events, route attempts, diffs, and validation payloads
- Phase 05-03: The workbench now emphasizes the active run, secondary create-run affordances, and operator notices for pause, retry, and completion states
- Milestone v1.1: Continue phase numbering from 6 instead of resetting roadmap numbering
- Milestone v1.1: Use Azure Functions as the cloud control-plane host and keep long-running repo execution behind a worker boundary
- Milestone v1.1: Keep the Operator Workbench and the external HTTP API on one shared orchestration contract

### Pending Todos

None yet.

### Blockers/Concerns

- The repo still contains overlapping MAF and legacy AutoGen runtime paths
- DevUI customization is useful locally but too brittle to treat as the final product UI
- Provider fallback capability drift and secret exposure need early hardening
- `azd` is not installed locally, so milestone work should rely on Azure Functions Core Tools, Azure CLI, and deployment-ready packaging instead of `azd` as a hard prerequisite
- Local Python is `3.14.2`, but Azure Functions hosted deployment work should target GA-supported Python such as `3.13` or `3.12`
- A cloud-hosted control plane cannot assume local CLI logins, desktop-bound tooling, or direct repo access unless a compatible worker is attached

## Session Continuity

Last session: 2026-03-22T19:11:41+02:00
Stopped at: Phase 6 context gathered
Resume file: .planning/phases/06-api-boundary-and-control-plane-contract/06-CONTEXT.md
