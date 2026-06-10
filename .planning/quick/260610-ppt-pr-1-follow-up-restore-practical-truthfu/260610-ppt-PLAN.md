---
quick_id: 260610-ppt
mode: quick-full
status: ready
date: 2026-06-10
---

# PR #1 follow-up: truthful Quickstart and Configuration guidance

## Goal

Restore practical README guidance that helps readers validate and understand the checked-in repository without claiming a missing dependency manifest, `.env.example`, launcher, or supported full-runtime bootstrap.

## Must Haves

- Quickstart commands operate against files present on `docs/portfolio-hardening-20260610`.
- The README clearly distinguishes the CI-aligned static contract tests from a full runtime launch.
- Configuration guidance is derived from `maf_starter/config.py` and does not claim an `.env.example` exists.
- Validation includes the documented test command, README claim checks, and `git diff --check`.

## Tasks

### Task 1: Restore truthful operator guidance

**Files:** `README.md`

**Action:** Add a Quickstart that runs the same static contract tests as CI, disclose the current runtime-bootstrap limitations, and add a configuration reference based only on variables read by `maf_starter/config.py`.

**Verify:** Confirm every named repository path exists and every documented command is appropriate for this snapshot.

**Done:** Readers can validate the portfolio evidence and understand configuration boundaries without being told to use missing files or unsupported launch commands.

### Task 2: Validate and record completion

**Files:** `.planning/quick/260610-ppt-pr-1-follow-up-restore-practical-truthfu/260610-ppt-SUMMARY.md`, `.planning/quick/260610-ppt-pr-1-follow-up-restore-practical-truthfu/260610-ppt-VERIFICATION.md`, `.planning/STATE.md`

**Action:** Run the CI-aligned tests and `git diff --check`, verify README claims against tracked files and configuration source, then record the quick-task result.

**Verify:** All validation commands pass and the final commit contains only the README follow-up and GSD quick-task artifacts/state.

**Done:** The task is documented, verified, atomically committed, and ready to push on the existing PR branch.
