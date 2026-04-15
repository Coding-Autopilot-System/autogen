# Phase 3: Specialist Delegation and Routing Visibility - Research

**Researched:** 2026-03-21
**Domain:** Specialist-state visibility, route-lane control, and routing/fallback transparency over the existing local MAF runtime and dashboard operator surface
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Keep the manager as the only canonical run owner while surfacing `planner`, `researcher`, `implementer`, and `reviewer` as first-class visible specialists.
- Persist per-specialist state and handoffs inside the same durable run record instead of fragmenting one engineering run into child sessions.
- Use a lane-first pre-run routing control with advanced model pinning rather than raw provider choice only.
- Keep routing API-first with CLI providers last unless the operator explicitly pins a CLI path.
- Surface actual route outcome, fallback chain activity, and capability drift through dedicated route cards and routing views.
- Add structural operator views for `Overview`, `Agents`, `Routing`, and `Artifacts/Traces` in Phase 3, while deferring final polish to Phase 5.

### the agent's Discretion
- Exact lane names and the internal mapping from lane to provider/model chain
- Exact schema layout for specialist state and handoff payloads
- Exact panel and tab rendering approach for the current dashboard shell

### Deferred Ideas (OUT OF SCOPE)
- Final bubble styling, animation, opacity system, and finished operator-grade visual language
- Autonomous file editing, diff capture, and validation execution
- Shared cloud control plane or Azure-hosted multi-user surface

</user_constraints>

<research_summary>
## Summary

Phase 3 should treat specialist visibility and route visibility as first-class product data contracts, not as UI-only embellishments. The current runtime already contains the right raw seams:
- `maf_core/team_factory.py` already declares the specialist roster
- `maf_core/orchestration.py` already owns the canonical manager stage contract
- `maf_core/routing_policy.py` and `maf_core/provider_fallback.py` already classify prompts, order fallbacks, and emit route metadata
- `autogen_dashboard/session_runner.py`, `autogen_dashboard/schemas.py`, and `autogen_dashboard/static/app.js` already persist and render manager-oriented orchestration cards

The missing piece is explicit specialist-state and route-plan data that survives the run, can be queried by the API, and can be rendered in the operator UI without scraping transcript text or DevUI traces.

**Primary recommendation:** add a shared specialist-state and handoff contract in `maf_core/orchestration.py`, make route lanes and fallback attempt metadata explicit in the runtime contract, then project both into the dashboard API and UI as dedicated `Agents` and `Routing` surfaces. Keep DevUI trace enrichment as an engineering aid only.
</research_summary>

<standard_stack>
## Standard Stack

No new framework is required for Phase 3. This phase is primarily a deeper use of existing runtime and dashboard contracts.

### Core
| Library / Module | Version | Purpose | Why Standard Here |
|---------|---------|---------|--------------|
| `agent-framework` | `1.0.0rc5` | Active agent and workflow runtime | Already powers the specialist workflow and entity surface |
| `maf_core/orchestration.py` | in-repo | Shared run and stage contract | Best place to extend the manager contract with specialist-state and handoff data |
| `maf_core/team_factory.py` | in-repo | Current specialist workflow | Already names the specialist roster that Phase 3 should expose |
| `maf_core/routing_policy.py` | in-repo | Current route classification and chain selection | Natural place to formalize lane selection and route-plan metadata |
| `maf_core/provider_fallback.py` | in-repo | Actual fallback execution and route metadata | Already records provider/model/fallback/tool-availability fields |
| `autogen_dashboard/session_runner.py` | in-repo | Durable run projection layer | Already maps orchestration state into persisted operator-facing state |
| `autogen_dashboard/static/` | in-repo | Current product-facing dashboard shell | Already has the card-based UI surface Phase 3 should extend |

### Supporting
| Library / Module | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `maf_core/devui_patches.py` | in-repo | Local route trace enrichment | Keep for engineering-console visibility, but not as the product contract |
| `autogen_dashboard/schemas.py` | in-repo | Typed run, route, and stage payloads | Extend for specialist and route-lane data |
| `unittest` | stdlib | Existing automated validation baseline | Add phase-specific specialist, routing, and API/UI contract tests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Shared specialist-state contract inside the durable run | Per-specialist child sessions | Better isolation, but breaks the one-run mental model and complicates resume behavior |
| Lane-first routing with advanced override | Provider/model dropdown only | Powerful, but too low-level for the default operator flow |
| Dashboard product surfaces for agent/routing views | More DevUI patching | Faster locally, but brittle and not aligned with the product direction |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Manager-owned run with visible specialists
**What:** Keep the run manager-centric, but attach visible specialist records and handoff edges underneath it.
**When to use:** Always for Phase 3.
**Example:** The run remains one `SessionDetail`, but it now carries `specialist_states` and `specialist_handoffs` in addition to manager stage data.

### Pattern 2: Planned route versus actual route
**What:** Distinguish what the manager intended to use from what actually executed after fallback.
**When to use:** On every turn that can route or fallback.
**Example:** A run selects the `Deep` lane, plans `gemini-2.5-pro`, falls through to `claude-cli sonnet`, and records both the planned chain and the actual capability downgrade.

### Pattern 3: Capability drift as first-class state
**What:** Track when fallback changes what the runtime can safely do, especially when moving from API tool use to CLI text-only behavior.
**When to use:** Any time `tools_available` or a similar capability boundary changes.
**Example:** A route card shows `fallback used` and `tools unavailable`, and the manager can pause or adapt based on that fact.

### Pattern 4: Structural operator surfaces over transcript mining
**What:** Build explicit `Overview`, `Agents`, `Routing`, and `Artifacts/Traces` views from structured data.
**When to use:** For all product-facing visibility in this phase.
**Example:** The operator can open `Agents` and see `implementer -> waiting on reviewer` without reading message chronology.

### Anti-Patterns to Avoid
- **Per-specialist transcript scraping:** deriving agent task ownership from message text alone
- **DevUI-first product design:** pushing more of the product contract into patching a debug console
- **Hidden capability downgrade:** falling back to CLI without making the loss of tool support explicit
- **Provider-centric operator UX:** forcing the operator to think in provider strings instead of route lanes and outcomes

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that already have strong in-repo primitives:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Specialist roster discovery | A second role registry hidden in UI code | `maf_core/team_factory.py` + `maf_core/orchestration.py` | The runtime already knows the canonical participants |
| Run-level state projection | A second persistence system for agent cards | `autogen_dashboard/session_runner.py` + `autogen_dashboard/schemas.py` | The dashboard already persists run-scoped orchestration data |
| Route outcome metadata | A custom log parser over DevUI traces | `maf_core/provider_fallback.py` additional properties | The route metadata is already emitted at runtime |
| Lane classification | Ad hoc UI-only heuristics | `maf_core/routing_policy.py` | The current classification logic already exists and should be surfaced, not replaced |

**Key insight:** Phase 3 succeeds by promoting existing specialist and route metadata into durable operator contracts. It should not invent a parallel control plane for visibility alone.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Making specialists visible only after they speak
**What goes wrong:** The operator cannot tell which specialists exist, are queued, or are waiting.
**How to avoid:** Persist and render the full planned specialist roster up front with an explicit state for not-started and idle specialists.

### Pitfall 2: Treating lane selection as only a UI dropdown
**What goes wrong:** The UI claims a lane choice, but the runtime still behaves as opaque auto-routing.
**How to avoid:** Persist the requested lane, the planned route chain, the actual route, and the capability result in the shared run contract.

### Pitfall 3: Reporting fallback without reporting consequence
**What goes wrong:** The operator sees a provider change but does not know if tool availability or approval behavior changed.
**How to avoid:** Turn capability changes into explicit operator-facing state and badges.

### Pitfall 4: Burying new visibility in the transcript
**What goes wrong:** Phase 3 technically adds metadata, but the operator still has to read raw logs to understand the run.
**How to avoid:** Build dedicated agent and routing surfaces that consume structured specialist and route payloads directly.

</common_pitfalls>

<code_examples>
## Code Examples

Verified in-repo patterns worth preserving:

### Existing specialist roster
```python
# Source: maf_core/team_factory.py
# Pattern: planner -> researcher -> implementer -> reviewer
```

### Current route planning and fallback metadata
```python
# Source: maf_core/routing_policy.py and maf_core/provider_fallback.py
# Pattern: tier classification plus response metadata for provider, model, fallback, and tools availability
```

### Current dashboard orchestration projection
```python
# Source: autogen_dashboard/session_runner.py and autogen_dashboard/static/app.js
# Pattern: structured orchestration data persisted first, then rendered into cards and summaries
```

</code_examples>

## Validation Architecture

Phase 3 validation should prove that specialist visibility and route visibility are durable, queryable, and understandable.

- **Primary automated framework:** stdlib `unittest`
- **Quick verification target:** unit tests for specialist-state serialization, handoff edges, route-lane selection, and capability-drift metadata
- **Broader verification target:** API contract tests for specialist states, route plans, route outcomes, and operator-surface summary payloads
- **Static sanity target:** compile smoke for touched Python modules and `node --check` for touched dashboard JS

Recommended commands once implementation lands:

- Quick specialist check: `.\.venv\Scripts\python.exe -m unittest tests.test_phase3_specialists -v`
- Quick routing check: `.\.venv\Scripts\python.exe -m unittest tests.test_phase3_routing tests.test_maf_setup -v`
- API/UI contract check: `.\.venv\Scripts\python.exe -m unittest tests.test_phase3_api -v`
- Full suite: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- Static sanity: `.\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py`
- Frontend syntax: `node --check autogen_dashboard\static\app.js`

Focus the test map on:
- specialist roster, idle states, and stage-to-specialist ownership
- structured handoff serialization and projection into API payloads
- route-lane selection, planned chain, actual route, and fallback attempt capture
- capability drift visibility when fallback removes tool support
- operator-facing payloads for `Overview`, `Agents`, and `Routing` views

<open_questions>
## Open Questions

1. **Should route lanes be persisted on the session summary or a deeper run-attempt object?**
   - What we know: the operator chooses before the run, but later retries may want a different route.
   - Recommendation: persist the requested lane on the run summary and the exact actual route on each attempt or stage record.

2. **Should specialist visibility be stage-derived or participant-derived?**
   - What we know: the current workflow maps stages to participants, but later phases may add more nuanced specialist flows.
   - Recommendation: persist both a stable participant roster and current stage ownership so Phase 3 stays flexible.

3. **How much styling belongs in Phase 3 versus Phase 5?**
   - What we know: structural tabs and route cards are required now, but the final product polish is later.
   - Recommendation: Phase 3 delivers structural clarity and polished-enough cards; Phase 5 does the final visual language pass.

</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/phases/03-specialist-delegation-and-routing-visibility/03-CONTEXT.md`
- `.planning/phases/02-manager-led-orchestration-core/02-CONTEXT.md`
- `maf_core/orchestration.py`
- `maf_core/team_factory.py`
- `maf_core/agent_factory.py`
- `maf_core/routing_policy.py`
- `maf_core/provider_fallback.py`
- `maf_core/devui_patches.py`
- `autogen_dashboard/schemas.py`
- `autogen_dashboard/session_runner.py`
- `autogen_dashboard/static/index.html`
- `autogen_dashboard/static/app.js`
- `docs/DEVUI_CUSTOMIZATION.md`

### Secondary (MEDIUM confidence)
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/STRUCTURE.md`
- `.planning/codebase/CONVENTIONS.md`
- `tests/test_phase2_manager.py`
- `tests/test_phase2_api.py`
- `tests/test_maf_setup.py`

</sources>

<metadata>
## Metadata

**Research scope:**
- Specialist-role and handoff seams in the active MAF workflow
- Current routing and fallback metadata contract
- Dashboard operator-surface seams for structural visibility
- Validation strategy needed for agent and routing transparency

**Confidence breakdown:**
- Specialist contract direction: HIGH
- Route-lane and fallback reporting direction: HIGH
- Operator-surface integration path: HIGH
- Phase boundary versus later polish: HIGH

**Research date:** 2026-03-21
**Valid until:** 2026-04-20

</metadata>

---

*Phase: 03-specialist-delegation-and-routing-visibility*
*Research completed: 2026-03-21*
*Ready for planning: yes*
