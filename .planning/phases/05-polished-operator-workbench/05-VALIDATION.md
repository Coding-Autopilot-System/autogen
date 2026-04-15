---
phase: 5
slug: polished-operator-workbench
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-22
---

# Phase 5 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` (stdlib) |
| **Config file** | none - existing repo uses stdlib discovery |
| **Quick run command** | `.\.venv\Scripts\python.exe -m unittest tests.test_phase5_ui_contract -v` |
| **Full suite command** | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` |
| **Static sanity** | `.\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py` and `node --check autogen_dashboard\static\app.js` |
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
| 05-01-01 | 05-01 | 1 | UI-01 | static UI contract | `.\.venv\Scripts\python.exe -m unittest tests.test_phase5_ui_contract -v` | NO - W0 | pending |
| 05-01-02 | 05-01 | 1 | UI-01 | frontend syntax | `node --check autogen_dashboard\static\app.js` | YES | pending |
| 05-01-03 | 05-01 | 1 | UI-01, UI-02 | regression | `.\.venv\Scripts\python.exe -m unittest tests.test_phase5_ui_contract tests.test_phase3_api -v` | YES | pending |
| 05-02-01 | 05-02 | 2 | UI-02, UI-03 | payload and view-model | `.\.venv\Scripts\python.exe -m unittest tests.test_phase5_operator_views -v` | NO - W0 | pending |
| 05-02-02 | 05-02 | 2 | UI-02, UI-03 | API/runtime regression | `.\.venv\Scripts\python.exe -m unittest tests.test_phase5_operator_views tests.test_phase3_api tests.test_phase4_approval -v` | YES | pending |
| 05-02-03 | 05-02 | 2 | UI-02, UI-03 | static sanity | `node --check autogen_dashboard\static\app.js` | YES | pending |
| 05-03-01 | 05-03 | 3 | UI-01 | UI contract regression | `.\.venv\Scripts\python.exe -m unittest tests.test_phase5_ui_contract tests.test_phase5_operator_views -v` | YES | pending |
| 05-03-02 | 05-03 | 3 | UI-01, UI-02, UI-03 | full regression | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` | YES | pending |
| 05-03-03 | 05-03 | 3 | UI-01, UI-02, UI-03 | compile and syntax | `.\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py` and `node --check autogen_dashboard\static\app.js` | YES | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase5_ui_contract.py` - shell landmarks, tab inventory, message-family hooks, and route-strip rendering contracts
- [ ] `tests/test_phase5_operator_views.py` - operator view-model payloads for timeline, events, agents, routing, artifacts, and approval visibility

*Phase 5 reuses the existing test infrastructure; Wave 0 is only the new product-UI contract coverage.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Human, manager, specialist, event, and approval content are visually distinct at a glance | UI-01 | Requires human judgment about hierarchy and scanability | Start a run with approvals and specialist activity, then confirm each content family uses a visibly different surface and can be understood without transcript prefixes |
| The operator can inspect timeline, routing, agents, and artifacts without reading raw logs | UI-02, UI-03 | Requires end-to-end product judgment across multiple tabs and cards | Run a session that produces routing, specialist handoffs, structured events, validation output, and artifacts, then confirm each surface is inspectable through dedicated views and cards instead of transcript scraping |
| The active run workspace feels focused and usable on desktop and laptop widths | UI-01, UI-02 | Requires layout and ergonomics judgment | Use the operator workbench with a selected run, scroll the transcript and tabs, and confirm sticky controls, active-run emphasis, and spacing remain readable |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 90s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
