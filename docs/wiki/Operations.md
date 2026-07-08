# Operations

## Setup

```powershell
git clone https://github.com/Coding-Autopilot-System/autogen.git
Set-Location autogen
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

If you are running from WSL/Linux, do not install into the system interpreter. This repo expects
an isolated `.venv`; distro Python can be PEP 668 managed and will either reject direct package
installs or produce non-reproducible verification results.

## Run

```powershell
.\.venv\Scripts\python.exe main.py providers
.\.venv\Scripts\python.exe main.py dashboard --host 127.0.0.1 --port 8000
```

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short
```

Contract-compatibility gate only (consumer-side check against the pinned `cas-contracts` v1.1
release):

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_contract_compatibility.py -q --tb=short
```

## CI (`.github/workflows/ci.yml`, matrix: ubuntu-latest + windows-latest, Python 3.12, 20-minute timeout)

1. `actions/checkout` pinned to a full commit SHA
2. `actions/setup-python` pinned to a full commit SHA (Python 3.12, pip cache)
3. `pip install -r requirements.txt`
4. `pip check` — dependency consistency
5. **Contract compatibility** — `tests/test_contract_compatibility.py`, fails red on pinned-contract drift
6. **Run full test suite** — installs `pytest-cov`, runs `pytest --cov=. --cov-report=xml` (coverage is measured; no `--cov-fail-under` threshold is enforced on `main` yet — see [Architecture](./Architecture.md) and PR #11)
7. `python -m compileall autogen_starter autogen_dashboard maf_starter main.py -q`
8. `node --check autogen_dashboard/static/app.js` — legacy dashboard JS syntax check

A separate `.github/workflows/codeql.yml` runs CodeQL analysis (badge in the root `README.md`).

<!-- docs-verified: 91d12d3 2026-07-08 -->
