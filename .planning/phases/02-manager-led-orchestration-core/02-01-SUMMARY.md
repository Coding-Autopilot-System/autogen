---
phase: 02-manager-led-orchestration-core
plan: 01
subsystem: manager-contract
tags: [manager, orchestration, stage-machine, maf, persistence]
requires:
  - phase: 01
    provides: workspace-scoped runs and durable run directories
provides:
  - canonical manager-owned stage contract shared across runtime and workflow layers
  - run-scoped orchestration artifact layout under runtime/orchestration and artifacts/stages
  - manager-led repo_team workflow wrapper with explicit specialist ownership
affects: [maf-runtime, repo-team, stage-contract, orchestration-tests]
requirements-completed: [ORCH-01]
completed: 2026-03-21
---

# Phase 02 Plan 01: Manager Contract Summary

## Accomplishments

- Added `maf_core/orchestration.py` as the canonical stage machine for `planning -> research -> implementation -> review -> validation`.
- Added serializable `RunOrchestrationState`, `StageRecord`, `StageSummary`, and `AutoAnswerRecord` helpers so stage transitions no longer depend on transcript parsing.
- Updated `maf_core/workflow_factory.py` to expose run-scoped orchestration and stage-artifact layout instead of raw checkpoint storage only.
- Refactored `maf_core/team_factory.py` into a manager-led workflow wrapper that exposes canonical stages and structured specialist handoff expectations.
- Updated `maf_core/agent_factory.py` and `entities/repo_team/workflow.py` so the active repo team clearly advertises manager-led engineering orchestration.

## Files

- `maf_core/orchestration.py`
- `maf_core/workflow_factory.py`
- `maf_core/team_factory.py`
- `maf_core/agent_factory.py`
- `entities/repo_team/workflow.py`
- `tests/test_phase2_manager.py`
- `tests/test_maf_setup.py`

## Decisions

- Stage order is fixed and shared from one module, not reconstructed from UI or workflow descriptions.
- `validation` exists as a first-class terminal stage even before full validation automation is implemented.
- Workflow objects now carry orchestration layout metadata so later phases can attach traces and artifacts without guessing directory structure.

## Verification

- `.\.venv\Scripts\python.exe -m unittest tests.test_phase2_manager tests.test_maf_setup -v`
