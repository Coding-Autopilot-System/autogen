from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from maf_starter.config import load_settings
from maf_starter.orchestration import (
    CANONICAL_STAGE_NAMES,
    RunOrchestrationState,
    StageSummary,
    orchestration_state_path_for_checkpoint,
    stage_summary_path_for_checkpoint,
)
from maf_starter.team_factory import build_repo_team
from maf_starter.workflow_factory import RunScopedWorkflowArtifacts


SCRATCH_ROOT = Path(__file__).resolve().parents[1] / ".tmp-tests"


class Phase2ManagerTests(unittest.TestCase):
    def make_scratch_dir(self) -> Path:
        path = SCRATCH_ROOT / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path

    def test_run_orchestration_state_uses_canonical_stage_order_and_round_trips(self) -> None:
        state = RunOrchestrationState.new("run-001")
        self.assertEqual(tuple(record.stage for record in state.stage_records), CANONICAL_STAGE_NAMES)
        self.assertEqual(state.current_stage, "planning")

        state.start_stage("planning")
        state.complete_stage(
            "planning",
            StageSummary(
                stage="planning",
                summary="Plan agreed.",
                artifacts=["artifacts/stages/planning/summary.json"],
                next_action="Run research.",
                needs_approval=True,
            ),
        )
        state.retry_stage("research")

        restored = RunOrchestrationState.from_dict(state.to_dict())
        self.assertEqual(restored.last_completed_stage, "planning")
        self.assertEqual(restored.current_stage, "research")
        self.assertEqual(restored.stage_outputs()["planning"]["summary"], "Plan agreed.")

    def test_stage_pause_and_retry_are_stage_scoped(self) -> None:
        state = RunOrchestrationState.new("run-002")
        state.start_stage("planning")
        state.complete_stage("planning", StageSummary(stage="planning", summary="ok"))
        state.start_stage("research")
        state.pause_stage(
            "research",
            "needs_input",
            summary=StageSummary(
                stage="research",
                summary="Need target repo confirmation.",
                needs_input=True,
                blocked_questions=["Which repo should I inspect?"],
            ),
            blocked_questions=["Which repo should I inspect?"],
        )

        self.assertEqual(state.last_completed_stage, "planning")
        self.assertEqual(state.current_stage, "research")
        self.assertEqual(state.pause_kind, "needs_input")
        self.assertEqual(state.get_record("research").blocked_questions, ["Which repo should I inspect?"])

        state.retry_stage("research")
        self.assertEqual(state.current_stage, "research")
        self.assertEqual(state.get_record("research").status, "pending")
        self.assertEqual(state.last_completed_stage, "planning")

    def test_run_scoped_workflow_artifact_layout_uses_runtime_orchestration_and_stage_paths(self) -> None:
        scratch = self.make_scratch_dir()
        checkpoint_dir = scratch / "state" / "sessions" / "run-001" / "runtime" / "checkpoint"
        layout = RunScopedWorkflowArtifacts(checkpoint_dir).ensure()

        self.assertEqual(layout.orchestration_state_path, orchestration_state_path_for_checkpoint(checkpoint_dir))
        self.assertEqual(
            stage_summary_path_for_checkpoint(checkpoint_dir, "planning"),
            scratch / "state" / "sessions" / "run-001" / "artifacts" / "stages" / "planning" / "summary.json",
        )
        self.assertTrue(layout.orchestration_dir.exists())
        self.assertTrue(layout.stage_artifacts_dir.exists())

    def test_build_repo_team_exposes_manager_led_description_and_template(self) -> None:
        scratch = self.make_scratch_dir()
        entities = scratch / "entities"
        repo = scratch / "repo"
        entities.mkdir()
        repo.mkdir()
        (repo / "README.md").write_text("hello", encoding="utf-8")

        with patch.dict(
            "os.environ",
            {
                "MAF_API_KEY": "test-key",
                "MAF_MODEL": "gemini-2.5-flash",
                "MAF_REPO_ROOT": str(repo),
                "MAF_ENTITIES_DIR": str(entities),
                "MAF_CHECKPOINT_DIR": str(scratch / "state"),
            },
            clear=False,
        ):
            settings = load_settings(project_root=scratch, env_path=scratch / ".missing-env")
            workflow = build_repo_team(settings)

        self.assertTrue(hasattr(workflow, "run"))
        self.assertIn("manager-led", workflow.description.lower())
        self.assertEqual(workflow.canonical_stages[0], "planning")
        self.assertEqual(workflow.orchestration_template("run-xyz").current_stage, "planning")


if __name__ == "__main__":
    unittest.main()
