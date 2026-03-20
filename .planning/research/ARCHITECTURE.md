# Architecture Research

**Research Date:** 2026-03-20

## Recommended Direction

This platform should keep a headless orchestration core and expose it through thin local and remote surfaces. The right near-term shape is:

`manager workflow -> specialist agents/workflows -> typed tools/policies -> checkpoint/state/trace store`

DevUI and CLI remain local operator surfaces, while Azure Functions and REST come later as adapters rather than rewrites.

## Core Architecture

| Layer | Responsibility | Guidance |
| --- | --- | --- |
| Orchestration core | Task decomposition, stage transitions, retry/fallback, final output | Keep Microsoft Agent Framework as the runtime. Use workflows for explicit repo jobs and agents for dynamic reasoning. |
| Stable backend contract | One callable entrypoint for UI, CLI, and API | Wrap the main multi-agent workflow as an agent-like surface so every client calls the same contract. |
| Specialist execution | Planner, researcher, implementer, reviewer, optional fan-out research | Start sequential. Add parallel fan-out only for independent subtasks. |
| Tool and policy boundary | Filesystem, git, shell, tests, network, approvals | Keep side effects at the boundary and make approval/policy checks explicit. |
| State and artifacts | Sessions, checkpoints, traces, approvals, outputs | File checkpoints are fine locally; hide storage behind an interface so durable Azure storage can replace it later. |
| Surfaces | DevUI, custom operator UI, CLI, REST/Azure Functions | Surfaces should render and submit runs, not contain orchestration logic. |

## Workflow and HITL Patterns

- Use a manager agent for intake, clarification, and workflow selection, then hand repo-changing work to a typed workflow.
- Keep the current `planner -> researcher -> implementer -> reviewer` sequence as the default execution spine.
- Use workflow request/response patterns for approve, reject, revise, and missing-context pauses. Reserve tool-level approval for immediate local guardrails.
- Persist pending approvals as first-class state so runs can pause, resume, and survive restart.
- Add parallel research or validation stages only after traces, checkpoints, and approval flows are reliable.
- Treat provider capability differences as routing policy. Tool-heavy edit stages should prefer providers that preserve tool contracts.

## Local UI vs Custom UI

- Keep DevUI as the default local discovery, debugging, and trace surface.
- Do not treat DevUI as the long-term product UI; Microsoft documents it as a sample app for development rather than production use.
- Build a custom operator UI when you need approval inboxes, resumable job lists, per-agent stage views, artifact browsing, durable auth, or product-grade presentation.
- Keep the backend contract UI-agnostic so DevUI, a custom web app, and REST clients can all drive the same orchestration entrypoint.

## Azure Functions and REST Path

- Add a thin HTTP facade only after the local orchestration contract is stable.
- Use HTTP-triggered functions for short synchronous requests or for job submission that returns a run ID immediately.
- Use Agent Framework's Azure Functions durable integration for long-running multi-agent jobs, retries, and human wait states.
- Keep orchestrator code deterministic and move file I/O, network calls, git, and shell work into activities or tool workers.
- Plan for externalized state, artifacts, and traces when moving off the local machine.

## Repo-Specific Implications

- Standardize on the current MAF-first path as the primary runtime boundary.
- Treat the legacy AutoGen dashboard/runtime as migration debt unless it becomes the intentional custom UI or API host.
- Invest first in stable contracts, approval state, and observability before spending heavily on visual polish.

## Suggested Build Order

| Phase | Goal | Exit Criteria |
| --- | --- | --- |
| 1 | Stabilize the orchestration core | One manager-led workflow with structured input/output, clear stage boundaries, and a run ID |
| 2 | Unify state and observability | Checkpoints, traces, artifacts, and approval records survive restart and are easy to inspect |
| 3 | Harden HITL and policy | Structured approval payloads, timeout/escalation paths, and policy-aware tool execution |
| 4 | Improve the operator experience | Better local DevUI overlays or a custom UI for stage views, approvals, and artifacts |
| 5 | Harden execution reliability | Idempotent edit/test workers, provider-aware routing, and safer fallback behavior |
| 6 | Add REST and Azure Functions exposure | Thin API facade for run submission/status plus durable orchestration for long jobs |

## Sources Considered

- https://learn.microsoft.com/en-us/agent-framework/overview/?pivots=programming-language-python
- https://learn.microsoft.com/en-us/agent-framework/workflows/
- https://learn.microsoft.com/en-us/agent-framework/workflows/as-agents
- https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop
- https://learn.microsoft.com/en-us/agent-framework/devui/
- https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/security
- https://learn.microsoft.com/en-us/agent-framework/devui/tracing
- https://learn.microsoft.com/en-us/agent-framework/integrations/azure-functions
- https://learn.microsoft.com/en-us/azure/azure-functions/functions-bindings-http-webhook-trigger
- https://learn.microsoft.com/en-us/azure/azure-functions/performance-reliability
- https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-code-constraints
