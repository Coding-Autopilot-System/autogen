# Phase 5: Polished Operator Workbench - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-03-22
**Phase:** 05-polished-operator-workbench
**Areas discussed:** product surface choice, workbench shell, message presentation, timeline and routing visibility, visual direction

---

## Product surface choice

| Option | Description | Selected |
|--------|-------------|----------|
| Dashboard as product UI | Use `autogen_dashboard` as the durable operator workbench and keep DevUI as a local engineering console only. | selected |
| DevUI as primary UI | Continue treating patched DevUI as the main user-facing surface. | |
| Full UI rewrite | Replace the current UI path with a fresh frontend stack before polishing behavior. | |

**User's choice:** `[auto] Dashboard as product UI`
**Notes:** Recommended because the product-facing operator shell, data contracts, and active requirements already live in `autogen_dashboard`. DevUI patching is useful for local diagnostics but too brittle to serve as the long-term product UI.

---

## Workbench shell and navigation

| Option | Description | Selected |
|--------|-------------|----------|
| Two-pane operator workbench | Keep queue and setup on one side and the active run workspace on the other, with durable tabs for run inspection. | selected |
| Single chat-first page | Collapse everything into one main conversation page with drawers for details. | |
| Separate full-screen pages | Split runs, agents, routing, and artifacts into mostly separate pages. | |

**User's choice:** `[auto] Two-pane operator workbench`
**Notes:** Recommended because the current shell already has the right structural pieces, and the operator needs both run-management context and an active workspace at the same time. Phase 5 is polish and hierarchy, not a navigation-model reset.

---

## Message and activity presentation

| Option | Description | Selected |
|--------|-------------|----------|
| Distinct message families | Use visually distinct human, manager, specialist, event, and approval surfaces with route and model strips outside transcript text. | selected |
| Keep generic chat bubbles | Continue rendering most content as similar bubbles and add more textual prefixes. | |
| Replace transcript with cards only | Remove most chat-like presentation and show only structured cards. | |

**User's choice:** `[auto] Distinct message families`
**Notes:** Recommended because `UI-01` explicitly requires visually distinct message presentation. The operator still benefits from conversational continuity, but important run metadata should stop living inside plain text bubbles.

---

## Timeline, routing, and per-agent inspection

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated tabs in active workspace | Add clear `Overview`, `Timeline`, `Agents`, `Routing`, and `Artifacts` views inside the selected run workspace. | selected |
| One transcript plus filters | Keep a single transcript and rely on filtering or search to inspect events, agents, and routes. | |
| Raw traces first | Treat traces and event rows as the main inspection surface. | |

**User's choice:** `[auto] Dedicated tabs in active workspace`
**Notes:** Recommended because `UI-02` and `UI-03` explicitly call for switching between run, agent, trace, and artifact views without forcing raw-log reading. The underlying contracts already exist from earlier phases, so the UX should now be productized.

---

## Visual direction

| Option | Description | Selected |
|--------|-------------|----------|
| Refine existing warm rounded system | Keep the current warm palette, rounded panels, and glassy surfaces, but make the hierarchy feel more deliberate and product-grade. | selected |
| Full visual reset | Replace the current aesthetic with a completely different design language before improving workflow clarity. | |
| Minimal utilitarian UI | Strip styling back and optimize only for density and functional controls. | |

**User's choice:** `[auto] Refine existing warm rounded system`
**Notes:** Recommended because the repo already has a non-generic visual direction in `styles.css`, and the user’s stated goal is to make it feel stylish and professional. The real gap is hierarchy and presentation quality, not the total absence of design language.

---

## the agent's Discretion

- Exact tab labeling between `Overview` and `Timeline`
- Exact chip, card, and route-strip rendering approach
- Exact typography and motion details within the existing frontend stack

## Deferred Ideas

- Azure-hosted UI and REST/API operator surface
- Multi-user collaboration or authentication
- Full framework migration if the current frontend becomes an actual blocker later
