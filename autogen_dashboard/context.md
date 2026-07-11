# AutoGen Dashboard & Starter Context

## Technology Stack
- **Language**: JavaScript (legacy dashboard UI in `app.js`), HTML/CSS (`index.html`, `styles.css`), Python.
- **Framework**: FastAPI/Uvicorn (`autogen_dashboard/app.py`), AutoGen AgentChat.
- **Dependencies**: `fastapi`, `uvicorn`, Pydantic (`schemas.py`).

## Conventions
- **Naming**: `snake_case.py` for Python modules. `PascalCase` for dataclasses and schema types (e.g., `SessionDetail`).
- **Error Handling**: `HTTPException` boundary translation in `app.py`. Custom provider configuration errors exist in the legacy AutoGen path.
- **Function Design**: The legacy `autogen_dashboard/session_runner.py` is substantially larger and more stateful than modern MAF components.

## Architecture Layers
- **Purpose**: Preserve the older AutoGen dashboard and provider/session architecture.
- **Data Flow**: Legacy AutoGen state is file-based under `state/team_state.json` and `state/sessions/*`.
- **Entry Points**: `autogen_starter/cli.py` triggers the legacy `dashboard` command path to launch `autogen_dashboard.app`.

## Practical Rule For New Work
- Treat `autogen_dashboard/` and `autogen_starter/` as **legacy paths** unless intentionally maintaining them. New shared behavior should go to `maf_starter/`.
