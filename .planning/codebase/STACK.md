# Technology Stack

**Analysis Date:** 2026-03-26

## Languages

**Primary:**
- Python - active runtime, control plane, and tests in `main.py`, `maf_core/*.py`, `command_center/app.py`, `entities/**/*.py`, and `tests/*.py`

**Secondary:**
- JavaScript - operator UI and legacy dashboard UI in `command_center/static/app.js` and `autogen_dashboard/static/app.js`
- HTML/CSS - local UI shells in `command_center/static/index.html`, `command_center/static/styles.css`, `autogen_dashboard/static/index.html`, and `autogen_dashboard/static/styles.css`
- PowerShell - local launcher and stop scripts in `start_ui.ps1`, `stop_ui.ps1`, `start_devui.ps1`, `stop_devui.ps1`, `start_both_uis.ps1`, and `stop_both_uis.ps1`
- JSON/JSONL - durable run and event artifacts under `state/` via `maf_core/control_plane/store.py`

## Runtime

**Environment:**
- Python - repo-local virtualenv workflow described in `README.md`; no interpreter version file is checked in
- Windows/PowerShell-first local development from `README.md` and the repo-root `*.ps1` scripts

**Package Manager:**
- `pip` with `requirements.txt`
- Lockfile: missing

## Frameworks

**Core:**
- `agent-framework==1.0.0rc5` - active agent, workflow, middleware, and checkpoint runtime in `maf_core/agent_factory.py`, `maf_core/provider_fallback.py`, `maf_core/workflow_factory.py`, and `maf_core/team_factory.py`
- `agent-framework-ag-ui==1.0.0b260319` - AG-UI adapter used in `command_center/app.py`
- `agent-framework-devui==1.0.0b260319` - local debugger server used in `maf_core/cli.py` and patched by `maf_core/devui_patches.py`

**Testing:**
- `unittest` (stdlib) - primary test style across `tests/*.py`
- `fastapi.testclient.TestClient` - API testing in `tests/test_command_center.py`, `tests/test_phase6_api_contract.py`, and `tests/test_workspace_contract.py`

**Build/Dev:**
- FastAPI - HTTP hosting for `command_center/app.py` and `autogen_dashboard/app.py`
- `uvicorn` - ASGI server launcher in `maf_core/cli.py` and `autogen_starter/cli.py`
- `structlog>=24.1.0,<25.0.0` - JSON logging configured in `maf_core/logging.py`

## Key Dependencies

**Critical:**
- `pydantic>=2.0,<3.0` and `pydantic-settings>=2.0,<3.0` - settings and API contracts in `maf_core/config.py`, `maf_core/control_plane/contracts.py`, and `autogen_dashboard/schemas.py`
- Gemini OpenAI-compatible client path - `agent_framework.openai.OpenAIChatClient` against `https://generativelanguage.googleapis.com/v1beta/openai/` in `maf_core/agent_factory.py` and `maf_core/provider_fallback.py`
- Repo tool surface - `get_repo_overview`, `list_repo_files`, `read_repo_file`, `search_repo`, `request_human_approval`, and `apply_repo_write_plan` in `maf_core/tools.py`
- Manager-worker delegation - Gemini API manager plus local CLI workers in `maf_core/manager_worker_team_factory.py` and `maf_core/worker_delegation.py`

**Infrastructure:**
- `python-dotenv>=1.0,<2.0` - declared in `requirements.txt`; legacy config reads `.env` directly in `autogen_starter/config.py`, while the active MAF path uses `pydantic-settings` in `maf_core/config.py`
- `FileCheckpointStorage` - workflow checkpoint persistence in `maf_core/workflow_factory.py`
- FastAPI control plane - `/api/v1` router in `maf_core/control_plane/router.py`, mounted by `command_center/app.py`
- Local CLI backends - `gemini.cmd`, `claude`, and `codex.cmd` invoked by `maf_core/provider_fallback.py` and `maf_core/worker_delegation.py`
- `prometheus-fastapi-instrumentator>=6.0.0,<7.0.0` - declared in `requirements.txt`; no runtime usage is detected in the current source tree
- FastAPI, `uvicorn`, and legacy AutoGen packages are imported by `command_center/app.py`, `maf_core/cli.py`, `autogen_dashboard/app.py`, and `autogen_starter/providers.py`, but are not declared in `requirements.txt`

## Configuration

**Environment:**
- Repo-root `.env` is the active config and secret boundary; `.env.example` documents `MAF_*`, `GEMINI_*`, `ANTHROPIC_*`, and CLI override variables
- `maf_core/config.py` is the active MAF settings loader for `MAF_MODEL`, `MAF_BASE_URL`, `GEMINI_API_KEY`, routing, checkpoint, and CLI fallback settings
- `autogen_starter/config.py` keeps a separate legacy config surface for `AUTOGEN_*`, `OLLAMA_*`, `OPENAI_*`, and `AZURE_OPENAI_*`

**Build:**
- `requirements.txt` - only checked-in Python dependency manifest
- `README.md` - local setup, runtime commands, API surface, and fallback guidance
- `docs/DEVUI_CUSTOMIZATION.md` - DevUI override and patch guidance
- No `pyproject.toml`, `poetry.lock`, `uv.lock`, or `package.json` is detected at the repo root

## Platform Requirements

**Development:**
- Local git installation is required for repo discovery and workspace metadata in `maf_core/tools.py` and `autogen_dashboard/repo_context.py`
- Writable `state/` directories are required for checkpoints and durable run artifacts in `maf_core/workflow_factory.py`, `maf_core/control_plane/store.py`, and `command_center/app.py`
- Installed AI backends depend on the selected route: `GEMINI_API_KEY` for the primary MAF path, optional `ANTHROPIC_API_KEY`, and optional local `gemini.cmd`, `claude`, and `codex.cmd`
- The primary operator surface is `python main.py ui`, with the raw debugger on `python main.py devui`, both dispatched from `maf_core/cli.py`

**Production:**
- Not detected. `maf_core/control_plane/auth.py` contains an Azure Functions auth stub, but no deployment manifests or CI/CD pipeline files are present

---

*Stack analysis: 2026-03-26*
