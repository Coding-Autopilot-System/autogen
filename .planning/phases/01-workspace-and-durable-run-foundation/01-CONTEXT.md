# Phase 1: Workspace and Durable Run Foundation - Context

**Gathered:** 2026-03-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Create the run and workspace contract that all later orchestration builds on. This phase covers repo or worktree selection, durable run identity, persisted transcript and artifacts, and visible workspace context. It does not add new orchestration capabilities beyond establishing the foundation that later phases will use.

</domain>

<decisions>
## Implementation Decisions

### Workspace targeting and run entry
- Every run starts from an explicit repo or worktree selection. The system must not rely on one hidden global repo root for operator-facing runs.
- Selectable workspaces are git repositories inside the configured scan root. Manual path entry is acceptable only when the chosen directory still resolves inside that allowed root.
- The workspace picker should show repo name, absolute root, branch, dirty or clean status, stack hints, and recent commits before the run starts.
- The UI should remember recent and last-used workspaces for speed, but the current selection remains visible and changeable before execution.

### Run identity and lifecycle
- Each run gets a stable run ID at creation time and keeps one durable history across pauses, resumes, and retries.
- Each run also has an operator-facing title. The default title should be derived from the prompt or task plus workspace context, but the operator can edit it later.
- Resume continues the same run and keeps prior transcript, events, artifacts, and latest saved state intact.
- Retry should stay attached to the same run history as a new attempt on the timeline, not create an unrelated session by default.
- The original operator task and later approval or rejection notes must be stored separately so retry targets never degrade into `APPROVE` or `REJECT` text.
- The status model should be explicit and user-facing from the start: queued, running, waiting, completed, error, and stopped.
- Pause and stop reasons should be explicit and structured, not inferred only from raw text.

### Persisted run record and artifacts
- Each run stores metadata, transcript, event stream, saved state or checkpoint, and generated artifacts in one dedicated run directory.
- Human, manager, and specialist messages belong in a single chronological transcript, while machine-readable events stay in a parallel structured stream.
- Artifact categories visible from the start should include workspace snapshot, stage summaries, approvals, changed-file or diff outputs, and validation results.
- The system should save on run creation, each stage transition, each human decision, and each completion, error, or stop boundary.
- Local JSON and JSONL storage under `state/` is acceptable for v1 as long as schemas stay explicit and migration-friendly.

### Workspace snapshot and freshness
- Capture a workspace snapshot at run creation and refresh it at run start, resume, retry, and each major stage boundary.
- A snapshot should include repo root, branch, dirty flag, changed files, recent commits, and stack hints.
- If the underlying workspace changes outside the run between snapshots, the run should show a stale-workspace warning instead of silently assuming the old snapshot is still valid.
- Repo context must be visible in the operator surface and persisted with the run, not only injected into model prompts.
- Phase 1 only needs concise git summaries and changed-file lists. Full diff capture can remain a later artifact feature.

### the agent's Discretion
- Exact file naming inside the per-run directory as long as metadata, transcript, events, and artifacts remain clearly separated.
- Exact visual treatment of the workspace summary and run header in the temporary operator surface.
- Exact timestamp formatting, relative-time display, and badge wording for status and pause reasons.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and phase scope
- `.planning/PROJECT.md` - defines the product as a local-first multi-agent orchestration workbench, the primary operator, and the autonomy goals.
- `.planning/REQUIREMENTS.md` - defines `WKSP-01`, `WKSP-02`, and `WKSP-03`, which this phase must satisfy.
- `.planning/ROADMAP.md` - defines the fixed Phase 1 boundary, goal, success criteria, and plan stubs.
- `.planning/STATE.md` - records current blockers and confirms Phase 1 is the active focus.

### Current runtime constraints
- `README.md` - documents the current MAF-first entrypoint, DevUI boundary, fallback behavior, and current local workflow assumptions.
- `docs/DEVUI_CUSTOMIZATION.md` - documents that DevUI is a local engineering console and not the final product UI.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `autogen_dashboard/repo_context.py`: already discovers local repos under a scan root, validates git repos, and builds repo summaries with branch, dirty state, stack hints, changed files, and recent commits.
- `autogen_dashboard/session_store.py`: already persists one session per directory with `metadata.json`, `transcript.json`, `events.jsonl`, and a saved state file using atomic writes.
- `autogen_dashboard/session_runner.py`: already implements stable session IDs, queue or run or retry behavior, pause reasons, background runs, event emission, and repo-context refresh hooks.
- `autogen_dashboard/schemas.py`: already models repo options, repo context, session summary, session detail, transcript entries, and structured events.
- `autogen_dashboard/app.py`: already exposes a usable API surface for repo listing, session CRUD-like operations, and event streaming over SSE.
- `maf_starter/config.py`: already defines the active repo root, entities directory, checkpoint directory, and fallback settings boundary.
- `maf_starter/workflow_factory.py`: already defines the checkpoint storage seam for the active MAF workflow path.

### Established Patterns
- Paths and provider behavior are configured through environment variables and repo-local config rather than hard-coded values.
- Local durable state is file-backed under `state/` using explicit JSON and JSONL files with atomic replace semantics where possible.
- Repo access is expected to stay inside configured roots and is already guarded in both the MAF tool layer and the legacy dashboard repo helpers.
- The current product is local-first and Windows-first, with loopback HTTP surfaces and local log files rather than production hosting assumptions.

### Integration Points
- `main.py` dispatches to `maf_starter/cli.py`, so any durable run contract must either be exposed there or wrapped behind a shared service boundary.
- `entities/` exposes MAF agents and workflows, but those entities do not yet own a stable operator-facing run identity or artifact model.
- The active MAF path currently binds one startup-time `MAF_REPO_ROOT`; Phase 1 needs a run-level workspace concept above that static configuration.
- `state/maf-checkpoints` and `state/sessions/` are the two current persistence roots that Phase 1 should reconcile or clearly separate.
- The legacy `/api/repos`, `/api/sessions`, and `/api/sessions/{id}/events` surface is the strongest existing starting point for repo-aware durable run management.

</code_context>

<specifics>
## Specific Ideas

- Use the richer legacy session model as the starting contract for durable runs, even if the long-term UI later moves away from the old dashboard shell.
- Keep one-prompt run creation as the primary operator action: choose workspace, enter prompt, create run, then continue from the run identity instead of stateless chat turns.
- Keep DevUI usable as a local engineering console, but do not make DevUI-specific rendering rules the core run model.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 01-workspace-and-durable-run-foundation*
*Context gathered: 2026-03-20*
