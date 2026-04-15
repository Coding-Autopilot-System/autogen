# External Integrations

**Analysis Date:** 2026-03-26

## APIs & External Services

**Model APIs:**
- Gemini API - primary model endpoint for the active MAF runtime in `maf_core/agent_factory.py` and `maf_core/provider_fallback.py`
  - SDK/Client: `agent_framework.openai.OpenAIChatClient`
  - Auth: `GEMINI_API_KEY`
- Anthropic API - optional API fallback when quota or rate-limit failures occur in `maf_core/provider_fallback.py`
  - SDK/Client: `agent_framework_anthropic.AnthropicClient`
  - Auth: `ANTHROPIC_API_KEY`

**Local AI Tooling:**
- Gemini CLI - local fallback provider and manager-worker delegate in `maf_core/provider_fallback.py` and `maf_core/worker_delegation.py`
  - SDK/Client: subprocess execution of `GEMINI_CLI_COMMAND`
  - Auth: CLI-managed local session
- Claude CLI - local fallback provider and manager-worker delegate in `maf_core/provider_fallback.py`, `maf_core/worker_delegation.py`, and `maf_core/manager_worker_team_factory.py`
  - SDK/Client: subprocess execution of `CLAUDE_CLI_COMMAND`
  - Auth: CLI-managed local session plus `CLAUDE_CODE_GIT_BASH_PATH`
- Codex CLI - local fallback provider and manager-worker delegate in `maf_core/provider_fallback.py` and `maf_core/worker_delegation.py`
  - SDK/Client: subprocess execution of `CODEX_CLI_COMMAND`
  - Auth: CLI-managed local session

**Programmatic Interfaces:**
- AG-UI streaming endpoints - interactive chat protocol exposed by `command_center/app.py`
  - SDK/Client: `agent_framework_ag_ui` and `ag_ui`
  - Auth: local default is unauthenticated; see `maf_core/control_plane/auth.py`
- Control-plane REST API - run lifecycle, routing, artifact, and operator-action endpoints under `/api/v1` in `maf_core/control_plane/router.py`
  - SDK/Client: FastAPI router mounted by `command_center/app.py`
  - Auth: `AUTH_POLICY` selects `none` or `azure-functions`; only `NoAuthPolicy` is implemented

**Local Workspace Integration:**
- Git-backed repo discovery and workspace metadata - local repo selection, branch state, recent commits, and stack hints in `autogen_dashboard/repo_context.py` and `maf_core/tools.py`
  - SDK/Client: subprocess `git` calls
  - Auth: local git installation only

**Legacy Provider Surface:**
- Ollama, Azure OpenAI, and legacy AutoGen provider wiring remain in `autogen_starter/providers.py` for the older runtime path
  - SDK/Client: `autogen_ext` model clients and CLI clients from `autogen_starter/cli_clients.py`
  - Auth: `OLLAMA_*`, `AZURE_OPENAI_*`, and related variables from `autogen_starter/config.py`

## Data Storage

**Databases:**
- None
  - Connection: Not applicable
  - Client: Not applicable

**File Storage:**
- Local filesystem only
  - Active workflow checkpoints: `state/maf-checkpoints` via `maf_core/workflow_factory.py`
  - Repo-scoped checkpoint buckets: `state/maf-checkpoints/repos/<repo>-<hash>` via `command_center/app.py`
  - Durable control-plane runs and artifacts: `state/sessions/<run_id>` via `maf_core/control_plane/store.py`
  - Legacy dashboard state: `state/sessions/<session_id>` and `state/team_state.json` via `autogen_dashboard/session_store.py` and `autogen_starter/cli.py`

**Caching:**
- None detected

## Authentication & Identity

**Auth Provider:**
- Local no-auth policy by default
  - Implementation: `NoAuthPolicy` in `maf_core/control_plane/auth.py`
- Future Azure Functions auth hook
  - Implementation: `AzureFunctionsAuthPolicy` stub in `maf_core/control_plane/auth.py`

## Monitoring & Observability

**Error Tracking:**
- None detected

**Logs:**
- Structured JSON logs via `structlog` in `maf_core/logging.py`
- Repo-root runtime log files such as `.command-center.out.log`, `.command-center.err.log`, `.maf-devui.out.log`, and `.maf-devui.err.log`
- `prometheus-fastapi-instrumentator` is declared in `requirements.txt`, but no instrumentation wiring is present in the current source tree

## CI/CD & Deployment

**Hosting:**
- Local Uvicorn/FastAPI only from `maf_core/cli.py` and `autogen_starter/cli.py`

**CI Pipeline:**
- None detected

## Environment Configuration

**Required env vars:**
- `GEMINI_API_KEY` for the active Gemini API path in `maf_core/config.py`
- `MAF_MODEL`, `MAF_BASE_URL`, `MAF_REPO_ROOT`, `MAF_ENTITIES_DIR`, `MAF_CHECKPOINT_DIR`, `MAF_ROUTE_LANE`, `MAF_REQUESTED_PROVIDER`, `MAF_REQUESTED_MODEL`, `MAF_FALLBACK_CHAIN`, and `MAF_MODEL_CANDIDATES` in `maf_core/config.py`
- `GEMINI_CLI_COMMAND`, `GEMINI_CLI_MODEL`, `CLAUDE_CLI_COMMAND`, `CLAUDE_CLI_MODEL`, `CLAUDE_CODE_GIT_BASH_PATH`, `CODEX_CLI_COMMAND`, and `CODEX_CLI_MODEL` for local worker and fallback execution in `maf_core/config.py`
- `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` for the optional Anthropic API path in `maf_core/config.py`
- `AUTH_POLICY` for control-plane auth mode in `maf_core/control_plane/auth.py`
- Legacy-only variables in `autogen_starter/config.py`: `AUTOGEN_PROVIDER`, `AUTOGEN_STATE_DIR`, `AUTOGEN_STATE_FILE`, `AUTOGEN_REPO_SCAN_ROOT`, `OLLAMA_*`, `OPENAI_*`, and `AZURE_OPENAI_*`

**Secrets location:**
- Repo-root `.env` is present and ignored by git; `.env.example` documents the non-secret shape
- CLI providers rely on local installed-tool sessions outside the repo in addition to env vars

## Webhooks & Callbacks

**Incoming:**
- None detected. External automation integrates through HTTP endpoints in `command_center/app.py` and `maf_core/control_plane/router.py`, not webhook handlers

**Outgoing:**
- No webhook callbacks detected
- Outbound network calls are limited to Gemini and optional Anthropic API requests from `maf_core/agent_factory.py` and `maf_core/provider_fallback.py`

---

*Integration audit: 2026-03-26*
