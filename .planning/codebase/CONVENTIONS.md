# Coding Conventions

**Analysis Date:** 2026-03-26

## Naming Patterns

**Files:**
- Use `snake_case.py` for Python modules across `maf_core/`, `autogen_dashboard/`, `command_center/`, and `entities/`.
- Keep entry files literal and thin: `main.py`, `app.py`, `cli.py`, `config.py`, plus `agent.py` and `workflow.py` under `entities/`.
- Use responsibility-based suffixes such as `*_factory.py`, `*_policy.py`, `*_parser.py`, `*_service.py`, `*_store.py`, and `*_contracts.py`.

**Functions:**
- Use `snake_case` for Python functions and methods, including async functions in `maf_core/routing_policy.py`, `maf_core/validation_runner.py`, and `autogen_dashboard/app.py`.
- Name builders and factories literally, for example `build_agent`, `build_repo_team`, `build_routing_plan`, `create_command_center_app`, and `create_app`.
- Browser-side helpers in `command_center/static/*.js` and `autogen_dashboard/static/app.js` use lower camel case names such as `normalizeMessage` and `renderMessageCard`.

**Variables:**
- Use `snake_case` for locals and parameters.
- Use `UPPER_SNAKE_CASE` for module constants such as `PROJECT_ROOT`, `DEFAULT_MODEL`, `STATIC_DIR`, and `SCRATCH_ROOT`.
- Test helpers use descriptive names like `make_scratch_dir`, `init_repo`, `fake_service`, and `mock_settings`.

**Types:**
- Use `PascalCase` for dataclasses and Pydantic models such as `Settings`, `RoutingPlan`, `ChainStep`, `ValidationPlan`, `RunSummary`, and `SessionDetail`.
- Use `Literal` aliases and `TypeAlias` for constrained values in `maf_core/routing_types.py`, `maf_core/orchestration.py`, and `maf_core/config.py`.
- Prefer typed collections and explicit model objects over loose dictionaries, except at JSON and SSE boundaries.

## Code Style

**Formatting:**
- Use typed Python with `from __future__ import annotations` as the default in active modules such as `maf_core/config.py`, `command_center/app.py`, `autogen_dashboard/app.py`, and most files under `tests/`.
- Keep imports grouped as stdlib, third-party, then local packages, separated by blank lines.
- Favor small helper functions, guard clauses, and explicit dataclass or model construction over free-form dictionaries in core runtime code.
- No committed formatter config was detected. The repo has no `pyproject.toml`, `.editorconfig`, `ruff.toml`, `.flake8`, or formatter-specific config files.

**Linting:**
- No committed lint runner or lint config was detected.
- The checked-in static validation path in `maf_core/validation_runner.py` only plans `git diff --check`, `python -m compileall`, `python -m unittest discover -s tests -v`, and per-file `node --check ...`.
- Keep formatting and import hygiene readable without assuming automated lint fixes exist.

## Tooling Setup

**Dependency manifests:**
- `requirements.txt` is the only committed Python dependency manifest.
- It includes runtime and observability packages such as `structlog` and `prometheus-fastapi-instrumentator`, but no dev-only quality tools like `pytest`, `pytest-asyncio`, `mypy`, `ruff`, or `black`.
- No lockfile or separate dev requirements file was detected.

## Import Organization

**Order:**
1. Standard library imports such as `pathlib`, `dataclasses`, `typing`, `subprocess`, and `unittest`.
2. Third-party imports such as `fastapi`, `pydantic`, `pydantic_settings`, `structlog`, and `agent_framework`.
3. Local package imports such as `maf_core.*`, `command_center.*`, `autogen_dashboard.*`, and `entities.*`.

**Path Aliases:**
- None detected. Imports use real package names and the repo's package layout.
- Relative imports are rare. New code should follow the absolute-import pattern used in `command_center/app.py` and `tests/test_phase6_api_contract.py`.

## Type Checking

**Posture:**
- Type hints are pervasive across the active runtime: `Path`, `Literal`, `TypeAlias`, dataclasses, and Pydantic models are used heavily in `maf_core/config.py`, `maf_core/routing_types.py`, `maf_core/control_plane/contracts.py`, and `autogen_dashboard/schemas.py`.
- Runtime validation is delegated to `pydantic` and `pydantic-settings` for config and API contracts.
- No committed type-checker config or command was detected. There is no `mypy.ini`, `pyrightconfig.json`, or repo-local type gate.

## Error Handling

**Patterns:**
- Raise `ValueError` for invalid paths, config, or request payloads in setup and repo-resolution code such as `maf_core/config.py` and `autogen_dashboard/repo_context.py`.
- Translate boundary failures to `HTTPException` in FastAPI surfaces such as `command_center/app.py` and `autogen_dashboard/app.py`.
- Preserve structured state with dataclasses or Pydantic models instead of returning ad hoc error dictionaries.
- Tests assert failure types explicitly with `self.assertRaises(...)` and `pytest.raises(...)`.

## Logging

**Framework:** Mixed `structlog`, stdlib `logging`, and `print`.

**Patterns:**
- `maf_core/logging.py` configures JSON `structlog`, and `maf_core/cli.py` calls `configure_logging()`.
- `maf_core/cli.py` still prints doctor and smoke output directly for human operators.
- `maf_core/worker_delegation.py` uses stdlib `logging.getLogger(__name__)` instead of `structlog`.
- New logging work should stay at CLI, API, and service boundaries and avoid introducing another logging style.

## Comments

**When to Comment:**
- Module docstrings are used at boundary files such as `autogen_dashboard/app.py` and in some test files to describe compatibility or contract scope.
- Inline comments are sparse and usually reserved for setup or assertion rationale in tests, especially around scratch repos and validation expectations.
- Prefer descriptive names over comment-heavy implementation.

**JSDoc/TSDoc:**
- Not detected in `command_center/static/*.js` or `autogen_dashboard/static/*.js`.
- Python docstrings are used selectively for fixtures, tests, and boundary helpers.

## Function Design

**Size:**
- Keep pure helpers small and focused as in `maf_core/routing_policy.py` and `maf_core/validation_runner.py`.
- Large boundary modules already exist in `command_center/app.py` and `autogen_dashboard/session_runner.py`; new code should extract helpers instead of expanding those files further.

**Parameters:**
- Prefer explicit keyword arguments and typed objects such as `Settings`, `ValidationPlan`, and request or response models.
- Use `Path` and typed tuples when the domain is known.

**Return Values:**
- Prefer dataclasses, Pydantic models, and explicit tuples, as seen in `maf_core/routing_policy.py`, `maf_core/validation_runner.py`, and `maf_core/control_plane/contracts.py`.
- Use raw dictionaries primarily at JSON serialization and event-payload boundaries.

## Module Design

**Exports:**
- Keep entrypoints thin: `main.py` dispatches to `maf_core/cli.py`, and `entities/*/agent.py` and `entities/*/workflow.py` should stay wrapper-only.
- Keep shared orchestration logic in `maf_core/`.
- Keep HTTP surface assembly in `command_center/app.py` and `autogen_dashboard/app.py`.
- Keep schema contracts in `maf_core/control_plane/contracts.py` and `autogen_dashboard/schemas.py`.

**Barrel Files:**
- Minimal `__init__.py` files are used for package discovery, not for broad re-export barrels.
- Import new code from its concrete module path instead of relying on umbrella exports.

## CI & Automation

**Current state:**
- No `.github/workflows/`, `azure-pipelines.yml`, `.pre-commit-config.yaml`, or other committed CI automation was detected.
- Quality checks are local and manual today: `README.md` documents `python main.py doctor`, `python main.py smoke`, and `python main.py probe-models`, while `maf_core/validation_runner.py` codifies the safe validation ladder.
- New enforcement should assume no existing pipeline contract and add automation explicitly.

---

*Convention analysis: 2026-03-26*
