# Phase 4: Autonomous Repo Execution and Validation Guardrails - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-03-21
**Phase:** 04-autonomous-repo-execution-and-validation-guardrails
**Areas discussed:** autonomous edit surface, change artifacts and operator inspection, validation runner policy, approval guardrails

---

## Autonomous edit surface

| Option | Description | Selected |
|--------|-------------|----------|
| Direct selected repo/worktree | Edit inside the operator-selected repo or worktree, with the runtime capturing every write operation. | selected |
| Automatic scratch worktree | Clone work into a new worktree or branch per run before applying changes. | |
| Proposal only | Keep writing disabled and stop at plans or diffs that the human applies later. | |

**User's choice:** `[auto] Direct selected repo/worktree`
**Notes:** Recommended because the product goal is "one prompt and stuff happens," while automatic isolation is already a later v2 concern under `SAFE-01`. The current runtime already scopes activity to an explicit repo or worktree root, so direct in-root edits are the strongest Phase 4 fit without expanding scope.

---

## Change artifacts and operator inspection

| Option | Description | Selected |
|--------|-------------|----------|
| File list only | Store the changed-file names and a short summary. | |
| File list + operation records + unified diff | Persist changed-file lists, write-operation records, and diffs under the run artifact manifest. | selected |
| Commit-based history only | Use git commits or branches as the main inspection surface for every run. | |

**User's choice:** `[auto] File list + operation records + unified diff`
**Notes:** Recommended because `autogen_dashboard/session_store.py` already has a durable artifact manifest and per-attempt layout. This gives the operator inspectable artifacts without forcing git history mutation into scope.

---

## Validation runner policy

| Option | Description | Selected |
|--------|-------------|----------|
| One fixed validation command | Run the same repo-wide command every time, regardless of the change set. | |
| Targeted ladder | Run fast targeted checks first, then escalate to broader validation only when changed files or failures justify it. | selected |
| Human-selected validation | Pause every run and ask the operator which validation commands to run. | |

**User's choice:** `[auto] Targeted ladder`
**Notes:** Recommended because the current codebase is mixed-path and local-first, and the requirement explicitly calls for targeted validation. The repo already standardizes local verification commands in `.planning/codebase/TESTING.md`, so recording command, cwd, exit code, duration, and output summary is the right durable contract.

---

## Approval guardrails

| Option | Description | Selected |
|--------|-------------|----------|
| Approve every write | Require human approval before any file edit or validation command. | |
| Approve only destructive or externally visible actions | Allow routine safe repo edits and local validation to run automatically, but stop for destructive or outward-facing actions. | selected |
| No approval gates | Allow the runtime to execute all actions automatically once the run starts. | |

**User's choice:** `[auto] Approve only destructive or externally visible actions`
**Notes:** Recommended because prior project direction explicitly favors autonomy, while Phase 4 still exists to contain execution risk. The current `request_human_approval` seam can be extended with explicit scope details for deletes, deploys, git pushes, external APIs, and service start/stop actions.

---

## the agent's Discretion

- Exact diff-file naming and patch-record payload shape
- Validation command-selection heuristics within the targeted ladder
- Exact operator-surface presentation of diffs, validation cards, and approval summaries before Phase 5 polish

## Deferred Ideas

- Automatic per-run branch or worktree isolation by default - defer to later `SAFE-01`
- Cloud-hosted worker execution and Azure Function or REST exposure of repo-editing runs - defer to later cloud phases
- Final polished diff viewer styling and operator-grade visual system - defer to Phase 5
