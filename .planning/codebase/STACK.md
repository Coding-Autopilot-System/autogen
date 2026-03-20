# Technology Stack

**Analysis Date:** 2026-03-20

## Languages

**Primary:**
- Python 3.14-era codebase targeting a repo-local virtual environment in `.venv/`; all active runtime code lives in `main.py`, `maf_starter/*.py`, `entities/**/*.py`, and supporting test modules under `tests/`.

**Secondary:**
- JavaScript - legacy dashboard UI logic in `autogen_dashboard/static/app.js`
- HTML/CSS - legacy dashboard shell in `autogen_dashboard/static/index.html` and `autogen_dashboard/static/styles.css`
- PowerShell - local launcher and stop scripts in `start_devui.ps1` and `stop_devui.ps1`

## Runtime

**Environment:**
- Python CLI application with local web UI/dev server behavior
- Windows/PowerShell-first developer workflow, as shown in `README.md`, `start_devui.ps1`, and `stop_devui.ps1`
- Uvicorn-based HTTP serving for DevUI and the legacy FastAPI dashboard

**Package Manager:**
- `pip` via a repo-local virtual environment at `.venv/`
- Lockfile: none present

## Frameworks

**Core:**
- Microsoft Agent Framework `agent-framework==1.0.0rc5` - active agent runtime declared in `requirements.txt`
- Microsoft DevUI `agent-framework-devui==1.0.0b260319` - local debugging UI, also declared in `requirements.txt`
- FastAPI/Uvicorn - used by the legacy dashboard in `autogen_dashboard/app.py` and by DevUI customization hooks in `maf_starter/devui_overrides.py`

**Workflow/Orchestration:**
- `agent_framework_orchestrations.SequentialBuilder` in `maf_starter/team_factory.py`
- File checkpointing via `FileCheckpointStorage` in `maf_starter/team_factory.py` and `maf_starter/workflow_factory.py`

**Legacy Stack Still Present:**
- AutoGen AgentChat code in `autogen_starter/*.py` and `autogen_dashboard/*.py`
- Pydantic-backed session schemas in `autogen_dashboard/schemas.py`

## Key Dependencies

**Critical:**
- `agent_framework` - core agent and workflow primitives used in `maf_starter/agent_factory.py`, `maf_starter/tools.py`, and `maf_starter/workflow_factory.py`
- `agent_framework_devui` - DevUI server and discovery path used in `maf_starter/cli.py`
- `python-dotenv` - `.env` loading in `maf_starter/config.py`
- `OpenAIChatClient` - Gemini API path via Google's OpenAI-compatible endpoint in `maf_starter/agent_factory.py` and `maf_starter/provider_fallback.py`
- `AnthropicClient` - optional API fallback path in `maf_starter/provider_fallback.py`

**Infrastructure:**
- `uvicorn` - local HTTP serving in `maf_starter/cli.py` and `autogen_starter/cli.py`
- `fastapi` - legacy dashboard backend in `autogen_dashboard/app.py`
- local CLI executables `gemini.cmd`, `claude`, and `codex.cmd` invoked by `maf_starter/provider_fallback.py`

## Configuration

**Environment:**
- `.env` at the repo root is the active configuration boundary
- `.env.example` documents `MAF_*`, `GEMINI_*`, optional `ANTHROPIC_*`, and CLI command settings
- `.gitignore` excludes `.env`, `.venv/`, `state/`, and `__pycache__/`

**Build/Runtime Files:**
- `main.py` - top-level entrypoint
- `requirements.txt` - root dependency manifest
- `README.md` - operational usage and model/fallback guidance
- `docs/DEVUI_CUSTOMIZATION.md` - repo-specific DevUI patching guidance

## Platform Requirements

**Development:**
- Windows PowerShell workflow is the documented default
- Writable `state/` directory for checkpoints, transcripts, and session artifacts
- Installed AI backends for the selected path: Gemini API for primary use, optional Anthropic API, and optional CLI tools for fallback

**Production/Deployment:**
- No production deployment packaging is defined in this repo
- This repository is oriented around local agent development and local DevUI debugging rather than packaged service deployment

## Notes

- The current active path is MAF-first: `main.py` delegates into `maf_starter/cli.py`.
- Legacy AutoGen code remains in-tree and still imports additional packages that are not declared in `requirements.txt`, so a clean environment relies on more than the root manifest alone.

---

*Stack analysis: 2026-03-20*
*Update after major dependency or runtime changes*
