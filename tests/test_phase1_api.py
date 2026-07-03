from __future__ import annotations

import unittest
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from autogen_dashboard.app import create_app
from autogen_dashboard.dependencies import get_session_service
from autogen_dashboard.schemas import RepoContext, SessionDetail


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FakeSessionService:
    def __init__(self) -> None:
        snapshot = RepoContext(
            name="repo",
            kind="repo",
            root="C:\\repo\\autogen",
            branch="main",
            dirty=False,
            changed_files=[],
            recent_commits=["abc123 init"],
            stack_hints=["Python"],
            scanned_at=utc_now(),
            signature="repo|main|clean",
            error=None,
        )
        now = utc_now()
        self.session = SessionDetail(
            id="run-001",
            title="repo: Inspect the repo",
            provider="gemini",
            model="gemini-2.5-pro",
            original_task="Inspect the repo",
            latest_human_note=None,
            approval_decisions=[],
            retry_seed_prompt=None,
            workspace_kind="repo",
            workspace_snapshot=snapshot,
            workspace_stale=False,
            workspace_stale_detail=None,
            workspace_last_checked_at=snapshot.scanned_at,
            workspace_drift_fields=[],
            attempt_count=0,
            latest_attempt_id=None,
            artifact_manifest={"workspace_snapshot": "artifacts/workspace/creation.json", "attempts": []},
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
            queued_prompt="Inspect the repo",
            last_prompt=None,
            last_error=None,
            last_assistant_message=None,
            last_stop_reason=None,
            created_at=now,
            updated_at=now,
            last_run_at=None,
            transcript_count=1,
            event_count=1,
            transcript=[],
            events=[],
            state_saved=False,
        )
        self.create_calls = 0
        self.retry_calls = 0

    async def create_session(self, request):
        self.create_calls += 1
        return self.session

    def get_session(self, session_id: str):
        if session_id != self.session.id:
            raise KeyError(session_id)
        return self.session

    async def retry(self, session_id: str):
        if session_id != self.session.id:
            raise KeyError(session_id)
        self.retry_calls += 1
        now = utc_now()
        self.session.attempt_count = 2
        self.session.latest_attempt_id = "attempt-002"
        self.session.updated_at = now
        self.session.artifact_manifest = {
            "workspace_snapshot": "artifacts/workspace/creation.json",
            "attempts": [
                {"attempt_id": "attempt-001", "summary": "attempts/attempt-001/summary.json"},
                {"attempt_id": "attempt-002", "summary": "attempts/attempt-002/summary.json"},
            ],
        }
        return self.session


class Phase1ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = FakeSessionService()
        app = create_app()
        app.dependency_overrides[get_session_service] = lambda: self.service
        self.client = TestClient(app)

    def test_create_get_retry_flow_preserves_workspace_and_attempt_metadata(self) -> None:
        empty_task = self.client.post(
            "/api/sessions",
            json={"repo_root": "C:\\repo\\autogen", "task": "   ", "provider": "gemini"},
        )
        self.assertEqual(empty_task.status_code, 400)
        self.assertEqual(self.service.create_calls, 0)

        created = self.client.post(
            "/api/sessions",
            json={
                "repo_root": "C:\\repo\\autogen",
                "task": "Inspect the repo",
                "provider": "gemini",
                "model": "gemini-2.5-pro",
            },
        )
        self.assertEqual(created.status_code, 200)
        created_body = created.json()
        self.assertEqual(created_body["workspace_snapshot"]["root"], "C:\\repo\\autogen")
        self.assertEqual(created_body["original_task"], "Inspect the repo")
        self.assertEqual(created_body["attempt_count"], 0)
        self.assertFalse(created_body["workspace_stale"])
        self.assertEqual(created_body["workspace_drift_fields"], [])

        fetched = self.client.get("/api/sessions/run-001")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json()["workspace_kind"], "repo")

        retried = self.client.post("/api/sessions/run-001/retry")
        self.assertEqual(retried.status_code, 200)
        retried_body = retried.json()["session"]
        self.assertEqual(retried_body["latest_attempt_id"], "attempt-002")
        self.assertEqual(retried_body["attempt_count"], 2)
        self.assertEqual(retried_body["artifact_manifest"]["attempts"][-1]["attempt_id"], "attempt-002")


if __name__ == "__main__":
    unittest.main()
