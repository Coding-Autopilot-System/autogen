---
phase: 3
slug: specialist-delegation-and-routing-visibility
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-21
---

# Phase 3 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` (stdlib) |
| **Config file** | none - existing repo uses stdlib discovery |
| **Quick run command** | `.\.venv\Scripts\python.exe -m unittest tests.test_phase3_specialists -v` |
| **Full suite command** | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` |
| **Static sanity** | `.\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py` and `node --check autogen_dashboard\static\app.js` |
| **Estimated runtime** | ~75 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-specific `verify` command from the active plan
- **After every plan wave:** Run `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- **Before `$gsd-verify-work`:** Full suite plus static sanity must be green
- **Max feedback latency:** 75 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 03-01 | 1 | AGNT-01, AGNT-02 | unit | `.\.venv\Scripts\python.exe -m unittest tests.test_phase3_specialists -v` | NO - W0 | pending |
| 03-01-02 | 03-01 | 1 | AGNT-01, AGNT-02, AGNT-03 | runtime | `.\.venv\Scripts\python.exe -m unittest tests.test_phase3_specialists -v` | NO - W0 | pending |
| 03-01-03 | 03-01 | 1 | AGNT-01, AGNT-02 | regression | `.\.venv\Scripts\python.exe -m unittest tests.test_phase3_specialists tests.test_maf_setup -v` | YES | pending |
| 03-02-01 | 03-02 | 1 | ROUT-01, ROUT-02 | unit | `.\.venv\Scripts\python.exe -m unittest tests.test_phase3_routing -v` | NO - W0 | pending |
| 03-02-02 | 03-02 | 1 | ROUT-01, ROUT-02, ROUT-03 | runtime | `.\.venv\Scripts\python.exe -m unittest tests.test_phase3_routing tests.test_maf_setup -v` | NO - W0 | pending |
| 03-02-03 | 03-02 | 1 | ROUT-02, ROUT-03 | persistence | `.\.venv\Scripts\python.exe -m unittest tests.test_phase3_routing tests.test_maf_setup -v` | YES | pending |
| 03-03-01 | 03-03 | 2 | AGNT-01, AGNT-02, ROUT-02 | API/runtime | `.\.venv\Scripts\python.exe -m unittest tests.test_phase3_api -v` | NO - W0 | pending |
| 03-03-02 | 03-03 | 2 | ROUT-01, ROUT-02, ROUT-03 | UI contract | `node --check autogen_dashboard\static\app.js` | YES | pending |
| 03-03-03 | 03-03 | 2 | AGNT-01, AGNT-02, AGNT-03, ROUT-01, ROUT-02, ROUT-03 | regression | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` | YES | pending |
| 03-03-03b | 03-03 | 2 | ROUT-02 | static sanity | `.\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py` | YES | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase3_specialists.py` - specialist roster, idle-state, handoff, and stage-ownership coverage
- [ ] `tests/test_phase3_routing.py` - route-lane selection, fallback chain, and capability-drift coverage
- [ ] `tests/test_phase3_api.py` - API and operator-surface payload coverage for agents and routing

*Phase 3 can reuse the existing test infrastructure; Wave 0 is only the new specialist and routing visibility coverage.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Operator can understand which specialist owns work at a glance | AGNT-01, AGNT-02 | Requires human judgment about scanability and clarity | Launch the dashboard, start a routed specialist run, and confirm the `Agents` or equivalent per-agent surface clearly shows role, state, current task, and latest handoff without reading raw transcript text |
| Route cards make fallback and capability drift obvious | ROUT-02, ROUT-03 | Requires visual confirmation of chips, labels, and summary wording | Start a run that triggers route metadata or fallback, then confirm the operator surface shows the planned lane, actual provider/model, fallback use, and capability change clearly |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 75s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
