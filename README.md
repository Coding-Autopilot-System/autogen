# autogen

[![CI](https://github.com/Coding-Autopilot-System/autogen/actions/workflows/ci.yml/badge.svg)](https://github.com/Coding-Autopilot-System/autogen/actions/workflows/ci.yml) [![CodeQL](https://github.com/Coding-Autopilot-System/autogen/actions/workflows/codeql.yml/badge.svg)](https://github.com/Coding-Autopilot-System/autogen/actions/workflows/codeql.yml)


[![CI](https://github.com/Coding-Autopilot-System/autogen/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Coding-Autopilot-System/autogen/actions/workflows/ci.yml)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue)](https://www.python.org/)
[![MIT License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

Part of the [Coding-Autopilot-System](https://github.com/Coding-Autopilot-System) ecosystem:
[gsd-orchestrator](https://github.com/Coding-Autopilot-System/gsd-orchestrator) | [Promptimprover](https://github.com/Coding-Autopilot-System/Promptimprover)

`autogen` is a local-first multi-agent engineering workbench built on Microsoft Agent Framework. The product goal is simple: point the system at a real repository, give it one engineering objective, and let a manager-led workflow coordinate planning, research, implementation, review, approvals, validation, and durable artifacts with less manual steering than a chat-first coding loop.

This repository is strongest as an architecture and operator-systems portfolio piece: it shows how to turn LLM tooling into a controlled engineering runtime instead of a demo chatbot.

## Product Story

Most agent demos stop at "the model answered." `autogen` focuses on the operator problem after that:

- How do you scope agents to a real repo without letting them roam the machine?
- How do you keep a manager, specialists, and provider fallback chain inspectable?
- How do you pause for approval before destructive changes?
- How do you leave behind run artifacts, validation results, and retryable state instead of ephemeral chat output?

The answer in this codebase is a manager-led orchestration model with bounded repo tools, approval-aware execution, and a UI contract designed for traceability.

## What Exists In The Repo Today

- **Manager-led orchestration**: `entities/repo_team/workflow.py` wires a workflow for planner, researcher, implementer, reviewer, and validation-stage visibility.
- **Scoped repository operations**: `maf_starter/tools.py` enforces repo-root path boundaries, blocks writes to sensitive targets like `.env`, and limits read/search surfaces.
- **Routed provider execution**: `maf_starter/provider_fallback.py` and `maf_starter/routing_policy.py` select models by task depth and fall back across API and CLI providers when needed.
- **Approval and guardrails**: `maf_starter/approval_policy.py` classifies file operations and validation commands so destructive or externally visible actions stop for operator approval.
- **Durable run artifacts**: `autogen_dashboard/session_store.py` persists transcripts, runtime state, stage summaries, diffs, validation records, and attempt metadata.
- **Operator-facing visibility**: the dashboard contract covers timeline, routing, agents, artifacts, and approval surfaces rather than a single opaque transcript.

## Demo Scenarios

The best way to understand the product is through operator outcomes:

- **Architecture review on a real repo**: point the system at a checked-out repository and ask for a plan. The manager can retain workspace metadata, route to the right model tier, and preserve the resulting artifacts for follow-up attempts.
- **Guardrailed implementation run**: ask for a change that touches code or config. Safe edits can proceed through bounded repo tools, while destructive actions pause with an explicit approval scope.
- **Provider-resilience drill**: trigger a quota or rate-limit failure on the primary model path and inspect how the fallback chain records the route attempt history and capability changes.

## Evidence And Evaluation Posture

This repo already carries more engineering evidence than the old README surfaced:

- `tests/test_workspace_contract.py` validates workspace discovery, repo-root safety, and session creation contracts against real temporary git repos.
- `tests/test_run_persistence.py` verifies durable session layout, artifact manifests, attempts, diffs, validation outputs, and atomic persistence behavior.
- `tests/test_phase4_approval.py` proves destructive writes and externally visible commands are classified and paused behind approval.
- `tests/test_phase4_validation.py` checks that changed files produce a proportionate validation ladder including `git diff --check`, Python compile checks, unit discovery, and JavaScript syntax checks.
- `tests/test_phase5_ui_contract.py` and `tests/test_phase5_operator_views.py` lock the operator UI to timeline, routing, artifact, and specialist-view contracts.
- `.github/workflows/ci.yml` installs the declared environment and runs the full suite, Python compilation, dependency consistency, and JavaScript syntax checks on Windows and Linux.

### Test Coverage

`main`'s `Run full test suite` CI step installs `pytest-cov` and runs `pytest --cov=. --cov-report=xml`,
but does not currently fail the build on a coverage threshold. A ratcheted coverage gate is
**in progress (PR #11)**: it adds a `.coveragerc` with `branch = true` and a `--cov-fail-under`
threshold, plus branch-coverage telemetry read from the produced `coverage.xml`. Per the PR's
own recorded validation, the repo-local suite reached ~73.3% total coverage and ~54.6% branch
coverage against the ratcheted threshold. Until PR #11 merges, coverage is measured but not
enforced on `main`.

## Quickstart

The checked-in snapshot supports a clean-clone local dashboard and full validation workflow:

```powershell
git clone https://github.com/Coding-Autopilot-System/autogen.git
Set-Location autogen

python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env

.\.venv\Scripts\python.exe main.py providers
.\.venv\Scripts\python.exe main.py dashboard --host 127.0.0.1 --port 8000
```

Do not install into the system Python on WSL/Linux. That interpreter may be externally managed
under PEP 668, which blocks direct `pip install` runs and creates ambiguous test environments.
Always use the repo-local `.venv` so verification and coverage come from `requirements.txt`, not
ambient machine packages.

MAF 1.0 direction: the current operator shell still uses the local dashboard, but the
orchestration core is intentionally aligned with Microsoft Agent Framework's graph-style
workflow model. The next durable UI/runtime step is to expose the existing manager-led flow
through DevUI or AG-UI style surfaces rather than inventing a separate orchestration concept.

Run the complete regression suite before changing runtime behavior:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short
```

## Configuration
`maf_starter/config.py` is the source of truth for the active MAF configuration contract. Copy `.env.example` to `.env`, set only the providers you intend to use, and never commit API keys. The legacy dashboard launcher also reads `AUTOGEN_*` settings through `autogen_starter/config.py`.

Minimal provider and workspace settings:

```dotenv
GEMINI_API_KEY=your-gemini-api-key
MAF_REPO_ROOT=C:\path\to\target-repository
```

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `MAF_API_KEY` or `GEMINI_API_KEY` | Yes for MAF agent construction | None | API key used by the OpenAI-compatible Gemini client; `MAF_API_KEY` takes precedence. |
| `MAF_MODEL` or `GEMINI_MODEL` | No | `gemini-2.5-flash` | Primary model; the `MAF_*` name takes precedence. |
| `MAF_BASE_URL` or `GEMINI_BASE_URL` | No | Gemini OpenAI-compatible endpoint | Provider base URL; the `MAF_*` name takes precedence. |
| `MAF_REPO_ROOT` | No | Repository root | Repository exposed to bounded repo tools. The path must exist. |
| `MAF_ENTITIES_DIR` | No | `entities` | Entity discovery directory. |
| `MAF_CHECKPOINT_DIR` | No | `state\maf-checkpoints` | File-backed checkpoint location. |
| `MAF_ROUTE_LANE` | No | `auto` | Routing lane used to select task depth and provider order. |
| `MAF_REQUESTED_PROVIDER`, `MAF_REQUESTED_MODEL` | No | None | Optional explicit provider/model selection. |
| `MAF_FALLBACK_CHAIN` | No | Built-in Gemini/API/CLI chain | Comma-separated fallback steps. |
| ANTHROPIC_API_KEY, ANTHROPIC_MODEL | No | No key; claude-sonnet-4-6 model | Enables the optional Anthropic fallback when its package is installed. |
| `AUTOGEN_CORS_ORIGINS` | No | Explicit loopback origins | Comma-separated origins allowed to call the local dashboard API; wildcard CORS is rejected. |
| `GEMINI_CLI_COMMAND`, `CLAUDE_CLI_COMMAND`, `CODEX_CLI_COMMAND` | No | `gemini.cmd`, `claude`, `codex.cmd` | Executable names used by optional local CLI fallbacks. |

Additional optional model-candidate and CLI-model overrides are defined directly in `maf_starter/config.py`.

## Why This Is A Strong Hiring Signal

This project demonstrates more than framework familiarity. It shows judgment about:

- turning agent capabilities into bounded operational surfaces,
- separating operator control from model improvisation,
- preserving artifacts and retry semantics for long-running engineering work,
- designing UI and API contracts around observability instead of novelty,
- and shaping local-first tooling so it can evolve toward service boundaries later.

## Cloud-Ready Direction

`autogen` is intentionally local-first today, but its primitives already point toward a future control plane:

- durable run IDs and persisted artifacts,
- explicit pause, approve, retry, and resume semantics,
- structured route-attempt metadata,
- workspace and execution contracts that can sit behind HTTP later,
- and an orchestration core that can be split from the local operator shell.

That is the right foundation for a later Azure-hosted control plane or worker boundary without rebuilding the product concept from scratch.

## Repository Pointers

- `maf_starter/` - orchestration core, routing, fallback, repo tools, approvals, validation
- `autogen_dashboard/` - API and operator-facing session surfaces
- `entities/repo_team/` - manager-led workflow entrypoint
- `tests/` - contract, runtime, approval, persistence, and operator-view evidence
- `.planning/` - architecture notes, phased roadmap, and future control-plane direction

## License

MIT -- see [LICENSE](LICENSE)

<!-- docs-verified: 91d12d3 2026-07-08 -->
