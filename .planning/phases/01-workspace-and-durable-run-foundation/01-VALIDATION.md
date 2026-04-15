---
phase: 1
slug: workspace-and-durable-run-foundation
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-20
---

# Phase 1 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` (stdlib) |
| **Config file** | none - existing repo uses stdlib discovery |
| **Quick run command** | `.\.venv\Scripts\python.exe -m unittest tests.test_maf_setup` |
| **Full suite command** | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v && .\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py` |
| **Estimated runtime** | ~40 seconds |

---

## Sampling Rate

- **After every task commit:** Run `.\.venv\Scripts\python.exe -m unittest tests.test_maf_setup`
- **After every plan wave:** Run `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` and `.\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01-01 | 1 | WKSP-01 | unit | `.\.venv\Scripts\python.exe -m unittest tests.test_workspace_contract` | NO - W0 | pending |
| 01-01-02 | 01-01 | 1 | WKSP-01, WKSP-02 | UI contract | `node --check autogen_dashboard\static\app.js` | YES | pending |
| 01-02-01 | 01-02 | 2 | WKSP-03 | unit | `.\.venv\Scripts\python.exe -m unittest tests.test_run_persistence` | NO - W0 | pending |
| 01-02-02 | 01-02 | 2 | WKSP-03 | API/integration | `.\.venv\Scripts\python.exe -m unittest tests.test_phase1_api tests.test_phase1_runtime` | NO - W0 | pending |
| 01-02-03 | 01-02 | 2 | WKSP-03 | regression | `.\.venv\Scripts\python.exe -m unittest tests.test_run_persistence tests.test_phase1_api tests.test_phase1_runtime` | NO - W0 | pending |
| 01-03-01 | 01-03 | 3 | WKSP-02 | runtime | `.\.venv\Scripts\python.exe -m unittest tests.test_phase1_runtime` | NO - W0 | pending |
| 01-03-02 | 01-03 | 3 | WKSP-01, WKSP-02, WKSP-03 | regression | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` | YES | pending |
| 01-03-03 | 01-03 | 3 | WKSP-01, WKSP-02, WKSP-03 | static sanity | `.\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py` | YES | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_workspace_contract.py` - repo selection, scan-root validation, and workspace snapshot coverage for `WKSP-01` and `WKSP-02`
- [ ] `tests/test_run_persistence.py` - run directory, artifact manifest, and retry semantics coverage for `WKSP-03`
- [ ] `tests/test_phase1_api.py` - create/get/retry/reopen API coverage, including non-empty prompt validation and persisted workspace metadata
- [ ] `tests/test_phase1_runtime.py` - run-scoped MAF workspace, stale-workspace warning, and resume or reopen integration coverage

*Existing infrastructure covers all framework needs; Wave 0 is only new phase-specific test modules.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Workspace header shows repo root, branch, dirty state, and stale warning clearly in the operator surface | WKSP-02 | Visual layout and warning prominence matter, and current repo does not have browser automation wired in | Launch the local operator surface, create a run, confirm the selected repo summary is visible before execution, then change the repo outside the run and confirm the stale-workspace warning is shown without reading raw JSON |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 30s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
