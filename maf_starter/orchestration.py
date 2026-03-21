from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal


StageName = Literal["planning", "research", "implementation", "review", "validation"]
StageStatus = Literal["pending", "running", "paused", "blocked", "completed", "failed"]
RunStagePauseKind = Literal["needs_input", "needs_approval", "blocked", "retryable_error", "completed", "stopped"]
RunLifecycleStatus = Literal["idle", "running", "paused", "completed", "failed", "stopped"]
SpecialistRole = Literal["manager", "planner", "researcher", "implementer", "reviewer"]
SpecialistStatus = Literal["not_started", "running", "waiting", "handoff_ready", "completed", "blocked", "failed"]
SpecialistHandoffStatus = Literal["requested", "completed", "blocked", "rejected", "cancelled"]

CANONICAL_STAGE_NAMES: tuple[StageName, ...] = (
    "planning",
    "research",
    "implementation",
    "review",
    "validation",
)
STAGE_AGENT_MAP: dict[StageName, SpecialistRole] = {
    "planning": "planner",
    "research": "researcher",
    "implementation": "implementer",
    "review": "reviewer",
    "validation": "manager",
}
VISIBLE_SPECIALIST_ROLES: tuple[SpecialistRole, ...] = (
    "manager",
    "planner",
    "researcher",
    "implementer",
    "reviewer",
)
SPECIALIST_ROLES: tuple[SpecialistRole, ...] = VISIBLE_SPECIALIST_ROLES
SPECIALIST_STAGE_MAP: dict[SpecialistRole, StageName | None] = {
    "manager": None,
    "planner": "planning",
    "researcher": "research",
    "implementer": "implementation",
    "reviewer": "review",
}
SPECIALIST_DEFAULT_HANDOFF_TARGETS: dict[SpecialistRole, SpecialistRole | None] = {
    "manager": "planner",
    "planner": "researcher",
    "researcher": "implementer",
    "implementer": "reviewer",
    "reviewer": "manager",
}
SPECIALIST_HANDOFF_FIELDS: tuple[str, ...] = (
    "current_task",
    "latest_output_summary",
    "handoff_to",
    "handoff_reason",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_list(value: list[str] | tuple[str, ...] | None) -> list[str]:
    return [item for item in (value or []) if item]


@dataclass
class SpecialistState:
    role: SpecialistRole
    stage: StageName | None = None
    status: SpecialistStatus = "not_started"
    current_task: str | None = None
    latest_output_summary: str | None = None
    last_handoff_target: SpecialistRole | None = None
    last_handoff_reason: str | None = None
    started_at: str | None = None
    updated_at: str = field(default_factory=utc_now_iso)
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "stage": self.stage,
            "status": self.status,
            "current_task": self.current_task,
            "latest_output_summary": self.latest_output_summary,
            "last_handoff_target": self.last_handoff_target,
            "last_handoff_reason": self.last_handoff_reason,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SpecialistState":
        role = str(payload.get("role", "manager")).strip() or "manager"
        return cls(
            role=role,  # type: ignore[arg-type]
            stage=payload.get("stage"),
            status=payload.get("status", "not_started"),
            current_task=payload.get("current_task"),
            latest_output_summary=payload.get("latest_output_summary"),
            last_handoff_target=payload.get("last_handoff_target"),
            last_handoff_reason=payload.get("last_handoff_reason"),
            started_at=payload.get("started_at"),
            updated_at=str(payload.get("updated_at", utc_now_iso())),
            completed_at=payload.get("completed_at"),
        )


@dataclass
class SpecialistHandoff:
    from_role: SpecialistRole
    to_role: SpecialistRole
    reason: str
    requested_by: SpecialistRole = "manager"
    status: SpecialistHandoffStatus = "requested"
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_role": self.from_role,
            "to_role": self.to_role,
            "reason": self.reason,
            "requested_by": self.requested_by,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SpecialistHandoff":
        return cls(
            from_role=payload.get("from_role", "manager"),  # type: ignore[arg-type]
            to_role=payload.get("to_role", "planner"),  # type: ignore[arg-type]
            reason=str(payload.get("reason", "")).strip(),
            requested_by=payload.get("requested_by", "manager"),  # type: ignore[arg-type]
            status=payload.get("status", "requested"),
            created_at=str(payload.get("created_at", utc_now_iso())),
            updated_at=str(payload.get("updated_at", utc_now_iso())),
            completed_at=payload.get("completed_at"),
        )


def specialist_role_for_stage(stage: StageName) -> SpecialistRole:
    return STAGE_AGENT_MAP[stage]


def build_specialist_state(
    role: SpecialistRole,
    *,
    status: SpecialistStatus = "not_started",
    current_task: str | None = None,
    latest_output_summary: str | None = None,
    last_handoff_target: SpecialistRole | None = None,
    last_handoff_reason: str | None = None,
    started_at: str | None = None,
    updated_at: str | None = None,
    completed_at: str | None = None,
) -> SpecialistState:
    return SpecialistState(
        role=role,
        stage=SPECIALIST_STAGE_MAP.get(role),
        status=status,
        current_task=current_task,
        latest_output_summary=latest_output_summary,
        last_handoff_target=last_handoff_target,
        last_handoff_reason=last_handoff_reason,
        started_at=started_at,
        updated_at=updated_at or utc_now_iso(),
        completed_at=completed_at,
    )


def initialize_specialist_roster() -> list[SpecialistState]:
    return [build_specialist_state(role) for role in VISIBLE_SPECIALIST_ROLES]


@dataclass
class AutoAnswerRecord:
    question: str
    answer: str | None
    sources: list[str] = field(default_factory=list)
    confidence: float = 0.0
    decision_type: str = "needs_input"
    needs_input: bool = False
    stage: StageName | None = None
    created_at: str = field(default_factory=utc_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "answer": self.answer,
            "sources": list(self.sources),
            "confidence": float(self.confidence),
            "decision_type": self.decision_type,
            "needs_input": self.needs_input,
            "stage": self.stage,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AutoAnswerRecord":
        return cls(
            question=str(payload.get("question", "")),
            answer=payload.get("answer"),
            sources=_normalize_list(payload.get("sources")),
            confidence=float(payload.get("confidence", 0.0) or 0.0),
            decision_type=str(payload.get("decision_type", "needs_input")),
            needs_input=bool(payload.get("needs_input", False)),
            stage=payload.get("stage"),
            created_at=str(payload.get("created_at", utc_now_iso())),
            metadata=dict(payload.get("metadata") or {}),
        )


@dataclass
class StageSummary:
    stage: StageName
    summary: str
    artifacts: list[str] = field(default_factory=list)
    next_action: str | None = None
    needs_approval: bool = False
    needs_input: bool = False
    blocked_questions: list[str] = field(default_factory=list)
    route_metadata: dict[str, Any] = field(default_factory=dict)
    changed_files: list[str] = field(default_factory=list)
    write_operations: list[dict[str, Any]] = field(default_factory=list)
    proposed_write_operations: list[dict[str, Any]] = field(default_factory=list)
    diff_artifacts: list[str] = field(default_factory=list)
    diff_patch: str | None = None
    validation_commands: list[dict[str, Any]] = field(default_factory=list)
    validation_results: list[dict[str, Any]] = field(default_factory=list)
    pending_approval: dict[str, Any] | None = None
    raw_output: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "summary": self.summary,
            "artifacts": list(self.artifacts),
            "next_action": self.next_action,
            "needs_approval": self.needs_approval,
            "needs_input": self.needs_input,
            "blocked_questions": list(self.blocked_questions),
            "route_metadata": dict(self.route_metadata),
            "changed_files": list(self.changed_files),
            "write_operations": list(self.write_operations),
            "proposed_write_operations": list(self.proposed_write_operations),
            "diff_artifacts": list(self.diff_artifacts),
            "diff_patch": self.diff_patch,
            "validation_commands": list(self.validation_commands),
            "validation_results": list(self.validation_results),
            "pending_approval": dict(self.pending_approval) if self.pending_approval else None,
            "raw_output": self.raw_output,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "StageSummary":
        return cls(
            stage=payload.get("stage", "planning"),
            summary=str(payload.get("summary", "")),
            artifacts=_normalize_list(payload.get("artifacts")),
            next_action=payload.get("next_action"),
            needs_approval=bool(payload.get("needs_approval", False)),
            needs_input=bool(payload.get("needs_input", False)),
            blocked_questions=_normalize_list(payload.get("blocked_questions")),
            route_metadata=dict(payload.get("route_metadata") or {}),
            changed_files=_normalize_list(payload.get("changed_files")),
            write_operations=[
                dict(item) for item in (payload.get("write_operations") or []) if isinstance(item, dict)
            ],
            proposed_write_operations=[
                dict(item)
                for item in (payload.get("proposed_write_operations") or [])
                if isinstance(item, dict)
            ],
            diff_artifacts=_normalize_list(payload.get("diff_artifacts")),
            diff_patch=payload.get("diff_patch"),
            validation_commands=[
                dict(item) for item in (payload.get("validation_commands") or []) if isinstance(item, dict)
            ],
            validation_results=[
                dict(item) for item in (payload.get("validation_results") or []) if isinstance(item, dict)
            ],
            pending_approval=dict(payload.get("pending_approval") or {}) or None,
            raw_output=payload.get("raw_output"),
        )


@dataclass
class StageRecord:
    stage: StageName
    status: StageStatus = "pending"
    pause_kind: RunStagePauseKind | None = None
    started_at: str | None = None
    completed_at: str | None = None
    updated_at: str = field(default_factory=utc_now_iso)
    attempt_count: int = 0
    error: str | None = None
    summary: StageSummary | None = None
    auto_answer_records: list[AutoAnswerRecord] = field(default_factory=list)
    blocked_questions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "status": self.status,
            "pause_kind": self.pause_kind,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "updated_at": self.updated_at,
            "attempt_count": self.attempt_count,
            "error": self.error,
            "summary": self.summary.to_dict() if self.summary else None,
            "auto_answer_records": [record.to_dict() for record in self.auto_answer_records],
            "blocked_questions": list(self.blocked_questions),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "StageRecord":
        summary = payload.get("summary")
        return cls(
            stage=payload.get("stage", "planning"),
            status=payload.get("status", "pending"),
            pause_kind=payload.get("pause_kind"),
            started_at=payload.get("started_at"),
            completed_at=payload.get("completed_at"),
            updated_at=str(payload.get("updated_at", utc_now_iso())),
            attempt_count=int(payload.get("attempt_count", 0) or 0),
            error=payload.get("error"),
            summary=StageSummary.from_dict(summary) if isinstance(summary, dict) else None,
            auto_answer_records=[
                AutoAnswerRecord.from_dict(item)
                for item in (payload.get("auto_answer_records") or [])
                if isinstance(item, dict)
            ],
            blocked_questions=_normalize_list(payload.get("blocked_questions")),
        )


@dataclass
class RunOrchestrationState:
    run_id: str
    current_stage: StageName | None
    last_completed_stage: StageName | None = None
    status: RunLifecycleStatus = "idle"
    pause_kind: RunStagePauseKind | None = None
    stage_records: list[StageRecord] = field(default_factory=list)
    specialist_states: list[SpecialistState] = field(default_factory=initialize_specialist_roster)
    specialist_handoffs: list[SpecialistHandoff] = field(default_factory=list)
    auto_answer_records: list[AutoAnswerRecord] = field(default_factory=list)
    blocked_questions: list[str] = field(default_factory=list)
    retry_target_stage: StageName | None = None
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    @classmethod
    def new(cls, run_id: str) -> "RunOrchestrationState":
        return cls(
            run_id=run_id,
            current_stage=CANONICAL_STAGE_NAMES[0],
            stage_records=[StageRecord(stage=stage) for stage in CANONICAL_STAGE_NAMES],
            specialist_states=initialize_specialist_roster(),
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "RunOrchestrationState":
        if not payload:
            return cls.new("run")
        records = payload.get("stage_records") or []
        specialist_states = payload.get("specialist_states") or []
        specialist_handoffs = payload.get("specialist_handoffs") or []
        state = cls(
            run_id=str(payload.get("run_id", "run")),
            current_stage=payload.get("current_stage"),
            last_completed_stage=payload.get("last_completed_stage"),
            status=payload.get("status", "idle"),
            pause_kind=payload.get("pause_kind"),
            stage_records=[StageRecord.from_dict(item) for item in records if isinstance(item, dict)],
            specialist_states=[
                SpecialistState.from_dict(item) for item in specialist_states if isinstance(item, dict)
            ],
            specialist_handoffs=[
                SpecialistHandoff.from_dict(item) for item in specialist_handoffs if isinstance(item, dict)
            ],
            auto_answer_records=[
                AutoAnswerRecord.from_dict(item)
                for item in (payload.get("auto_answer_records") or [])
                if isinstance(item, dict)
            ],
            blocked_questions=_normalize_list(payload.get("blocked_questions")),
            retry_target_stage=payload.get("retry_target_stage"),
            created_at=str(payload.get("created_at", utc_now_iso())),
            updated_at=str(payload.get("updated_at", utc_now_iso())),
        )
        if not state.stage_records:
            state.stage_records = [StageRecord(stage=stage) for stage in CANONICAL_STAGE_NAMES]
        if not state.specialist_states:
            state.specialist_states = initialize_specialist_roster()
        return state

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "current_stage": self.current_stage,
            "last_completed_stage": self.last_completed_stage,
            "status": self.status,
            "pause_kind": self.pause_kind,
            "stage_records": [record.to_dict() for record in self.stage_records],
            "specialist_states": [state.to_dict() for state in self.specialist_states],
            "specialist_handoffs": [handoff.to_dict() for handoff in self.specialist_handoffs],
            "auto_answer_records": [record.to_dict() for record in self.auto_answer_records],
            "blocked_questions": list(self.blocked_questions),
            "retry_target_stage": self.retry_target_stage,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def stage_order(self) -> tuple[StageName, ...]:
        return CANONICAL_STAGE_NAMES

    def get_record(self, stage: StageName) -> StageRecord:
        for record in self.stage_records:
            if record.stage == stage:
                return record
        record = StageRecord(stage=stage)
        self.stage_records.append(record)
        return record

    def stage_timeline(self) -> list[dict[str, Any]]:
        return [record.to_dict() for record in self.stage_records]

    def stage_outputs(self) -> dict[str, dict[str, Any]]:
        outputs: dict[str, dict[str, Any]] = {}
        for record in self.stage_records:
            if record.summary is not None:
                outputs[record.stage] = record.summary.to_dict()
        return outputs

    def get_specialist(self, role: SpecialistRole) -> SpecialistState:
        for specialist in self.specialist_states:
            if specialist.role == role:
                return specialist
        specialist = build_specialist_state(role)
        self.specialist_states.append(specialist)
        return specialist

    def specialist_payloads(self) -> list[dict[str, Any]]:
        return [specialist.to_dict() for specialist in self.specialist_states]

    def handoff_payloads(self) -> list[dict[str, Any]]:
        return [handoff.to_dict() for handoff in self.specialist_handoffs]

    def start_specialist(self, role: SpecialistRole, *, stage: StageName | None, current_task: str | None) -> SpecialistState:
        specialist = self.get_specialist(role)
        now = utc_now_iso()
        specialist.stage = stage
        specialist.status = "running"
        specialist.current_task = current_task
        specialist.started_at = specialist.started_at or now
        specialist.updated_at = now
        specialist.completed_at = None
        return specialist

    def update_specialist(
        self,
        role: SpecialistRole,
        *,
        stage: StageName | None = None,
        status: SpecialistStatus | None = None,
        current_task: str | None = None,
        latest_output_summary: str | None = None,
        last_handoff_target: SpecialistRole | None = None,
        last_handoff_reason: str | None = None,
        completed: bool = False,
    ) -> SpecialistState:
        specialist = self.get_specialist(role)
        now = utc_now_iso()
        if stage is not None:
            specialist.stage = stage
        if status is not None:
            specialist.status = status
        if current_task is not None:
            specialist.current_task = current_task
        if latest_output_summary is not None:
            specialist.latest_output_summary = latest_output_summary
        if last_handoff_target is not None or last_handoff_reason is not None:
            specialist.last_handoff_target = last_handoff_target
            specialist.last_handoff_reason = last_handoff_reason
        specialist.updated_at = now
        if completed:
            specialist.completed_at = now
        return specialist

    def record_handoff(
        self,
        from_role: SpecialistRole,
        to_role: SpecialistRole,
        *,
        reason: str,
        requested_by: SpecialistRole = "manager",
        status: SpecialistHandoffStatus = "completed",
    ) -> SpecialistHandoff:
        now = utc_now_iso()
        handoff = SpecialistHandoff(
            from_role=from_role,
            to_role=to_role,
            reason=reason,
            requested_by=requested_by,
            status=status,
            created_at=now,
            updated_at=now,
            completed_at=now if status == "completed" else None,
        )
        self.specialist_handoffs.append(handoff)
        self.update_specialist(
            from_role,
            last_handoff_target=to_role,
            last_handoff_reason=reason,
            status="completed" if status == "completed" else "handoff_ready",
            completed=True,
        )
        self.update_specialist(
            to_role,
            status="waiting" if status == "completed" else "handoff_ready",
            current_task=f"Waiting for {to_role} stage handoff.",
            last_handoff_target=to_role,
            last_handoff_reason=reason,
        )
        return handoff

    def start_stage(self, stage: StageName) -> StageRecord:
        now = utc_now_iso()
        record = self.get_record(stage)
        record.status = "running"
        record.pause_kind = None
        record.started_at = record.started_at or now
        record.updated_at = now
        record.error = None
        record.attempt_count += 1
        self.current_stage = stage
        self.status = "running"
        self.pause_kind = None
        self.blocked_questions = []
        self.updated_at = now
        active_role = specialist_role_for_stage(stage)
        self.start_specialist(active_role, stage=stage, current_task=f"Own the {stage} stage.")
        self.start_specialist("manager", stage=None, current_task=f"Coordinate the {stage} stage.")
        return record

    def complete_stage(self, stage: StageName, summary: StageSummary) -> StageRecord:
        now = utc_now_iso()
        record = self.get_record(stage)
        record.status = "completed"
        record.pause_kind = None
        record.completed_at = now
        record.updated_at = now
        record.error = None
        record.summary = summary
        record.blocked_questions = list(summary.blocked_questions)
        self.last_completed_stage = stage
        self.blocked_questions = []
        next_stage = self._next_stage(stage)
        self.current_stage = next_stage
        self.pause_kind = None
        self.status = "running" if next_stage is not None else "completed"
        if next_stage is None:
            self.pause_kind = "completed"
        self.updated_at = now

        active_role = specialist_role_for_stage(stage)
        self.update_specialist(
            active_role,
            stage=stage,
            status="completed",
            latest_output_summary=summary.summary,
            current_task=summary.next_action,
            completed=True,
        )
        self.update_specialist(
            "manager",
            stage=None,
            status="running" if next_stage is not None else "completed",
            latest_output_summary=summary.summary,
            current_task=f"Coordinate the {next_stage} stage." if next_stage is not None else "Finalize run state.",
            completed=next_stage is None,
        )
        if next_stage is not None:
            next_role = specialist_role_for_stage(next_stage)
            reason = summary.next_action or f"Advance from {stage} to {next_stage}."
            self.record_handoff(active_role, next_role, reason=reason, requested_by="manager", status="completed")
        return record

    def pause_stage(
        self,
        stage: StageName,
        kind: RunStagePauseKind,
        *,
        summary: StageSummary | None = None,
        blocked_questions: list[str] | None = None,
    ) -> StageRecord:
        now = utc_now_iso()
        record = self.get_record(stage)
        record.status = "blocked" if kind == "blocked" else "paused"
        record.pause_kind = kind
        record.updated_at = now
        if summary is not None:
            record.summary = summary
        record.blocked_questions = _normalize_list(blocked_questions) or list(record.blocked_questions)
        self.current_stage = stage
        self.pause_kind = kind
        self.status = "paused"
        self.blocked_questions = list(record.blocked_questions)
        self.updated_at = now

        active_role = specialist_role_for_stage(stage)
        specialist_status: SpecialistStatus = "blocked" if kind in {"blocked", "retryable_error"} else "waiting"
        detail = None
        if summary is not None:
            detail = summary.summary
        elif record.blocked_questions:
            detail = record.blocked_questions[0]
        self.update_specialist(
            active_role,
            stage=stage,
            status=specialist_status,
            latest_output_summary=detail,
            current_task=record.blocked_questions[0] if record.blocked_questions else None,
        )
        self.update_specialist(
            "manager",
            stage=None,
            status="running",
            current_task=f"Await human action for the {stage} stage.",
            latest_output_summary=detail,
        )
        return record

    def fail_stage(self, stage: StageName, error: str, *, retryable: bool = True) -> StageRecord:
        now = utc_now_iso()
        record = self.get_record(stage)
        record.status = "failed"
        record.pause_kind = "retryable_error" if retryable else "blocked"
        record.error = error
        record.updated_at = now
        self.current_stage = stage
        self.pause_kind = record.pause_kind
        self.status = "failed"
        self.updated_at = now
        active_role = specialist_role_for_stage(stage)
        self.update_specialist(
            active_role,
            stage=stage,
            status="failed",
            latest_output_summary=error,
            current_task="Recover from stage failure.",
        )
        self.update_specialist(
            "manager",
            stage=None,
            status="running",
            current_task=f"Recover the {stage} stage.",
            latest_output_summary=error,
        )
        return record

    def retry_stage(self, stage: StageName | None = None) -> StageRecord:
        target = stage or self.retry_target_stage or self.current_stage or CANONICAL_STAGE_NAMES[0]
        now = utc_now_iso()
        record = self.get_record(target)
        record.status = "pending"
        record.pause_kind = None
        record.error = None
        record.updated_at = now
        self.current_stage = target
        self.pause_kind = None
        self.status = "idle"
        self.retry_target_stage = target
        self.blocked_questions = []
        self.updated_at = now
        active_role = specialist_role_for_stage(target)
        self.update_specialist(
            active_role,
            stage=target,
            status="waiting",
            current_task=f"Retry the {target} stage.",
        )
        return record

    def add_auto_answer(self, record: AutoAnswerRecord) -> None:
        self.auto_answer_records.append(record)
        if record.stage:
            stage_record = self.get_record(record.stage)
            stage_record.auto_answer_records.append(record)
            stage_record.updated_at = utc_now_iso()
        self.updated_at = utc_now_iso()

    def mark_completed(self) -> None:
        self.current_stage = None
        self.status = "completed"
        self.pause_kind = "completed"
        self.update_specialist(
            "manager",
            stage=None,
            status="completed",
            current_task="Run completed.",
            completed=True,
        )
        self.updated_at = utc_now_iso()

    def _next_stage(self, stage: StageName) -> StageName | None:
        try:
            index = CANONICAL_STAGE_NAMES.index(stage)
        except ValueError:
            return None
        if index + 1 >= len(CANONICAL_STAGE_NAMES):
            return None
        return CANONICAL_STAGE_NAMES[index + 1]


def runtime_dir_for_checkpoint(checkpoint_dir: Path) -> Path:
    checkpoint_dir = checkpoint_dir.resolve()
    if checkpoint_dir.name == "checkpoint":
        return checkpoint_dir.parent
    return checkpoint_dir / "runtime"


def session_dir_for_checkpoint(checkpoint_dir: Path) -> Path:
    checkpoint_dir = checkpoint_dir.resolve()
    runtime_dir = runtime_dir_for_checkpoint(checkpoint_dir)
    if runtime_dir.name == "runtime":
        return runtime_dir.parent
    return runtime_dir


def orchestration_dir_for_checkpoint(checkpoint_dir: Path) -> Path:
    return runtime_dir_for_checkpoint(checkpoint_dir) / "orchestration"


def orchestration_state_path_for_checkpoint(checkpoint_dir: Path) -> Path:
    return orchestration_dir_for_checkpoint(checkpoint_dir) / "state.json"


def stage_artifacts_dir_for_checkpoint(checkpoint_dir: Path) -> Path:
    return session_dir_for_checkpoint(checkpoint_dir) / "artifacts" / "stages"


def stage_artifact_dir_for_checkpoint(checkpoint_dir: Path, stage: StageName) -> Path:
    return stage_artifacts_dir_for_checkpoint(checkpoint_dir) / stage


def stage_summary_path_for_checkpoint(checkpoint_dir: Path, stage: StageName) -> Path:
    return stage_artifact_dir_for_checkpoint(checkpoint_dir, stage) / "summary.json"


def gsd_artifacts_dir_for_checkpoint(checkpoint_dir: Path) -> Path:
    return session_dir_for_checkpoint(checkpoint_dir) / "artifacts" / "gsd"


def auto_answers_path_for_checkpoint(checkpoint_dir: Path) -> Path:
    return gsd_artifacts_dir_for_checkpoint(checkpoint_dir) / "auto_answers.json"


def blocked_questions_path_for_checkpoint(checkpoint_dir: Path) -> Path:
    return gsd_artifacts_dir_for_checkpoint(checkpoint_dir) / "blocked_questions.json"
