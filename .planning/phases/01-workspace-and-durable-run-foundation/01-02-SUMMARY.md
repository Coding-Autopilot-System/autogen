---
phase: 01-workspace-and-durable-run-foundation
plan: 02
subsystem: runtime
tags: [run-state, persistence, retry, artifacts, attempts]
requires:
  - phase: 01-01
    provides: explicit workspace selection and run creation contract
provides:
  - one stable run directory with metadata, transcript, events, artifacts, runtime state, and attempts
  - retry semantics that preserve the original task instead of replaying approval notes
  - service and API coverage for reopen and retry behavior
affects: [operator-ui, runtime-state, resume-retry, later-maf-integration]
tech-stack:
  added: []
  patterns:
    - attempt summaries persisted under attempts/attempt-XXX/summary.json
    - artifact manifest as the machine-readable index for run outputs
key-files:
  created:
    - autogen_dashboard/dependencies.py
    - autogen_dashboard/session_store.py
    - tests/test_run_persistence.py
    - tests/test_phase1_api.py
    - tests/test_phase1_runtime.py
  modified:
    - autogen_dashboard/schemas.py
    - autogen_dashboard/session_runner.py
key-decisions:
  - "A retry always stays on the same run id but starts a fresh attempt directory."
  - "Approval decisions, latest human note, retry seed, and original task are stored separately."
patterns-established:
  - "Persist runtime state under runtime/state.json and keep attempts under attempts/attempt-XXX."
  - "Use slash-normalized relative paths inside artifact manifests for stable cross-platform consumption."
requirements-completed: [WKSP-03]
duration: 1 min
completed: 2026-03-21
---

# Phase 01 Plan 02: Workspace and Durable Run Foundation Summary

**Stable per-run storage with attempt history, artifact manifests, and retry-safe original task handling**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-21T07:42:10Z
- **Completed:** 2026-03-21T07:42:48Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- Each run now persists under a single directory that contains metadata, transcript, events, runtime state, workspace artifacts, and attempt summaries.
- The runner now preserves `original_task`, `latest_human_note`, `approval_decisions`, and `retry_seed_prompt` as separate concerns instead of collapsing everything into one last prompt.
- Focused runtime and API tests now lock reopen, retry, and artifact-manifest behavior in place.

## Task Commits

Each task was committed atomically:

1. **Task 1: Normalize the on-disk run directory and artifact manifest** - `dd3e281` (`feat`)
2. **Task 2: Separate original task, human decisions, and retry seeds in the run lifecycle** - `88c13de` (`feat`)
3. **Task 3: Add persistence and reopen regression coverage** - `81048d1` (`test`)

## Files Created/Modified

- `autogen_dashboard/session_store.py` - durable run directory layout, artifact manifest generation, attempt summaries, runtime state, and atomic JSON writes.
- `autogen_dashboard/schemas.py` - explicit approval decisions, retry seed, artifact manifest, and latest attempt fields.
- `autogen_dashboard/session_runner.py` - attempt lifecycle events, retry semantics, and preserved original task handling.
- `autogen_dashboard/dependencies.py` - reusable dashboard context builder for testable run-service composition.
- `tests/test_run_persistence.py` - on-disk run layout and atomic-write regression tests.
- `tests/test_phase1_api.py` - create/get/retry API contract tests for workspace and attempt metadata.
- `tests/test_phase1_runtime.py` - service-level retry and reopen behavior tests.

## Decisions Made

- The run directory is now the canonical durability boundary, while attempts describe retries within that one run identity.
- Retry uses `retry_seed_prompt` when explicitly set, otherwise it falls back to `original_task`, never to approval or rejection notes.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Normalized artifact manifest paths to stable slash-separated values**
- **Found during:** Task 3 (Add persistence and reopen regression coverage)
- **Issue:** Windows-native relative paths were written with backslashes, which made the manifest less stable for tests and UI consumers.
- **Fix:** Artifact-manifest entries now use `as_posix()` relative paths inside the run directory.
- **Files modified:** `autogen_dashboard/session_store.py`, `tests/test_run_persistence.py`
- **Verification:** `.\.venv\Scripts\python.exe -m unittest tests.test_run_persistence tests.test_phase1_api tests.test_phase1_runtime -v`
- **Committed in:** `dd3e281` (captured before the final regression pass and retained in the task commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The fix tightened portability and did not change scope.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan `01-03` can now push the selected workspace and checkpoint root through the active MAF runtime instead of only the dashboard shell.
- The stale-workspace warning path can build directly on the persisted workspace snapshot and attempt metadata added here.

---
*Phase: 01-workspace-and-durable-run-foundation*
*Completed: 2026-03-21*
