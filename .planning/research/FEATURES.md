# Feature Research

**Domain:** Cloud API and Azure Function hosting for a local-first orchestration platform
**Researched:** 2026-03-22
**Confidence:** HIGH

## Feature Categories

### Control-Plane API

**Table stakes:**
- Submit a run over HTTP and get back a durable run identifier
- Poll current run status, active stage, pause reason, and summary over HTTP
- Fetch timeline, routing history, agent state, validation results, and artifacts over HTTP
- Send control actions such as approve, retry, cancel, or append operator input to an existing run

**Differentiators:**
- Keep the Operator Workbench and the API on the same run contract so the UI and API can view the same run
- Return route and model metadata in the API so callers can see planned versus actual fallback behavior
- Preserve artifact and approval visibility outside the UI, not only in browser surfaces

**Anti-features:**
- Blocking HTTP requests until the full implementation run finishes
- Returning only chat text while hiding orchestration state, route history, and artifacts

### Azure Functions Hosting

**Table stakes:**
- Run the orchestration control plane under Azure Functions locally with Core Tools
- Persist run state across host restarts and long-running operations
- Expose documented HTTP routes and auth configuration suitable for local and Azure environments

**Differentiators:**
- Package the Functions host so it can move to Azure without redesigning the orchestration core
- Keep the local Operator Workbench usable against the same API and storage contract

**Anti-features:**
- Building a cloud entrypoint that can only run behind DevUI
- Treating Azure deployment as a completely separate runtime with different behavior and state

### Worker Boundary

**Table stakes:**
- Separate HTTP ingress from long-running orchestration execution
- Make worker handoff explicit so cloud mode does not assume local disk or local CLI sessions
- Support the async HTTP polling pattern for long-running runs

**Differentiators:**
- Keep local repo execution and CLI fallbacks available in a local worker profile
- Allow cloud mode to run with API-backed providers while rejecting incompatible local-only steps clearly

**Anti-features:**
- Letting the cloud control plane call local Codex, Claude, or Gemini CLI paths as if they existed in Azure
- Coupling worker execution lifetime to the HTTP request lifetime

### Access and Safety

**Table stakes:**
- Basic API protection using function auth or a configured shared secret outside local dev
- Clear error responses when an action requires a local worker or unsupported capability

**Differentiators:**
- Approval and artifact endpoints usable both from the UI and external callers
- Future-ready path to stronger shared-operator auth without redesigning the control-plane contract

**Anti-features:**
- Public unauthenticated cloud endpoints for repo-editing actions
- Implicit capability drift where a cloud caller thinks a local-only provider is available

## Complexity Notes

- Control-plane API is moderate complexity because much of the run contract already exists in the dashboard
- Azure Functions hosting is moderate-to-high complexity because the current runtime assumes a local process and repo access
- Worker separation is the highest-risk area because it forces the first clean boundary between cloud ingress and local execution assumptions

## Dependencies on Existing System

- Reuse the current stage model, run identity, artifact manifests, route history, and approval policy
- Avoid rewriting the Operator Workbench; it should consume the same control-plane responses
- Preserve local repo execution as a first-class development profile while adding cloud-safe behavior

## Sources

- https://learn.microsoft.com/en-us/agent-framework/integrations/azure-functions
- https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-http-features
- https://learn.microsoft.com/en-us/azure/azure-functions/functions-best-practices

---
*Feature research for: Cloud API and Azure Function hosting*
*Researched: 2026-03-22*
