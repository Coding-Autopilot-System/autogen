---
phase: 4
slug: autonomous-repo-execution-and-validation-guardrails
status: green
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-21
---

# Phase 4 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` (stdlib) |
| **Config file** | none - existing repo uses stdlib discovery |
| **Quick run command** | `.\.venv\Scripts\python.exe -m unittest tests.test_phase4_write_execution -v` |
| **Full suite command** | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` |
| **Static sanity** | `.\.venv\Scripts\python.exe -m compileall maf_starter autogen_dashboard tests main.py` and `node --check autogen_dashboard\static\app.js` |
| **Estimated runtime** | ~90 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-specific `verify` command from the active plan
- **After every plan wave:** Run `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- **Before `$gsd-verify-work`:** Full suite plus static sanity must be green
- **Max feedback latency:** 90 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 04-01 | 1 | EXEC-01 | unit | `.\.venv\Scripts\python.exe -m unittest tests.test_phase4_write_execution -v` | YES | green |
| 04-01-02 | 04-01 | 1 | EXEC-01, EXEC-02 | persistence | `.\.venv\Scripts\python.exe -m unittest tests.test_phase4_write_execution tests.test_run_persistence -v` | YES | green |
| 04-01-03 | 04-01 | 1 | EXEC-01, EXEC-02 | regression | `.\.venv\Scripts\python.exe -m unittest tests.test_phase4_write_execution tests.test_run_persistence -v` | YES | green |
| 04-02-01 | 04-02 | 2 | EXEC-03 | unit | `.\.venv\Scripts\python.exe -m unittest tests.test_phase4_validation -v` | YES | green |
| 04-02-02 | 04-02 | 2 | EXEC-02, EXEC-03 | runtime | `.\.venv\Scripts\python.exe -m unittest tests.test_phase4_validation tests.test_run_persistence -v` | YES | green |
| 04-02-03 | 04-02 | 2 | EXEC-03 | regression | `.\.venv\Scripts\python.exe -m unittest tests.test_phase4_validation tests.test_phase2_runtime -v` | YES | green |
| 04-03-01 | 04-03 | 3 | EXEC-04 | unit | `.\.venv\Scripts\python.exe -m unittest tests.test_phase4_approval -v` | YES | green |
| 04-03-02 | 04-03 | 3 | EXEC-04 | API/UI contract | `.\.venv\Scripts\python.exe -m unittest tests.test_phase4_approval tests.test_phase3_api -v` | YES | green |
| 04-03-03 | 04-03 | 3 | EXEC-01, EXEC-02, EXEC-03, EXEC-04 | regression | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` | YES | green |
| 04-03-03b | 04-03 | 3 | EXEC-02, EXEC-04 | static sanity | `.\.venv\Scripts\python.exe -m compileall maf_starter autogen_dashboard tests main.py` and `node --check autogen_dashboard\static\app.js` | YES | green |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [x] `tests/test_phase4_write_execution.py` - controlled write execution, path safety, diff capture, and operation-record coverage
- [x] `tests/test_phase4_validation.py` - validation command selection, result recording, and failure-to-pause coverage
- [x] `tests/test_phase4_approval.py` - approval classification, pending-approval payload, and destructive/external action coverage

*Phase 4 reuses the existing stdlib test infrastructure; Wave 0 is the new autonomous-execution safety coverage.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Operator can inspect changed files and diffs without reading raw logs | EXEC-02 | Requires human judgment about readability and scanability | Start an autonomous implementation run, then confirm the operator surface shows changed files first and exposes a readable diff artifact for drill-down |
| Approval scope is clear before risky actions execute | EXEC-04 | Requires human judgment about wording and scope clarity | Trigger a destructive or externally visible action, then confirm the approval card names the action, affected files or resources, reason, and what approval will allow |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all new autonomous-execution safety surfaces
- [x] No watch-mode flags
- [x] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** passed
