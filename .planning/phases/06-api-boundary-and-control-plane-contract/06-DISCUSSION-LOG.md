# Phase 6: API Boundary and Control Plane Contract - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `06-CONTEXT.md`; this log preserves the alternatives considered.

**Date:** 2026-03-22
**Phase:** 06-api-boundary-and-control-plane-contract
**Areas discussed:** API surface and resource model, run actions and lifecycle over HTTP, shared control-plane ownership, auth posture and local-versus-cloud boundary

---

## API surface and resource model

| Option | Description | Selected |
|--------|-------------|----------|
| Versioned REST run resources | Expose a stable `/api/v1` run-oriented contract with separate summary, timeline, routing, agent, and artifact surfaces | ✓ |
| Extend AG-UI as the external API | Treat `command_center/app.py` AG-UI endpoints as the public control-plane API | |
| Keep ad hoc UI-specific endpoints | Continue growing separate UI-first surfaces without a canonical external contract | |

**User's choice:** `[auto]` Selected **Versioned REST run resources** as the recommended default.
**Notes:** Recommended because the milestone requirement is a durable control-plane API shared by the UI and Azure Functions later. AG-UI remains valuable, but it is a protocol surface for the product UI rather than the canonical external API.

---

## Run actions and lifecycle over HTTP

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit per-action run commands | Keep durable run identity and expose create, continue, approve, retry, cancel, and input as explicit run actions | ✓ |
| Single generic command endpoint | Use one POST endpoint with an action enum and variable payloads for every run mutation | |
| Synchronous request-per-turn model | Treat each HTTP request as a stateless chat turn instead of a durable run lifecycle | |

**User's choice:** `[auto]` Selected **Explicit per-action run commands** as the recommended default.
**Notes:** Recommended because the existing `autogen_dashboard/app.py` already models actions explicitly, and this keeps pause/resume/approval semantics readable, auditable, and easier to mirror in Azure Functions later.

---

## Shared control-plane ownership

| Option | Description | Selected |
|--------|-------------|----------|
| Extract shared run-control services | Move durable run control out of UI-centric modules and let both `command_center/` and future hosts call one shared service | ✓ |
| Keep runtime ownership in `command_center/` | Grow the current AG-UI host into the sole control plane and duplicate missing durable-run logic there | |
| Keep `autogen_dashboard/` as the primary runtime | Preserve the legacy session stack as the permanent owner and let the Command Center stay a secondary shell | |

**User's choice:** `[auto]` Selected **Extract shared run-control services** as the recommended default.
**Notes:** Recommended because the current codebase is split: the product UI lives in `command_center/`, but the richest durable run lifecycle still lives in `autogen_dashboard/`. Phase 6 needs a shared service layer to remove that drift.

---

## Auth posture and local-versus-cloud boundary

| Option | Description | Selected |
|--------|-------------|----------|
| Pluggable auth boundary with local-open dev mode | Keep local loopback development simple while formalizing request-auth as a reusable control-plane boundary for cloud hosting | ✓ |
| No auth concern in Phase 6 | Leave auth completely implicit until Azure Functions hosting begins | |
| Force full production auth now | Design the API as if it were already a multi-user public cloud surface | |

**User's choice:** `[auto]` Selected **Pluggable auth boundary with local-open dev mode** as the recommended default.
**Notes:** Recommended because this milestone is still single-user and local-first, but Phase 7 needs a clean Azure Functions-ready auth seam. Local CLI and repo capabilities must stay runtime concerns, not API assumptions.

---

## the agent's Discretion

- Exact REST path naming under `/api/v1` as long as runs remain the durable top-level resource.
- Exact package placement of the shared control-plane service layer.
- Exact split between summary and detail payload DTOs.

## Deferred Ideas

- Azure Functions host entrypoint and Durable Functions behavior - Phase 7
- Worker dispatch contract and cloud-safe provider capability enforcement - Phase 8
- Shared multi-user auth and collaboration - later milestone
