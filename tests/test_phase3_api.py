from __future__ import annotations

import unittest
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from autogen_dashboard.app import create_app
from autogen_dashboard.dependencies import get_session_service
from autogen_dashboard.schemas import (
    CapabilityChangeModel,
    RepoContext,
    RouteAttemptModel,
    RoutePlanStepModel,
    SessionCreateRequest,
    SessionDetail,
    SessionEvent,
    SpecialistHandoffModel,
    SpecialistStateModel,
    StageOutputModel,
    StageTimelineEntry,
    TranscriptMessage,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class FakePhase3SessionService:
    def __init__(self) -> None:
        now = utc_now()
        snapshot = RepoContext(
            name="autogen",
            kind="repo",
            root="C:\\repo\\autogen",
            branch="main",
            dirty=False,
            changed_files=["autogen_dashboard/static/app.js"],
            recent_commits=["abc123 phase3"],
            stack_hints=["Python", "FastAPI", "Vanilla JS"],
            scanned_at=now,
            signature="autogen|main|clean",
            error=None,
        )
        self.last_request: SessionCreateRequest | None = None
        self.session = SessionDetail(
            id="run-003",
            title="repo: specialist routing visibility",
            provider="gemini",
            model="gemini-2.5-pro",
            route_lane="deep",
            requested_provider="gemini",
            requested_model="gemini-2.5-pro",
            route_plan=[
                RoutePlanStepModel(
                    provider="gemini",
                    model="gemini-2.5-pro",
                    label="gemini:gemini-2.5-pro",
                    execution_mode="api",
                    tools_available=True,
                    order=0,
                ),
                RoutePlanStepModel(
                    provider="gemini-cli",
                    model="gemini-2.5-pro",
                    label="gemini-cli:gemini-2.5-pro",
                    execution_mode="cli",
                    tools_available=False,
                    order=1,
                ),
            ],
            route_attempts=[
                RouteAttemptModel(
                    provider="gemini",
                    model="gemini-2.5-pro",
                    status="failed",
                    tools_available=True,
                    fallback_index=0,
                    error="quota exhausted",
                ),
                RouteAttemptModel(
                    provider="gemini-cli",
                    model="gemini-2.5-pro",
                    status="succeeded",
                    tools_available=False,
                    fallback_index=1,
                    error=None,
                ),
            ],
            capability_changes=[
                CapabilityChangeModel(
                    name="tools_available",
                    before=True,
                    after=False,
                    reason="Fallback moved execution from API to CLI.",
                )
            ],
            original_task="Make specialist routing visible.",
            latest_human_note=None,
            approval_decisions=[],
            retry_seed_prompt="Make specialist routing visible.",
            workspace_kind="repo",
            workspace_snapshot=snapshot,
            workspace_stale=False,
            workspace_stale_detail=None,
            workspace_last_checked_at=snapshot.scanned_at,
            workspace_drift_fields=[],
            attempt_count=1,
            latest_attempt_id="attempt-003",
            artifact_manifest={
                "stages": [{"stage": "planning", "summary": "artifacts/stages/planning/summary.json"}],
                "runtime": {"orchestration_state": "runtime/orchestration/state.json"},
            },
            last_provider_used="gemini-cli",
            last_model_used="gemini-2.5-pro",
            last_attempts=[
                "gemini:gemini-2.5-pro failed: quota exhausted",
                "gemini-cli:gemini-2.5-pro succeeded",
            ],
            last_fallback_count=1,
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
                    summary="Planner handed off to researcher.",
                    artifacts=["artifacts/stages/planning/summary.json"],
                    next_action="Run research.",
                    needs_approval=True,
                    needs_input=False,
                    blocked_questions=[],
                    pending_approval={
                        "action_kind": "file_write",
                        "risk_level": "destructive",
                        "reason": "Deleting README.md requires explicit approval.",
                        "affected_paths": ["README.md"],
                        "commands": [],
                        "external_targets": [],
                    },
                    route_metadata={
                        "route_lane": "deep",
                        "active_provider": "gemini-cli",
                        "active_model": "gemini-2.5-pro",
                        "route_plan": [
                            {
                                "provider": "gemini",
                                "model": "gemini-2.5-pro",
                                "label": "gemini:gemini-2.5-pro",
                                "execution_mode": "api",
                                "tools_available": True,
                                "order": 0,
                            }
                        ],
                        "route_attempts": [
                            {
                                "provider": "gemini-cli",
                                "model": "gemini-2.5-pro",
                                "status": "succeeded",
                                "tools_available": False,
                                "fallback_index": 1,
                                "error": None,
                            }
                        ],
                        "capability_changes": [
                            {
                                "name": "tools_available",
                                "before": True,
                                "after": False,
                                "reason": "Fallback moved execution from API to CLI.",
                            }
                        ],
                        "pending_approval": {
                            "action_kind": "file_write",
                            "risk_level": "destructive",
                            "reason": "Deleting README.md requires explicit approval.",
                            "affected_paths": ["README.md"],
                            "commands": [],
                            "external_targets": [],
                        },
                    },
                )
            },
            specialist_states=[
                SpecialistStateModel(
                    role="planner",
                    stage="planning",
                    status="completed",
                    current_task="Draft the plan.",
                    latest_output_summary="Plan ready for research.",
                    last_handoff_target="researcher",
                    last_handoff_reason="Need repo evidence.",
                    started_at=now,
                    updated_at=now,
                    completed_at=now,
                ),
                SpecialistStateModel(
                    role="researcher",
                    stage="research",
                    status="running",
                    current_task="Inspect repo evidence.",
                    latest_output_summary="Collecting file-level context.",
                    last_handoff_target=None,
                    last_handoff_reason=None,
                    started_at=now,
                    updated_at=now,
                    completed_at=None,
                ),
            ],
            specialist_handoffs=[
                SpecialistHandoffModel(
                    from_role="planner",
                    to_role="researcher",
                    reason="Need repo evidence.",
                    requested_by="manager",
                    status="requested",
                    created_at=now,
                    updated_at=now,
                    completed_at=None,
                )
            ],
            auto_answer_records=[],
            blocked_questions=[],
            pending_approval={
                "action_kind": "file_write",
                "risk_level": "destructive",
                "reason": "Deleting README.md requires explicit approval.",
                "affected_paths": ["README.md"],
                "commands": [],
                "external_targets": [],
            },
            route_metadata={
                "route_lane": "deep",
                "active_provider": "gemini-cli",
                "active_model": "gemini-2.5-pro",
                "route_tier": "deep",
                "fallback_count": 1,
                "fallback_used": True,
                "tools_available": False,
            },
            system_message="You are a test assistant.",
            queued_prompt="Make specialist routing visible.",
            last_prompt="Make specialist routing visible.",
            last_error=None,
            last_assistant_message="Manager update",
            last_stop_reason=None,
            created_at=now,
            updated_at=now,
            last_run_at=now,
            transcript_count=2,
            event_count=2,
            transcript=[
                TranscriptMessage(
                    id="msg-001",
                    role="user",
                    content="Make specialist routing visible.",
                    source="user",
                    created_at=now,
                    metadata={},
                )
            ],
            events=[
                SessionEvent(
                    seq=1,
                    type="stage.completed",
                    session_id="run-003",
                    created_at=now,
                    payload={"stage": "planning"},
                ),
                SessionEvent(
                    seq=2,
                    type="stage.paused",
                    session_id="run-003",
                    created_at=now,
                    payload={"stage": "research", "pause_kind": "needs_approval"},
                ),
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

    async def create_session(self, request: SessionCreateRequest):
        self.last_request = request
        if request.route_lane is not None:
            self.session.route_lane = request.route_lane
        if request.provider is not None:
            self.session.provider = request.provider
            self.session.requested_provider = request.provider
        if request.model is not None:
            self.session.model = request.model
            self.session.requested_model = request.model
        return self.session

    async def stream_events(self, session_id: str, since_seq: int = 0):
        if session_id != self.session.id:
            raise KeyError(session_id)
        for event in self.session.events:
            if event.seq > since_seq:
                yield event


class Phase3ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = FakePhase3SessionService()
        app = create_app()
        app.dependency_overrides[get_session_service] = lambda: self.service
        self.client = TestClient(app)

    def test_create_and_fetch_include_specialist_and_routing_contract(self) -> None:
        created = self.client.post(
            "/api/sessions",
            json={
                "repo_root": "C:\\repo\\autogen",
                "task": "Make specialist routing visible.",
                "provider": "gemini",
                "model": "gemini-2.5-pro",
                "route_lane": "balanced",
            },
        )
        self.assertEqual(created.status_code, 200)
        created_body = created.json()
        self.assertEqual(self.service.last_request.route_lane, "balanced")
        self.assertEqual(created_body["route_lane"], "balanced")
        self.assertEqual(created_body["route_plan"][0]["provider"], "gemini")
        self.assertEqual(created_body["route_attempts"][1]["provider"], "gemini-cli")
        self.assertEqual(created_body["capability_changes"][0]["name"], "tools_available")
        self.assertEqual(created_body["specialist_states"][0]["role"], "planner")
        self.assertEqual(created_body["specialist_handoffs"][0]["to_role"], "researcher")
        self.assertEqual(created_body["pending_approval"]["affected_paths"], ["README.md"])

        fetched = self.client.get("/api/sessions/run-003")
        self.assertEqual(fetched.status_code, 200)
        fetched_body = fetched.json()
        self.assertEqual(fetched_body["requested_provider"], "gemini")
        self.assertEqual(fetched_body["requested_model"], "gemini-2.5-pro")
        self.assertEqual(fetched_body["route_metadata"]["active_provider"], "gemini-cli")
        self.assertEqual(fetched_body["specialist_states"][1]["status"], "running")
        self.assertEqual(fetched_body["stage_outputs"]["planning"]["pending_approval"]["risk_level"], "destructive")

    def test_sse_snapshot_contains_specialist_and_route_visibility(self) -> None:
        with self.client.stream("GET", "/api/sessions/run-003/events") as response:
            body = "".join(
                chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk
                for chunk in response.iter_text()
            )
        self.assertIn('"route_lane": "deep"', body)
        self.assertIn('"route_plan"', body)
        self.assertIn('"specialist_states"', body)
        self.assertIn('"specialist_handoffs"', body)
        self.assertIn('"affected_paths": ["README.md"]', body)


if __name__ == "__main__":
    unittest.main()
