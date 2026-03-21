from __future__ import annotations

from pathlib import Path

from agent_framework import FileCheckpointStorage, WorkflowBuilder

from maf_starter.agent_factory import build_agent
from maf_starter.config import Settings, current_checkpoint_dir, load_settings
from maf_starter.orchestration import (
    orchestration_dir_for_checkpoint,
    orchestration_state_path_for_checkpoint,
    stage_artifacts_dir_for_checkpoint,
)


class RunScopedFileCheckpointStorage:
    def __init__(self, default_path):
        self.default_path = Path(default_path).resolve()
        self.default_path.mkdir(parents=True, exist_ok=True)

    @property
    def storage_path(self) -> Path:
        return current_checkpoint_dir(self.default_path)

    def _storage(self) -> FileCheckpointStorage:
        return FileCheckpointStorage(self.storage_path)

    async def save(self, checkpoint):
        return await self._storage().save(checkpoint)

    async def load(self, checkpoint_id):
        return await self._storage().load(checkpoint_id)

    async def list_checkpoints(self, *, workflow_name: str):
        return await self._storage().list_checkpoints(workflow_name=workflow_name)

    async def delete(self, checkpoint_id):
        return await self._storage().delete(checkpoint_id)

    async def get_latest(self, *, workflow_name: str):
        return await self._storage().get_latest(workflow_name=workflow_name)

    async def list_checkpoint_ids(self, *, workflow_name: str):
        return await self._storage().list_checkpoint_ids(workflow_name=workflow_name)


class RunScopedWorkflowArtifacts:
    def __init__(self, checkpoint_dir: Path) -> None:
        self.checkpoint_dir = checkpoint_dir.resolve()

    @property
    def orchestration_dir(self) -> Path:
        return orchestration_dir_for_checkpoint(self.checkpoint_dir)

    @property
    def orchestration_state_path(self) -> Path:
        return orchestration_state_path_for_checkpoint(self.checkpoint_dir)

    @property
    def stage_artifacts_dir(self) -> Path:
        return stage_artifacts_dir_for_checkpoint(self.checkpoint_dir)

    def ensure(self) -> "RunScopedWorkflowArtifacts":
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.orchestration_dir.mkdir(parents=True, exist_ok=True)
        self.stage_artifacts_dir.mkdir(parents=True, exist_ok=True)
        return self


def build_workflow(settings: Settings | None = None):
    current = settings or load_settings()
    artifact_layout = RunScopedWorkflowArtifacts(current.checkpoint_dir).ensure()
    workflow = (
        WorkflowBuilder(
            start_executor=build_agent(current),
            name="repo_copilot_workflow",
            description=(
                "Checkpointed workflow wrapper for the repo copilot agent with "
                "run-scoped orchestration state and stage artifacts."
            ),
            checkpoint_storage=RunScopedFileCheckpointStorage(current.checkpoint_dir),
        )
        .build()
    )
    workflow.orchestration_layout = artifact_layout
    workflow.orchestration_state_path = artifact_layout.orchestration_state_path
    workflow.stage_artifacts_dir = artifact_layout.stage_artifacts_dir
    return workflow
