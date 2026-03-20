# Codebase Structure

**Analysis Date:** 2026-03-20

## Directory Layout

```text
autogen/
├── .planning/              # GSD planning artifacts, including this codebase map
│   └── codebase/           # Codebase reference docs
├── .venv/                  # Repo-local virtual environment
├── autogen_dashboard/      # Legacy FastAPI dashboard backend and static UI
│   └── static/             # Legacy browser assets
├── autogen_starter/        # Legacy AutoGen CLI and provider wiring
├── docs/                   # Repo-specific developer documentation
├── entities/               # DevUI-discoverable MAF agents and workflows
├── maf_starter/            # Active MAF runtime, routing, fallback, tools, and UI patching
├── state/                  # Checkpoints, sessions, and runtime artifacts
├── tests/                  # Checked-in automated tests
├── main.py                 # Top-level Python entrypoint
├── README.md               # Main operator and developer guide
├── requirements.txt        # Root dependency manifest
├── start_devui.ps1         # Start local DevUI
└── stop_devui.ps1          # Stop local DevUI
```

## Directory Purposes

**maf_starter/**
- Purpose: active MAF implementation
- Contains: CLI, config, agent/workflow factories, routing, provider fallback, tool definitions, and DevUI customization logic
- Key files: `cli.py`, `config.py`, `agent_factory.py`, `provider_fallback.py`, `routing_policy.py`, `tools.py`, `team_factory.py`
- Subdirectories: none; flat module package

**entities/**
- Purpose: DevUI discovery surface for concrete agent and workflow variants
- Contains: one directory per agent/workflow
- Key files: `repo_copilot/agent.py`, `repo_copilot_auto/agent.py`, `repo_copilot_workflow/workflow.py`, `repo_team/workflow.py`
- Subdirectories: model-pinned variants and workflow wrappers

**autogen_dashboard/**
- Purpose: legacy local HITL dashboard implementation
- Contains: FastAPI app, session/state logic, repo context helpers, schemas, and static frontend assets
- Key files: `app.py`, `session_runner.py`, `session_store.py`, `static/app.js`
- Subdirectories: `static/` for browser UI assets

**autogen_starter/**
- Purpose: legacy AutoGen provider and CLI orchestration path
- Contains: old config, CLI client wrappers, provider readiness and creation logic
- Key files: `cli.py`, `cli_clients.py`, `config.py`, `providers.py`
- Subdirectories: none

**state/**
- Purpose: runtime persistence
- Contains: MAF checkpoints, legacy AutoGen team state, and per-session JSON/JSONL artifacts
- Key files: `team_state.json`, `sessions/*`, `maf-checkpoints/*`
- Subdirectories: `sessions/` for legacy dashboard state

**tests/**
- Purpose: automated verification
- Contains: `test_maf_setup.py` plus stale compiled artifacts in `__pycache__/`
- Key files: `test_maf_setup.py`
- Subdirectories: `__pycache__/`

**docs/**
- Purpose: extra developer and operator guidance
- Contains: customization notes for the DevUI patch path
- Key files: `DEVUI_CUSTOMIZATION.md`
- Subdirectories: none

## Key File Locations

**Entry Points:**
- `main.py` - primary runtime entrypoint
- `start_devui.ps1` - local DevUI launcher
- `stop_devui.ps1` - local DevUI stop helper

**Configuration:**
- `.env` - live local config (gitignored)
- `.env.example` - environment template
- `requirements.txt` - root dependencies
- `.gitignore` - ignored local and runtime artifacts

**Core Logic:**
- `maf_starter/agent_factory.py` - active agent assembly
- `maf_starter/provider_fallback.py` - provider and model retry chain
- `maf_starter/routing_policy.py` - prompt tier classification and chain selection
- `maf_starter/tools.py` - repo inspection and HITL tool boundary
- `maf_starter/team_factory.py` - sequential multi-agent workflow

**Testing:**
- `tests/test_maf_setup.py` - current source test suite

**Documentation:**
- `README.md` - current operating guide
- `docs/DEVUI_CUSTOMIZATION.md` - DevUI patching notes

## Naming Conventions

**Files:**
- `snake_case.py` for Python modules
- `agent.py` or `workflow.py` for entity entry files
- `*_factory.py`, `*_policy.py`, `*_types.py` for role-specific MAF modules

**Directories:**
- `snake_case` for Python package directories
- one entity per directory under `entities/`

**Special Patterns:**
- `__init__.py` re-exports discovery objects for DevUI
- `state/sessions/<id>/` stores stable JSON artifact names
- root `snippet_*.txt` files are ad hoc local helper artifacts, not core runtime structure

## Where to Add New Code

**New MAF Agent Variant:**
- Implementation: `entities/<entity_name>/agent.py`
- Shared behavior: `maf_starter/agent_factory.py` or related helpers
- Tests: `tests/`

**New MAF Workflow:**
- Implementation: `entities/<workflow_name>/workflow.py`
- Shared builder logic: `maf_starter/workflow_factory.py` or `maf_starter/team_factory.py`
- Checkpoint behavior: `state/maf-checkpoints`

**New Repo Tool or Routing Logic:**
- Implementation: `maf_starter/tools.py` or `maf_starter/routing_policy.py`
- Fallback/runtime behavior: `maf_starter/provider_fallback.py`

**Legacy Dashboard Changes:**
- Backend/API: `autogen_dashboard/*.py`
- Frontend: `autogen_dashboard/static/*`
- Provider/session support: `autogen_starter/*.py`

## Special Directories

**.planning/**
- Purpose: GSD planning and codebase-map artifacts
- Source: local workflow output
- Committed: intended to be committed once git is initialized

**state/**
- Purpose: generated runtime artifacts and checkpoints
- Source: local application execution
- Committed: no; ignored by `.gitignore`

**.venv/**
- Purpose: local Python environment
- Source: developer-created virtual environment
- Committed: no; ignored by `.gitignore`

---

*Structure analysis: 2026-03-20*
*Update when directory structure changes*
