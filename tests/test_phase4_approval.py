from __future__ import annotations

import shutil
import subprocess
import unittest
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch

from autogen_dashboard.schemas import SessionCreateRequest, SessionDecisionRequest
from autogen_dashboard.session_runner import SessionService
from autogen_dashboard.session_store import SessionStore
from autogen_starter.config import Settings as DashboardSettings
from autogen_starter.providers import ProviderStatus
from maf_starter.approval_policy import ApprovalScope, classify_validation_commands, classify_write_operations
from maf_starter.validation_runner import ValidationCommand


SCRATCH_ROOT = Path(__file__).resolve().parents[1] / ".tmp-tests"


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
    return __import__("json").dumps(payload)


class Phase4ApprovalTests(unittest.IsolatedAsyncioTestCase):
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
                title="approval run",
                task="Inspect the repo",
                provider="gemini",
                model="gemini-2.5-pro",
                repo_root=str(repo_root),
            )
        )
        return service, created

    def test_classifiers_distinguish_routine_safe_destructive_blocked_and_external(self) -> None:
        safe_decision = classify_write_operations(
            [{"action": "update_file", "path": "README.md", "content": "# repo\n"}]
        )
        self.assertEqual(safe_decision.classification, "routine_safe")

        destructive = classify_write_operations(
            [{"action": "delete_file", "path": "README.md", "content": ""}]
        )
        self.assertEqual(destructive.classification, "destructive")
        self.assertIsInstance(destructive.scope, ApprovalScope)

        blocked = classify_write_operations(
            [{"action": "update_file", "path": ".env", "content": "SECRET=1\n"}]
        )
        self.assertEqual(blocked.classification, "blocked")

        external = classify_validation_commands(
            [
                ValidationCommand(
                    label="git push",
                    command=["git", "push"],
                    reason="Publish changes",
                    cwd="C:\\repo\\autogen",
                )
            ]
        )
        self.assertEqual(external.classification, "externally_visible")

    async def test_destructive_write_plan_pauses_with_pending_approval_scope(self) -> None:
        service, created = await self._create_service_and_session()

        stage_calls = [
            (stage_json("Plan ready.", needs_approval=True), "gemini", "gemini-2.5-pro", ["gemini:gemini-2.5-pro succeeded"]),
            (stage_json("Research complete."), "gemini", "gemini-2.5-pro", ["gemini:gemini-2.5-pro succeeded"]),
            (
                stage_json(
                    "Implementation wants to delete a file.",
                    file_operations=[
                        {
                            "action": "delete_file",
                            "path": "README.md",
                            "content": "",
                            "reason": "Remove the obsolete file.",
                        }
                    ],
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
        self.assertEqual(updated.pause_kind, "needs_approval")
        self.assertEqual(updated.current_stage, "implementation")
        self.assertIsNotNone(updated.pending_approval)
        assert updated.pending_approval is not None
        self.assertEqual(updated.pending_approval["risk_level"], "destructive")
        self.assertEqual(updated.pending_approval["affected_paths"], ["README.md"])
        self.assertIn("implementation", updated.stage_outputs)
        self.assertEqual(
            updated.stage_outputs["implementation"].pending_approval["risk_level"],
            "destructive",
        )


if __name__ == "__main__":
    unittest.main()
