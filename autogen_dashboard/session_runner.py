from __future__ import annotations

import asyncio
import re
import uuid
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from autogen_core import CancellationToken
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage

from autogen_dashboard.schemas import (
    ApprovalDecision,
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
    TranscriptMessage,
)
from autogen_dashboard.repo_context import build_repo_brief, collect_repo_context, discover_local_repos, resolve_repo_root
from autogen_dashboard.session_store import SessionStore
from autogen_starter.config import Settings
from autogen_starter.providers import ProviderConfigError, collect_provider_statuses, create_model_client


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
    ) -> None:
        super().__init__(message)
        self.attempt_log = attempt_log
        self.provider_used = provider_used
        self.model_used = model_used


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
        task = (request.task or "").strip()
        if not task:
            raise ValueError("An engineering prompt is required to create a run.")
        repo_path = resolve_repo_root(request.repo_root, self.settings.repo_scan_root)
        if repo_path is None:
            raise ValueError("Select a workspace inside the allowed scan root before creating a run.")
        repo_context = collect_repo_context(repo_path)

        session_id = uuid.uuid4().hex
        title = request.title or self._default_title(provider, task, repo_context.name)
        system_message = request.system_message or self._default_system_message()
        now = utc_now()
        transcript: list[TranscriptMessage] = []
        queued_prompt = task

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
            pause_title=pause_title,
            pause_detail=pause_detail,
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
            summary.updated_at = now
            summary.last_prompt = prompt
            state = self.store.load_state(session_id)
            system_message = summary.system_message
            provider = summary.provider
            model_override = summary.model
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
                summary.status = "error"
                summary.pause_reason = "error"
                summary.pause_title = "Error"
                summary.pause_detail = summarized_error
                summary.last_error = summarized_error
                if isinstance(exc, RunFailure):
                    summary.last_provider_used = exc.provider_used
                    summary.last_model_used = exc.model_used
                    summary.last_attempts = exc.attempt_log
                    summary.last_fallback_count = max(0, len(exc.attempt_log) - 1)
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
                    },
                )
                await self._emit_event(
                    session_id,
                    "run.attempt.failed",
                    {"attempt_id": attempt_id, "error": summarized_error},
                )
                self.store.save_summary(summary)
                await self._emit_event(session_id, "run.failed", {"error": summarized_error})
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
            if len(outcome.attempt_log) > 1:
                pause_detail = (
                    f"{pause_detail} Fallback used {outcome.provider_used}"
                    f"{':' + outcome.model_used if outcome.model_used else ''}."
                )
            summary.status = completion_status
            summary.pause_reason = pause_reason
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
            summary.transcript_count = len(transcript)
            summary.event_count = len(runtime.events) + 1

            self.store.save_state(session_id, outcome.state_snapshot)
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
                },
            )
            await self._emit_event(
                session_id,
                "run.attempt.completed",
                {
                    "attempt_id": attempt_id,
                    "provider_used": outcome.provider_used,
                    "model_used": outcome.model_used,
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
                },
            )

    async def _mark_stopped(self, session_id: str, *, stop_reason: str, event_type: str) -> SessionDetail:
        runtime = self._session_runtime(session_id)
        async with runtime.lock:
            summary = self.store.load_summary(session_id)
            active_task = runtime.active_task
            summary.status = "stopped"
            summary.pause_reason = "stopped"
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

    def _build_run_targets(self, provider: ProviderName, model_override: str | None) -> list[RunTarget]:
        ready_providers = self._ready_provider_names()
        normalized_model = self._normalize_model(model_override)
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
            gemini_models = self._gemini_fallback_models(normalized_model or self.settings.gemini_model)
            if provider == "gemini":
                for model in gemini_models:
                    add_target("gemini", model)
                    add_target("gemini-cli", model)
                add_target("gemini-cli", None)
            else:
                add_target("gemini-cli", normalized_model)
                add_target("gemini-cli", None)
                for model in gemini_models:
                    add_target("gemini-cli", model)
                    add_target("gemini", model)
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
        repo_context,
    ) -> RunOutcome:
        effective_prompt = self._prompt_with_repo_context(prompt, repo_context)
        working_directory = repo_context.root if repo_context is not None else None
        assistant_state = self._normalize_assistant_state(state)
        targets = self._build_run_targets(provider, model_override)
        attempt_log: list[str] = []
        last_error: Exception | None = None

        for target in targets:
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
                if assistant_state:
                    await assistant.load_state(assistant_state)
                result = await assistant.on_messages(
                    [TextMessage(content=effective_prompt, source="user")],
                    CancellationToken(),
                )
                attempt_log.append(f"{target_label} succeeded")
                return RunOutcome(
                    assistant_messages=self._assistant_response_messages(result),
                    stop_reason="Maximum number of turns 1 reached.",
                    state_snapshot=await assistant.save_state(),
                    provider_used=target.provider,
                    model_used=target.model,
                    attempt_log=attempt_log,
                )
            except Exception as exc:
                last_error = exc
                attempt_log.append(f"{target_label} failed: {self._summarize_exception(exc)}")
                if not self._is_fallback_worthy_error(exc) or target == targets[-1]:
                    break
            finally:
                await model_client.close()

        if last_error is None:
            raise RunFailure("No run targets were available for this session.", attempt_log=attempt_log)
        final_target = targets[-1] if targets else None
        raise RunFailure(
            " | ".join(attempt_log),
            attempt_log=attempt_log,
            provider_used=final_target.provider if final_target is not None else None,
            model_used=final_target.model if final_target is not None else None,
        ) from last_error

    def _pause_for_result(self, stop_reason: str | None) -> tuple[SessionStatus, str, str, str]:
        normalized = (stop_reason or "").strip().lower()
        if not normalized:
            return ("waiting", "needs_approval", "Awaiting approval", "Assistant finished a turn and saved state.")
        if "maximum number of turns" in normalized:
            return ("waiting", "needs_approval", "Awaiting approval", "Assistant finished a turn and saved state.")
        if re.search(r"\b(complete|completed|done|finished)\b", normalized):
            return ("completed", "completed", "Completed", stop_reason or "Session completed.")
        return ("waiting", "needs_approval", "Awaiting approval", stop_reason or "Assistant finished a turn and saved state.")

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
