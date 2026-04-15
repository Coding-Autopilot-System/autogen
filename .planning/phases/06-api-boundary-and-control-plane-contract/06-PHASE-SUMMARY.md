# Phase 6: API Boundary and Control Plane Contract - Planning Summary

**Date:** 2026-03-22
**Status:** Planning complete, ready for execution
**Plans:** 3 sequential execution plans

---

## Overview

Phase 6 extracts the existing local orchestration runtime into a host-agnostic control-plane API that both Command Center and external callers can use. This phase defines the shared service boundary, the durable HTTP run contract, and parity rules between UI-driven runs and API-driven runs.

**Key Goal:** Eliminate drift between the product UI and external API by creating one shared run-control contract.

---

## Execution Plans

### 06-01: Extract Shared Control-Plane Package
**Wave:** 1
**Dependencies:** None
**Focus:** Service extraction from autogen_dashboard donors

**Deliverables:**
- `maf_core/control_plane/contracts.py` - Canonical Run* models migrated from SessionStore schemas
- `maf_core/control_plane/store.py` - Durable run persistence with file-backed storage
- `maf_core/control_plane/service.py` - Run lifecycle and control actions (create, get, continue, approve, retry, cancel)
- `tests/test_phase6_service.py` - Service-level validation for API-01 through API-04

**Key Decision:** Preserve existing `state/sessions/{run_id}/` disk layout during extraction; execution engine remains stubbed behind placeholder.

---

### 06-02: Add Versioned /api/v1 Router
**Wave:** 2
**Dependencies:** 06-01
**Focus:** REST contract delivery and Command Center mounting

**Deliverables:**
- `maf_core/control_plane/router.py` - Resource-oriented FastAPI router with full CRUD and control actions
- `maf_core/control_plane/auth.py` - Pluggable auth boundary (NoAuthPolicy default, Azure Functions-ready)
- `command_center/app.py` - Mounts shared /api/v1 router
- `tests/test_phase6_api_contract.py` - REST contract validation

**Endpoints Delivered:**
- `POST /api/v1/runs` - Create run (API-01)
- `GET /api/v1/runs` - List runs
- `GET /api/v1/runs/{run_id}` - Get run status (API-02)
- `GET /api/v1/runs/{run_id}/timeline` - Stage timeline (API-03)
- `GET /api/v1/runs/{run_id}/agents` - Specialist states (API-03)
- `GET /api/v1/runs/{run_id}/routing` - Route history (API-03)
- `GET /api/v1/runs/{run_id}/artifacts` - Artifact manifest (API-03)
- `GET /api/v1/runs/{run_id}/artifacts/{path}` - Fetch artifact (API-03)
- `GET /api/v1/runs/{run_id}/events` - Event log (API-03)
- `POST /api/v1/runs/{run_id}/actions/continue` - Resume (API-04)
- `POST /api/v1/runs/{run_id}/actions/approve` - Approve (API-04)
- `POST /api/v1/runs/{run_id}/actions/retry` - Retry (API-04)
- `POST /api/v1/runs/{run_id}/actions/cancel` - Cancel (API-04)
- `POST /api/v1/runs/{run_id}/actions/operator-input` - Append operator message (API-04)

---

### 06-03: Command Center Parity and Compatibility Cleanup
**Wave:** 3
**Dependencies:** 06-02
**Focus:** UI migration and legacy compatibility

**Deliverables:**
- `command_center/static/app.js` - Fetches run data from /api/v1 instead of parallel state
- `autogen_dashboard/app.py` - Legacy routes delegate to RunService (compatibility wrapper)
- `tests/test_phase6_command_center_parity.py` - Parity validation
- `README.md` - External API documentation

**Key Decision:** Keep legacy dashboard routes alive as compatibility wrappers; mark as deprecated but do not break.

---

## Validation Strategy

**Test Coverage:**
- Service-level: `tests/test_phase6_service.py`
- REST contract: `tests/test_phase6_api_contract.py`
- Parity: `tests/test_phase6_command_center_parity.py`

**Commands:**
- Quick: `.\.venv\Scripts\python.exe -m unittest tests.test_phase6_service tests.test_phase6_api_contract -v`
- Full: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- Static: `python -m compileall maf_core command_center autogen_dashboard` + `node --check command_center\static\app.js`

**Max feedback latency:** 120 seconds

---

## Requirements Satisfied

- **API-01**: POST /api/v1/runs creates durable run, returns run_id
- **API-02**: GET /api/v1/runs/{run_id} returns status, current_stage, pause_kind, routing
- **API-03**: Timeline, agents, routing, artifacts endpoints expose inspectable run detail
- **API-04**: Explicit action endpoints for continue, approve, retry, cancel, operator-input

---

## Next Steps

1. Execute `06-01` - Extract shared control-plane package
2. Execute `06-02` - Add /api/v1 router
3. Execute `06-03` - Command Center parity
4. Verify all tests green
5. Proceed to Phase 7 (Azure Functions hosting)

---

**Planned by:** Claude (continuing from codex)
**Ready for:** `$gsd-execute-phase 6 --plan 01 --auto`
