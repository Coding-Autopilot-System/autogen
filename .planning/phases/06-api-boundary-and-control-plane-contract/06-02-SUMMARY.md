# Phase 6, Plan 02 - Summary

**Phase:** 06-api-boundary-and-control-plane-contract
**Plan:** 02
**Status:** ✅ Complete
**Completed:** 2026-03-22

---

## Objective

Deliver a versioned `/api/v1/runs` REST router that exposes the shared control-plane contract and mount it in Command Center.

---

## Deliverables

### Files Created

1. **maf_core/control_plane/auth.py** (118 lines)
   - `AuthPolicy` abstract base class with `require_auth()` method
   - `NoAuthPolicy` for local loopback development (returns `{"caller": "local"}`)
   - `AzureFunctionsAuthPolicy` stub for Phase 7
   - `get_auth_policy()` factory with environment-based selection
   - `get_current_auth_policy()` singleton for FastAPI dependency injection

2. **maf_core/control_plane/router.py** (534 lines)
   - FastAPI `APIRouter(prefix="/api/v1")` with complete REST API
   - **15 endpoints** covering all API-01 through API-04 requirements
   - Dependency injection for `RunService` and `AuthPolicy`
   - Proper HTTP status codes (201 for create, 404 for missing, 403 for security)
   - Path traversal protection on artifact fetch

3. **tests/test_phase6_api_contract.py** (366 lines)
   - TestClient-based REST API validation
   - 8 comprehensive test methods
   - All tests passing

### Files Modified

1. **command_center/app.py**
   - Added import: `from maf_core.control_plane.router import router as api_v1_router`
   - Mounted router: `app.include_router(api_v1_router)` in `create_command_center_app()`
   - Preserves existing AG-UI endpoints and repo catalog routes

---

## API Endpoints Delivered

### Resource Management
- ✅ `POST /api/v1/runs` - Create run (API-01)
- ✅ `GET /api/v1/runs` - List runs
- ✅ `GET /api/v1/runs/{run_id}` - Get run detail (API-02)

### Inspection (API-03)
- ✅ `GET /api/v1/runs/{run_id}/timeline` - Stage timeline
- ✅ `GET /api/v1/runs/{run_id}/agents` - Specialist states
- ✅ `GET /api/v1/runs/{run_id}/routing` - Route plan, attempts, capability changes
- ✅ `GET /api/v1/runs/{run_id}/artifacts` - Artifact manifest
- ✅ `GET /api/v1/runs/{run_id}/artifacts/{path}` - Fetch specific artifact
- ✅ `GET /api/v1/runs/{run_id}/events` - Event log

### Control Actions (API-04)
- ✅ `POST /api/v1/runs/{run_id}/actions/continue` - Resume paused run
- ✅ `POST /api/v1/runs/{run_id}/actions/approve` - Approve pending approval
- ✅ `POST /api/v1/runs/{run_id}/actions/retry` - Retry failed run
- ✅ `POST /api/v1/runs/{run_id}/actions/cancel` - Cancel run
- ✅ `POST /api/v1/runs/{run_id}/actions/operator-input` - Append operator message

---

## Verification Results

✅ All tasks completed
✅ `python -m compileall maf_core/control_plane command_center` - No errors
✅ `python -m unittest tests.test_phase6_api_contract -v` - 8 tests, all passed
✅ `/api/v1/runs` router exists and is mounted in Command Center
✅ All API-01, API-02, API-03, and API-04 endpoints implemented and tested
✅ Auth is a pluggable boundary ready for Phase 7

---

## API Coverage

### API-01: Create Run
- ✅ `POST /api/v1/runs` accepts `CreateRunRequest`
- ✅ Returns 201 Created status
- ✅ Response includes stable `run_id`
- ✅ Initial status, workspace, routing included

### API-02: Get Run Status
- ✅ `GET /api/v1/runs/{run_id}` returns `RunDetail`
- ✅ Status, current_stage, pause_kind projected correctly
- ✅ Route metadata available
- ✅ 404 for missing runs

### API-03: Inspect Run Detail
- ✅ Timeline endpoint returns stage timeline entries
- ✅ Agents endpoint returns specialist states
- ✅ Routing endpoint returns route plan, attempts, capability changes
- ✅ Artifacts endpoint returns manifest with relative paths
- ✅ Artifact fetch serves files with path traversal protection
- ✅ Events endpoint returns event log

### API-04: Control Actions
- ✅ Continue action resumes paused run
- ✅ Approve action records approval decision
- ✅ Retry action creates new attempt
- ✅ Cancel action updates status to stopped
- ✅ Operator-input action appends message to transcript

---

## Security Features

1. **Pluggable Authentication**
   - `AuthPolicy` abstraction allows different auth strategies
   - `NoAuthPolicy` for local development (returns local caller identity)
   - Ready for Azure Functions Easy Auth in Phase 7

2. **Path Traversal Protection**
   - Artifact paths checked for `..`, `/`, `\` before resolution
   - Resolved paths validated to stay within run directory
   - Returns 403 for escape attempts, 404 for missing files

3. **Proper HTTP Status Codes**
   - 201 for resource creation
   - 404 for missing resources
   - 403 for security violations
   - 400 for invalid requests

---

## Test Coverage

### REST Contract Tests (test_phase6_api_contract.py)
1. **test_create_run_api** - API-01 create run validation
2. **test_get_run_api** - API-02 get run status validation
3. **test_list_runs_api** - List runs validation
4. **test_timeline_agents_routing_artifacts_api** - API-03 inspection endpoints
5. **test_events_api** - API-03 event log validation
6. **test_control_actions_api** - API-04 control actions validation
7. **test_artifact_fetch_api** - API-03 artifact fetch with security validation
8. **test_missing_run_404** - Error handling for missing runs

All 8 tests passing.

---

## Key Design Decisions

1. **Resource-Oriented API Design**
   - Separate endpoints for summary vs detail (`GET /runs` vs `GET /runs/{id}/timeline`)
   - Explicit action endpoints under `/actions/*` for mutations
   - RESTful HTTP status codes throughout

2. **Dependency Injection**
   - `RunService` injected via `Depends(get_run_service)`
   - `AuthPolicy` injected via `Depends(require_auth)`
   - Allows easy testing and future customization

3. **Security-First Artifact Access**
   - Multiple layers of path validation
   - Manifest-relative paths only
   - No arbitrary filesystem access

4. **Command Center Integration**
   - Router mounted without breaking existing endpoints
   - AG-UI streaming remains for interactive protocol
   - `/api/v1` now canonical external contract

---

## Dependencies for Next Plan

The shared control-plane API is now ready for:
- **06-03**: Command Center parity - migrate UI to fetch from /api/v1
- External API consumers can now create and manage runs
- Azure Functions can mount the same router in Phase 7

---

## Notes

- All API-01 through API-04 requirements fully satisfied
- Auth boundary is pluggable and ready for cloud deployment
- Command Center now exposes both AG-UI (specialized transport) and /api/v1 (canonical contract)
- No breaking changes to existing UI or AG-UI protocol
- Path security validated with traversal protection tests

---

**Next:** Execute Plan 06-03 to migrate Command Center UI onto the shared API
