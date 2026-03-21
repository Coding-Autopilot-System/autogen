from maf_starter.team_factory import build_repo_team


workflow = build_repo_team()
workflow.description = (
    "Manager-led orchestration workflow for engineering runs with planner, researcher, "
    "implementer, reviewer, and terminal validation stage visibility."
)
