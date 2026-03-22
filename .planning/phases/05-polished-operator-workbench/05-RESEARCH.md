# Phase 5: Polished Operator Workbench - Research

**Researched:** 2026-03-22
**Domain:** Product-grade operator UI for the existing local orchestration runtime, including polished message surfaces, route visibility, agent activity, event timeline, and artifact inspection over the current static dashboard shell
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- The durable product UI for this phase is `autogen_dashboard`, not MAF DevUI.
- The shell stays a two-pane operator workbench with queue and setup on one side and the active run workspace on the other.
- The active run workspace must support `Overview`, `Timeline`, `Agents`, `Routing`, and `Artifacts`.
- Human, manager, specialist, event, and approval content must become visually distinct message or card families.
- Route, model, and fallback details must render in dedicated strips, chips, or cards instead of transcript prefixes.
- The UI should refine the current warm, rounded, glassy design direction instead of resetting the aesthetic.
- The phase should reuse the existing backend run contracts for routing, specialists, approvals, validation, and artifacts rather than inventing a second UI-only backend.

### the agent's Discretion
- Exact typography sizes, chip styling, iconography, and motion rules
- Exact split of content between `Overview` and `Timeline`
- Exact frontend decomposition if the current single-file JS becomes a productivity problem during implementation

### Deferred Ideas (OUT OF SCOPE)
- Azure Function or REST exposure of the operator workbench
- Automatic branch or worktree isolation and multi-user collaboration
- Full frontend framework migration unless the current static UI becomes a hard blocker

</user_constraints>

<research_summary>
## Summary

Phase 5 should be treated as a productization pass over a mostly complete operator contract, not as a greenfield UI build. The current dashboard already exposes the correct run concepts:
- workspace and run identity from Phase 1
- manager-owned orchestration stages and pause semantics from Phase 2
- specialists and routing visibility from Phase 3
- approvals, validation results, diffs, and artifact manifests from Phase 4

The main gap is presentation quality and operator ergonomics. The UI currently behaves like a capable internal dashboard: dense, functional, and already card-based. The remaining work is to make the active run feel like an operator cockpit with clearer hierarchy, stronger message families, dedicated event and inspection surfaces, and fewer places where the user has to read raw log-like content.

**Primary recommendation:** implement Phase 5 as a sequential UI productization chain:
1. restructure the active-run shell and transcript surfaces around distinct message families and a stronger workspace hierarchy
2. build dedicated `Timeline`, `Agents`, `Routing`, and `Artifacts` inspection surfaces on top of the existing session payloads
3. polish the visual system, interaction details, empty states, notices, and responsive behavior until the interface feels deliberate instead of provisional

Because the same static files drive almost all of the current UI, sequential execution is safer than parallel plan waves. The DOM, rendering helpers, and design tokens are tightly coupled, and large concurrent edits to `index.html`, `styles.css`, and `app.js` would create needless merge friction and inconsistent UX.
</research_summary>

<standard_stack>
## Standard Stack

No framework migration is required for Phase 5. The most reliable path is to deepen the existing static frontend contract and keep the backend session model stable.

### Core
| Library / Module | Version | Purpose | Why Standard Here |
|---------|---------|---------|--------------|
| `FastAPI` via `autogen_dashboard/app.py` | in-repo | Serves the operator UI and session APIs | Already hosts the durable product surface |
| `autogen_dashboard/static/index.html` | in-repo | Operator shell structure | Already contains the run creation, queue, tab, and control surfaces |
| `autogen_dashboard/static/styles.css` | in-repo | Design tokens, layout, card styles, message styles | Already establishes the current warm rounded visual direction |
| `autogen_dashboard/static/app.js` | in-repo | UI state, normalization, rendering, and action wiring | Already owns the operator view-model logic |
| `autogen_dashboard/session_runner.py` | in-repo | Projects orchestration state into product-facing session payloads | Already centralizes stage, route, specialist, approval, and artifact summaries |
| `autogen_dashboard/schemas.py` | in-repo | Session and artifact schema | Best seam for any UI-facing payload refinements |

### Supporting
| Library / Module | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `unittest` | stdlib | Static and API/UI contract tests | Use for Phase 5 render and payload regression coverage |
| `node --check` | local tool | JavaScript syntax sanity | Keep for every frontend touch |
| `python -m compileall` | stdlib | Python syntax sanity | Run after payload or API changes |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Evolving the existing static dashboard | Rewrite into React or another SPA stack | More component control long-term, but scope explosion during a polish-first milestone |
| Dedicated operator tabs and view models | Force everything through one transcript with filters | Faster to hack, but fails the requirement to inspect traces, agents, and artifacts without raw logs |
| Route chips and summary cards outside transcript text | Keep embedding route banners into message content | Minimal code change, but poor readability and visually weak hierarchy |
| Product dashboard as primary surface | Keep patching DevUI harder | DevUI remains brittle and is explicitly documented as non-production |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Product shell over stable orchestration contracts
**What:** Treat the UI as a projection layer over stable run data rather than a place to invent new runtime truths.
**When to use:** Always for routing, specialists, approvals, validation, and artifacts in Phase 5.
**Example:** `session_runner.py` emits durable `route_metadata`, `stage_outputs`, `specialist_states`, `specialist_handoffs`, and `pending_approval`; `app.js` should reshape these into operator cards instead of scraping transcript text.

### Pattern 2: Message-family rendering instead of prefix-based messaging
**What:** Render human, manager, specialist, approval, and event content through distinct visual containers with role-aware chrome.
**When to use:** For transcript and activity presentation.
**Example:** Manager messages use the canonical orchestrator bubble, specialist updates get role cards or labeled message blocks, and event output becomes a timeline row rather than a generic bubble.

### Pattern 3: Inspection views for operator tasks
**What:** The active workspace should separate “what is happening now” from “what happened over time” and “what changed on disk”.
**When to use:** For `Overview`, `Timeline`, `Agents`, `Routing`, and `Artifacts`.
**Example:** `Overview` summarizes state, approvals, active route, and stage outputs; `Timeline` sequences important events; `Artifacts` drills into diffs and validation outputs.

### Pattern 4: View-model shaping close to render seams
**What:** Normalize and condense backend payloads just before rendering so the HTML stays simple.
**When to use:** For route cards, specialist cards, artifact grids, and timeline rows.
**Example:** `app.js` can compute operator-facing cards from session payloads, while backend code only adds fields when the UI cannot derive them cleanly.

### Anti-Patterns to Avoid
- **Transcript as the only inspection tool:** forcing the operator to infer route, approval, or validation state from prose
- **DevUI-first product decisions:** tying the final product surface to patched DevUI assumptions
- **Parallel UI rewrites of the same files:** letting multiple plans edit the same shell and style files in the same wave
- **Visual novelty without hierarchy:** adding more color or motion before fixing structure, scanability, and active-run focus

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that already have strong in-repo primitives:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Specialist, routing, approval, and artifact truth | UI-only shadow state or duplicate metadata registries | Existing session payloads from `session_runner.py` and `schemas.py` | The durable run contract already exists |
| Product shell navigation | Separate frontend app or multiple pages for this milestone | Existing `index.html` shell with improved active-run hierarchy and tabs | Faster, safer, and consistent with current product path |
| Routing visibility | More transcript banners | Existing `route_metadata`, `route_plan`, `route_attempts`, and capability drift fields | The data is already structured |
| Artifact lookup | Raw manifest JSON dumps | Existing stage outputs and manifest paths plus focused UI cards and drill-downs | Better operator UX without backend churn |

**Key insight:** most of Phase 5 is not about adding more backend capability. It is about presenting existing capability cleanly enough that the product feels trustworthy and fast to operate.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Overlapping plans that all edit the same UI files
**What goes wrong:** Parallel execution produces merge-heavy plans that touch the same DOM structure, CSS tokens, and render helpers.
**How to avoid:** Use sequential waves for the three plans and keep each plan’s objective narrow: shell and message system first, inspection surfaces second, ergonomics and polish third.

### Pitfall 2: Treating route or approval metadata as decoration
**What goes wrong:** The UI looks nicer, but the operator still has to read transcript text to understand which model answered or why the run paused.
**How to avoid:** Promote route, approval, and validation signals into dedicated strips, cards, and status regions that sit outside transcript prose.

### Pitfall 3: Doing polish only in CSS
**What goes wrong:** The interface keeps the same information architecture problems but with prettier shadows.
**How to avoid:** Change layout hierarchy, tab framing, message families, and render seams in `index.html` and `app.js`, not only token values in `styles.css`.

### Pitfall 4: Missing automated guardrails for UI contract drift
**What goes wrong:** The product regresses silently because there are no tests for tab inventory, render helpers, or payload fields.
**How to avoid:** Add Phase 5 tests that assert the presence of required tabs, message-family hooks, route/status helpers, and operator-view payload expectations.

</common_pitfalls>

<code_examples>
## Code Examples

Verified in-repo patterns worth preserving:

### Current operator tab model
```javascript
// Source: autogen_dashboard/static/app.js
// Pattern: dedicated operator tabs with overview, agents, routing, and artifacts view renderers
```

### Current durable approval scope rendering
```javascript
// Source: autogen_dashboard/static/app.js
// Pattern: renderApprovalScope(...) already turns pending approval payloads into operator cards
```

### Current route and specialist payload projection
```python
# Source: autogen_dashboard/session_runner.py
# Pattern: session summaries already persist route_metadata, specialist_states, specialist_handoffs, and stage_outputs
```

### Current design-token base
```css
/* Source: autogen_dashboard/static/styles.css */
/* Pattern: centralized CSS variables for palette, radii, shadow, and type families */
```

</code_examples>

## Validation Architecture

Phase 5 validation should combine static UI-contract checks with targeted runtime/API regression coverage and a small amount of manual product review.

1. **Static UI contract tests** should verify the presence of the workbench tab inventory, message-family hooks, route/status helpers, and shell landmarks in `index.html`, `styles.css`, and `app.js`.
2. **Payload and operator-view tests** should verify the active backend session contract still exposes the fields the product UI depends on for timeline, routing, specialists, approvals, and artifacts.
3. **Manual operator checks** remain necessary for polished message hierarchy, responsive layout quality, and “readability without raw logs”.

- **Primary automated framework:** stdlib `unittest`
- **Quick verification target:** `tests.test_phase5_ui_contract`
- **Payload regression target:** a new `tests.test_phase5_operator_views` plus existing `tests.test_phase3_api` and `tests.test_phase4_approval`
- **Static sanity target:** `node --check autogen_dashboard\static\app.js` plus `python -m compileall ...`

Recommended commands once implementation lands:

- Quick UI contract: `.\.venv\Scripts\python.exe -m unittest tests.test_phase5_ui_contract -v`
- Operator-view payloads: `.\.venv\Scripts\python.exe -m unittest tests.test_phase5_operator_views tests.test_phase3_api -v`
- Approval and artifact regression: `.\.venv\Scripts\python.exe -m unittest tests.test_phase5_operator_views tests.test_phase4_approval tests.test_run_persistence -v`
- Full suite: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- Static sanity: `.\.venv\Scripts\python.exe -m compileall maf_starter autogen_dashboard tests main.py`
- Frontend syntax: `node --check autogen_dashboard\static\app.js`

Focus the test map on:
- shell tab inventory and active-run landmarks
- message-family rendering hooks for human, manager, specialist, event, and approval content
- route and model visibility outside transcript prose
- timeline, artifact, and specialist surfaces driven from structured session payloads
- approval and validation cards remaining visible without raw log dependence

<open_questions>
## Open Questions

1. **Should Phase 5 add a dedicated backend event-timeline payload, or can the UI derive the timeline fully from current stage outputs and events?**
   - What we know: the current UI already has `stage_timeline`, `events`, stage outputs, approvals, and validation artifacts.
   - Recommendation: prefer client-side view-model shaping first; only add backend fields if the current payloads cannot support a readable operator timeline.

2. **Should the monolithic `app.js` be split during this phase?**
   - What we know: the file already owns almost all render logic and is large.
   - Recommendation: do not make splitting a primary objective. Allow targeted extraction only if Phase 5 delivery gets blocked by local complexity.

3. **How much of the visual polish should be machine-tested?**
   - What we know: exact visual quality is hard to automate in the current repo.
   - Recommendation: test the contract and render hooks automatically, then require manual UX spot checks for hierarchy, readability, and responsiveness.

</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/phases/05-polished-operator-workbench/05-CONTEXT.md`
- `.planning/phases/03-specialist-delegation-and-routing-visibility/03-CONTEXT.md`
- `.planning/phases/04-autonomous-repo-execution-and-validation-guardrails/04-CONTEXT.md`
- `autogen_dashboard/static/index.html`
- `autogen_dashboard/static/styles.css`
- `autogen_dashboard/static/app.js`
- `autogen_dashboard/app.py`
- `autogen_dashboard/session_runner.py`
- `autogen_dashboard/schemas.py`
- `docs/DEVUI_CUSTOMIZATION.md`

### Secondary (MEDIUM confidence)
- `.planning/codebase/STACK.md`
- `.planning/codebase/STRUCTURE.md`
- `.planning/codebase/CONVENTIONS.md`
- `.planning/codebase/TESTING.md`
- `tests/test_phase3_api.py`
- `tests/test_phase4_approval.py`
- `tests/test_run_persistence.py`

</sources>

<metadata>
## Metadata

**Research scope:**
- Operator-shell structure and active-run hierarchy
- Message-family rendering and route visibility
- Specialist, routing, approval, validation, and artifact inspection surfaces
- UI contract and regression strategy for a static frontend stack

**Recommended execution shape:** 3 sequential plans over 3 waves

</metadata>
