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

- **PR #11** (`feat/phase-26-coverage-gates`) — already merged to `main`; it is now the
  compatibility baseline that exposed the remaining stale branch stack.
- **PRs #12, #13, #14, #15, #16** — still open on GitHub but stale against current `main`.
  Their surviving runtime, CI, and docs changes are being consolidated into one refreshed branch
  instead of re-merging the old dependency snapshot piecemeal.

## Directional decision

The medium-term architecture should adopt Microsoft Agent Framework's first-party workflow and UI
direction where it fits the local-first product:

- keep manager-led orchestration as a graph/workflow problem, not a free-form chat problem;
- prefer MAF-native workflow builders and DevUI or AG-UI style surfaces over inventing a parallel UI abstraction;
- keep the current dashboard only as a bridge while the richer graphical workflow surface matures.

<!-- docs-verified: 91d12d3 2026-07-08 -->
