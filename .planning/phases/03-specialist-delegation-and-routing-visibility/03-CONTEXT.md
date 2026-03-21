# Phase 3: Specialist Delegation and Routing Visibility - Context

**Gathered:** 2026-03-21
**Status:** Ready for planning

<domain>
## Phase Boundary

Make delegation and model or provider behavior auditable and understandable. This phase covers which specialists participate in a run, how their state and handoffs are recorded, how route lanes and model choice are exposed before the run starts, and how routing and fallback behavior appears in the operator surface. It does not yet add autonomous repo editing, validation execution, or the final polished visual system for the product UI.

</domain>

<decisions>
## Implementation Decisions

### Specialist roster and ownership
- Keep the manager as the only canonical run owner. Specialists are visible participants inside that one run, not separate top-level runs.
- Phase 3 should make `planner`, `researcher`, `implementer`, and `reviewer` first-class visible specialists because those roles already exist in the active runtime and map cleanly to the operator mental model.
- `validation` remains manager-owned terminal synthesis in Phase 3 instead of becoming a fifth visible specialist. The reviewer can surface validation concerns, while the manager owns the final validation status.
- Each specialist must keep one explicit responsibility and emit structured handoffs. Do not introduce an unconstrained agent swarm or dynamic role creation in this phase.

### Specialist state and handoff contract
- Persist per-specialist state inside the same durable run record, nested under orchestration artifacts instead of creating separate session histories.
- Each specialist record must expose role, current task, latest output summary, latest handoff target, state, timestamps, and whether it is waiting on manager approval or another specialist.
- Handoffs must be recorded as structured events or edges with `from`, `to`, `reason`, `requested_by`, and `status` fields so the operator can see what moved work forward.
- Specialists that have not started yet should still be visible as reserved participants with an `idle` or `not_started` state rather than disappearing from the operator view.

### Route lane control and model selection
- The main pre-run control should be a route-lane selector, not only a raw provider dropdown. The operator should choose a lane such as `Auto`, `Deep`, `Balanced`, or `Fast`, then optionally pin a specific model in an advanced control.
- The default route is `Auto`, which keeps the current smart routing behavior but makes the selected lane explicit before the run starts.
- Route policy stays API-first, strongest-to-cheapest within the chosen lane, with CLI providers last in the fallback chain unless the operator explicitly pins a CLI provider.
- Specialists may have different default route expectations by role, but they still inherit one run-level lane contract that the manager can override only when capability or cost reasons are explicit.

### Routing and fallback visibility
- Every routed turn must record both the planned route and the actual route outcome: selected lane, intended primary provider and model, actual provider and model used, fallback attempts, and final capability state.
- Capability drift caused by fallback, especially API-to-CLI fallback, must be explicit in the operator surface through badges such as `tools unavailable`, `approval boundary changed`, or `structured tools off`.
- Routing rationale should be short and operator-readable. Show the classification reason and fallback summary without exposing raw quota or stack traces by default.
- Route visibility belongs in structured route cards and timelines, not buried only inside message text or trace payloads.

### Operator surface structure for Phase 3
- The operator surface should gain structural views for `Overview`, `Agents`, `Routing`, and `Artifacts/Traces` so specialist work and route behavior are inspectable without reading a single transcript stream end-to-end.
- The `Overview` stays manager-oriented and shows current stage, approval state, and the active specialist summary. The `Agents` view shows one panel per specialist with status, current task, latest output, and handoff state.
- The `Routing` view shows lane selection, route cards, fallback chain activity, capability changes, and the exact provider and model used per stage or specialist turn.
- Rounded cards, chips, and clearly separated state blocks should be introduced now because they improve comprehension, but deeper visual polish, animation, and final stylistic system remain Phase 5 work.

### the agent's Discretion
- Exact naming of route lanes as long as there is one smart default lane, one faster or cheaper lane, one deeper lane, and advanced model pinning remains available.
- Exact rendering choice for specialist views, tabs versus split panels, as long as specialist ownership, state, task, output, and handoff information remain visible.
- Exact color palette, iconography, and trace-density defaults for Phase 3 as long as fallback and capability drift are visually obvious.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and phase scope
- `.planning/PROJECT.md` - defines the local-first operator workbench, the one-prompt manager model, and the requirement that specialist visibility become a first-class product feature.
- `.planning/REQUIREMENTS.md` - defines `AGNT-01`, `AGNT-02`, `AGNT-03`, `ROUT-01`, `ROUT-02`, and `ROUT-03`, which this phase must satisfy.
- `.planning/ROADMAP.md` - defines the fixed Phase 3 boundary, success criteria, and plan split.
- `.planning/STATE.md` - records the active focus, prior phase decisions, and current blockers entering Phase 3.
- `.planning/phases/02-manager-led-orchestration-core/02-CONTEXT.md` - locks the manager-owned stage machine, pause semantics, and operator-stage visibility that Phase 3 must extend rather than replace.

### Shared runtime seams
- `.planning/codebase/ARCHITECTURE.md` - maps the current runtime layers and shows where specialist, routing, and operator-surface changes belong.
- `.planning/codebase/STRUCTURE.md` - identifies the active MAF modules, dashboard operator surface, and entity wrappers that Phase 3 should build on.
- `.planning/codebase/CONVENTIONS.md` - captures the module, typing, and error-handling patterns that new specialist and routing code should follow.
- `maf_starter/orchestration.py` - defines the canonical stage names and the current stage record contract that specialist state should extend.
- `maf_starter/team_factory.py` - defines the current `planner`, `researcher`, `implementer`, and `reviewer` workflow participants.
- `maf_starter/agent_factory.py` - defines the shared specialist instruction and tool boundary used by the active runtime.

### Routing and operator-surface seams
- `maf_starter/routing_policy.py` - defines the current lane-like tier selection and fallback ordering that Phase 3 should surface and refine.
- `maf_starter/provider_fallback.py` - defines the current route metadata, fallback metadata, and capability boundary between API and CLI providers.
- `maf_starter/devui_patches.py` - shows the existing route banner and route trace payload shape, which must be treated as local-console glue rather than the final product contract.
- `autogen_dashboard/schemas.py` - defines the current persisted operator-facing run schema and is the correct seam for adding per-specialist and routing fields.
- `autogen_dashboard/session_runner.py` - owns the active run summary, orchestration state application, and stage-to-operator projection logic.
- `autogen_dashboard/static/index.html` - defines the current operator shell layout that Phase 3 should extend with specialist and routing surfaces.
- `autogen_dashboard/static/app.js` - contains the current client-side normalization and rendering logic for orchestration, route metadata, and cards.
- `docs/DEVUI_CUSTOMIZATION.md` - documents why DevUI is a local engineering console and why product-grade specialist visibility should land in the dashboard contract first.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `maf_starter/team_factory.py`: already assembles the exact specialist roster Phase 3 needs, so the phase should formalize and expose those roles rather than invent new participants first.
- `maf_starter/orchestration.py`: already centralizes stage names and records, making it the right place to add specialist-state and handoff primitives shared across runtime and UI.
- `maf_starter/routing_policy.py`: already classifies prompts into `simple`, `standard`, and `deep` lanes, which can evolve into explicit operator-selectable route lanes.
- `maf_starter/provider_fallback.py`: already emits route metadata, fallback flags, and tool-availability state. Phase 3 should extend that payload instead of rebuilding routing traces from scratch.
- `autogen_dashboard/schemas.py` and `autogen_dashboard/session_runner.py`: already persist orchestration summaries, route metadata, and stage outputs, so per-agent and route-card data should be added here.
- `autogen_dashboard/static/app.js` and `autogen_dashboard/static/index.html`: already render a card-based operator shell with approval, orchestration, and transcript regions that can absorb agent and routing tabs.

### Established Patterns
- The manager remains the top-level authority for run progression; specialist visibility should layer on top of the manager contract, not bypass it.
- Structured JSON payloads and file-backed run state are the accepted durability model for the active operator surface.
- Routing metadata already centers on provider, model, tier, rationale, fallback, and capability flags. Phase 3 should deepen that contract, not replace the vocabulary.
- DevUI patching is useful for local inspection but too brittle for the durable product UI, so specialist and routing visibility should be implemented primarily in the dashboard path.

### Integration Points
- `maf_starter/team_factory.py` and `maf_starter/orchestration.py` are the main seams for adding a shared specialist roster, handoff model, and per-agent state.
- `maf_starter/routing_policy.py` and `maf_starter/provider_fallback.py` are the main seams for explicit route lanes, route rationale, fallback attempt recording, and capability drift reporting.
- `autogen_dashboard/session_runner.py` is the projection seam from manager and routing internals into persisted operator-facing run data.
- `autogen_dashboard/static/index.html`, `autogen_dashboard/static/app.js`, and `autogen_dashboard/static/styles.css` are the main seams for adding per-agent tabs, routing views, and route cards without depending on DevUI.

</code_context>

<specifics>
## Specific Ideas

- The operator should be able to tell, at a glance, who is doing what right now and which model actually answered.
- Route information should appear in dedicated cards or strips above or beside the relevant content, not as raw text buried inside the assistant bubble.
- CLI providers remain resilience paths and specialist options, not the default smart route for normal runs.
- The eventual Azure Function or REST surface should reuse the same specialist-state and route-metadata payloads rather than inventing a second contract later.

</specifics>

<deferred>
## Deferred Ideas

- Final conversation bubble polish, opacity layers, motion system, and full operator-grade visual language - Phase 5
- Autonomous file editing, diff capture, and validation execution guardrails - Phase 4
- Shared multi-user cloud operator surface or Azure-hosted control plane - later cloud phase

</deferred>

---

*Phase: 03-specialist-delegation-and-routing-visibility*
*Context gathered: 2026-03-21*
