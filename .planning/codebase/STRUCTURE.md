# Structure

## Top-Level Layout
- `main.py` is the root dispatcher for all supported commands.
- `maf_starter/` holds the active MAF runtime, routing, tooling, persistence helpers, and DevUI patches.
- `command_center/` holds the primary operator backend plus its static web shell.
- `autogen_dashboard/` holds the retained legacy dashboard and session runtime.
- `autogen_starter/` holds legacy AutoGen entrypoints and provider glue.
- `entities/` exposes DevUI-discoverable agents and workflows.

## Package Ownership
- `maf_starter/agent_factory.py` builds the repo-aware assistant and model-pinned variants.
- `maf_starter/team_factory.py` builds the manager-led `repo_team` workflow.
- `maf_starter/workflow_factory.py` builds the simpler checkpointed workflow wrapper.
- `maf_starter/orchestration.py` owns orchestration state models, stage names, and persistence path helpers.
- `maf_starter/tools.py` owns safe repo reads, listing, search, approval, and write-plan application.
- `maf_starter/repo_execution.py` owns bounded file write execution and diff capture.
- `autogen_dashboard/session_runner.py` and `autogen_dashboard/session_store.py` own legacy session lifecycle and disk state.

## Entry Points
- `python main.py doctor` prints configuration.
- `python main.py smoke` runs a one-shot agent call.
- `python main.py probe-models` probes configured Gemini candidates.
- `python main.py ui` starts `command_center/app.py`.
- `python main.py devui` starts the raw DevUI debugger.
- `start_ui.ps1`, `stop_ui.ps1`, `start_devui.ps1`, and `stop_devui.ps1` are the Windows launch scripts.

## Entities
- `entities/repo_copilot/agent.py` exposes the default repo-aware agent.
- `entities/repo_copilot_auto/agent.py` exposes the auto-routed agent.
- `entities/repo_copilot_pro/agent.py`, `entities/repo_copilot_flash/agent.py`, and `entities/repo_copilot_flash_lite/agent.py` expose model-pinned agents.
- `entities/repo_copilot_workflow/workflow.py` exposes the checkpointed single-agent workflow.
- `entities/repo_team/workflow.py` exposes the manager-led multi-agent workflow.
- Each entity package keeps its `__init__.py` thin so DevUI discovery stays simple.

## Tests
- `tests/test_command_center.py` exercises the primary UI backend and catalog responses.
- `tests/test_maf_setup.py` covers settings, routing, fallback middleware, tools, and DevUI patching.
- `tests/test_phase3_routing.py` and `tests/test_phase3_specialists.py` validate route selection and specialist metadata.
- `tests/test_phase4_write_execution.py` covers safe write capture and diff generation.
- `tests/test_run_persistence.py` and `tests/test_workspace_contract.py` cover session storage and repo discovery.
- `tests/test_phase5_ui_contract.py` checks the legacy dashboard frontend contract.

## Docs and Planning
- `README.md` documents the active runtime, command center, and fallback behavior.
- `docs/DEVUI_CUSTOMIZATION.md` documents the local DevUI patching seam.
- `.planning/PROJECT.md`, `.planning/STATE.md`, and `.planning/ROADMAP.md` hold the live project plan.
- `.planning/phases/` stores phase context, plans, validation, and summaries.
- `.planning/codebase/` stores the repo map, including `ARCHITECTURE.md` and `STRUCTURE.md`.

## Naming and Organization Patterns
- Python modules use `snake_case.py` across `maf_starter/`, `autogen_dashboard/`, `autogen_starter/`, and `entities/`.
- Builder functions are named literally, such as `build_agent`, `build_workflow`, and `build_repo_team`.
- Shared responsibility modules tend to end in `_factory.py`, `_policy.py`, `_types.py`, or `_runner.py`.
- Constants use `UPPER_SNAKE_CASE`, while data carriers use `PascalCase` dataclasses and schemas.
- The repo keeps active MAF code in `maf_starter/` and treats legacy AutoGen paths as compatibility surfaces.
