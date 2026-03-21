---
phase: 01-workspace-and-durable-run-foundation
plan: 01
subsystem: ui
tags: [workspace-selection, repo-discovery, run-creation, dashboard, fastapi]
requires: []
provides:
  - explicit workspace discovery under the configured scan root
  - run creation that requires both a workspace and an engineering prompt
  - persisted workspace snapshot fields on the run contract
affects: [operator-ui, run-contract, repo-context, later-runtime-phases]
tech-stack:
  added: []
  patterns:
    - explicit workspace snapshot persisted with run metadata
    - create-run validation at the API edge before orchestration starts
key-files:
  created:
    - autogen_dashboard/repo_context.py
    - autogen_dashboard/schemas.py
    - autogen_dashboard/app.py
    - autogen_dashboard/static/index.html
    - autogen_dashboard/static/app.js
    - autogen_dashboard/static/styles.css
    - tests/test_workspace_contract.py
  modified:
    - autogen_dashboard/session_runner.py
key-decisions:
  - "Run creation now requires an explicit repo or worktree root instead of allowing a hidden global workspace."
  - "Workspace preview data rides on /api/repos so the operator sees branch, dirty state, stack hints, and recent commits before execution."
patterns-established:
  - "Workspace roots must resolve inside AUTOGEN_REPO_SCAN_ROOT and must be actual repo or worktree roots."
  - "Original operator task is stored separately from later human notes on the run summary."
requirements-completed: [WKSP-01, WKSP-02]
duration: 1 min
completed: 2026-03-21
---

# Phase 01 Plan 01: Workspace and Durable Run Foundation Summary

**Explicit repo-root run creation with recursive workspace discovery and a styled preflight workspace preview**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-21T07:30:14Z
- **Completed:** 2026-03-21T07:30:58Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments

- Recursive workspace discovery now finds nested repos and worktrees under the configured scan root while skipping internal runtime folders.
- Run summaries now carry explicit workspace snapshot, workspace kind, original task, latest human note, and attempt count fields.
- The operator surface now requires a workspace plus engineering prompt before create, and shows a rounded workspace preview card before execution.

## Task Commits

Each task was committed atomically:

1. **Task 1: Expand workspace discovery and explicit run schema** - `70f9a96` (`feat`)
2. **Task 2: Require explicit workspace selection in the operator surface** - `f6e51f0` (`feat`)

## Files Created/Modified

- `autogen_dashboard/repo_context.py` - Recursive repo discovery, strict repo-root resolution, workspace kind detection, and snapshot signatures.
- `autogen_dashboard/schemas.py` - Run-facing workspace snapshot and original-task fields in the API contract.
- `autogen_dashboard/session_runner.py` - Run creation now requires a workspace and persists the original task plus workspace snapshot fields.
- `autogen_dashboard/app.py` - Create-run API now rejects empty task or missing repo root before calling the service layer.
- `autogen_dashboard/static/index.html` - Create-run form now includes explicit workspace selection, manual path entry, and a workspace preview card.
- `autogen_dashboard/static/app.js` - Front-end now renders workspace preview, validates create-run readiness, and posts explicit workspace roots.
- `autogen_dashboard/static/styles.css` - Added a dedicated polished workspace summary card style block.
- `tests/test_workspace_contract.py` - Regression coverage for recursive discovery, strict repo-root validation, and create-run API requirements.

## Decisions Made

- The create-run boundary validates `task` and `repo_root` at the API edge so the backend never starts a run from an ambiguous workspace.
- `/api/repos` now carries enough repo summary data to render the preflight workspace card without a second preview endpoint.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Tightened repo detection to actual repo or worktree roots**
- **Found during:** Task 1 (Expand workspace discovery and explicit run schema)
- **Issue:** `git rev-parse --show-toplevel` made any folder inside an existing repo look like a valid workspace, which broke scan-root safety and test expectations.
- **Fix:** `is_git_repo` and `collect_repo_context` now require the resolved folder to match the git-reported repo/worktree root exactly.
- **Files modified:** `autogen_dashboard/repo_context.py`, `tests/test_workspace_contract.py`
- **Verification:** `.\.venv\Scripts\python.exe -m unittest tests.test_workspace_contract -v`
- **Committed in:** `70f9a96` (part of Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The fix tightened the exact workspace contract the plan intended. No scope creep.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan `01-02` can now build durable on-disk run identity and retry semantics on top of explicit workspace selection.
- The active runtime still needs run-scoped workspace propagation and stale-workspace detection in later Phase 1 plans.

---
*Phase: 01-workspace-and-durable-run-foundation*
*Completed: 2026-03-21*
