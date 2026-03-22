# External Integrations

## Model Providers
- Gemini API is the primary model path via `OpenAIChatClient` and `GEMINI_BASE_URL` in `maf_starter/agent_factory.py` and `maf_starter/config.py`.
- Anthropic API is optional in `maf_starter/provider_fallback.py` when `ANTHROPIC_API_KEY` is present.
- `autogen_starter/providers.py` also models `azure-openai` through `AZURE_OPENAI_DEPLOYMENT`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, and `AZURE_OPENAI_API_VERSION`.
- Local CLI providers are wired through `gemini.cmd`, `claude`, and `codex.cmd` in `maf_starter/provider_fallback.py`.
- The fallback chain in `maf_starter/provider_fallback.py` retries across API and CLI providers when quota or rate-limit style failures appear.

## AG-UI and DevUI
- `command_center/app.py` uses `agent_framework_ag_ui.AGUIRequest`, `AgentFrameworkAgent`, `AgentFrameworkWorkflow`, and `ag_ui.encoder.EventEncoder`.
- `maf_starter/cli.py` launches `agent_framework_devui._server.DevServer` for the raw debugger.
- `maf_starter/devui_patches.py` and `maf_starter/devui_overrides.py` inject route metadata, banners, and UI styling into DevUI.
- `docs/DEVUI_CUSTOMIZATION.md` documents the overlay and in-flight bundle patch strategy.
- `command_center/static/index.html` exposes Events, Tools, Agents, Workflow, and Routing tabs plus a debug link to DevUI on `127.0.0.1:8090`.

## Local Process Boundaries
- `maf_starter/provider_fallback.py` shells out to CLI providers with `subprocess.run`.
- `maf_starter/tools.py`, `autogen_dashboard/repo_context.py`, and `maf_starter/validation_runner.py` shell out to `git`.
- `maf_starter/cli.py` and `autogen_starter/cli.py` run local `uvicorn` servers.
- `command_center/app.py` can start the debug DevUI in a background thread when `127.0.0.1:8090` is not already listening.
- `maf_starter/tools.py` constrains file operations to the repo root and blocks writes into `state/`, `.env`, `.venv`, and `.git`.

## Persistence and Checkpointing
- Active MAF checkpoints live under `state/maf-checkpoints` through `FileCheckpointStorage`.
- Run-scoped orchestration artifacts are written by `maf_starter/workflow_factory.py` and `maf_starter/orchestration.py`.
- `command_center/app.py` hashes repo roots into `state/maf-checkpoints/repos/<repo>-<hash>`.
- Legacy dashboard sessions persist under `state/sessions/<session_id>/...` via `autogen_dashboard/session_store.py`.
- Legacy resumable state is also stored in `state/team_state.json` by `autogen_starter/cli.py`.
- GSD artifacts such as auto answers and blocked questions are persisted in the session runtime tree.

## Git and Repo Integration
- `maf_starter/tools.py` provides `get_repo_overview`, `list_repo_files`, `read_repo_file`, `search_repo`, `request_human_approval`, and `apply_repo_write_plan`.
- `autogen_dashboard/repo_context.py` resolves repo roots, branch names, dirty state, recent commits, and stack hints.
- `command_center/app.py` discovers local repos under `AUTOGEN_REPO_SCAN_ROOT` and `settings.project_root.parent`.
- `maf_starter/approval_policy.py` and `maf_starter/validation_runner.py` classify `git diff --check`, `git push`, and similar risky commands.
- Tests in `tests/test_workspace_contract.py` and related files create scratch git repos to verify path safety and repo detection.

## Azure and Cloud Touchpoints
- `autogen_starter/providers.py` already supports `azure-openai` as a first-class provider.
- `autogen_dashboard/schemas.py` and `autogen_starter/config.py` both model `azure-openai`.
- `autogen_dashboard/repo_context.py` treats `host.json` as an `Azure Functions` stack hint.
- `README.md` and `docs/DEVUI_CUSTOMIZATION.md` both say DevUI should remain a local/operator console, not a public production surface.
- No Bicep, Functions deployment, or cloud infra manifests are present in the current tree, so Azure work is config-level only.
