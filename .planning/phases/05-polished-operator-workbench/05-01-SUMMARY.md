---
phase: 05-polished-operator-workbench
plan: 01
subsystem: operator-shell
tags: [ui, operator-workbench, transcript, routing, message-families]
requires: []
provides:
  - operator-first shell copy and active-run hierarchy
  - dedicated route and stage strips above the transcript workspace
  - distinct transcript message families for human, manager, specialist, approval, event, and system content
affects: [dashboard-ui, operator-tabs, transcript-rendering, ui-contract-tests]
requirements-completed: [UI-01]
completed: 2026-03-22
---

# Phase 05 Plan 01: Operator Shell Summary

## Accomplishments

- Reframed the product shell as `Operator Workbench` with active-run language instead of generic dashboard or session wording.
- Added dedicated `active-route-strip` and `active-stage-strip` surfaces so model routing, stage state, and pause context sit above the transcript instead of being buried in message text.
- Promoted `Timeline` to a first-class operator tab and wired the tab model so the active run reads like a cockpit rather than a form-plus-chat page.
- Replaced the generic transcript renderer with explicit message-family helpers that preserve `source`, `metadata`, stage, and route fields from the backend payload.
- Added distinct visual treatments for human, manager, specialist, approval, event, and system messages plus a reusable metadata strip for route and stage context.
- Added a static Wave 1 UI contract suite to protect the new shell landmarks, tab inventory, transcript helpers, and message-family CSS hooks.

## Files

- `autogen_dashboard/static/index.html`
- `autogen_dashboard/static/app.js`
- `autogen_dashboard/static/styles.css`
- `tests/test_phase5_ui_contract.py`

## Decisions

- Route and stage context now render as dedicated operator strips at the active-run header instead of transcript prefixes.
- Transcript actor separation is driven by preserved `source` and `metadata`, not just the coarse `role` value.
- Timeline was added as a top-level tab immediately so later operator views can build on the same shell contract.

## Verification

- `.\.venv\Scripts\python.exe -m unittest tests.test_phase5_ui_contract -v`
- `node --check autogen_dashboard\static\app.js`
