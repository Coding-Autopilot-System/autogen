# GSD Orchestration Platform

## What This Is

This project is a local-first multi-agent orchestration platform for software development, built around Microsoft Agent Framework, GSD workflows, and your installed AI backends. Its job is to let you open the UI, choose a repo, type one engineering prompt, and have a manager agent coordinate planning, specialist execution, code edits, validation, traces, and final output with minimal manual back-and-forth.

The primary user is you as the operator and developer. The current codebase already provides a repo-aware MAF runtime, DevUI integration, routing and fallback logic, and a retained legacy AutoGen dashboard path; this project evolves that into a more polished, autonomous, professional engineering workbench.

## Core Value

You can give one prompt and watch a trustworthy multi-agent coding system drive real repo work end-to-end with clear traces, specialist visibility, and minimal manual intervention.

## Requirements

### Validated

- Existing: repo-aware local agent runtime via Microsoft Agent Framework and DevUI in `maf_starter/` and `entities/`
- Existing: multi-agent workflow scaffolding, including the `repo_team` planner/researcher/implementer/reviewer workflow
- Existing: provider and model routing with fallback across Gemini API, optional Anthropic, and CLI fallbacks
- Existing: human-in-the-loop and route trace mechanisms in local form through tool approval, route metadata, and DevUI patching
- Existing: legacy dashboard and session-management path in `autogen_dashboard/` and `autogen_starter/`
- Phase 1: explicit repo or worktree run creation, durable run directories, and retry-safe run identity
- Phase 1: run-scoped MAF repo-root and checkpoint overrides with workspace freshness and stale-workspace warnings

### Active

- [ ] A manager agent can take one prompt in the UI and drive the GSD workflow automatically for repo work
- [ ] Specialist agents can plan, research, implement, review, and report progress with clear per-agent visibility
- [ ] The operator UI feels professional and polished, with strong visual design, modern message bubbles, route cards, rounded panels, and readable traces
- [ ] The UI exposes model selection, routing decisions, fallback history, and per-agent activity without forcing raw log reading
- [ ] The system can autonomously edit files and run local validation by default, instead of asking for approval on every step
- [ ] Sessions, traces, and outputs are inspectable and reusable so runs can be understood, resumed, and exported
- [ ] The core orchestration runtime is designed so it can later be exposed through an Azure Function or REST API without a full rewrite

### Out of Scope

- Multi-tenant external product for general public users - v1 is for you as the primary operator and developer
- Full production Azure deployment in the first milestone - local-first maturity comes before cloud hosting
- Non-coding general assistant behavior - the product is optimized for repo-aware engineering execution

## Context

This is a brownfield codebase with an existing local agent runtime. The active path is MAF-first: `main.py` dispatches into `maf_starter/cli.py`, entities are discovered from `entities/`, and DevUI is used for local interaction. The repo also retains a substantial legacy AutoGen stack in `autogen_dashboard/` and `autogen_starter/`, which creates both opportunity and drift risk.

The workstation context matters. GSD is already installed locally, and you also have Gemini CLI, Claude CLI, and Codex CLI available, along with Gemini API access and local Azure Functions development tools. The intended operating model is to use the local machine as the main execution environment, let Gemini API answer most orchestration and GSD questions automatically, and use the installed CLIs as specialist workers or fallback engines when appropriate.

The current repo already proves some of the technical foundation: repo-aware tools, fallback chains, multi-agent workflow scaffolding, session persistence, and DevUI customization hooks. The next evolution is not a greenfield rewrite; it is turning an engineering-heavy prototype into a more autonomous, polished orchestration platform with a stronger UX and clearer runtime behavior.

## Constraints

- **Tech stack**: Extend the current Python and Microsoft Agent Framework codebase rather than rewriting into a different platform - preserves working runtime primitives and existing investment
- **Runtime**: Must work well on the local Windows machine with installed CLI tools and local virtualenv workflows - this is the primary execution environment
- **Autonomy**: Default behavior should favor automatic code editing and local validation once a prompt is given - manual approval should be the exception, not the baseline
- **Cost**: Prefer Gemini API and available local CLI tools before introducing additional paid API dependencies - keeps experimentation affordable
- **UX**: The UI must look professional and readable, not like an internal demo shell - this is a productized operator workbench, not only a developer test harness
- **Future deployment**: Design the orchestration core so Azure Function or REST exposure can be added later without re-architecting the whole runtime - local-first now, cloud-ready later

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep Microsoft Agent Framework as the active runtime base | The current repo already runs on MAF and has working entities, workflows, and DevUI integration | Pending |
| Treat the product as a local-first orchestration workbench | Your main usage is on the local machine with installed CLIs, local repo access, and local validation | Validated in Phase 1 |
| Use a manager-driven multi-agent workflow as the primary interaction model | The goal is one-prompt execution with specialist delegation rather than manual step-by-step prompting | Pending |
| Make autonomous repo editing and validation the default behavior | You explicitly want the system to do the work automatically instead of asking on every step | Pending |
| Defer Azure Function/REST hosting to a later stage | Cloud exposure matters, but local execution quality and operator UX are higher priority in v1 | Validated in Phase 1 |
| Prefer Gemini API first and local CLIs as fallback or specialist paths | This fits your installed tooling, cost preference, and current runtime capabilities | Validated in Phase 1 |

## Current State

- Phase 1 is complete: runs now start from an explicit workspace, persist under one durable run identity, and surface workspace drift visibly.
- The active MAF runtime can be re-scoped per run for repo root and checkpoint storage instead of relying only on startup-time defaults.
- The next execution focus is Phase 2, where the manager-led orchestration state machine will replace the current mostly single-turn runtime behavior.

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `$gsd-transition`):
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone** (via `$gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-21 after Phase 01 completion*
