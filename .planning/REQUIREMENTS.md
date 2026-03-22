# Requirements: GSD Orchestration Platform

**Defined:** 2026-03-22
**Core Value:** You can give one prompt and watch a trustworthy multi-agent coding system drive real repo work end-to-end with clear traces, specialist visibility, and minimal manual intervention.

## v1 Requirements

Scope for milestone v1.1: Cloud API and Azure Function Hosting.

### API Surface

- [ ] **API-01**: User can submit a run over HTTP and receive a durable run ID plus initial status
- [ ] **API-02**: User can fetch current run status, active stage, pause reason, and last route over HTTP
- [ ] **API-03**: User can fetch timeline, agent state, routing history, validation results, and artifacts for a run over HTTP
- [ ] **API-04**: User can continue, approve, retry, cancel, or append operator input to an existing run over HTTP

### Azure Functions Hosting

- [ ] **AZFN-01**: User can host the orchestration control plane as a Python Azure Functions app without rewriting the shared orchestration core
- [ ] **AZFN-02**: Long-running run state persists across Azure Functions restarts and outlives the original HTTP request
- [ ] **AZFN-03**: User can run and validate the Functions-hosted API locally with Azure Functions Core Tools before cloud deployment
- [ ] **AZFN-04**: The Functions host exposes documented HTTP routes and auth configuration that work locally and in Azure

### Worker Boundary

- [ ] **WRKR-01**: The control-plane API can hand off long-running execution to a background worker boundary instead of holding the HTTP request open
- [ ] **WRKR-02**: Cloud-hosted execution rejects or reroutes local-only providers and repo-execution paths when no compatible worker is attached
- [ ] **WRKR-03**: The platform can keep local repo execution and CLI-backed specialists for development while exposing the same durable run contract through the cloud API

## v2 Requirements

### Collaboration and Isolation

- **SAFE-01**: The system can isolate autonomous runs in dedicated branches, worktrees, or sandboxed execution contexts by default
- **AUTH-01**: The platform can support authenticated shared operator access when it is no longer single-user local-only

### Cloud Expansion

- **WRKR-04**: The platform can run the worker plane in Azure without depending on the local workstation
- **OBSV-01**: User can inspect cloud-hosted run health, logs, and failure diagnostics from a dedicated operator or diagnostics surface

## Out of Scope

| Feature | Reason |
|---------|--------|
| Public multi-tenant SaaS orchestration portal | This milestone is still for your own trusted operator workflow, not a general public product |
| Cloud-hosted execution that depends on local Codex, Claude, or Gemini CLI sessions | Those desktop-bound sessions are not a reliable cloud capability |
| Fully shared multi-user approval workflow | Basic protected endpoints are enough for this milestone; richer auth and collaboration stay deferred |
| Automated production Azure deployment pipeline | This milestone makes the host deployable and locally testable first; full production rollout automation can follow |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| API-01 | Phase 6 | Pending |
| API-02 | Phase 6 | Pending |
| API-03 | Phase 6 | Pending |
| API-04 | Phase 6 | Pending |
| AZFN-01 | Phase 7 | Pending |
| AZFN-02 | Phase 7 | Pending |
| AZFN-03 | Phase 7 | Pending |
| AZFN-04 | Phase 7 | Pending |
| WRKR-01 | Phase 8 | Pending |
| WRKR-02 | Phase 8 | Pending |
| WRKR-03 | Phase 8 | Pending |

**Coverage:**
- v1 requirements: 11 total
- Mapped to phases: 11
- Unmapped: 0

---
*Requirements defined: 2026-03-22*
*Last updated: 2026-03-22 after milestone v1.1 requirements definition*
