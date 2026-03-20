# Pitfalls

**Research Date:** 2026-03-20

Phase names below are suggested delivery buckets, since `PROJECT.md` defines goals but not named phases yet.

## DevUI used as a product UI

- Warning signs: DevUI or the legacy dashboard gets bound beyond `127.0.0.1`; operators rely on DevUI as the durable approval or audit surface; remote access is added before auth, tenancy, or deployment hardening exists.
- Prevention strategy: Treat DevUI as a local debugging surface only, keep it loopback-only, and plan a separate operator UI before any shared or remote usage.
- Phase: Runtime and Security Hardening

## Routing and fallback capability drift

- Warning signs: the same prompt behaves differently across runs; traces show fallback but missing tool results; CLI fallback answers are accepted even when the original route required tools; model probes start failing because hardcoded IDs moved.
- Prevention strategy: Maintain a central provider and model catalog with capability metadata, probe it on startup and in CI, and fail closed when a route needs tools that a fallback cannot provide. Surface `active_provider`, `active_model`, `fallback_used`, and `tools_available` in the UI and logs for every turn.
- Phase: Runtime and Security Hardening

## Secret and artifact exposure

- Warning signs: repo tools can list or read `.env`, `local.settings.json`, `state/`, or root log files; prompts or traces contain tokens, paths, or approval payloads; CLI subprocesses inherit more environment than they need.
- Prevention strategy: Add an explicit denylist for secret-bearing files and generated artifacts, redact stored traces, minimize environment inheritance into subprocesses, and treat local artifacts as sensitive data. For cloud paths, use app settings and Key Vault references instead of checked-in secrets.
- Phase: Runtime and Security Hardening

## Brittle UI patching against private DevUI internals

- Warning signs: a DevUI upgrade makes route panels disappear, hard refresh changes behavior, or server-side tests still pass while the browser render regresses.
- Prevention strategy: Keep DevUI pinned, add explicit version or bundle-signature assertions, and back the patch with browser smoke tests instead of string-only tests. Move product UX into a custom front end once the operator surface matters.
- Phase: Operator UI Foundation

## Autonomous edit and command blast radius

- Warning signs: the manager edits unrelated files, produces large diffs without a narrow plan, skips targeted validation, or continues through fallback paths with weaker guarantees than the primary provider.
- Prevention strategy: Isolate runs in a branch, worktree, or sandbox; require a plan, diff summary, and targeted tests before applying write-heavy changes; and reserve human approval for destructive, privileged, or secret-touching actions.
- Phase: Autonomous Execution Safety

## Repo-scale performance collapse

- Warning signs: first-turn latency grows with repo size, `rglob()` and literal-text scans dominate runtime, CPU spikes during repeated searches, and large generated or vendored trees pollute UI and model context.
- Prevention strategy: Replace naive recursive scanning with indexed or `rg`-based search, expand ignore rules for generated and high-volume paths, cache repo inventory and git summaries, and cap file size and match volume before sending content to agents.
- Phase: Repo-Scale Performance

## Local-first design carried directly into cloud hosting

- Warning signs: the architecture assumes Windows executables such as `gemini.cmd` or `codex.cmd`, writable local `state/` directories, browser-driven approvals, or long-lived in-process orchestration loops, and an HTTP or Azure wrapper tries to preserve the same runtime shape.
- Prevention strategy: Keep orchestration core logic headless and portable, externalize checkpoints and approvals, and separate control-plane APIs from long-running worker execution. Validate Linux-compatible dependencies and config parity early, and treat Azure Functions as a thin entry surface unless the workflow duration and toolchain truly fit.
- Phase: Cloud Readiness

## Sources Considered

- https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/security
- https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop
- https://learn.microsoft.com/en-us/azure/azure-functions/functions-scale
- https://learn.microsoft.com/en-us/azure/azure-functions/functions-develop-vs-code
- https://learn.microsoft.com/en-us/azure/app-service/app-service-key-vault-references
- https://docs.github.com/en/code-security/secret-scanning/enabling-secret-scanning-features/enabling-push-protection-for-your-repository
- https://ai.google.dev/gemini-api/docs/models
- https://ai.google.dev/gemini-api/docs/function-calling
- https://platform.openai.com/docs/guides/tools-shell
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool
