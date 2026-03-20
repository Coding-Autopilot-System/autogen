# Coding Conventions

**Analysis Date:** 2026-03-20

## Naming Patterns

**Files:**
- `snake_case.py` for Python modules across `maf_starter/`, `autogen_starter/`, and `autogen_dashboard/`
- `agent.py` and `workflow.py` are reserved as entity entry files under `entities/`
- `*_factory.py`, `*_policy.py`, `*_types.py` name modules by responsibility rather than feature marketing language

**Functions:**
- `snake_case` for functions and helper methods
- async functions do not use a special naming prefix
- builders are named literally: `build_agent`, `build_workflow`, `build_repo_team`

**Variables:**
- `snake_case` for local variables and parameters
- module-level constants are `UPPER_SNAKE_CASE`, for example `DEFAULT_MODEL`, `DEFAULT_SMOKE_MESSAGE`, and `FALLBACK_NOTICE`

**Types:**
- `PascalCase` for dataclasses and schema types such as `Settings`, `RoutingPlan`, `RunOutcome`, and `SessionDetail`
- no `I` prefix for interfaces or types

## Code Style

**Formatting:**
- typed Python with `from __future__ import annotations` used broadly in the active path
- imports grouped stdlib, third-party, then local packages
- explicit `Path`, dataclass, and union type usage rather than loose dictionaries where possible
- no checked-in formatter config was present

**Linting:**
- no repo-level lint config (`pyproject.toml`, `ruff.toml`, `setup.cfg`, `tox.ini`, `noxfile.py`) was present
- style is enforced mainly by consistency and local validation commands

## Import Organization

**Order:**
1. standard library imports
2. third-party imports
3. repo-local imports

**Grouping:**
- blank line separation between import groups is used consistently
- absolute package imports are preferred over deep relative imports

**Path Aliases:**
- none detected; Python package imports use actual package names like `maf_starter.*` and `autogen_dashboard.*`

## Error Handling

**Patterns:**
- raise explicit exceptions at the point of failure
- catch and translate at boundaries rather than swallowing errors
- fallback behavior is opt-in and centralized in `maf_starter/provider_fallback.py`

**Error Types:**
- `ValueError` for config and path validation issues
- `RuntimeError` for provider and subprocess failures
- `HTTPException` boundary translation in `autogen_dashboard/app.py`
- custom provider configuration errors exist in the legacy AutoGen path

## Logging

**Framework:**
- no structured logging framework detected
- `print(...)` and log files are used for CLI/runtime visibility

**Patterns:**
- status output is emitted mainly from command entrypoints
- runtime logs are captured into `.maf-devui.*.log` and `.dashboard.*.log`
- deeper modules prefer raising errors with context instead of logging internally

## Comments

**When to Comment:**
- comments are sparse and mostly avoided when naming is clear
- docstrings are used for repo tools in `maf_starter/tools.py`
- `# pragma: no cover` appears only where necessary in tests and small CLI seams

**TODO Comments:**
- no dominant TODO convention was evident in the scanned source

## Function Design

**Size:**
- most active MAF modules are small and focused
- the main exception is the legacy `autogen_dashboard/session_runner.py`, which is substantially larger and more stateful

**Parameters:**
- explicit parameters are preferred over freeform dictionaries
- settings objects and dataclasses are used to avoid passing large option lists repeatedly

**Return Values:**
- explicit returns and guard clauses are common
- factories return ready-to-use agents and workflows rather than partially configured components

## Module Design

**Exports:**
- modules usually export a small set of focused functions and classes
- `__init__.py` files under `entities/` expose one discovery object for DevUI

**Barrel/Entry Modules:**
- `main.py` acts as the root dispatcher
- entity packages keep entry files thin and push logic into shared starter modules

## Practical Rule For New Work

- Put new shared MAF behavior in `maf_starter/`
- Keep entity files thin wrappers around factories
- Treat `autogen_dashboard/` and `autogen_starter/` as legacy paths unless intentionally maintaining them

---

*Convention analysis: 2026-03-20*
*Update when patterns change*
