# Codebase Conventions

## Python Layout
- Active runtime code lives in `main.py`, `maf_starter/*.py`, `command_center/app.py`, and `autogen_dashboard/*.py`.
- New shared orchestration behavior should go into `maf_starter/`, not into the entity wrappers or UI shells.
- Thin entry modules should stay thin, especially `main.py` and the `entities/*/agent.py` and `entities/*/workflow.py` entry points.
- Keep filesystem-safe helpers and repo boundary checks close to `maf_starter/tools.py` and `autogen_dashboard/repo_context.py`.

## Naming And Typing
- Use `snake_case` for functions, modules, and local variables across `maf_starter/` and the frontend helpers in `command_center/static/app.js`.
- Use `PascalCase` for dataclasses and schema objects such as `Settings`, `RoutingPlan`, `ChainStep`, and `SessionDetail`.
- Prefer explicit type hints, `from __future__ import annotations`, and concrete union types over loose dictionaries.
- Favor builder names like `build_agent`, `build_workflow`, and `build_repo_team` when constructing runtime objects.

## Separation Of Concerns
- Keep config parsing in `maf_starter/config.py` and out of agent, workflow, or UI code.
- Keep provider fallback logic centralized in `maf_starter/provider_fallback.py`.
- Keep route policy decisions in `maf_starter/routing_policy.py` and route data shapes in `maf_starter/routing_types.py`.
- Keep command-center HTTP assembly in `command_center/app.py` and browser rendering in `command_center/static/app.js`.

## Error Handling
- Raise explicit exceptions at the point of failure instead of silently recovering in helper code.
- Convert config and path validation problems to `ValueError` in core setup code such as `maf_starter/config.py`.
- Convert boundary failures to `HTTPException` in FastAPI apps such as `autogen_dashboard/app.py` and `command_center/app.py`.
- Keep fallback retries narrow and intentional in `maf_starter/provider_fallback.py`; do not broaden retry logic into unrelated modules.

## Route And Event Modeling
- Route decisions are modeled with dataclasses and literals in `maf_starter/routing_types.py` and `maf_starter/routing_policy.py`.
- `ChainStep`, `RouteAttempt`, `CapabilityChange`, and `RoutingPlan` are the core structured route objects.
- The command center streams AG-UI events from `command_center/app.py` and prepends route banners so the UI can surface the active provider and tier.
- The browser client in `command_center/static/app.js` keys off event `type` values such as `RUN_STARTED`, `TOOL_CALL_START`, `CUSTOM`, `RUN_FINISHED`, and `RUN_ERROR`.

## Frontend Patterns
- `command_center/static/index.html` uses a three-column operator layout: workspace sidebar, transcript center, inspector rail.
- `command_center/static/styles.css` uses dark enterprise cards, pill chips, rounded panels, and responsive grid breakpoints.
- `command_center/static/app.js` is a single IIFE that owns state, rendering, and SSE request handling.
- Keep the command center UI polished and readable, while treating `autogen_dashboard/static/*` as the legacy operator surface.

## Legacy UI Boundaries
- `autogen_dashboard/app.py` still exposes session APIs and static files for the older dashboard path.
- `autogen_dashboard/static/app.js` and `autogen_dashboard/static/styles.css` remain contract-tested but should not drive new UI patterns.
- New UI work should target `command_center/` unless the task explicitly concerns legacy compatibility.

## Script Conventions
- `main.py` is the top-level dispatcher and should stay a small pass-through to `maf_starter/cli.py`.
- `maf_starter/cli.py` owns argparse parsing and runtime launch logic for `doctor`, `smoke`, `probe-models`, `ui`, and `devui`.
- PowerShell launchers `start_ui.ps1`, `stop_ui.ps1`, `start_devui.ps1`, `stop_devui.ps1`, `start_debug_devui.ps1`, and `stop_debug_devui.ps1` are the preferred local entry scripts.
- Script names should match their behavior closely and avoid hidden side effects outside the documented launch or shutdown task.
