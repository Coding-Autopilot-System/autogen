from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ValidationCommand:
    label: str
    command: list[str]
    reason: str
    cwd: str
    created_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "command": list(self.command),
            "reason": self.reason,
            "cwd": self.cwd,
            "created_at": self.created_at,
        }


@dataclass
class ValidationPlan:
    repo_root: str
    changed_files: list[str]
    commands: list[ValidationCommand]

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_root": self.repo_root,
            "changed_files": list(self.changed_files),
            "commands": [command.to_dict() for command in self.commands],
        }


@dataclass
class ValidationResult:
    label: str
    command: list[str]
    cwd: str
    exit_code: int
    duration_seconds: float
    output_summary: str
    status: str
    completed_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "command": list(self.command),
            "cwd": self.cwd,
            "exit_code": self.exit_code,
            "duration_seconds": self.duration_seconds,
            "output_summary": self.output_summary,
            "status": self.status,
            "completed_at": self.completed_at,
        }


def plan_validation(repo_root: Path, changed_files: list[str]) -> ValidationPlan:
    normalized_root = repo_root.resolve()
    unique_files = sorted({path.replace("\\", "/") for path in changed_files if path})
    commands: list[ValidationCommand] = []

    if (normalized_root / ".git").exists():
        commands.append(
            ValidationCommand(
                label="git diff --check",
                command=["git", "diff", "--check"],
                reason="Verify patch formatting and whitespace issues before deeper validation.",
                cwd=str(normalized_root),
            )
        )

    python_files = [path for path in unique_files if path.endswith(".py")]
    if python_files:
        compile_targets = _validation_targets(python_files)
        commands.append(
            ValidationCommand(
                label="python -m compileall",
                command=["python", "-m", "compileall", *compile_targets],
                reason="Compile touched Python paths to catch syntax errors.",
                cwd=str(normalized_root),
            )
        )
        if (normalized_root / "tests").exists() and any(_needs_python_tests(path) for path in python_files):
            commands.append(
                ValidationCommand(
                    label="python -m unittest discover -s tests -v",
                    command=["python", "-m", "unittest", "discover", "-s", "tests", "-v"],
                    reason="Run the repo's stdlib test suite when runtime or test Python paths changed.",
                    cwd=str(normalized_root),
                )
            )

    javascript_files = [path for path in unique_files if path.endswith((".js", ".mjs", ".cjs"))]
    for relative_path in javascript_files:
        commands.append(
            ValidationCommand(
                label=f"node --check {relative_path}",
                command=["node", "--check", relative_path],
                reason="Check changed JavaScript files for syntax errors.",
                cwd=str(normalized_root),
            )
        )

    return ValidationPlan(
        repo_root=str(normalized_root),
        changed_files=unique_files,
        commands=commands,
    )


def execute_validation_plan(plan: ValidationPlan, *, timeout_seconds: int = 120) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for command in plan.commands:
        started = time.perf_counter()
        completed = subprocess.run(
            command.command,
            cwd=command.cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout_seconds,
        )
        duration = time.perf_counter() - started
        output_summary = _summarize_output(completed.stdout, completed.stderr)
        results.append(
            ValidationResult(
                label=command.label,
                command=command.command,
                cwd=command.cwd,
                exit_code=completed.returncode,
                duration_seconds=round(duration, 3),
                output_summary=output_summary,
                status="passed" if completed.returncode == 0 else "failed",
            )
        )
    return results


def _validation_targets(paths: list[str]) -> list[str]:
    targets: list[str] = []
    seen: set[str] = set()
    for path in paths:
        parts = [part for part in Path(path).parts if part not in {".", ""}]
        target = "tests" if parts and parts[0] == "tests" else parts[0]
        if not target:
            continue
        if target not in seen:
            seen.add(target)
            targets.append(target)
    return targets or ["."]


def _needs_python_tests(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized.startswith("tests/") or normalized.startswith("autogen_dashboard/") or normalized.startswith("maf_starter/")


def _summarize_output(stdout: str, stderr: str) -> str:
    combined = "\n".join(part.strip() for part in (stdout, stderr) if part and part.strip()).strip()
    if not combined:
        return "Command completed without output."
    lines = combined.splitlines()
    summary = "\n".join(lines[:20])
    if len(summary) > 1600:
        return summary[:1597] + "..."
    return summary
