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
- [x] **Phase 6: API Boundary and Control Plane Contract** - Extract a shared orchestration service layer and expose it through a stable HTTP API
- [x] **Phase 7: Worker Boundary and Cloud-Safe Execution Profiles** - Separate cloud ingress from long-running repo execution and local-only provider assumptions
- [x] **Phase 8: Local Ollama Provider + OpenAPI Spec** - Wire Gemma/Ollama as tier-0 provider and export OpenAPI 3.1 spec for the dashboard API

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

### Phase 7: Worker Boundary and Cloud-Safe Execution Profiles
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
- [x] 07-01: Introduce the worker boundary and background run dispatch contract
- [x] 07-02: Add cloud-safe provider and execution profiles with explicit capability enforcement
- [x] 07-03: Validate end-to-end API-driven runs across local and cloud-safe execution modes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Workspace and Durable Run Foundation | 3/3 | Complete | 2007-03-21 |
| 2. Manager-Led Orchestration Core | 3/3 | Complete | 2007-03-21 |
| 3. Specialist Delegation and Routing Visibility | 3/3 | Complete | 2007-03-21 |
| 4. Autonomous Repo Execution and Validation Guardrails | 3/3 | Complete | 2007-03-21 |
| 5. Polished Operator Workbench | 3/3 | Complete | 2007-03-22 |
| 6. API Boundary and Control Plane Contract | 3/3 | Complete | 2026-06-10 |
| 7. Worker Boundary and Cloud-Safe Execution Profiles | 3/3 | Complete | 2026-06-14 |
| 8. Local Ollama Provider + OpenAPI Spec | 2/2 | Complete | 2026-06-23 |
