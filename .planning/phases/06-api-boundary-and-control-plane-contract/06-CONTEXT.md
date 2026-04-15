# Phase 6: API Boundary and Control Plane Contract - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Extract the existing local orchestration runtime into a host-agnostic control-plane API that both the Command Center and external callers can use. This phase defines the shared service boundary, the durable HTTP run contract, and the parity rules between UI-driven runs and API-driven runs. It does not yet host the API in Azure Functions, add durable cloud worker dispatch, or broaden the product into a multi-user SaaS surface.

</domain>

<decisions>
## Implementation Decisions

### API surface and resource model
- The Phase 6 control plane should be a versioned REST surface rooted at `/api/v1`, not a collection of UI-only or framework-specific endpoints.
- The durable top-level resource is a **run**. The contract should center on `run_id`, current status, stage, pause state, routing state, agents, artifacts, and control actions.
- AG-UI streaming endpoints in `command_center/app.py` remain a specialized UI transport and debugger-friendly protocol surface; they are not the canonical external control-plane contract.
- The control-plane HTTP surface should separate run submission, run summary, timeline or event inspection, routing/agent inspection, artifact retrieval, and control actions into explicit resources instead of one overloaded RPC-style endpoint.

### Run actions and lifecycle over HTTP
- `POST /api/v1/runs` should create a durable run and return the initial run summary immediately, including `run_id`, status, stage, repo/workspace context, and the accepted task payload.
- Run mutation actions should stay explicit and command-like: continue, approve, retry, cancel, and append operator input should each have stable, dedicated POST actions under the run resource rather than one generic “do anything” payload.
- Read surfaces should be stable and browser-independent: run summary, current stage, pause reason, route metadata, specialist state, timeline/events, and artifact manifest must all be fetchable without depending on browser session state or AG-UI event streams.
- The API should preserve the existing durable run identity rules from Phase 1 and Phase 2: one stable run record across pauses, resumes, approvals, and retries, with attempts nested under that same run.

### Shared control-plane ownership
- The source of truth for run control must move out of UI-specific entrypoints. Phase 6 should extract a shared orchestration service layer that both `command_center/` and later Azure Functions can call directly.
- The existing `autogen_dashboard` session service, store, and schemas are the strongest donor assets for the durable run contract, but `command_center/` is now the active product surface and should consume the shared service rather than duplicate runtime ownership.
- Phase 6 should treat `autogen_dashboard/` as a compatibility donor and migration source, not as the long-term primary operator surface described in older Phase 5 documents.
- Route, stage, specialist, approval, validation, artifact, and workspace-freshness data should come from one shared run schema and service boundary rather than separate projections in `command_center/app.py` and `autogen_dashboard/app.py`.

### Auth posture and local-versus-cloud boundary
- Phase 6 should define an explicit request-auth boundary even if local development remains effectively open by default on loopback. Auth must be a pluggable policy, not handler-local branching.
- The contract should be ready for Azure Functions host auth in Phase 7: local no-auth or dev-auth is acceptable now, but the API shape should already separate caller identity and authorization from the orchestration handlers.
- The control-plane contract must not assume local CLI sessions, direct desktop access, or mutable local repo roots as part of the HTTP interface itself. Those are worker/runtime capabilities, not API invariants.
- Capability and execution-mode information should be visible in API payloads so future cloud callers can understand whether a run is local-tool-capable, cloud-safe, paused for approval, or blocked by unavailable execution capabilities.

### the agent's Discretion
- Exact route and artifact endpoint naming as long as the API stays versioned, resource-oriented, and consistent across local UI and external callers.
- Exact summary-versus-detail payload split as long as the default run summary is enough for dashboards and the detail surfaces expose timeline, routing, agents, and artifact drill-down cleanly.
- Exact implementation placement of the shared control-plane package as long as it is not owned by one UI shell and remains reusable by both the Command Center and Azure Functions.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and milestone scope
- `.planning/PROJECT.md` - defines the v1.1 milestone, local-first runtime, cloud API goal, and requirement that the HTTP API and operator surface share one orchestration contract.
- `.planning/REQUIREMENTS.md` - defines `API-01`, `API-02`, `API-03`, and `API-04`, which Phase 6 must satisfy.
- `.planning/ROADMAP.md` - defines the fixed Phase 6 boundary, success criteria, and plan split.
- `.planning/STATE.md` - records the active milestone, blockers, and prior decisions that constrain the API design.

### Prior phase contracts that Phase 6 must preserve
- `.planning/phases/01-workspace-and-durable-run-foundation/01-CONTEXT.md` - locks durable run identity, workspace targeting, and workspace freshness rules.
- `.planning/phases/02-manager-led-orchestration-core/02-CONTEXT.md` - locks the manager-owned stage machine, pause semantics, and stage visibility contract.
- `.planning/phases/03-specialist-delegation-and-routing-visibility/03-CONTEXT.md` - locks specialist state, route-lane control, and planned-versus-actual route visibility.
- `.planning/phases/04-autonomous-repo-execution-and-validation-guardrails/04-CONTEXT.md` - locks diff, validation, approval, and artifact semantics that the HTTP API must expose without reinterpretation.
- `.planning/phases/05-polished-operator-workbench/05-CONTEXT.md` - captures the earlier UI assumptions and reveals where Phase 6 must realign ownership now that `command_center/` is the active shell.

### Current runtime and API seams
- `command_center/app.py` - current Command Center HTTP app, AG-UI endpoint registration, repo catalog, and status surface.
- `maf_core/cli.py` - current process entrypoints for UI and DevUI, which show how the product boots today.
- `maf_core/config.py` - current runtime configuration, repo-root scoping, and fallback chain settings that any shared API service must respect.
- `maf_core/orchestration.py` - canonical stage, specialist, pause, and artifact-path contract that the API must surface directly.
- `maf_core/routing_policy.py` - route-lane semantics and route planning rules that the API must expose consistently.
- `maf_core/provider_fallback.py` - active route/fallback metadata model and capability-drift behavior.
- `autogen_dashboard/app.py` - existing REST-style session API with explicit run actions and SSE event feed; strongest donor for the HTTP contract.
- `autogen_dashboard/schemas.py` - existing durable run schema for summary, detail, routing, agents, approvals, and artifacts.
- `autogen_dashboard/session_runner.py` - existing session-service logic for run creation, control actions, and orchestration projection.
- `autogen_dashboard/session_store.py` - existing file-backed durable run persistence and artifact manifest model.

### Architecture and drift watchpoints
- `.planning/codebase/ARCHITECTURE.md` - maps the current runtime split between MAF runtime, command center, and legacy dashboard service layer.
- `.planning/codebase/STRUCTURE.md` - identifies where runtime ownership currently lives and where a shared control-plane package can be placed.
- `.planning/codebase/CONCERNS.md` - documents the current drift between `command_center/`, `autogen_dashboard/`, and planning docs, which Phase 6 should reduce.
- `README.md` - documents the current Command Center and DevUI launch surface and is the public-facing runtime reference that will need API updates.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `autogen_dashboard/session_runner.py`: already implements durable run creation, explicit control actions, stage-aware state projection, approvals, retries, and run summaries; this is the strongest donor for the shared control-plane service.
- `autogen_dashboard/session_store.py`: already persists metadata, transcript, events, attempts, runtime state, stage outputs, validation results, and artifact manifests under a stable run directory layout.
- `autogen_dashboard/schemas.py`: already provides a rich operator-facing run schema that includes workspace, routing, specialist, approval, and artifact data.
- `autogen_dashboard/app.py`: already demonstrates a REST-like action surface for sessions and can inform the Phase 6 HTTP route structure.
- `command_center/app.py`: already owns the active product HTTP app, repo catalog, status surface, and AG-UI streaming integration, making it the natural host for the new shared API layer once the runtime ownership is extracted.

### Established Patterns
- Durable run state is file-backed, JSON-oriented, and explicitly modeled rather than implicit in chat history.
- Manager, stage, routing, specialist, approval, validation, and artifact semantics are already shared concepts across the runtime and should remain the vocabulary of the API.
- UI-specific protocol surfaces exist beside richer REST-like session surfaces; Phase 6 should reduce this duplication by extracting shared control services instead of growing both paths.
- Local development is Windows-first and loopback-hosted, but the milestone explicitly requires a cloud-safe API contract that does not hard-wire local CLI assumptions into the HTTP layer.

### Integration Points
- A new host-agnostic control-plane service should sit between `command_center/app.py` and the existing `autogen_dashboard` session logic so both the UI and future Azure Functions host can drive the same run contract.
- `command_center/app.py` should evolve from a thin AG-UI shell into a consumer of the shared run-control endpoints rather than owning separate runtime concepts.
- `autogen_dashboard/app.py` should either delegate to the same shared service or be treated as a compatibility wrapper until it can be retired.
- `maf_core/cli.py` and `main.py` are the current process entrypoints and should remain thin after the control-plane extraction.

</code_context>

<specifics>
## Specific Ideas

- The external API should feel like an enterprise run-control surface, not a thin wrapper over browser interactions.
- AG-UI and DevUI stay useful, but they should sit on top of the same run contract rather than define it.
- The operator UI should eventually be able to fetch run status, routing, agents, timeline, and artifacts from the same endpoints that Azure Functions will expose.
- Phase 6 should explicitly clean up the current planning drift: `command_center/` is the active UI, while `autogen_dashboard/` is now a donor runtime and compatibility layer.

</specifics>

<deferred>
## Deferred Ideas

- Azure Functions host wiring, local Core Tools validation, and cloud route/auth settings - Phase 7
- Background worker boundary, cloud-safe execution profiles, and local-only provider rejection/rerouting - Phase 8
- Shared multi-user auth, external operator collaboration, and broader product tenancy - later milestone

</deferred>

---

*Phase: 06-api-boundary-and-control-plane-contract*
*Context gathered: 2026-03-22*
