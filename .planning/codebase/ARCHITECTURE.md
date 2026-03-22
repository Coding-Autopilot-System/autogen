# Architecture

## Runtime Surfaces
- `main.py` is the thin entrypoint; it dispatches into `maf_starter/cli.py`.
- `maf_starter/cli.py` exposes `doctor`, `smoke`, `probe-models`, `ui`, and `devui`.
- `command_center/app.py` hosts the primary operator API and AG-UI endpoints.
- `autogen_dashboard/app.py` remains the legacy FastAPI surface for compatibility.
- `entities/repo_copilot/*.py` and `entities/repo_team/*.py` expose DevUI-discovered agent/workflow entrypoints.

## Orchestration Flow
- Configuration loads in `maf_starter/config.py` from `.env` at the repo root.
- Agent construction starts in `maf_starter/agent_factory.py`.
- Repo tools come from `maf_starter/tools.py` and are bound to the configured repo root.
- The active agent uses `maf_starter/provider_fallback.py` middleware for route selection and fallback execution.
- Workflow assembly lives in `maf_starter/workflow_factory.py` and `maf_starter/team_factory.py`.

## Routing and Fallback
- `maf_starter/routing_policy.py` builds a `RoutingPlan` from prompt shape, explicit lane, and requested model/provider overrides.
- `maf_starter/routing_types.py` carries the route steps, attempts, and capability drift metadata.
- `provider_fallback.py` resolves the effective run scope, then tries the primary Gemini path first.
- On quota or rate-limit style failures, the middleware falls back across Gemini, Anthropic, and CLI providers.
- CLI fallbacks (`gemini.cmd`, `claude`, `codex.cmd`) are last-resort paths and do not preserve tool calling.

## Manager and Specialist Model
- `maf_starter/orchestration.py` defines the canonical stages: planning, research, implementation, review, validation.
- The same module defines visible specialist roles: manager, planner, researcher, implementer, reviewer.
- `team_factory.py` builds the manager-led sequential workflow and exposes specialist profiles for operator views.
- Stage transitions are persisted through `RunOrchestrationState`, `StageRecord`, `StageSummary`, and handoff records.
- The manager owns the run; specialists publish current task, latest output summary, and handoff metadata.

## Persistence Boundaries
- Run checkpoints and orchestration state are stored under `state/maf-checkpoints` by default.
- `maf_starter/workflow_factory.py` wraps `FileCheckpointStorage` with run-scoped checkpoint selection.
- `maf_starter/orchestration.py` derives runtime paths such as `runtime/orchestration/state.json` and `artifacts/stages/*`.
- `maf_starter/repo_execution.py` captures write operations, changed files, and unified diffs for safe repo edits.
- Legacy run storage lives in `autogen_dashboard/session_store.py` with session metadata, transcripts, events, and artifacts.

## UI and Backend Split
- `command_center/app.py` is the primary HTTP backend and AG-UI host.
- `command_center/static/app.js`, `index.html`, and `styles.css` render the operator workbench.
- The command center streams protocol events and exposes catalog, repo, and health endpoints.
- `autogen_dashboard/app.py` still serves the older FastAPI dashboard and session API.
- `maf_starter/devui_patches.py` and `maf_starter/devui_overrides.py` only customize the local DevUI debugger.

## Data and Control Flow
- User input enters `main.py`, then reaches `maf_starter/cli.py` or the HTTP app layer.
- The active repo root and checkpoint dir are threaded through `maf_starter/config.py` and scoped with context vars.
- Agent turns flow through `build_repo_tools`, routing policy, fallback middleware, and response metadata decoration.
- Workflow runs flow through `team_factory.py`, which projects orchestration state into workflow metadata and checkpoints.
- Safe repo writes flow through `maf_starter/tools.py` into `maf_starter/repo_execution.py`, then into stage artifacts and validation outputs.
