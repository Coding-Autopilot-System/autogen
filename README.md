# Microsoft Agent Framework Starter

This repo now runs as a Microsoft Agent Framework starter instead of the previous AutoGen-first setup.

It is configured for:

- Microsoft Agent Framework Python SDK
- Operator Workbench as the primary local product UI
- Microsoft DevUI for local interactive testing
- Gemini API through Google's OpenAI-compatible endpoint
- Gemini CLI fallback when the Gemini API returns quota errors
- local repo inspection tools so the agent can reason over files in this repo
- human approval before the agent treats a proposed action as approved

The current entrypoint is [main.py](/C:/repo/autogen/main.py), which now dispatches to the MAF CLI in [maf_starter/cli.py](/C:/repo/autogen/maf_starter/cli.py).

## What Is Included

- `entities/repo_copilot`
  A repo-aware Gemini agent discovered by DevUI.

- `entities/repo_copilot_auto`
  Auto-routing repo assistant with ordered API and CLI fallback.

- `entities/repo_copilot_pro`
- `entities/repo_copilot_flash`
- `entities/repo_copilot_flash_lite`
  Model-pinned assistants so the DevUI entity dropdown acts like a model selector.

- `entities/repo_copilot_workflow`
  A checkpointed workflow wrapper around the same agent.

- `entities/repo_team`
  A true multi-agent sequential workflow: planner -> researcher -> implementer -> reviewer, with request-info pauses.

- `maf_starter/tools.py`
  Safe local tools for:
  - repo overview
  - file listing
  - file reading
  - text search
  - human approval requests

- `maf_starter/cli.py`
  Local commands for:
  - config checks
  - smoke tests
  - Gemini model probing
  - launching DevUI

## Quick Start

### 1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
python -m pip install -U pip
python -m pip install -r requirements.txt
```

### 3. Copy the env template

```powershell
Copy-Item .env.example .env
```

Then fill in `GEMINI_API_KEY`.

### 4. Check configuration

```powershell
python main.py doctor
```

### 5. Run a smoke test

```powershell
python main.py smoke --message "Reply with exactly READY"
```

### 6. Probe Gemini models

This is useful if you want to see which Gemini models work with your current key/project before picking a default.

```powershell
python main.py probe-models
```

### 7. Launch Operator Workbench

```powershell
python -m uvicorn autogen_dashboard.app:create_app --factory --host 127.0.0.1 --port 8000
```

Then open:

- `http://127.0.0.1:8000`

The Operator Workbench is the polished local UI for daily use. The active run workspace is organized into:

- `Overview`
- `Timeline`
- `Agents`
- `Routing`
- `Artifacts`

Operator Workbench manual spot checks:

- confirm human, manager, specialist, approval, and event messages are visually distinct at a glance
- confirm the active route and active stage strips stay visible above the transcript
- confirm Timeline shows approvals, route attempts, validation steps, and stage changes without reading raw logs
- confirm Artifacts shows changed files, diff artifacts, validation results, and saved stage outputs
- confirm the selected run stays visually dominant and the create-run panel becomes secondary once a run is active
- confirm the rail and workspace stack cleanly on narrower laptop widths

### 8. Launch DevUI

```powershell
python main.py devui --host 127.0.0.1 --port 8080 --no-open
```

Then open:

- `http://127.0.0.1:8080`

DevUI will discover the entities under [entities](/C:/repo/autogen/entities).

On Windows, the easiest way to keep the server alive is:

```powershell
.\start_devui.ps1
```

That opens a dedicated PowerShell window and keeps DevUI running there.

To stop it later:

```powershell
.\stop_devui.ps1
```

Runtime logs are written to `.maf-devui.out.log` and `.maf-devui.err.log`.

## Commands

- `python main.py doctor`
  Prints the effective MAF config without exposing the API key.

- `python main.py smoke --message "..."`
  Runs the repo copilot once through Agent Framework and prints the response.

- `python main.py probe-models`
  Tries the configured Gemini model candidates with a short prompt and prints success/failure per model.

- `python main.py devui --host 127.0.0.1 --port 8080 --no-open`
  Starts Microsoft Agent Framework DevUI using directory discovery.

- `python -m uvicorn autogen_dashboard.app:create_app --factory --host 127.0.0.1 --port 8000`
  Starts the Operator Workbench product UI over the existing dashboard runtime.

## Human In The Loop

This starter currently uses tool approval as the first HITL mechanism.

The agent has a `request_human_approval` tool marked with mandatory approval. In DevUI, when the model decides it needs confirmation for a proposed action, DevUI will pause and ask you to approve or reject the tool call before the run continues.

That is the simplest supported MAF path for a practical local setup. A richer request/response workflow gate can be added next if you want explicit pause states separate from tool approval.

## Gemini Quota Fallback

The main auto-routing MAF agent now uses an ordered fallback chain.

Default chain:

1. `gemini:gemini-2.5-pro`
2. `anthropic:claude-sonnet-4-6` when `ANTHROPIC_API_KEY` is configured
3. `gemini:gemini-2.5-flash`
4. `gemini:gemini-2.5-flash-lite`
5. `claude-cli`
6. `codex-cli`
7. `gemini-cli:gemini-2.5-pro`

That means DevUI can keep answering even when the free-tier Gemini project is exhausted.

Important limitation:

- when a turn falls back to a CLI provider, tool calling is unavailable for that turn
- the response is prefixed so you can see that fallback was used

You can override the chain in `.env` with:

```env
MAF_FALLBACK_CHAIN=gemini:gemini-2.5-pro,anthropic:claude-sonnet-4-6,gemini:gemini-2.5-flash,gemini:gemini-2.5-flash-lite,claude-cli,codex-cli,gemini-cli:gemini-2.5-pro
```

## Configuration

The loader in [maf_starter/config.py](/C:/repo/autogen/maf_starter/config.py) reads `.env` from the repo root.

Primary variables:

```env
MAF_MODEL=gemini-2.5-flash
MAF_REPO_ROOT=C:\repo\autogen
MAF_ENTITIES_DIR=entities
MAF_CHECKPOINT_DIR=state\maf-checkpoints
MAF_FALLBACK_CHAIN=gemini:gemini-2.5-pro,gemini:gemini-2.5-flash,gemini:gemini-2.5-flash-lite,claude-cli,codex-cli,gemini-cli:gemini-2.5-pro
GEMINI_API_KEY=...
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
```

Compatibility fallbacks:

- `MAF_MODEL` falls back to `GEMINI_MODEL`
- `MAF_BASE_URL` falls back to `GEMINI_BASE_URL`
- `MAF_API_KEY` falls back to `GEMINI_API_KEY`

Optional extra API:

```env
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-6
```

## Notes

- `autogen_dashboard` is now the primary operator-facing product UI. DevUI remains useful for framework-level inspection, but the workbench is the surface intended for daily run management.
- `autogen_starter` remains legacy code.
- Gemini model availability and quota are project-specific. Use `python main.py probe-models` if you want a real answer for your current key instead of guessing from docs.

## DevUI UI Development

This repo treats DevUI as a local sample app, not a long-term product UI.

The practical customization seams are:

- [maf_starter/routing_policy.py](/C:/repo/autogen/maf_starter/routing_policy.py) for model/provider selection
- [maf_starter/devui_patches.py](/C:/repo/autogen/maf_starter/devui_patches.py) for route metadata and trace payloads
- [maf_starter/devui_overrides.py](/C:/repo/autogen/maf_starter/devui_overrides.py) for injected CSS/JS presentation changes

For the full repo-specific guide, see [docs/DEVUI_CUSTOMIZATION.md](/C:/repo/autogen/docs/DEVUI_CUSTOMIZATION.md).

## Official References

- [Microsoft Agent Framework Overview](https://learn.microsoft.com/en-us/agent-framework/overview/?pivots=programming-language-python)
- [AutoGen to Microsoft Agent Framework Migration Guide](https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/)
- [DevUI Directory Discovery](https://learn.microsoft.com/en-us/agent-framework/devui/directory-discovery)
- [DevUI Security](https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/security)
- [DevUI Samples](https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/samples)
- [Human in the Loop](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop)
