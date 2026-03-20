# Research Summary

**Research Date:** 2026-03-20

## Stack

Stay local-first, Python-first, and workflow-first. The existing Microsoft Agent Framework base is the right orchestration core, but DevUI should remain an engineering console rather than the long-term product UI. A custom operator UI over a thin Python API is the likely durable direction.

## Table Stakes

- One-prompt autonomous repo run with clear stage ownership
- Per-agent visibility and traceability
- Explicit routing and fallback visibility
- Repo-aware execution and safe file boundaries
- Durable sessions, checkpoints, and resumable runs
- Validation-backed completion instead of chat-only completion

## Architecture Direction

Keep a headless orchestration core and expose it through thin local and remote surfaces. The core shape should be:

`manager workflow -> specialist agents/workflows -> typed tools/policies -> checkpoint/state/trace store`

Start with a sequential manager-led workflow, stabilize state and observability, then improve the operator UI, and only after that add Azure REST and Function exposure.

## Watch Out For

- Treating DevUI as a production UI
- Silent or capability-losing fallback behavior
- Secret leakage through repo tools, traces, or CLI subprocess inheritance
- Brittle UI patching against private DevUI internals
- Autonomous edit blast radius without branch/worktree isolation and targeted validation
- Poor repo-scale performance from naive recursive scanning
- Carrying Windows-local assumptions directly into Azure hosting

## Implication For This Project

The right v1 is a polished local operator workbench with a strong orchestration core, visible specialist execution, stable run and trace contracts, and autonomous repo execution guarded by policy. Azure exposure is important, but it should come after the core runtime, state model, and operator UX are stable.

## Sources

- `.planning/research/STACK.md`
- `.planning/research/FEATURES.md`
- `.planning/research/ARCHITECTURE.md`
- `.planning/research/PITFALLS.md`
