# Roadmap: GSD Orchestration Platform

## Overview

This roadmap now enters milestone v1.1: Cloud API and Azure Function Hosting. The local-first operator workbench is already in place. The next delivery sequence extracts the orchestration contract into a real control plane, hosts that control plane on Azure Functions with durable state, and then introduces a worker boundary so cloud-hosted execution does not depend on local workstation assumptions.

## Phases

**Phase Numbering:**
- Integer phases (6, 7, 8): Planned milestone work
- Decimal phases (6.1, 6.2): Urgent insertions if needed later

- [x] **Phase 1: Workspace and Durable Run Foundation** - Establish repo selection, workspace context, and durable local run state
- [x] **Phase 2: Manager-Led Orchestration Core** - Deliver the manager workflow and explicit stage/state model
- [x] **Phase 3: Specialist Delegation and Routing Visibility** - Make specialist participation and provider routing fully visible
- [x] **Phase 4: Autonomous Repo Execution and Validation Guardrails** - Turn the system into a safe default-doer for repo work
- [x] **Phase 5: Polished Operator Workbench** - Replace prototype interaction with a durable operator-grade UI
- [ ] **Phase 6: API Boundary and Control Plane Contract** - Extract a shared orchestration service layer and expose it through a stable HTTP API
- [ ] **Phase 7: Azure Functions Host and Durable API Surface** - Host the control plane in Python Azure Functions with durable run state and async status behavior
- [ ] **Phase 8: Worker Boundary and Cloud-Safe Execution Profiles** - Separate cloud ingress from long-running repo execution and local-only provider assumptions

## Phase Details

### Phase 6: API Boundary and Control Plane Contract
**Goal**: Turn the existing run contract into a host-agnostic control-plane API that both the UI and external callers can use.
**Depends on**: Phase 5
**Requirements**: API-01, API-02, API-03, API-04
**Success Criteria** (what must be TRUE):
  1. A caller can submit a run over HTTP and receive a durable run ID plus initial status.
  2. A caller can inspect run status, stage, pause reason, route, agents, and artifacts over HTTP without browser-only state.
  3. A caller can continue, approve, retry, cancel, or append operator input to the same run over HTTP.
  4. The Operator Workbench and the HTTP API observe and control the same shared run contract instead of separate implementations.
**Plans**: 3 plans

Plans:
- [ ] 06-01: Extract shared orchestration services and run schemas from UI-centric entrypoints
- [ ] 06-02: Add REST endpoints for submit, status, control, routing, agents, and artifacts
- [ ] 06-03: Align Operator Workbench and HTTP API parity over the shared run contract

### Phase 7: Azure Functions Host and Durable API Surface
**Goal**: Host the control plane on Azure Functions with durable state and local Core Tools parity.
**Depends on**: Phase 6
**Requirements**: AZFN-01, AZFN-02, AZFN-03, AZFN-04
**Success Criteria** (what must be TRUE):
  1. The shared control-plane API can run inside a Python Azure Functions host without rewriting the orchestration core.
  2. Long-running run state survives host restarts and outlives the original HTTP request.
  3. The Functions-hosted API can be started and validated locally with Azure Functions Core Tools.
  4. Routes, settings, and auth behavior are documented and behave consistently between local and Azure environments.
**Plans**: 3 plans

Plans:
- [ ] 07-01: Create the Functions host entrypoint and cloud-safe configuration surface
- [ ] 07-02: Add durable run-start and async status behavior with local Core Tools verification
- [ ] 07-03: Document routes, auth, and deployment-ready function settings

### Phase 8: Worker Boundary and Cloud-Safe Execution Profiles
**Goal**: Make long-running execution explicit and safe when the control plane is hosted away from the local workstation.
**Depends on**: Phase 7
**Requirements**: WRKR-01, WRKR-02, WRKR-03
**Success Criteria** (what must be TRUE):
  1. HTTP ingress never waits for the full long-running repo execution path to complete.
  2. Long-running repo execution can be handed off through a worker boundary and reported back into the same durable run.
  3. Cloud-hosted runs clearly reject or reroute local-only providers and repo-execution paths when no compatible worker is attached.
  4. Local development can still use repo execution and CLI-backed specialists against the same durable run contract.
**Plans**: 3 plans

Plans:
- [ ] 08-01: Introduce the worker boundary and background run dispatch contract
- [ ] 08-02: Add cloud-safe provider and execution profiles with explicit capability enforcement
- [ ] 08-03: Validate end-to-end API-driven runs across local and cloud-safe execution modes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Workspace and Durable Run Foundation | 3/3 | Complete | 2026-03-21 |
| 2. Manager-Led Orchestration Core | 3/3 | Complete | 2026-03-21 |
| 3. Specialist Delegation and Routing Visibility | 3/3 | Complete | 2026-03-21 |
| 4. Autonomous Repo Execution and Validation Guardrails | 3/3 | Complete | 2026-03-21 |
| 5. Polished Operator Workbench | 3/3 | Complete | 2026-03-22 |
| 6. API Boundary and Control Plane Contract | 0/3 | Planned | - |
| 7. Azure Functions Host and Durable API Surface | 0/3 | Planned | - |
| 8. Worker Boundary and Cloud-Safe Execution Profiles | 0/3 | Planned | - |
