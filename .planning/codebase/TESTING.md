# Testing Patterns

**Analysis Date:** 2026-03-20

## Test Framework

**Runner:**
- Python stdlib `unittest`
- Main checked-in source suite: `tests/test_maf_setup.py`

**Assertion Library:**
- built-in `unittest` assertions
- mocking via `unittest.mock`, including `AsyncMock`

**Run Commands:**
```bash
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall maf_starter tests main.py
python main.py doctor
python main.py smoke --message "Reply with exactly READY"
python main.py probe-models
```

## Test File Organization

**Location:**
- tests live in a separate `tests/` tree
- currently only `tests/test_maf_setup.py` is present as checked-in source

**Naming:**
- `test_*.py` module naming
- `__pycache__/` contains compiled artifacts, including a stale `test_dashboard_api` bytecode file without a matching source file

**Structure:**
```text
tests/
├── test_maf_setup.py
└── __pycache__/
```

## Test Structure

**Suite Organization:**
- `unittest.TestCase` classes with helper subclasses such as `RepoScratchTestCase`
- scratch directories are created for filesystem-safe tests
- endpoint-style tests use `fastapi.testclient.TestClient`

**Patterns:**
- patch environment variables with `patch.dict`
- patch async fallback calls with `AsyncMock`
- verify exact routing and fallback metadata, not just truthy behavior

## Mocking

**Framework:**
- `unittest.mock.patch`
- `AsyncMock` for async provider and fallback seams

**What gets mocked:**
- provider fallback execution in `maf_starter/provider_fallback.py`
- environment variables during settings resolution
- filesystem roots through scratch directories

**What is not heavily mocked:**
- pure routing logic
- real path-resolution logic
- simple helper functions such as secret masking

## Fixtures and Factories

**Test Data:**
- temporary scratch directories under `.tmp-tests/`
- inline `Message`, `ChatResponse`, and `ResponseStream` objects inside tests

**Location:**
- no separate fixtures or factory package was present
- helper setup lives directly in `tests/test_maf_setup.py`

## Coverage

**Requirements:**
- no coverage threshold or report config detected
- focus is currently on critical MAF setup seams rather than broad product coverage

**What is covered:**
- config loading precedence
- fallback chain parsing
- repo-tool safety boundaries
- agent and workflow construction
- routing plan selection
- streaming fallback behavior
- DevUI root HTML and bundle patch injection

**What is not covered well:**
- end-to-end legacy dashboard behavior in `autogen_dashboard/*`
- the large state machine in `autogen_dashboard/session_runner.py`
- UI behavior in `autogen_dashboard/static/app.js`

## Test Types

**Unit and Component Tests:**
- dominant pattern today
- focused on small runtime helpers and integration seams

**Integration Tests:**
- partial integration through `TestClient` and real helper composition
- no full browser automation or end-to-end DevUI validation was present

**Manual Validation:**
- `README.md` and `docs/DEVUI_CUSTOMIZATION.md` still rely on manual smoke checks through DevUI and CLI commands

## Common Patterns

**Async Testing:**
- async helpers are run through the event loop and validated with explicit final response assertions

**Error Testing:**
- settings and provider failures are asserted through exception paths
- fallback behavior is checked with synthetic quota-style errors

**Environment Testing:**
- local `.venv` is the expected runtime for reliable validation
- global interpreter runs are not reliable because package versions can diverge from the repo

---

*Testing analysis: 2026-03-20*
*Update when test patterns change*
