# MAF Starter Context

## Technology Stack
- **Language**: Python 3.14-era targeting a repo-local virtual environment in `.venv/`.
- **Framework**: Microsoft Agent Framework `agent-framework==1.0.0rc5`.
- **Dependencies**: `agent_framework`, `python-dotenv`, `OpenAIChatClient`, `AnthropicClient`.

## Conventions
- **Naming**: `snake_case.py` for Python modules. `*_factory.py`, `*_policy.py` name modules by responsibility.
- **Code Style**: Typed Python (`from __future__ import annotations`). Absolute package imports are preferred. No checked-in formatter config.
- **Error Handling**: Raise explicit exceptions at the point of failure. Fallback behavior is opt-in and centralized in `provider_fallback.py`.

## Architecture Layers
- **Routing & Config**: `config.py` resolves paths and API keys.
- **Factories**: `agent_factory.py`, `workflow_factory.py`, `team_factory.py` build agents and orchestrations.
- **Tools**: Constrain agent access to local repo files through explicit tools (`get_repo_overview`, `list_repo_files`, etc.).

## Practical Rule For New Work
- Put new shared MAF behavior in this `maf_starter/` directory.
- Treat `autogen_dashboard/` and `autogen_starter/` as legacy paths.
