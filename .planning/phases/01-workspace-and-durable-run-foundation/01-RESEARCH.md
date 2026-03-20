# Phase 1: Workspace and Durable Run Foundation - Research

**Researched:** 2026-03-20
**Domain:** Local-first workspace selection, durable run state, and operator-facing run lifecycle for the in-repo MAF workbench
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Every run starts from an explicit repo or worktree selection; no hidden global workspace assumption.
- Selectable workspaces are git repositories inside the configured scan root, with manual path entry allowed only inside that root.
- The workspace picker must show repo root, branch, dirty state, stack hints, and recent commits before execution.
- Each run must have a stable run ID, durable history, explicit statuses, explicit pause reasons, and persisted artifacts.
- Resume continues the same run; retry stays attached to the same run history as a new attempt.
- Original operator task and later approval or rejection notes must be stored separately.
- Repo context must be visible in the operator surface and refreshed at creation, run start, resume, retry, and stage boundaries.

### the agent's Discretion
- Exact on-disk file naming inside each run directory
- Exact temporary UX treatment of the workspace summary and run header
- Exact timestamp and badge wording for status, attempts, and stale-workspace warnings

### Deferred Ideas (OUT OF SCOPE)
- None

</user_constraints>

<research_summary>
## Summary

Phase 1 should not try to turn DevUI itself into a durable workbench. The active MAF path is still optimized for one configured repo root plus checkpointed agent execution, while the legacy dashboard already has the stronger operator-facing primitives: explicit repo discovery, stable session IDs, per-session folders, append-only events, resumable state, retry, and SSE updates.

The strongest Phase 1 path is to promote those legacy run-management patterns into the active runtime boundary rather than hand-rolling a second durability system inside DevUI. In practice that means: add a shared run contract above the active MAF runtime, make repo or worktree selection a run-level concern instead of a startup-only env var, preserve one dedicated run directory per operator run, and keep checkpoints, transcript, events, and artifacts tied to that stable run identity.

**Primary recommendation:** Use the legacy repo picker, session store, and session event model as the foundation for Phase 1, while keeping MAF as the execution engine behind that shared run contract.
</research_summary>

<standard_stack>
## Standard Stack

The established in-repo stack for this phase is not a new library choice. It is a consolidation choice around components already present in the codebase.

### Core
| Library / Module | Version | Purpose | Why Standard Here |
|---------|---------|---------|--------------|
| `agent-framework` | `1.0.0rc5` | Active orchestration runtime | Already powers the live entities and workflow/checkpoint seam |
| `agent-framework-devui` | `1.0.0b260319` | Local engineering console | Useful for debugging, but should stay a local surface rather than become the durable run model |
| `autogen_dashboard/session_store.py` | in-repo | Per-session file storage | Already stores metadata, transcript, events, and saved state with atomic writes |
| `autogen_dashboard/repo_context.py` | in-repo | Repo discovery and repo summary scan | Already supports scan-root enforcement and workspace summaries |
| `autogen_dashboard/schemas.py` | in-repo | Typed run and repo models | Already captures explicit status, pause, attempt, and repo-context fields |

### Supporting
| Library / Module | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `FastAPI` via `autogen_dashboard/app.py` | existing env | Operator-facing API and SSE stream | Use as the current best local API seam for run lifecycle work |
| `FileCheckpointStorage` via `maf_starter/workflow_factory.py` | bundled with Agent Framework | Durable workflow checkpoints | Keep as the MAF execution-state seam, but hang it off the run contract |
| `unittest` via `tests/test_maf_setup.py` | stdlib | Current automated validation baseline | Use for Phase 1 regression coverage before adding broader test layers |
| PowerShell launchers | in-repo | Local operator workflow for DevUI | Reuse for local serving until a better workbench shell replaces them |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Reusing legacy session/event model | Building a brand-new MAF-only run service | Cleaner on paper, but duplicates proven local durability patterns |
| Promoting run identity above MAF | Encoding run state inside DevUI or checkpoint paths only | Faster short term, but weak for operator UX and resumability |
| Explicit workspace picker | One fixed `MAF_REPO_ROOT` | Simpler, but conflicts with the product goal and future isolated worktrees |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```text
state/
|- sessions/<run-id>/
|  |- metadata.json
|  |- transcript.json
|  |- events.jsonl
|  |- runtime/
|  |  |- checkpoint/...
|  |- artifacts/
|     |- workspace.json
|     |- stage-*.json
|     |- validation/
maf_starter/
|- run_*.py            # shared active run contract and execution service
autogen_dashboard/
|- app.py              # current local operator API shell
|- static/             # temporary operator workbench shell
```

### Pattern 1: Shared run contract above the execution engine
**What:** Treat run identity, workspace selection, transcript, events, and artifacts as a first-class service that the execution engine plugs into.
**When to use:** Always. The execution runtime can change, but run lifecycle should remain stable.
**Example:** A run is created from `{workspace, prompt}` first, then the MAF workflow uses that run record rather than inventing a separate identity.

### Pattern 2: Run-level workspace selection, not startup-level workspace selection
**What:** Move repo or worktree targeting from process configuration into run creation.
**When to use:** Whenever the product is supposed to work across multiple repos or worktrees.
**Example:** Keep `MAF_REPO_ROOT` as a fallback default, but let the operator choose a workspace per run and propagate that workspace into repo tools, checkpoint roots, and CLI working directories.

### Pattern 3: Structured human transcript plus machine event stream
**What:** Keep chronological messages for operators and a separate append-only event stream for status, stage, attempts, and machine-readable transitions.
**When to use:** Always for durable operator workflows.
**Example:** `transcript.json` holds human and agent messages, while `events.jsonl` records `run.created`, `stage.started`, `attempt.failed`, `run.completed`, and stale-workspace warnings.

### Anti-Patterns to Avoid
- **Split-brain state:** storing transcript and status in one system while checkpoints live in another without a shared run ID
- **Global repo root as product contract:** fine for a starter, wrong for the intended workbench
- **Approval text as retry target:** approval notes must never overwrite the original run task
- **DevUI as the durable operator surface:** Phase 1 should build reusable run contracts, not couple them to a patch-heavy local debug UI

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that look small but already have strong in-repo solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Repo discovery and workspace summary | A new ad hoc git scanner | `autogen_dashboard/repo_context.py` | Already handles scan-root enforcement, git validation, dirty files, recent commits, and stack hints |
| Per-run file persistence | A custom persistence format from scratch | `autogen_dashboard/session_store.py` shape | Already separates metadata, transcript, events, and saved state cleanly |
| Event streaming | A fresh polling loop | Existing SSE stream pattern in `autogen_dashboard/app.py` | Already models snapshot + incremental event delivery |
| Explicit status and pause model | Deriving state from chat text | Existing `SessionSummary` / `SessionDetail` schema pattern | Already captures pause reasons, attempts, fallback count, and timestamps |
| Workflow checkpoint storage | A second homegrown checkpointing system | `FileCheckpointStorage` under the run contract | Already supported in the active MAF path |

**Key insight:** Phase 1 is mostly a consolidation and promotion exercise. The risk is not missing a new library. The risk is duplicating partially correct run/session concepts in multiple places.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Split-brain run durability
**What goes wrong:** MAF checkpoints and operator-facing run data evolve separately, so resume and retry behave inconsistently.
**Why it happens:** Checkpoint storage exists in `maf_starter`, but operator session identity exists only in the legacy dashboard path.
**How to avoid:** Introduce one shared run ID and make checkpoints, transcript, events, and artifacts all hang off that run directory.
**Warning signs:** Resume works at the agent layer but not at the operator layer, or a run has transcript history without matching execution state.

### Pitfall 2: Retry target corruption
**What goes wrong:** Later approval or rejection notes replace the original task, so retries rerun `APPROVE` instead of the actual work request.
**Why it happens:** The existing legacy flow stores `last_prompt` too aggressively.
**How to avoid:** Store original task, latest human note, latest retry seed, and approval decisions as distinct fields.
**Warning signs:** A reopened run appears healthy, but retry repeats only an approval token or short note.

### Pitfall 3: Workspace drift hidden from the operator
**What goes wrong:** Repo state changes outside the run, but the system keeps acting on stale assumptions.
**Why it happens:** Repo context is captured once and reused without freshness checks.
**How to avoid:** Refresh snapshots at run lifecycle boundaries and raise a visible stale-workspace warning when the repo changed externally.
**Warning signs:** File lists or dirty-state badges in the UI no longer match the actual git state.

### Pitfall 4: Building Phase 1 inside DevUI patches
**What goes wrong:** Core run behavior ends up buried in local UI overrides instead of reusable backend services.
**Why it happens:** DevUI is the current visible shell, so it is tempting to keep layering behavior into the patch surface.
**How to avoid:** Keep run identity, workspace selection, status, and persistence in shared Python services first. Let the UI render those contracts.
**Warning signs:** A DevUI upgrade breaks operator state behavior, not just visual polish.

</common_pitfalls>

<code_examples>
## Code Examples

Verified in-repo patterns worth preserving:

### Repo discovery and summary scan
```python
# Source: autogen_dashboard/repo_context.py
# Pattern: resolve repo root inside a configured scan root,
# validate git repo, then collect branch/dirty/recent-commit summary.
```

### Dedicated per-session directory
```python
# Source: autogen_dashboard/session_store.py
# Pattern: one directory per run/session containing metadata.json,
# transcript.json, events.jsonl, and saved state with atomic writes.
```

### Checkpoint seam in the active MAF path
```python
# Source: maf_starter/workflow_factory.py
# Pattern: workflow execution state persists through FileCheckpointStorage,
# which can be re-rooted under a run-scoped directory.
```

</code_examples>

## Validation Architecture

Phase 1 validation should focus on deterministic workspace and run-state behavior, not open-ended model quality.

- **Primary automated framework:** stdlib `unittest`, extending `tests/test_maf_setup.py`
- **Quick verification target:** focused unit and API tests for repo selection, run ID creation, run-directory persistence, status transitions, and resume/retry semantics
- **Broader verification target:** compile/import smoke checks for touched Python modules plus targeted API smoke tests for the operator surface
- **Manual verification target:** lightweight local operator flow checks only where UI wiring is introduced

Recommended commands once Phase 1 implementation exists:

- Quick: `.\.venv\Scripts\python.exe -m unittest tests.test_maf_setup`
- Quick UI/API smoke: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- Static import sanity: `.\.venv\Scripts\python.exe -m compileall maf_starter autogen_dashboard tests main.py`

Focus the test map on:
- workspace selection stays inside allowed roots
- run creation persists a stable ID and initial workspace snapshot
- transcript and event stream survive resume and retry
- retry does not replace the original task with approval notes
- workspace refresh and stale-workspace warnings behave deterministically

<open_questions>
## Open Questions

1. **Where should the shared run service live?**
   - What we know: `maf_starter` is the active runtime home, but the stronger operator session model is in `autogen_dashboard`.
   - What's unclear: whether to move the legacy session primitives into `maf_starter` or keep a thin dashboard service facade over them.
   - Recommendation: plan for a shared Python service boundary first, then decide whether its module home is `maf_starter` or a small new shared package.

2. **How much of the old dashboard becomes active again in Phase 1?**
   - What we know: the old dashboard already provides repo listing, sessions, SSE, and a repo-aware UI shell.
   - What's unclear: whether Phase 1 should promote that shell immediately or only reuse its service layer.
   - Recommendation: keep the shell reusable, but prioritize shared run and workspace contracts over UI polish.

</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `.planning/PROJECT.md` - product goal, constraints, and operator expectations
- `.planning/REQUIREMENTS.md` - `WKSP-01`, `WKSP-02`, `WKSP-03`
- `.planning/ROADMAP.md` - Phase 1 goal and success criteria
- `.planning/phases/01-workspace-and-durable-run-foundation/01-CONTEXT.md` - locked Phase 1 decisions
- `autogen_dashboard/session_store.py` - existing durable run/session storage pattern
- `autogen_dashboard/session_runner.py` - existing run lifecycle, retry, and event model
- `autogen_dashboard/repo_context.py` - existing repo discovery and repo summary pattern
- `autogen_dashboard/schemas.py` - existing status, pause, and repo-context schema contract
- `autogen_dashboard/app.py` - existing repo/session API and SSE event stream
- `maf_starter/config.py` - current static repo-root and checkpoint configuration seam
- `maf_starter/workflow_factory.py` - current MAF checkpoint storage seam
- `README.md` - current runtime boundary, DevUI boundary, and operator workflow notes
- `docs/DEVUI_CUSTOMIZATION.md` - current DevUI limitation and customization notes

### Secondary (MEDIUM confidence)
- `tests/test_maf_setup.py` - current validation baseline and runtime assumptions
- `start_devui.ps1` and `stop_devui.ps1` - current local operator lifecycle pattern

</sources>

<metadata>
## Metadata

**Research scope:**
- Core runtime: MAF entrypoint and checkpointing
- Operator durability: legacy session store and API
- Workspace awareness: repo scan and repo summary helpers
- Validation: current unittest-based test surface

**Confidence breakdown:**
- Shared run contract recommendation: HIGH - grounded in existing repo code
- Workspace selection strategy: HIGH - directly supported by existing repo context helpers
- Validation strategy: HIGH - grounded in checked-in tests and current runtime commands
- UI implications: MEDIUM - active shell choice remains open even though the service boundary is clear

**Research date:** 2026-03-20
**Valid until:** 2026-04-19

</metadata>

---

*Phase: 01-workspace-and-durable-run-foundation*
*Research completed: 2026-03-20*
*Ready for planning: yes*
