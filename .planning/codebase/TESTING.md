# Testing Map

## Test Framework
- The checked-in suite uses Python `unittest`, not `pytest`.
- HTTP-level tests use `fastapi.testclient.TestClient` against `command_center/app.py` and `autogen_dashboard/app.py`.
- Async seams are exercised with `unittest.mock.AsyncMock`, `patch`, and direct `asyncio` execution.
- Most tests are written as small `unittest.TestCase` classes with scratch-directory helpers.

## Test Layout
- Source tests live in `tests/` and are named `test_*.py`.
- `tests/test_maf_setup.py` is the broadest setup and runtime seam test.
- `tests/test_command_center.py` covers the new operator surface in `command_center/app.py`.
- Phase-oriented files such as `tests/test_phase1_api.py`, `tests/test_phase2_manager.py`, `tests/test_phase3_routing.py`, `tests/test_phase4_validation.py`, and `tests/test_phase5_ui_contract.py` preserve feature-specific coverage.
- Workspace and persistence checks live in `tests/test_workspace_contract.py` and `tests/test_run_persistence.py`.

## Behaviors Covered
- Config precedence, model selection, and fallback-chain parsing are covered in `maf_starter/config.py` and `maf_starter/routing_types.py`.
- Repo path safety, local tool exposure, and approval hooks are covered in `maf_starter/tools.py` and `maf_starter/approval_policy.py`.
- Routing decisions, lane selection, and fallback metadata are covered in `maf_starter/routing_policy.py` and `maf_starter/provider_fallback.py`.
- Workflow orchestration and stage transitions are covered in `maf_starter/orchestration.py`, `maf_starter/team_factory.py`, and `maf_starter/workflow_factory.py`.
- Command-center catalog, repo listing, status endpoints, and SSE run shaping are covered in `command_center/app.py` and `command_center/static/app.js`.
- Legacy dashboard session CRUD, repo discovery, and event stream behavior are covered in `autogen_dashboard/app.py`, `autogen_dashboard/repo_context.py`, and `autogen_dashboard/session_runner.py`.

## Mocks And Fakes
- Tests prefer scratch repos under `.tmp-tests/` over heavy fixtures.
- `patch.dict` is used for environment isolation around `maf_starter/config.py`.
- `AsyncMock` is used to simulate provider fallback execution and streaming reroutes in `maf_starter/provider_fallback.py`.
- Fake services are used for API tests, especially in `tests/test_phase1_api.py`, `tests/test_command_center.py`, and `tests/test_workspace_contract.py`.
- UI contract tests read static files directly rather than booting a browser.

## Static Checks
- The repo currently expects local checks such as `python -m compileall`, `git diff --check`, and `python -m unittest discover -s tests -v`.
- `tests/test_phase4_validation.py` codifies the safe command ladder, including `python -m compileall`, `python -m unittest discover -s tests -v`, and `node --check autogen_dashboard/static/app.js`.
- Manual runtime checks remain documented in `README.md` through `python main.py doctor`, `python main.py smoke`, `python main.py probe-models`, `start_ui.ps1`, and `start_devui.ps1`.

## Known Validation Gaps
- There is no coverage threshold or coverage report config in the repo.
- There is no browser automation for `command_center/static/*` or `autogen_dashboard/static/*`.
- The large legacy state machine in `autogen_dashboard/session_runner.py` is only partially covered.
- The new command-center UI is verified mostly through contract and API tests, not end-to-end UI interaction tests.
- External provider behavior, real network failures, and Azure-style deployment paths remain outside automated test coverage.
