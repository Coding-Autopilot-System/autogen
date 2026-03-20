Refer to %USERPROFILE%\.codex\AGENTS.md for the active global instructions.

<!-- GSD:project-start source:PROJECT.md -->
## Project

**GSD Orchestration Platform**

This project is a local-first multi-agent orchestration platform for software development, built around Microsoft Agent Framework, GSD workflows, and your installed AI backends. Its job is to let you open the UI, choose a repo, type one engineering prompt, and have a manager agent coordinate planning, specialist execution, code edits, validation, traces, and final output with minimal manual back-and-forth.

The primary user is you as the operator and developer. The current codebase already provides a repo-aware MAF runtime, DevUI integration, routing and fallback logic, and a retained legacy AutoGen dashboard path; this project evolves that into a more polished, autonomous, professional engineering workbench.

**Core Value:** You can give one prompt and watch a trustworthy multi-agent coding system drive real repo work end-to-end with clear traces, specialist visibility, and minimal manual intervention.

### Constraints

- **Tech stack**: Extend the current Python and Microsoft Agent Framework codebase rather than rewriting into a different platform - preserves working runtime primitives and existing investment
- **Runtime**: Must work well on the local Windows machine with installed CLI tools and local virtualenv workflows - this is the primary execution environment
- **Autonomy**: Default behavior should favor automatic code editing and local validation once a prompt is given - manual approval should be the exception, not the baseline
- **Cost**: Prefer Gemini API and available local CLI tools before introducing additional paid API dependencies - keeps experimentation affordable
- **UX**: The UI must look professional and readable, not like an internal demo shell - this is a productized operator workbench, not only a developer test harness
- **Future deployment**: Design the orchestration core so Azure Function or REST exposure can be added later without re-architecting the whole runtime - local-first now, cloud-ready later
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Python 3.14-era codebase targeting a repo-local virtual environment in `.venv/`; all active runtime code lives in `main.py`, `maf_starter/*.py`, `entities/**/*.py`, and supporting test modules under `tests/`.
- JavaScript - legacy dashboard UI logic in `autogen_dashboard/static/app.js`
- HTML/CSS - legacy dashboard shell in `autogen_dashboard/static/index.html` and `autogen_dashboard/static/styles.css`
- PowerShell - local launcher and stop scripts in `start_devui.ps1` and `stop_devui.ps1`
## Runtime
- Python CLI application with local web UI/dev server behavior
- Windows/PowerShell-first developer workflow, as shown in `README.md`, `start_devui.ps1`, and `stop_devui.ps1`
- Uvicorn-based HTTP serving for DevUI and the legacy FastAPI dashboard
- `pip` via a repo-local virtual environment at `.venv/`
- Lockfile: none present
## Frameworks
- Microsoft Agent Framework `agent-framework==1.0.0rc5` - active agent runtime declared in `requirements.txt`
- Microsoft DevUI `agent-framework-devui==1.0.0b260319` - local debugging UI, also declared in `requirements.txt`
- FastAPI/Uvicorn - used by the legacy dashboard in `autogen_dashboard/app.py` and by DevUI customization hooks in `maf_starter/devui_overrides.py`
- `agent_framework_orchestrations.SequentialBuilder` in `maf_starter/team_factory.py`
- File checkpointing via `FileCheckpointStorage` in `maf_starter/team_factory.py` and `maf_starter/workflow_factory.py`
- AutoGen AgentChat code in `autogen_starter/*.py` and `autogen_dashboard/*.py`
- Pydantic-backed session schemas in `autogen_dashboard/schemas.py`
## Key Dependencies
- `agent_framework` - core agent and workflow primitives used in `maf_starter/agent_factory.py`, `maf_starter/tools.py`, and `maf_starter/workflow_factory.py`
- `agent_framework_devui` - DevUI server and discovery path used in `maf_starter/cli.py`
- `python-dotenv` - `.env` loading in `maf_starter/config.py`
- `OpenAIChatClient` - Gemini API path via Google's OpenAI-compatible endpoint in `maf_starter/agent_factory.py` and `maf_starter/provider_fallback.py`
- `AnthropicClient` - optional API fallback path in `maf_starter/provider_fallback.py`
- `uvicorn` - local HTTP serving in `maf_starter/cli.py` and `autogen_starter/cli.py`
- `fastapi` - legacy dashboard backend in `autogen_dashboard/app.py`
- local CLI executables `gemini.cmd`, `claude`, and `codex.cmd` invoked by `maf_starter/provider_fallback.py`
## Configuration
- `.env` at the repo root is the active configuration boundary
- `.env.example` documents `MAF_*`, `GEMINI_*`, optional `ANTHROPIC_*`, and CLI command settings
- `.gitignore` excludes `.env`, `.venv/`, `state/`, and `__pycache__/`
- `main.py` - top-level entrypoint
- `requirements.txt` - root dependency manifest
- `README.md` - operational usage and model/fallback guidance
- `docs/DEVUI_CUSTOMIZATION.md` - repo-specific DevUI patching guidance
## Platform Requirements
- Windows PowerShell workflow is the documented default
- Writable `state/` directory for checkpoints, transcripts, and session artifacts
- Installed AI backends for the selected path: Gemini API for primary use, optional Anthropic API, and optional CLI tools for fallback
- No production deployment packaging is defined in this repo
- This repository is oriented around local agent development and local DevUI debugging rather than packaged service deployment
## Notes
- The current active path is MAF-first: `main.py` delegates into `maf_starter/cli.py`.
- Legacy AutoGen code remains in-tree and still imports additional packages that are not declared in `requirements.txt`, so a clean environment relies on more than the root manifest alone.
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Naming Patterns
- `snake_case.py` for Python modules across `maf_starter/`, `autogen_starter/`, and `autogen_dashboard/`
- `agent.py` and `workflow.py` are reserved as entity entry files under `entities/`
- `*_factory.py`, `*_policy.py`, `*_types.py` name modules by responsibility rather than feature marketing language
- `snake_case` for functions and helper methods
- async functions do not use a special naming prefix
- builders are named literally: `build_agent`, `build_workflow`, `build_repo_team`
- `snake_case` for local variables and parameters
- module-level constants are `UPPER_SNAKE_CASE`, for example `DEFAULT_MODEL`, `DEFAULT_SMOKE_MESSAGE`, and `FALLBACK_NOTICE`
- `PascalCase` for dataclasses and schema types such as `Settings`, `RoutingPlan`, `RunOutcome`, and `SessionDetail`
- no `I` prefix for interfaces or types
## Code Style
- typed Python with `from __future__ import annotations` used broadly in the active path
- imports grouped stdlib, third-party, then local packages
- explicit `Path`, dataclass, and union type usage rather than loose dictionaries where possible
- no checked-in formatter config was present
- no repo-level lint config (`pyproject.toml`, `ruff.toml`, `setup.cfg`, `tox.ini`, `noxfile.py`) was present
- style is enforced mainly by consistency and local validation commands
## Import Organization
- blank line separation between import groups is used consistently
- absolute package imports are preferred over deep relative imports
- none detected; Python package imports use actual package names like `maf_starter.*` and `autogen_dashboard.*`
## Error Handling
- raise explicit exceptions at the point of failure
- catch and translate at boundaries rather than swallowing errors
- fallback behavior is opt-in and centralized in `maf_starter/provider_fallback.py`
- `ValueError` for config and path validation issues
- `RuntimeError` for provider and subprocess failures
- `HTTPException` boundary translation in `autogen_dashboard/app.py`
- custom provider configuration errors exist in the legacy AutoGen path
## Logging
- no structured logging framework detected
- `print(...)` and log files are used for CLI/runtime visibility
- status output is emitted mainly from command entrypoints
- runtime logs are captured into `.maf-devui.*.log` and `.dashboard.*.log`
- deeper modules prefer raising errors with context instead of logging internally
## Comments
- comments are sparse and mostly avoided when naming is clear
- docstrings are used for repo tools in `maf_starter/tools.py`
- `# pragma: no cover` appears only where necessary in tests and small CLI seams
- no dominant TODO convention was evident in the scanned source
## Function Design
- most active MAF modules are small and focused
- the main exception is the legacy `autogen_dashboard/session_runner.py`, which is substantially larger and more stateful
- explicit parameters are preferred over freeform dictionaries
- settings objects and dataclasses are used to avoid passing large option lists repeatedly
- explicit returns and guard clauses are common
- factories return ready-to-use agents and workflows rather than partially configured components
## Module Design
- modules usually export a small set of focused functions and classes
- `__init__.py` files under `entities/` expose one discovery object for DevUI
- `main.py` acts as the root dispatcher
- entity packages keep entry files thin and push logic into shared starter modules
## Practical Rule For New Work
- Put new shared MAF behavior in `maf_starter/`
- Keep entity files thin wrappers around factories
- Treat `autogen_dashboard/` and `autogen_starter/` as legacy paths unless intentionally maintaining them
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Thin bootstrap entrypoint in `main.py`
- Environment-driven assembly from `maf_starter/config.py`
- Entity/workflow discovery through the `entities/` tree
- Fallback across API models and local CLI providers
- Local-only DevUI customization via runtime monkey patches and bundle rewriting
## Layers
- Purpose: start commands and dispatch into the active runtime
- Contains: `main.py`, `maf_starter/cli.py`, `start_devui.ps1`, `stop_devui.ps1`
- Depends on: config loading and runtime factories
- Used by: human operators running the repo locally
- Purpose: resolve paths, API keys, model defaults, fallback chains, and repo roots
- Contains: `maf_starter/config.py`
- Depends on: `.env` and `.env.example`
- Used by: every active MAF entrypoint and factory
- Purpose: build agents, workflows, and team orchestrations
- Contains: `maf_starter/agent_factory.py`, `maf_starter/workflow_factory.py`, `maf_starter/team_factory.py`
- Depends on: config, tools, routing, and fallback middleware
- Used by: DevUI-discovered entities and smoke/doctor/probe flows
- Purpose: route prompts, retry providers, expose repo tools, and shape DevUI output
- Contains: `maf_starter/routing_policy.py`, `maf_starter/provider_fallback.py`, `maf_starter/tools.py`, `maf_starter/devui_patches.py`, `maf_starter/devui_overrides.py`
- Depends on: Agent Framework clients, subprocess CLIs, repo filesystem
- Used by: active MAF agent and workflow executions
- Purpose: expose concrete agents and workflows to DevUI directory discovery
- Contains: `entities/repo_copilot/*`, `entities/repo_copilot_auto/*`, `entities/repo_copilot_pro/*`, `entities/repo_copilot_flash/*`, `entities/repo_copilot_flash_lite/*`, `entities/repo_copilot_workflow/*`, `entities/repo_team/*`
- Depends on: starter factories
- Used by: DevUI entity selection
- Purpose: preserve the older AutoGen dashboard and provider/session architecture
- Contains: `autogen_starter/*.py`, `autogen_dashboard/*.py`
- Depends on: AutoGen packages, FastAPI, Pydantic, file-backed session state
- Used by: legacy manual flows only
## Data Flow
- Active MAF state is file-based under `state/maf-checkpoints`
- Legacy AutoGen state is file-based under `state/team_state.json` and `state/sessions/*`
## Key Abstractions
- Purpose: centralize agent and workflow construction
- Examples: `maf_starter/agent_factory.py`, `maf_starter/team_factory.py`, `maf_starter/workflow_factory.py`
- Pattern: pure builder functions with config injection
- Purpose: classify a user turn and decide provider/model order
- Examples: `RoutingPlan` in `maf_starter/routing_policy.py`
- Pattern: small immutable planning object with primary and fallback steps
- Purpose: constrain agent access to local repo files through explicit tools
- Examples: `get_repo_overview`, `list_repo_files`, `read_repo_file`, `search_repo`, `request_human_approval` in `maf_starter/tools.py`
- Pattern: tool-wrapped boundary APIs over the filesystem
## Entry Points
- Location: `main.py`
- Triggers: `python main.py doctor|smoke|probe-models|devui`
- Responsibilities: delegate to the active MAF CLI
- Location: `start_devui.ps1`
- Triggers: local PowerShell invocation
- Responsibilities: start `python main.py devui` and capture logs
- Location: `autogen_starter/cli.py`
- Triggers: legacy `dashboard` command path
- Responsibilities: launch `autogen_dashboard.app`
## Error Handling
- Config errors raise `ValueError` in `maf_starter/config.py`
- Provider fallback retries only on heuristic quota and rate-limit errors in `maf_starter/provider_fallback.py`
- Legacy FastAPI endpoints translate `ValueError`, `KeyError`, and `ProviderConfigError` into HTTP errors in `autogen_dashboard/app.py`
## Cross-Cutting Concerns
- Mostly `print(...)` and local log files rather than a structured logging framework
- Path and repo-root safety checks in `maf_starter/tools.py`
- Session and request schema validation in the legacy dashboard layer
- Implemented as a mandatory-approval tool in the active MAF path
- Implemented as explicit session actions in the legacy dashboard path
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
