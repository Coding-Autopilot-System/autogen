---
phase: 04-autonomous-repo-execution-and-validation-guardrails
plan: 02
subsystem: validation-runtime
tags: [validation, command-ladder, runtime, artifacts, failure-handling]
requires:
  - plan: 04-01
    provides: controlled write execution and change artifacts
provides:
  - targeted local validation ladder selected from changed files and repo context
  - durable validation command/result artifacts under the validation stage
  - failure-to-pause behavior for broken implementation output
affects: [maf-runtime, dashboard-runtime, run-artifacts, tests]
requirements-completed: [EXEC-02, EXEC-03]
completed: 2026-03-21
---

# Phase 04 Plan 02: Validation Runner Summary

## Accomplishments

- Added a shared validation runner with serializable command, plan, and result types for the local validation ladder.
- Selected safe validation commands from repo context and changed files, including `git diff --check`, `python -m compileall`, `python -m unittest discover -s tests -v`, and `node --check`.
- Persisted validation command and result artifacts under the validation stage so operators can see what ran, where it ran, and how it failed or passed.
- Changed validation failures from silent transcript noise into explicit runtime pauses with recorded result payloads.

## Files

- `maf_core/validation_runner.py`
- `maf_core/orchestration.py`
- `autogen_dashboard/schemas.py`
- `autogen_dashboard/session_store.py`
- `autogen_dashboard/session_runner.py`
- `tests/test_phase4_validation.py`
- `tests/test_phase2_runtime.py`
- `tests/test_run_persistence.py`

## Decisions

- Validation remains a bounded local ladder and does not install dependencies or call external services.
- Validation artifacts are durable stage data and feed the operator UI directly.
- Failed validation is treated as a stage pause with actionable data rather than a soft warning.

## Verification

- `.\.venv\Scripts\python.exe -m unittest tests.test_phase4_validation tests.test_run_persistence tests.test_phase2_runtime -v`
- `.\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py`
