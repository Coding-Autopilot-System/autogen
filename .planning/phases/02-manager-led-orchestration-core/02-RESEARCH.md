# Phase 2: Manager-Led Orchestration Core - Research

**Researched:** 2026-03-21
**Domain:** Manager-led multi-stage orchestration over the existing local MAF runtime and durable run model
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- The manager owns one canonical stage sequence for normal engineering runs: `planning -> research -> implementation -> review -> validation`.
- Stage outputs live inside one durable run rather than becoming separate runs or loose transcript fragments.
- Pause reasons must be explicit and structured, and resume must continue from the paused stage with prior outputs intact.
- Stage-level orchestration gates should exist for meaningful approval points, while lower-level risky-action approval remains available underneath.
- Routine GSD clarification questions should be answered automatically from project, phase, repo, and workspace context when confidence is high enough.
- Automatic GSD answers must be recorded as structured artifacts and events so the operator can inspect what happened.
- The active orchestration contract must live in the shared runtime and be mirrored into the operator-facing run API instead of being hidden only inside DevUI.

### the agent's Discretion
- Exact file and schema layout for stage artifacts
- Exact confidence heuristics for automatic GSD answering
- Exact temporary UI treatment of stage summaries and pause banners before the polished workbench phase

### Deferred Ideas (OUT OF SCOPE)
- Rich per-agent panes and specialist tabs
- Final stylish operator UI shell
- Autonomous repo editing and validation-by-default execution
- Azure Function and REST exposure

</user_constraints>

<research_summary>
## Summary

Phase 2 should promote the existing `repo_team` proof-of-concept into a real manager-led orchestration contract instead of building another conversational surface around single-turn agents. The strongest implementation path is to preserve the current Phase 1 durable run model in `autogen_dashboard`, add an explicit orchestration state model in `maf_core`, and let the manager workflow persist stage records, stage artifacts, pause reasons, and auto-answer decisions into the same run directory already established in Phase 1.

The current codebase already contains the raw pieces:
- a sequential specialist workflow in `maf_core/team_factory.py`
- checkpointed workflow seams in `maf_core/workflow_factory.py`
- explicit run status and pause models in `autogen_dashboard/session_runner.py` and `autogen_dashboard/schemas.py`
- route and capability metadata in `maf_core/provider_fallback.py`

The gap is not missing agent infrastructure. The gap is the absence of one explicit orchestration state machine that both the runtime and operator surface can agree on.

**Primary recommendation:** introduce a shared orchestration module in `maf_core/` that owns stage definitions, stage artifacts, pause semantics, and auto-answer provenance, then mirror that contract into the persisted run schemas and operator-facing API.
</research_summary>

<standard_stack>
## Standard Stack

No new framework is required for Phase 2. This phase is primarily a consolidation of existing in-repo runtime seams.

### Core
| Library / Module | Version | Purpose | Why Standard Here |
|---------|---------|---------|--------------|
| `agent-framework` | `1.0.0rc5` | Active agent and workflow runtime | Already powers the live entities and checkpointed workflows |
| `agent_framework_orchestrations.SequentialBuilder` | bundled | Specialist sequencing | Already expresses the planner/researcher/implementer/reviewer chain the manager will own |
| `maf_core/team_factory.py` | in-repo | Existing multi-agent workflow scaffold | Best starting point for a real manager workflow |
| `autogen_dashboard/session_runner.py` | in-repo | Durable run lifecycle, pause states, event persistence | Already models the operator-facing run contract established in Phase 1 |
| `autogen_dashboard/schemas.py` | in-repo | Typed persisted run and API payload models | Already carries status, pause, workspace, and attempt metadata |

### Supporting
| Library / Module | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `maf_core/provider_fallback.py` | in-repo | Provider/model routing metadata and fallback execution | Use for route metadata and capability change annotations, not for orchestration state itself |
| `maf_core/tools.py` | in-repo | Repo inspection and approval boundary | Use as the current tool seam for manager and specialist stages |
| `FileCheckpointStorage` via `maf_core/workflow_factory.py` | bundled | Durable workflow checkpointing | Use to preserve stage state inside a run-scoped runtime directory |
| `unittest` | stdlib | Existing automated validation baseline | Extend with orchestration, stage, and API contract coverage |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Shared orchestration contract above runtime and operator API | DevUI-only workflow state | Fast locally, but too brittle and too tied to a debug console |
| Promoting `repo_team` into a manager workflow | Keeping single-turn `repo_copilot` as the Phase 2 path | Simpler, but would not satisfy `ORCH-01` |
| Structured auto-answer artifacts | Pure transcript-based answers | Human-readable, but too weak for auditable orchestration decisions |

</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```text
maf_core/
|- orchestration.py          # shared stage names, stage state, pause reasons, artifact helpers
|- gsd_autofill.py           # project/phase/repo context resolver for routine GSD questions
|- team_factory.py           # manager-owned specialist workflow
|- workflow_factory.py       # run-scoped checkpoint and stage persistence helpers
autogen_dashboard/
|- session_runner.py         # durable run and stage lifecycle
|- schemas.py                # run + stage + auto-answer payload contract
|- app.py                    # operator API exposure for orchestration state
|- static/                   # temporary operator stage timeline and pause summary
state/
|- sessions/<run-id>/
|  |- artifacts/
|  |  |- stages/
|  |  |- gsd/
|  |  |- validation/
```

### Pattern 1: Manager-owned stage machine over specialist execution
**What:** The manager owns the canonical stage contract and delegates work to specialists as stage implementations rather than exposing free-form specialist chat as the product contract.
**When to use:** Always for Phase 2. Specialist visibility becomes richer later, but the manager state model must stabilize now.
**Example:** A run enters `planning`, persists a plan summary artifact, pauses for approval if needed, then advances to `research` without changing run identity.

### Pattern 2: Stage artifacts plus stage events, not transcript-derived state
**What:** Each stage produces both a persisted artifact and structured event sequence.
**When to use:** Always for pause/resume and later UI tabs.
**Example:** `stage.started`, `stage.completed`, and `stage.paused` emit alongside `artifacts/stages/planning.json`.

### Pattern 3: Context-first GSD auto-answering
**What:** Before asking the operator a routine GSD question, the manager attempts a structured answer from project docs, phase docs, workspace snapshot, and repo facts.
**When to use:** For routine clarification, planning defaults, and common assumptions.
**Example:** If a planning workflow asks about scope or default validation posture, the manager resolves it from `PROJECT.md`, `REQUIREMENTS.md`, and current phase context, then records that answer as a run artifact.

### Pattern 4: Capability-aware orchestration continuity
**What:** Orchestration state continues across provider fallback, but records whether tool use or capability changed.
**When to use:** Whenever the active turn falls through to CLI fallback or a downgraded model.
**Example:** A stage output remains valid, but the stage summary records that the turn completed through CLI fallback with tools unavailable.

### Anti-Patterns to Avoid
- **Transcript-derived stage state:** inferring progress only from chat text or DevUI events
- **Scope creep into specialist UI:** building per-agent panes in Phase 2 instead of stabilizing the manager contract
- **Unlogged auto-answering:** resolving GSD questions silently with no persisted reasoning trail
- **Full-run replay on stage retry:** redoing successful stages when only one stage failed

</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

Problems that already have strong in-repo primitives:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Specialist sequencing | A custom ad hoc agent chain runner | `maf_core/team_factory.py` + `SequentialBuilder` | Already models the current specialist flow |
| Pause and status vocabulary | Transcript parsing or UI-only flags | `autogen_dashboard/session_runner.py` + `autogen_dashboard/schemas.py` | Already has explicit run statuses and pause state seams |
| Run durability | A second persistence subsystem | Phase 1 run directory under `state/sessions/<run-id>/` | Already stores artifacts, attempts, events, and runtime state |
| Route metadata | A parallel routing log format | `maf_core/provider_fallback.py` additional properties | Already records provider/model/tier/capability information |
| Workspace summary | A new repo snapshot model | `autogen_dashboard/repo_context.py` | Already computes branch, dirty state, recent commits, and stack hints |

**Key insight:** Phase 2 succeeds by joining the active MAF workflow path to the durable run model. It should not create a third orchestration vocabulary.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Treating the current `repo_team` workflow as already complete
**What goes wrong:** The team sequence exists, but there is still no durable stage state contract, explicit stage artifacts, or shared pause model.
**How to avoid:** Wrap the specialist sequence in explicit manager-owned stage records and persisted outputs.

### Pitfall 2: Auto-answering routine questions without provenance
**What goes wrong:** The system becomes opaque; operators cannot tell what was inferred or from where.
**How to avoid:** Persist auto-answered GSD decisions under `artifacts/gsd/` and emit `gsd.answer.generated` or equivalent structured events.

### Pitfall 3: Using pause reasons inconsistently across runtime layers
**What goes wrong:** The MAF workflow, persisted run model, and UI show different state names or meanings.
**How to avoid:** Define one canonical pause and stage status vocabulary in a shared orchestration module and reuse it everywhere.

### Pitfall 4: Losing capability awareness after fallback
**What goes wrong:** A stage continues after CLI fallback as if tools were still available, leading to invalid assumptions.
**How to avoid:** Carry route and capability metadata into stage summaries and pause the run when a stage can no longer safely continue with the current capability set.

</common_pitfalls>

<code_examples>
## Code Examples

Verified in-repo patterns worth preserving:

### Sequential specialist workflow
```python
# Source: maf_core/team_factory.py
# Pattern: planner -> researcher -> implementer -> reviewer
# with request-info pauses at selected points.
```

### Durable operator-facing run state
```python
# Source: autogen_dashboard/session_runner.py
# Pattern: explicit run status, pause reason, background execution,
# persisted events, and workspace freshness tracking.
```

### Route and fallback metadata
```python
# Source: maf_core/provider_fallback.py
# Pattern: attach provider/model/tier/fallback metadata to responses,
# updates, and streams without rewriting the client surface.
```

</code_examples>

## Validation Architecture

Phase 2 validation should prove orchestration correctness rather than model quality.

- **Primary automated framework:** stdlib `unittest`
- **Quick verification target:** unit tests for stage-state transitions, auto-answer resolution, and pause/retry semantics
- **Broader verification target:** API contract tests for current stage, pause reason, stage artifacts, and structured events
- **Static sanity target:** compile smoke for touched Python modules and `node --check` for touched dashboard JS

Recommended commands once implementation lands:

- Quick manager/state check: `.\.venv\Scripts\python.exe -m unittest tests.test_phase2_manager`
- Runtime/API check: `.\.venv\Scripts\python.exe -m unittest tests.test_phase2_runtime tests.test_phase2_api`
- Full suite: `.\.venv\Scripts\python.exe -m unittest discover -s tests -v`
- Static sanity: `.\.venv\Scripts\python.exe -m compileall maf_core autogen_dashboard tests main.py`
- Frontend syntax: `node --check autogen_dashboard\static\app.js`

Focus the test map on:
- canonical stage order and stage persistence
- stage-scoped pause, resume, and retry behavior
- structured auto-answer artifacts and fallback to `needs_input`
- API payloads for current stage, last completed stage, pause reason, and stage timeline
- capability annotations when provider fallback changes available tools

<open_questions>
## Open Questions

1. **Should the manager workflow replace `repo_team` or wrap it?**
   - What we know: `repo_team` already expresses the specialist order.
   - Recommendation: preserve `repo_team` as the execution skeleton, but add a shared orchestration module that makes it a true manager-owned workflow.

2. **Where should routine GSD auto-answer logic live?**
   - What we know: the answer inputs span planning docs, repo facts, and run state.
   - Recommendation: keep it in `maf_core/` as a shared runtime helper, then mirror results into the operator run model through `session_runner.py`.

3. **How much operator UI should Phase 2 expose?**
   - What we know: `ORCH-02` requires visibility, but polished UX belongs later.
   - Recommendation: expose a compact stage timeline and stage summaries now, then defer premium styling and per-agent tabs to Phase 5 and Phase 3.

</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- `.planning/PROJECT.md` - product goal, autonomy target, and runtime constraints
- `.planning/REQUIREMENTS.md` - `ORCH-01`, `ORCH-02`, `ORCH-03`, `ORCH-04`
- `.planning/ROADMAP.md` - Phase 2 goal and success criteria
- `.planning/STATE.md` - current focus and known blockers
- `.planning/phases/02-manager-led-orchestration-core/02-CONTEXT.md` - locked Phase 2 decisions
- `.planning/phases/01-workspace-and-durable-run-foundation/01-CONTEXT.md` - locked Phase 1 durability contract
- `maf_core/team_factory.py` - current sequential specialist workflow
- `maf_core/workflow_factory.py` - checkpointed workflow seam
- `maf_core/agent_factory.py` - active agent construction and instructions seam
- `maf_core/tools.py` - repo tool and approval boundary
- `maf_core/provider_fallback.py` - route and capability metadata seam
- `autogen_dashboard/session_runner.py` - durable operator-facing run lifecycle
- `autogen_dashboard/schemas.py` - persisted run payload contract
- `README.md` - active runtime notes and current workflow surface
- `docs/DEVUI_CUSTOMIZATION.md` - DevUI limitations and local-console positioning

### Secondary (MEDIUM confidence)
- `.planning/codebase/ARCHITECTURE.md` - architecture map and current layering
- `.planning/codebase/STRUCTURE.md` - module placement guidance
- `.planning/codebase/CONVENTIONS.md` - code organization and testing norms
- `tests/test_phase1_runtime.py` - current runtime durability expectations
- `tests/test_phase1_api.py` - current operator API contract baseline
- `tests/test_maf_setup.py` - current MAF runtime and fallback smoke coverage

</sources>

<metadata>
## Metadata

**Research scope:**
- Active MAF workflow assembly and current multi-agent scaffolding
- Durable run-state and pause-state seams from Phase 1
- Current provider-routing metadata boundary
- Existing test surface for runtime and API contracts

**Confidence breakdown:**
- Manager contract direction: HIGH
- Pause/resume integration strategy: HIGH
- Automatic GSD answering strategy: HIGH
- Temporary operator surface scope: MEDIUM-HIGH

**Research date:** 2026-03-21
**Valid until:** 2026-04-20

</metadata>

---

*Phase: 02-manager-led-orchestration-core*
*Research completed: 2026-03-21*
*Ready for planning: yes*
