---
phase: 01-workspace-and-durable-run-foundation
plan: 03
subsystem: runtime-ui
tags: [workspace-scope, maf, stale-detection, operator-ui, attempts]
requires:
  - phase: 01-01
    provides: explicit workspace selection and run identity creation
  - phase: 01-02
    provides: durable run directories, attempt history, and reopen/retry semantics
provides:
  - run-scoped MAF repo-root and checkpoint overrides instead of startup-root-only behavior
  - deterministic workspace snapshot refresh with stale-workspace events and operator warnings
  - integration coverage for dynamic repo scope, checkpoint paths, and workspace drift detection
affects: [maf-runtime, dashboard-ui, workspace-freshness, traces, retry-resume]
tech-stack:
  added: []
  patterns:
    - immutable settings clones plus per-invocation run scope
    - workspace drift captured as structured events and operator-facing summary fields
key-files:
  created: []
  modified:
    - maf_core/config.py
    - maf_core/tools.py
    - maf_core/provider_fallback.py
    - maf_core/workflow_factory.py
    - maf_core/team_factory.py
    - maf_core/agent_factory.py
    - autogen_dashboard/schemas.py
    - autogen_dashboard/session_runner.py
    - autogen_dashboard/static/index.html
    - autogen_dashboard/static/app.js
    - autogen_dashboard/static/styles.css
    - tests/test_maf_setup.py
    - tests/test_phase1_api.py
    - tests/test_phase1_runtime.py
    - tests/test_workspace_contract.py
key-decisions:
  - "MAF keeps env-based defaults, but each run can override repo root and checkpoint dir through immutable settings clones."
  - "Repo tools resolve their root from the active run scope instead of a startup-time closure."
  - "Workspace freshness is represented as explicit summary fields plus workspace.refreshed/workspace.stale events."
patterns-established:
  - "Use ContextVar-backed run scope for active repo-root and checkpoint resolution."
  - "Show workspace freshness in the operator header, not only inside raw events or transcript text."
requirements-completed: [WKSP-01, WKSP-02, WKSP-03]
duration: 1 min
completed: 2026-03-21
---

# Phase 01 Plan 03: Workspace and Durable Run Foundation Summary

**Run-scoped MAF workspace propagation plus stale-workspace visibility across the operator surface**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-21T08:05:00Z
- **Completed:** 2026-03-21T08:15:00Z
- **Tasks:** 3
- **Files modified:** 15

## Accomplishments

- The active MAF runtime now supports run-scoped repo-root and checkpoint overrides instead of relying only on startup-time `MAF_REPO_ROOT` and `MAF_CHECKPOINT_DIR`.
- Repo tools now read from the active run scope, and CLI fallback metadata records the workspace root and checkpoint directory used for the turn.
- The dashboard now refreshes workspace snapshots at run boundaries, emits `workspace.refreshed` and `workspace.stale` events, and shows stale-workspace warnings plus attempt metadata directly in the run header.

## Task Commits

Each task was committed atomically:

1. **Task 1: Make the active MAF runtime run-scoped instead of startup-root scoped** - `15d5a0d` (`feat`)
2. **Task 2: Add workspace snapshot refresh, stale warnings, and operator visibility** - `47b6b3a` (`feat`)
3. **Task 3: Lock run-scoped workspace behavior with integration tests and smoke checks** - `c523062` (`test`)

## Files Created/Modified

- `maf_core/config.py` - immutable run-scoped settings helpers plus active repo/checkpoint scope management.
- `maf_core/tools.py` - dynamic repo-tool root resolution from the active run scope.
- `maf_core/provider_fallback.py` - run-scope extraction from middleware context plus workspace/checkpoint trace metadata.
- `maf_core/workflow_factory.py` - run-scoped checkpoint storage wrapper for workflow execution.
- `maf_core/team_factory.py` - team workflow checkpoint storage aligned to run-scoped paths.
- `maf_core/agent_factory.py` - explicit helper for building run-scoped agents from a settings clone.
- `autogen_dashboard/schemas.py` - workspace freshness, last-checked, and drift-field summary fields.
- `autogen_dashboard/session_runner.py` - snapshot refresh, stale detection, workspace events, and run-start runtime path metadata.
- `autogen_dashboard/static/index.html` - dedicated workspace warning surface in the header area.
- `autogen_dashboard/static/app.js` - stale banner rendering, attempt chips, and workspace freshness normalization.
- `autogen_dashboard/static/styles.css` - rounded warning banner styling for stale workspace state.
- `tests/test_maf_setup.py` - MAF run-scope and middleware metadata regression coverage.
- `tests/test_phase1_api.py` - API payload checks for workspace freshness fields.
- `tests/test_phase1_runtime.py` - stale-workspace and dynamic checkpoint-root runtime tests.
- `tests/test_workspace_contract.py` - compatibility update for queued run status.

## Decisions Made

- Run scope is a first-class concept with defaults from env and per-run overrides at execution time.
- Workspace drift is treated as structured machine state, not inferred later from transcript text.
- The operator surface now shows attempt and freshness context near the run header so the user does not need raw event logs to understand repo drift.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Reused the dashboard session summary as the latest workspace snapshot instead of inventing a second snapshot model**
- **Found during:** Task 2
- **Issue:** A second snapshot model would have duplicated state and made stale comparisons harder to reason about.
- **Fix:** `workspace_snapshot` remains the latest persisted snapshot, while stale status, drift fields, and last-checked time live as explicit summary fields.
- **Impact:** Lower complexity without reducing operator visibility.

---

**Total deviations:** 1 auto-fixed (1 design simplification)
**Impact on plan:** The fix reduced duplication and aligned with the plan intent.

## Issues Encountered

None.

## User Setup Required

None - the existing local repo scan root and state folders continue to work.

## Verification

- `.\.venv\Scripts\python.exe -m unittest tests.test_phase1_runtime tests.test_maf_setup tests.test_phase1_api tests.test_run_persistence -v`
- `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- `.\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py`
- `node --check autogen_dashboard\static\app.js`

## Next Phase Readiness

- Phase 2 can now build the manager-led stage machine on one stable workspace/run contract instead of mixing startup-global runtime assumptions with per-run operator state.
- The new workspace freshness events and run-scoped runtime metadata give the orchestration layer a stable place to attach stage and specialist traces next.

---
*Phase: 01-workspace-and-durable-run-foundation*
*Completed: 2026-03-21*
