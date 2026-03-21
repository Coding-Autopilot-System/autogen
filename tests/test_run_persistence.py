from __future__ import annotations

import shutil
import subprocess
import unittest
import uuid
from datetime import datetime, timezone
from pathlib import Path

from autogen_dashboard.schemas import RepoContext, SessionSummary, TranscriptMessage
from autogen_dashboard.session_store import SessionStore


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


def make_workspace_snapshot(repo_root: Path) -> RepoContext:
    return RepoContext(
        name=repo_root.name,
        kind="repo",
        root=str(repo_root.resolve()),
        branch="main",
        dirty=False,
        changed_files=[],
        recent_commits=["abc123 init"],
        stack_hints=["Python"],
        scanned_at=utc_now(),
        signature=f"{repo_root.name}|main|clean",
        error=None,
    )


def make_summary(session_id: str, repo_root: Path) -> SessionSummary:
    snapshot = make_workspace_snapshot(repo_root)
    now = utc_now()
    return SessionSummary(
        id=session_id,
        title=f"{repo_root.name}: durable run",
        provider="gemini",
        model="gemini-2.5-pro",
        original_task="Review the repo",
        latest_human_note=None,
        approval_decisions=[],
        retry_seed_prompt=None,
        workspace_kind="repo",
        workspace_snapshot=snapshot,
        attempt_count=0,
        latest_attempt_id=None,
        artifact_manifest={},
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
        queued_prompt="Review the repo",
        last_prompt=None,
        last_error=None,
        last_assistant_message=None,
        last_stop_reason=None,
        created_at=now,
        updated_at=now,
        last_run_at=None,
        transcript_count=0,
        event_count=0,
    )


class RunPersistenceTests(unittest.TestCase):
    def make_scratch_dir(self) -> Path:
        path = SCRATCH_ROOT / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path

    def test_run_directory_contains_artifacts_runtime_and_attempts(self) -> None:
        scratch = self.make_scratch_dir()
        repo_root = scratch / "repo"
        init_repo(repo_root)
        store = SessionStore(scratch / "state" / "sessions")
        summary = make_summary("run-001", repo_root)

        detail = store.create_session(
            summary,
            [
                TranscriptMessage(
                    id="msg-001",
                    role="user",
                    content="Review the repo",
                    source="user",
                    created_at=utc_now(),
                    metadata={"kind": "task"},
                )
            ],
        )

        store.save_state(summary.id, {"cursor": 1})
        store.save_attempt_summary(
            summary.id,
            "attempt-001",
            {"attempt_id": "attempt-001", "status": "running", "prompt": "Review the repo"},
        )

        session_dir = store.session_dir(summary.id)
        self.assertTrue((session_dir / "metadata.json").exists())
        self.assertTrue((session_dir / "transcript.json").exists())
        self.assertTrue((session_dir / "events.jsonl").exists())
        self.assertTrue((session_dir / "artifacts" / "manifest.json").exists())
        self.assertTrue((session_dir / "artifacts" / "workspace" / "creation.json").exists())
        self.assertTrue((session_dir / "runtime").exists())
        self.assertTrue((session_dir / "runtime" / "state.json").exists())
        self.assertTrue((session_dir / "attempts" / "attempt-001" / "summary.json").exists())
        self.assertEqual(detail.workspace_snapshot.root, str(repo_root.resolve()))

    def test_artifact_manifest_and_attempt_metadata_are_hydrated_from_disk(self) -> None:
        scratch = self.make_scratch_dir()
        repo_root = scratch / "repo"
        init_repo(repo_root)
        store = SessionStore(scratch / "state" / "sessions")
        summary = make_summary("run-002", repo_root)
        store.create_session(summary, [])
        store.save_state(summary.id, {"checkpoint": True})
        store.save_attempt_summary(
            summary.id,
            "attempt-001",
            {"attempt_id": "attempt-001", "status": "completed", "prompt": "Review the repo"},
        )

        hydrated = store.load_summary(summary.id)

        self.assertEqual(hydrated.attempt_count, 1)
        self.assertEqual(hydrated.latest_attempt_id, "attempt-001")
        self.assertIn("artifact_manifest", hydrated.model_dump())
        self.assertTrue(hydrated.artifact_manifest["runtime"]["checkpoint_state_exists"])
        self.assertEqual(
            hydrated.artifact_manifest["workspace_snapshot"],
            "artifacts/workspace/creation.json",
        )

    def test_atomic_json_writes_leave_no_temp_files(self) -> None:
        scratch = self.make_scratch_dir()
        repo_root = scratch / "repo"
        init_repo(repo_root)
        store = SessionStore(scratch / "state" / "sessions")
        summary = make_summary("run-003", repo_root)
        store.create_session(summary, [])

        for index in range(3):
            summary.updated_at = utc_now()
            summary.latest_human_note = f"note-{index}"
            store.save_summary(summary)

        temp_files = list(store.session_dir(summary.id).rglob("*.tmp"))
        self.assertEqual(temp_files, [])


if __name__ == "__main__":
    unittest.main()
