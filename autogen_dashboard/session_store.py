from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from autogen_dashboard.schemas import RepoContext, SessionDetail, SessionEvent, SessionSummary, TranscriptMessage


class SessionStore:
    def __init__(self, sessions_root: Path) -> None:
        self.sessions_root = sessions_root
        self.sessions_root.mkdir(parents=True, exist_ok=True)

    def session_dir(self, session_id: str) -> Path:
        return self.sessions_root / session_id

    def metadata_path(self, session_id: str) -> Path:
        return self.session_dir(session_id) / "metadata.json"

    def transcript_path(self, session_id: str) -> Path:
        return self.session_dir(session_id) / "transcript.json"

    def events_path(self, session_id: str) -> Path:
        return self.session_dir(session_id) / "events.jsonl"

    def artifacts_dir(self, session_id: str) -> Path:
        return self.session_dir(session_id) / "artifacts"

    def artifact_manifest_path(self, session_id: str) -> Path:
        return self.artifacts_dir(session_id) / "manifest.json"

    def workspace_artifacts_dir(self, session_id: str) -> Path:
        return self.artifacts_dir(session_id) / "workspace"

    def stage_artifacts_dir(self, session_id: str) -> Path:
        return self.artifacts_dir(session_id) / "stages"

    def stage_artifact_dir(self, session_id: str, stage: str) -> Path:
        return self.stage_artifacts_dir(session_id) / stage

    def stage_summary_path(self, session_id: str, stage: str) -> Path:
        return self.stage_artifact_dir(session_id, stage) / "summary.json"

    def gsd_artifacts_dir(self, session_id: str) -> Path:
        return self.artifacts_dir(session_id) / "gsd"

    def auto_answers_path(self, session_id: str) -> Path:
        return self.gsd_artifacts_dir(session_id) / "auto_answers.json"

    def blocked_questions_path(self, session_id: str) -> Path:
        return self.gsd_artifacts_dir(session_id) / "blocked_questions.json"

    def workspace_creation_path(self, session_id: str) -> Path:
        return self.workspace_artifacts_dir(session_id) / "creation.json"

    def runtime_dir(self, session_id: str) -> Path:
        return self.session_dir(session_id) / "runtime"

    def checkpoint_dir(self, session_id: str) -> Path:
        return self.runtime_dir(session_id) / "checkpoint"

    def state_path(self, session_id: str) -> Path:
        return self.runtime_dir(session_id) / "state.json"

    def orchestration_dir(self, session_id: str) -> Path:
        return self.runtime_dir(session_id) / "orchestration"

    def orchestration_state_path(self, session_id: str) -> Path:
        return self.orchestration_dir(session_id) / "state.json"

    def attempts_dir(self, session_id: str) -> Path:
        return self.session_dir(session_id) / "attempts"

    def attempt_dir(self, session_id: str, attempt_id: str) -> Path:
        return self.attempts_dir(session_id) / attempt_id

    def attempt_summary_path(self, session_id: str, attempt_id: str) -> Path:
        return self.attempt_dir(session_id, attempt_id) / "summary.json"

    def exists(self, session_id: str) -> bool:
        return self.metadata_path(session_id).exists()

    def list_session_ids(self) -> list[str]:
        if not self.sessions_root.exists():
            return []
        session_ids: list[str] = []
        for child in self.sessions_root.iterdir():
            if child.is_dir() and (child / "metadata.json").exists():
                session_ids.append(child.name)
        return sorted(session_ids)

    def list_summaries(self) -> list[SessionSummary]:
        summaries: list[SessionSummary] = []
        for session_id in self.list_session_ids():
            try:
                summaries.append(self.load_summary(session_id))
            except FileNotFoundError:
                continue
        summaries.sort(key=lambda item: item.updated_at, reverse=True)
        return summaries

    def load_summary(self, session_id: str) -> SessionSummary:
        payload = json.loads(self.metadata_path(session_id).read_text(encoding="utf-8"))
        payload = self._normalize_summary_payload(payload)
        summary = SessionSummary.model_validate(payload)
        return self._hydrate_summary(summary)

    def save_summary(self, summary: SessionSummary) -> SessionSummary:
        self._ensure_session_layout(summary.id)
        hydrated = self._hydrate_summary(summary)
        self._write_json(self.metadata_path(summary.id), hydrated.model_dump(mode="json"))
        self.save_artifact_manifest(summary.id)
        return hydrated

    def load_transcript(self, session_id: str) -> list[TranscriptMessage]:
        path = self.transcript_path(session_id)
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        return [TranscriptMessage.model_validate(item) for item in data]

    def save_transcript(self, session_id: str, transcript: list[TranscriptMessage]) -> None:
        self._ensure_session_layout(session_id)
        self._write_json(self.transcript_path(session_id), [item.model_dump(mode="json") for item in transcript])
        self.save_artifact_manifest(session_id)

    def load_events(self, session_id: str) -> list[SessionEvent]:
        path = self.events_path(session_id)
        if not path.exists():
            return []
        events: list[SessionEvent] = []
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            events.append(SessionEvent.model_validate_json(line))
        return events

    def append_event(self, session_id: str, event: SessionEvent) -> None:
        self._ensure_session_layout(session_id)
        path = self.events_path(session_id)
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(event.model_dump(mode="json"), ensure_ascii=True))
            handle.write("\n")
        self.save_artifact_manifest(session_id)

    def load_state(self, session_id: str) -> dict[str, Any] | None:
        path = self.state_path(session_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_state(self, session_id: str, state: dict[str, Any]) -> None:
        self._ensure_session_layout(session_id)
        self._write_json(self.state_path(session_id), state)
        self.save_artifact_manifest(session_id)

    def load_orchestration_state(self, session_id: str) -> dict[str, Any] | None:
        path = self.orchestration_state_path(session_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_orchestration_state(self, session_id: str, state: dict[str, Any]) -> None:
        self._ensure_session_layout(session_id)
        self._write_json(self.orchestration_state_path(session_id), state)
        self.save_artifact_manifest(session_id)

    def save_stage_output(self, session_id: str, stage: str, payload: dict[str, Any]) -> None:
        self._ensure_session_layout(session_id)
        self._write_json(self.stage_summary_path(session_id, stage), payload)
        self.save_artifact_manifest(session_id)

    def save_auto_answer_records(self, session_id: str, payload: list[dict[str, Any]]) -> None:
        self._ensure_session_layout(session_id)
        self._write_json(self.auto_answers_path(session_id), payload)
        self.save_artifact_manifest(session_id)

    def save_blocked_questions(self, session_id: str, payload: list[str]) -> None:
        self._ensure_session_layout(session_id)
        self._write_json(self.blocked_questions_path(session_id), payload)
        self.save_artifact_manifest(session_id)

    def checkpoint_state_exists(self, session_id: str) -> bool:
        if self.state_path(session_id).exists() or self.orchestration_state_path(session_id).exists():
            return True
        checkpoint_dir = self.checkpoint_dir(session_id)
        return checkpoint_dir.exists() and any(checkpoint_dir.rglob("*"))

    def load_artifact_manifest(self, session_id: str) -> dict[str, Any]:
        path = self.artifact_manifest_path(session_id)
        if not path.exists():
            return self.save_artifact_manifest(session_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def save_artifact_manifest(self, session_id: str) -> dict[str, Any]:
        self._ensure_session_layout(session_id)
        manifest = self._build_artifact_manifest(session_id)
        self._write_json(self.artifact_manifest_path(session_id), manifest)
        return manifest

    def save_workspace_creation(self, session_id: str, workspace_snapshot: dict[str, Any] | None) -> None:
        self._ensure_session_layout(session_id)
        if workspace_snapshot is None:
            if self.workspace_creation_path(session_id).exists():
                self.workspace_creation_path(session_id).unlink()
            self.save_artifact_manifest(session_id)
            return
        self._write_json(self.workspace_creation_path(session_id), workspace_snapshot)
        self.save_artifact_manifest(session_id)

    def load_workspace_creation(self, session_id: str) -> dict[str, Any] | None:
        path = self.workspace_creation_path(session_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list_attempt_ids(self, session_id: str) -> list[str]:
        attempts_dir = self.attempts_dir(session_id)
        if not attempts_dir.exists():
            return []
        return sorted(child.name for child in attempts_dir.iterdir() if child.is_dir())

    def latest_attempt_id(self, session_id: str) -> str | None:
        attempts = self.list_attempt_ids(session_id)
        return attempts[-1] if attempts else None

    def next_attempt_id(self, session_id: str) -> str:
        existing = self.list_attempt_ids(session_id)
        return f"attempt-{len(existing) + 1:03d}"

    def load_attempt_summary(self, session_id: str, attempt_id: str) -> dict[str, Any] | None:
        path = self.attempt_summary_path(session_id, attempt_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def save_attempt_summary(self, session_id: str, attempt_id: str, payload: dict[str, Any]) -> None:
        self._ensure_session_layout(session_id)
        self.attempt_dir(session_id, attempt_id).mkdir(parents=True, exist_ok=True)
        self._write_json(self.attempt_summary_path(session_id, attempt_id), payload)
        self.save_artifact_manifest(session_id)

    def load_detail(self, session_id: str) -> SessionDetail:
        summary = self.load_summary(session_id)
        transcript = self.load_transcript(session_id)
        events = self.load_events(session_id)
        return SessionDetail(
            **summary.model_dump(),
            transcript=transcript,
            events=events,
            state_saved=self.checkpoint_state_exists(session_id),
        )

    def create_session(self, summary: SessionSummary, transcript: list[TranscriptMessage] | None = None) -> SessionDetail:
        self._ensure_session_layout(summary.id)
        self.save_workspace_creation(
            summary.id,
            summary.workspace_snapshot.model_dump(mode="json") if summary.workspace_snapshot is not None else None,
        )
        self.save_summary(summary)
        self.save_transcript(summary.id, transcript or [])
        if not self.events_path(summary.id).exists():
            self.events_path(summary.id).touch()
        self.save_artifact_manifest(summary.id)
        return self.load_detail(summary.id)

    def _hydrate_summary(self, summary: SessionSummary) -> SessionSummary:
        summary.transcript_count = len(self.load_transcript(summary.id))
        summary.event_count = len(self.load_events(summary.id))
        summary.attempt_count = len(self.list_attempt_ids(summary.id))
        summary.latest_attempt_id = self.latest_attempt_id(summary.id)
        summary.artifact_manifest = self.load_artifact_manifest(summary.id) if self.exists(summary.id) else self._build_artifact_manifest(summary.id)
        if summary.workspace_snapshot is None:
            workspace_snapshot = self.load_workspace_creation(summary.id)
            if workspace_snapshot is not None:
                summary.workspace_snapshot = RepoContext.model_validate(workspace_snapshot)
        return summary

    def _normalize_summary_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(payload)
        raw_status = str(normalized.get("status", "")).strip().lower()
        if raw_status == "idle":
            normalized["status"] = "queued"
        elif raw_status == "waiting_for_human":
            normalized["status"] = "waiting"
        return normalized

    def _ensure_session_layout(self, session_id: str) -> None:
        self.session_dir(session_id).mkdir(parents=True, exist_ok=True)
        self.artifacts_dir(session_id).mkdir(parents=True, exist_ok=True)
        self.workspace_artifacts_dir(session_id).mkdir(parents=True, exist_ok=True)
        self.stage_artifacts_dir(session_id).mkdir(parents=True, exist_ok=True)
        self.gsd_artifacts_dir(session_id).mkdir(parents=True, exist_ok=True)
        self.runtime_dir(session_id).mkdir(parents=True, exist_ok=True)
        self.orchestration_dir(session_id).mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir(session_id).mkdir(parents=True, exist_ok=True)
        self.attempts_dir(session_id).mkdir(parents=True, exist_ok=True)

    def _build_artifact_manifest(self, session_id: str) -> dict[str, Any]:
        attempt_entries = [
            {
                "attempt_id": attempt_id,
                "summary": self._relative_to_session(session_id, self.attempt_summary_path(session_id, attempt_id)),
            }
            for attempt_id in self.list_attempt_ids(session_id)
            if self.attempt_summary_path(session_id, attempt_id).exists()
        ]
        stage_entries = []
        for stage_dir in sorted(self.stage_artifacts_dir(session_id).iterdir()) if self.stage_artifacts_dir(session_id).exists() else []:
            if not stage_dir.is_dir():
                continue
            summary_path = stage_dir / "summary.json"
            stage_entries.append(
                {
                    "stage": stage_dir.name,
                    "summary": self._relative_if_exists(session_id, summary_path),
                }
            )
        return {
            "metadata": self._relative_to_session(session_id, self.metadata_path(session_id)),
            "transcript": self._relative_to_session(session_id, self.transcript_path(session_id)),
            "events": self._relative_to_session(session_id, self.events_path(session_id)),
            "workspace_snapshot": self._relative_if_exists(session_id, self.workspace_creation_path(session_id)),
            "stages": stage_entries,
            "gsd": {
                "directory": self._relative_to_session(session_id, self.gsd_artifacts_dir(session_id)),
                "auto_answers": self._relative_if_exists(session_id, self.auto_answers_path(session_id)),
                "blocked_questions": self._relative_if_exists(session_id, self.blocked_questions_path(session_id)),
            },
            "runtime": {
                "directory": self._relative_to_session(session_id, self.runtime_dir(session_id)),
                "state": self._relative_if_exists(session_id, self.state_path(session_id)),
                "orchestration_directory": self._relative_to_session(session_id, self.orchestration_dir(session_id)),
                "orchestration_state": self._relative_if_exists(session_id, self.orchestration_state_path(session_id)),
                "checkpoint_directory": self._relative_to_session(session_id, self.checkpoint_dir(session_id)),
                "checkpoint_state_exists": self.checkpoint_state_exists(session_id),
            },
            "attempts": attempt_entries,
        }

    def _relative_if_exists(self, session_id: str, path: Path) -> str | None:
        if not path.exists():
            return None
        return self._relative_to_session(session_id, path)

    def _relative_to_session(self, session_id: str, path: Path) -> str:
        return path.relative_to(self.session_dir(session_id)).as_posix()

    def _write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, indent=2, ensure_ascii=True)
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent, suffix=".tmp") as handle:
            handle.write(payload)
            temp_name = handle.name
        Path(temp_name).replace(path)
