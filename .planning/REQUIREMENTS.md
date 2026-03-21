# Requirements: GSD Orchestration Platform

**Defined:** 2026-03-20
**Core Value:** You can give one prompt and watch a trustworthy multi-agent coding system drive real repo work end-to-end with clear traces, specialist visibility, and minimal manual intervention.

## v1 Requirements

### Workspace

- [x] **WKSP-01**: User can start a run by selecting a local repo or worktree and entering one engineering prompt
- [x] **WKSP-02**: User can see the selected repo's branch, dirty state, and summary before or during a run
- [x] **WKSP-03**: User can resume, retry, or reopen a previous run with its prior context, transcript, and artifacts

### Orchestration

- [ ] **ORCH-01**: User can run a manager-led workflow that moves through planning, research, implementation, review, and validation stages
- [ ] **ORCH-02**: User can see the current stage, overall run status, and why the run is paused, blocked, or complete
- [ ] **ORCH-03**: User can continue a paused run after approval, missing input, or retry without losing state
- [ ] **ORCH-04**: The system can answer routine GSD clarification and planning questions automatically from available project and repo context instead of asking the operator every time

### Specialists

- [ ] **AGNT-01**: User can see which specialist agents are participating in the run
- [ ] **AGNT-02**: User can inspect each specialist agent's current task, latest output, and handoff status
- [ ] **AGNT-03**: The system can delegate repo work to specialist agents without requiring manual prompt choreography by the user

### Routing and Models

- [ ] **ROUT-01**: User can choose a preferred model or route lane for a run before it starts
- [ ] **ROUT-02**: User can see the provider, model, route tier, and rationale for each turn
- [ ] **ROUT-03**: User can see when fallback occurred and whether tool availability changed because of it

### Execution and Safety

- [ ] **EXEC-01**: The system can edit files in the selected repo automatically during an autonomous run
- [ ] **EXEC-02**: User can inspect changed files, diffs, or file lists produced by a run
- [ ] **EXEC-03**: The system can run targeted local validation commands and attach the results to the run
- [ ] **EXEC-04**: Destructive or externally visible actions require an explicit approval step

### Operator UI

- [ ] **UI-01**: User can read run output in a polished operator UI with visually distinct human, manager, and specialist messages
- [ ] **UI-02**: User can switch between overall run view, per-agent view, traces, and artifacts
- [ ] **UI-03**: User can inspect traces, event timeline, approvals, and generated artifacts without reading raw logs

## v2 Requirements

### Cloud Exposure

- **API-01**: User can submit a run and poll its status through an HTTP API
- **AZFN-01**: User can host the orchestration entrypoint on Azure Functions with durable run state
- **AZFN-02**: User can separate the control-plane API from long-running worker execution when moving beyond local-only hosting

### Collaboration and Isolation

- **SAFE-01**: The system can isolate autonomous runs in dedicated branches, worktrees, or sandboxed execution contexts by default
- **AUTH-01**: The platform can support authenticated shared operator access when it is no longer single-user local-only

## Out of Scope

| Feature | Reason |
|---------|--------|
| Public multi-tenant SaaS assistant | v1 is a trusted local operator workbench for one primary user |
| Mobile app | Desktop and browser operator workflows are the priority |
| Production use of raw DevUI as the final product UI | DevUI is an engineering console, not the durable product surface |
| Full Azure-hosted repo-editing worker plane in v1 | Local-first maturity comes before cloud execution of the heavy worker tier |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| WKSP-01 | Phase 1 | Complete |
| WKSP-02 | Phase 1 | Complete |
| WKSP-03 | Phase 1 | Complete |
| ORCH-01 | Phase 2 | Pending |
| ORCH-02 | Phase 2 | Pending |
| ORCH-03 | Phase 2 | Pending |
| ORCH-04 | Phase 2 | Pending |
| AGNT-01 | Phase 3 | Pending |
| AGNT-02 | Phase 3 | Pending |
| AGNT-03 | Phase 3 | Pending |
| ROUT-01 | Phase 3 | Pending |
| ROUT-02 | Phase 3 | Pending |
| ROUT-03 | Phase 3 | Pending |
| EXEC-01 | Phase 4 | Pending |
| EXEC-02 | Phase 4 | Pending |
| EXEC-03 | Phase 4 | Pending |
| EXEC-04 | Phase 4 | Pending |
| UI-01 | Phase 5 | Pending |
| UI-02 | Phase 5 | Pending |
| UI-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 20 total
- Mapped to phases: 20
- Unmapped: 0

---
*Requirements defined: 2026-03-20*
*Last updated: 2026-03-21 after Phase 01 completion*
