# Testing Patterns

**Analysis Date:** 2026-03-26

## Test Framework

**Runner:**
- Mixed framework:
  - `unittest` is the dominant checked-in style in 21 of 23 modules under `tests/`, including `tests/test_command_center.py`, `tests/test_phase1_runtime.py`, and `tests/test_phase6_api_contract.py`.
  - `pytest` is also required by `tests/test_config.py` and `tests/test_workflows.py`.
- Config: Not detected. There is no committed `pytest.ini`, `pyproject.toml`, `conftest.py`, `tox.ini`, or `noxfile.py`.

**Assertion Library:**
- `unittest.TestCase` assertions dominate the suite.
- Plain `assert` and `pytest.raises(...)` are used in `tests/test_config.py` and `tests/test_workflows.py`.

**Run Commands:**
```bash
python -m unittest discover -s tests -v
python -m pytest tests/test_config.py tests/test_workflows.py
node --check autogen_dashboard/static/app.js
```

## Test File Organization

**Location:**
- The main suite lives in `tests/` with 23 top-level `test_*.py` modules.
- Additional ad hoc scripts `test_delegation_quick.py` and `test_manager_worker_demo.py` sit at repo root and are outside default `tests/` discovery.

**Naming:**
- `test_*.py` naming is consistent.
- Phase-scoped files group work by milestone, for example `tests/test_phase1_api.py` through `tests/test_phase6_service.py`.

**Structure:**
```text
tests/
  test_command_center.py
  test_config.py
  test_maf_setup.py
  test_phase1_*.py
  test_phase2_*.py
  test_phase3_*.py
  test_phase4_*.py
  test_phase5_*.py
  test_phase6_*.py
  test_run_persistence.py
  test_worker_delegation.py
  test_workflows.py
  test_workspace_contract.py
```

## Test Structure

**Suite Organization:**
```python
class CommandCenterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_command_center_app(self.settings))

    def test_status_reports_debug_surface(self) -> None:
        response = self.client.get("/api/status")
        self.assertEqual(response.status_code, 200)
```

**Patterns:**
- `unittest.TestCase` and `unittest.IsolatedAsyncioTestCase` are the default class-based patterns, as seen in `tests/test_command_center.py`, `tests/test_phase1_runtime.py`, `tests/test_phase2_runtime.py`, and `tests/test_phase4_approval.py`.
- Pytest function tests with fixtures and `@pytest.mark.asyncio` exist in `tests/test_config.py` and `tests/test_workflows.py`.
- Scratch repos under `.tmp-tests/` plus helper methods like `make_scratch_dir()` and `init_repo()` are the standard way to exercise filesystem and git behavior.
- API and UI contract tests use `fastapi.testclient.TestClient` plus direct file reads instead of browser automation.

## Mocking

**Framework:** `unittest.mock` plus pytest fixtures.

**Patterns:**
```python
with patch.object(service, "_run_stage_prompt", new=AsyncMock(side_effect=stage_calls)):
    await service.run_step(created.id)
```

**What to Mock:**
- Provider calls, planner or agent builders, and background execution seams in `autogen_dashboard/session_runner.py`, `maf_core/provider_fallback.py`, and workflow runners.
- Environment variables via `patch.dict("os.environ", ...)` when exercising `maf_core/config.py`.

**What NOT to Mock:**
- Repo layout, git metadata, and filesystem contract checks; tests usually create real temporary repos under `.tmp-tests/`.
- Static asset contract tests in `tests/test_phase5_ui_contract.py` and `tests/test_phase5_operator_views.py` read checked-in files directly.

## Fixtures and Factories

**Test Data:**
```python
class RepoScratchTestCase(unittest.TestCase):
    def make_scratch_dir(self) -> Path:
        path = SCRATCH_ROOT / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path
```

**Location:**
- Fixture helpers are mostly inline inside each module, for example `RepoScratchTestCase` in `tests/test_workspace_contract.py` and `tests/test_maf_setup.py`.
- Pytest fixtures are also inline, especially in `tests/test_config.py` and `tests/test_workflows.py`.
- No shared `conftest.py`, fixture package, or factory module was detected.

## Coverage

**Requirements:** None enforced. No coverage command, `.coveragerc`, or threshold gate was detected.

**View Coverage:**
```bash
# Not configured in-repo
```

## Test Types

**Unit Tests:**
- Config parsing, route planning, validation planning, write execution, orchestration state, and worker delegation logic are covered in files such as `tests/test_config.py`, `tests/test_phase3_routing.py`, `tests/test_phase4_validation.py`, `tests/test_phase4_write_execution.py`, and `tests/test_worker_delegation.py`.

**Integration Tests:**
- FastAPI `TestClient` exercises `command_center/app.py` and `autogen_dashboard/app.py` in `tests/test_command_center.py`, `tests/test_phase1_api.py`, `tests/test_phase3_api.py`, and `tests/test_phase6_api_contract.py`.
- Real temporary git repos and state directories are used for workspace, persistence, and validation behavior in `tests/test_workspace_contract.py`, `tests/test_run_persistence.py`, and `tests/test_phase4_validation.py`.

**E2E Tests:**
- Not used. No browser automation or live provider integration tests were detected.

## Common Patterns

**Async Testing:**
```python
class Phase2RuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def test_planning_stage_pauses_for_approval_and_persists_stage_output(self) -> None:
        ...
```

**Error Testing:**
```python
with self.assertRaises(ValueError):
    resolve_repo_root(str(outside_repo), scan_root)
```

## Tooling and CI Gaps

- `requirements.txt` does not declare `pytest` or `pytest-asyncio`, even though `tests/test_config.py` and `tests/test_workflows.py` require them.
- `python -m pytest --collect-only tests/test_config.py tests/test_workflows.py -q` currently fails in the repo `.venv` with `No module named pytest`.
- `python -m unittest discover -s tests -v` currently fails because `tests/test_workflows.py` imports `pytest`, and several settings-driven tests error while `pydantic-settings` parses `fallback_chain` from the repo-root `.env`.
- `maf_core/validation_runner.py` and `tests/test_phase4_validation.py` still encode `python -m unittest discover -s tests -v` as the Python test gate, so the checked-in validation ladder does not cover the pytest-only modules.
- No committed CI pipeline was detected: no `.github/workflows/`, `azure-pipelines.yml`, or other automation files are present.
- No browser E2E, coverage reporting, or automated type-check gate is present.

---

*Testing analysis: 2026-03-26*
