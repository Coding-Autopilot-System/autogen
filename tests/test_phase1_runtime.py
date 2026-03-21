from __future__ import annotations

import shutil
import subprocess
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

from autogen_dashboard.schemas import SessionCreateRequest, SessionDecisionRequest, TranscriptMessage
from autogen_dashboard.session_runner import RunOutcome, SessionService
from autogen_dashboard.session_store import SessionStore
from autogen_starter.config import Settings
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


def make_settings(project_root: Path, scan_root: Path, state_dir: Path) -> Settings:
    return Settings(
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


class Phase1RuntimeTests(unittest.IsolatedAsyncioTestCase):
    def make_scratch_dir(self) -> Path:
        path = SCRATCH_ROOT / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path

    async def test_retry_preserves_original_task_and_reopened_run_has_attempt_history(self) -> None:
        scratch = self.make_scratch_dir()
        repo_root = scratch / "repo"
        init_repo(repo_root)
        settings = make_settings(scratch, scratch, scratch / "state")
        store = SessionStore(settings.state_dir / "sessions")
        service = SessionService(settings=settings, store=store)

        prompts: list[str] = []

        async def fake_run_turn(**kwargs):
            prompts.append(kwargs["prompt"])
            return RunOutcome(
                assistant_messages=[
                    TranscriptMessage(
                        id=uuid.uuid4().hex,
                        role="assistant",
                        content=f"handled: {kwargs['prompt']}",
                        source="assistant",
                        created_at=utc_now(),
                        metadata={},
                    )
                ],
                stop_reason="Maximum number of turns 1 reached.",
                state_snapshot={"attempt": len(prompts)},
                provider_used="gemini",
                model_used="gemini-2.5-pro",
                attempt_log=["gemini:gemini-2.5-pro succeeded"],
            )

        ready_providers = [ProviderStatus("gemini", True, "ready")]

        with patch("autogen_dashboard.session_runner.collect_provider_statuses", return_value=ready_providers):
            with patch.object(service, "_run_team_turn", new=AsyncMock(side_effect=fake_run_turn)):
                created = await service.create_session(
                    SessionCreateRequest(
                        title="repo run",
                        task="Inspect the repo",
                        provider="gemini",
                        model="gemini-2.5-pro",
                        repo_root=str(repo_root),
                    )
                )
                self.assertEqual(created.status, "queued")
                self.assertEqual(created.original_task, "Inspect the repo")
                self.assertEqual(created.attempt_count, 0)

                await service.run_step(created.id)
                first_task = service._session_runtime(created.id).active_task
                self.assertIsNotNone(first_task)
                await first_task

                after_first = service.get_session(created.id)
                self.assertEqual(after_first.status, "waiting")
                self.assertEqual(after_first.latest_attempt_id, "attempt-001")
                self.assertEqual(after_first.attempt_count, 1)
                self.assertEqual(prompts[0], "Inspect the repo")

                approved = await service.approve(
                    created.id,
                    SessionDecisionRequest(note="APPROVE once the retry path is ready"),
                )
                self.assertEqual(approved.original_task, "Inspect the repo")
                self.assertEqual(approved.latest_human_note, "APPROVE once the retry path is ready")
                self.assertEqual(approved.approval_decisions[-1].decision, "approve")

                await service.retry(created.id)
                second_task = service._session_runtime(created.id).active_task
                self.assertIsNotNone(second_task)
                await second_task

                reopened = service.get_session(created.id)
                self.assertEqual(prompts[-1], "Inspect the repo")
                self.assertEqual(reopened.original_task, "Inspect the repo")
                self.assertEqual(reopened.latest_attempt_id, "attempt-002")
                self.assertEqual(reopened.attempt_count, 2)
                self.assertGreaterEqual(len(reopened.transcript), 3)
                self.assertGreaterEqual(len(reopened.events), 5)
                self.assertIn("attempts", reopened.artifact_manifest)
                self.assertEqual(reopened.artifact_manifest["attempts"][-1]["attempt_id"], "attempt-002")


if __name__ == "__main__":
    unittest.main()
