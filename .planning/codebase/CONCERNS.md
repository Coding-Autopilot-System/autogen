# Codebase Concerns

## Technical Debt
- The repo still carries two meaningful runtime surfaces: the active MAF path in `maf_starter/` and the legacy AutoGen stack in `autogen_dashboard/` and `autogen_starter/`.
- `README.md` now treats `command_center/` as the primary operator UI, while `.planning/PROJECT.md` still describes `autogen_dashboard/` as the primary local product UI. That mismatch is a planning debt signal.
- `maf_starter/cli.py` still auto-starts the debug DevUI sidecar when launching the Command Center, which couples product flow to framework-debug behavior.
- `maf_starter/config.py` hard-codes model lists and CLI command defaults, so environment drift is easy to encode in code instead of config.

## Duplicated Runtime Surfaces
- `command_center/app.py` and `autogen_dashboard/app.py` both expose repo-aware orchestration APIs, but they do so with different schemas, state models, and UI expectations.
- `command_center/static/app.js` is a lighter operator shell, while `autogen_dashboard/static/app.js` still contains the deeper session-management implementation. The product has two frontends with overlapping intent.
- `maf_starter/orchestration.py` and `autogen_dashboard/session_runner.py` both model pause, retry, and stage progression, which increases drift risk for resume semantics.

## Fragile Areas
- `maf_starter/provider_fallback.py` mixes route planning, streaming wrapping, CLI subprocess execution, and metadata reshaping in one boundary module.
- `maf_starter/devui_patches.py` and `maf_starter/devui_overrides.py` remain version-coupled to DevUI internals, so small upstream changes can break local inspection behavior.
- `autogen_dashboard/session_runner.py` is a large stateful file that concentrates prompt handling, persistence, retry, and run lifecycle code in one place.
- `command_center/static/app.js` depends on a fairly implicit event contract; the shell is smaller, but the browser behavior still depends on many payload shapes staying stable.

## Provider Capability Boundaries
- `maf_starter/provider_fallback.py` explicitly drops tool calling on `gemini-cli`, `claude-cli`, and `codex-cli` fallback turns, so provider fallback is not capability-preserving.
- `maf_starter/config.py` bakes in local command names like `gemini.cmd`, `claude`, and `codex.cmd`, which makes provider availability a workstation assumption.
- `command_center/app.py` builds route previews from model names, but those previews are only as accurate as the current provider catalog and installed SDKs.
- `autogen_dashboard/session_runner.py` still assumes the legacy provider layer can surface usable statuses and retry paths across all configured backends.

## Approval And Resume Risks
- `maf_starter/approval_policy.py` uses coarse string matching for approval words and path classification, so approval semantics are easy to misread or over-approve.
- `maf_starter/orchestration.py` persists pause kinds, retry targets, and stage records, but the same concepts also exist in the legacy session runner, so resume behavior can diverge.
- `tests/test_phase1_runtime.py` and `tests/test_phase2_manager.py` cover retry and pause flows, but they do not prove crash-safe recovery after a mid-turn tool or write interruption.
- `autogen_dashboard/app.py` exposes approve, reject, run, retry, stop, and cancel endpoints, which is powerful but raises the risk of inconsistent lifecycle transitions if the runtime contract changes.

## Repo, CLI, And Environment Assumptions
- `maf_starter/config.py` requires a repo-local `.env` and a valid repo root, so local startup is tightly coupled to workstation state.
- `command_center/app.py` scans local directories for repos and assumes the operator machine can read them directly.
- `maf_starter/repo_execution.py` writes directly into the selected repo root, so execution assumes a mutable local checkout rather than an isolated worker volume.
- `README.md` assumes Windows PowerShell, a repo-local virtualenv, and locally installed CLI tools; `\\.venv\\`, `gemini.cmd`, `claude`, and `codex.cmd` are part of the normal path.
- `.planning/STATE.md` notes `azd` is absent locally, so cloud work must not silently depend on it.

## UI Gaps
- `command_center/static/index.html` and `command_center/static/styles.css` present a clean shell, but the feature depth is still thinner than `autogen_dashboard/static/index.html` and `autogen_dashboard/static/app.js`.
- `command_center/static/app.js` shows one live run and a compact approval panel, but it does not yet match the richer session list, pause banner, or workspace warning surface of the legacy dashboard.
- `tests/test_command_center.py` only checks shell and API smoke behavior; it does not exercise real browser rendering or SSE streaming in a browser.
- `tests/test_phase5_ui_contract.py` is a static contract test over files, not an end-to-end UI proof.

## Cloud Readiness Risks
- `command_center/app.py` and `maf_starter/cli.py` both assume local-host behavior, with debug DevUI wiring and local repo access baked in.
- `autogen_dashboard/app.py` still enables permissive CORS, which is acceptable for localhost but not a safe default for a broader control plane.
- `maf_starter/provider_fallback.py` shells out to local CLIs with a 240-second timeout, which is fine for a desktop worker but awkward for hosted HTTP boundaries.
- `maf_starter/orchestration.py` and `autogen_dashboard/session_runner.py` both persist state on the filesystem, so a future Azure Functions host will need an explicit durable-worker split.

## Testing Gaps
- `tests/test_command_center.py` verifies catalog and status payloads, but not the browser interaction or event streaming path in `command_center/static/app.js`.
- `tests/test_phase4_write_execution.py` covers blocked paths and diff capture in `maf_starter/repo_execution.py`, but not a full repo-execution lifecycle through `maf_starter/provider_fallback.py` plus `maf_starter/orchestration.py`.
- `tests/test_phase5_ui_contract.py` checks selectors and helper names in `autogen_dashboard/static/app.js`, but it does not validate rendered DOM or responsive behavior.
- There is no dedicated test proving the cloud-control-plane assumptions in `.planning/PROJECT.md` or the worker-boundary split implied by `command_center/app.py`.

## Watchlist
- Keep an eye on `README.md`, `.planning/PROJECT.md`, and `.planning/STATE.md` whenever the primary UI or runtime ownership changes.
- Treat `autogen_dashboard/` as frozen unless a specific legacy behavior still depends on it.
- Re-check `maf_starter/provider_fallback.py` and `maf_starter/approval_policy.py` whenever provider catalogs or approval rules change.
