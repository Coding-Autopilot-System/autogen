# Phase 4: Autonomous Repo Execution and Validation Guardrails - Research

**Researched:** 2026-03-21
**Domain:** Safe autonomous repo edits, durable change artifacts, targeted validation execution, and explicit approval guardrails over the existing local MAF runtime and dashboard operator surface
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Autonomous runs should write directly inside the operator-selected repo or worktree rather than forcing proposal-only mode.
- Routine safe repo edits should run without per-step approval when they stay under the selected repo root and can be recorded as structured operations.
- Every implementation-capable run must persist changed-file lists, per-file operation records, and unified diffs under the existing run artifact manifest.
- Validation should run automatically as a targeted ladder and record command, cwd, exit code, duration, and output summaries.
- Approval is reserved for destructive or externally visible actions with explicit scope, reason, and impact.

### the agent's Discretion
- Exact internal record shapes for write operations, validation commands, and approval-scope payloads
- Exact command-selection heuristics inside the targeted validation ladder
- Exact operator-surface presentation of diffs, validation summaries, and approval cards before Phase 5 polish

### Deferred Ideas (OUT OF SCOPE)
- Automatic per-run branch or worktree isolation by default
- Cloud-hosted worker execution and Azure Function or REST exposure of repo-editing runs
- Final product-grade visual polish for diff viewers, message surfaces, and operator ergonomics

</user_constraints>

<research_summary>
## Summary

Phase 4 should extend the existing manager-owned run contract rather than inventing a separate execution subsystem. The current codebase already has the right durable seams:
- `maf_core/tools.py` already bounds file access to a selected repo root and owns the current approval boundary
- `autogen_dashboard/session_store.py` already persists stage artifacts, attempt summaries, and a run artifact manifest
- `autogen_dashboard/session_runner.py` already owns manager-stage execution, pause and retry semantics, and projection into operator-facing run state
- `maf_core/provider_fallback.py` already records capability drift when fallback removes tool support

The missing pieces are: a controlled write service, structured change-capture artifacts, a validation runner that selects safe commands from repo context and changed files, and an approval classifier that can stop destructive or externally visible actions before execution.

**Primary recommendation:** implement Phase 4 as a sequential safety chain:
1. controlled write execution and durable change capture
2. targeted validation planning and result recording
3. approval policy enforcement and operator-visible approval scope

This keeps safety logic centralized, reuses the existing run manifest, and avoids scattering repo-editing behavior across transcript-driven agent prompts.
</research_summary>

<standard_stack>
## Standard Stack

No new framework is required for Phase 4. The best path is deeper use of existing Python runtime seams plus stdlib process and diff primitives.

### Core
| Library / Module | Version | Purpose | Why Standard Here |
|---------|---------|---------|--------------|
| `agent-framework` | `1.0.0rc5` | Active manager and workflow runtime | Already owns the specialist workflow and tool boundary |
| `maf_core/tools.py` | in-repo | Current repo-root boundary and approval seam | Best place to expose safe write and validation entrypoints |
| `autogen_dashboard/session_runner.py` | in-repo | Active manager-stage coordinator | Already owns pause, retry, and durable run projection |
| `autogen_dashboard/session_store.py` | in-repo | Durable session and artifact persistence | Already indexes artifacts per run and attempt |
| `maf_core/provider_fallback.py` | in-repo | Provider capability tracking | Needed to block write or validation when fallback loses tool support |
| `subprocess` | stdlib | Local validation command execution | Already used safely across repo helpers |
| `pathlib` and `json` | stdlib | Safe path handling and durable artifact formats | Matches current repo conventions |

### Supporting
| Library / Module | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `git` CLI | local tool | Unified diff capture and whitespace or patch checks | Use when the selected workspace is a git repo, which Phase 1 already assumes |
| `difflib` | stdlib | Fallback unified diff rendering when git diff is unavailable or too broad | Use only as a fallback, not the primary diff contract |
| `unittest` | stdlib | Automated regression coverage | Add phase-specific runtime, validation, and approval tests |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Structured write service plus artifact records | Let the model emit raw shell commands and hope the transcript explains them | Faster to prototype, but weakly bounded and not durable enough for safe autonomous edits |
| Artifact-manifest-based diff storage | Git commits or branches as the only inspection surface | Good developer ergonomics, but forces history mutation into a phase that only needs inspectable change artifacts |
| Built-in targeted validation ladder | Human-selected validation every run | More control, but violates the default-autonomous requirement and slows the operator loop |
| Shared approval classifier | Ad hoc `request_human_approval` calls in prompts | Easier initially, but hard to audit and inconsistent across write and validation paths |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Pattern 1: Manager-owned execution service
**What:** Keep the manager as the only run owner, but move actual repo-write and validation behavior into shared runtime services rather than transcript-only instructions.
**When to use:** Always for implementation and validation stages in Phase 4.
**Example:** `session_runner.py` receives a structured change payload, calls a controlled write service, persists artifacts, then advances to targeted validation.

### Pattern 2: Structured action records before and after side effects
**What:** Every write or validation action gets a machine-readable record with scope, inputs, result, and artifact references.
**When to use:** For file writes, diff capture, validation commands, and approval-required actions.
**Example:** An implementation stage stores `operations.json`, `files.json`, and `diff.patch` under the stage artifact directory and exposes those paths in the run manifest.

### Pattern 3: Safe-by-default command allowlist
**What:** Validation commands should come from a controlled set derived from changed files, stack hints, and repo structure instead of arbitrary model-generated shell.
**When to use:** For all automatic validation execution in this phase.
**Example:** Python file changes map to `python -m compileall ...` or `python -m unittest ...`; JS static changes map to `node --check ...`; all commands run under the selected repo root only.

### Pattern 4: Approval as policy, not prompt wording
**What:** Decide whether approval is required by classifying an action, not by depending on whether a prompt happened to call an approval tool.
**When to use:** For deletes, writes outside repo, git history mutation, deploys, notifications, service control, installs, and external side effects.
**Example:** A pending approval payload includes `risk_level`, `action_kind`, `affected_paths`, `commands`, and `reason`, and the run pauses before execution.

### Anti-Patterns to Avoid
- **Raw shell as the default write path:** letting model text decide arbitrary commands for repo editing
- **Transcript-only change visibility:** burying changed files or diffs inside assistant prose
- **Silent capability drift:** letting CLI fallback attempt tool-like write or validation behavior after tool support is gone
- **Approval by convention only:** relying on "remember to ask" rather than explicit action classification

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that already have strong in-repo primitives:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Run artifact indexing | A second storage tree for diffs and validation | `autogen_dashboard/session_store.py` artifact manifest and per-stage artifact directories | The repo already has a durable run layout and hydration path |
| Pause and approval flow | A parallel queue or popup system | Existing `SessionSummary` pause fields, approval queue, and decision actions | The operator control surface already knows how to wait, approve, reject, and retry |
| Provider capability reporting | New ad hoc flags in the UI | `maf_core/provider_fallback.py` route attempts and capability changes | Fallback and tool-loss metadata already exists |
| Workspace scoping | A separate repo selector inside execution helpers | Phase 1 workspace contract plus repo-root resolution in `maf_core/tools.py` and `repo_context.py` | The selected repo or worktree is already a first-class run property |

**Key insight:** Phase 4 should deepen the current run contract, not fork it.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Capturing only the final diff
**What goes wrong:** The operator can see what changed overall, but cannot tell which automated action created which file change or retry pass.
**How to avoid:** Persist both a run-level diff artifact and structured per-operation records grouped by stage and attempt.

### Pitfall 2: Letting validation commands become arbitrary shell
**What goes wrong:** Automatic validation becomes a side-effect channel that can mutate the environment or do networked work.
**How to avoid:** Use a controlled command registry or allowlist, run only under the selected repo root, and record exact commands before execution.

### Pitfall 3: Treating all file actions as equally safe
**What goes wrong:** Deleting files, resetting git state, or modifying `.env` paths slips through the same path as routine text-file edits.
**How to avoid:** Classify actions into routine-safe, destructive, externally-visible, and blocked categories before execution.

### Pitfall 4: Ignoring provider capability drift during autonomous stages
**What goes wrong:** A route falls back to CLI, loses tool support, and the manager still tries to perform write or validation actions.
**How to avoid:** Gate autonomous stages on `tools_available` or an equivalent capability flag and either reroute or pause when capabilities are insufficient.

</common_pitfalls>

<code_examples>
## Code Examples

Verified in-repo patterns worth preserving:

### Current repo-root safety boundary
```python
# Source: maf_core/tools.py
# Pattern: resolve_repo_path(...) rejects paths that escape the selected repo root
```

### Current durable stage artifact persistence
```python
# Source: autogen_dashboard/session_store.py
# Pattern: save_stage_output(...), save_attempt_summary(...), and save_artifact_manifest(...)
```

### Current manager-stage projection and pause model
```python
# Source: autogen_dashboard/session_runner.py
# Pattern: manager stage execution persists stage outputs, pause_kind, route metadata, and durable summaries
```

### Current provider capability drift reporting
```python
# Source: maf_core/provider_fallback.py
# Pattern: route attempts plus capability_changes when fallback changes provider, model, or tool support
```

</code_examples>

## Validation Architecture

Phase 4 validation needs two layers:

1. **Feature regression tests** for write execution, validation selection, approval classification, and artifact persistence
2. **Static sanity and full-suite checks** so the new runtime services do not break the existing orchestration paths

- **Primary automated framework:** stdlib `unittest`
- **Quick verification target:** phase-specific runtime tests for write execution, validation runner behavior, and approval classification
- **Broader verification target:** run persistence and API contract coverage for new artifact and approval payloads
- **Static sanity target:** compile smoke for Python modules plus `node --check` for touched dashboard JS

Recommended commands once implementation lands:

- Quick write checks: `.\.venv\Scripts\python.exe -m unittest tests.test_phase4_write_execution -v`
- Quick validation checks: `.\.venv\Scripts\python.exe -m unittest tests.test_phase4_validation -v`
- Quick approval checks: `.\.venv\Scripts\python.exe -m unittest tests.test_phase4_approval -v`
- Persistence regression: `.\.venv\Scripts\python.exe -m unittest tests.test_run_persistence -v`
- Full suite: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- Static sanity: `.\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py`
- Frontend syntax: `node --check autogen_dashboard\static\app.js`

Focus the test map on:
- path safety, secret-path denial, and repo-root confinement for write actions
- changed-file lists, per-operation records, and unified diff artifact persistence
- validation command selection, command recording, and failure-to-pause behavior
- approval classification for destructive and externally visible actions
- operator-facing payloads for change artifacts, validation results, and pending approval scope

<open_questions>
## Open Questions

1. **Should write execution be exposed only as runtime services, or also as MAF tools?**
   - What we know: the current active execution path already funnels through `session_runner.py`, while MAF tools own repo-root safety.
   - Recommendation: build the execution logic as shared Python services first, then wrap only the safe entrypoints as tools if the MAF workflow needs them directly.

2. **Should validation rules support repo-local overrides in Phase 4?**
   - What we know: the product will operate across multiple repos, but the current repo has no standard validation-config file.
   - Recommendation: implement conservative built-in rules first and keep a lightweight hook for future repo-local overrides without making that hook a hard dependency of this phase.

3. **What should happen when the selected route falls back to a CLI provider before implementation or validation?**
   - What we know: CLI fallback today can lose structured tool support.
   - Recommendation: treat missing tool support as a hard execution guardrail and pause or reroute before write or validation actions rather than silently degrading.

</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/phases/04-autonomous-repo-execution-and-validation-guardrails/04-CONTEXT.md`
- `.planning/phases/03-specialist-delegation-and-routing-visibility/03-CONTEXT.md`
- `maf_core/tools.py`
- `maf_core/orchestration.py`
- `maf_core/provider_fallback.py`
- `autogen_dashboard/session_runner.py`
- `autogen_dashboard/session_store.py`
- `autogen_dashboard/schemas.py`
- `autogen_dashboard/repo_context.py`
- `README.md`

### Secondary (MEDIUM confidence)
- `.planning/codebase/ARCHITECTURE.md`
- `.planning/codebase/STRUCTURE.md`
- `.planning/codebase/CONVENTIONS.md`
- `.planning/codebase/TESTING.md`
- `.planning/codebase/CONCERNS.md`
- `tests/test_run_persistence.py`
- `tests/test_phase2_runtime.py`
- `tests/test_phase3_api.py`

</sources>

<metadata>
## Metadata

**Research scope:**
- Safe write-execution boundaries in the active runtime
- Durable artifact seams for changed files, diffs, and validation results
- Approval classification and pause semantics for risky actions
- Test strategy needed for autonomous execution and guardrails

**Confidence breakdown:**
- Runtime seam selection: HIGH
- Change-artifact persistence direction: HIGH
- Validation ladder direction: HIGH
- Approval-classification approach: HIGH

**Research date:** 2026-03-21
**Valid until:** 2026-04-20

</metadata>

---

*Phase: 04-autonomous-repo-execution-and-validation-guardrails*
*Research completed: 2026-03-21*
*Ready for planning: yes*
