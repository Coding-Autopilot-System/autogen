from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath


_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")
_BLOCKED_PARTS = {".git", ".env", "secrets", "credentials", "state"}


@dataclass(frozen=True)
class MutationContract:
    goal_id: str
    work_item_id: str
    repo_root: Path
    worktree_path: Path
    base_ref: str
    deadline: datetime
    path_allowlist: tuple[str, ...]
    idempotency_key: str
    implementation_owner: str

    def validate(self, *, now: datetime | None = None) -> None:
        current = now or datetime.now(UTC)
        if not _SAFE_ID.fullmatch(self.goal_id) or not _SAFE_ID.fullmatch(self.work_item_id):
            raise ValueError("Goal and work-item IDs must be path-safe")
        if not self.idempotency_key.strip() or not self.implementation_owner.strip():
            raise ValueError("Idempotency key and implementation owner are required")
        if not self.path_allowlist:
            raise ValueError("At least one allowed path pattern is required")
        if self.deadline.tzinfo is None or self.deadline <= current:
            raise TimeoutError("Mutation work item deadline has expired")
        repo = self.repo_root.resolve()
        worktree = self.worktree_path.resolve()
        if repo == worktree or repo in worktree.parents:
            raise ValueError("Mutation worktree must be distinct from and outside the source repository")


@dataclass(frozen=True)
class SandboxManifest:
    goal_id: str
    work_item_id: str
    worktree_path: str
    branch: str
    base_sha: str
    idempotency_key: str
    implementation_owner: str


@dataclass(frozen=True)
class ArtifactManifest:
    goal_id: str
    work_item_id: str
    idempotency_key: str
    changed_files: tuple[str, ...]
    worktree_path: str


class GitWorktreeSandbox:
    def __init__(self, contract: MutationContract) -> None:
        self.contract = contract
        self._manifest: SandboxManifest | None = None

    def create(self) -> SandboxManifest:
        self.contract.validate()
        if self.contract.worktree_path.exists():
            raise FileExistsError(f"Worktree already exists: {self.contract.worktree_path}")
        self.contract.worktree_path.parent.mkdir(parents=True, exist_ok=True)
        base_sha = self._git_source("rev-parse", self.contract.base_ref).stdout.strip()
        branch = f"codex/{self.contract.goal_id}-{self.contract.work_item_id}"
        self._git_source("worktree", "add", "-b", branch, str(self.contract.worktree_path), base_sha)
        self._manifest = SandboxManifest(
            self.contract.goal_id,
            self.contract.work_item_id,
            str(self.contract.worktree_path.resolve()),
            branch,
            base_sha,
            self.contract.idempotency_key,
            self.contract.implementation_owner,
        )
        return self._manifest

    def authorize_mutation(self, actor: str) -> None:
        self.contract.validate()
        if actor != self.contract.implementation_owner:
            raise PermissionError(f"Mutation owner is {self.contract.implementation_owner}, not {actor}")

    def resolve_write_path(self, relative_path: str) -> Path:
        self.contract.validate()
        if self._manifest is None:
            raise RuntimeError("Sandbox has not been created")
        normalized = relative_path.replace("\\", "/").lstrip("./")
        pure = PurePosixPath(normalized)
        if not normalized or pure.is_absolute() or ".." in pure.parts or any(part.lower() in _BLOCKED_PARTS for part in pure.parts):
            raise ValueError(f"Write path is blocked: {relative_path}")
        if not any(pure.match(pattern) for pattern in self.contract.path_allowlist):
            raise ValueError(f"Write path is outside the allowlist: {relative_path}")
        target = (self.contract.worktree_path / Path(*pure.parts)).resolve()
        if self.contract.worktree_path.resolve() not in target.parents:
            raise ValueError(f"Write path escapes the worktree: {relative_path}")
        return target

    def capture_artifacts(self) -> ArtifactManifest:
        if self._manifest is None:
            raise RuntimeError("Sandbox has not been created")
        result = subprocess.run(
            ["git", "-C", str(self.contract.worktree_path), "status", "--porcelain", "--untracked-files=all"],
            check=True,
            capture_output=True,
            text=True,
        )
        changed = tuple(sorted(line[3:].strip() for line in result.stdout.splitlines() if len(line) >= 4))
        return ArtifactManifest(
            self.contract.goal_id,
            self.contract.work_item_id,
            self.contract.idempotency_key,
            changed,
            str(self.contract.worktree_path.resolve()),
        )

    def _git_source(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", str(self.contract.repo_root), *args], check=True, capture_output=True, text=True)
