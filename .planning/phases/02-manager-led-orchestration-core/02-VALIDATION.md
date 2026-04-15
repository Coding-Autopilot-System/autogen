---
phase: 2
slug: manager-led-orchestration-core
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-21
---

# Phase 2 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` (stdlib) |
| **Config file** | none - existing repo uses stdlib discovery |
| **Quick run command** | `.\.venv\Scripts\python.exe -m unittest tests.test_phase2_manager` |
| **Full suite command** | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` |
| **Static sanity** | `.\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py` and `node --check autogen_dashboard\static\app.js` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-specific `verify` command from the active plan
- **After every plan wave:** Run `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- **Before `$gsd-verify-work`:** Full suite plus static sanity must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 02-01 | 1 | ORCH-01, ORCH-02 | unit | `.\.venv\Scripts\python.exe -m unittest tests.test_phase2_manager` | NO - W0 | pending |
| 02-01-02 | 02-01 | 1 | ORCH-01 | runtime | `.\.venv\Scripts\python.exe -m unittest tests.test_phase2_manager` | NO - W0 | pending |
| 02-01-03 | 02-01 | 1 | ORCH-01, ORCH-02 | smoke | `.\.venv\Scripts\python.exe -m unittest tests.test_phase2_manager tests.test_maf_setup -v` | YES | pending |
| 02-02-01 | 02-02 | 2 | ORCH-04 | unit | `.\.venv\Scripts\python.exe -m unittest tests.test_phase2_runtime -v` | NO - W0 | pending |
| 02-02-02 | 02-02 | 2 | ORCH-02, ORCH-03, ORCH-04 | runtime | `.\.venv\Scripts\python.exe -m unittest tests.test_phase2_runtime -v` | NO - W0 | pending |
| 02-02-03 | 02-02 | 2 | ORCH-03, ORCH-04 | persistence | `.\.venv\Scripts\python.exe -m unittest tests.test_phase2_runtime tests.test_run_persistence -v` | YES | pending |
| 02-03-01 | 02-03 | 3 | ORCH-01, ORCH-02 | API/runtime | `.\.venv\Scripts\python.exe -m unittest tests.test_phase2_api tests.test_maf_setup -v` | NO - W0 | pending |
| 02-03-02 | 02-03 | 3 | ORCH-02 | UI contract | `node --check autogen_dashboard\static\app.js` | YES | pending |
| 02-03-03 | 02-03 | 3 | ORCH-01, ORCH-02, ORCH-03, ORCH-04 | regression | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` | YES | pending |
| 02-03-03b | 02-03 | 3 | ORCH-02 | static sanity | `.\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py` | YES | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase2_manager.py` - manager stage order, stage serialization, and run-scoped stage persistence
- [ ] `tests/test_phase2_runtime.py` - stage-aware pause, resume, retry, and GSD auto-answer coverage
- [ ] `tests/test_phase2_api.py` - current stage, last completed stage, pause kind, stage timeline, and route metadata API coverage

*Phase 2 can reuse the existing test infrastructure; Wave 0 is only the new orchestration-specific modules.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Operator surface clearly shows current stage, last completed stage, and pause reason | ORCH-02 | Visual density and clarity matter, and the repo still has no browser automation | Launch the current operator surface, start a manager-led run, confirm the current stage card and stage timeline update as the run advances or pauses |
| Automatic GSD answering feels inspectable rather than magical | ORCH-04 | Requires operator judgment about clarity and trustworthiness | Run a prompt that triggers routine clarification, confirm the run records an auto-answer artifact or a concise missing-information pause instead of a vague interruption |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
