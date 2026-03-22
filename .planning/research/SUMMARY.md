# Project Research Summary

**Project:** GSD Orchestration Platform
**Domain:** Cloud API and Azure Function hosting for a local-first multi-agent orchestration platform
**Researched:** 2026-03-22
**Confidence:** HIGH

## Executive Summary

The strongest next milestone is not more UI polish. It is extracting the current orchestration contract into a real control plane that can be driven over HTTP and hosted by Azure Functions without forking the product into a second runtime. The current code already has the important local foundations: durable run identity, manager stages, specialist visibility, route history, artifacts, approvals, and a polished operator workbench. That existing contract should become the API contract.

Official Microsoft guidance aligns with that direction. Agent Framework now has an Azure Functions durable-hosting path, and Azure Durable Functions is explicitly built for long-running, stateful, replayable workflows with async HTTP status patterns. That maps directly onto this product's pause/resume, review, validation, and long-running repo-work model. The biggest risk is not hosting itself; it is accidentally assuming the cloud host can behave like the local workstation. It cannot. Cloud mode needs a control plane and an explicit worker boundary.

## Key Findings

### Recommended Stack

Use a Python Azure Functions host as the public control plane, Durable Functions as the durable execution/state backbone, and the Agent Framework Azure Functions integration as the official MAF hosting path. Keep API-backed providers as the cloud default and treat local CLIs as worker-only capabilities. Target Python `3.13` for hosted work even though the local machine is on `3.14.2`.

**Core technologies:**
- Azure Functions for Python: HTTP ingress and Azure hosting surface
- Durable Functions: async long-running run lifecycle and durable state
- `agent-framework-azurefunctions --pre`: official MAF durable hosting path
- Azure Storage / Durable Task backend: persisted orchestration history and recovery

### Expected Features

**Must have (table stakes):**
- Submit, status, control, timeline, routing, and artifact HTTP endpoints
- Durable run identifiers and async status behavior
- Azure Functions local-host support via Core Tools
- Explicit worker boundary for long-running repo execution

**Should have (competitive):**
- API and Operator Workbench reading the same run contract
- Route/model/fallback visibility outside the UI
- Clear capability errors when a cloud request needs a local worker path

**Defer (v2+):**
- Shared multi-user auth model beyond basic protected endpoints
- Full cloud-hosted repo worker plane with isolated branch/worktree execution by default

### Architecture Approach

The correct architecture is a shared orchestration service layer with two hosts: the local Operator Workbench and the Functions-hosted HTTP control plane. The Functions host should stay thin and durable, while a worker adapter boundary owns repo execution, validations, and provider capabilities that differ between local and cloud environments.

**Major components:**
1. Shared orchestration services - run creation, stage progression, pause semantics, approvals, routing, artifacts
2. Azure Functions HTTP control plane - submit/status/control/artifact endpoints
3. Durable execution backbone - long-running orchestration state and async status pattern
4. Worker adapter boundary - local worker today, cloud-safe worker profile later

### Critical Pitfalls

1. **Holding the HTTP request open for full run completion** - avoid with Durable Functions and async status polling
2. **Assuming local CLI providers exist in Azure** - avoid with execution profiles and explicit worker capability boundaries
3. **Using local disk as cloud source of truth** - avoid with durable state and cloud-safe artifact storage contracts
4. **Targeting Python 3.14 first in Azure Functions** - avoid by standardizing hosted work on Python 3.13 or 3.12
5. **Building a second orchestration runtime for the API** - avoid by extracting shared services and keeping hosts thin

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 6: API Boundary and Control Plane Contract
**Rationale:** The product already has durable run concepts, but they are still shaped by the local UI. Extracting one shared control-plane contract is the dependency for everything else.
**Delivers:** Stable HTTP-facing run schemas, submit/status/control endpoints, and parity between UI and API views
**Addresses:** Control-plane API requirements
**Avoids:** The pitfall of building a second runtime

### Phase 7: Azure Functions Host and Durable API Surface
**Rationale:** Once the control-plane contract is stable, the host can be swapped from local-only process entrypoints to Azure Functions with durable state.
**Delivers:** Python Azure Functions host, local Core Tools parity, durable async status behavior, and host-level auth/config
**Uses:** Azure Functions, Durable Functions, Agent Framework Azure Functions integration
**Implements:** Durable execution backbone

### Phase 8: Worker Boundary and Cloud-Safe Execution Profiles
**Rationale:** The hardest platform risk is capability drift between the local machine and Azure. That boundary should be explicit before any serious cloud usage.
**Delivers:** Background worker boundary, cloud-safe routing/execution profiles, and clear capability errors for unsupported local-only paths
**Implements:** Worker adapter and capability boundary

### Phase Ordering Rationale

- API contract comes first because both the UI and Azure host need the same run surface
- Durable hosting comes second because long-running orchestration cannot safely ride on synchronous HTTP
- Worker separation comes third because it depends on the control-plane and durable-host contracts already being stable

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 7:** exact Azure Functions durable wiring, host settings, and storage choices
- **Phase 8:** worker transport and storage choices if the cloud worker later moves off the local machine

Phases with standard patterns:
- **Phase 6:** API contract extraction and REST surface alignment against the existing run model

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Official Microsoft docs now cover Agent Framework Azure Functions and Durable Functions patterns directly |
| Features | HIGH | The feature set follows well-established async control-plane patterns for long-running workflows |
| Architecture | HIGH | The split between control plane and worker boundary directly matches current repo constraints |
| Pitfalls | HIGH | The main risks are explicit in Azure Functions and Durable Functions guidance and visible in the current repo assumptions |

**Overall confidence:** HIGH

### Gaps to Address

- The current repo still has overlapping MAF and legacy AutoGen surfaces; phase planning should decide where the cloud API service layer lives
- The cloud artifact store can start with local-compatible abstractions, but phase planning should choose the first cloud-safe backing store explicitly
- Auth can begin with Functions-compatible protection, but shared multi-operator identity can remain deferred

## Sources

### Primary (HIGH confidence)
- https://learn.microsoft.com/en-us/agent-framework/integrations/azure-functions - official durable Agent Framework hosting path in Azure Functions
- https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-overview - long-running durable orchestration model and storage guidance
- https://learn.microsoft.com/en-us/azure/azure-functions/durable/durable-functions-http-features - async HTTP polling pattern for long-running operations
- https://learn.microsoft.com/en-us/azure/azure-functions/functions-best-practices - statelessness, deployment, storage, and long-running execution guidance
- https://learn.microsoft.com/ko-kr/azure/azure-functions/functions-versions - current Python version support for Azure Functions

---
*Research completed: 2026-03-22*
*Ready for roadmap: yes*
