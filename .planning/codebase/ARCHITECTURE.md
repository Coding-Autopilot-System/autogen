# Architecture

**Analysis Date:** 2026-03-26

## Pattern Overview

**Overall:** Local-first orchestration runtime with shared MAF builders in `maf_core/`, a primary operator shell in `command_center/app.py`, a file-backed REST control plane in `maf_core/control_plane/`, DevUI/AG-UI discovery wrappers in `entities/`, and a separate legacy compatibility surface in `autogen_dashboard/` and `autogen_starter/`.

**Key Characteristics:**
- `main.py` is a thin bootstrap; `maf_core/cli.py` owns command parsing, logging setup, and Uvicorn/DevUI startup.
- Run scope is environment-driven and request-scoped. `maf_core/config.py` loads settings, then binds `repo_root` and `checkpoint_dir` with context vars for each run.
- `command_center/app.py` is the primary operator backend. It serves static UI assets from `command_center/static/`, AG-UI streaming endpoints, repo discovery, and the shared `/api/v1` router from `maf_core/control_plane/router.py`.
- The browser catalog is explicit. `command_center/app.py` uses a curated `AGENT_IDS` tuple and workflow lookups instead of scanning every package under `entities/`.
- Orchestration and persistence are file-backed. `maf_core/workflow_factory.py`, `maf_core/orchestration.py`, and `maf_core/control_plane/store.py` all project deterministic state under `state/`.

## Layers

**Bootstrap and Host Layer:**
- Purpose: Start the active runtime and choose the operator surface.
- Location: `main.py`, `maf_core/cli.py`, `start_ui.ps1`, `start_devui.ps1`, `stop_ui.ps1`, `stop_devui.ps1`
- Contains: CLI commands (`doctor`, `smoke`, `probe-models`, `ui`, `devui`), log configuration, and Uvicorn bootstrap.
- Depends on: `maf_core/config.py`, `command_center/app.py`, `maf_core/agent_factory.py`
- Used by: Local operators and Windows launcher scripts.

**Settings and Run Scope Layer:**
- Purpose: Resolve repo roots, workflow directories, checkpoint directories, and provider settings for a single run.
- Location: `maf_core/config.py`
- Contains: `Settings`, environment defaults, `with_run_scope()`, `activate_run_scope()`, `current_repo_root()`, `current_checkpoint_dir()`
- Depends on: `.env`, `.env.example`
- Used by: All active runtime builders, tools, workflows, and control-plane handlers.

**Command Center Layer:**
- Purpose: Expose the primary operator backend and AG-UI protocol surface.
- Location: `command_center/app.py`, `command_center/static/app.js`, `command_center/static/components/*.js`
- Contains: `/api/agui/*` streaming endpoints, `/api/catalog`, `/api/repos`, `/api/status`, `/healthz`, static asset hosting, and route banner decoration.
- Depends on: `maf_core/control_plane/router.py`, `maf_core/team_factory.py`, `maf_core/workflow_parser.py`, `entities/workflow_runner.py`, `autogen_dashboard/repo_context.py`
- Used by: Browser operators and AG-UI clients.

**Control Plane Layer:**
- Purpose: Provide resource-oriented run APIs independent of the AG-UI stream surface.
- Location: `maf_core/control_plane/contracts.py`, `maf_core/control_plane/router.py`, `maf_core/control_plane/service.py`, `maf_core/control_plane/store.py`, `maf_core/control_plane/auth.py`
- Contains: Pydantic contracts, `/api/v1/runs` endpoints, run summaries/details, durable JSON and JSONL storage, and auth policy selection.
- Depends on: `fastapi`, `pydantic`, `maf_core/orchestration.py`
- Used by: `command_center/app.py` and future external clients.

**Agent and Workflow Assembly Layer:**
- Purpose: Build repo-aware agents, workflows, route plans, and provider fallback chains.
- Location: `maf_core/agent_factory.py`, `maf_core/team_factory.py`, `maf_core/workflow_factory.py`, `maf_core/workflow_parser.py`, `maf_core/manager_worker_team_factory.py`, `maf_core/provider_fallback.py`, `maf_core/routing_policy.py`
- Contains: model-pinned agents, auto-routed agents, YAML workflow loading, the manager-led `repo_team` workflow, manager-to-CLI-worker delegation, and quota/rate-limit fallback middleware.
- Depends on: `agent_framework`, `agent_framework_devui`, `OpenAIChatClient`, optional `AnthropicClient`, and CLI executables through `maf_core/worker_delegation.py`
- Used by: `command_center/app.py`, `entities/*`, and `maf_core/cli.py`

**Repo Boundary and Guardrail Layer:**
- Purpose: Constrain filesystem access, classify risky actions, apply bounded writes, and plan validation.
- Location: `maf_core/tools.py`, `maf_core/repo_execution.py`, `maf_core/approval_policy.py`, `maf_core/validation_runner.py`
- Contains: repo overview/list/read/search tools, `request_human_approval`, `apply_repo_write_plan`, write-operation parsing/execution, validation command planning, and risk classification.
- Depends on: the run-scoped repo root from `maf_core/config.py`
- Used by: repo agents, the manager-worker manager, and downstream orchestration.

**Entity Exposure Layer:**
- Purpose: Keep DevUI and AG-UI discovery entrypoints thin and stable.
- Location: `entities/repo_copilot*/agent.py`, `entities/repo_copilot_workflow/workflow.py`, `entities/repo_team/workflow.py`, `entities/manager_worker_team/agent.py`, `entities/dynamic_workflow_runner.py`, `entities/workflow_runner.py`
- Contains: thin wrappers around builders plus dynamic and YAML workflow runners and human-interrupt types.
- Depends on: `maf_core/*` builders and workflow models.
- Used by: DevUI entity discovery and `command_center/app.py::_build_protocol_runner()`.

**Legacy Compatibility Layer:**
- Purpose: Preserve the older AutoGen dashboard and session lifecycle as a separate boundary.
- Location: `autogen_dashboard/app.py`, `autogen_dashboard/session_runner.py`, `autogen_dashboard/session_store.py`, `autogen_starter/cli.py`
- Contains: legacy FastAPI session APIs, session and event streaming, provider readiness, and AutoGen chat and step flows.
- Depends on: AutoGen packages and legacy schemas in `autogen_dashboard/schemas.py`
- Used by: Compatibility-only flows; the primary operator surface is `command_center/app.py`.

## Data Flow

**Command Center AG-UI Flow:**

1. `main.py` routes `python main.py ui` into `maf_core/cli.py::run_ui()`.
2. `maf_core/cli.py::run_ui()` keeps a debug DevUI server available, then serves `command_center/app.py`.
3. `/api/agui/{agent_id}` resolves repo-scoped settings with `_scoped_settings()` and chooses a protocol runner in `_build_protocol_runner()`.
4. The selected runner is one of `maf_core/agent_factory.py`, `maf_core/team_factory.py`, `maf_core/manager_worker_team_factory.py`, `entities/workflow_runner.py`, or `entities/dynamic_workflow_runner.py`.
5. AG-UI events stream back through `StreamingResponse`; route metadata is attached by `maf_core/provider_fallback.py`, and human approval pauses surface as `human_in_the_loop_request` events from `entities/interrupts.py`.

**Control Plane REST Flow:**

1. `command_center/app.py` mounts `maf_core/control_plane/router.py` at `/api/v1`.
2. `maf_core/control_plane/auth.py` selects `NoAuthPolicy` or `AzureFunctionsAuthPolicy` for request gating.
3. `maf_core/control_plane/service.py` creates, loads, continues, approves, retries, cancels, and annotates runs using `maf_core/control_plane/store.py`.
4. `maf_core/control_plane/store.py` persists metadata, transcript, events, orchestration state, stage artifacts, validation results, and attempt summaries under `state/sessions/{run_id}/`.
5. Artifact file reads go through manifest-relative path resolution in `maf_core/control_plane/router.py` to prevent path escape.

**Workflow Execution Flow:**

1. `maf_core/workflow_parser.py` loads `workflows/{workflow_name}.yaml` from `settings.workflows_dir`.
2. `entities/workflow_runner.py` hydrates `entities.workflow_state.WorkflowState` from the workflow orchestration state path and executes each step with `maf_core/agent_factory.py::build_agent_for_model()`.
3. `entities/dynamic_workflow_runner.py` asks `entities/planner_agent.py` for a JSON workflow, converts it into the same `Workflow` model, then reuses `entities/workflow_runner.py`.
4. Step-level approval pauses are raised as `HumanInTheLoop` exceptions from `entities/interrupts.py`.
5. Workflow state is saved under the run-scoped orchestration path exposed by `maf_core/workflow_factory.py::RunScopedWorkflowArtifacts`.

**Manager-Led Repo Team Flow:**

1. `maf_core/team_factory.py` builds a checkpointed planner -> researcher -> implementer -> reviewer chain.
2. `maf_core/orchestration.py` defines the canonical stage model: planning, research, implementation, review, validation.
3. `RunOrchestrationState` tracks stage records, specialist states, handoff records, auto-answer records, and blocked questions.
4. Stage summaries, diff artifacts, write operations, and validation outputs map to deterministic paths under `runtime/orchestration/` and `artifacts/stages/`.
5. `command_center/app.py::_catalog()` publishes specialist metadata from `workflow.specialist_profiles` so the UI can surface stage ownership.

**Manager + CLI Worker Flow:**

1. `entities/manager_worker_team/agent.py` exposes `maf_core/manager_worker_team_factory.py::build_manager_worker_agent()`.
2. The manager agent keeps repo tools locally and exposes `delegate_to_worker()` as an additional tool.
3. `maf_core/worker_delegation.py` assembles worker prompts with embedded file contents, routes task types to `gemini-cli`, `claude-cli`, or `codex-cli`, and normalizes JSON worker output.
4. `maf_core/manager_worker_orchestration.py` extends `RunOrchestrationState` with delegated `WorkerTask` records.
5. This path is separate from the `repo_team` workflow in `maf_core/team_factory.py`.

**State Management:**
- Active repo and checkpoint scope is carried in context vars from `maf_core/config.py`.
- Checkpointed MAF workflow artifacts live under `state/maf-checkpoints/` or repo-scoped children derived in `command_center/app.py::_checkpoint_dir_for_repo()`.
- Control-plane run records live under `state/sessions/{run_id}/` via `maf_core/control_plane/store.py`.
- Legacy session state lives under `autogen_dashboard/session_store.py` and is independent of `maf_core/control_plane/store.py`.

## Key Abstractions

**Settings and Run Scope:**
- Purpose: Bind environment configuration and the selected workspace to a single run.
- Examples: `maf_core/config.py`
- Pattern: `Settings` object plus contextvar-based scope activation.

**RoutingPlan:**
- Purpose: Decide the primary provider and model, fallback order, and route tier before execution starts.
- Examples: `maf_core/routing_policy.py`, `maf_core/routing_types.py`
- Pattern: small planning object that is later attached to response metadata.

**RunOrchestrationState:**
- Purpose: Model canonical stages, specialist ownership, pause kinds, handoffs, and stage outputs.
- Examples: `maf_core/orchestration.py`
- Pattern: dataclass-backed state machine serialized to JSON.

**ManagerWorkerOrchestrationState:**
- Purpose: Add delegated CLI worker task tracking on top of canonical run state.
- Examples: `maf_core/manager_worker_orchestration.py`
- Pattern: subclass extension of the base orchestration state.

**RunStore:**
- Purpose: Make control-plane run persistence deterministic and inspectable.
- Examples: `maf_core/control_plane/store.py`
- Pattern: file-backed repository object with stable per-run path helpers and manifest generation.

**Workflow and WorkflowRunner:**
- Purpose: Load YAML or planner-generated steps and execute them with per-step approval support.
- Examples: `maf_core/workflow_parser.py`, `entities/workflow_runner.py`, `entities/dynamic_workflow_runner.py`
- Pattern: declarative workflow definition plus imperative step runner.

**Repo Tool Surface:**
- Purpose: Give agents explicit, bounded access to the repo instead of raw filesystem access.
- Examples: `maf_core/tools.py`, `maf_core/repo_execution.py`
- Pattern: tool-wrapped filesystem and write-plan boundary with allow and deny rules.

## Entry Points

**Main CLI:**
- Location: `main.py`
- Triggers: `python main.py <command>`
- Responsibilities: Delegate directly into `maf_core/cli.py::main()`.

**Command Center:**
- Location: `maf_core/cli.py`, `command_center/app.py`
- Triggers: `python main.py ui`, `start_ui.ps1`
- Responsibilities: Host the primary operator UI, AG-UI streaming endpoints, repo catalog, status endpoints, and `/api/v1` control-plane routes.

**Raw DevUI Debugger:**
- Location: `maf_core/cli.py`, `maf_core/devui_patches.py`, `maf_core/devui_overrides.py`
- Triggers: `python main.py devui`, `start_devui.ps1`
- Responsibilities: Launch DevUI for entity inspection and patch the local DevUI UI.

**Workflow Definitions:**
- Location: `workflows/default.yaml`
- Triggers: `python main.py ui --workflow <name>` or AG-UI workflow lookup through `command_center/app.py`
- Responsibilities: Define step-based YAML workflows loaded by `maf_core/workflow_parser.py`.

**Legacy Dashboard:**
- Location: `autogen_starter/cli.py`, `autogen_dashboard/app.py`
- Triggers: `python -m autogen_starter.cli dashboard`
- Responsibilities: Host the legacy FastAPI dashboard and legacy session APIs.

## Error Handling

**Strategy:** Fail fast on config and path errors, translate at HTTP and stream boundaries, and only retry automatically for explicit fallback-worthy provider failures.

**Patterns:**
- `maf_core/config.py`, `maf_core/tools.py`, and `maf_core/agent_factory.py` raise `ValueError` for invalid paths, missing workflows, and bad config; `maf_core/cli.py` converts config failures into exit code `2`.
- `maf_core/provider_fallback.py` retries only quota and rate-limit style failures and records route attempts and capability changes in response metadata.
- `command_center/app.py` translates bad agent or workflow selection into `HTTPException(400)` and emits `RunErrorEvent` for streaming failures.
- `entities/workflow_runner.py` uses `HumanInTheLoop` to pause step execution when a workflow step requires approval.
- `maf_core/control_plane/router.py` guards artifact reads with explicit path validation and returns `404` or `403` when runs or artifacts are invalid.

## Cross-Cutting Concerns

**Logging:** `maf_core/logging.py` configures `structlog` for the active runtime; `maf_core/worker_delegation.py` uses stdlib logging; some compatibility paths still rely on direct console or log-file output.

**Validation:** `maf_core/control_plane/contracts.py` uses Pydantic models for REST payloads, `maf_core/tools.py` validates repo path boundaries, and `maf_core/validation_runner.py` produces the safe local validation ladder.

**Authentication:** `maf_core/control_plane/auth.py` defaults to `NoAuthPolicy` for local development and exposes `AzureFunctionsAuthPolicy` as the cloud-ready seam.

**Approval and Safety:** `maf_core/tools.py::request_human_approval()`, `entities/interrupts.py`, `maf_core/approval_policy.py`, and `maf_core/repo_execution.py` form the active human-in-the-loop and safe-write boundary.

**Legacy Boundary:** `autogen_dashboard/app.py` identifies itself as the legacy compatibility surface, but `command_center/app.py` actively reuses `autogen_dashboard/repo_context.py` for repo discovery and workspace context.

---

*Architecture analysis: 2026-03-26*
