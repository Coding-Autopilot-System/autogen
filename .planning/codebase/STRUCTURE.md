# Codebase Structure

**Analysis Date:** 2026-03-26

## Directory Layout

```text
autogen/
- .planning/                 # GSD roadmap, phase artifacts, and codebase maps
- command_center/            # Primary operator FastAPI app and browser assets
  - static/components/       # Browser-side transcript, inspector, and error UI modules
- entities/                  # DevUI and AG-UI discovery wrappers plus workflow runners
- maf_core/               # Active MAF runtime, orchestration, routing, tools, guardrails
  - control_plane/           # Shared `/api/v1` REST contracts, auth, service, and store
- workflows/                 # YAML workflow definitions loaded at runtime
- autogen_dashboard/         # Legacy dashboard and shared repo-context helper
- autogen_starter/           # Legacy AutoGen CLI and provider bootstrap
- tests/                     # Runtime, API, orchestration, workflow, and UI contract tests
- state/                     # Runtime checkpoints, run records, and artifacts
- main.py                    # Root CLI entrypoint
- README.md                  # Operator/runtime documentation
```

## Directory Purposes

**`maf_core/`:**
- Purpose: Active runtime and orchestration core.
- Contains: bootstrap, settings, routing, fallback, repo tools, write and validation guardrails, workflow and team builders, manager-worker support, and `control_plane/`.
- Key files: `maf_core/cli.py`, `maf_core/config.py`, `maf_core/agent_factory.py`, `maf_core/provider_fallback.py`, `maf_core/team_factory.py`, `maf_core/workflow_factory.py`, `maf_core/control_plane/router.py`

**`command_center/`:**
- Purpose: Primary operator HTTP surface.
- Contains: `command_center/app.py` plus browser assets in `command_center/static/`.
- Key files: `command_center/app.py`, `command_center/static/app.js`, `command_center/static/components/transcript.js`

**`entities/`:**
- Purpose: Discovery wrappers and workflow executors instantiated by ID.
- Contains: model-pinned repo agents, workflow wrappers, `dynamic_workflow_runner.py`, `workflow_runner.py`, and `interrupts.py`.
- Key files: `entities/repo_team/workflow.py`, `entities/manager_worker_team/agent.py`, `entities/workflow_runner.py`, `entities/planner_agent.py`

**`workflows/`:**
- Purpose: Declarative YAML workflows.
- Contains: one YAML file per runtime-loadable workflow.
- Key files: `workflows/default.yaml`

**`autogen_dashboard/`:**
- Purpose: Legacy dashboard boundary plus shared repo scanning and context helpers reused by `command_center/app.py`.
- Contains: legacy FastAPI app, session runtime and store, static assets, repo context helpers, and schemas.
- Key files: `autogen_dashboard/app.py`, `autogen_dashboard/session_runner.py`, `autogen_dashboard/repo_context.py`, `autogen_dashboard/session_store.py`

**`autogen_starter/`:**
- Purpose: Legacy AutoGen CLI and provider readiness path.
- Contains: CLI parser, provider config, and model client setup.
- Key files: `autogen_starter/cli.py`, `autogen_starter/providers.py`, `autogen_starter/config.py`

**`tests/`:**
- Purpose: Regression coverage for runtime, operator surfaces, and contract boundaries.
- Contains: phase-oriented API and runtime tests, workflow tests, persistence tests, and worker delegation tests.
- Key files: `tests/test_command_center.py`, `tests/test_phase6_api_contract.py`, `tests/test_phase6_service.py`, `tests/test_workflows.py`, `tests/test_worker_delegation.py`

**`state/`:**
- Purpose: Durable runtime artifacts produced by the active runtime.
- Contains: checkpointed workflow state and control-plane session records.
- Key files: runtime-created directories under `state/maf-checkpoints/` and `state/sessions/`

**`.planning/`:**
- Purpose: GSD planning artifacts and repo map docs.
- Contains: milestone and phase docs, research, project state, and codebase maps.
- Key files: `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md`

## Key File Locations

**Entry Points:**
- `main.py`: Root CLI dispatcher.
- `maf_core/cli.py`: Active host commands for `doctor`, `smoke`, `probe-models`, `ui`, and `devui`.
- `command_center/app.py`: Primary FastAPI and AG-UI app.
- `autogen_dashboard/app.py`: Legacy FastAPI app.
- `autogen_starter/cli.py`: Legacy AutoGen CLI host.

**Configuration:**
- `maf_core/config.py`: Environment-driven settings and run scoping.
- `.env.example`: Runtime environment contract.
- `workflows/default.yaml`: Declarative workflow definition.

**Core Logic:**
- `maf_core/agent_factory.py`: Repo copilot and workflow-agent builders.
- `maf_core/team_factory.py`: Manager-led `repo_team` workflow.
- `maf_core/manager_worker_team_factory.py`: Manager-to-CLI-worker path.
- `maf_core/control_plane/service.py`: Run-control facade.
- `maf_core/provider_fallback.py`: Route execution and provider fallback.
- `maf_core/tools.py`: Repo tool boundary and safe write entrypoint.

**Testing:**
- `tests/test_command_center.py`: Command Center app behavior.
- `tests/test_phase6_command_center_parity.py`: Command Center and control-plane parity checks.
- `tests/test_phase6_service.py`: Control-plane service and store behavior.
- `tests/test_workflows.py`: YAML and dynamic workflow behavior.
- `tests/test_run_persistence.py`: Run artifact and persistence behavior.

## Naming Conventions

**Files:**
- Use `snake_case.py` across `maf_core/`, `command_center/`, `autogen_dashboard/`, `autogen_starter/`, and top-level runtime helpers.
- Use `agent.py` for exposed agents under `entities/<entity_id>/`.
- Use `workflow.py` for exposed workflows under `entities/<workflow_id>/`.
- Use `<workflow_name>.yaml` for declarative workflows under `workflows/`.
- Keep shared runtime modules responsibility-based, for example `provider_fallback.py`, `workflow_parser.py`, `repo_execution.py`, and `validation_runner.py`.

**Directories:**
- Use boundary or surface names for top-level packages, such as `command_center/`, `maf_core/`, and `autogen_dashboard/`.
- Use exposed catalog or entity IDs for discovery packages under `entities/`, such as `entities/repo_copilot_auto/` and `entities/manager_worker_team/`.
- Keep REST boundary code under `maf_core/control_plane/` rather than under `command_center/`.

## Where to Add New Code

**New Feature:**
- Primary runtime or orchestration behavior: `maf_core/`
- REST run-control API shape or persistence: `maf_core/control_plane/`
- Operator UI and HTTP handlers: `command_center/app.py` and `command_center/static/`
- Tests: `tests/` with the boundary-matching pattern used by the existing phase tests

**New Component/Module:**
- New repo-aware agent exposed in UI or DevUI: `entities/<agent_id>/agent.py`
- New exposed workflow: `entities/<workflow_id>/workflow.py`
- New declarative YAML workflow: `workflows/<workflow_name>.yaml`
- Keep entity files thin wrappers; place substantive runtime logic in `maf_core/` or `command_center/`

**Utilities:**
- Shared backend and runtime helpers: `maf_core/`
- Browser-side helpers and components: `command_center/static/utils.js` and `command_center/static/components/`
- Shared repo scanning and workspace context helpers: `autogen_dashboard/repo_context.py`
- Do not place new primary runtime logic under `autogen_dashboard/` or `autogen_starter/` unless the task is explicitly compatibility maintenance

## Special Directories

**`state/`:**
- Purpose: Durable runtime artifacts, checkpoints, stage outputs, transcripts, events, and attempts.
- Generated: Yes
- Committed: No

**`.planning/`:**
- Purpose: Project planning, roadmap, research, validation, and codebase maps.
- Generated: No
- Committed: Yes

**`workflows/`:**
- Purpose: Runtime-loaded YAML workflow definitions.
- Generated: No
- Committed: Yes

---

*Structure analysis: 2026-03-26*


