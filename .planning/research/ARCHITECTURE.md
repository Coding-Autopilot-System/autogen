# Architecture Research

**Domain:** Cloud-ready orchestration control plane over the existing local-first runtime
**Researched:** 2026-03-22
**Confidence:** HIGH

## Recommended Architecture

The existing product should evolve into a split architecture with one canonical orchestration contract and two host profiles:

1. **Local operator profile** for the current Operator Workbench, local repo execution, and CLI-backed fallbacks
2. **Cloud control-plane profile** for HTTP ingress, durable run state, and Azure Functions hosting

The crucial rule is that these are two hosts over the same orchestration services, not two independent runtimes.

## Major Components

### Shared Orchestration Services

- Own run creation, run state, stages, pause semantics, route history, artifacts, and approvals
- Must be host-agnostic so both the dashboard and Functions app can call into the same services
- Should absorb logic that currently lives only in UI-centric or process-centric entrypoints

### HTTP Control Plane

- Azure Functions HTTP triggers expose submit, status, control, timeline, routing, agent, and artifact endpoints
- Should return durable run IDs and async-friendly status payloads
- Must not depend on browser session state or local desktop context

### Durable Execution Backbone

- Durable Functions orchestration or equivalent durable host path owns long-running run progression
- Stores run progress, stage transitions, and recovery state outside the process
- Supports async HTTP start/status patterns instead of request-held execution

### Worker Adapter Boundary

- Executes repo edits, validations, and provider calls that may not be cloud-safe
- Can map to local in-process execution for development, then later to a separate worker path for Azure
- Must advertise capability availability so routing can reject or downgrade incompatible steps

### Artifact and Status Storage

- Stores timeline events, artifacts, diffs, validation outputs, and durable run summaries
- Needs a stable contract so UI and REST callers see the same evidence
- Can begin with file-backed local storage for development but must define a cloud-safe backing model

## Integration Points with Current Repo

- `maf_starter/orchestration.py` is the right place for the canonical stage and run contract
- `autogen_dashboard/session_runner.py` already exposes a strong run model that can be extracted behind a service boundary
- `maf_starter/provider_fallback.py` and `routing_policy.py` should become execution-profile aware so cloud mode can avoid local-only routes
- The Operator Workbench should consume API responses from shared schemas instead of owning separate business logic

## Suggested Build Order

1. Extract shared control-plane services and request/response schemas from UI-specific code
2. Expose those services through local HTTP endpoints first
3. Add Azure Functions host and durable run-start/status behavior
4. Introduce explicit worker profiles and cloud-safe capability enforcement
5. Validate the same run through both the Operator Workbench and the HTTP API

## New vs Modified Components

**New components likely required:**
- Functions app entrypoint and HTTP trigger module
- Cloud-control-plane schemas and response adapters
- Worker profile / capability boundary
- Cloud-safe settings model for auth, provider policy, and storage

**Existing components to modify:**
- Run/session service layer
- Routing and fallback logic
- Artifact/state persistence boundary
- Operator Workbench API integration path

## Sources

- https://learn.microsoft.com/en-us/agent-framework/integrations/azure-functions
- https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview
- https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-http-features

---
*Architecture research for: Azure Function-hosted orchestration control plane*
*Researched: 2026-03-22*
