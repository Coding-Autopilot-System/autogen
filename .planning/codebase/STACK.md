# Technology Stack

## Languages
- Python 3.14-era runtime code lives in `main.py`, `maf_starter/*.py`, `command_center/*.py`, `autogen_dashboard/*.py`, `autogen_starter/*.py`, and `entities/**/*.py`.
- JavaScript UI code lives in `command_center/static/app.js` and `autogen_dashboard/static/app.js`.
- HTML and CSS shells live in `command_center/static/index.html`, `command_center/static/styles.css`, `autogen_dashboard/static/index.html`, and `autogen_dashboard/static/styles.css`.
- PowerShell launchers live in `start_devui.ps1` and `stop_devui.ps1`.
- JSON and JSONL are the main persistence formats under `state/` and the legacy dashboard store.

## Runtime Surfaces
- `main.py` is a thin dispatcher into `maf_starter/cli.py`.
- `maf_starter/cli.py` provides `doctor`, `smoke`, `probe-models`, `ui`, and `devui`.
- `autogen_starter/cli.py` still exposes `providers`, `chat`, `step`, `dashboard`, and `reset-state`.
- `command_center/app.py` serves the AG-UI operator surface on top of FastAPI.
- `autogen_dashboard/app.py` remains the legacy FastAPI dashboard and SSE API.

## Frameworks
- Microsoft Agent Framework is the active runtime via `agent_framework`, `agent_framework_devui`, and `agent_framework_ag_ui`.
- FastAPI and Uvicorn host both the command center and the legacy dashboard.
- AutoGen packages are still used by the legacy path through `autogen_core`, `autogen_agentchat`, and `autogen_ext`.
- Pydantic backs the dashboard schemas in `autogen_dashboard/schemas.py`.

## Dependencies
- Root pinned deps are `agent-framework==1.0.0rc5`, `agent-framework-ag-ui==1.0.0b260319`, `agent-framework-devui==1.0.0b260319`, and `python-dotenv`.
- `maf_starter/agent_factory.py` uses `OpenAIChatClient` against Gemini's OpenAI-compatible endpoint.
- `maf_starter/provider_fallback.py` optionally imports `AnthropicClient` and shells out to `gemini.cmd`, `claude`, and `codex.cmd`.
- `autogen_starter/providers.py` also supports `ollama`, `openai`, `gemini`, `anthropic`, `azure-openai`, `codex-cli`, `gemini-cli`, and `claude-cli`.
- Tests depend on `unittest` and `fastapi.testclient.TestClient`.

## Configuration Surface
- Repo-root `.env` is loaded by `maf_starter/config.py` and `autogen_starter/config.py`.
- `.env.example` documents `MAF_*`, `GEMINI_*`, `ANTHROPIC_*`, `AUTOGEN_*`, and CLI override variables.
- `MAF_REPO_ROOT`, `MAF_ENTITIES_DIR`, and `MAF_CHECKPOINT_DIR` drive the active MAF runtime layout.
- `AUTOGEN_STATE_DIR`, `AUTOGEN_STATE_FILE`, and `AUTOGEN_REPO_SCAN_ROOT` drive the legacy dashboard.
- `CLAUDE_CODE_GIT_BASH_PATH` is required for the Claude CLI path to be considered ready.
- `state/`, `.venv/`, and `.tmp-tests/` are treated as local-only workspace state.

## Entry Points
- `main.py` forwards to `maf_starter/cli.main()`.
- `autogen_starter/cli.py` is the legacy AutoGen CLI and dashboard launcher.
- `command_center/app.py` exposes `/api/agui/*`, `/api/catalog`, `/api/repos`, `/api/status`, and `/healthz`.
- `autogen_dashboard/app.py` exposes the legacy `/api/sessions/*` and `/api/providers` surface.
- `entities/repo_copilot*/agent.py` and `entities/repo_copilot_workflow/workflow.py` expose DevUI-discoverable agents and workflows.
- `entities/repo_team/workflow.py` exposes the manager-led specialist workflow.

## Local Scripts and UI
- `start_devui.ps1` starts the local DevUI debugger; `stop_devui.ps1` stops it.
- `command_center/static/*` is the primary operator UI, with a debug link to `127.0.0.1:8090`.
- `autogen_dashboard/static/*` is the retained legacy UI.
- `docs/DEVUI_CUSTOMIZATION.md` documents the DevUI overlay and bundle patching approach.
- `README.md` describes the command center, DevUI, and model probe flow.

## Testing and Runtime Packages
- `tests/*.py` uses `unittest`, including async `IsolatedAsyncioTestCase` coverage.
- Several tests use `fastapi.testclient` to exercise the command center and legacy dashboard APIs.
- `agent_framework`, `agent_framework_devui`, and `agent_framework_ag_ui` are the core runtime packages under test.
- `uvicorn` is the local server runner for both UI surfaces.
- `state/maf-checkpoints` and `state/sessions/*` are part of runtime verification.
