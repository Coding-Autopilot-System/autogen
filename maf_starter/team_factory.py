from __future__ import annotations

from dataclasses import replace

from agent_framework_orchestrations import SequentialBuilder

from maf_starter.agent_factory import build_agent, build_agent_for_model
from maf_starter.config import Settings, load_settings
from maf_starter.workflow_factory import RunScopedFileCheckpointStorage


def build_repo_team(settings: Settings | None = None):
    current = settings or load_settings()
    current.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    planner = build_agent_for_model(
        "gemini-2.5-pro",
        settings=current,
        agent_name="planner",
        description="Turns user intent into an execution plan.",
        role_instructions=(
            "You are the planner. Produce a crisp plan with assumptions, risks, and recommended execution order. "
            "Do not implement. End by asking for approval if the work implies code or config changes."
        ),
    )
    researcher = build_agent_for_model(
        "gemini-2.5-flash",
        settings=current,
        agent_name="researcher",
        description="Inspects the repo and gathers the facts needed for implementation.",
        role_instructions=(
            "You are the researcher. Use the repo tools to gather relevant file paths, configs, and evidence. "
            "Prefer facts over speculation."
        ),
    )
    implementer = build_agent_for_model(
        "gemini-2.5-pro",
        settings=current,
        agent_name="implementer",
        description="Proposes or implements the concrete technical change.",
        role_instructions=(
            "You are the implementer. Turn the approved plan and research into a concrete technical proposal. "
            "Be explicit about changed files, commands, and validation steps."
        ),
    )
    reviewer = build_agent_for_model(
        "gemini-2.5-pro",
        settings=current,
        agent_name="reviewer",
        description="Finds bugs, regressions, and validation gaps.",
        role_instructions=(
            "You are the reviewer. Focus on risks, regressions, missing tests, and weak assumptions. "
            "Prefer findings over praise."
        ),
    )

    workflow = (
        SequentialBuilder(
            participants=[planner, researcher, implementer, reviewer],
            checkpoint_storage=RunScopedFileCheckpointStorage(current.checkpoint_dir / "repo-team"),
            intermediate_outputs=True,
        )
        .with_request_info(agents=["planner", "implementer", "reviewer"])
        .build()
    )
    workflow.name = "repo_team"
    workflow.description = (
        "Sequential specialist workflow: planner -> researcher -> implementer -> reviewer, "
        "with human request-info pauses after key stages."
    )
    return workflow
