from __future__ import annotations

from dataclasses import dataclass

from agent_framework_orchestrations import SequentialBuilder

from maf_starter.agent_factory import build_agent, build_agent_for_model
from maf_starter.config import Settings, load_settings
from maf_starter.orchestration import CANONICAL_STAGE_NAMES, RunOrchestrationState, STAGE_AGENT_MAP, StageName
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
    return (
        f"You own the {stage} stage as the {stage_owner}. {specialty} "
        "Return a structured stage handoff as JSON with keys "
        "`summary`, `artifacts`, `next_action`, `needs_approval`, `needs_input`, and `blocked_questions`. "
        "Be explicit when the stage can proceed automatically versus when the human must intervene. "
        f"{fallback_note}".strip()
    )


def build_repo_team(settings: Settings | None = None):
    current = settings or load_settings()
    artifact_layout = RunScopedWorkflowArtifacts(current.checkpoint_dir / "repo-team").ensure()

    planner = build_agent_for_model(
        "gemini-2.5-pro",
        settings=current,
        agent_name="planner",
        description="Turns user intent into an execution plan.",
        role_instructions=_stage_role_instructions(
            "planning",
            "Produce a crisp plan with assumptions, risks, and recommended execution order. Do not implement.",
            "Default `needs_approval` to true when the work implies code, config, or deployment changes.",
        ),
    )
    researcher = build_agent_for_model(
        "gemini-2.5-flash",
        settings=current,
        agent_name="researcher",
        description="Inspects the repo and gathers the facts needed for implementation.",
        role_instructions=_stage_role_instructions(
            "research",
            "Use the repo tools to gather relevant file paths, configs, and evidence. Prefer facts over speculation.",
        ),
    )
    implementer = build_agent_for_model(
        "gemini-2.5-pro",
        settings=current,
        agent_name="implementer",
        description="Proposes or implements the concrete technical change.",
        role_instructions=_stage_role_instructions(
            "implementation",
            "Turn the approved plan and research into a concrete technical proposal. "
            "Be explicit about changed files, commands, and validation steps.",
        ),
    )
    reviewer = build_agent_for_model(
        "gemini-2.5-pro",
        settings=current,
        agent_name="reviewer",
        description="Finds bugs, regressions, and validation gaps.",
        role_instructions=_stage_role_instructions(
            "review",
            "Focus on risks, regressions, missing tests, and weak assumptions. Prefer findings over praise.",
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
        "with specialist participants and human request-info pauses after key stages."
    )
    workflow.canonical_stages = CANONICAL_STAGE_NAMES
    workflow.stage_agent_map = dict(STAGE_AGENT_MAP)
    workflow.orchestration_layout = artifact_layout
    return ManagerLedWorkflow(
        workflow=workflow,
        artifact_layout=artifact_layout,
    )
