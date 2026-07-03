from __future__ import annotations

import shutil
import subprocess
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from autogen_dashboard.app import create_app
from autogen_dashboard.dependencies import get_session_service
from autogen_dashboard.repo_context import discover_local_repos, resolve_repo_root
from autogen_dashboard.schemas import (
    RepoContext,
    RepoListResponse,
    RepoOption,
    SessionCreateResponse,
    SessionDetail,
)


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
    (path / "README.md").write_text(f"# {path.name}\n", encoding="utf-8")
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


class RepoScratchTestCase(unittest.TestCase):
    def make_scratch_dir(self) -> Path:
        path = SCRATCH_ROOT / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path


class FakeSessionService:
    def __init__(self, response: SessionDetail, repo_items: list[RepoOption]) -> None:
        self.response = response
        self.repo_items = repo_items
        self.create_calls: list[object] = []

    def available_repos(self) -> RepoListResponse:
        return RepoListResponse(items=self.repo_items)

    async def create_session(self, request):
        self.create_calls.append(request)
        return self.response


class WorkspaceContractTests(RepoScratchTestCase):
    def test_discover_local_repos_scans_recursively_and_skips_internal_dirs(self) -> None:
        scan_root = self.make_scratch_dir()
        alpha = scan_root / "alpha"
        beta = scan_root / "nested" / "tools" / "beta"
        ignored_state = scan_root / "state" / "ignored"
        ignored_tmp = scan_root / ".tmp-tests" / "ignored-again"

        init_repo(alpha)
        init_repo(beta)
        init_repo(ignored_state)
        init_repo(ignored_tmp)

        repos = discover_local_repos(scan_root)
        roots = {str(Path(item.root).resolve()) for item in repos}

        self.assertIn(str(alpha.resolve()), roots)
        self.assertIn(str(beta.resolve()), roots)
        self.assertNotIn(str(ignored_state.resolve()), roots)
        self.assertNotIn(str(ignored_tmp.resolve()), roots)
        self.assertTrue(all(item.root and item.path for item in repos))
        self.assertTrue(any(item.recent_commits for item in repos))

    def test_resolve_repo_root_blocks_escape_and_requires_git_repo(self) -> None:
        scan_root = self.make_scratch_dir()
        valid_repo = scan_root / "valid"
        init_repo(valid_repo)
        outside_root = self.make_scratch_dir()
        outside_repo = outside_root / "outside"
        init_repo(outside_repo)
        non_repo = scan_root / "plain-folder"
        non_repo.mkdir(parents=True, exist_ok=True)

        resolved = resolve_repo_root(str(valid_repo), scan_root)
        self.assertEqual(resolved, valid_repo.resolve())

        with self.assertRaises(ValueError):
            resolve_repo_root(str(outside_repo), scan_root)

        with self.assertRaises(ValueError):
            resolve_repo_root(str(non_repo), scan_root)

    def test_create_run_requires_workspace_and_task_and_returns_workspace_snapshot(self) -> None:
        repo_root = self.make_scratch_dir() / "workspace"
        init_repo(repo_root)
        snapshot = RepoContext(
            name="workspace",
            kind="repo",
            root=str(repo_root.resolve()),
            branch="main",
            dirty=False,
            changed_files=[],
            recent_commits=["abc123 init"],
            stack_hints=["Python"],
            scanned_at=utc_now(),
            signature="workspace|main|clean",
            error=None,
        )
        response = SessionCreateResponse(
            id="run-001",
            title="workspace: Reply with exactly READY",
            provider="gemini",
            model="gemini-2.5-pro",
            original_task="Reply with exactly READY",
            latest_human_note=None,
            workspace_kind="repo",
            workspace_snapshot=snapshot,
            attempt_count=0,
            last_provider_used=None,
            last_model_used=None,
            last_attempts=[],
            last_fallback_count=0,
            repo_root=snapshot.root,
            repo_context=snapshot,
            status="queued",
            pause_reason="not_started",
            pause_title="Queued prompt",
            pause_detail="The initial prompt is ready to run.",
            system_message="You are a test assistant.",
            queued_prompt="Reply with exactly READY",
            last_prompt="Reply with exactly READY",
            last_error=None,
            last_assistant_message=None,
            last_stop_reason=None,
            created_at=utc_now(),
            updated_at=utc_now(),
            last_run_at=None,
            transcript_count=1,
            event_count=1,
            transcript=[],
            events=[],
            state_saved=False,
        )
        repo_items = [
            RepoOption(
                name="workspace",
                path=snapshot.root,
                root=snapshot.root,
                kind="repo",
                branch="main",
                dirty=False,
                detail="repo | main | clean | Python",
                changed_files=[],
                recent_commits=["abc123 init"],
                stack_hints=["Python"],
                scanned_at=snapshot.scanned_at,
                signature=snapshot.signature,
            )
        ]
        fake_service = FakeSessionService(response=response, repo_items=repo_items)
        app = create_app()
        app.dependency_overrides[get_session_service] = lambda: fake_service
        client = TestClient(app)

        empty_task = client.post(
            "/api/sessions",
            json={"repo_root": snapshot.root, "task": "   ", "provider": "gemini"},
        )
        self.assertEqual(empty_task.status_code, 400)
        self.assertEqual(len(fake_service.create_calls), 0)

        missing_workspace = client.post(
            "/api/sessions",
            json={"task": "Reply with exactly READY", "provider": "gemini"},
        )
        self.assertEqual(missing_workspace.status_code, 400)
        self.assertEqual(len(fake_service.create_calls), 0)

        created = client.post(
            "/api/sessions",
            json={
                "repo_root": snapshot.root,
                "task": "Reply with exactly READY",
                "provider": "gemini",
                "model": "gemini-2.5-pro",
            },
        )
        self.assertEqual(created.status_code, 200)
        body = created.json()
        self.assertEqual(body["title"], "workspace: Reply with exactly READY")
        self.assertEqual(body["original_task"], "Reply with exactly READY")
        self.assertEqual(body["workspace_kind"], "repo")
        self.assertEqual(body["workspace_snapshot"]["root"], snapshot.root)
        self.assertEqual(body["attempt_count"], 0)
        self.assertEqual(len(fake_service.create_calls), 1)


if __name__ == "__main__":
    unittest.main()
