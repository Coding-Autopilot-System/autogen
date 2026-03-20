# Stack Research

**Research Date:** 2026-03-20

## Recommended Stack Direction

This product should stay local-first, Python-first, and workflow-first. The current repo already has the right base primitives: Microsoft Agent Framework for orchestration, DevUI for local debugging, Gemini API access, and local CLI specialists. The right move is to harden and productize that path instead of replacing it.

## Recommended Stack

| Area | Recommendation | Why |
| --- | --- | --- |
| Core runtime | Python + Microsoft Agent Framework workflows | The product needs explicit steps, checkpoints, and human gates more than free-form chat alone. |
| Deterministic execution | Plain Python executors/functions for repo tools, routing, file ops, validation, and approvals | Keep non-agentic work programmable and reliable. |
| Composition boundary | Wrap the main workflow as an agent | One orchestration can then serve DevUI, CLI, REST, and later Azure Functions without duplicating logic. |
| Local runtime | Windows-first local process with repo-mounted tools and installed CLIs | Local repo access, git state, shell tools, and human approval are core product advantages. |
| State | File checkpoints locally, with a pluggable persistence boundary | Fits local development now while keeping a migration path to durable cloud state later. |
| Observability | OpenTelemetry-first traces plus route metadata | DevUI already surfaces traces locally, and OTLP export can later flow to Azure Monitor. |
| Engineering UI | Keep DevUI as the engineering console | Good for discovery, debugging, tracing, and iteration. |
| Product UI | Build a custom operator UI | DevUI is a local sample app, not the long-term product surface. |
| Custom UI stack | TypeScript/React over a thin Python ASGI API | Best fit for live per-agent activity, approvals, route cards, resumable sessions, and streaming output. |
| Cloud path | Azure Functions durable integration on Flex Consumption | Strong later-stage serverless path for remote HTTP entry, durable threads, and long-running orchestration. |
| Functions structure | Python v2 programming model plus blueprints | Current Microsoft guidance for modular Python Azure Functions apps. |

## Orchestration Guidance

- Use a sequential `manager -> researcher -> implementer -> reviewer` workflow as the default repo-work pattern.
- Add concurrent branches only for clearly independent fan-out work such as large repo scans, parallel research, or validation checks.
- Keep tool execution, repo reads/writes, and approval gates outside the model whenever possible.
- Preserve a clean workflow-agent boundary so the same orchestration can power DevUI today and REST/Azure Functions later.

## Local vs Cloud Hosting

| Keep local by default when... | Add cloud hosting when... |
| --- | --- |
| Work needs the live repo checkout, installed CLIs, shell access, human approval, or deep trace/debug loops | You need a remote HTTP entrypoint, timers/webhooks/queues, durable thread state, resumable runs, or a shared operator endpoint |
| The operator is the primary user and the machine is the trusted execution environment | You want service-style invocation without exposing the whole local workstation |
| Fast iteration matters more than remote availability | You are ready to isolate credentials, sandbox tool execution, and define repo/materialization rules |

Guidance: do not move the repo-editing worker tier to Azure first. Move the entrypoint and durable session layer first, and keep the heavy repo/tool runner local until sandboxing, checkout strategy, and credential boundaries are explicit.

## Model Routing Implications

| Route | Recommended default | Notes |
| --- | --- | --- |
| High-reasoning manager, planner, and reviewer turns | `gemini-2.5-pro` | Stable, strongest current non-preview choice for complex coding and reasoning. |
| Default interactive worker turns | `gemini-2.5-flash` | Best price/performance lane for most orchestration and coding turns. |
| Cheap bulk status or summarization turns | `gemini-2.5-flash-lite` | Good fit for high-throughput scan, summarization, and trace compression work. |
| Preview experimentation lane | Preview Gemini models as opt-in only | Preview models move faster and should not be the hardcoded default. |
| Local resilience lane | Gemini CLI, Codex CLI, Claude CLI | Keep these last in the chain; useful for resilience or specialist execution, not as the default orchestration lane. |

Additional guidance:

- Keep the current OpenAI-compatible Gemini path for near-term MAF compatibility, but preserve a provider abstraction.
- Use explicit stable model strings for core workflows rather than `latest` aliases.
- Treat preview models as selectable operator lanes, not implicit defaults.

## Sources Considered

- https://learn.microsoft.com/en-us/agent-framework/overview/
- https://learn.microsoft.com/en-us/agent-framework/workflows/orchestrations/
- https://learn.microsoft.com/en-us/agent-framework/workflows/as-agents
- https://learn.microsoft.com/en-us/agent-framework/devui/
- https://learn.microsoft.com/en-us/agent-framework/devui/security
- https://learn.microsoft.com/en-us/agent-framework/devui/tracing
- https://learn.microsoft.com/en-us/agent-framework/integrations/azure-functions
- https://learn.microsoft.com/en-us/azure/azure-functions/flex-consumption-plan
- https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python
- https://ai.google.dev/gemini-api/docs/openai
- https://ai.google.dev/gemini-api/docs/function-calling
- https://ai.google.dev/gemini-api/docs/models
