from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal


StageName = Literal["planning", "research", "implementation", "review", "validation"]
StageStatus = Literal["pending", "running", "paused", "blocked", "completed", "failed"]
RunStagePauseKind = Literal["needs_input", "needs_approval", "blocked", "retryable_error", "completed", "stopped"]
RunLifecycleStatus = Literal["idle", "running", "paused", "completed", "failed", "stopped"]

CANONICAL_STAGE_NAMES: tuple[StageName, ...] = (
    "planning",
    "research",
    "implementation",
    "review",
    "validation",
)
STAGE_AGENT_MAP: dict[StageName, str] = {
    "planning": "planner",
    "research": "researcher",
    "implementation": "implementer",
    "review": "reviewer",
    "validation": "manager",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_list(value: list[str] | tuple[str, ...] | None) -> list[str]:
    return [item for item in (value or []) if item]


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
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "RunOrchestrationState":
        if not payload:
            return cls.new("run")
        records = payload.get("stage_records") or []
        state = cls(
            run_id=str(payload.get("run_id", "run")),
            current_stage=payload.get("current_stage"),
            last_completed_stage=payload.get("last_completed_stage"),
            status=payload.get("status", "idle"),
            pause_kind=payload.get("pause_kind"),
            stage_records=[StageRecord.from_dict(item) for item in records if isinstance(item, dict)],
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
        return state

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "current_stage": self.current_stage,
            "last_completed_stage": self.last_completed_stage,
            "status": self.status,
            "pause_kind": self.pause_kind,
            "stage_records": [record.to_dict() for record in self.stage_records],
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

