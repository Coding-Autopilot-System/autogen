# Feature Research

**Research Date:** 2026-03-20

This product should be positioned as a local-first operator workbench for autonomous repo execution: one prompt starts a managed GSD run across planning, research, implementation, review, and validation. The durable boundary is the orchestration core, run/event model, and repo-aware execution rather than the current sample UI shell alone.

## Table Stakes

- One-prompt run creation with explicit repo selection, branch and context summary, execution mode, and autonomy level
- A manager-led workflow that makes the active stage obvious: plan, research, implement, review, validate, complete, or blocked
- Per-agent visibility for manager and specialists, including current task, last output, files touched, and next handoff
- Repo-aware execution grounded in the selected worktree: git status, branch, changed files, targeted file read/search, and safe path boundaries
- Routing visibility on every turn: selected provider/model, route tier, why it was chosen, and whether fallback occurred
- Fallback visibility that also shows capability changes, especially when a fallback loses tool calling or local repo actions
- Durable sessions with run IDs, transcript, event timeline, checkpoints, artifacts, and resume/retry from the last safe stage
- Approval flows for risky actions only, with human-readable summaries of proposed edits, commands, or side effects and explicit approve/reject outcomes
- Validation as a required closing step: commands run, pass/fail results, reviewer findings, and final operator-facing summary
- A clean backend boundary so the same orchestration engine can later be exposed over HTTP or Azure Functions without rewriting the run model

## Differentiators

- GSD-native autonomy: one prompt can drive the full repo loop end-to-end instead of forcing manual prompt chaining
- Operator-grade multi-agent observability: the UI explains why the manager delegated, what each specialist produced, and what evidence moved the run forward
- Trustworthy routing and fallback UX: fallback is an auditable state change with visible impact on tool access, confidence, and next-step safety
- Repo workbench behavior instead of chatbot behavior: every run is tied to a concrete repo snapshot, branch, diff, and validation trail
- Session branching and replay so operators can compare alternate plans, rerun on a different model, or resume from a checkpoint without losing provenance
- Approval as policy, not interruption: default autonomy for normal edits/tests, with escalation thresholds for destructive or externally visible actions
- Validation-first completion: a run is not done when the model stops talking; it is done when repo changes and verification results line up
- Azure-ready orchestration: preserve stable run, event, checkpoint, and artifact contracts so a future custom UI or Azure Function host is an exposure layer, not a rewrite

## Anti-Features

- Treating DevUI as the long-term production UI or exposing it directly on Azure
- Hiding routing, fallback, or capability downgrades inside raw logs or prompt text
- Silent CLI fallback when tool calling or repo access disappears for a turn
- Chat-only sessions with no explicit run state, stage ownership, or artifact timeline
- Approval on every step; human review should gate risk, not basic execution flow
- Sending the whole repo on every turn instead of using selective repo tools, summaries, and reusable context packs
- Unbounded filesystem access that can read secrets or wander outside the selected repo root
- Done states without executed validation commands, results, and reviewer scrutiny
- Designing v1 as a public multi-tenant assistant instead of a trusted local operator console
- Coupling the orchestration core to a single UI shell so Azure exposure requires a second system

## Sources Considered

- https://learn.microsoft.com/en-us/agent-framework/overview/?pivots=programming-language-python
- https://learn.microsoft.com/en-us/agent-framework/workflows/
- https://learn.microsoft.com/en-us/agent-framework/user-guide/devui/security
- https://learn.microsoft.com/en-us/agent-framework/integrations/azure-functions
- https://ai.google.dev/gemini-api/docs/function-calling
- https://ai.google.dev/api/caching
