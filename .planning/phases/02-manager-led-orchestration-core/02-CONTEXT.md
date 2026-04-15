# Phase 2: Manager-Led Orchestration Core - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the usable one-prompt manager workflow and explicit orchestration state model. This phase covers the manager-owned stage machine, structured pause and resume semantics, automatic handling of routine GSD clarification questions, and consistent run-stage visibility across the active runtime. It does not yet require polished per-agent tabs, final product UI styling, or autonomous repo editing beyond the orchestration contract.

</domain>

<decisions>
## Implementation Decisions

### Manager workflow and stage model
- The manager owns one canonical stage sequence for normal engineering runs: `planning -> research -> implementation -> review -> validation`.
- A run remains one durable run record while stages advance internally; stage outputs are nested artifacts of that one run rather than separate runs or loose chat turns.
- Stage transitions are manager-controlled based on structured stage outputs and run state, not on unstructured transcript cues alone.
- Phase 2 should keep specialist execution behind the manager boundary. The operator needs clear stage visibility now, while deeper per-specialist presence and live handoff views remain Phase 3 work.

### Pause, resume, and retry semantics
- Pause reasons must be explicit and structured: `needs_input`, `needs_approval`, `blocked`, `retryable_error`, `completed`, and `stopped`.
- Resume continues from the paused stage with prior stage outputs, artifacts, and approvals intact instead of replaying the full workflow by default.
- The main approval gates for Phase 2 are stage-level orchestration gates: after planning when execution would change code or config, and after review or validation when operator confirmation is needed. Tool-level risky action approvals still remain in effect underneath.
- Retry should be stage-scoped by default. Re-running one failed or blocked stage must preserve successful prior stages unless the operator explicitly starts a fresh attempt.

### Automatic GSD clarification handling
- Routine GSD clarification and planning questions should be answered automatically from a prioritized context bundle: `PROJECT.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `STATE.md`, prior phase context, current phase context, workspace snapshot, and repo inspection results.
- Automatic answering is allowed for routine clarification, planning defaults, and common execution assumptions, but not for product-direction changes, destructive approvals, or ambiguous scope changes.
- Auto-answered GSD decisions must be recorded as structured run artifacts and events so the operator can inspect what was answered automatically and why.
- When the manager cannot answer confidently from available context, it must pause with a concise missing-information summary and suggested options instead of silently guessing.

### Operator-visible orchestration state
- The active implementation seam for Phase 2 is a shared orchestration state contract in the MAF runtime, mirrored into the existing operator-facing run API and persistence model rather than buried only inside DevUI.
- The operator surface for Phase 2 should expose a compact but explicit orchestration view: current stage, overall run status, last completed stage, active pause reason, and links or summaries for stage outputs.
- The runtime must emit structured orchestration events such as `run.started`, `stage.started`, `stage.completed`, `stage.paused`, `stage.blocked`, `run.completed`, and `run.failed`, alongside the existing transcript and provider-route metadata.
- The same canonical run and stage statuses must be reused across MAF execution, persisted run state, and operator-facing API responses so the system has one orchestration vocabulary.

### the agent's Discretion
- Exact internal representation of stage summaries and artifact filenames as long as each stage has a clearly retrievable persisted output.
- Exact heuristics used to decide when a question is safe to auto-answer versus when it must trigger `needs_input`.
- Exact temporary UI treatment of the stage banner, pause banner, and stage timeline before the polished workbench lands in Phase 5.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and phase scope
- `.planning/PROJECT.md` - defines the product as a local-first orchestration workbench and makes manager-led one-prompt execution the primary interaction model.
- `.planning/REQUIREMENTS.md` - defines `ORCH-01`, `ORCH-02`, `ORCH-03`, and `ORCH-04`, which Phase 2 must satisfy.
- `.planning/ROADMAP.md` - defines the fixed Phase 2 boundary, goal, success criteria, and plan stubs.
- `.planning/STATE.md` - records the active focus, prior decisions, and current blockers entering Phase 2.
- `.planning/phases/01-workspace-and-durable-run-foundation/01-CONTEXT.md` - defines the locked run identity, workspace freshness, and operator-visible run contract that Phase 2 must build on instead of replacing.

### Current runtime and operator constraints
- `README.md` - documents the current MAF-first runtime, `repo_team` workflow, fallback behavior, and current HITL boundary.
- `docs/DEVUI_CUSTOMIZATION.md` - defines DevUI as a local engineering console rather than the final product UI, which constrains Phase 2 to backend and contract work instead of over-investing in DevUI.
- `.planning/codebase/ARCHITECTURE.md` - maps the active runtime layers, shared seams, and current split between MAF execution and legacy operator state.
- `.planning/codebase/STRUCTURE.md` - identifies where new orchestration code should live and which modules are shared versus legacy.
- `.planning/codebase/CONVENTIONS.md` - captures the current Python, error-handling, and module-organization patterns the phase should preserve.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `maf_core/team_factory.py`: already builds a sequential `planner -> researcher -> implementer -> reviewer` workflow with request-info pauses after key specialist stages.
- `maf_core/workflow_factory.py`: already provides checkpointed workflow construction, which is the best current seam for persisting stage progress.
- `maf_core/agent_factory.py`: already centralizes active-agent instructions and is the natural place to formalize the manager role.
- `maf_core/tools.py`: already exposes repo inspection tools and a mandatory-approval boundary for risky actions.
- `maf_core/provider_fallback.py`: already attaches route and capability metadata to responses; the orchestration layer can extend this with stage metadata instead of inventing a parallel trace format.
- `autogen_dashboard/session_runner.py`: already has explicit run status, pause reasons, background execution, workspace refresh, and structured event emission.
- `autogen_dashboard/schemas.py`: already models stable run summaries, pause fields, workspace metadata, and attempt metadata that can absorb stage-level orchestration state.

### Established Patterns
- MAF is the active execution engine, but the strongest operator-facing run contract currently lives in the legacy dashboard persistence layer.
- File-backed run directories and JSON or JSONL event streams are already the accepted local durability model.
- Provider fallback can preserve conversational continuity, but CLI fallback can lose tool-calling capability; orchestration state must record that capability drift clearly.
- DevUI is useful for local inspection, but the durable orchestration contract should live in shared Python services and persisted run state first.

### Integration Points
- `main.py` and `maf_core/cli.py` are the bootstrap seam for any shared orchestration service or manager entrypoint.
- `entities/repo_copilot_workflow` and `entities/repo_team` are the current MAF entity seams that can be promoted into manager-led workflows instead of staying as disconnected demos.
- `autogen_dashboard/app.py` and `autogen_dashboard/session_runner.py` are the best existing operator-facing API seams for exposing current stage, pause reasons, and stage outputs.
- `maf_core/provider_fallback.py` and `maf_core/devui_patches.py` are the current metadata seams that can carry stage identifiers and route rationale into traces.

</code_context>

<specifics>
## Specific Ideas

- One engineering prompt should start a manager run, not a single-turn copilot response.
- The operator should primarily see stage progress and decisions in Phase 2, not raw specialist chatter.
- Automatic GSD answering should feel like the system is reading the project and phase docs on the operator's behalf, then only asking when real ambiguity remains.
- Approval should happen at meaningful orchestration boundaries, not on every internal handoff.

</specifics>

<deferred>
## Deferred Ideas

- Rich per-agent tabs, specialist live panes, and fully transparent handoff views - Phase 3 and Phase 5
- Fully polished message bubbles, rounded conversation surfaces, and final product-grade operator shell - Phase 5
- Autonomous repo editing and local validation as the default execution mode - Phase 4
- Azure Function and REST exposure of the orchestration core - later cloud phase, not Phase 2

</deferred>

---

*Phase: 02-manager-led-orchestration-core*
*Context gathered: 2026-03-21*
