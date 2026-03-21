from __future__ import annotations

import os
import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from maf_starter.config import load_settings
from maf_starter.orchestration import (
    SPECIALIST_DEFAULT_HANDOFF_TARGETS,
    SPECIALIST_HANDOFF_FIELDS,
    SPECIALIST_ROLES,
    SPECIALIST_STAGE_MAP,
    SpecialistHandoff,
    SpecialistState,
    build_specialist_state,
    initialize_specialist_roster,
    specialist_role_for_stage,
)
from maf_starter.team_factory import build_repo_team


SCRATCH_ROOT = Path(__file__).resolve().parents[1] / ".tmp-tests"


class Phase3SpecialistTests(unittest.TestCase):
    def make_scratch_dir(self) -> Path:
        path = SCRATCH_ROOT / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path

    def test_initialize_specialist_roster_returns_full_not_started_roster(self) -> None:
        roster = initialize_specialist_roster()

        self.assertEqual(tuple(state.role for state in roster), SPECIALIST_ROLES)
        self.assertEqual(tuple(state.stage for state in roster), tuple(SPECIALIST_STAGE_MAP.values()))
        self.assertTrue(all(state.status == "not_started" for state in roster))
        self.assertTrue(all(state.current_task is None for state in roster))
        self.assertTrue(all(state.latest_output_summary is None for state in roster))
        self.assertTrue(all(state.started_at is None for state in roster))
        self.assertTrue(all(state.completed_at is None for state in roster))
        self.assertTrue(all(state.updated_at for state in roster))

    def test_specialist_state_and_handoff_round_trip(self) -> None:
        state = build_specialist_state(
            "planner",
            status="running",
            current_task="Draft the execution plan.",
            latest_output_summary="Draft ready for research.",
            last_handoff_target="researcher",
            last_handoff_reason="Need repo evidence before implementation.",
            started_at="2026-03-21T10:00:00+00:00",
            updated_at="2026-03-21T10:05:00+00:00",
        )
        restored_state = SpecialistState.from_dict(state.to_dict())

        self.assertEqual(restored_state.role, "planner")
        self.assertEqual(restored_state.stage, "planning")
        self.assertEqual(restored_state.status, "running")
        self.assertEqual(restored_state.current_task, "Draft the execution plan.")
        self.assertEqual(restored_state.latest_output_summary, "Draft ready for research.")
        self.assertEqual(restored_state.last_handoff_target, "researcher")
        self.assertEqual(restored_state.last_handoff_reason, "Need repo evidence before implementation.")
        self.assertEqual(restored_state.started_at, "2026-03-21T10:00:00+00:00")
        self.assertEqual(restored_state.updated_at, "2026-03-21T10:05:00+00:00")

        handoff = SpecialistHandoff(
            from_role="planner",
            to_role="researcher",
            reason="Need repo evidence before implementation.",
            requested_by="manager",
            status="requested",
            created_at="2026-03-21T10:05:00+00:00",
            updated_at="2026-03-21T10:06:00+00:00",
        )
        restored_handoff = SpecialistHandoff.from_dict(handoff.to_dict())

        self.assertEqual(restored_handoff.from_role, "planner")
        self.assertEqual(restored_handoff.to_role, "researcher")
        self.assertEqual(restored_handoff.reason, "Need repo evidence before implementation.")
        self.assertEqual(restored_handoff.requested_by, "manager")
        self.assertEqual(restored_handoff.status, "requested")
        self.assertEqual(restored_handoff.created_at, "2026-03-21T10:05:00+00:00")
        self.assertEqual(restored_handoff.updated_at, "2026-03-21T10:06:00+00:00")

        self.assertEqual(specialist_role_for_stage("planning"), "planner")
        self.assertEqual(SPECIALIST_DEFAULT_HANDOFF_TARGETS["planner"], "researcher")

    def test_build_repo_team_exposes_specialist_roster_and_metadata(self) -> None:
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

        self.assertEqual(workflow.manager_role, "manager")
        self.assertEqual(workflow.canonical_stages[0], "planning")
        self.assertEqual(workflow.name, "repo_team")
        self.assertIn("visible planner", workflow.description.lower())
        self.assertEqual(workflow.specialist_roles, SPECIALIST_ROLES)
        self.assertEqual(workflow.specialist_stage_map["researcher"], "research")
        self.assertEqual(workflow.specialist_handoff_fields, SPECIALIST_HANDOFF_FIELDS)
        self.assertEqual(workflow.specialist_profiles["planner"]["handoff_to"], "researcher")
        self.assertIn("current_task", workflow.specialist_profiles["reviewer"]["description"])
        self.assertEqual(tuple(state.role for state in workflow.specialist_roster), SPECIALIST_ROLES)
        self.assertTrue(all(state.status == "not_started" for state in workflow.specialist_roster))
        self.assertEqual(workflow.orchestration_template("run-xyz").current_stage, "planning")


if __name__ == "__main__":
    unittest.main()
