# Entities Context

## Architecture Layers
- **Purpose**: Expose concrete agents and workflows to DevUI directory discovery.
- **Contents**: `entities/repo_copilot/*`, `entities/repo_copilot_auto/*`, `entities/repo_copilot_pro/*`, `entities/repo_team/*`, etc.
- **Dependencies**: Relies on starter factories (`maf_starter`).

## Conventions
- **Naming**: `agent.py` and `workflow.py` are reserved as entity entry files under `entities/`.
- **Module Design**: `__init__.py` files under `entities/` expose one discovery object for DevUI.
- **Practical Rule For New Work**: Keep entity files as thin wrappers around factories.
