from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from maf_starter.orchestration import RunStagePauseKind, StageName, StageStatus

ProviderName = Literal[
    "ollama",
    "openai",
    "gemini",
    "anthropic",
    "azure-openai",
    "codex-cli",
    "gemini-cli",
    "claude-cli",
]
WorkspaceKind = Literal["repo", "worktree", "manual"]

SessionStatus = Literal["queued", "running", "waiting", "completed", "stopped", "error"]
PauseReason = Literal[
    "not_started",
    "needs_input",
    "needs_approval",
    "blocked",
    "retryable_error",
    "completed",
    "stopped",
    "error",
]


class ProviderStatusModel(BaseModel):
    name: ProviderName
    ready: bool
    detail: str


class ProviderListResponse(BaseModel):
    active_provider: ProviderName
    providers: list[ProviderStatusModel] = Field(default_factory=list)


class RepoOption(BaseModel):
    name: str
    path: str
    root: str
    kind: WorkspaceKind = "repo"
    branch: str | None = None
    dirty: bool = False
    detail: str = ""
    changed_files: list[str] = Field(default_factory=list)
    recent_commits: list[str] = Field(default_factory=list)
    stack_hints: list[str] = Field(default_factory=list)
    scanned_at: datetime | None = None
    signature: str = ""


class RepoContext(BaseModel):
    name: str
    kind: WorkspaceKind = "repo"
    root: str
    branch: str | None = None
    dirty: bool = False
    changed_files: list[str] = Field(default_factory=list)
    recent_commits: list[str] = Field(default_factory=list)
    stack_hints: list[str] = Field(default_factory=list)
    scanned_at: datetime
    signature: str = ""
    error: str | None = None


class RepoListResponse(BaseModel):
    items: list[RepoOption] = Field(default_factory=list)


class SessionCreateRequest(BaseModel):
    title: str | None = None
    task: str | None = None
    provider: ProviderName | None = None
    model: str | None = None
    repo_root: str | None = None
    workspace_kind: WorkspaceKind | None = None
    system_message: str | None = None


class SessionMessageRequest(BaseModel):
    content: str


class SessionDecisionRequest(BaseModel):
    note: str | None = None


class SessionRunRequest(BaseModel):
    input: str | None = None


class ApprovalDecision(BaseModel):
    decision: Literal["approve", "reject"]
    note: str
    created_at: datetime


class AutoAnswerRecordModel(BaseModel):
    question: str
    answer: str | None = None
    sources: list[str] = Field(default_factory=list)
    confidence: float = 0.0
    decision_type: str = "needs_input"
    needs_input: bool = False
    stage: StageName | None = None
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class StageOutputModel(BaseModel):
    stage: StageName
    summary: str
    artifacts: list[str] = Field(default_factory=list)
    next_action: str | None = None
    needs_approval: bool = False
    needs_input: bool = False
    blocked_questions: list[str] = Field(default_factory=list)
    route_metadata: dict[str, Any] = Field(default_factory=dict)
    raw_output: str | None = None


class StageTimelineEntry(BaseModel):
    stage: StageName
    status: StageStatus
    pause_kind: RunStagePauseKind | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    updated_at: datetime
    attempt_count: int = 0
    error: str | None = None
    blocked_questions: list[str] = Field(default_factory=list)
    auto_answer_count: int = 0


class TranscriptMessage(BaseModel):
    id: str
    role: Literal["user", "assistant", "system", "event"]
    content: str
    source: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionEvent(BaseModel):
    seq: int
    type: str
    session_id: str
    created_at: datetime
    payload: dict[str, Any] = Field(default_factory=dict)


class SessionSummary(BaseModel):
    id: str
    title: str
    provider: ProviderName
    model: str | None = None
    original_task: str | None = None
    latest_human_note: str | None = None
    approval_decisions: list[ApprovalDecision] = Field(default_factory=list)
    retry_seed_prompt: str | None = None
    workspace_kind: WorkspaceKind | None = None
    workspace_snapshot: RepoContext | None = None
    workspace_stale: bool = False
    workspace_stale_detail: str | None = None
    workspace_last_checked_at: datetime | None = None
    workspace_drift_fields: list[str] = Field(default_factory=list)
    attempt_count: int = 0
    latest_attempt_id: str | None = None
    artifact_manifest: dict[str, Any] = Field(default_factory=dict)
    last_provider_used: ProviderName | None = None
    last_model_used: str | None = None
    last_attempts: list[str] = Field(default_factory=list)
    last_fallback_count: int = 0
    repo_root: str | None = None
    repo_context: RepoContext | None = None
    status: SessionStatus
    pause_reason: PauseReason = "not_started"
    pause_kind: RunStagePauseKind | None = None
    pause_title: str = "Ready"
    pause_detail: str = "No action has been taken yet."
    current_stage: StageName | None = "planning"
    last_completed_stage: StageName | None = None
    stage_timeline: list[StageTimelineEntry] = Field(default_factory=list)
    stage_outputs: dict[str, StageOutputModel] = Field(default_factory=dict)
    auto_answer_records: list[AutoAnswerRecordModel] = Field(default_factory=list)
    blocked_questions: list[str] = Field(default_factory=list)
    route_metadata: dict[str, Any] = Field(default_factory=dict)
    system_message: str
    queued_prompt: str | None = None
    last_prompt: str | None = None
    last_error: str | None = None
    last_assistant_message: str | None = None
    last_stop_reason: str | None = None
    created_at: datetime
    updated_at: datetime
    last_run_at: datetime | None = None
    transcript_count: int = 0
    event_count: int = 0


class SessionDetail(SessionSummary):
    transcript: list[TranscriptMessage] = Field(default_factory=list)
    events: list[SessionEvent] = Field(default_factory=list)
    state_saved: bool = False


class SessionListResponse(BaseModel):
    items: list[SessionSummary] = Field(default_factory=list)


class SessionCreateResponse(SessionDetail):
    pass


class SessionActionResponse(BaseModel):
    session: SessionDetail


class HealthResponse(BaseModel):
    status: str = "ok"
