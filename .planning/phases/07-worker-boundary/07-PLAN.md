# Phase 07 Plan: Worker Boundary and Cloud-Safe Execution Profiles

**Phase**: 07 — Worker Boundary and Cloud-Safe Execution Profiles
**Goal**: Make long-running execution explicit and safe when the control plane is hosted away from the local workstation. Separate cloud ingress from local-only providers.
**Requirements**: WRKR-01, WRKR-02, WRKR-03

## Context

Phase 6 delivered a stable REST API and shared orchestration contract. Phase 7 introduces a worker boundary so HTTP ingress never waits on long-running repo execution, and adds execution profiles so cloud-hosted runs can explicitly reject local-only subprocess providers.

The local execution path is preserved intact. Cloud-safe is strictly opt-in via `--profile cloud-safe`.

## Plans

### 07-01: Worker boundary and background run dispatch contract

**Files created:**
- `maf_starter/worker_boundary.py` — `WorkerProfile` enum (LOCAL, CLOUD_SAFE), `WorkerBoundary` class with async dispatch and run status
- `tests/test_worker_boundary.py` — unit tests for submit_async, get_status, done/pending states

**Design decisions:**
- `WorkerBoundary.submit_async(run_id, workflow)` dispatches via `asyncio.create_task` — no new dependencies
- Status is tracked in a plain dict keyed by run_id; values are `"pending"`, `"running"`, `"done"`, or `"error:<message>"`
- `submit_async` returns immediately with the run_id so the HTTP layer is never blocked
- `WorkerProfile` is a string enum to allow clean serialization and CLI parsing

### 07-02: Cloud-safe provider and execution profiles

**Files created / modified:**
- `maf_starter/execution_profile.py` — `ExecutionProfile` dataclass, `CLOUD_SAFE_PROFILE` and `LOCAL_PROFILE` constants, `IncompatibleProviderError`
- `maf_starter/provider_fallback.py` — guard added at the top of `_execute_chain_step` to reject subprocess providers when profile is CLOUD_SAFE
- `maf_starter/devui_overrides.py` — `--profile` CLI flag added (choices: local, cloud-safe; default: local) wired through to settings context
- `tests/test_execution_profile.py` — unit tests for profile enforcement and IncompatibleProviderError

**Design decisions:**
- `IncompatibleProviderError(RuntimeError)` carries provider name and profile name in a clear message
- Subprocess providers are `gemini-cli`, `claude-cli`, `codex-cli` — same set already used throughout `provider_fallback.py`
- LOCAL profile imposes no restrictions; CLOUD_SAFE rejects all subprocess providers on first check before any subprocess is spawned
- `ExecutionProfile` is a frozen dataclass with `profile: WorkerProfile` and `capabilities: tuple[str, ...]`
- `CLOUD_SAFE_PROFILE` capabilities list: `["api-only", "no-subprocess"]`
- `LOCAL_PROFILE` capabilities list: `["api", "subprocess", "repo-execution"]`

### 07-03: End-to-end validation

**Files created / modified:**
- `tests/test_phase7_e2e.py` — three integration tests:
  1. Cloud-safe profile rejects gemini-cli subprocess provider with `IncompatibleProviderError`
  2. Local profile accepts all providers (gemini, anthropic, gemini-cli, claude-cli, codex-cli)
  3. Async dispatch via `WorkerBoundary.submit_async` returns run_id immediately without blocking
- `STATE.md` updated: Phase 7 marked complete

## Verification

All tests pass with:
```
cd C:\PersonalRepo\portfolio\autogen && python -m pytest tests/ -v
```

## Constraints

- No new pip dependencies — asyncio and stdlib only
- Local path unchanged — subprocess providers still work under LOCAL profile
- `IncompatibleProviderError` is informative: `"Provider {name} requires subprocess access which is not available in cloud-safe profile"`
- snake_case modules, PascalCase dataclasses, UPPER_SNAKE_CASE module constants — consistent with existing maf_starter patterns
