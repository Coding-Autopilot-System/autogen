---
phase: 6
slug: api-boundary-and-control-plane-contract
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-03-22
---

# Phase 6 - Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` (stdlib) |
| **Config file** | none - existing repo uses stdlib discovery |
| **Quick run command** | `.\.venv\Scripts\python.exe -m unittest tests.test_phase6_service tests.test_phase6_api_contract -v` |
| **Full suite command** | `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` |
| **Static sanity** | `.\.venv\Scripts\python.exe -m compileall maf_core command_center autogen_dashboard tests main.py` and `node --check command_center\static\app.js` |
| **Estimated runtime** | ~120 seconds |

---

## Sampling Rate

- **After every task commit:** Run the task-specific `verify` command from the active plan
- **After every plan wave:** Run `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- **Before `$gsd-verify-work`:** Full suite plus static sanity must be green
- **Max feedback latency:** 120 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 06-01 | 1 | API-01, API-02 | syntax | `python -m compileall maf_core/control_plane` | YES | pending |
| 06-01-02 | 06-01 | 1 | API-01, API-02 | syntax | `python -m compileall maf_core/control_plane` | YES | pending |
| 06-01-03 | 06-01 | 1 | API-01, API-02, API-03, API-04 | syntax | `python -m compileall maf_core/control_plane` | YES | pending |
| 06-01-04 | 06-01 | 1 | API-01, API-02, API-03, API-04 | service contract | `.\.venv\Scripts\python.exe -m unittest tests.test_phase6_service -v` | NO - W0 | pending |
| 06-02-01 | 06-02 | 2 | API-01, API-02, API-03, API-04 | syntax | `python -m compileall maf_core/control_plane` | YES | pending |
| 06-02-02 | 06-02 | 2 | API-01, API-02, API-03, API-04 | syntax | `python -m compileall maf_core/control_plane` | YES | pending |
| 06-02-03 | 06-02 | 2 | API-01, API-02, API-03, API-04 | syntax | `python -m compileall command_center` | YES | pending |
| 06-02-04 | 06-02 | 2 | API-01, API-02, API-03, API-04 | REST contract | `.\.venv\Scripts\python.exe -m unittest tests.test_phase6_api_contract -v` | NO - W0 | pending |
| 06-03-01 | 06-03 | 3 | API-01, API-02, API-03, API-04 | frontend syntax | `node --check command_center\static\app.js` | YES | pending |
| 06-03-02 | 06-03 | 3 | API-01, API-02, API-03, API-04 | syntax | `python -m compileall autogen_dashboard` | YES | pending |
| 06-03-03 | 06-03 | 3 | API-01, API-02, API-03, API-04 | parity | `.\.venv\Scripts\python.exe -m unittest tests.test_phase6_command_center_parity -v` | NO - W0 | pending |
| 06-03-04 | 06-03 | 3 | API-01, API-02, API-03, API-04 | documentation | `python -c "open('README.md').read()"` | YES | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_phase6_service.py` - service-level validation for create, control actions, orchestration projection, and artifact manifest
- [ ] `tests/test_phase6_api_contract.py` - REST contract validation for API-01, API-02, API-03, API-04
- [ ] `tests/test_phase6_command_center_parity.py` - parity validation that Command Center and /api/v1 share run contract

*Phase 6 extends existing test infrastructure with new control-plane contract coverage.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| External callers can create and inspect runs via /api/v1 endpoints | API-01, API-02, API-03 | Requires external client (curl, Postman) to validate contract outside test client | Start Command Center, use `curl -X POST http://localhost:8001/api/v1/runs -H "Content-Type: application/json" -d '{"task": "test", "repo_root": "C:\\repo\\autogen"}'`, verify response includes run_id, then GET the run and artifacts |
| Command Center UI displays run data from /api/v1 endpoints | API-02, API-03 | Requires browser dev tools to confirm fetch URLs | Open Command Center in browser, create a run, open dev tools network tab, verify timeline/agents/routing/artifacts fetch from /api/v1 paths |
| Legacy dashboard routes still work but delegate to RunService | API-01, API-02, API-04 | Requires testing compatibility surface in isolation | Start legacy dashboard, create a session via old `/api/sessions` POST, verify it works and check logs for RunService delegation |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all missing references
- [x] No watch-mode flags
- [x] Feedback latency < 120s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
