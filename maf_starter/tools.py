from __future__ import annotations

import subprocess
from pathlib import Path

from agent_framework import tool

from maf_starter.config import current_repo_root


SKIP_DIR_NAMES = {".git", ".venv", "__pycache__", "state", ".tmp-tests"}
MAX_FILE_READ_LINES = 400
MAX_SEARCH_MATCHES = 60


def resolve_repo_path(repo_root: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = (repo_root / candidate).resolve()
    else:
        candidate = candidate.resolve()

    try:
        candidate.relative_to(repo_root)
    except ValueError as exc:
        raise ValueError(f"Path escapes the configured repo root: {raw_path}") from exc

    if not candidate.exists():
        raise ValueError(f"Path does not exist: {raw_path}")

    return candidate


def _should_skip(path: Path, repo_root: Path) -> bool:
    relative = path.relative_to(repo_root)
    return any(part in SKIP_DIR_NAMES for part in relative.parts)


def _iter_repo_files(repo_root: Path, pattern: str) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob(pattern or "*"):
        if not path.is_file():
            continue
        if _should_skip(path, repo_root):
            continue
        files.append(path)
    return sorted(files)


def _read_text_file(path: Path) -> str | None:
    try:
        data = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None
    if "\x00" in data:
        return None
    return data


def build_repo_context_snapshot(repo_root: Path) -> dict[str, object]:
    normalized_root = repo_root.resolve()
    top_level = [
        f"{item.name}/" if item.is_dir() else item.name
        for item in normalized_root.iterdir()
        if item.name not in SKIP_DIR_NAMES
    ]
    snapshot: dict[str, object] = {
        "root": str(normalized_root),
        "top_level_items": top_level[:20],
        "file_count_hint": len(_iter_repo_files(normalized_root, "*")),
    }

    git_dir = normalized_root / ".git"
    if git_dir.exists():
        result = subprocess.run(
            ["git", "status", "--short", "--branch"],
            cwd=normalized_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.stdout.strip():
            lines = result.stdout.strip().splitlines()
            snapshot["git_status"] = lines
            snapshot["branch"] = lines[0]
    return snapshot


def build_repo_tools(repo_root: Path) -> list[object]:
    default_root = repo_root.resolve()

    def runtime_root() -> Path:
        return current_repo_root(default_root)

    @tool(description="Get a compact overview of the local repository, including top-level items and git status when available.")
    def get_repo_overview() -> str:
        """Summarize the configured repo root for the agent."""
        normalized_root = runtime_root()
        top_level = sorted(
            f"{item.name}/" if item.is_dir() else item.name
            for item in normalized_root.iterdir()
            if item.name not in SKIP_DIR_NAMES
        )

        lines = [
            f"Repo root: {normalized_root}",
            "Top-level items:",
            *[f"- {item}" for item in top_level[:30]],
        ]

        git_dir = normalized_root / ".git"
        if git_dir.exists():
            result = subprocess.run(
                ["git", "status", "--short", "--branch"],
                cwd=normalized_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if result.stdout.strip():
                lines.append("Git status:")
                lines.extend(result.stdout.strip().splitlines())

        return "\n".join(lines)

    @tool(description="List repository files relative to the configured repo root. Use this before reading files when you do not know the exact path.")
    def list_repo_files(pattern: str = "*", limit: int = 200) -> str:
        """List files in the repo."""
        normalized_root = runtime_root()
        safe_limit = max(1, min(limit, 500))
        files = _iter_repo_files(normalized_root, pattern)
        if not files:
            return f"No files matched pattern {pattern!r}."
        relative_paths = [path.relative_to(normalized_root).as_posix() for path in files[:safe_limit]]
        lines = [f"Matched {min(len(files), safe_limit)} of {len(files)} files for pattern {pattern!r}:"]
        lines.extend(relative_paths)
        if len(files) > safe_limit:
            lines.append(f"... {len(files) - safe_limit} more omitted")
        return "\n".join(lines)

    @tool(description="Read a text file from the repository with optional line slicing. Path must stay under the configured repo root.")
    def read_repo_file(path: str, start_line: int = 1, end_line: int = 200) -> str:
        """Read a repository file safely."""
        normalized_root = runtime_root()
        resolved = resolve_repo_path(normalized_root, path)
        if not resolved.is_file():
            raise ValueError(f"Not a file: {path}")

        safe_start = max(1, start_line)
        safe_end = max(safe_start, min(end_line, safe_start + MAX_FILE_READ_LINES - 1))
        contents = _read_text_file(resolved)
        if contents is None:
            return f"File is not readable as UTF-8 text: {path}"

        lines = contents.splitlines()
        selected = lines[safe_start - 1 : safe_end]
        numbered = [f"{index}: {line}" for index, line in enumerate(selected, start=safe_start)]
        header = f"{resolved.relative_to(normalized_root).as_posix()} lines {safe_start}-{safe_end}"
        return "\n".join([header, *numbered]) if numbered else f"{header}\n<empty range>"

    @tool(description="Search text across repository files and return matching lines with file and line number.")
    def search_repo(pattern: str, limit: int = 30, case_sensitive: bool = False) -> str:
        """Search the repo for a literal text pattern."""
        normalized_root = runtime_root()
        if not pattern.strip():
            raise ValueError("pattern must not be empty")

        safe_limit = max(1, min(limit, MAX_SEARCH_MATCHES))
        needle = pattern if case_sensitive else pattern.lower()
        matches: list[str] = []

        for path in _iter_repo_files(normalized_root, "*"):
            contents = _read_text_file(path)
            if contents is None:
                continue
            for line_number, line in enumerate(contents.splitlines(), start=1):
                haystack = line if case_sensitive else line.lower()
                if needle in haystack:
                    matches.append(f"{path.relative_to(normalized_root).as_posix()}:{line_number}: {line.strip()}")
                    if len(matches) >= safe_limit:
                        break
            if len(matches) >= safe_limit:
                break

        if not matches:
            return f"No matches found for {pattern!r}."
        return "\n".join(matches)

    @tool(
        description="Pause and request human approval for a proposed plan, change, or risky action before continuing.",
        approval_mode="always_require",
    )
    def request_human_approval(summary: str) -> str:
        """Request human approval before the agent treats a plan as approved."""
        return f"Human approved this proposal: {summary}"

    return [
        get_repo_overview,
        list_repo_files,
        read_repo_file,
        search_repo,
        request_human_approval,
    ]
