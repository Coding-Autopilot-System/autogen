# autogen Wiki

## Role in the CAS portfolio

`autogen` is the **Execution plane** of the Coding-Autopilot-System three-plane model (Control
/ Execution / Governance). Built on Microsoft Agent Framework, it runs manager-led,
specialist-delegated engineering work against a real repository: planning, research,
implementation, review, and validation, with bounded repo tools and an approval gate for
destructive actions.

| Plane | This repo's responsibility |
|---|---|
| Control | *(not this repo — see `gsd-orchestrator`)* |
| Execution | Manager-led worker fan-out, bounded repo tools, provider routing/fallback, run artifacts |
| Governance | *(not this repo — see `Promptimprover`, `cas-contracts`, `cas-evals`)* |

## Quickstart

- [README.md](../../README.md) — Quickstart, configuration reference, evidence posture
- [Architecture](./Architecture.md) — worker fan-out, telemetry boundary (in progress), critic gate (in progress)
- [Operations](./Operations.md) — verified run/test/CI commands
- [Decisions](./Decisions.md) — phase history and open PRs

## MAF 1.0 alignment

The repo direction is to reuse Microsoft Agent Framework's workflow and UI model, not to fork it.

- keep the current manager-led specialist graph and evolve it with official MAF workflow builders;
- keep the local operator experience, but converge toward DevUI or AG-UI style surfaces for richer execution traces and graphical workflow visibility;
- treat the legacy dashboard as a transition shell, not the long-term orchestration abstraction.

## Ecosystem links

Part of the [Coding-Autopilot-System](https://github.com/Coding-Autopilot-System) org:
[gsd-orchestrator](https://github.com/Coding-Autopilot-System/gsd-orchestrator) (control plane) ·
[Promptimprover](https://github.com/Coding-Autopilot-System/Promptimprover) (prompt governance) ·
[cas-contracts](https://github.com/Coding-Autopilot-System/cas-contracts) (shared schemas) ·
[cas-evals](https://github.com/Coding-Autopilot-System/cas-evals) (evidence gate)

<!-- docs-verified: 91d12d3 2026-07-08 -->
