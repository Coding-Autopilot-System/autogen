# Phase 1: Workspace and Durable Run Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-03-20
**Phase:** 01-workspace-and-durable-run-foundation
**Areas discussed:** Workspace targeting and run entry, Run identity and lifecycle, Persisted run record and artifacts, Workspace snapshot and freshness

---

## Workspace targeting and run entry

### Question 1

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit repo or worktree picker | Operator chooses the workspace before every run; best match for a repo-aware workbench | yes |
| Hidden global repo root | Reuse one configured repo only; simpler but blocks multi-repo operation | |
| Freeform path-only entry | Flexible but weak on safety and discoverability | |

**User's choice:** [auto] Selected: Explicit repo or worktree picker
**Notes:** Recommended because Phase 1 must satisfy `WKSP-01` and the repo already contains reusable repo-discovery code.

### Question 2

| Option | Description | Selected |
|--------|-------------|----------|
| Treat worktrees as first-class targets | A selected workspace can be either a repo root or a repo worktree with the same UX | yes |
| Support repo roots only | Simpler but blocks future isolated run flows | |
| Add worktree support later | Reduces scope now but leaves the workspace contract incomplete | |

**User's choice:** [auto] Selected: Treat worktrees as first-class targets
**Notes:** Recommended because later phases will likely need isolated execution contexts.

### Question 3

| Option | Description | Selected |
|--------|-------------|----------|
| Show branch, dirty state, stack hints, and recent commits before start | Best operator visibility and already supported by legacy repo context helpers | yes |
| Show only repo name and path | Lower effort but too little context for an orchestration tool | |
| Hide context until after run creation | Fastest flow but weak for trust and review | |

**User's choice:** [auto] Selected: Show branch, dirty state, stack hints, and recent commits before start
**Notes:** Recommended because the codebase already computes this summary and `WKSP-02` requires it.

### Question 4

| Option | Description | Selected |
|--------|-------------|----------|
| Remember recent and last-used workspaces, but keep selection visible | Fast repeat use without hiding the active target | yes |
| Always force a fresh selection | Safe but slower for daily use | |
| Auto-start in the last workspace with no confirmation | Fastest but easier to mis-target | |

**User's choice:** [auto] Selected: Remember recent and last-used workspaces, but keep selection visible
**Notes:** Recommended because the product is operator-facing and should optimize repeat work without hiding context.

---

## Run identity and lifecycle

### Question 1

| Option | Description | Selected |
|--------|-------------|----------|
| Stable run ID with one durable history | Resume and retry stay attached to the same run record | yes |
| New session for every retry | Cleaner separation but fragments the operator history | |
| Stateless chat turns only | Too weak for durable orchestration | |

**User's choice:** [auto] Selected: Stable run ID with one durable history
**Notes:** Recommended because `WKSP-03` calls for reopening and resuming prior runs with context intact.

### Question 2

| Option | Description | Selected |
|--------|-------------|----------|
| Resume continues the same run from the last saved checkpoint | Preserves transcript, artifacts, and stage outputs | yes |
| Resume starts a fresh copy of the old run | Simpler implementation but loses continuity | |
| Only support retry, not resume | Does not satisfy the roadmap intent | |

**User's choice:** [auto] Selected: Resume continues the same run from the last saved checkpoint
**Notes:** Recommended because the current session store and checkpoint seams already support this direction.

### Question 3

| Option | Description | Selected |
|--------|-------------|----------|
| Retry creates a new attempt on the same run timeline | Keeps one operator-facing history while distinguishing attempts | yes |
| Retry replaces the prior attempt entirely | Hides the run history | |
| Retry spawns a brand-new unrelated run | Makes reopen and comparison harder | |

**User's choice:** [auto] Selected: Retry creates a new attempt on the same run timeline
**Notes:** Recommended because Phase 1 should optimize durable understanding, not raw implementation convenience.

### Question 4

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit statuses and pause reasons in the run model | Best support for future UI tabs, traces, and approvals | yes |
| Derive state from transcript text only | Brittle and hard to automate | |
| Minimal running or done status only | Too weak for later orchestration phases | |

**User's choice:** [auto] Selected: Explicit statuses and pause reasons in the run model
**Notes:** Recommended because the legacy dashboard already demonstrates the value of this structure.

---

## Persisted run record and artifacts

### Question 1

| Option | Description | Selected |
|--------|-------------|----------|
| One dedicated run directory with metadata, transcript, events, state, and artifacts | Clear local durability model and strongest reuse of existing storage patterns | yes |
| Split storage across unrelated folders | Harder to reason about and migrate later | |
| Keep only checkpoints and rebuild everything else | Too lossy for operator review | |

**User's choice:** [auto] Selected: One dedicated run directory with metadata, transcript, events, state, and artifacts
**Notes:** Recommended because the legacy session store already follows this shape.

### Question 2

| Option | Description | Selected |
|--------|-------------|----------|
| Chronological transcript plus parallel structured event stream | Good for both operator UX and machine-driven orchestration | yes |
| Transcript only | Easier now but weak for traces and automation | |
| Events only | Poor operator readability | |

**User's choice:** [auto] Selected: Chronological transcript plus parallel structured event stream
**Notes:** Recommended because later phases need both human-readable and machine-readable history.

### Question 3

| Option | Description | Selected |
|--------|-------------|----------|
| Artifact categories visible from the first phase | Workspace snapshot, stage outputs, approvals, diffs, and validation all become first-class | yes |
| Only store artifacts later when execution lands | Delays the run contract too much | |
| Store artifacts but hide them from the UI | Weak trust and review experience | |

**User's choice:** [auto] Selected: Artifact categories visible from the first phase
**Notes:** Recommended because later UI and execution phases depend on this contract.

### Question 4

| Option | Description | Selected |
|--------|-------------|----------|
| Save at creation, stage boundaries, human decisions, and finish states | Best durability with predictable restore points | yes |
| Save only at the end of a run | Too fragile for long-running work | |
| Save on every token or message delta | Likely too noisy for local storage | |

**User's choice:** [auto] Selected: Save at creation, stage boundaries, human decisions, and finish states
**Notes:** Recommended because it balances durability and storage simplicity.

---

## Workspace snapshot and freshness

### Question 1

| Option | Description | Selected |
|--------|-------------|----------|
| Snapshot at creation and refresh at run start, resume, retry, and stage boundaries | Best balance of freshness and determinism | yes |
| Snapshot only once at creation | Too stale for long-lived runs | |
| Refresh on every turn only | Misses important lifecycle boundaries and can be noisy | |

**User's choice:** [auto] Selected: Snapshot at creation and refresh at run start, resume, retry, and stage boundaries
**Notes:** Recommended because the run model should detect workspace drift without overcomplicating v1.

### Question 2

| Option | Description | Selected |
|--------|-------------|----------|
| Snapshot includes root, branch, dirty flag, changed files, recent commits, and stack hints | Strong operator context and already supported by existing repo helpers | yes |
| Snapshot only repo path and branch | Too little context for review | |
| Capture full git diff every time | Useful later but too heavy for Phase 1 | |

**User's choice:** [auto] Selected: Snapshot includes root, branch, dirty flag, changed files, recent commits, and stack hints
**Notes:** Recommended because it satisfies current visibility needs without overloading persistence.

### Question 3

| Option | Description | Selected |
|--------|-------------|----------|
| Show a stale-workspace warning when the repo changes outside the run | Makes external drift visible without blocking all work | yes |
| Silently overwrite the snapshot | Dangerous for operator trust | |
| Hard-block the run immediately on any change | Safer but too rigid for the first phase | |

**User's choice:** [auto] Selected: Show a stale-workspace warning when the repo changes outside the run
**Notes:** Recommended because it keeps the operator informed while preserving local iteration speed.

### Question 4

| Option | Description | Selected |
|--------|-------------|----------|
| Show repo context in the UI header or side panel and persist it with the run | Best operator visibility; not hidden only in prompt text | yes |
| Inject repo context only into model prompts | Invisible to the operator | |
| Show repo context only on a separate debug page | Too buried for primary workflow use | |

**User's choice:** [auto] Selected: Show repo context in the UI header or side panel and persist it with the run
**Notes:** Recommended because later polished UI work depends on operator-visible workspace state.

---

## the agent's Discretion

- Exact visual design of the temporary Phase 1 workspace and run header
- Exact artifact filename conventions inside the run directory
- Exact wording of status, attempt, and stale-workspace badges

## Deferred Ideas

None.
