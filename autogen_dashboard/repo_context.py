from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from autogen_dashboard.schemas import RepoContext, RepoOption


_IGNORED_SCAN_DIRS = {".git", ".venv", "state", ".tmp-tests", "__pycache__"}


def discover_local_repos(scan_root: Path) -> list[RepoOption]:
    root = scan_root.expanduser().resolve()
    if not root.exists() or not root.is_dir():
        return []

    discovered: dict[str, RepoOption] = {}
    options: list[RepoOption] = []
    if is_git_repo(root):
        root_context = collect_repo_context(root)
        root_option = RepoOption(
            name=root_context.name,
            path=root_context.root,
            root=root_context.root,
            kind=root_context.kind,
            branch=root_context.branch,
            dirty=root_context.dirty,
            detail=_option_detail(root_context),
            changed_files=list(root_context.changed_files),
            recent_commits=list(root_context.recent_commits),
            stack_hints=list(root_context.stack_hints),
            scanned_at=root_context.scanned_at,
            signature=root_context.signature,
        )
        discovered[root_option.root] = root_option
        options.append(root_option)
    for current_root, dir_names, _ in os.walk(root):
        current_path = Path(current_root)
        dir_names[:] = [
            name
            for name in sorted(dir_names, key=str.lower)
            if not _should_ignore_dir(name)
        ]
        if current_path == root:
            continue
        if not is_git_repo(current_path):
            continue
        try:
            context = collect_repo_context(current_path)
        except ValueError:
            continue
        option = RepoOption(
            name=context.name,
            path=context.root,
            root=context.root,
            kind=context.kind,
            branch=context.branch,
            dirty=context.dirty,
            detail=_option_detail(context),
            changed_files=list(context.changed_files),
            recent_commits=list(context.recent_commits),
            stack_hints=list(context.stack_hints),
            scanned_at=context.scanned_at,
            signature=context.signature,
        )
        if option.root not in discovered:
            discovered[option.root] = option
            options.append(option)
        dir_names[:] = []
    return sorted(options, key=lambda item: (item.name or item.root).lower())


def resolve_repo_root(repo_root: str | None, scan_root: Path) -> Path | None:
    if repo_root is None:
        return None

    raw = repo_root.strip()
    if not raw:
        return None

    root = scan_root.expanduser().resolve()
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        candidate = (root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if not candidate.exists() or not candidate.is_dir():
        raise ValueError(f"Repo path does not exist: {candidate}")
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Repo path must be inside {root}") from exc
    if not is_git_repo(candidate):
        raise ValueError(f"Repo path is not a git repository: {candidate}")
    return candidate


def is_git_repo(path: Path) -> bool:
    if shutil.which("git") is None:
        return False
    completed = _run_git(["rev-parse", "--show-toplevel"], cwd=path)
    if completed.returncode != 0:
        return False
    top_level = completed.stdout.strip()
    if not top_level:
        return False
    return Path(top_level).resolve() == path.expanduser().resolve()


def collect_repo_context(repo_root: Path) -> RepoContext:
    resolved_root = repo_root.expanduser().resolve()
    if not resolved_root.exists() or not resolved_root.is_dir():
        raise ValueError(f"Repo path does not exist: {resolved_root}")
    if shutil.which("git") is None:
        raise ValueError("Git is not installed.")

    top_level = _git_output(["rev-parse", "--show-toplevel"], cwd=resolved_root)
    if Path(top_level).resolve() != resolved_root:
        raise ValueError(f"Repo path is not a repository root or worktree root: {resolved_root}")
    branch = _safe_git_output(["rev-parse", "--abbrev-ref", "HEAD"], cwd=resolved_root)
    status_lines = _safe_git_output(["status", "--porcelain=1", "--branch"], cwd=resolved_root).splitlines()
    recent_commits = _safe_git_output(["log", "--oneline", "-n", "3"], cwd=resolved_root).splitlines()
    changed_files = _parse_changed_files(status_lines)
    stack_hints = _detect_stack_hints(Path(top_level))
    kind = detect_workspace_kind(resolved_root)

    return RepoContext(
        name=Path(top_level).name,
        kind=kind,
        root=top_level,
        branch=branch or None,
        dirty=bool(changed_files),
        changed_files=changed_files[:12],
        recent_commits=[line.strip() for line in recent_commits if line.strip()][:3],
        stack_hints=stack_hints,
        scanned_at=datetime.now(timezone.utc),
        signature=_workspace_signature(
            root=top_level,
            branch=branch or "",
            dirty=bool(changed_files),
            changed_files=changed_files[:12],
            recent_commits=[line.strip() for line in recent_commits if line.strip()][:3],
        ),
        error=None,
    )


def build_repo_brief(repo_context: RepoContext | None) -> str:
    if repo_context is None:
        return ""

    lines = [
        "Repository context from the local machine:",
        f"- repo: {repo_context.name}",
        f"- root: {repo_context.root}",
        f"- branch: {repo_context.branch or 'unknown'}",
        f"- dirty: {'yes' if repo_context.dirty else 'no'}",
    ]
    if repo_context.stack_hints:
        lines.append(f"- stack: {', '.join(repo_context.stack_hints)}")
    if repo_context.changed_files:
        lines.append("- changed files:")
        lines.extend(f"  - {path}" for path in repo_context.changed_files[:8])
    if repo_context.recent_commits:
        lines.append("- recent commits:")
        lines.extend(f"  - {commit}" for commit in repo_context.recent_commits)
    return "\n".join(lines)


def _option_detail(repo_context: RepoContext) -> str:
    detail_parts = [repo_context.kind, repo_context.branch or "unknown branch"]
    detail_parts.append("dirty" if repo_context.dirty else "clean")
    if repo_context.stack_hints:
        detail_parts.append(", ".join(repo_context.stack_hints[:3]))
    return " | ".join(detail_parts)


def detect_workspace_kind(repo_root: Path) -> str:
    git_entry = repo_root / ".git"
    if git_entry.is_file():
        return "worktree"
    return "repo"


def _detect_stack_hints(repo_root: Path) -> list[str]:
    hints: list[str] = []
    if any((repo_root / name).exists() for name in ("pyproject.toml", "requirements.txt", "requirements-dev.txt")):
        hints.append("Python")
    if (repo_root / "package.json").exists():
        hints.append("Node.js")
    if list(repo_root.glob("*.sln")) or list(repo_root.glob("**/*.csproj")):
        hints.append(".NET")
    if (repo_root / "host.json").exists():
        hints.append("Azure Functions")
    if list(repo_root.glob("**/*.bicep")):
        hints.append("Bicep")
    if (repo_root / "docker-compose.yml").exists() or (repo_root / "compose.yaml").exists():
        hints.append("Docker Compose")
    return hints


def _parse_changed_files(status_lines: list[str]) -> list[str]:
    changed_files: list[str] = []
    for line in status_lines:
        if not line or line.startswith("##"):
            continue
        candidate = line[3:].strip()
        if " -> " in candidate:
            candidate = candidate.split(" -> ", 1)[1].strip()
        if candidate:
            changed_files.append(candidate)
    return changed_files


def _should_ignore_dir(name: str) -> bool:
    return name in _IGNORED_SCAN_DIRS or name.startswith(".")


def _workspace_signature(
    *,
    root: str,
    branch: str,
    dirty: bool,
    changed_files: list[str],
    recent_commits: list[str],
) -> str:
    changed_signature = ",".join(changed_files[:6]) if changed_files else "clean"
    commit_signature = recent_commits[0] if recent_commits else "no-commits"
    return "|".join(
        [
            root,
            branch or "unknown",
            "dirty" if dirty else "clean",
            changed_signature,
            commit_signature,
        ]
    )


def _safe_git_output(args: list[str], *, cwd: Path) -> str:
    completed = _run_git(args, cwd=cwd)
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def _git_output(args: list[str], *, cwd: Path) -> str:
    completed = _run_git(args, cwd=cwd)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise ValueError(detail)
    return completed.stdout.strip()


def _run_git(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        check=False,
    )
