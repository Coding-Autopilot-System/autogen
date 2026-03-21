from __future__ import annotations

import asyncio
import json
import re
import uuid
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator

from autogen_core import CancellationToken
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage

from autogen_dashboard.schemas import (
    ApprovalDecision,
    AutoAnswerRecordModel,
    CapabilityChangeModel,
    ProviderListResponse,
    ProviderName,
    ProviderStatusModel,
    RepoListResponse,
    SessionCreateRequest,
    SessionDetail,
    SessionEvent,
    SessionListResponse,
    SessionDecisionRequest,
    SessionMessageRequest,
    SessionRunRequest,
    SessionStatus,
    SessionSummary,
    SpecialistHandoffModel,
    SpecialistStateModel,
    StageOutputModel,
    StageTimelineEntry,
    TranscriptMessage,
    RouteAttemptModel,
    RoutePlanStepModel,
)
from autogen_dashboard.repo_context import build_repo_brief, collect_repo_context, discover_local_repos, resolve_repo_root
from autogen_dashboard.session_store import SessionStore
from autogen_starter.config import Settings
from autogen_starter.providers import ProviderConfigError, collect_provider_statuses, create_model_client
from maf_starter.gsd_autofill import resolve_gsd_questions
from maf_starter.orchestration import (
    CANONICAL_STAGE_NAMES,
    AutoAnswerRecord,
    RunOrchestrationState,
    RunStagePauseKind,
    SpecialistHandoff,
    SpecialistState,
    StageName,
    StageSummary,
    specialist_role_for_stage,
)
from maf_starter.tools import build_repo_context_snapshot

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


_GEMINI_STABLE_MODELS = (
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
)


@dataclass
class SessionRuntime:
    lock: asyncio.Lock
    condition: asyncio.Condition
    events: list[SessionEvent]
    next_seq: int
    active_task: asyncio.Task[Any] | None = None


@dataclass
class RunOutcome:
    assistant_messages: list[TranscriptMessage]
    stop_reason: str | None
    state_snapshot: dict[str, Any]
    provider_used: ProviderName
    model_used: str | None
    attempt_log: list[str]
    current_stage: StageName | None = None
    last_completed_stage: StageName | None = None
    stage_timeline: list[dict[str, Any]] = field(default_factory=list)
    stage_outputs: dict[str, dict[str, Any]] = field(default_factory=dict)
    pause_kind: RunStagePauseKind | None = None
    auto_answer_records: list[dict[str, Any]] = field(default_factory=list)
    blocked_questions: list[str] = field(default_factory=list)
    route_lane: str = "auto"
    route_plan: list[dict[str, Any]] = field(default_factory=list)
    route_attempts: list[dict[str, Any]] = field(default_factory=list)
    capability_changes: list[dict[str, Any]] = field(default_factory=list)
    specialist_states: list[dict[str, Any]] = field(default_factory=list)
    specialist_handoffs: list[dict[str, Any]] = field(default_factory=list)
    route_metadata: dict[str, Any] = field(default_factory=dict)
    transition_events: list[tuple[str, dict[str, Any]]] = field(default_factory=list)


@dataclass(frozen=True)
class RunTarget:
    provider: ProviderName
    model: str | None


@dataclass(frozen=True)
class WorkspaceRefresh:
    repo_context: Any | None
    stale: bool
    detail: str | None
    drift_fields: list[str]


class RunFailure(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        attempt_log: list[str],
        provider_used: ProviderName | None = None,
        model_used: str | None = None,
        current_stage: StageName | None = None,
        orchestration_state: dict[str, Any] | None = None,
        auto_answer_records: list[dict[str, Any]] | None = None,
        blocked_questions: list[str] | None = None,
        route_lane: str = "auto",
        route_plan: list[dict[str, Any]] | None = None,
        route_attempts: list[dict[str, Any]] | None = None,
        capability_changes: list[dict[str, Any]] | None = None,
        specialist_states: list[dict[str, Any]] | None = None,
        specialist_handoffs: list[dict[str, Any]] | None = None,
        route_metadata: dict[str, Any] | None = None,
        transition_events: list[tuple[str, dict[str, Any]]] | None = None,
    ) -> None:
        super().__init__(message)
        self.attempt_log = attempt_log
        self.provider_used = provider_used
        self.model_used = model_used
        self.current_stage = current_stage
        self.orchestration_state = orchestration_state or {}
        self.auto_answer_records = auto_answer_records or []
        self.blocked_questions = blocked_questions or []
        self.route_lane = route_lane
        self.route_plan = route_plan or []
        self.route_attempts = route_attempts or []
        self.capability_changes = capability_changes or []
        self.specialist_states = specialist_states or []
        self.specialist_handoffs = specialist_handoffs or []
        self.route_metadata = route_metadata or {}
        self.transition_events = transition_events or []


class StageExecutionError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        attempt_log: list[str],
        route_lane: str,
        route_plan: list[dict[str, Any]],
        route_attempts: list[dict[str, Any]],
        capability_changes: list[dict[str, Any]],
        route_metadata: dict[str, Any],
    ) -> None:
        super().__init__(message)
        self.attempt_log = attempt_log
        self.route_lane = route_lane
        self.route_plan = route_plan
        self.route_attempts = route_attempts
        self.capability_changes = capability_changes
        self.route_metadata = route_metadata


class SessionService:
    def __init__(self, settings: Settings, store: SessionStore) -> None:
        self.settings = settings
        self.store = store
        self._runtimes: dict[str, SessionRuntime] = {}

    def provider_statuses(self) -> ProviderListResponse:
        providers = [ProviderStatusModel(**asdict(status)) for status in collect_provider_statuses(self.settings)]
        return ProviderListResponse(active_provider=self.settings.provider, providers=providers)

    def available_repos(self) -> RepoListResponse:
        return RepoListResponse(items=discover_local_repos(self.settings.repo_scan_root))

    def list_sessions(self) -> SessionListResponse:
        return SessionListResponse(items=self.store.list_summaries())

    def get_session(self, session_id: str) -> SessionDetail:
        self._ensure_session_exists(session_id)
        return self.store.load_detail(session_id)

    async def create_session(self, request: SessionCreateRequest) -> SessionDetail:
        provider = request.provider or self.settings.provider
        self._validate_provider(provider)
        model = self._normalize_model(request.model)
        route_lane = self._normalize_route_lane(request.route_lane)
        task = (request.task or "").strip()
        if not task:
            raise ValueError("An engineering prompt is required to create a run.")
        repo_path = resolve_repo_root(request.repo_root, self.settings.repo_scan_root)
        if repo_path is None:
            raise ValueError("Select a workspace inside the allowed scan root before creating a run.")
        repo_context = collect_repo_context(repo_path)
        planned_route = self._planned_route_steps(provider, model, route_lane, stage=None)

        session_id = uuid.uuid4().hex
        title = request.title or self._default_title(provider, task, repo_context.name)
        system_message = request.system_message or self._default_system_message()
        now = utc_now()
        transcript: list[TranscriptMessage] = []
        queued_prompt = task
        orchestration = RunOrchestrationState.new(session_id)

        if queued_prompt:
            transcript.append(
                TranscriptMessage(
                    id=uuid.uuid4().hex,
                    role="user",
                    content=queued_prompt,
                    source="user",
                    created_at=now,
                    metadata={"kind": "task"},
                )
            )

        pause_reason, pause_title, pause_detail = self._pause_for_creation(queued_prompt)

        summary = SessionSummary(
            id=session_id,
            title=title,
            provider=provider,
            model=model,
            route_lane=route_lane,
            requested_provider=provider,
            requested_model=model,
            route_plan=[RoutePlanStepModel.model_validate(item) for item in planned_route],
            route_attempts=[],
            capability_changes=[],
            original_task=task,
            latest_human_note=None,
            approval_decisions=[],
            retry_seed_prompt=None,
            workspace_kind=repo_context.kind,
            workspace_snapshot=repo_context,
            workspace_stale=False,
            workspace_stale_detail=None,
            workspace_last_checked_at=repo_context.scanned_at,
            workspace_drift_fields=[],
            attempt_count=0,
            latest_attempt_id=None,
            artifact_manifest={},
            repo_root=repo_context.root,
            repo_context=repo_context,
            status="queued",
            pause_reason=pause_reason,
            pause_kind=None,
            pause_title=pause_title,
            pause_detail=pause_detail,
            current_stage=orchestration.current_stage,
            last_completed_stage=orchestration.last_completed_stage,
            stage_timeline=self._stage_timeline_models(orchestration),
            stage_outputs={},
            specialist_states=self._specialist_state_models(orchestration),
            specialist_handoffs=[],
            auto_answer_records=[],
            blocked_questions=[],
            route_metadata={
                "route_lane": route_lane,
                "route_plan": planned_route,
                "route_attempts": [],
                "capability_changes": [],
            },
            system_message=system_message,
            queued_prompt=queued_prompt,
            last_prompt=None,
            last_error=None,
            last_assistant_message=None,
            last_stop_reason=None,
            created_at=now,
            updated_at=now,
            last_run_at=None,
            transcript_count=len(transcript),
            event_count=1,
        )

        detail = self.store.create_session(summary, transcript)
        self.store.save_orchestration_state(session_id, orchestration.to_dict())
        self.store.save_auto_answer_records(session_id, [])
        self.store.save_blocked_questions(session_id, [])
        await self._emit_event(session_id, "session.created", {"session": detail.model_dump(mode="json")})
        return self.get_session(session_id)

    async def append_message(self, session_id: str, request: SessionMessageRequest) -> SessionDetail:
        return await self._record_human_input(
            session_id,
            request.content,
            source="human",
            metadata={"kind": "message"},
            pause_title="Queued human input",
            pause_detail="Human input is queued for the next run.",
        )

    async def approve(self, session_id: str, request: SessionDecisionRequest) -> SessionDetail:
        note = request.note or "APPROVE"
        return await self._record_human_input(
            session_id,
            note,
            source="approval",
            metadata={"decision": "approve"},
            decision="approve",
            pause_title="Ready for next step",
            pause_detail=self._decision_detail("approve", note),
        )

    async def reject(self, session_id: str, request: SessionDecisionRequest) -> SessionDetail:
        note = request.note or "REJECT"
        return await self._record_human_input(
            session_id,
            note,
            source="rejection",
            metadata={"decision": "reject"},
            decision="reject",
            pause_title="Ready for next step",
            pause_detail=self._decision_detail("reject", note),
        )

    async def stop(self, session_id: str) -> SessionDetail:
        return await self._mark_stopped(session_id, stop_reason="stopped by human", event_type="session.stopped")

    async def cancel(self, session_id: str) -> SessionDetail:
        return await self._mark_stopped(session_id, stop_reason="cancelled by human", event_type="session.cancelled")

    async def run_step(self, session_id: str, request: SessionRunRequest | None = None) -> SessionDetail:
        runtime = self._session_runtime(session_id)
        async with runtime.lock:
            summary = self.store.load_summary(session_id)
            if summary.status == "running":
                raise ValueError("Session is already running.")
            if summary.status == "stopped":
                raise ValueError("Session is stopped.")

            prompt, prompt_origin = self._resolve_prompt(summary, request)
            if not prompt:
                raise ValueError("No actionable prompt is available for this session.")
            record_input = bool(request and request.input)
        return await self._start_prompt_run(
            session_id,
            prompt=prompt,
            prompt_origin=prompt_origin,
            record_input=record_input,
        )

    async def retry(self, session_id: str) -> SessionDetail:
        runtime = self._session_runtime(session_id)
        async with runtime.lock:
            summary = self.store.load_summary(session_id)
            if summary.status == "running":
                raise ValueError("Session is already running.")
            if summary.status == "stopped":
                raise ValueError("Session is stopped.")
            prompt = summary.retry_seed_prompt or summary.original_task
            if not prompt:
                raise ValueError("No prior prompt is available to retry.")
        return await self._start_prompt_run(
            session_id,
            prompt=prompt,
            prompt_origin="retry",
            record_input=False,
        )

    async def stream_events(self, session_id: str, since_seq: int = 0) -> AsyncIterator[SessionEvent]:
        self._ensure_session_exists(session_id)
        runtime = self._session_runtime(session_id)
        cursor = since_seq

        for event in runtime.events:
            if event.seq > cursor:
                cursor = event.seq
                yield event

        while True:
            async with runtime.condition:
                await runtime.condition.wait_for(lambda: runtime.next_seq - 1 > cursor)
                new_events = [event for event in runtime.events if event.seq > cursor]

            for event in new_events:
                cursor = event.seq
                yield event

    async def _record_human_input(
        self,
        session_id: str,
        content: str,
        *,
        source: str,
        metadata: dict[str, Any],
        decision: str | None = None,
        pause_title: str,
        pause_detail: str,
    ) -> SessionDetail:
        runtime = self._session_runtime(session_id)
        async with runtime.lock:
            if not content or not content.strip():
                raise ValueError("Message content cannot be empty.")
            summary = self.store.load_summary(session_id)
            if summary.status == "running":
                raise ValueError("Session is running.")
            if summary.status == "stopped":
                raise ValueError("Session is stopped.")
            transcript = self.store.load_transcript(session_id)
            now = utc_now()
            transcript.append(
                TranscriptMessage(
                    id=uuid.uuid4().hex,
                    role="user",
                    content=content,
                    source=source,
                    created_at=now,
                    metadata=metadata,
                )
            )
            summary.status = "queued"
            summary.pause_reason = "not_started"
            summary.pause_kind = None
            summary.pause_title = pause_title
            summary.pause_detail = pause_detail
            summary.queued_prompt = content
            summary.latest_human_note = content
            if decision in {"approve", "reject"}:
                summary.approval_decisions.append(
                    ApprovalDecision(decision=decision, note=content, created_at=now)
                )
            refresh = self._refresh_workspace_snapshot(summary)
            summary.last_error = None
            summary.updated_at = now
            summary.transcript_count = len(transcript)
            summary.event_count = len(runtime.events) + (3 if refresh.stale else 2)
            self.store.save_transcript(session_id, transcript)
            self.store.save_summary(summary)
            await self._emit_workspace_refresh_events(
                session_id,
                refresh,
                reason="human-input",
            )
            await self._emit_event(session_id, "message.added", {"content": content, "source": source})
            return self.get_session(session_id)

    async def _start_prompt_run(
        self,
        session_id: str,
        *,
        prompt: str,
        prompt_origin: str,
        record_input: bool,
    ) -> SessionDetail:
        runtime = self._session_runtime(session_id)
        async with runtime.lock:
            summary = self.store.load_summary(session_id)
            if summary.status == "running":
                raise ValueError("Session is already running.")
            if summary.status == "stopped":
                raise ValueError("Session is stopped.")
            now = utc_now()
            summary.status = "running"
            summary.pause_reason = "not_started"
            summary.pause_title = "Running"
            summary.pause_detail = f"Executing {prompt_origin} prompt."
            summary.last_error = None
            summary.last_provider_used = None
            summary.last_model_used = None
            summary.last_attempts = []
            summary.last_fallback_count = 0
            planned_route = self._planned_route_steps(
                summary.requested_provider or summary.provider,
                summary.requested_model or summary.model,
                summary.route_lane,
                stage=summary.current_stage,
            )
            summary.route_plan = [RoutePlanStepModel.model_validate(item) for item in planned_route]
            summary.route_attempts = []
            summary.capability_changes = []
            summary.updated_at = now
            summary.last_prompt = prompt
            state = self.store.load_state(session_id)
            system_message = summary.system_message
            provider = summary.provider
            model_override = summary.model
            operator_task = summary.original_task or prompt
            refresh = self._refresh_workspace_snapshot(summary)
            repo_context = refresh.repo_context
            attempt_id, created_attempt = self._resolve_attempt_id(summary, prompt_origin)
            summary.latest_attempt_id = attempt_id
            if created_attempt:
                summary.attempt_count += 1
                self.store.save_attempt_summary(
                    session_id,
                    attempt_id,
                    {
                        "attempt_id": attempt_id,
                        "status": "running",
                        "prompt_origin": prompt_origin,
                        "prompt": prompt,
                        "started_at": now.isoformat(),
                        "completed_at": None,
                        "error": None,
                    },
                )
                await self._emit_event(
                    session_id,
                    "run.attempt.started",
                    {"attempt_id": attempt_id, "prompt_origin": prompt_origin},
                )

            if record_input:
                transcript = self.store.load_transcript(session_id)
                transcript.append(
                    TranscriptMessage(
                        id=uuid.uuid4().hex,
                        role="user",
                        content=prompt,
                        source="human",
                        created_at=now,
                        metadata={"kind": "run_input"},
                    )
                )
                self.store.save_transcript(session_id, transcript)
                summary.transcript_count = len(transcript)
                summary.retry_seed_prompt = prompt

            summary.queued_prompt = None
            summary.event_count = len(runtime.events) + (3 if refresh.stale else 2)
            self.store.save_summary(summary)
            await self._emit_workspace_refresh_events(
                session_id,
                refresh,
                reason=f"run-start:{prompt_origin}",
            )
            await self._emit_event(
                session_id,
                "run.started",
                {
                    "prompt": prompt,
                    "prompt_origin": prompt_origin,
                    "attempt_id": attempt_id,
                    "route_lane": summary.route_lane,
                    "requested_provider": summary.requested_provider,
                    "requested_model": summary.requested_model,
                    "repo_root": repo_context.root if repo_context is not None else None,
                    "checkpoint_dir": str(self.store.checkpoint_dir(session_id)),
                },
            )

            run_task = asyncio.create_task(
                self._finish_prompt_run(
                    session_id,
                    prompt_origin=prompt_origin,
                    provider=provider,
                    system_message=system_message,
                    prompt=prompt,
                    state=state,
                    model_override=model_override,
                    route_lane=summary.route_lane,
                    operator_task=operator_task,
                    repo_context=repo_context,
                    attempt_id=attempt_id,
                )
            )
            runtime.active_task = run_task
            run_task.add_done_callback(self._consume_background_task)
            return self.get_session(session_id)

    async def _finish_prompt_run(
        self,
        session_id: str,
        *,
        prompt_origin: str,
        provider: ProviderName,
        system_message: str,
        prompt: str,
        state: dict[str, Any] | None,
        model_override: str | None,
        route_lane: str,
        operator_task: str,
        repo_context,
        attempt_id: str,
    ) -> None:
        runtime = self._session_runtime(session_id)

        try:
            outcome = await self._run_team_turn(
                provider=provider,
                system_message=system_message,
                prompt=prompt,
                state=state,
                model_override=model_override,
                route_lane=route_lane,
                operator_task=operator_task,
                repo_context=repo_context,
            )
        except asyncio.CancelledError:
            async with runtime.lock:
                if runtime.active_task is asyncio.current_task():
                    runtime.active_task = None
                summary = self.store.load_summary(session_id)
                if summary.status == "stopped":
                    return
                summary.status = "error"
                summary.pause_reason = "error"
                summary.pause_kind = None
                summary.pause_title = "Cancelled"
                summary.pause_detail = "The run was cancelled."
                summary.last_error = "The run was cancelled."
                summary.last_attempts = []
                summary.last_fallback_count = 0
                summary.updated_at = utc_now()
                summary.event_count = len(runtime.events) + 1
                self.store.save_attempt_summary(
                    session_id,
                    attempt_id,
                    {
                        "attempt_id": attempt_id,
                        "status": "failed",
                        "prompt_origin": prompt_origin,
                        "prompt": prompt,
                        "completed_at": utc_now().isoformat(),
                        "error": "The run was cancelled.",
                    },
                )
                await self._emit_event(
                    session_id,
                    "run.attempt.failed",
                    {"attempt_id": attempt_id, "error": "The run was cancelled."},
                )
                self.store.save_summary(summary)
                await self._emit_event(session_id, "run.failed", {"error": "The run was cancelled."})
                return
        except Exception as exc:
            async with runtime.lock:
                if runtime.active_task is asyncio.current_task():
                    runtime.active_task = None
                summary = self.store.load_summary(session_id)
                if summary.status == "stopped":
                    return
                summarized_error = self._summarize_exception(exc)
                summary.status = "waiting" if isinstance(exc, RunFailure) and exc.current_stage else "error"
                summary.pause_reason = "retryable_error" if isinstance(exc, RunFailure) and exc.current_stage else "error"
                summary.pause_kind = "retryable_error" if isinstance(exc, RunFailure) and exc.current_stage else None
                summary.pause_title = "Retryable error" if isinstance(exc, RunFailure) and exc.current_stage else "Error"
                summary.pause_detail = summarized_error
                summary.last_error = summarized_error
                if isinstance(exc, RunFailure):
                    summary.last_provider_used = exc.provider_used
                    summary.last_model_used = exc.model_used
                    summary.last_attempts = exc.attempt_log
                    summary.last_fallback_count = max(0, len(exc.attempt_log) - 1)
                    self._apply_orchestration_summary(summary, exc.orchestration_state)
                    summary.blocked_questions = list(exc.blocked_questions)
                    summary.route_lane = exc.route_lane or summary.route_lane
                    summary.route_plan = [
                        RoutePlanStepModel.model_validate(item) for item in exc.route_plan
                    ]
                    summary.route_attempts = [
                        RouteAttemptModel.model_validate(item) for item in exc.route_attempts
                    ]
                    summary.capability_changes = [
                        CapabilityChangeModel.model_validate(item) for item in exc.capability_changes
                    ]
                    summary.route_metadata = dict(exc.route_metadata)
                    self._persist_orchestration_artifacts(session_id, exc.orchestration_state)
                    self.store.save_auto_answer_records(session_id, exc.auto_answer_records)
                    self.store.save_blocked_questions(session_id, exc.blocked_questions)
                summary.updated_at = utc_now()
                summary.event_count = len(runtime.events) + 1
                self.store.save_attempt_summary(
                    session_id,
                    attempt_id,
                    {
                        "attempt_id": attempt_id,
                        "status": "failed",
                        "prompt_origin": prompt_origin,
                        "prompt": prompt,
                        "completed_at": utc_now().isoformat(),
                        "error": summarized_error,
                        "current_stage": summary.current_stage,
                    },
                )
                if isinstance(exc, RunFailure):
                    for event_type, payload in exc.transition_events:
                        await self._emit_event(session_id, event_type, payload)
                await self._emit_event(
                    session_id,
                    "run.attempt.failed",
                    {"attempt_id": attempt_id, "error": summarized_error, "current_stage": summary.current_stage},
                )
                self.store.save_summary(summary)
                await self._emit_event(
                    session_id,
                    "run.failed",
                    {
                        "error": summarized_error,
                        "current_stage": summary.current_stage,
                        "pause_kind": summary.pause_kind,
                    },
                )
                return

        async with runtime.lock:
            if runtime.active_task is asyncio.current_task():
                runtime.active_task = None

            summary = self.store.load_summary(session_id)
            if summary.status == "stopped":
                return

            transcript = self.store.load_transcript(session_id)
            transcript.extend(outcome.assistant_messages)

            completion_status, pause_reason, pause_title, pause_detail = self._pause_for_result(outcome.stop_reason)
            if outcome.pause_kind is not None:
                completion_status = "completed" if outcome.pause_kind == "completed" else "waiting"
                pause_reason = outcome.pause_kind
                pause_title, pause_detail = self._pause_metadata_for_kind(
                    outcome.pause_kind,
                    current_stage=outcome.current_stage,
                    blocked_questions=outcome.blocked_questions,
                )
            elif len(outcome.attempt_log) > 1:
                pause_detail = (
                    f"{pause_detail} Fallback used {outcome.provider_used}"
                    f"{':' + outcome.model_used if outcome.model_used else ''}."
                )
            summary.status = completion_status
            summary.pause_reason = pause_reason
            summary.pause_kind = outcome.pause_kind
            summary.pause_title = pause_title
            summary.pause_detail = pause_detail
            summary.last_run_at = utc_now()
            summary.updated_at = summary.last_run_at
            summary.last_assistant_message = (
                outcome.assistant_messages[-1].content
                if outcome.assistant_messages
                else summary.last_assistant_message
            )
            summary.last_stop_reason = outcome.stop_reason
            summary.last_provider_used = outcome.provider_used
            summary.last_model_used = outcome.model_used
            summary.last_attempts = outcome.attempt_log
            summary.last_fallback_count = max(0, len(outcome.attempt_log) - 1)
            summary.route_lane = outcome.route_lane or summary.route_lane
            summary.route_plan = [RoutePlanStepModel.model_validate(item) for item in outcome.route_plan]
            summary.route_attempts = [RouteAttemptModel.model_validate(item) for item in outcome.route_attempts]
            summary.capability_changes = [
                CapabilityChangeModel.model_validate(item) for item in outcome.capability_changes
            ]
            summary.route_metadata = dict(outcome.route_metadata)
            summary.blocked_questions = list(outcome.blocked_questions)
            summary.auto_answer_records = [
                AutoAnswerRecordModel.model_validate(item)
                for item in outcome.auto_answer_records
            ]
            self._apply_orchestration_summary(summary, outcome.state_snapshot.get("orchestration"))
            summary.transcript_count = len(transcript)
            summary.event_count = len(runtime.events) + 1

            self.store.save_state(session_id, outcome.state_snapshot)
            self._persist_orchestration_artifacts(session_id, outcome.state_snapshot.get("orchestration"))
            self.store.save_auto_answer_records(session_id, outcome.auto_answer_records)
            self.store.save_blocked_questions(session_id, outcome.blocked_questions)
            self.store.save_transcript(session_id, transcript)
            self.store.save_attempt_summary(
                session_id,
                attempt_id,
                {
                    "attempt_id": attempt_id,
                    "status": "completed" if completion_status == "completed" else "waiting",
                    "prompt_origin": prompt_origin,
                    "prompt": prompt,
                    "completed_at": summary.last_run_at.isoformat() if summary.last_run_at else utc_now().isoformat(),
                    "stop_reason": outcome.stop_reason,
                    "provider_used": outcome.provider_used,
                    "model_used": outcome.model_used,
                        "attempt_log": outcome.attempt_log,
                        "route_lane": outcome.route_lane,
                        "route_plan": outcome.route_plan,
                        "route_attempts": outcome.route_attempts,
                        "capability_changes": outcome.capability_changes,
                        "current_stage": summary.current_stage,
                        "last_completed_stage": summary.last_completed_stage,
                        "pause_kind": summary.pause_kind,
                    },
                )
            for event_type, payload in outcome.transition_events:
                await self._emit_event(session_id, event_type, payload)
            await self._emit_event(
                session_id,
                "run.attempt.completed",
                {
                    "attempt_id": attempt_id,
                    "provider_used": outcome.provider_used,
                    "model_used": outcome.model_used,
                    "route_lane": outcome.route_lane,
                    "current_stage": summary.current_stage,
                    "pause_kind": summary.pause_kind,
                },
            )
            self.store.save_summary(summary)
            await self._emit_event(
                session_id,
                "run.completed",
                {
                    "attempt_id": attempt_id,
                    "stop_reason": outcome.stop_reason,
                    "assistant_message_count": len(outcome.assistant_messages),
                    "prompt_origin": prompt_origin,
                    "provider_used": outcome.provider_used,
                    "model_used": outcome.model_used,
                    "attempt_count": len(outcome.attempt_log),
                    "route_lane": outcome.route_lane,
                    "current_stage": summary.current_stage,
                    "last_completed_stage": summary.last_completed_stage,
                    "pause_kind": summary.pause_kind,
                },
            )

    async def _mark_stopped(self, session_id: str, *, stop_reason: str, event_type: str) -> SessionDetail:
        runtime = self._session_runtime(session_id)
        async with runtime.lock:
            summary = self.store.load_summary(session_id)
            active_task = runtime.active_task
            summary.status = "stopped"
            summary.pause_reason = "stopped"
            summary.pause_kind = "stopped"
            summary.pause_title = "Stopped"
            summary.pause_detail = stop_reason
            summary.last_stop_reason = stop_reason
            summary.updated_at = utc_now()
            summary.event_count = len(runtime.events) + 1
            self.store.save_summary(summary)
            await self._emit_event(event_type=event_type, session_id=session_id, payload={"status": "stopped", "reason": stop_reason})
        if active_task is not None and not active_task.done():
            active_task.cancel()
        return self.get_session(session_id)

    async def _emit_event(self, session_id: str, event_type: str, payload: dict[str, Any]) -> SessionEvent:
        runtime = self._session_runtime(session_id)
        async with runtime.condition:
            event = SessionEvent(
                seq=runtime.next_seq,
                type=event_type,
                session_id=session_id,
                created_at=utc_now(),
                payload=payload,
            )
            runtime.next_seq += 1
            runtime.events.append(event)
            self.store.append_event(session_id, event)
            runtime.condition.notify_all()
            return event

    def _session_runtime(self, session_id: str) -> SessionRuntime:
        self._ensure_session_exists(session_id)
        runtime = self._runtimes.get(session_id)
        if runtime is None:
            events = self.store.load_events(session_id)
            runtime = SessionRuntime(
                lock=asyncio.Lock(),
                condition=asyncio.Condition(),
                events=events,
                next_seq=(events[-1].seq + 1 if events else 1),
            )
            self._runtimes[session_id] = runtime
        return runtime

    def _ensure_session_exists(self, session_id: str) -> None:
        if not self.store.exists(session_id):
            raise KeyError(f"Session '{session_id}' not found.")

    def _validate_provider(self, provider: ProviderName) -> None:
        statuses = {status.name: status for status in collect_provider_statuses(self.settings)}
        status = statuses.get(provider)
        if status is None:
            raise ProviderConfigError(f"Unknown provider '{provider}'.")
        if not status.ready:
            raise ProviderConfigError(status.detail)

    def _default_title(self, provider: ProviderName, task: str | None, workspace_name: str | None = None) -> str:
        if task and task.strip():
            trimmed = " ".join(task.split())
            if workspace_name:
                return f"{workspace_name}: {trimmed[:52]}".strip()
            return trimmed[:64]
        return f"{provider} session"

    def _default_system_message(self) -> str:
        return (
            "You are a collaborative assistant. Produce one useful step at a time, then stop. "
            "If you need clarification, ask for it directly and briefly."
        )

    def _refresh_workspace_snapshot(self, summary: SessionSummary) -> WorkspaceRefresh:
        previous_snapshot = summary.workspace_snapshot or summary.repo_context
        if not summary.repo_root:
            summary.repo_context = None
            summary.workspace_snapshot = None
            summary.workspace_stale = False
            summary.workspace_stale_detail = None
            summary.workspace_last_checked_at = None
            summary.workspace_drift_fields = []
            return WorkspaceRefresh(
                repo_context=None,
                stale=False,
                detail=None,
                drift_fields=[],
            )

        try:
            repo_path = resolve_repo_root(summary.repo_root, self.settings.repo_scan_root)
            repo_context = collect_repo_context(repo_path) if repo_path is not None else None
        except Exception as exc:
            repo_context = previous_snapshot.model_copy(deep=True) if previous_snapshot is not None else None
            if repo_context is not None:
                repo_context.error = self._summarize_exception(exc)
                repo_context.scanned_at = utc_now()
            summary.repo_context = repo_context
            summary.workspace_snapshot = repo_context
            summary.workspace_stale = True
            summary.workspace_stale_detail = f"Workspace refresh failed: {self._summarize_exception(exc)}"
            summary.workspace_last_checked_at = utc_now()
            summary.workspace_drift_fields = ["unavailable"]
            return WorkspaceRefresh(
                repo_context=repo_context,
                stale=True,
                detail=summary.workspace_stale_detail,
                drift_fields=["unavailable"],
            )

        drift_fields = self._workspace_drift_fields(previous_snapshot, repo_context)
        stale = bool(drift_fields)
        detail = self._workspace_stale_detail(previous_snapshot, repo_context, drift_fields) if stale else None

        summary.repo_root = repo_context.root if repo_context is not None else None
        summary.repo_context = repo_context
        summary.workspace_snapshot = repo_context
        summary.workspace_kind = repo_context.kind if repo_context is not None else summary.workspace_kind
        summary.workspace_stale = stale
        summary.workspace_stale_detail = detail
        summary.workspace_last_checked_at = repo_context.scanned_at if repo_context is not None else utc_now()
        summary.workspace_drift_fields = drift_fields
        return WorkspaceRefresh(
            repo_context=repo_context,
            stale=stale,
            detail=detail,
            drift_fields=drift_fields,
        )

    async def _emit_workspace_refresh_events(
        self,
        session_id: str,
        refresh: WorkspaceRefresh,
        *,
        reason: str,
    ) -> None:
        await self._emit_event(
            session_id,
            "workspace.refreshed",
            {
                "reason": reason,
                "repo_root": refresh.repo_context.root if refresh.repo_context is not None else None,
                "stale": refresh.stale,
                "drift_fields": refresh.drift_fields,
                "detail": refresh.detail,
            },
        )
        if refresh.stale:
            await self._emit_event(
                session_id,
                "workspace.stale",
                {
                    "reason": reason,
                    "detail": refresh.detail,
                    "drift_fields": refresh.drift_fields,
                    "repo_root": refresh.repo_context.root if refresh.repo_context is not None else None,
                },
            )

    def _workspace_drift_fields(self, previous_snapshot, current_snapshot) -> list[str]:
        if previous_snapshot is None or current_snapshot is None:
            return []
        drift_fields: list[str] = []
        if previous_snapshot.root != current_snapshot.root:
            drift_fields.append("root")
        if (previous_snapshot.branch or "") != (current_snapshot.branch or ""):
            drift_fields.append("branch")
        if previous_snapshot.dirty != current_snapshot.dirty:
            drift_fields.append("dirty")
        if previous_snapshot.changed_files != current_snapshot.changed_files:
            drift_fields.append("changed_files")
        if previous_snapshot.signature != current_snapshot.signature and "changed_files" not in drift_fields:
            drift_fields.append("signature")
        return drift_fields

    def _workspace_stale_detail(self, previous_snapshot, current_snapshot, drift_fields: list[str]) -> str:
        parts: list[str] = []
        if "branch" in drift_fields:
            parts.append(
                f"branch {previous_snapshot.branch or 'unknown'} -> {current_snapshot.branch or 'unknown'}"
            )
        if "dirty" in drift_fields:
            parts.append(
                f"dirty {self._bool_label(previous_snapshot.dirty)} -> {self._bool_label(current_snapshot.dirty)}"
            )
        if "changed_files" in drift_fields or "signature" in drift_fields:
            previous_changed = len(previous_snapshot.changed_files or [])
            current_changed = len(current_snapshot.changed_files or [])
            parts.append(f"changed files {previous_changed} -> {current_changed}")
        if "root" in drift_fields:
            parts.append("workspace root changed")
        if "unavailable" in drift_fields:
            return "Workspace refresh failed. The recorded repo snapshot may be stale."
        return "Workspace changed since the last saved snapshot: " + ", ".join(parts)

    def _bool_label(self, value: bool) -> str:
        return "dirty" if value else "clean"

    def _assistant_messages(self, messages: list[Any]) -> list[TranscriptMessage]:
        assistant_messages: list[TranscriptMessage] = []
        for message in messages:
            source = getattr(message, "source", "")
            if source == "user":
                continue
            content = getattr(message, "content", "")
            assistant_messages.append(
                TranscriptMessage(
                    id=uuid.uuid4().hex,
                    role="assistant",
                    content=str(content),
                    source=str(source or "assistant"),
                    created_at=utc_now(),
                    metadata={},
                )
            )
        return assistant_messages

    def _assistant_response_messages(self, response: Any) -> list[TranscriptMessage]:
        chat_message = getattr(response, "chat_message", None)
        if chat_message is None:
            return []
        return self._assistant_messages([chat_message])

    def _normalize_assistant_state(self, state: dict[str, Any] | None) -> dict[str, Any] | None:
        if not state:
            return None
        if state.get("type") != "TeamState":
            return state

        agent_states = state.get("agent_states")
        if not isinstance(agent_states, dict):
            return None
        assistant_container = agent_states.get("assistant")
        if not isinstance(assistant_container, dict):
            return None
        assistant_state = assistant_container.get("agent_state")
        return assistant_state if isinstance(assistant_state, dict) else None

    def _resolve_prompt(self, summary: SessionSummary, request: SessionRunRequest | None) -> tuple[str | None, str]:
        if request and request.input and request.input.strip():
            return request.input.strip(), "manual"
        if summary.queued_prompt:
            return summary.queued_prompt, "queued"
        return None, "missing"

    def _pause_for_creation(self, queued_prompt: str | None) -> tuple[str, str, str]:
        if queued_prompt:
            return ("not_started", "Queued prompt", "The initial prompt is ready to run.")
        return ("needs_input", "Ready for input", "No prompt has been queued yet.")

    def _normalize_model(self, model: str | None) -> str | None:
        if model is None:
            return None
        value = model.strip()
        return value or None

    def _ready_provider_names(self) -> set[ProviderName]:
        return {
            status.name
            for status in collect_provider_statuses(self.settings)
            if status.ready and status.name != "openai"
        }

    def _gemini_fallback_models(self, selected_model: str | None) -> list[str]:
        models: list[str] = []
        normalized_selected = self._normalize_model(selected_model)
        if normalized_selected:
            models.append(normalized_selected)
        for model in _GEMINI_STABLE_MODELS:
            if model not in models:
                models.append(model)
        return models

    def _normalize_route_lane(self, value: str | None) -> str:
        normalized = (value or "auto").strip().lower()
        if normalized not in {"auto", "deep", "balanced", "fast"}:
            return "auto"
        return normalized

    def _effective_route_lane(self, route_lane: str | None, stage: StageName | None) -> str:
        selected = self._normalize_route_lane(route_lane)
        if selected != "auto":
            return selected
        if stage in {"planning", "implementation", "review"}:
            return "deep"
        return "balanced"

    def _provider_tools_available(self, provider: ProviderName) -> bool:
        return provider not in {"gemini-cli", "claude-cli", "codex-cli"}

    def _provider_execution_mode(self, provider: ProviderName) -> str:
        return "cli" if provider.endswith("-cli") else "api"

    def _route_step_payload(self, target: RunTarget, *, order: int) -> dict[str, Any]:
        return {
            "order": order,
            "provider": target.provider,
            "model": target.model,
            "label": f"{target.provider}:{target.model}" if target.model else target.provider,
            "execution_mode": self._provider_execution_mode(target.provider),
            "tools_available": self._provider_tools_available(target.provider),
        }

    def _route_attempt_payload(
        self,
        target: RunTarget,
        *,
        status: str,
        fallback_index: int,
        error: str | None = None,
    ) -> dict[str, Any]:
        return {
            "provider": target.provider,
            "model": target.model,
            "status": status,
            "tools_available": self._provider_tools_available(target.provider),
            "fallback_index": fallback_index,
            "error": error,
            "started_at": None,
            "completed_at": None,
        }

    def _capability_changes(self, attempts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        changes: list[dict[str, Any]] = []
        for previous, current in zip(attempts, attempts[1:]):
            if previous.get("tools_available") != current.get("tools_available"):
                changes.append(
                    {
                        "name": "tools_available",
                        "before": previous.get("tools_available"),
                        "after": current.get("tools_available"),
                        "reason": "Fallback changed the available tool surface.",
                    }
                )
            if previous.get("provider") != current.get("provider"):
                changes.append(
                    {
                        "name": "provider",
                        "before": previous.get("provider"),
                        "after": current.get("provider"),
                        "reason": "Fallback moved execution to a different provider.",
                    }
                )
            if previous.get("model") != current.get("model"):
                changes.append(
                    {
                        "name": "model",
                        "before": previous.get("model"),
                        "after": current.get("model"),
                        "reason": "Fallback moved execution to a different model.",
                    }
                )
            previous_mode = self._provider_execution_mode(previous.get("provider", "gemini"))  # type: ignore[arg-type]
            current_mode = self._provider_execution_mode(current.get("provider", "gemini"))  # type: ignore[arg-type]
            if previous_mode != current_mode:
                changes.append(
                    {
                        "name": "execution_mode",
                        "before": previous_mode,
                        "after": current_mode,
                        "reason": "Fallback moved execution between API and CLI.",
                    }
                )
        return changes

    def _planned_route_steps(
        self,
        provider: ProviderName,
        model_override: str | None,
        route_lane: str | None,
        *,
        stage: StageName | None,
    ) -> list[dict[str, Any]]:
        return [
            self._route_step_payload(target, order=index)
            for index, target in enumerate(
                self._build_run_targets(provider, model_override, route_lane=route_lane, stage=stage)
            )
        ]

    def _build_run_targets(
        self,
        provider: ProviderName,
        model_override: str | None,
        *,
        route_lane: str | None,
        stage: StageName | None,
    ) -> list[RunTarget]:
        ready_providers = self._ready_provider_names()
        normalized_model = self._normalize_model(model_override)
        effective_lane = self._effective_route_lane(route_lane, stage)
        targets: list[RunTarget] = []
        seen: set[tuple[ProviderName, str | None]] = set()

        def add_target(target_provider: ProviderName, target_model: str | None) -> None:
            normalized_target_model = self._normalize_model(target_model)
            key = (target_provider, normalized_target_model)
            if target_provider not in ready_providers:
                return
            if key in seen:
                return
            seen.add(key)
            targets.append(RunTarget(provider=target_provider, model=normalized_target_model))

        if provider in {"gemini", "gemini-cli"}:
            lane_default = {
                "deep": "gemini-2.5-pro",
                "balanced": "gemini-2.5-flash",
                "fast": "gemini-2.5-flash-lite",
            }.get(effective_lane, self.settings.gemini_model)
            gemini_models = self._gemini_fallback_models(normalized_model or lane_default or self.settings.gemini_model)
            if provider == "gemini":
                for model in gemini_models:
                    add_target("gemini", model)
                if "anthropic" in ready_providers and effective_lane != "fast":
                    add_target("anthropic", self.settings.anthropic_model)
                for model in gemini_models:
                    add_target("gemini-cli", model)
                add_target("gemini-cli", None)
            else:
                add_target("gemini-cli", normalized_model)
                add_target("gemini-cli", None)
                for model in gemini_models:
                    add_target("gemini", model)
                if "anthropic" in ready_providers and effective_lane != "fast":
                    add_target("anthropic", self.settings.anthropic_model)
            add_target("claude-cli", None)
            add_target("codex-cli", None)
            return targets

        add_target(provider, normalized_model)
        return targets

    def _is_fallback_worthy_error(self, exc: Exception) -> bool:
        text = self._summarize_exception(exc).lower()
        return any(
            marker in text
            for marker in (
                "429",
                "rate limit",
                "ratelimiterror",
                "resource_exhausted",
                "quota",
                "too many requests",
            )
        )

    def _summarize_exception(self, exc: Exception) -> str:
        text = str(exc).strip()
        if not text:
            text = exc.__class__.__name__
        text = text.replace("\r", " ").replace("\n", " ")
        if "Traceback:" in text:
            text = text.split("Traceback:", 1)[0].strip()
        text = re.sub(r"\s+", " ", text)
        if len(text) > 320:
            return text[:317] + "..."
        return text

    async def _run_team_turn(
        self,
        *,
        provider: ProviderName,
        system_message: str,
        prompt: str,
        state: dict[str, Any] | None,
        model_override: str | None,
        route_lane: str,
        operator_task: str,
        repo_context,
    ) -> RunOutcome:
        orchestration = self._load_orchestration_state(state)
        workspace_snapshot = repo_context.model_dump(mode="json") if repo_context is not None else None
        repo_snapshot = build_repo_context_snapshot(Path(repo_context.root)) if repo_context is not None else None
        transition_events: list[tuple[str, dict[str, Any]]] = []
        attempt_log: list[str] = []
        auto_answer_records: list[dict[str, Any]] = []
        last_provider_used: ProviderName = provider
        last_model_used = model_override
        last_route_metadata: dict[str, Any] = {
            "route_lane": route_lane,
            "route_plan": self._planned_route_steps(provider, model_override, route_lane, stage=orchestration.current_stage),
            "route_attempts": [],
            "capability_changes": [],
        }

        while orchestration.current_stage is not None:
            stage = orchestration.current_stage
            record = orchestration.start_stage(stage)
            transition_events.append(
                (
                    "stage.started",
                    {
                        "stage": stage,
                        "status": record.status,
                        "attempt_count": record.attempt_count,
                    },
                )
            )

            if stage == "validation":
                summary = self._validation_summary(orchestration)
                orchestration.complete_stage(stage, summary)
                transition_events.append(self._stage_event_payload("stage.completed", stage, summary, orchestration))
                orchestration.mark_completed()
                last_route_metadata = summary.route_metadata
                break

            stage_prompt = self._build_stage_prompt(
                stage=stage,
                prompt=operator_task,
                human_note=prompt,
                orchestration=orchestration,
                repo_context=repo_context,
            )

            try:
                stage_result = await self._run_stage_prompt(
                    provider=provider,
                    system_message=self._stage_system_message(system_message, stage),
                    prompt=stage_prompt,
                    model_override=model_override,
                    repo_context=repo_context,
                    route_lane=route_lane,
                    stage=stage,
                )
                if len(stage_result) == 4:
                    stage_text, provider_used, model_used, stage_attempt_log = stage_result
                    stage_route_metadata = self._route_metadata(
                        route_lane=route_lane,
                        provider_used=provider_used,
                        model_used=model_used,
                        route_plan=self._planned_route_steps(provider, model_override, route_lane, stage=stage),
                        route_attempts=[],
                        stage=stage,
                        requested_provider=provider,
                        requested_model=model_override,
                    )
                else:
                    stage_text, provider_used, model_used, stage_attempt_log, stage_route_metadata = stage_result
            except Exception as exc:
                summarized_error = self._summarize_exception(exc)
                stage_error = exc if isinstance(exc, StageExecutionError) else None
                if stage_error is not None:
                    attempt_log.extend(stage_error.attempt_log)
                    last_route_metadata = dict(stage_error.route_metadata)
                orchestration.fail_stage(stage, summarized_error, retryable=True)
                transition_events.append(
                    (
                        "stage.blocked",
                        {
                            "stage": stage,
                            "status": "failed",
                            "pause_kind": "retryable_error",
                            "error": summarized_error,
                            "route_lane": last_route_metadata.get("route_lane"),
                            "route_attempts": list(last_route_metadata.get("route_attempts") or []),
                        },
                    )
                )
                raise RunFailure(
                    summarized_error,
                    attempt_log=attempt_log,
                    provider_used=provider,
                    model_used=model_override,
                    current_stage=stage,
                    orchestration_state={"orchestration": orchestration.to_dict()},
                    auto_answer_records=auto_answer_records,
                    blocked_questions=list(orchestration.blocked_questions),
                    route_lane=str(last_route_metadata.get("route_lane") or "auto"),
                    route_plan=list(last_route_metadata.get("route_plan") or []),
                    route_attempts=list(last_route_metadata.get("route_attempts") or []),
                    capability_changes=list(last_route_metadata.get("capability_changes") or []),
                    specialist_states=orchestration.specialist_payloads(),
                    specialist_handoffs=orchestration.handoff_payloads(),
                    route_metadata=last_route_metadata,
                    transition_events=transition_events,
                ) from exc

            attempt_log.extend(stage_attempt_log)
            last_provider_used = provider_used
            last_model_used = model_used
            last_route_metadata = dict(stage_route_metadata)
            summary = self._parse_stage_summary(stage, stage_text, last_route_metadata)
            specialist_payload = self._extract_specialist_payload(stage, stage_text, summary)
            orchestration.update_specialist(
                specialist_role_for_stage(stage),
                stage=stage,
                status="running",
                current_task=specialist_payload.get("current_task"),
                latest_output_summary=specialist_payload.get("latest_output_summary"),
                last_handoff_target=specialist_payload.get("handoff_to"),
                last_handoff_reason=specialist_payload.get("handoff_reason"),
            )

            answers, unresolved = self._resolve_stage_questions(
                stage=stage,
                questions=summary.blocked_questions,
                workspace_snapshot=workspace_snapshot,
                repo_snapshot=repo_snapshot,
            )
            for answer in answers:
                orchestration.add_auto_answer(answer)
                auto_answer_records.append(answer.to_dict())
                transition_events.append(
                    (
                        "gsd.answer.generated",
                        {
                            "stage": stage,
                            "question": answer.question,
                            "answer": answer.answer,
                            "confidence": answer.confidence,
                            "sources": answer.sources,
                        },
                    )
                )
            summary.blocked_questions = unresolved
            summary.needs_input = bool(unresolved) or (summary.needs_input and not answers)

            if summary.needs_input or unresolved:
                orchestration.pause_stage(
                    stage,
                    "needs_input",
                    summary=summary,
                    blocked_questions=unresolved,
                )
                transition_events.append(self._stage_event_payload("stage.paused", stage, summary, orchestration))
                return self._build_orchestration_outcome(
                    orchestration=orchestration,
                    prompt=operator_task,
                    provider_used=last_provider_used,
                    model_used=last_model_used,
                    attempt_log=attempt_log,
                    route_lane=str(last_route_metadata.get("route_lane") or "auto"),
                    route_plan=list(last_route_metadata.get("route_plan") or []),
                    route_attempts=list(last_route_metadata.get("route_attempts") or []),
                    capability_changes=list(last_route_metadata.get("capability_changes") or []),
                    route_metadata=last_route_metadata,
                    auto_answer_records=auto_answer_records,
                    blocked_questions=unresolved,
                    transition_events=transition_events,
                    pause_kind="needs_input",
                )

            if summary.needs_approval:
                orchestration.complete_stage(stage, summary)
                transition_events.append(self._stage_event_payload("stage.completed", stage, summary, orchestration))
                orchestration.status = "paused"
                orchestration.pause_kind = "needs_approval"
                transition_events.append(
                    (
                        "stage.paused",
                        {
                            "stage": orchestration.current_stage,
                            "status": "paused",
                            "pause_kind": "needs_approval",
                            "last_completed_stage": stage,
                            "route_metadata": dict(summary.route_metadata),
                        },
                    )
                )
                return self._build_orchestration_outcome(
                    orchestration=orchestration,
                    prompt=operator_task,
                    provider_used=last_provider_used,
                    model_used=last_model_used,
                    attempt_log=attempt_log,
                    route_lane=str(last_route_metadata.get("route_lane") or "auto"),
                    route_plan=list(last_route_metadata.get("route_plan") or []),
                    route_attempts=list(last_route_metadata.get("route_attempts") or []),
                    capability_changes=list(last_route_metadata.get("capability_changes") or []),
                    route_metadata=last_route_metadata,
                    auto_answer_records=auto_answer_records,
                    blocked_questions=[],
                    transition_events=transition_events,
                    pause_kind="needs_approval",
                )

            orchestration.complete_stage(stage, summary)
            transition_events.append(self._stage_event_payload("stage.completed", stage, summary, orchestration))

        orchestration.mark_completed()
        return self._build_orchestration_outcome(
            orchestration=orchestration,
            prompt=operator_task,
            provider_used=last_provider_used,
            model_used=last_model_used,
            attempt_log=attempt_log,
            route_lane=str(last_route_metadata.get("route_lane") or "auto"),
            route_plan=list(last_route_metadata.get("route_plan") or []),
            route_attempts=list(last_route_metadata.get("route_attempts") or []),
            capability_changes=list(last_route_metadata.get("capability_changes") or []),
            route_metadata=last_route_metadata,
            auto_answer_records=auto_answer_records,
            blocked_questions=[],
            transition_events=transition_events,
            pause_kind="completed",
        )

    async def _run_stage_prompt(
        self,
        *,
        provider: ProviderName,
        system_message: str,
        prompt: str,
        model_override: str | None,
        repo_context,
        route_lane: str,
        stage: StageName,
    ) -> tuple[str, ProviderName, str | None, list[str], dict[str, Any]]:
        working_directory = repo_context.root if repo_context is not None else None
        effective_prompt = self._prompt_with_repo_context(prompt, repo_context)
        targets = self._build_run_targets(provider, model_override, route_lane=route_lane, stage=stage)
        attempt_log: list[str] = []
        route_attempts: list[dict[str, Any]] = []
        last_error: Exception | None = None

        for index, target in enumerate(targets):
            run_settings = replace(self.settings, provider=target.provider)
            model_client = create_model_client(
                run_settings,
                model_override=target.model,
                working_directory=working_directory,
            )
            target_label = f"{target.provider}:{target.model or 'default'}"
            try:
                assistant = AssistantAgent(
                    "assistant",
                    model_client=model_client,
                    system_message=system_message,
                )
                result = await assistant.on_messages(
                    [TextMessage(content=effective_prompt, source="user")],
                    CancellationToken(),
                )
                attempt_log.append(f"{target_label} succeeded")
                route_attempts.append(
                    self._route_attempt_payload(target, status="succeeded", fallback_index=index)
                )
                messages = self._assistant_response_messages(result)
                content = messages[-1].content if messages else ""
                route_plan = [self._route_step_payload(item, order=order) for order, item in enumerate(targets)]
                route_metadata = self._route_metadata(
                    route_lane=route_lane,
                    provider_used=target.provider,
                    model_used=target.model,
                    route_plan=route_plan,
                    route_attempts=route_attempts,
                    stage=stage,
                    requested_provider=provider,
                    requested_model=model_override,
                )
                return content, target.provider, target.model, attempt_log, route_metadata
            except Exception as exc:
                last_error = exc
                error_text = self._summarize_exception(exc)
                attempt_log.append(f"{target_label} failed: {error_text}")
                route_attempts.append(
                    self._route_attempt_payload(
                        target,
                        status="failed",
                        fallback_index=index,
                        error=error_text,
                    )
                )
                if not self._is_fallback_worthy_error(exc) or target == targets[-1]:
                    break
            finally:
                await model_client.close()

        if last_error is None:
            raise RuntimeError("No run targets were available for this stage.")
        route_plan = [self._route_step_payload(item, order=order) for order, item in enumerate(targets)]
        route_metadata = self._route_metadata(
            route_lane=route_lane,
            provider_used=targets[min(len(route_attempts), len(targets)) - 1].provider if targets else provider,
            model_used=targets[min(len(route_attempts), len(targets)) - 1].model if targets else model_override,
            route_plan=route_plan,
            route_attempts=route_attempts,
            stage=stage,
            requested_provider=provider,
            requested_model=model_override,
        )
        raise StageExecutionError(
            self._summarize_exception(last_error),
            attempt_log=attempt_log,
            route_lane=route_metadata.get("route_lane", "auto"),
            route_plan=route_plan,
            route_attempts=route_attempts,
            capability_changes=list(route_metadata.get("capability_changes") or []),
            route_metadata=route_metadata,
        ) from last_error

    def _load_orchestration_state(self, state: dict[str, Any] | None) -> RunOrchestrationState:
        if isinstance(state, dict) and isinstance(state.get("orchestration"), dict):
            return RunOrchestrationState.from_dict(state["orchestration"])
        return RunOrchestrationState.new("run")

    def _build_stage_prompt(
        self,
        *,
        stage: StageName,
        prompt: str,
        human_note: str,
        orchestration: RunOrchestrationState,
        repo_context,
    ) -> str:
        prior_outputs = orchestration.stage_outputs()
        rendered_outputs = []
        for stage_name in CANONICAL_STAGE_NAMES:
            if stage_name not in prior_outputs:
                continue
            rendered_outputs.append(
                f"- {stage_name}: {prior_outputs[stage_name].get('summary', '')}"
            )
        auto_answers = [
            f"- {record.question}: {record.answer}"
            for record in orchestration.auto_answer_records
            if record.answer
        ]
        repo_brief = build_repo_brief(repo_context)
        return "\n".join(
            part
            for part in (
                f"Current stage: {stage}",
                f"Original operator request: {prompt}",
                f"Latest human note: {human_note}" if human_note and human_note != prompt else "",
                f"Prior stage outputs:\n{chr(10).join(rendered_outputs)}" if rendered_outputs else "",
                f"Automatic GSD answers:\n{chr(10).join(auto_answers)}" if auto_answers else "",
                f"Workspace context:\n{repo_brief}" if repo_brief else "",
                "Return JSON with summary, artifacts, next_action, needs_approval, needs_input, blocked_questions.",
            )
            if part
        )

    def _stage_system_message(self, base_system_message: str, stage: StageName) -> str:
        specialty = {
            "planning": "Turn the request into an execution plan and surface risky assumptions.",
            "research": "Gather repo facts, likely files, and evidence that implementation needs.",
            "implementation": "Describe the concrete change set and validation path.",
            "review": "Check the proposal for regressions, missing tests, and weak assumptions.",
            "validation": "Summarize the final validation state.",
        }[stage]
        return (
            f"{base_system_message} You are executing the {stage} stage of a manager-led engineering workflow. "
            f"{specialty} Keep the answer concise and machine-readable. Include `current_task`, "
            "`latest_output_summary`, `handoff_to`, and `handoff_reason` in the JSON when they are known."
        )

    def _parse_stage_summary(
        self,
        stage: StageName,
        raw_text: str,
        route_metadata: dict[str, Any],
    ) -> StageSummary:
        payload = self._extract_json_object(raw_text)
        if payload is not None:
            return StageSummary(
                stage=stage,
                summary=str(payload.get("summary", "")).strip() or self._strip_route_banner(raw_text),
                artifacts=[str(item) for item in (payload.get("artifacts") or []) if str(item).strip()],
                next_action=self._nullable_text(payload.get("next_action")),
                needs_approval=bool(payload.get("needs_approval", stage == "planning")),
                needs_input=bool(payload.get("needs_input", False)),
                blocked_questions=[str(item).strip() for item in (payload.get("blocked_questions") or []) if str(item).strip()],
                route_metadata=route_metadata,
                raw_output=raw_text,
            )

        stripped = self._strip_route_banner(raw_text)
        return StageSummary(
            stage=stage,
            summary=stripped,
            artifacts=[],
            next_action=None,
            needs_approval=(stage == "planning"),
            needs_input=False,
            blocked_questions=self._extract_questions(stripped),
            route_metadata=route_metadata,
            raw_output=raw_text,
        )

    def _extract_specialist_payload(
        self,
        stage: StageName,
        raw_text: str,
        summary: StageSummary,
    ) -> dict[str, Any]:
        payload = self._extract_json_object(raw_text) or {}
        handoff_to = payload.get("handoff_to")
        normalized_handoff = None
        if isinstance(handoff_to, str):
            normalized = handoff_to.strip().lower()
            if normalized in {"manager", "planner", "researcher", "implementer", "reviewer"}:
                normalized_handoff = normalized
        return {
            "stage": stage,
            "current_task": self._nullable_text(payload.get("current_task")) or summary.next_action or f"Own the {stage} stage.",
            "latest_output_summary": self._nullable_text(payload.get("latest_output_summary")) or summary.summary,
            "handoff_to": normalized_handoff,
            "handoff_reason": self._nullable_text(payload.get("handoff_reason")) or summary.next_action,
        }

    def _resolve_stage_questions(
        self,
        *,
        stage: StageName,
        questions: list[str],
        workspace_snapshot: dict[str, Any] | None,
        repo_snapshot: dict[str, Any] | None,
    ) -> tuple[list[AutoAnswerRecord], list[str]]:
        if not questions:
            return [], []
        phase_context_path = PROJECT_ROOT / ".planning" / "phases" / "02-manager-led-orchestration-core" / "02-CONTEXT.md"
        results = resolve_gsd_questions(
            questions,
            project_root=PROJECT_ROOT,
            workspace_snapshot=workspace_snapshot,
            repo_snapshot=repo_snapshot,
            phase_context_path=phase_context_path,
        )
        answered = [result.to_record(stage=stage) for result in results if not result.needs_input and result.answer]
        unresolved = [result.question for result in results if result.needs_input or not result.answer]
        return answered, unresolved

    def _validation_summary(self, orchestration: RunOrchestrationState) -> StageSummary:
        completed = [
            record.stage
            for record in orchestration.stage_records
            if record.stage != "validation" and record.status == "completed"
        ]
        return StageSummary(
            stage="validation",
            summary=f"Validation placeholder completed after stages: {', '.join(completed) or 'none'}.",
            artifacts=["artifacts/stages/validation/summary.json"],
            next_action="Run final operator verification.",
            route_metadata={
                "route_lane": "balanced",
                "route_reason": "manager validation placeholder",
                "route_plan": [],
                "route_attempts": [],
                "capability_changes": [],
                "tools_available": False,
            },
        )

    def _route_metadata(
        self,
        *,
        route_lane: str,
        provider_used: ProviderName,
        model_used: str | None,
        route_plan: list[dict[str, Any]],
        route_attempts: list[dict[str, Any]],
        stage: StageName,
        requested_provider: ProviderName,
        requested_model: str | None,
    ) -> dict[str, Any]:
        effective_lane = self._effective_route_lane(route_lane, stage)
        return {
            "route_lane": route_lane,
            "active_lane": effective_lane,
            "active_provider": provider_used,
            "active_model": model_used,
            "primary_provider": route_plan[0]["provider"] if route_plan else provider_used,
            "primary_model": route_plan[0].get("model") if route_plan else model_used,
            "requested_provider": requested_provider,
            "requested_model": requested_model,
            "route_plan": route_plan,
            "route_attempts": route_attempts,
            "fallback_count": max(0, len(route_attempts) - 1),
            "fallback_used": len(route_attempts) > 1,
            "tools_available": self._provider_tools_available(provider_used),
            "capability_changes": self._capability_changes(route_attempts),
            "route_tier": "deep" if effective_lane == "deep" else "simple" if effective_lane == "fast" else "standard",
            "route_reason": f"{stage} stage execution through the {effective_lane} lane.",
        }

    def _build_orchestration_outcome(
        self,
        *,
        orchestration: RunOrchestrationState,
        prompt: str,
        provider_used: ProviderName,
        model_used: str | None,
        attempt_log: list[str],
        route_lane: str,
        route_plan: list[dict[str, Any]],
        route_attempts: list[dict[str, Any]],
        capability_changes: list[dict[str, Any]],
        route_metadata: dict[str, Any],
        auto_answer_records: list[dict[str, Any]],
        blocked_questions: list[str],
        transition_events: list[tuple[str, dict[str, Any]]],
        pause_kind: RunStagePauseKind,
    ) -> RunOutcome:
        current_stage = orchestration.current_stage
        summary_text = self._render_manager_summary(orchestration, prompt, pause_kind)
        return RunOutcome(
            assistant_messages=[
                TranscriptMessage(
                    id=uuid.uuid4().hex,
                    role="assistant",
                    content=summary_text,
                    source="manager",
                    created_at=utc_now(),
                    metadata={"current_stage": current_stage, "pause_kind": pause_kind},
                )
            ],
            stop_reason=f"Manager paused with {pause_kind}.",
            state_snapshot={"orchestration": orchestration.to_dict()},
            provider_used=provider_used,
            model_used=model_used,
            attempt_log=attempt_log,
            current_stage=current_stage,
            last_completed_stage=orchestration.last_completed_stage,
            stage_timeline=orchestration.stage_timeline(),
            stage_outputs=orchestration.stage_outputs(),
            pause_kind=pause_kind,
            auto_answer_records=auto_answer_records,
            blocked_questions=blocked_questions,
            route_lane=route_lane,
            route_plan=route_plan,
            route_attempts=route_attempts,
            capability_changes=capability_changes,
            specialist_states=orchestration.specialist_payloads(),
            specialist_handoffs=orchestration.handoff_payloads(),
            route_metadata=route_metadata,
            transition_events=transition_events,
        )

    def _render_manager_summary(
        self,
        orchestration: RunOrchestrationState,
        prompt: str,
        pause_kind: RunStagePauseKind,
    ) -> str:
        current_stage = orchestration.current_stage or "completed"
        last_stage = orchestration.last_completed_stage or "none"
        stage_outputs = orchestration.stage_outputs()
        current_summary = ""
        if orchestration.current_stage and orchestration.current_stage in stage_outputs:
            current_summary = stage_outputs[orchestration.current_stage].get("summary", "")
        elif orchestration.last_completed_stage and orchestration.last_completed_stage in stage_outputs:
            current_summary = stage_outputs[orchestration.last_completed_stage].get("summary", "")
        lines = [
            f"Manager update for task: {prompt}",
            f"Current stage: {current_stage}",
            f"Last completed stage: {last_stage}",
            f"Pause kind: {pause_kind}",
        ]
        if current_summary:
            lines.append(f"Summary: {current_summary}")
        if orchestration.blocked_questions:
            lines.append("Blocked questions:")
            lines.extend(f"- {question}" for question in orchestration.blocked_questions)
        return "\n".join(lines)

    def _stage_event_payload(
        self,
        event_type: str,
        stage: StageName,
        summary: StageSummary,
        orchestration: RunOrchestrationState,
    ) -> tuple[str, dict[str, Any]]:
        payload = {
            "stage": stage,
            "status": orchestration.get_record(stage).status,
            "pause_kind": orchestration.get_record(stage).pause_kind,
            "summary": summary.summary,
            "artifacts": list(summary.artifacts),
            "route_metadata": dict(summary.route_metadata),
            "route_lane": summary.route_metadata.get("route_lane"),
            "route_attempts": list(summary.route_metadata.get("route_attempts") or []),
            "specialist_states": orchestration.specialist_payloads(),
            "specialist_handoffs": orchestration.handoff_payloads(),
            "last_completed_stage": orchestration.last_completed_stage,
        }
        if orchestration.get_record(stage).blocked_questions:
            payload["blocked_questions"] = list(orchestration.get_record(stage).blocked_questions)
        return event_type, payload

    def _extract_json_object(self, text: str) -> dict[str, Any] | None:
        if not text.strip():
            return None
        candidates = []
        fenced = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
        candidates.extend(fenced)
        brace_match = re.search(r"(\{.*\})", text, flags=re.DOTALL)
        if brace_match:
            candidates.append(brace_match.group(1))
        for candidate in candidates:
            try:
                payload = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload
        return None

    def _strip_route_banner(self, text: str) -> str:
        cleaned = re.sub(r"^\[Route:[^\n]+\]\s*", "", text.strip())
        return cleaned.strip()

    def _extract_questions(self, text: str) -> list[str]:
        questions = []
        for match in re.findall(r"([A-Z0-9][^?\n]{3,}\?)", text, flags=re.IGNORECASE):
            normalized = " ".join(match.split())
            if normalized not in questions:
                questions.append(normalized)
        return questions[:5]

    def _nullable_text(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    def _pause_for_result(self, stop_reason: str | None) -> tuple[SessionStatus, str, str, str]:
        normalized = (stop_reason or "").strip().lower()
        if not normalized:
            return ("waiting", "needs_approval", "Awaiting approval", "Assistant finished a turn and saved state.")
        if "maximum number of turns" in normalized:
            return ("waiting", "needs_approval", "Awaiting approval", "Assistant finished a turn and saved state.")
        if re.search(r"\b(complete|completed|done|finished)\b", normalized):
            return ("completed", "completed", "Completed", stop_reason or "Session completed.")
        return ("waiting", "needs_approval", "Awaiting approval", stop_reason or "Assistant finished a turn and saved state.")

    def _pause_metadata_for_kind(
        self,
        pause_kind: RunStagePauseKind,
        *,
        current_stage: StageName | None,
        blocked_questions: list[str],
    ) -> tuple[str, str]:
        label_stage = current_stage or "workflow"
        if pause_kind == "needs_approval":
            return ("Awaiting approval", f"{label_stage} is ready for human approval.")
        if pause_kind == "needs_input":
            detail = f"{label_stage} needs more input."
            if blocked_questions:
                detail = f"{detail} First question: {blocked_questions[0]}"
            return ("Needs input", detail)
        if pause_kind == "retryable_error":
            return ("Retryable error", f"{label_stage} failed and can be retried without replaying prior stages.")
        if pause_kind == "blocked":
            return ("Blocked", f"{label_stage} is blocked.")
        if pause_kind == "completed":
            return ("Completed", "All manager stages completed.")
        return ("Stopped", f"{label_stage} was stopped.")

    def _apply_orchestration_summary(self, summary: SessionSummary, orchestration_payload: dict[str, Any] | None) -> None:
        if isinstance(orchestration_payload, dict) and isinstance(orchestration_payload.get("orchestration"), dict):
            orchestration_payload = orchestration_payload["orchestration"]
        orchestration = RunOrchestrationState.from_dict(orchestration_payload)
        summary.current_stage = orchestration.current_stage
        summary.last_completed_stage = orchestration.last_completed_stage
        summary.stage_timeline = self._stage_timeline_models(orchestration)
        summary.stage_outputs = {
            stage: StageOutputModel.model_validate(payload)
            for stage, payload in orchestration.stage_outputs().items()
        }
        summary.specialist_states = self._specialist_state_models(orchestration)
        summary.specialist_handoffs = self._specialist_handoff_models(orchestration)
        summary.auto_answer_records = [
            AutoAnswerRecordModel.model_validate(self._auto_answer_payload(record))
            for record in orchestration.auto_answer_records
        ]
        summary.blocked_questions = list(orchestration.blocked_questions)
        summary.pause_kind = orchestration.pause_kind
        if summary.stage_outputs:
            latest_output = summary.stage_outputs.get(orchestration.last_completed_stage or "") or next(
                reversed(list(summary.stage_outputs.values())),
                None,
            )
            if latest_output is not None:
                route_metadata = dict(latest_output.route_metadata or {})
                if route_metadata:
                    summary.route_metadata = route_metadata
                    summary.route_lane = str(route_metadata.get("route_lane") or summary.route_lane)
                    summary.route_plan = [
                        RoutePlanStepModel.model_validate(item)
                        for item in (route_metadata.get("route_plan") or [])
                    ]
                    summary.route_attempts = [
                        RouteAttemptModel.model_validate(item)
                        for item in (route_metadata.get("route_attempts") or [])
                    ]
                    summary.capability_changes = [
                        CapabilityChangeModel.model_validate(item)
                        for item in (route_metadata.get("capability_changes") or [])
                    ]

    def _stage_timeline_models(self, orchestration: RunOrchestrationState) -> list[StageTimelineEntry]:
        entries: list[StageTimelineEntry] = []
        for record in orchestration.stage_records:
            entries.append(
                StageTimelineEntry.model_validate(
                    {
                        "stage": record.stage,
                        "status": record.status,
                        "pause_kind": record.pause_kind,
                        "started_at": record.started_at,
                        "completed_at": record.completed_at,
                        "updated_at": record.updated_at,
                        "attempt_count": record.attempt_count,
                        "error": record.error,
                        "blocked_questions": list(record.blocked_questions),
                        "auto_answer_count": len(record.auto_answer_records),
                    }
                )
            )
        return entries

    def _specialist_state_models(self, orchestration: RunOrchestrationState) -> list[SpecialistStateModel]:
        return [
            SpecialistStateModel.model_validate(payload)
            for payload in orchestration.specialist_payloads()
        ]

    def _specialist_handoff_models(self, orchestration: RunOrchestrationState) -> list[SpecialistHandoffModel]:
        return [
            SpecialistHandoffModel.model_validate(payload)
            for payload in orchestration.handoff_payloads()
        ]

    def _persist_orchestration_artifacts(self, session_id: str, orchestration_payload: dict[str, Any] | None) -> None:
        if not orchestration_payload:
            return
        if isinstance(orchestration_payload, dict) and isinstance(orchestration_payload.get("orchestration"), dict):
            orchestration_payload = orchestration_payload["orchestration"]
        orchestration = RunOrchestrationState.from_dict(orchestration_payload)
        self.store.save_orchestration_state(session_id, orchestration.to_dict())
        for stage, payload in orchestration.stage_outputs().items():
            persisted = dict(payload)
            artifacts = list(persisted.get("artifacts") or [])
            default_summary_path = f"artifacts/stages/{stage}/summary.json"
            if default_summary_path not in artifacts:
                artifacts.insert(0, default_summary_path)
            persisted["artifacts"] = artifacts
            self.store.save_stage_output(session_id, stage, persisted)

    def _auto_answer_payload(self, record: AutoAnswerRecord) -> dict[str, Any]:
        payload = record.to_dict()
        payload["created_at"] = record.created_at
        return payload

    def _decision_detail(self, decision: str, note: str) -> str:
        verb = "Approved" if decision == "approve" else "Rejected"
        if note and note not in {"APPROVE", "REJECT"}:
            return f"{verb}: {note}"
        return f"{verb}."

    def _resolve_attempt_id(self, summary: SessionSummary, prompt_origin: str) -> tuple[str, bool]:
        if prompt_origin == "retry" or not summary.latest_attempt_id:
            return self.store.next_attempt_id(summary.id), True
        return summary.latest_attempt_id, False

    def _consume_background_task(self, task: asyncio.Task[Any]) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            return
        except Exception:
            return

    def _prompt_with_repo_context(self, prompt: str, repo_context) -> str:
        repo_brief = build_repo_brief(repo_context)
        if not repo_brief:
            return prompt
        return f"{repo_brief}\n\nCurrent task:\n{prompt}"
