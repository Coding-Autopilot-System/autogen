from __future__ import annotations

from dataclasses import dataclass

from agent_framework_orchestrations import SequentialBuilder

from maf_starter.agent_factory import build_agent, build_agent_for_model
from maf_starter.config import Settings, load_settings
from maf_starter.orchestration import (
    CANONICAL_STAGE_NAMES,
    RunOrchestrationState,
    SPECIALIST_HANDOFF_FIELDS,
    SPECIALIST_DEFAULT_HANDOFF_TARGETS,
    SPECIALIST_ROLES,
    SPECIALIST_STAGE_MAP,
    STAGE_AGENT_MAP,
    StageName,
    initialize_specialist_roster,
)
from maf_starter.workflow_factory import RunScopedFileCheckpointStorage
from maf_starter.workflow_factory import RunScopedWorkflowArtifacts


@dataclass
class ManagerLedWorkflow:
    workflow: object
    artifact_layout: RunScopedWorkflowArtifacts
    canonical_stages: tuple[StageName, ...] = CANONICAL_STAGE_NAMES
    manager_agent: str = "manager"

    def __getattr__(self, name: str):
        return getattr(self.workflow, name)

    async def run(self, *args, **kwargs):
        return await self.workflow.run(*args, **kwargs)

    def orchestration_template(self, run_id: str = "template") -> RunOrchestrationState:
        return RunOrchestrationState.new(run_id)


def _stage_role_instructions(stage: StageName, specialty: str, fallback_note: str = "") -> str:
    stage_owner = STAGE_AGENT_MAP[stage]
    parts = [
        f"You own the {stage} stage as the {stage_owner}. {specialty}",
        "Return a structured stage handoff as JSON with keys "
        "`summary`, `artifacts`, `next_action`, `needs_approval`, `needs_input`, `blocked_questions`, "
        "`current_task`, `latest_output_summary`, `handoff_to`, and `handoff_reason`.",
        "Be explicit when the stage can proceed automatically versus when the human must intervene.",
    ]
    if fallback_note:
        parts.append(fallback_note)
    return " ".join(parts)


def _specialist_description(role: str, stage: StageName, summary: str) -> str:
    return (
        f"{role.title()} specialist for the {stage} stage. {summary} "
        "Publishes current_task, latest_output_summary, handoff_to, and handoff_reason metadata."
    )


def _specialist_profile(role: str, stage: StageName, summary: str) -> dict[str, str]:
    return {
        "role": role,
        "stage": stage,
        "description": _specialist_description(role, stage, summary),
        "handoff_to": SPECIALIST_DEFAULT_HANDOFF_TARGETS[role],
        "handoff_reason_field": "handoff_reason",
        "current_task_field": "current_task",
        "latest_output_summary_field": "latest_output_summary",
    }


def build_repo_team(settings: Settings | None = None):
    current = settings or load_settings()
    artifact_layout = RunScopedWorkflowArtifacts(current.checkpoint_dir / "repo-team").ensure()

    planner = build_agent_for_model(
        "gemini-2.5-pro",
        settings=current,
        agent_name="planner",
        description=_specialist_description(
            "planner",
            "planning",
            "Turns user intent into an execution plan and hands off to research with crisp constraints.",
        ),
        role_instructions=_stage_role_instructions(
            "planning",
            "Produce a crisp plan with assumptions, risks, and recommended execution order. Do not implement. "
            "Emit current_task before work begins, latest_output_summary after each turn, and handoff_to/handoff_reason "
            "when passing to the researcher.",
            "Default `needs_approval` to true when the work implies code, config, or deployment changes.",
        ),
    )
    researcher = build_agent_for_model(
        "gemini-2.5-flash",
        settings=current,
        agent_name="researcher",
        description=_specialist_description(
            "researcher",
            "research",
            "Inspects the repo, gathers facts, and hands implementation-ready evidence to the implementer.",
        ),
        role_instructions=_stage_role_instructions(
            "research",
            "Use the repo tools to gather relevant file paths, configs, and evidence. Prefer facts over speculation. "
            "Emit current_task, latest_output_summary, handoff_to, and handoff_reason so downstream stages can see "
            "what evidence was collected.",
        ),
    )
    implementer = build_agent_for_model(
        "gemini-2.5-pro",
        settings=current,
        agent_name="implementer",
        description=_specialist_description(
            "implementer",
            "implementation",
            "Proposes or implements the concrete technical change and hands review-ready output to the reviewer.",
        ),
        role_instructions=_stage_role_instructions(
            "implementation",
            "Turn the approved plan and research into a concrete technical proposal. "
            "Be explicit about changed files, commands, and validation steps. "
            "Use current_task, latest_output_summary, handoff_to, and handoff_reason so the reviewer can see the exact "
            "implementation handoff.",
        ),
    )
    reviewer = build_agent_for_model(
        "gemini-2.5-pro",
        settings=current,
        agent_name="reviewer",
        description=_specialist_description(
            "reviewer",
            "review",
            "Finds bugs, regressions, and validation gaps before the manager synthesizes the final validation step.",
        ),
        role_instructions=_stage_role_instructions(
            "review",
            "Focus on risks, regressions, missing tests, and weak assumptions. Prefer findings over praise. "
            "Record current_task, latest_output_summary, handoff_to, and handoff_reason so the manager can see if the "
            "work is ready to advance.",
        ),
    )

    workflow = (
        SequentialBuilder(
            participants=[planner, researcher, implementer, reviewer],
            checkpoint_storage=RunScopedFileCheckpointStorage(artifact_layout.checkpoint_dir),
            intermediate_outputs=True,
        )
        .with_request_info(agents=["planner", "implementer", "reviewer"])
        .build()
    )
    workflow.name = "repo_team"
    workflow.description = (
        "Manager-led orchestration workflow for engineering runs. "
        "The manager owns the canonical planning -> research -> implementation -> review -> validation sequence, "
        "with visible planner, researcher, implementer, and reviewer specialists that publish current_task, "
        "latest_output_summary, handoff_to, and handoff_reason metadata alongside human request-info pauses."
    )
    workflow.manager_role = "manager"
    workflow.canonical_stages = CANONICAL_STAGE_NAMES
    workflow.stage_agent_map = dict(STAGE_AGENT_MAP)
    workflow.specialist_roles = SPECIALIST_ROLES
    workflow.specialist_stage_map = dict(SPECIALIST_STAGE_MAP)
    workflow.specialist_handoff_fields = SPECIALIST_HANDOFF_FIELDS
    workflow.specialist_profiles = {
        "manager": _specialist_profile(
            "manager",
            "validation",
            "Owns the canonical run and passes implementation-ready work to the planner.",
        ),
        "planner": _specialist_profile(
            "planner",
            "planning",
            "Turns user intent into an execution plan and hands off to research with crisp constraints.",
        ),
        "researcher": _specialist_profile(
            "researcher",
            "research",
            "Inspects the repo, gathers facts, and hands implementation-ready evidence to the implementer.",
        ),
        "implementer": _specialist_profile(
            "implementer",
            "implementation",
            "Proposes or implements the concrete technical change and hands review-ready output to the reviewer.",
        ),
        "reviewer": _specialist_profile(
            "reviewer",
            "review",
            "Finds bugs, regressions, and validation gaps before the manager synthesizes the final validation step.",
        ),
    }
    workflow.specialist_roster = tuple(initialize_specialist_roster())
    workflow.orchestration_layout = artifact_layout
    return ManagerLedWorkflow(
        workflow=workflow,
        artifact_layout=artifact_layout,
    )
