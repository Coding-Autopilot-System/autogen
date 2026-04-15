# Codebase Concerns

**Analysis Date:** 2026-03-26

## Tech Debt

**Split runtime and schema surfaces:**
- Issue: The active operator shell, the shared `/api/v1` control plane, and the legacy dashboard still carry overlapping run contracts, file stores, and lifecycle concepts instead of one authoritative runtime.
- Files: `command_center/app.py`, `maf_core/control_plane/contracts.py`, `maf_core/control_plane/store.py`, `autogen_dashboard/app.py`, `autogen_dashboard/schemas.py`, `autogen_dashboard/session_store.py`, `autogen_dashboard/session_runner.py`
- Impact: State-shape drift is already visible. `tests/test_phase6_api_contract.py` and `tests/test_phase6_command_center_parity.py` move `state/sessions` aside to avoid schema conflicts. Concurrent maintenance raises break risk across UI, API, and persisted artifacts.
- Fix approach: Pick one durable run contract and store, then adapter-wrap the legacy path until it can be retired.

**AG-UI and `/api/v1` are not the same execution path:**
- Issue: The Command Center shell streams AG-UI sessions directly, while `/api/v1` helpers are only exported on `window.CommandCenterAPI` and do not drive the main interactive flow.
- Files: `command_center/static/app.js`, `command_center/app.py`, `maf_core/control_plane/service.py`
- Impact: Operators can see one live interaction model in the UI and a different durable run model in the external API. Delivery claims of parity are stronger than the current implementation.
- Fix approach: Route the primary UI through the same run service, or explicitly separate the interactive stream surface from the durable run API.

## Known Bugs

**Cloud auth mode is selectable but not implemented:**
- Symptoms: Setting `AUTH_POLICY=azure-functions` makes `/api/v1` authentication depend on `AzureFunctionsAuthPolicy.require_auth`, which raises `NotImplementedError`.
- Files: `maf_core/control_plane/auth.py`
- Trigger: Start the API with `AUTH_POLICY=azure-functions`.
- Workaround: Keep `AUTH_POLICY=none` for local-only use. Do not treat the current control plane as cloud-ready.

**`/api/v1` actions advance state without executing work:**
- Symptoms: `continue`, `approve`, and `retry` mark runs as `running` and append events, but the real execution engine is stubbed out and `_execute_run` is never invoked.
- Files: `maf_core/control_plane/service.py`, `command_center/static/app.js`
- Trigger: Use `/api/v1/runs/*/actions/*` or build against `window.CommandCenterAPI`.
- Workaround: Use AG-UI endpoints or the legacy `autogen_dashboard.session_runner.SessionService` for actual execution.

## Security Considerations

**No auth policy does not enforce loopback and metadata endpoints stay open:**
- Risk: `NoAuthPolicy` always returns a local caller identity without checking source address, while `command_center/app.py` also exposes `/api/catalog`, `/api/repos`, and `/api/status` without auth.
- Files: `maf_core/control_plane/auth.py`, `maf_core/control_plane/router.py`, `command_center/app.py`, `maf_core/cli.py`
- Current mitigation: CLI defaults bind to `127.0.0.1` in `maf_core/cli.py`.
- Recommendations: Enforce loopback at the auth layer, gate metadata endpoints, and fail closed when host binding is not local.

**External run creation accepts arbitrary local paths:**
- Risk: `RunService.create_run` accepts `request.repo_root` and only checks `Path.exists()`. Unlike the AG-UI repo selector, `/api/v1` does not constrain repo paths to the configured scan root.
- Files: `maf_core/control_plane/service.py`, `command_center/app.py`, `autogen_dashboard/repo_context.py`
- Current mitigation: None in the `/api/v1` path beyond existence checks.
- Recommendations: Reuse `resolve_repo_root(...)` or an equivalent allowlist for every API entrypoint that accepts a repo root.

**Approval and write blocking are shallow for enterprise repos:**
- Risk: `classify_write_operations(...)` treats all `create_file`, `update_file`, and `append_file` actions as `routine_safe` unless they hit a small blocked path list. Secrets beyond `.env*`, CI files, policy files, deployment manifests, and workflow definitions are not specially gated.
- Files: `maf_core/approval_policy.py`, `maf_core/tools.py`, `maf_core/repo_execution.py`
- Current mitigation: Writes cannot escape the repo root and block `.git`, `.venv`, `state`, and `.env*`.
- Recommendations: Add path-class risk tiers for infra, CI/CD, auth, secrets, and public-surface files, then require explicit approval for those classes.

## Performance Bottlenecks

**Repo discovery and context collection are synchronous and scale poorly:**
- Problem: `_discover_repos_fast(...)` scans the parent tree and calls `collect_repo_context(...)` for each candidate on every `/api/repos` request. `build_repo_context_snapshot(...)` also counts repo files recursively.
- Files: `command_center/app.py`, `autogen_dashboard/repo_context.py`, `maf_core/tools.py`
- Cause: No caching, background indexing, or bounded git/context sampling beyond directory filters.
- Improvement path: Cache repo inventory, debounce refreshes, and move heavier git/context collection off the request path.

## Fragile Areas

**Provider fallback is not capability-preserving and only covers narrow failure shapes:**
- Files: `maf_core/provider_fallback.py`, `maf_core/routing_policy.py`, `maf_core/worker_delegation.py`
- Why fragile: CLI fallback strips tool availability (`tools_available=False`), flattens multi-turn tool context into a plain prompt, only retries on string-matched quota and rate-limit errors, and only falls back in streaming before the first emitted token.
- Safe modification: Treat fallback targets as separate capability tiers and add tests for tool-use loss, mid-stream failure, and non-quota transient errors before extending the chain.
- Test coverage: `tests/test_maf_setup.py` covers metadata decoration and pre-first-token streaming fallback, but not mid-stream recovery or tool-call parity.

**The control-plane file store is atomic per file but not coordinated across callers:**
- Files: `maf_core/control_plane/store.py`, `maf_core/control_plane/service.py`, `autogen_dashboard/session_runner.py`
- Why fragile: JSON writes use atomic replace, but the control-plane service has no per-run locks, background worker ownership, or optimistic concurrency. The legacy runtime does use `asyncio.Lock` and `Condition`, so behavior can diverge under concurrent actions.
- Safe modification: Add per-run coordination tokens or a worker owner before allowing concurrent API callers.
- Test coverage: `tests/test_run_persistence.py` verifies atomic temp-file cleanup for the legacy store only. There is no concurrency test for `RunStore` or `RunService`.

**The legacy dashboard remains a monolithic frontend and a parallel operator surface:**
- Files: `autogen_dashboard/static/app.js`, `autogen_dashboard/static/index.html`, `command_center/static/app.js`, `command_center/static/components/inspector.js`
- Why fragile: The legacy dashboard still carries a 3395-line DOM script, while the current shell still depends on global mutable state plus manual DOM wiring. UI contract drift is easy while both surfaces remain live in-tree.
- Safe modification: Freeze `autogen_dashboard/` except for break-fix, and keep new operator features inside the smaller `command_center/static/components/*` split.
- Test coverage: `tests/test_command_center.py` only smoke-tests shell and API HTML. No browser-level tests protect Command Center interaction paths.

**DevUI customization remains version-coupled:**
- Files: `maf_core/devui_patches.py`, `maf_core/devui_overrides.py`, `maf_core/cli.py`
- Why fragile: The local operator story still auto-starts a patched debug DevUI sidecar and relies on string-level UI rewrites against upstream DevUI assets.
- Safe modification: Treat DevUI as optional debug tooling, not a product dependency, and isolate patching behind version checks.
- Test coverage: `tests/test_maf_setup.py` covers patch text expectations but not upstream package drift.

## Scaling Limits

**Current capacity is one workstation-oriented runtime, not a multi-user control plane:**
- Current capacity: One local filesystem root, one `state/` tree, locally installed CLI executables, and loopback-oriented server defaults.
- Limit: Multi-user, remote, or elastic hosting breaks on local repo access, filesystem-backed checkpoints, unimplemented auth, and CLI subprocess execution.
- Scaling path: Split API, durable store, and worker execution. Replace local CLI dependence with service-backed workers or isolated job runners.

## Dependencies at Risk

**CLI worker availability and preview model defaults are workstation assumptions:**
- Risk: `gemini.cmd`, `claude`, `codex.cmd`, and preview Gemini model IDs are compiled into config and routing defaults.
- Impact: Missing binaries or retired model IDs change fallback behavior at runtime, often after the primary provider has already failed.
- Migration plan: Validate provider inventory at startup, move model catalogs out of code, and treat CLI workers as optional capabilities with health gates.

## Missing Critical Features

**Production-grade observability is largely absent:**
- Problem: `structlog` is configured but lightly used, `prometheus-fastapi-instrumentator` is declared but not wired, and no trace or metric export exists for request latency, provider retries, approval latency, or run recovery.
- Blocks: Reliable SRE monitoring, cloud deployment hardening, and incident triage across AG-UI, `/api/v1`, and legacy runtime paths.
- Files: `maf_core/logging.py`, `maf_core/cli.py`, `requirements.txt`, `command_center/app.py`, `maf_core/provider_fallback.py`

**The extracted control plane is not yet a durable execution plane:**
- Problem: `RunService` persists metadata and events but does not own actual orchestration, resume, or worker execution.
- Blocks: Safe external automation, reliable retries, and a cloud-hostable manager/worker split.
- Files: `maf_core/control_plane/service.py`, `maf_core/control_plane/router.py`, `autogen_dashboard/session_runner.py`

## Test Coverage Gaps

**Auth and exposure paths are untested:**
- What is not tested: `NoAuthPolicy` loopback assumptions, failure behavior for `AUTH_POLICY=azure-functions`, and protection of unauthenticated metadata endpoints.
- Files: `maf_core/control_plane/auth.py`, `command_center/app.py`, `tests/test_phase6_api_contract.py`
- Risk: A future deployment can expose local-only surfaces without failing fast in CI.
- Priority: High

**Command Center interaction is not browser-tested:**
- What is not tested: The real browser flow that creates or resumes AG-UI sessions, processes interrupts, and renders inspector state from live streaming events.
- Files: `command_center/static/app.js`, `command_center/static/components/inspector.js`, `tests/test_command_center.py`
- Risk: Product-shell regressions can slip past the current HTML and API smoke tests.
- Priority: High

**Control-plane durability is only contract-tested, not recovery-tested:**
- What is not tested: Concurrent `/api/v1` callers, crash recovery between state transitions, and consistency between `/api/v1` persisted runs and AG-UI live sessions.
- Files: `maf_core/control_plane/store.py`, `maf_core/control_plane/service.py`, `tests/test_phase6_api_contract.py`, `tests/test_phase6_command_center_parity.py`
- Risk: Delivery and cloud-readiness issues stay hidden until real operators or automation hit the same run simultaneously.
- Priority: High

---

*Concerns audit: 2026-03-26*
