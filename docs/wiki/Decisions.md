# Decisions

## ADR convention

`docs/adr/README.md` establishes the convention (sequential numbering, Context/Decision/
Consequences) but **no numbered ADR files exist in the repo yet**. Decisions to date live in
`.planning/phases/` plan/summary pairs instead.

## Phase history (`.planning/phases/`, this repo's own GSD project)

| Phase | Topic |
|---|---|
| 01 | Workspace and durable run foundation |
| 02 | Manager-led orchestration core |
| 03 | Specialist delegation and routing visibility |
| 04 | Autonomous repo execution and validation guardrails |
| 05 | Polished operator workbench |
| 06 | API boundary and control-plane contract |
| 07 | Worker boundary |

See each `.planning/phases/<NN-topic>/*-SUMMARY.md` for the detailed record.

## Open decisions tracked in this Phase 36 refresh

- **PR #11** (`feat/phase-26-coverage-gates`) — ratchets CI to a pytest-cov branch-coverage
  gate; open, not yet merged.
- **PR #12** (`feat/phase-28-fault-injection`) — structured JSON failure telemetry + CLI
  fallback size guards; open, not yet merged.
- **PR #13** (`ci/phase-31-workflow-hardening`) — pins third-party GitHub Actions to commit
  SHAs and least-privilege permissions; open, not yet merged.
- **PR #14** (`feat/phase-29-peer-critic`) — deterministic peer critic pattern-scan engine;
  open, not yet merged. See [Architecture](./Architecture.md) for the critic-gate design this
  PR introduces.

<!-- docs-verified: e52e6aa9383a11722bbf92f95c21ff39feb3dd65 2026-07-08 -->
