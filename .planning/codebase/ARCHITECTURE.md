# Architecture

**Analysis Date:** 2026-03-20

## Pattern Overview

**Overall:** MAF-first local agent runtime with factory-based assembly, entity discovery, fallback middleware, and a retained legacy AutoGen dashboard stack.

**Key Characteristics:**
- Thin bootstrap entrypoint in `main.py`
- Environment-driven assembly from `maf_starter/config.py`
- Entity/workflow discovery through the `entities/` tree
- Fallback across API models and local CLI providers
- Local-only DevUI customization via runtime monkey patches and bundle rewriting

## Layers

**Bootstrap Layer:**
- Purpose: start commands and dispatch into the active runtime
- Contains: `main.py`, `maf_starter/cli.py`, `start_devui.ps1`, `stop_devui.ps1`
- Depends on: config loading and runtime factories
- Used by: human operators running the repo locally

**Configuration Layer:**
- Purpose: resolve paths, API keys, model defaults, fallback chains, and repo roots
- Contains: `maf_starter/config.py`
- Depends on: `.env` and `.env.example`
- Used by: every active MAF entrypoint and factory

**Runtime Assembly Layer:**
- Purpose: build agents, workflows, and team orchestrations
- Contains: `maf_starter/agent_factory.py`, `maf_starter/workflow_factory.py`, `maf_starter/team_factory.py`
- Depends on: config, tools, routing, and fallback middleware
- Used by: DevUI-discovered entities and smoke/doctor/probe flows

**Cross-Cutting Runtime Layer:**
- Purpose: route prompts, retry providers, expose repo tools, and shape DevUI output
- Contains: `maf_starter/routing_policy.py`, `maf_starter/provider_fallback.py`, `maf_starter/tools.py`, `maf_starter/devui_patches.py`, `maf_starter/devui_overrides.py`
- Depends on: Agent Framework clients, subprocess CLIs, repo filesystem
- Used by: active MAF agent and workflow executions

**Entity Surface Layer:**
- Purpose: expose concrete agents and workflows to DevUI directory discovery
- Contains: `entities/repo_copilot/*`, `entities/repo_copilot_auto/*`, `entities/repo_copilot_pro/*`, `entities/repo_copilot_flash/*`, `entities/repo_copilot_flash_lite/*`, `entities/repo_copilot_workflow/*`, `entities/repo_team/*`
- Depends on: starter factories
- Used by: DevUI entity selection

**Legacy Runtime Layer:**
- Purpose: preserve the older AutoGen dashboard and provider/session architecture
- Contains: `autogen_starter/*.py`, `autogen_dashboard/*.py`
- Depends on: AutoGen packages, FastAPI, Pydantic, file-backed session state
- Used by: legacy manual flows only

## Data Flow

**MAF Agent Turn:**
1. User runs `python main.py ...` or launches DevUI via `start_devui.ps1`
2. `main.py` dispatches into `maf_starter/cli.py`
3. `load_settings()` in `maf_starter/config.py` resolves model, paths, keys, and fallback chain
4. `build_agent()` or a workflow builder assembles an agent with repo tools and fallback middleware
5. `routing_policy.py` classifies the prompt as `simple`, `standard`, or `deep`
6. `provider_fallback.py` executes the primary provider and falls through alternate APIs/CLIs on quota/rate failures
7. DevUI patches add route metadata; DevUI overrides attempt to restyle the local UI
8. Checkpoints and state are written under `state/`

**Sequential Multi-Agent Workflow (`repo_team`):**
1. `team_factory.py` builds `planner`, `researcher`, `implementer`, and `reviewer`
2. `SequentialBuilder` runs them in order with file checkpoint storage
3. `with_request_info()` inserts human pauses for planner, implementer, and reviewer stages
4. Results are surfaced through DevUI as a workflow rather than a single chat agent

**Legacy Dashboard Turn:**
1. FastAPI routes in `autogen_dashboard/app.py` accept REST and SSE session commands
2. `autogen_dashboard/session_runner.py` manages session state, prompts, provider fallback, and persistence
3. Static frontend files in `autogen_dashboard/static/` render the dashboard UI

**State Management:**
- Active MAF state is file-based under `state/maf-checkpoints`
- Legacy AutoGen state is file-based under `state/team_state.json` and `state/sessions/*`

## Key Abstractions

**Factory:**
- Purpose: centralize agent and workflow construction
- Examples: `maf_starter/agent_factory.py`, `maf_starter/team_factory.py`, `maf_starter/workflow_factory.py`
- Pattern: pure builder functions with config injection

**Routing Plan:**
- Purpose: classify a user turn and decide provider/model order
- Examples: `RoutingPlan` in `maf_starter/routing_policy.py`
- Pattern: small immutable planning object with primary and fallback steps

**Repo Tool Boundary:**
- Purpose: constrain agent access to local repo files through explicit tools
- Examples: `get_repo_overview`, `list_repo_files`, `read_repo_file`, `search_repo`, `request_human_approval` in `maf_starter/tools.py`
- Pattern: tool-wrapped boundary APIs over the filesystem

## Entry Points

**CLI Entry:**
- Location: `main.py`
- Triggers: `python main.py doctor|smoke|probe-models|devui`
- Responsibilities: delegate to the active MAF CLI

**DevUI Launcher:**
- Location: `start_devui.ps1`
- Triggers: local PowerShell invocation
- Responsibilities: start `python main.py devui` and capture logs

**Legacy Dashboard Entry:**
- Location: `autogen_starter/cli.py`
- Triggers: legacy `dashboard` command path
- Responsibilities: launch `autogen_dashboard.app`

## Error Handling

**Strategy:** explicit exception propagation with boundary translation and fallback retries.

**Patterns:**
- Config errors raise `ValueError` in `maf_starter/config.py`
- Provider fallback retries only on heuristic quota and rate-limit errors in `maf_starter/provider_fallback.py`
- Legacy FastAPI endpoints translate `ValueError`, `KeyError`, and `ProviderConfigError` into HTTP errors in `autogen_dashboard/app.py`

## Cross-Cutting Concerns

**Logging:**
- Mostly `print(...)` and local log files rather than a structured logging framework

**Validation:**
- Path and repo-root safety checks in `maf_starter/tools.py`
- Session and request schema validation in the legacy dashboard layer

**Human Approval:**
- Implemented as a mandatory-approval tool in the active MAF path
- Implemented as explicit session actions in the legacy dashboard path

---

*Architecture analysis: 2026-03-20*
*Update when major runtime patterns change*
