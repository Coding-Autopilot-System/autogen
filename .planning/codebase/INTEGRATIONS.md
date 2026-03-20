# External Integrations

**Analysis Date:** 2026-03-20

## APIs & External Services

**Primary Model Provider:**
- Google Gemini API - primary model execution path for the MAF runtime
  - SDK/Client: `OpenAIChatClient` in `maf_starter/agent_factory.py` and `maf_starter/provider_fallback.py`
  - Auth: `GEMINI_API_KEY` / `MAF_API_KEY` from `.env`
  - Endpoint: `GEMINI_BASE_URL` / `MAF_BASE_URL`, defaulting to Google's OpenAI-compatible endpoint in `maf_starter/config.py`

**Optional Secondary API Provider:**
- Anthropic API - optional fallback when `ANTHROPIC_API_KEY` is configured
  - SDK/Client: `AnthropicClient` in `maf_starter/provider_fallback.py`
  - Auth: `ANTHROPIC_API_KEY`
  - Model config: `ANTHROPIC_MODEL` in `.env.example`

**CLI AI Providers:**
- Gemini CLI - fallback subprocess path in `maf_starter/provider_fallback.py`
  - Command: `gemini.cmd`
  - Auth: the CLI's local cached login session
  - Notes: tool calling is unavailable on CLI fallback turns
- Claude CLI - fallback subprocess path in `maf_starter/provider_fallback.py`
  - Command: `claude`
  - Auth: local CLI/app account session
  - Extra config: optional `CLAUDE_CODE_GIT_BASH_PATH`
- Codex CLI - fallback subprocess path in `maf_starter/provider_fallback.py`
  - Command: `codex.cmd`
  - Auth: local Codex login/session

## Data Storage

**Workflow State:**
- File-based checkpoint storage under `state/maf-checkpoints`
  - Used by `maf_starter/workflow_factory.py` and `maf_starter/team_factory.py`

**Legacy Session State:**
- `state/team_state.json`
- `state/sessions/*/metadata.json`
- `state/sessions/*/transcript.json`
- `state/sessions/*/events.jsonl`
- `state/sessions/*/autogen_state.json`

**Caching:**
- No dedicated cache service is integrated
- State and artifacts are file-backed only

## Authentication & Identity

**Provider Identity:**
- Gemini API auth is key-based via `.env`
- Anthropic API auth is optional and key-based via `.env`
- CLI providers rely on local workstation login state rather than API keys

**Human Approval:**
- `request_human_approval` in `maf_starter/tools.py` is the current human-in-the-loop control surface for MAF turns
- It is implemented as a mandatory-approval tool rather than a separate identity system

## Monitoring & Observability

**Logs:**
- `.maf-devui.out.log` and `.maf-devui.err.log` capture DevUI runtime output
- `.dashboard.out.log` and `.dashboard.err.log` capture the legacy dashboard server output
- No external logging or metrics service is integrated

**Tracing/UI Metadata:**
- DevUI route metadata is patched in `maf_starter/devui_patches.py`
- UI styling/renderer overrides are injected by `maf_starter/devui_overrides.py`

## CI/CD & Deployment

**Hosting:**
- No production hosting target is declared in this repo
- Active usage is local execution through `python main.py ...` and `start_devui.ps1`

**CI Pipeline:**
- No checked-in CI workflow files were present in the scanned tree
- Validation is currently command-driven from the local virtualenv

## Environment Configuration

**Development:**
- Required core vars: `GEMINI_API_KEY` or `MAF_API_KEY`, plus model/base URL settings
- Optional vars: `ANTHROPIC_API_KEY`, CLI command/model overrides, `CLAUDE_CODE_GIT_BASH_PATH`
- Secrets location: repo-root `.env` (gitignored)

**Environment Differences:**
- The MAF path uses `MAF_*` names in `maf_starter/config.py`
- The legacy AutoGen path uses `AUTOGEN_*` and provider-specific variables in `autogen_starter/config.py` and `autogen_starter/providers.py`

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- LLM API calls through Gemini and optional Anthropic clients
- CLI subprocess calls to Gemini, Claude, and Codex CLIs

## Integration Risks

- DevUI customization depends on private underscore-prefixed internals in `agent_framework_devui`
- CLI fallback changes capabilities mid-turn because tool calling is not preserved
- Root `requirements.txt` does not fully document all imported integrations present in the active and legacy code paths

---

*Integration audit: 2026-03-20*
*Update when adding or removing external services*
