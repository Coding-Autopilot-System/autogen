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
- Phase 2: manager-owned orchestration state machine with canonical stages, stage-scoped persistence, and explicit pause semantics
- Phase 2: automatic GSD clarification answers for common planning-context questions plus blocked-question persistence
- Phase 2: dashboard orchestration summary cards with stage timeline, stage outputs, and route metadata
- Phase 3: visible specialist roster, handoff visibility, route lanes, planned-versus-actual routing history, and operator tabs for Overview, Agents, Routing, and Artifacts
- Phase 4: routine-safe autonomous repo writes, durable changed-file and diff artifacts, targeted local validation, and explicit approval scopes for risky actions
- Phase 5: polished Operator Workbench UI with active route/stage strips, distinct message families, and dedicated Overview, Timeline, Agents, Routing, and Artifacts views

### Active

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
| Keep Microsoft Agent Framework as the active runtime base | The current repo already runs on MAF and has working entities, workflows, and DevUI integration | Validated in Phase 2 |
| Treat the product as a local-first orchestration workbench | Your main usage is on the local machine with installed CLIs, local repo access, and local validation | Validated in Phase 1 |
| Use a manager-driven multi-agent workflow as the primary interaction model | The goal is one-prompt execution with specialist delegation rather than manual step-by-step prompting | Validated in Phase 2 |
| Make orchestration state explicit and durable | Phase 2 needs a shared contract for pause/resume/retry and operator visibility | Validated in Phase 2 |
| Answer routine GSD clarification locally from planning context first | Common planning questions should not burn extra model turns or always block the operator | Validated in Phase 2 |
| Keep the manager as the only canonical run owner while surfacing specialists as first-class visible actors | This preserves one durable workflow contract while still making delegation observable | Validated in Phase 3 |
| Make route lanes the main operator control and persist planned-versus-actual routing history | Users need cost/depth control and clear fallback visibility without reading raw traces | Validated in Phase 3 |
| Organize the dashboard operator surface into task-oriented tabs instead of one generic orchestration panel | Specialist, routing, and artifact visibility should feel product-grade and scannable | Validated in Phase 3 |
| Allow routine-safe repo edits and local validation to run automatically while pausing risky actions with explicit approval scope | The platform should be a safe default-doer, not only a planner or reviewer | Validated in Phase 4 |
| Treat `autogen_dashboard` as the primary local product UI and keep DevUI secondary | The operator workbench now needs a durable, polished surface that is not constrained by framework-debug UX | Validated in Phase 5 |
| Surface route, model, stage, approval, and artifact context in dedicated strips and cards instead of transcript prefixes | Operator trust depends on scanable product surfaces rather than raw-log reading | Validated in Phase 5 |
| Defer Azure Function/REST hosting to a later stage | Cloud exposure matters, but local execution quality and operator UX are higher priority in v1 | Validated in Phase 1 |
| Prefer Gemini API first and local CLIs as fallback or specialist paths | This fits your installed tooling, cost preference, and current runtime capabilities | Validated in Phase 1 |

## Current State

- Phase 1 is complete: runs now start from an explicit workspace, persist under one durable run identity, and surface workspace drift visibly.
- Phase 2 is complete: the active dashboard runtime now executes against a manager-owned stage machine with durable stage artifacts, stage-aware pause kinds, and retry-scoped resume behavior.
- Phase 3 is complete: specialist roster state, handoff visibility, route lanes, planned-versus-actual route history, and operator-facing routing/artifact tabs are now part of the durable run contract.
- Phase 4 is complete: routine-safe implementation edits now execute inside the selected repo, changed files and diff artifacts persist per run, validation results are recorded durably, and destructive or externally-visible actions pause with explicit approval scope.
- Phase 5 is complete: the Operator Workbench is now the polished local UI with active route/stage strips, distinct message families, dedicated Timeline/Agents/Routing/Artifacts tabs, and stronger operator ergonomics.
- The product now supports one-prompt manager-led runs, specialist visibility, routing transparency, diff/validation inspection, and a professional operator-grade local workflow.
- The next milestone should focus on Azure Function or REST exposure and cloud-ready execution boundaries rather than more local-only UI work.

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
*Last updated: 2026-03-22 after Phase 05 completion*
