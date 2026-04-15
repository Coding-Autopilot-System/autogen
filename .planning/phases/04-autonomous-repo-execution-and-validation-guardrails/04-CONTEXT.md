# Phase 4: Autonomous Repo Execution and Validation Guardrails - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Turn the current manager-led orchestration runtime into a safe default-doer for repo work. This phase covers autonomous file edits inside the selected repo or worktree, durable change artifacts, targeted local validation execution, and explicit approval gates for destructive or externally visible actions. It does not add final product-grade UI styling, automatic branch or worktree isolation, or cloud-hosted worker execution.

</domain>

<decisions>
## Implementation Decisions

### Autonomous edit surface
- Autonomous runs should write directly inside the operator-selected repo or worktree. Phase 4 does not add automatic branch creation or scratch worktree cloning by default.
- Routine safe repo edits should run without per-step approval when they stay under the selected repo root and are represented as structured file operations the runtime can record.
- Repo editing should stay manager-owned at the run level. Specialists can propose or perform changes, but the durable run record remains the canonical source of file-operation history.
- Commands or actions that write outside the selected repo, mutate global tool state, or depend on uncontrolled shell side effects are not routine safe actions in this phase.

### Change artifacts and operator inspection
- Every implementation-capable run must persist a changed-file list, per-file operation records, and a unified diff artifact that the operator can inspect after the run or per stage.
- Change artifacts should be grouped by attempt and by stage so the operator can distinguish the latest implementation pass from earlier retries.
- The artifact manifest remains the canonical index. New change-capture files should be attached there instead of inventing a parallel artifact registry.
- Operator-facing summaries should show changed files and high-level file outcomes first, then allow drill-down into diffs and write-operation details.

### Validation runner policy
- After implementation work, the system should automatically run targeted local validation commands chosen from repo context, changed files, and stack hints.
- Validation should execute as a ladder: fast targeted checks first, then broader repo-level validation only when touched files or failure signals justify escalation.
- Each validation record must capture command, working directory, exit code, duration, and summarized stdout or stderr so results are machine-readable and operator-readable.
- Validation failure must never be silently treated as success. Failed validation should pause the run with retryable or blocked state and attach the failing results for inspection.

### Approval guardrails
- Approval should be reserved for destructive or externally visible actions, not ordinary repo file edits or local validation commands.
- Destructive actions include file deletion or move with data-loss risk, writes outside the selected repo or worktree, git history mutation, and reset or cleanup style operations.
- Externally visible actions include deploys, cloud or API side effects, git push or PR creation, package publishing, notification sends, and commands that start or stop shared services.
- When approval is required, the operator should see exact scope: intended action, affected files or resources, why approval is required, and what will happen if approved.

### the agent's Discretion
- Exact internal representation of file-operation records as long as file path, operation type, and before/after or diff references stay durable.
- Exact validation command-selection heuristics as long as the ladder stays targeted-first and broader checks are justified by changed files or failure signals.
- Exact UI presentation of change artifacts and approval cards before the final operator workbench polish lands in Phase 5.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and phase scope
- `.planning/PROJECT.md` - defines the product as a local-first multi-agent coding workbench and locks "safe default-doer" behavior as an active requirement.
- `.planning/REQUIREMENTS.md` - defines `EXEC-01`, `EXEC-02`, `EXEC-03`, and `EXEC-04`, which Phase 4 must satisfy.
- `.planning/ROADMAP.md` - defines the fixed Phase 4 boundary, success criteria, and plan split.
- `.planning/STATE.md` - records the current focus, current blockers, and prior phase decisions that Phase 4 must extend.
- `.planning/phases/03-specialist-delegation-and-routing-visibility/03-CONTEXT.md` - locks the manager-owned run model, route-lane contract, and operator tabs that Phase 4 must build on.

### Runtime execution seams
- `maf_core/orchestration.py` - defines the canonical stage model, pause kinds, specialist state, and stage artifact paths that Phase 4 write and validation records should extend.
- `maf_core/tools.py` - defines the current repo-tool boundary and the only active approval seam, which Phase 4 must evolve from read-only inspection into safe write and validation capabilities.
- `maf_core/provider_fallback.py` - defines provider fallback, capability drift, and CLI tool-loss behavior that Phase 4 must respect when write or validation actions depend on tool availability.
- `autogen_dashboard/session_runner.py` - is the active run coordinator for manager stages, artifact persistence, pause semantics, and route metadata projection.
- `autogen_dashboard/session_store.py` - owns the durable run directory layout, artifact manifest, stage outputs, workspace snapshot storage, and attempt summaries that new change and validation artifacts must use.
- `autogen_dashboard/schemas.py` - defines the operator-facing session, artifact, routing, and stage payload shapes that Phase 4 must extend rather than bypass.

### Architecture and validation guidance
- `.planning/codebase/ARCHITECTURE.md` - maps the active runtime layers, tool boundary, and persistence seams where Phase 4 work belongs.
- `.planning/codebase/STRUCTURE.md` - identifies where shared runtime changes belong versus legacy paths that should not become the new default.
- `.planning/codebase/CONVENTIONS.md` - captures the explicit error-handling, typing, and module-boundary patterns the phase should preserve.
- `.planning/codebase/TESTING.md` - documents the active local verification commands and test style that Phase 4 validation and approval work should extend.
- `README.md` - documents the current MAF-first runtime, current approval model, and fallback chain that Phase 4 will deepen.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `maf_core/tools.py`: already constrains repo access to the selected repo root and exposes the current approval boundary through `request_human_approval`.
- `maf_core/orchestration.py`: already provides shared stage state, pause kinds, specialist records, and stage artifact path helpers that can anchor write and validation metadata.
- `autogen_dashboard/session_store.py`: already persists attempt summaries, stage outputs, workspace snapshots, and an artifact manifest under stable per-run directories.
- `autogen_dashboard/session_runner.py`: already owns manager-stage execution, pause and retry semantics, route metadata persistence, and the projection of run state into operator-facing session summaries.
- `autogen_dashboard/repo_context.py`: already captures dirty state and changed-file summaries, which can seed later change-capture comparisons.
- `maf_core/provider_fallback.py`: already records route attempts and capability drift so Phase 4 can tell when a fallback lost tool support before write or validation work starts.

### Established Patterns
- Durable run state is file-backed under `state/sessions/<run-id>/` with JSON and JSONL artifacts plus a manifest file that indexes available outputs.
- The manager remains the canonical run owner; specialist activity is visible, but stage control, pause, and retry semantics are centralized.
- Provider fallback is API-first and can degrade from tool-capable API clients to CLI providers that do not support structured tools.
- Approval today is expressed through one explicit approval boundary. Phase 4 should formalize policy around that seam rather than scattering approval logic across ad hoc calls.

### Integration Points
- `maf_core/tools.py` is the primary seam for adding controlled write tools, diff helpers, and validation runners bounded to the selected repo.
- `autogen_dashboard/session_runner.py` is the primary seam for invoking write and validation actions during implementation and validation stages while preserving durable pause and retry behavior.
- `autogen_dashboard/session_store.py` and `autogen_dashboard/schemas.py` are the primary seams for attaching change artifacts, validation records, and approval-scope details to runs.
- `autogen_dashboard/static/app.js` and the existing operator tabs are the natural surface for changed-file summaries, diffs, validation results, and approval scope cards once backend artifacts exist.

</code_context>

<specifics>
## Specific Ideas

- One prompt should lead to real repo edits and real validation, not approval prompts for every routine step.
- Diffs and validation results should be product features with durable artifacts, not only shell output or temporary transcript text.
- CLI fallback can remain a resilience path, but Phase 4 guardrails should make tool loss explicit before any write or validation action is attempted.
- The write, diff, validation, and approval records created here should stay machine-readable so a later Azure Function or REST surface can reuse the same contract.

</specifics>

<deferred>
## Deferred Ideas

- Automatic per-run branch or worktree isolation by default - belongs with later `SAFE-01` collaboration and isolation work
- Cloud-hosted worker execution and Azure Function or REST exposure of repo-editing runs - belongs with later API and Azure Function phases
- Final polished diff viewer styling, message surfaces, and operator-grade visual system - belongs in Phase 5

</deferred>

---

*Phase: 04-autonomous-repo-execution-and-validation-guardrails*
*Context gathered: 2026-03-21*
