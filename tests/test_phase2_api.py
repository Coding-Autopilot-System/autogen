from __future__ import annotations

import unittest
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from autogen_dashboard.app import create_app
from autogen_dashboard.dependencies import get_session_service
from autogen_dashboard.schemas import (
    AutoAnswerRecordModel,
    RepoContext,
    SessionDetail,
    SessionEvent,
    StageOutputModel,
    StageTimelineEntry,
    TranscriptMessage,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FakePhase2SessionService:
    def __init__(self) -> None:
        now = utc_now()
        snapshot = RepoContext(
            name="repo",
            kind="repo",
            root="C:\\repo\\autogen",
            branch="main",
            dirty=False,
            changed_files=[],
            recent_commits=["abc123 init"],
            stack_hints=["Python"],
            scanned_at=now,
            signature="repo|main|clean",
            error=None,
        )
        self.session = SessionDetail(
            id="run-001",
            title="repo: Inspect the repo",
            provider="gemini",
            model="gemini-2.5-pro",
            original_task="Inspect the repo",
            latest_human_note=None,
            approval_decisions=[],
            retry_seed_prompt="Inspect the repo",
            workspace_kind="repo",
            workspace_snapshot=snapshot,
            workspace_stale=False,
            workspace_stale_detail=None,
            workspace_last_checked_at=snapshot.scanned_at,
            workspace_drift_fields=[],
            attempt_count=1,
            latest_attempt_id="attempt-001",
            artifact_manifest={
                "stages": [{"stage": "planning", "summary": "artifacts/stages/planning/summary.json"}],
                "runtime": {"orchestration_state": "runtime/orchestration/state.json"},
            },
            last_provider_used="gemini",
            last_model_used="gemini-2.5-pro",
            last_attempts=["gemini:gemini-2.5-pro succeeded"],
            last_fallback_count=0,
            repo_root=snapshot.root,
            repo_context=snapshot,
            status="waiting",
            pause_reason="needs_approval",
            pause_kind="needs_approval",
            pause_title="Awaiting approval",
            pause_detail="planning is ready for human approval.",
            current_stage="research",
            last_completed_stage="planning",
            stage_timeline=[
                StageTimelineEntry(
                    stage="planning",
                    status="completed",
                    pause_kind=None,
                    started_at=now,
                    completed_at=now,
                    updated_at=now,
                    attempt_count=1,
                    error=None,
                    blocked_questions=[],
                    auto_answer_count=0,
                ),
                StageTimelineEntry(
                    stage="research",
                    status="pending",
                    pause_kind="needs_approval",
                    started_at=None,
                    completed_at=None,
                    updated_at=now,
                    attempt_count=0,
                    error=None,
                    blocked_questions=[],
                    auto_answer_count=0,
                ),
            ],
            stage_outputs={
                "planning": StageOutputModel(
                    stage="planning",
                    summary="Plan ready.",
                    artifacts=["artifacts/stages/planning/summary.json"],
                    next_action="Run research.",
                    needs_approval=True,
                    needs_input=False,
                    blocked_questions=[],
                    route_metadata={
                        "active_provider": "gemini",
                        "active_model": "gemini-2.5-pro",
                        "route_tier": "deep",
                        "tools_available": True,
                    },
                )
            },
            auto_answer_records=[
                AutoAnswerRecordModel(
                    question="What phase are we in?",
                    answer="Phase 2 is executing manager-led orchestration core.",
                    sources=[".planning/STATE.md"],
                    confidence=0.88,
                    decision_type="planning_docs",
                    needs_input=False,
                    stage="research",
                    created_at=now,
                    metadata={},
                )
            ],
            blocked_questions=[],
            route_metadata={
                "active_provider": "gemini",
                "active_model": "gemini-2.5-pro",
                "route_tier": "deep",
                "fallback_used": False,
                "tools_available": True,
            },
            system_message="You are a test assistant.",
            queued_prompt="Inspect the repo",
            last_prompt="Inspect the repo",
            last_error=None,
            last_assistant_message="Manager update",
            last_stop_reason=None,
            created_at=now,
            updated_at=now,
            last_run_at=now,
            transcript_count=2,
            event_count=3,
            transcript=[
                TranscriptMessage(
                    id="msg-001",
                    role="user",
                    content="Inspect the repo",
                    source="user",
                    created_at=now,
                    metadata={},
                )
            ],
            events=[
                SessionEvent(seq=1, type="stage.started", session_id="run-001", created_at=now, payload={"stage": "planning"}),
                SessionEvent(seq=2, type="stage.completed", session_id="run-001", created_at=now, payload={"stage": "planning"}),
                SessionEvent(seq=3, type="stage.paused", session_id="run-001", created_at=now, payload={"stage": "research", "pause_kind": "needs_approval"}),
            ],
            state_saved=True,
        )

    def get_session(self, session_id: str):
        if session_id != self.session.id:
            raise KeyError(session_id)
        return self.session

    def list_sessions(self):
        from autogen_dashboard.schemas import SessionListResponse

        return SessionListResponse(items=[self.session])

    async def create_session(self, _request):
        return self.session

    async def run_step(self, session_id: str, _request=None):
        if session_id != self.session.id:
            raise KeyError(session_id)
        self.session.status = "running"
        return self.session

    async def retry(self, session_id: str):
        if session_id != self.session.id:
            raise KeyError(session_id)
        self.session.pause_kind = "retryable_error"
        self.session.pause_reason = "retryable_error"
        self.session.current_stage = "implementation"
        return self.session

    async def stream_events(self, session_id: str, since_seq: int = 0):
        if session_id != self.session.id:
            raise KeyError(session_id)
        for event in self.session.events:
            if event.seq > since_seq:
                yield event


class Phase2ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = FakePhase2SessionService()
        app = create_app()
        app.dependency_overrides[get_session_service] = lambda: self.service
        self.client = TestClient(app)

    def test_session_payloads_include_orchestration_fields(self) -> None:
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
        self.assertEqual(created_body["current_stage"], "research")
        self.assertEqual(created_body["pause_kind"], "needs_approval")
        self.assertIn("stage_timeline", created_body)
        self.assertIn("stage_outputs", created_body)
        self.assertIn("route_metadata", created_body)

        fetched = self.client.get("/api/sessions/run-001")
        self.assertEqual(fetched.status_code, 200)
        fetched_body = fetched.json()
        self.assertEqual(fetched_body["last_completed_stage"], "planning")
        self.assertEqual(fetched_body["stage_timeline"][0]["stage"], "planning")
        self.assertEqual(fetched_body["route_metadata"]["active_provider"], "gemini")

        running = self.client.post("/api/sessions/run-001/run")
        self.assertEqual(running.status_code, 200)
        self.assertEqual(running.json()["session"]["status"], "running")

        retried = self.client.post("/api/sessions/run-001/retry")
        self.assertEqual(retried.status_code, 200)
        retry_body = retried.json()["session"]
        self.assertEqual(retry_body["pause_kind"], "retryable_error")
        self.assertEqual(retry_body["current_stage"], "implementation")

    def test_sse_snapshot_contains_orchestration_summary(self) -> None:
        with self.client.stream("GET", "/api/sessions/run-001/events") as response:
            body = "".join(chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk for chunk in response.iter_text())
        self.assertIn('"current_stage": "research"', body)
        self.assertIn('"last_completed_stage": "planning"', body)
        self.assertIn('"pause_kind": "needs_approval"', body)


if __name__ == "__main__":
    unittest.main()
