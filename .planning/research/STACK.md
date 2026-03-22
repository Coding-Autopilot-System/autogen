# Stack Research

**Domain:** Azure Function-hosted multi-agent orchestration control plane for repo automation
**Researched:** 2026-03-22
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Azure Functions for Python | Python 3.13 GA target | HTTP control plane and Azure host | Keeps the entrypoint serverless, aligns with your Azure goal, and avoids inventing a second hosting model |
| Durable Functions | Current Azure Durable Functions extension | Durable run state, async status polling, long-running orchestration | Matches the product's existing pause/resume/run-state model and avoids tying run completion to one HTTP request |
| Microsoft Agent Framework Azure Functions integration | `agent-framework-azurefunctions --pre` | Function-hosted MAF agents and durable agent orchestration | It is the official path for hosting Agent Framework agents in Azure Functions |
| Azure Storage / Durable Task backend | Durable Task Scheduler preferred, Azure Storage compatible | Durable orchestration state and instance history | Durable orchestration needs durable storage that survives restarts and scale events |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `azure-functions` | current stable | Python function trigger and response surface | Required for the Python Azure Functions host |
| `azure-functions-durable` | current stable | Durable orchestrations and async HTTP pattern | Required when the control plane must start long-running orchestrations and return status URLs |
| `azure-identity` | current stable | Managed identity / credential flow | Use for Azure-hosted credentials instead of static secrets where possible |
| `pydantic` | existing v2 line in repo | API request and response schemas | Reuse the current structured run contracts across dashboard and HTTP API |
| `httpx` or `requests` | current stable | API smoke checks and local end-to-end verification | Use for local API tests and orchestration contract validation |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| Azure Functions Core Tools `4.8.0` | Local Functions host and trigger testing | Already installed on this machine |
| Azure CLI `2.80.0` | Azure resource setup, settings, storage, and deployment scripting | Already installed on this machine |
| Docker `29.1.5` | Local emulator support such as Azurite or other durable backing services | Already installed on this machine |
| `azd` | Optional template/bootstrap tooling | Not installed locally, so it should stay optional for this milestone |

## Installation

```bash
# Core
pip install azure-functions azure-functions-durable azure-identity
pip install agent-framework-azurefunctions --pre

# Supporting
pip install httpx

# Local tooling
func --version
az --version
docker --version
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Azure Functions + Durable Functions | Azure Container Apps / custom FastAPI host | Use a container host when you need custom runtime control or long-running worker co-location from day one |
| Durable async HTTP pattern | Synchronous HTTP request that waits for run completion | Only acceptable for very short tasks; not suitable for repo orchestration or validation-heavy flows |
| API-first providers in cloud | CLI-backed providers in cloud | Use CLI providers only in local or explicitly attached worker environments where the login session exists |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Python 3.14 as the first cloud deployment target | Azure Functions lists Python 3.14 as preview; it is not the stable target for hosted rollout | Target Python 3.13 GA or 3.12 GA for the Functions host |
| File-system-only run state in the Function host | Azure Functions instances are stateless and can restart or move between instances | Use Durable Functions state plus durable artifact storage |
| Local Gemini/Codex/Claude CLI sessions as the cloud default provider path | Those sessions and desktop assumptions do not exist in Azure Functions | Use API-backed providers in cloud and keep CLIs as local worker options |
| One giant function app that also does heavy repo execution synchronously | All functions in a function app scale together and long-running work fights the HTTP surface | Keep a control-plane app and a worker boundary, even if both start local-first |

## Stack Patterns by Variant

**If the run is local-first:**
- Keep the current Operator Workbench and local repo execution path
- Because you already have repo access, CLI providers, and direct validation tools on this machine

**If the run is Functions-hosted:**
- Use Azure Functions HTTP triggers plus Durable Functions orchestration and an explicit worker adapter
- Because the cloud host should own ingress and durable state, not direct desktop-bound execution

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Azure Functions Python target `3.13` | Durable Functions Python v2 and Core Tools v4 | Best stable cloud target based on current Azure Functions support |
| Local Python `3.14.2` | Repo development only | Fine for local tooling, but not the first hosted deployment target |
| `agent-framework-azurefunctions --pre` | Azure Functions Python host + durable agent patterns | Needed for the official MAF Azure Functions path |

## Sources

- https://learn.microsoft.com/en-us/agent-framework/integrations/azure-functions - official Agent Framework Azure Functions durable hosting path
- https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview - durable orchestration model, storage, local testing, and long-running workflow guidance
- https://learn.microsoft.com/en-us/azure/azure-functions/functions-best-practices - statelessness, storage, deployment, and long-running-function guidance
- https://learn.microsoft.com/ko-kr/azure/azure-functions/functions-versions - current Azure Functions Python version support, including Python 3.13 GA and 3.14 preview

---
*Stack research for: Azure Function-hosted orchestration control plane*
*Researched: 2026-03-22*
