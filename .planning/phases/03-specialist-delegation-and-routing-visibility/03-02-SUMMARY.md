---
phase: 03-specialist-delegation-and-routing-visibility
plan: 02
subsystem: routing-contract
tags: [routing, fallback, lane-selection, provider-visibility, compatibility]
requires:
  - plan: 03-01
    provides: specialist ownership contract
provides:
  - lane-aware route planning and requested-model persistence per run
  - planned-vs-actual route history with fallback attempts and capability drift
  - compatibility updates for the installed Microsoft Agent Framework package surface
affects: [routing-runtime, provider-fallback, maf-runtime, tests]
requirements-completed: [ROUT-01, ROUT-02, ROUT-03]
completed: 2026-03-21
---

# Phase 03 Plan 02: Routing Contract Summary

## Accomplishments

- Added lane-aware route selection with `auto`, `deep`, `balanced`, and `fast` controls that persist on each run.
- Recorded requested provider/model, planned route chain, actual route attempts, fallback count, and capability changes in structured session metadata.
- Updated the fallback middleware and route helpers so API-first execution can fall through cleanly while preserving operator-visible route history.
- Aligned the MAF integration with the installed SDK surface on this machine by adapting to `ChatAgent`, root-level builders, and compatibility `ResponseStream` handling.

## Files

- `maf_starter/routing_types.py`
- `maf_starter/routing_policy.py`
- `maf_starter/provider_fallback.py`
- `maf_starter/config.py`
- `maf_starter/agent_factory.py`
- `maf_starter/team_factory.py`
- `maf_starter/workflow_factory.py`
- `tests/test_phase3_routing.py`
- `tests/test_maf_setup.py`

## Decisions

- Route lanes are now the primary operator control for model depth and cost posture; direct model pinning remains an override, not the main workflow.
- Planned-versus-actual routing stays attached to the run contract instead of living only in DevUI or provider-specific traces.
- SDK compatibility fixes are treated as part of the routing contract because fallback and route visibility must work against the real locally installed MAF package.

## Verification

- `.\.venv\Scripts\python.exe -m unittest tests.test_phase3_routing tests.test_maf_setup -v`
- `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- `.\.venv\Scripts\python.exe -m compileall maf_starter autogen_dashboard tests main.py`
