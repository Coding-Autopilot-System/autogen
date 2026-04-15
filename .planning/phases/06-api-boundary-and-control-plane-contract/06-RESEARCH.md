# Phase 6: API Boundary and Control Plane Contract - Research

**Researched:** 2026-03-22
**Domain:** Shared control-plane extraction for durable run submission, status inspection, artifact retrieval, and run actions over HTTP, with one contract consumed by both `command_center/` and compatibility surfaces
**Confidence:** HIGH

<user_constraints>
## User Constraints (from `06-CONTEXT.md`)

### Locked Decisions
- Phase 6 is about a host-agnostic control-plane API, not Azure Functions hosting, worker dispatch, or multi-user SaaS.
- The canonical HTTP surface must be versioned and rooted at `/api/v1`.
- The durable top-level resource is a **run**, centered on `run_id`, status, stage, pause state, routing state, agents, artifacts, and explicit control actions.
- `command_center/app.py` remains the active product HTTP shell, but it must stop owning a separate runtime contract from the external API.
- `autogen_dashboard/` is a donor and compatibility source, not the long-term product surface.
- AG-UI endpoints in `command_center/app.py` are useful specialized transport, but they are not the canonical external contract.
- Auth must be a pluggable boundary. Loopback can remain effectively open for local use, but handler-local auth branching is the wrong shape.
- The HTTP contract must not assume direct desktop access, mutable repo roots, or installed CLI sessions as API invariants.

### the agent's Discretion
- Exact package placement for the shared control-plane code, as long as it is not UI-owned and is reusable by later hosts.
- Exact split between summary and detail payloads, as long as dashboards can load a run without browser-only state and drill into timeline, routing, agents, and artifacts cleanly.
- Exact endpoint naming for route, agent, artifact, and event detail resources, as long as the surface stays resource-oriented and stable.

### Deferred Ideas (OUT OF SCOPE)
- Azure Functions host wiring, Core Tools validation, and cloud auth settings from Phase 7
- Background worker handoff and cloud-safe execution profiles from Phase 8
- Shared multi-user collaboration, tenancy, and non-local auth workflows

</user_constraints>

<research_summary>
## Summary

Phase 6 should be planned as a service extraction and contract consolidation phase, not as a brand-new API implementation. The codebase already has most of the durable run model:
- `autogen_dashboard/schemas.py` already defines the rich run payload shape
- `autogen_dashboard/session_store.py` already persists runs, attempts, runtime state, stage summaries, validation output, and artifact manifests
- `autogen_dashboard/session_runner.py` already implements create, append input, approval, retry, cancel, event emission, and orchestration projection
- `maf_core/orchestration.py` already defines the canonical stage machine, pause kinds, specialist roster, and stage output structure
- `maf_core/routing_policy.py` and `maf_core/provider_fallback.py` already define planned-vs-actual routing, fallback history, and capability drift

The main problem is ownership drift. Today:
- `command_center/app.py` owns the active shell but only exposes AG-UI streaming plus lightweight catalog/status endpoints
- `autogen_dashboard/app.py` exposes the richer run-control REST surface, but it is attached to legacy naming (`sessions`) and a large legacy-owned service
- `autogen_dashboard/session_runner.py` still depends on `autogen_starter.config` and `autogen_starter.providers`, so it is not a straight drop-in shared control-plane module

**Primary recommendation:** plan Phase 6 as three sequential plans aligned to the roadmap:
1. extract a shared `RunStore`, `RunService`, and `Run*` contract package into the active shared runtime area, preserving the current on-disk run layout
2. add a versioned `/api/v1/runs` router that maps cleanly to API-01 through API-04 and is mounted by `command_center/app.py`
3. move Command Center status/timeline/routing/artifact reads onto the shared run API, while keeping `autogen_dashboard/app.py` as a compatibility wrapper over the same service until it can be retired

### Requirement Mapping

| Requirement | What Phase 6 must expose |
|---------|---------|
| `API-01` | `POST /api/v1/runs` creates a durable run, persists it immediately, and returns initial run summary with `run_id` |
| `API-02` | `GET /api/v1/runs/{run_id}` returns status, current stage, pause reason, and last route metadata without UI session state |
| `API-03` | `GET /api/v1/runs/{run_id}/timeline`, `/agents`, `/routing`, `/artifacts`, and `/events` expose inspectable durable run detail |
| `API-04` | `POST /api/v1/runs/{run_id}/actions/continue`, `/approve`, `/retry`, `/cancel`, and `/operator-input` mutate the existing run explicitly |

### Migration Conclusion

Do not plan a big-bang rewrite of `command_center/` or a direct rename of every `Session*` symbol in one shot. The safer path is:
- preserve disk layout and JSON field semantics first
- extract donor logic from `autogen_dashboard/` into a shared package under the active runtime
- add compatibility wrappers so both `command_center/` and `autogen_dashboard/` call the same service during the transition

</research_summary>

<standard_stack>
## Standard Stack

Phase 6 should deepen the existing Python/FastAPI/JSON/file-backed stack rather than introduce new infrastructure.

### Core
| Library / Module | Version | Purpose | Why Standard Here |
|---------|---------|---------|--------------|
| `FastAPI` | in-repo | HTTP router and dependency boundaries | Already used by both `command_center/app.py` and `autogen_dashboard/app.py` |
| `pydantic` models in `autogen_dashboard/schemas.py` | in-repo | Durable request/response contract | Already contains most of the fields Phase 6 needs |
| `SessionStore` in `autogen_dashboard/session_store.py` | in-repo | Durable run persistence and artifact manifesting | Already gives Phase 6 a usable file-backed run store with atomic JSON writes |
| `RunOrchestrationState` in `maf_core/orchestration.py` | in-repo | Canonical stage, pause, specialist, and stage-output contract | Already shared conceptually across the product |
| `build_routing_plan(...)` and route metadata in `maf_core/routing_policy.py` and `maf_core/provider_fallback.py` | in-repo | Planned route, attempt history, and capability drift | Already the source of truth for route visibility |

### Recommended Shared Package Shape
| New package area | Source donor | Responsibility |
|---------|---------|---------|
| `maf_core/control_plane/contracts.py` | `autogen_dashboard/schemas.py` | Canonical `Run*` request/response models |
| `maf_core/control_plane/store.py` | `autogen_dashboard/session_store.py` | Durable run persistence, attempts, events, and artifacts |
| `maf_core/control_plane/service.py` | `autogen_dashboard/session_runner.py` | Create/get/list/control runs and project orchestration state |
| `maf_core/control_plane/router.py` | `autogen_dashboard/app.py` | `/api/v1` FastAPI router with dependency injection |
| `maf_core/control_plane/auth.py` | new, small | Pluggable auth policy boundary, loopback-open by default |

### Supporting
| Library / Module | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `fastapi.testclient.TestClient` | in-repo | REST contract regression tests | Use for `/api/v1` and compatibility-route parity |
| `unittest` | stdlib | Repo-standard automated verification | Use for service, store, and router contract tests |
| `python -m compileall` | stdlib | Syntax sanity | Run after package extraction and compatibility rewiring |
| `node --check` | local tool | Static Command Center JS sanity | Run when `command_center/static/app.js` changes in parity work |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Extracting into `maf_core/control_plane/` | New top-level `control_plane/` package | Cleaner naming, but weaker fit with repo convention that new shared runtime behavior belongs in `maf_core/` |
| Preserving file-backed run storage in Phase 6 | Introduce a database now | Better long-term scale, but unnecessary scope and migration risk for this phase |
| Keeping `sessions` naming internally during extraction | Hard rename everything to `runs` immediately | More semantically correct, but high churn across tests, compatibility code, and UI adapters |
| Command Center-only API work | Ignore `autogen_dashboard` until later | Faster short term, but fails the requirement that the API and UI share one contract |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Shared control-plane package with thin host adapters
**What:** Put canonical run contracts, service logic, storage, and router composition in one shared package, then have `command_center/app.py` and `autogen_dashboard/app.py` mount or delegate to it.
**When to use:** Always for durable run lifecycle, status, and artifact APIs.
**Example:** `command_center/app.py` should include a shared `/api/v1` router instead of inventing run endpoints locally; `autogen_dashboard/app.py` should become a compatibility shell around the same service.

### Pattern 2: Contract-first extraction before runtime replacement
**What:** Extract request/response models and storage first, then peel execution logic out of `autogen_dashboard/session_runner.py`.
**When to use:** `06-01`, because the donor file is very large and still tied to legacy provider/config modules.
**Example:** Move `SessionStore` and `SessionSummary`-style models first, then split the public control actions from the internal execution engine behind a `RunExecutor` seam.

### Pattern 3: Resource-oriented runs with explicit action endpoints
**What:** Treat run state as resources and mutations as command subresources.
**When to use:** For API-01 through API-04.
**Recommended shape:**
- `GET /api/v1/runs`
- `POST /api/v1/runs`
- `GET /api/v1/runs/{run_id}`
- `GET /api/v1/runs/{run_id}/timeline`
- `GET /api/v1/runs/{run_id}/agents`
- `GET /api/v1/runs/{run_id}/routing`
- `GET /api/v1/runs/{run_id}/artifacts`
- `GET /api/v1/runs/{run_id}/artifacts/{artifact_path:path}`
- `GET /api/v1/runs/{run_id}/events`
- `POST /api/v1/runs/{run_id}/actions/continue`
- `POST /api/v1/runs/{run_id}/actions/approve`
- `POST /api/v1/runs/{run_id}/actions/retry`
- `POST /api/v1/runs/{run_id}/actions/cancel`
- `POST /api/v1/runs/{run_id}/actions/operator-input`

### Pattern 4: Compatibility wrappers instead of immediate breaking changes
**What:** Keep old `autogen_dashboard` route names alive as adapters during Phase 6, but make them call the shared service.
**When to use:** For migration safety and test continuity.
**Example:** `autogen_dashboard/app.py` can keep `/api/sessions/{session_id}/retry` temporarily by mapping to `RunService.retry(run_id)` and returning a compatibility-shaped payload.

### Pattern 5: Command Center reads shared run state; AG-UI remains specialized transport
**What:** Let AG-UI continue handling live conversational protocol, but move run list, run detail, routing, agents, artifacts, and control actions onto the shared `/api/v1` contract.
**When to use:** `06-03` parity work.
**Example:** the right-rail and status surfaces in Command Center should load from `/api/v1/runs/{run_id}` and subresources instead of inferring state only from AG-UI stream events.

### Recommended Extraction Boundary

The practical split in `autogen_dashboard/session_runner.py` is:
- **Keep as shared control-plane logic:** create/get/list/control actions, event emission, workspace refresh, attempt bookkeeping, orchestration projection
- **Wrap behind an executor seam:** actual run execution, provider selection, and any remaining `autogen_starter.*` calls
- **Do not keep in UI code:** request validation, run state mutation, artifact manifest building, or event sequencing

### Anti-Patterns to Avoid
- **Third run contract:** do not create a separate `command_center`-specific run model beside `autogen_dashboard` and `maf_core`
- **Big-bang rename:** do not force every `Session*` symbol to become `Run*` in the same plan wave
- **Handler-owned auth rules:** do not scatter local auth decisions through individual FastAPI endpoints
- **Absolute-path artifact APIs:** do not expose arbitrary filesystem reads; keep artifact retrieval manifest-relative to the run directory

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that already have strong in-repo donor implementations:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Durable run disk layout | New storage tree or DB abstraction in Phase 6 | The existing layout in `autogen_dashboard/session_store.py` | It already persists metadata, transcript, events, runtime state, attempts, and stage artifacts |
| Stage and pause contract | New API-only stage model | `RunOrchestrationState`, `StageRecord`, `StageSummary`, and pause kinds from `maf_core/orchestration.py` | This is already the canonical orchestration vocabulary |
| Route history and capability drift | New ad-hoc route summary DTOs | `route_plan`, `route_attempts`, and `capability_changes` from `maf_core/routing_policy.py` and `maf_core/provider_fallback.py` | The data is already modeled and operator-visible |
| Artifact manifest | Custom endpoint-only file lookup map | `_build_artifact_manifest(...)` in `autogen_dashboard/session_store.py` | It already gives a stable relative-path manifest per run |
| Compatibility routing | Forked duplicate FastAPI handlers in both apps | Shared `APIRouter` plus thin compatibility wrappers | Keeps the API and UI on one service boundary |
| Event sequencing | New queue or broker abstraction for local Phase 6 | Existing `SessionEvent` sequencing plus store-backed JSONL event log | Enough for local durable run inspection and TestClient validation |

**Key insight:** Phase 6 should hand-roll as little new domain logic as possible. The new work is packaging, naming, endpoint shape, and ownership cleanup.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Extracting the service but leaving it dependent on `autogen_dashboard` and `autogen_starter`
**What goes wrong:** The code moves files around but the shared control plane is still logically owned by legacy packages.
**How to avoid:** Move the canonical contract into `maf_core/control_plane/`, and treat `autogen_dashboard/*` as adapters or donors only. Call out early that `autogen_dashboard/session_runner.py` currently imports `autogen_starter.config` and `autogen_starter.providers`, so execution needs an adapter seam.

### Pitfall 2: Treating AG-UI streaming as the durable API
**What goes wrong:** Command Center keeps reading transient stream state, and external callers still cannot inspect runs without a browser protocol client.
**How to avoid:** Make `/api/v1/runs/{run_id}` and subresources the source of truth for status, stage, pause, routing, agents, timeline, and artifacts. Keep AG-UI only for interactive live transport.

### Pitfall 3: Mixing summary, detail, and control semantics into one endpoint
**What goes wrong:** The phase reproduces the current dashboard-style RPC surface under a new prefix and loses clarity.
**How to avoid:** Keep run reads resource-oriented and mutations explicit. `POST /api/v1/runs` creates; `GET /api/v1/runs/{run_id}` summarizes; `/timeline`, `/agents`, `/routing`, `/artifacts`, `/events` drill down; `/actions/*` mutates.

### Pitfall 4: Breaking existing on-disk runs during extraction
**What goes wrong:** Existing tests and locally created runs stop hydrating because the directory layout changed mid-phase.
**How to avoid:** Preserve `state/sessions/{run_id}` layout and relative artifact paths during Phase 6. If names change internally, adapt at the model layer, not on disk.

### Pitfall 5: Leaking local-machine assumptions into the external contract
**What goes wrong:** The API returns absolute repo paths, assumes local CLI availability, or makes future hosting impossible.
**How to avoid:** Return run capability metadata and manifest-relative artifacts. Treat local repo roots and CLI tools as runtime capabilities, not API invariants.

### Pitfall 6: Missing Command Center parity work
**What goes wrong:** `/api/v1` exists, but the active UI still depends on unrelated app-owned payloads, so the product keeps drifting.
**How to avoid:** Reserve `06-03` for real parity: Command Center should fetch run data from the shared control-plane API and stop treating `autogen_dashboard` as the only durable run surface.

</common_pitfalls>

<code_examples>
## Code Examples

Verified in-repo patterns worth preserving:

### Current REST donor surface
```python
# Source: `autogen_dashboard/app.py`
# Pattern: explicit create/get/list/action endpoints plus event streaming
# Donor actions already exist for create, append input, approve/reject, run, cancel, and retry.
```

### Current durable run contract donor
```python
# Source: `autogen_dashboard/schemas.py`
# Pattern: `SessionSummary` and `SessionDetail` already include status, pause, stage timeline,
# stage outputs, specialist states, routing history, artifact manifest, and transcript/events.
```

### Current run persistence donor
```python
# Source: `autogen_dashboard/session_store.py`
# Pattern: `_build_artifact_manifest(...)` and run-relative paths for metadata, runtime state,
# stage summaries, change artifacts, validation artifacts, and attempts.
```

### Current orchestration contract donor
```python
# Source: `maf_core/orchestration.py`
# Pattern: `RunOrchestrationState` is the canonical stage/pause/specialist state machine
# and already serializes cleanly to JSON for persistence and HTTP projection.
```

### Current route metadata donor
```python
# Source: `maf_core/provider_fallback.py`
# Pattern: `_merge_route_metadata(...)` already emits `route_lane`, `route_tier`,
# `route_plan`, `route_attempts`, `fallback_used`, `tools_available`, and capability changes.
```

### Current Command Center host seam
```python
# Source: `command_center/app.py`
# Pattern: the active host already creates a FastAPI app and can mount additional shared routers
# without changing the CLI entrypoint in `maf_core/cli.py`.
```

</code_examples>

## Validation Architecture

Phase 6 validation should prove three things locally:
1. the extracted shared service preserves durable run behavior
2. the new `/api/v1` router satisfies API-01 through API-04
3. Command Center and compatibility routes observe the same run data instead of parallel contracts

### Service-Level Validation
- Use stdlib `unittest` against the shared `RunService` with a temporary store rooted under `.tmp-tests`, following the pattern in `tests/test_run_persistence.py`.
- Cover:
  - create run persists metadata and returns a stable `run_id` for `API-01`
  - continue, approve, retry, cancel, and operator input update the same durable run for `API-04`
  - orchestration projection hydrates status, current stage, pause kind, route metadata, specialist state, and artifacts for `API-02` and `API-03`
  - manifest-relative artifact retrieval never escapes the run directory

### Router Contract Validation
- Use `fastapi.testclient.TestClient`, following `tests/test_command_center.py` and `tests/test_phase3_api.py`.
- Add focused Phase 6 tests for:
  - `POST /api/v1/runs` returning initial run summary with `run_id`, `status`, `current_stage`, and accepted task payload
  - `GET /api/v1/runs/{run_id}` returning status, pause, route, and workspace summary
  - `GET /api/v1/runs/{run_id}/timeline`, `/agents`, `/routing`, `/artifacts`, and `/events`
  - `POST /api/v1/runs/{run_id}/actions/continue|approve|retry|cancel|operator-input`
  - compatibility parity where old `autogen_dashboard` routes and new `/api/v1` routes return the same underlying run state

### Command Center Parity Validation
- Keep `TestClient(create_command_center_app(...))` tests and extend them so `command_center/app.py` exposes the shared `/api/v1` router.
- Add parity tests that create a run through the shared API, then confirm Command Center run-status endpoints or UI-facing fetch helpers read the same run summary and artifact data.
- Treat AG-UI streaming tests as secondary smoke coverage, not the primary proof of Phase 6 correctness.

### Static Sanity
- `.\.venv\Scripts\python.exe -m compileall maf_core command_center autogen_dashboard tests main.py`
- `node --check command_center\static\app.js`

### Recommended Test Targets
- `tests.test_phase6_service`
- `tests.test_phase6_api_contract`
- `tests.test_phase6_command_center_parity`
- existing regression coverage in `tests.test_command_center`, `tests.test_phase3_api`, and `tests.test_run_persistence`

### Recommended Commands
- `.\.venv\Scripts\python.exe -m unittest tests.test_phase6_service tests.test_phase6_api_contract -v`
- `.\.venv\Scripts\python.exe -m unittest tests.test_phase6_command_center_parity tests.test_command_center -v`
- `.\.venv\Scripts\python.exe -m unittest tests.test_run_persistence tests.test_phase3_api -v`
- `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`

<open_questions>
## Open Questions

1. **Should Phase 6 keep the current file-backed run layout exactly, or rename `state/sessions` to `state/runs` now?**
   - What we know: tests and donors already expect the current disk layout.
   - Recommendation: keep the current layout through Phase 6 and revisit naming only after the shared package is stable.

2. **How far should the execution engine be extracted from `autogen_dashboard/session_runner.py` in this phase?**
   - What we know: the public lifecycle and persistence logic are valuable donors, but execution still leans on `autogen_starter.*`.
   - Recommendation: extract a shared control-plane service plus executor interface in Phase 6, but do not require a full runtime-engine rewrite to satisfy the API contract.

3. **Should the canonical detail surface be one big `GET /api/v1/runs/{run_id}` payload or multiple subresources?**
   - What we know: the current schema can already return a large detail payload.
   - Recommendation: keep `GET /api/v1/runs/{run_id}` as the default summary-plus-core-status payload, then split heavy drill-down reads into `/timeline`, `/agents`, `/routing`, `/artifacts`, and `/events`.

4. **Should `reject` remain a first-class action even though `API-04` does not name it explicitly?**
   - What we know: `autogen_dashboard/app.py` already exposes reject, and `approval_decisions` already model negative decisions.
   - Recommendation: keep `reject` as a compatibility alias or explicit action if it costs little, but do not let it complicate the minimum Phase 6 contract.

5. **Where should repo discovery helpers live once the control plane is extracted?**
   - What we know: `command_center/app.py` and `autogen_dashboard/session_runner.py` both rely on repo-context helpers currently under `autogen_dashboard/`.
   - Recommendation: if this dependency blocks clean extraction, move repo-context helpers into a shared runtime utility module during `06-01`; otherwise defer that relocation behind compatibility imports.

</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `.planning/phases/06-api-boundary-and-control-plane-contract/06-CONTEXT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/STATE.md`
- `.planning/PROJECT.md`
- `.planning/ROADMAP.md`
- `command_center/app.py`
- `autogen_dashboard/app.py`
- `autogen_dashboard/schemas.py`
- `autogen_dashboard/session_runner.py`
- `autogen_dashboard/session_store.py`
- `maf_core/cli.py`
- `maf_core/config.py`
- `maf_core/orchestration.py`
- `maf_core/routing_policy.py`
- `maf_core/provider_fallback.py`
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/STRUCTURE.md`
- `.planning/codebase/CONCERNS.md`
- `README.md`

### Secondary (MEDIUM confidence)
- `.planning/phases/05-polished-operator-workbench/05-RESEARCH.md`
- `tests/test_command_center.py`
- `tests/test_phase3_api.py`
- `tests/test_run_persistence.py`

</sources>

<metadata>
## Metadata

**Research scope:**
- shared control-plane package extraction
- REST contract shape for `API-01`, `API-02`, `API-03`, and `API-04`
- migration path from `autogen_dashboard` donors to shared runtime ownership
- Command Center and external API parity
- local validation architecture for service, router, and static sanity

**Recommended execution shape:** 3 sequential plans with service-first extraction, then `/api/v1` router delivery, then Command Center parity and compatibility cleanup

</metadata>
