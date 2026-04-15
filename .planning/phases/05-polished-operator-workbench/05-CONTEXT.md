# Phase 5: Polished Operator Workbench - Context

**Gathered:** 2026-03-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Turn the current operator shell into a professional, stylish workbench that makes the orchestration system readable and trustworthy during real repo work. This phase covers the product-facing shell, message surfaces, route and specialist visibility, event and artifact inspection, and the interaction quality needed for daily use. It does not replace the underlying orchestration contract, rewrite the backend into a different platform, or deliver Azure-hosted deployment surfaces yet.

</domain>

<decisions>
## Implementation Decisions

### Product surface versus DevUI
- The durable product UI for Phase 5 is the existing `autogen_dashboard` shell, not raw MAF DevUI. DevUI remains a local engineering console and debugging aid.
- Phase 5 should consume the routing, specialist, execution, validation, and approval contracts created in Phases 1 through 4 instead of inventing a parallel UI-only data model.
- Any DevUI customization done earlier is considered tactical glue. Product-grade presentation belongs in the dashboard path and should not depend on brittle DevUI DOM patching.
- The UI should present orchestration outcomes as first-class product features rather than exposing backend implementation seams directly.

### Workbench shell and operator navigation
- Keep a two-pane operator workbench instead of collapsing into a single chat page. The left side remains queue, provider readiness, approvals, and run creation; the right side becomes the active run workspace.
- The active run workspace should prioritize the current run header, route and status indicators, sticky control/input surfaces, and a small set of durable task-oriented tabs.
- The primary run tabs for this phase are `Overview`, `Timeline`, `Agents`, `Routing`, and `Artifacts`. These should reflect operator tasks rather than backend object names.
- Run creation remains available, but it should stop visually dominating the interface once an active run is selected. The product focus is operating and understanding runs, not only creating them.

### Message and activity surfaces
- Human, manager, specialist, tool or event, and approval content must be visually distinct. They should not all render as the same bubble with different text prefixes.
- Manager output should read as the canonical orchestrator voice. Specialist updates should appear as owned sub-surfaces with explicit role labels, current task, and latest result.
- Route, model, and fallback details should render in dedicated header strips, chips, or cards above the relevant content instead of living inside transcript text.
- Tool and event output should be presented as compact timeline or event cards, not as normal chat bubbles. The operator should be able to understand what happened without scanning raw log lines.

### Timeline, routing, and per-agent inspection
- The operator must be able to inspect the whole run, the event timeline, each specialist, the routing path, and generated artifacts without leaving the active run workspace.
- The `Timeline` view should become the main event surface for stage changes, validations, approvals, tool activity, and noteworthy fallback events.
- The `Agents` view should show a stable roster with current status, owned responsibility, latest output summary, handoff target, and whether the agent is blocked or waiting.
- The `Routing` view should show requested route lane, planned route, actual route, fallback attempts, and capability drift in an operator-readable card format.
- The `Artifacts` view should show changed files, diff artifacts, validation results, and approval records as inspectable operator outputs rather than raw manifest dumps.

### Visual direction and interaction quality
- Phase 5 should refine the existing warm, rounded, glassy operator aesthetic rather than replace it with a generic framework look. The current palette and card language are a valid starting point, but the hierarchy needs to feel more deliberate and product-grade.
- Message hierarchy, spacing, sticky controls, chip systems, rounded panels, and muted-versus-active contrast should all improve readability before new decorative motion or novelty is added.
- The UI should favor high-signal operator ergonomics: cleaner status strips, fewer ambiguous empty states, stronger active selection styling, and better visual grouping around one active run.
- Keyboard shortcuts, quick actions, and route or model indicators are useful, but they should support the operator workflow instead of becoming the main visual story.

### Implementation posture
- Build Phase 5 on the current static `index.html` + `styles.css` + `app.js` product surface instead of switching frameworks mid-milestone.
- Reuse the existing backend session payloads for specialists, routing, approvals, validation, artifacts, and run summaries. Add new UI-focused view-model shaping only where the current payloads do not project cleanly.
- Keep the UI data contract aligned with the local runtime so the same operator payloads can later back an Azure Function or REST API surface.
- Treat major front-end decomposition or framework migration as optional cleanup only if Phase 5 delivery is blocked by the current file structure.

### the agent's Discretion
- Exact chip shapes, typography scale, iconography, and motion rules as long as the interface becomes visibly more polished and easier to scan.
- Exact split between `Overview` and `Timeline` details as long as the operator can understand both current state and recent progression quickly.
- Exact rendering approach for approvals, validation cards, and diff drill-down as long as they are visibly separate from transcript messages and usable without raw logs.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and phase scope
- `.planning/PROJECT.md` - defines the product as a local-first orchestration workbench and keeps the polished operator UI as an active requirement.
- `.planning/REQUIREMENTS.md` - defines `UI-01`, `UI-02`, and `UI-03`, which Phase 5 must satisfy.
- `.planning/ROADMAP.md` - defines the fixed Phase 5 boundary, success criteria, and plan split.
- `.planning/STATE.md` - records the current focus and prior decisions that Phase 5 must build on.
- `.planning/phases/03-specialist-delegation-and-routing-visibility/03-CONTEXT.md` - locks the operator views and routing visibility decisions that Phase 5 should polish rather than replace.
- `.planning/phases/04-autonomous-repo-execution-and-validation-guardrails/04-CONTEXT.md` - locks the artifact, validation, and approval visibility surfaces that Phase 5 must elevate into a product-grade UI.

### UI and runtime seams
- `.planning/codebase/STACK.md` - confirms the current frontend path is static HTML, CSS, and JavaScript, not a React or SPA framework.
- `.planning/codebase/STRUCTURE.md` - identifies `autogen_dashboard/` as the product-facing operator shell and `maf_core/` as the active runtime base.
- `.planning/codebase/CONVENTIONS.md` - captures the current naming, payload-shaping, and UI implementation patterns that Phase 5 should follow unless blocked.
- `autogen_dashboard/static/index.html` - defines the current shell layout, panel composition, and tab scaffolding that Phase 5 should restructure and refine.
- `autogen_dashboard/static/styles.css` - defines the current design tokens, panel system, message presentation, and responsive rules that Phase 5 should evolve.
- `autogen_dashboard/static/app.js` - owns client-side normalization and rendering for sessions, approvals, specialists, routing, artifacts, and run status.
- `autogen_dashboard/app.py` - defines the HTTP surface and static serving path for the operator product UI.
- `autogen_dashboard/session_runner.py` - projects backend orchestration state, approvals, validations, specialists, and routing into the session payloads that the UI renders.
- `autogen_dashboard/schemas.py` - defines the operator-facing session and artifact schema the polished workbench should continue to consume.
- `docs/DEVUI_CUSTOMIZATION.md` - documents why DevUI is a local engineering console and not the durable final product surface.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `autogen_dashboard/static/index.html`: already has the operator shell structure, create-run form, approvals queue, selected-run panel, tab system, and human control surfaces that Phase 5 can refine instead of rebuilding.
- `autogen_dashboard/static/app.js`: already normalizes route plans, specialist state, stage summaries, approvals, validation records, artifacts, and session modes into operator-facing rendering data.
- `autogen_dashboard/static/styles.css`: already establishes a rounded, glassy, warm-toned design language with sticky controls and card-based grouping that can be pushed to a more professional finish.
- `autogen_dashboard/session_runner.py` and `autogen_dashboard/schemas.py`: already expose durable run state for specialists, routing, approvals, changed files, validation results, and artifacts, which removes the need for UI-only backend invention in this phase.
- `maf_core/orchestration.py`, `maf_core/provider_fallback.py`, and `maf_core/routing_policy.py`: already produce the stage, specialist, route, and fallback metadata the UI should surface more cleanly.

### Established Patterns
- The manager is the canonical run owner, while specialists are visible collaborators with structured state and handoffs.
- Route visibility is already centered on lane, provider, model, rationale, fallback attempts, and capability drift. Phase 5 should present that contract more clearly, not redefine it.
- Approval scope, validation results, changed files, and artifact manifests already exist as durable operator-facing outputs and should be elevated into clearer inspection surfaces.
- The current frontend is intentionally framework-light. Phase 5 should keep momentum by improving the existing product UI rather than pausing to swap stacks.

### Integration Points
- `autogen_dashboard/static/index.html` is the seam for restructuring the shell, tabs, message containers, and active-run hierarchy.
- `autogen_dashboard/static/styles.css` is the seam for message-surface differentiation, route strips, event cards, visual hierarchy, and responsive polish.
- `autogen_dashboard/static/app.js` is the seam for projecting backend data into dedicated timeline cards, per-agent panels, route badges, and artifact inspection views.
- `autogen_dashboard/session_runner.py` and `autogen_dashboard/schemas.py` are the seams for any missing operator payload fields needed to avoid raw-log rendering.

</code_context>

<specifics>
## Specific Ideas

- The active run should feel like an operator cockpit, not a long generic dashboard column.
- Route or model identity should be visible at a glance in dedicated panels or strips above related content.
- The operator should be able to tell what the manager decided, what each specialist is doing, and what actually happened on the machine without reading transcript prefixes or raw trace rows.
- The same polished UI contracts should remain usable later if the orchestration runtime is exposed through Azure Functions or a REST API.

</specifics>

<deferred>
## Deferred Ideas

- Azure Function or REST exposure of the orchestration runtime - later API and cloud phases
- Automatic branch or worktree isolation and multi-user collaboration - later safety and collaboration phases
- Full frontend framework migration or design-system extraction unless the current static UI becomes a delivery blocker

</deferred>

---

*Phase: 05-polished-operator-workbench*
*Context gathered: 2026-03-22*
