# Pitfall Research

**Domain:** Azure Functions control plane for long-running repo orchestration
**Researched:** 2026-03-22
**Confidence:** HIGH

## Critical Pitfalls

### 1. Treating HTTP requests as the full run lifetime

**Why it fails:**
- Repo orchestration, validation, and pause/resume flows are too long-lived for a single synchronous HTTP request
- Azure Functions guidance explicitly pushes long-running workflows toward Durable Functions and async HTTP patterns

**Prevention:**
- Start runs asynchronously
- Return durable run identifiers and status endpoints immediately
- Keep stage progression in durable state, not in one request thread

**Phase impact:** Must be addressed in the first cloud-API and Azure-hosting phases

### 2. Assuming local CLI providers exist in cloud

**Why it fails:**
- Gemini CLI, Claude CLI, and Codex CLI rely on local login sessions and workstation tooling
- Azure Functions hosts will not have those desktop-bound sessions or repo-local assumptions

**Prevention:**
- Make provider capability profile explicit
- Prefer API-backed providers in cloud mode
- Treat CLI providers as local worker-only capabilities unless deliberately hosted elsewhere

**Phase impact:** Must be addressed when introducing worker profiles and route policies

### 3. Using ephemeral local disk as authoritative cloud state

**Why it fails:**
- Azure Functions instances are stateless and can restart or move
- Durable run history, artifacts, and pause state will drift or disappear if they only live on local disk

**Prevention:**
- Use durable orchestration state and cloud-safe artifact storage contracts
- Keep file-backed storage only as a development profile, not the cloud source of truth

**Phase impact:** Affects API, Azure-host, and worker-boundary phases

### 4. Targeting unsupported or unstable Python runtime for hosted deployment

**Why it fails:**
- The local machine is on Python `3.14.2`, but Azure Functions support for Python `3.14` is preview
- Hosted rollout on a preview target adds unnecessary risk

**Prevention:**
- Target Python `3.13` GA or `3.12` GA for the Functions host
- Keep local `3.14` only as a development convenience until cloud support stabilizes

**Phase impact:** Must be addressed in the host-setup phase before packaging or deployment work

### 5. Building a second runtime instead of a second host

**Why it fails:**
- A cloud-only API that reimplements orchestration logic separately from the Operator Workbench will drift immediately
- Fixes to routing, stages, approvals, and artifacts would need to be duplicated

**Prevention:**
- Extract shared orchestration services first
- Make UI and API clients over the same run contract
- Keep host-specific code thin

**Phase impact:** Should shape all phases in this milestone

### 6. Leaving auth and capability errors implicit

**Why it fails:**
- Cloud callers need explicit signals when an action is unauthorized or requires a worker capability that is unavailable
- Silent fallback or generic errors destroy operator trust

**Prevention:**
- Add explicit auth configuration and explicit unsupported-capability responses
- Surface worker requirements and route downgrades in both API and UI

**Phase impact:** Must be addressed by the time the Functions host exposes public HTTP routes

## Sources

- https://learn.microsoft.com/en-us/agent-framework/integrations/azure-functions
- https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-http-features
- https://learn.microsoft.com/en-us/azure/azure-functions/functions-best-practices
- https://learn.microsoft.com/ko-kr/azure/azure-functions/functions-versions

---
*Pitfall research for: Azure Functions orchestration control plane*
*Researched: 2026-03-22*
