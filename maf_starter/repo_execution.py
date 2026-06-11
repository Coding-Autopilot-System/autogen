from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
import tempfile
from typing import Any, Literal

from maf_starter.tools import resolve_repo_path


WriteAction = Literal["create_file", "update_file", "append_file"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class WriteOperation:
    action: WriteAction
    path: str
    content: str
    reason: str | None = None
    encoding: str = "utf-8"

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "path": self.path,
            "content": self.content,
            "reason": self.reason,
            "encoding": self.encoding,
        }


@dataclass
class WriteOperationRecord:
    action: WriteAction
    path: str
    status: Literal["applied", "skipped"]
    before_exists: bool
    after_exists: bool
    changed: bool
    bytes_written: int
    reason: str | None = None
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action,
            "path": self.path,
            "status": self.status,
            "before_exists": self.before_exists,
            "after_exists": self.after_exists,
            "changed": self.changed,
            "bytes_written": self.bytes_written,
            "reason": self.reason,
            "created_at": self.created_at,
        }


@dataclass
class ChangeCaptureResult:
    changed_files: list[str]
    write_operations: list[WriteOperationRecord]
    diff_patch: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "changed_files": list(self.changed_files),
            "write_operations": [record.to_dict() for record in self.write_operations],
            "diff_patch": self.diff_patch,
        }


def parse_write_operations_payload(payload: Any) -> list[WriteOperation]:
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise ValueError("file_operations must be a list")

    operations: list[WriteOperation] = []
    for item in payload:
        if not isinstance(item, dict):
            raise ValueError("Each file operation must be an object")
        action = str(item.get("action", "")).strip()
        path = str(item.get("path", "")).strip()
        content = item.get("content", "")
        reason = str(item.get("reason", "")).strip() or None
        encoding = str(item.get("encoding", "utf-8")).strip() or "utf-8"
        if action not in {"create_file", "update_file", "append_file"}:
            raise ValueError(f"Unsupported write action: {action or '<missing>'}")
        if not path:
            raise ValueError("Write operation path is required")
        if not isinstance(content, str):
            raise ValueError("Write operation content must be a string")
        operations.append(
            WriteOperation(
                action=action,
                path=path,
                content=content,
                reason=reason,
                encoding=encoding,
            )
        )
    return operations


def create_file(repo_root: Path, operation: WriteOperation) -> WriteOperationRecord:
    target = _resolve_write_target(repo_root, operation.path)
    if target.exists():
        raise ValueError(f"create_file requires a new path: {operation.path}")
    _write_text(target, operation.content, operation.encoding)
    return WriteOperationRecord(
        action="create_file",
        path=_relative_path(repo_root, target),
        status="applied",
        before_exists=False,
        after_exists=True,
        changed=True,
        bytes_written=len(operation.content.encode(operation.encoding)),
        reason=operation.reason,
    )


def update_file(repo_root: Path, operation: WriteOperation) -> WriteOperationRecord:
    target = _resolve_write_target(repo_root, operation.path)
    if not target.exists():
        raise ValueError(f"update_file requires an existing path: {operation.path}")
    if target.is_dir():
        raise ValueError(f"update_file requires a file path: {operation.path}")
    before_text = _read_text(target)
    changed = before_text != operation.content
    if changed:
        _write_text(target, operation.content, operation.encoding)
    return WriteOperationRecord(
        action="update_file",
        path=_relative_path(repo_root, target),
        status="applied" if changed else "skipped",
        before_exists=True,
        after_exists=True,
        changed=changed,
        bytes_written=len(operation.content.encode(operation.encoding)) if changed else 0,
        reason=operation.reason,
    )


def append_file(repo_root: Path, operation: WriteOperation) -> WriteOperationRecord:
    target = _resolve_write_target(repo_root, operation.path)
    if not target.exists():
        raise ValueError(f"append_file requires an existing path: {operation.path}")
    if target.is_dir():
        raise ValueError(f"append_file requires a file path: {operation.path}")
    before_text = _read_text(target)
    if operation.content:
        _write_text(target, before_text + operation.content, operation.encoding)
    after_text = _read_text(target)
    changed = before_text != after_text
    return WriteOperationRecord(
        action="append_file",
        path=_relative_path(repo_root, target),
        status="applied" if changed else "skipped",
        before_exists=True,
        after_exists=True,
        changed=changed,
        bytes_written=len(operation.content.encode(operation.encoding)) if changed else 0,
        reason=operation.reason,
    )


def apply_write_operations(repo_root: Path, operations: list[WriteOperation]) -> ChangeCaptureResult:
    normalized_root = repo_root.resolve()
    original_contents: dict[str, str] = {}
    final_contents: dict[str, str] = {}
    records: list[WriteOperationRecord] = []

    for operation in operations:
        target = _resolve_write_target(normalized_root, operation.path)
        relative_path = _relative_path(normalized_root, target)
        if relative_path not in original_contents:
            original_contents[relative_path] = _read_text(target) if target.exists() else ""

        if operation.action == "create_file":
            record = create_file(normalized_root, operation)
        elif operation.action == "update_file":
            record = update_file(normalized_root, operation)
        elif operation.action == "append_file":
            record = append_file(normalized_root, operation)
        else:
            raise ValueError(f"Unsupported write action: {operation.action}")

        final_contents[relative_path] = _read_text(target) if target.exists() else ""
        records.append(record)

    changed_files = [
        relative_path
        for relative_path, before_text in original_contents.items()
        if before_text != final_contents.get(relative_path, "")
    ]
    diff_patch = _build_diff_patch(original_contents, final_contents)
    return ChangeCaptureResult(
        changed_files=sorted(changed_files),
        write_operations=records,
        diff_patch=diff_patch,
    )


def _resolve_write_target(repo_root: Path, raw_path: str) -> Path:
    target = resolve_repo_path(repo_root, raw_path, allow_missing=True, for_write=True)
    if target.exists() and target.is_dir():
        raise ValueError(f"Write target must be a file: {raw_path}")
    return target


def _write_text(path: Path, content: str, encoding: str) -> None:
    if encoding.lower() != "utf-8":
        raise ValueError("Only UTF-8 write operations are supported")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="", delete=False, dir=path.parent, suffix=".tmp") as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    temp_path.replace(path)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"File is not readable as UTF-8 text: {path}") from exc


def _relative_path(repo_root: Path, path: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def _build_diff_patch(original_contents: dict[str, str], final_contents: dict[str, str]) -> str:
    chunks: list[str] = []
    for relative_path in sorted(original_contents):
        before_text = original_contents.get(relative_path, "")
        after_text = final_contents.get(relative_path, "")
        if before_text == after_text:
            continue
        before_lines = before_text.splitlines(keepends=True)
        after_lines = after_text.splitlines(keepends=True)
        diff_lines = unified_diff(
            before_lines,
            after_lines,
            fromfile=f"a/{relative_path}",
            tofile=f"b/{relative_path}",
        )
        chunks.append("".join(diff_lines))
    return "\n".join(chunk for chunk in chunks if chunk).strip()
