from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


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

SessionStatus = Literal["idle", "running", "waiting_for_human", "completed", "stopped", "error"]
PauseReason = Literal["not_started", "needs_input", "needs_approval", "completed", "stopped", "error"]


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
    workspace_kind: WorkspaceKind | None = None
    workspace_snapshot: RepoContext | None = None
    attempt_count: int = 0
    last_provider_used: ProviderName | None = None
    last_model_used: str | None = None
    last_attempts: list[str] = Field(default_factory=list)
    last_fallback_count: int = 0
    repo_root: str | None = None
    repo_context: RepoContext | None = None
    status: SessionStatus
    pause_reason: PauseReason = "not_started"
    pause_title: str = "Ready"
    pause_detail: str = "No action has been taken yet."
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
