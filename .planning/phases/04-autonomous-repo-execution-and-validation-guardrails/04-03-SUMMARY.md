---
phase: 04-autonomous-repo-execution-and-validation-guardrails
plan: 03
subsystem: approval-policy-and-operator-scope
tags: [approval, risk, operator-ui, api, runtime-guardrails, compatibility]
requires:
  - plan: 04-01
    provides: controlled write execution and change artifacts
  - plan: 04-02
    provides: validation command/result artifacts and failure pauses
provides:
  - centralized risk classification for routine-safe, destructive, blocked, and externally-visible actions
  - pending-approval payloads with reason, affected paths, commands, and scope
  - operator-facing approval cards plus full-suite compatibility with the installed MAF SDK
affects: [maf-runtime, dashboard-ui, api-contract, tests]
requirements-completed: [EXEC-01, EXEC-03, EXEC-04]
completed: 2026-03-21
---

# Phase 04 Plan 03: Approval Guardrails Summary

## Accomplishments

- Added a central approval-policy module that classifies write and validation actions as routine-safe, destructive, externally visible, or blocked.
- Updated the runtime so risky actions pause with explicit `pending_approval` payloads instead of executing or hiding the scope in transcript text.
- Extended the dashboard operator surface to render approval scope, affected files, and validation outcomes as first-class cards in overview and approval views.
- Aligned the older MAF compatibility assumptions with the installed SDK primitives so the full regression suite runs green against the real local package surface.

## Files

- `maf_core/approval_policy.py`
- `maf_core/agent_factory.py`
- `maf_core/provider_fallback.py`
- `maf_core/routing_policy.py`
- `maf_core/team_factory.py`
- `maf_core/workflow_factory.py`
- `autogen_dashboard/schemas.py`
- `autogen_dashboard/session_runner.py`
- `autogen_dashboard/static/index.html`
- `autogen_dashboard/static/app.js`
- `autogen_dashboard/static/styles.css`
- `tests/test_phase4_approval.py`
- `tests/test_phase3_api.py`
- `tests/test_maf_setup.py`
- `tests/test_phase1_runtime.py`
- `tests/test_phase2_manager.py`
- `tests/test_phase3_specialists.py`
- `tests/test_phase3_routing.py`

## Decisions

- Approval is now policy-driven and stage-owned, not dependent on prompt wording or tool call etiquette.
- Routine-safe local edits and validation stay autonomous; destructive, blocked, and externally-visible actions surface explicit approval scope before execution.
- Compatibility fixes to the installed MAF SDK are treated as part of the approval closeout because Phase 4 cannot claim a green regression gate on stale local wrappers.

## Verification

- `.\.venv\Scripts\python.exe -m unittest tests.test_phase4_approval tests.test_phase3_api -v`
- `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- `.\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py`
- `node --check autogen_dashboard\static\app.js`
