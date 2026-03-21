from __future__ import annotations

import json
import shutil
import subprocess
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

from autogen_dashboard.schemas import SessionCreateRequest, SessionDecisionRequest
from autogen_dashboard.session_runner import SessionService
from autogen_dashboard.session_store import SessionStore
from autogen_starter.config import Settings as DashboardSettings
from autogen_starter.providers import ProviderStatus


SCRATCH_ROOT = Path(__file__).resolve().parents[1] / ".tmp-tests"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _git(args: list[str], *, cwd: Path) -> None:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=20,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise RuntimeError(detail)


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(["init"], cwd=path)
    (path / "README.md").write_text("# repo\n", encoding="utf-8")
    _git(["add", "README.md"], cwd=path)
    _git(
        [
            "-c",
            "user.name=Test User",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-m",
            "init",
        ],
        cwd=path,
    )


def make_settings(project_root: Path, scan_root: Path, state_dir: Path) -> DashboardSettings:
    return DashboardSettings(
        provider="gemini",
        approval_word="APPROVE",
        state_dir=state_dir,
        state_file_name="team_state.json",
        repo_scan_root=scan_root,
        ollama_model="phi3:mini",
        ollama_host=None,
        openai_model="gpt-4.1-mini",
        openai_api_key=None,
        openai_base_url=None,
        gemini_model="gemini-2.5-pro",
        gemini_api_key="test-key",
        gemini_base_url="https://example.invalid",
        anthropic_model="claude-sonnet-4-20250514",
        anthropic_api_key=None,
        azure_openai_model="gpt-4o",
        azure_openai_deployment=None,
        azure_openai_endpoint=None,
        azure_openai_api_version="2024-06-01",
        azure_openai_api_key=None,
        codex_cli_command="codex.cmd",
        codex_cli_model=None,
        gemini_cli_command="gemini.cmd",
        claude_cli_command="claude",
        claude_cli_model=None,
        claude_code_git_bash_path=None,
    )


def stage_json(summary: str, **extra) -> str:
    payload = {
        "summary": summary,
        "artifacts": [],
        "next_action": None,
        "needs_approval": False,
        "needs_input": False,
        "blocked_questions": [],
    }
    payload.update(extra)
    return json.dumps(payload)


class Phase2RuntimeTests(unittest.IsolatedAsyncioTestCase):
    def make_scratch_dir(self) -> Path:
        path = SCRATCH_ROOT / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path

    async def _create_service_and_session(self):
        scratch = self.make_scratch_dir()
        repo_root = scratch / "repo"
        init_repo(repo_root)
        settings = make_settings(scratch, scratch, scratch / "state")
        store = SessionStore(settings.state_dir / "sessions")
        service = SessionService(settings=settings, store=store)
        ready_providers = [ProviderStatus("gemini", True, "ready")]
        provider_patch = patch("autogen_dashboard.session_runner.collect_provider_statuses", return_value=ready_providers)
        provider_patch.start()
        self.addCleanup(provider_patch.stop)
        created = await service.create_session(
            SessionCreateRequest(
                title="repo run",
                task="Inspect the repo",
                provider="gemini",
                model="gemini-2.5-pro",
                repo_root=str(repo_root),
            )
        )
        return service, store, created, repo_root

    async def test_planning_stage_pauses_for_approval_and_persists_stage_output(self) -> None:
        service, store, created, _repo_root = await self._create_service_and_session()

        with patch.object(
            service,
            "_run_stage_prompt",
            new=AsyncMock(return_value=(stage_json("Plan ready.", needs_approval=True), "gemini", "gemini-2.5-pro", ["gemini:gemini-2.5-pro succeeded"])),
        ):
            await service.run_step(created.id)
            await service._session_runtime(created.id).active_task

        updated = service.get_session(created.id)
        self.assertEqual(updated.pause_kind, "needs_approval")
        self.assertEqual(updated.current_stage, "research")
        self.assertEqual(updated.last_completed_stage, "planning")
        self.assertIn("planning", updated.stage_outputs)
        self.assertTrue(store.stage_summary_path(created.id, "planning").exists())
        event_types = [event.type for event in updated.events]
        self.assertIn("stage.started", event_types)
        self.assertIn("stage.completed", event_types)
        self.assertIn("stage.paused", event_types)

    async def test_unresolved_question_pauses_same_stage_and_persists_blocked_question(self) -> None:
        service, store, created, _repo_root = await self._create_service_and_session()

        stage_calls = [
            (stage_json("Plan ready.", needs_approval=True), "gemini", "gemini-2.5-pro", ["gemini:gemini-2.5-pro succeeded"]),
            (
                stage_json(
                    "Need target deployment details.",
                    needs_input=True,
                    blocked_questions=["Which Azure resource group should I target?"],
                ),
                "gemini",
                "gemini-2.5-pro",
                ["gemini:gemini-2.5-pro succeeded"],
            ),
        ]

        with patch.object(service, "_run_stage_prompt", new=AsyncMock(side_effect=stage_calls)):
            await service.run_step(created.id)
            await service._session_runtime(created.id).active_task
            await service.approve(created.id, SessionDecisionRequest(note="Proceed"))
            await service.run_step(created.id)
            await service._session_runtime(created.id).active_task

        updated = service.get_session(created.id)
        self.assertEqual(updated.pause_kind, "needs_input")
        self.assertEqual(updated.current_stage, "research")
        self.assertEqual(updated.last_completed_stage, "planning")
        self.assertEqual(updated.blocked_questions, ["Which Azure resource group should I target?"])
        self.assertTrue(store.blocked_questions_path(created.id).exists())
        self.assertEqual(updated.stage_timeline[1].status, "paused")

    async def test_auto_answer_allows_stage_flow_to_finish_without_manual_clarification(self) -> None:
        service, store, created, _repo_root = await self._create_service_and_session()

        stage_calls = [
            (stage_json("Plan ready.", needs_approval=True), "gemini", "gemini-2.5-pro", ["gemini:gemini-2.5-pro succeeded"]),
            (
                stage_json(
                    "Need a routine clarification before research can continue.",
                    needs_input=True,
                    blocked_questions=["What phase are we in?"],
                ),
                "gemini",
                "gemini-2.5-pro",
                ["gemini:gemini-2.5-pro succeeded"],
            ),
            (stage_json("Research complete."), "gemini", "gemini-2.5-pro", ["gemini:gemini-2.5-pro succeeded"]),
            (stage_json("Implementation plan complete."), "gemini", "gemini-2.5-pro", ["gemini:gemini-2.5-pro succeeded"]),
            (stage_json("Review complete."), "gemini", "gemini-2.5-pro", ["gemini:gemini-2.5-pro succeeded"]),
        ]

        with patch.object(service, "_run_stage_prompt", new=AsyncMock(side_effect=stage_calls)):
            await service.run_step(created.id)
            await service._session_runtime(created.id).active_task
            await service.approve(created.id, SessionDecisionRequest(note="Proceed"))
            await service.run_step(created.id)
            await service._session_runtime(created.id).active_task

        updated = service.get_session(created.id)
        self.assertEqual(updated.status, "completed")
        self.assertEqual(updated.pause_kind, "completed")
        self.assertEqual(updated.last_completed_stage, "validation")
        self.assertGreaterEqual(len(updated.auto_answer_records), 1)
        self.assertTrue(store.auto_answers_path(created.id).exists())
        self.assertTrue(store.stage_summary_path(created.id, "validation").exists())
        event_types = [event.type for event in updated.events]
        self.assertIn("gsd.answer.generated", event_types)
        self.assertIn("stage.completed", event_types)


if __name__ == "__main__":
    unittest.main()
