# Phase 6, Plan 01 - Summary

**Phase:** 06-api-boundary-and-control-plane-contract
**Plan:** 01
**Status:** ✅ Complete
**Completed:** 2026-03-22

---

## Objective

Extract a shared control-plane package with canonical run contracts, durable persistence, and lifecycle service logic from `autogen_dashboard/` donors.

---

## Deliverables

### Files Created

1. **maf_core/control_plane/__init__.py** (3 lines)
   - Package marker for shared control-plane

2. **maf_core/control_plane/contracts.py** (311 lines)
   - Canonical `Run*` models migrated from `autogen_dashboard/schemas.py`
   - `RunSummary`, `RunDetail`, `CreateRunRequest`, `RunEvent`
   - Supporting models: `RepoContext`, `StageTimelineEntry`, `SpecialistStateModel`, `RouteAttemptModel`, etc.
   - All field names and structure preserved from donor schemas

3. **maf_core/control_plane/store.py** (448 lines)
   - Durable run persistence migrated from `autogen_dashboard/session_store.py`
   - `RunStore` class with file-backed storage under `state/sessions/{run_id}/`
   - Methods for saving/loading run metadata, transcript, events, artifacts, stage outputs, validation results
   - `_build_artifact_manifest()` for manifest-relative artifact paths
   - All `session_id` → `run_id` and `Session*` → `Run*` type migrations complete

4. **maf_core/control_plane/service.py** (328 lines)
   - `RunService` class with control-plane API methods
   - Lifecycle: `create_run`, `get_run`, `list_runs`
   - Control actions: `continue_run`, `approve`, `retry`, `cancel`, `append_operator_input`
   - Projection methods: `get_timeline`, `get_agents`, `get_routing`, `get_artifacts`, `get_events`
   - Execution stubbed behind `_execute_run()` placeholder (deferred to later phases)

5. **tests/test_phase6_service.py** (283 lines)
   - Service-level validation for API-01 through API-04
   - 9 test methods covering create, get, control actions, timeline, agents, routing, artifacts, events, list
   - All tests passing

---

## Verification Results

✅ All tasks completed
✅ `python -m compileall maf_core/control_plane` - No errors
✅ `python -m unittest tests.test_phase6_service -v` - 9 tests, all passed
✅ Shared control-plane package exists under `maf_core/control_plane/`
✅ Run contracts, store, and service extracted from `autogen_dashboard/` donors
✅ Service preserves durable run identity, workspace, stage, routing, specialist, and artifact semantics

---

## API Coverage

### API-01: Create Run
- ✅ `create_run()` persists run immediately
- ✅ Returns `RunDetail` with stable `run_id`
- ✅ Workspace snapshot captured
- ✅ Initial status is "queued"

### API-02: Get Run Status
- ✅ `get_run()` returns `RunDetail`
- ✅ Status, current_stage, pause_kind projected correctly
- ✅ Route metadata available

### API-03: Inspect Run Detail
- ✅ `get_timeline()` returns stage timeline
- ✅ `get_agents()` returns specialist states
- ✅ `get_routing()` returns route plan, attempts, capability changes
- ✅ `get_artifacts()` returns manifest-relative artifact paths
- ✅ `get_events()` returns event log

### API-04: Control Actions
- ✅ `continue_run()` updates status to "running"
- ✅ `approve()` records approval decision
- ✅ `retry()` creates new attempt
- ✅ `cancel()` updates status to "stopped"
- ✅ `append_operator_input()` adds operator message to transcript
- ✅ All actions persist to same run_id

---

## Key Design Decisions

1. **Preserved disk layout**: Kept `state/sessions/{run_id}/` directory structure to maintain compatibility with existing runs

2. **Execution stub**: `_execute_run()` raises `NotImplementedError` with clear message that Phase 6 focuses on control-plane extraction, not execution engine migration

3. **Type migration**: All `Session*` types renamed to `Run*`, but internal `session_id` parameter names changed to `run_id` for clarity

4. **Event emission**: Events emitted immediately after actions and detail reloaded to ensure event_count is accurate

5. **Workspace snapshot**: Stubbed minimal implementation for Phase 6; production would call `maf_core.tools.build_repo_context_snapshot()`

---

## Dependencies for Next Plan

The shared control-plane package is now ready for:
- **06-02**: Add versioned `/api/v1/runs` router that uses `RunService`
- **06-03**: Command Center parity - migrate UI to consume shared API

---

## Notes

- All donor logic successfully extracted from `autogen_dashboard/` into shared package
- No breaking changes to existing disk layout or persisted run structure
- Service is host-agnostic and ready for both Command Center and Azure Functions
- Test coverage validates all core API requirements
- Execution engine remains in `autogen_dashboard/session_runner.py` until later phase

---

**Next:** Execute Plan 06-02 to add REST API router
