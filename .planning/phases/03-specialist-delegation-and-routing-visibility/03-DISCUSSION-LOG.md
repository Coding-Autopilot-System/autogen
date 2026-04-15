# Phase 3: Specialist Delegation and Routing Visibility - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-03-21
**Phase:** 03-specialist-delegation-and-routing-visibility
**Areas discussed:** Specialist roster and ownership, specialist state and handoffs, route lane control, routing and fallback visibility, operator surface structure
**Mode:** Auto (`--auto`) with recommended defaults selected from current roadmap, prior phase context, and active code seams

---

## Specialist roster and ownership

### Decision: Which specialists become first-class visible participants?

| Option | Description | Selected |
|--------|-------------|----------|
| `planner`, `researcher`, `implementer`, and `reviewer` as explicit visible specialists, with manager owning the run | Matches the current runtime roster in `maf_core/team_factory.py` and keeps ownership legible | ✓ |
| Hide specialists behind the manager and only show stage summaries | Simpler UI, but fails the phase goal for specialist visibility | |
| Allow dynamic ad hoc specialist creation per run | Flexible, but too open-ended for the first visibility phase | |

**User's choice:** `[auto]` Selected the existing `planner`, `researcher`, `implementer`, and `reviewer` roster as visible specialists, while keeping the manager as the only top-level run owner.
**Notes:** This preserves the Phase 2 manager contract and avoids introducing dynamic role orchestration before the visibility contract is stable.

### Decision: Who owns the final validation surface in Phase 3?

| Option | Description | Selected |
|--------|-------------|----------|
| Manager-owned final validation state, with reviewer findings feeding into it | Keeps validation attached to the canonical run summary | ✓ |
| Add a separate visible `validator` specialist now | Adds another specialist before the current roster is fully surfaced | |
| Let the reviewer own all validation state | Simpler, but blurs review versus final run status | |

**User's choice:** `[auto]` Kept validation manager-owned for Phase 3.
**Notes:** Phase 3 is about specialist visibility, not adding a broader workflow graph. A dedicated validator can wait until later if needed.

---

## Specialist state and handoffs

### Decision: How should specialist progress be persisted?

| Option | Description | Selected |
|--------|-------------|----------|
| Nested per-specialist state inside the same durable run record | Extends the existing orchestration and session schema cleanly | ✓ |
| Separate per-specialist runs or child sessions | Richer isolation, but fragments one engineering run into many identities | |
| UI-only specialist state with no persistence | Fast to build, but loses resume and auditability | |

**User's choice:** `[auto]` Persist specialist state inside the main run record.
**Notes:** This matches the existing run-centric contract in `autogen_dashboard/session_runner.py` and `autogen_dashboard/schemas.py`.

### Decision: How should handoffs be represented?

| Option | Description | Selected |
|--------|-------------|----------|
| Structured handoff events with `from`, `to`, `reason`, `requested_by`, and `status` fields | Clear, queryable, and suitable for UI timelines and later APIs | ✓ |
| Implicit handoffs inferred from transcript order | Minimal work, but brittle and hard to audit | |
| Raw trace-only handoff visibility | Keeps data hidden in diagnostics instead of product UI | |

**User's choice:** `[auto]` Use explicit structured handoff events.
**Notes:** Phase 3 needs specialist ownership to be inspectable without transcript archaeology.

---

## Route lane control

### Decision: What should the primary pre-run routing control be?

| Option | Description | Selected |
|--------|-------------|----------|
| Route-lane presets with optional advanced model pinning | Gives usable control without forcing raw model fluency every time | ✓ |
| Raw provider and model dropdown only | Powerful, but noisy and too low-level for default operator flow | |
| No operator routing control before the run | Simpler, but fails `ROUT-01` | |

**User's choice:** `[auto]` Use route-lane presets as the main control, with advanced model pinning available.
**Notes:** This matches the current routing tiers in `maf_core/routing_policy.py` while accommodating the desire for explicit model access.

### Decision: What is the default fallback ordering policy?

| Option | Description | Selected |
|--------|-------------|----------|
| API-first, strongest-to-cheapest within the chosen lane, then CLI providers last | Best fit for repo work, tool support, and existing user preference | ✓ |
| Cheapest-first across all providers | Saves cost, but weakens first-pass quality for codebase-heavy work | |
| Put CLI providers near the front of the chain | Good for quota resilience, but loses tool support too early | |

**User's choice:** `[auto]` Keep API-first routing with CLI providers as terminal fallbacks unless pinned explicitly.
**Notes:** This carries forward the earlier preference for Gemini API first and CLI tools as resilience paths rather than the default smart route.

---

## Routing and fallback visibility

### Decision: Where should route outcomes be shown?

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated route cards and routing views tied to stages and specialists | Makes provider/model behavior product-visible and auditable | ✓ |
| Raw trace pane only | Useful for debugging, but too hidden for normal operation | |
| Final summary only | Too late; the operator needs to understand route changes during the run | |

**User's choice:** `[auto]` Show route outcomes in dedicated cards and routing views.
**Notes:** This directly addresses the earlier operator pain with route information hiding inside DevUI text bubbles and traces.

### Decision: How should capability drift be surfaced during fallback?

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit badges and state diffs when fallback changes capabilities | Makes API-to-CLI degradation obvious and actionable | ✓ |
| Implicitly through the provider/model name only | Too subtle, especially when tools disappear | |
| Do not surface capability drift separately | Fails the phase requirement to show fallback impact clearly | |

**User's choice:** `[auto]` Surface explicit capability-drift badges and changes.
**Notes:** This is especially important because `maf_core/provider_fallback.py` already tracks `tools_available`, which can be promoted into a real operator-facing concept.

---

## Operator surface structure

### Decision: How should specialist and routing visibility be organized in the UI?

| Option | Description | Selected |
|--------|-------------|----------|
| Add structural views for `Overview`, `Agents`, `Routing`, and `Artifacts/Traces` | Cleanest mapping to the phase goals and future operator workbench | ✓ |
| Keep one transcript-first page and append more metadata blocks | Lower effort, but becomes dense and hard to scan | |
| Push specialist visibility mostly into DevUI and leave the dashboard minimal | Keeps the product surface dependent on brittle DevUI internals | |

**User's choice:** `[auto]` Add structural views for overview, agents, routing, and artifacts/traces.
**Notes:** This creates the right information architecture now while leaving final visual polish and motion work for Phase 5.

## the agent's Discretion

- Exact labels for route lanes and tabs
- Exact visual styling of chips, panels, and badges
- Exact density of trace detail shown by default

## Deferred Ideas

- Final stylish bubble system, opacity treatment, and polished visual language - Phase 5
- Autonomous editing and validation execution defaults - Phase 4
- Azure-hosted shared control plane and REST surface - later cloud phase
