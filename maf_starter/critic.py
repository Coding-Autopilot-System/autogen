from __future__ import annotations

from dataclasses import dataclass
import re
import sys
from typing import Literal

from maf_starter.config import Settings


@dataclass(frozen=True)
class Finding:
    check: str
    severity: Literal["blocking", "advisory"]
    file: str
    line: int | None
    detail: str


@dataclass(frozen=True)
class DiffFile:
    path: str
    added_lines: list[str]


@dataclass(frozen=True)
class CriticReport:
    findings: list[Finding]
    blocking_count: int
    advisory_count: int
    exit_code: int


_BARE_EXCEPT_PATTERN = re.compile(r"^\s*except\s*:\s*$")
_EXCEPTION_EXCEPT_PATTERN = re.compile(r"^\s*except\s+Exception(?:\s+as\s+\w+)?\s*:\s*$")
_LOG_TOKENS = ("logger.", "logging.", "print(", "emit_failure_telemetry(", "telemetry.")
_TYPED_FAILURE_TOKENS = ("FailureState", "McpException", "ValueError", "RuntimeError", "InvalidOperationException")


def parse_unified_diff(diff_text: str) -> list[DiffFile]:
    files: list[DiffFile] = []
    current_path: str | None = None
    current_added: list[str] = []

    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            if current_path is not None:
                files.append(DiffFile(path=current_path, added_lines=current_added))
            current_path = None
            current_added = []
            continue
        if line.startswith("+++ b/"):
            current_path = line[6:]
            continue
        if current_path is None:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            current_added.append(line[1:])

    if current_path is not None:
        files.append(DiffFile(path=current_path, added_lines=current_added))

    return files


def check_bare_except(file_path: str, added_lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for index, line in enumerate(added_lines):
        if not (_BARE_EXCEPT_PATTERN.match(line) or _EXCEPTION_EXCEPT_PATTERN.match(line)):
            continue
        window = added_lines[index + 1 : index + 5]
        has_reraise = any("raise" in candidate for candidate in window)
        has_logging = any(any(token in candidate for token in _LOG_TOKENS) for candidate in window)
        has_typed_failure = any(any(token in candidate for token in _TYPED_FAILURE_TOKENS) for candidate in window)
        if has_reraise and has_logging and has_typed_failure:
            continue
        findings.append(
            Finding(
                check="bare-except",
                severity="blocking",
                file=file_path,
                line=index + 1,
                detail="Broad exception handler added without a typed, logged re-raise path.",
            )
        )
    return findings


def check_missing_telemetry(file_path: str, added_lines: list[str]) -> list[Finding]:
    findings: list[Finding] = []
    for index, line in enumerate(added_lines):
        if "except" not in line:
            continue
        window = added_lines[index + 1 : index + 5]
        has_logging = any(any(token in candidate for token in _LOG_TOKENS) for candidate in window)
        if has_logging:
            continue
        findings.append(
            Finding(
                check="missing-telemetry",
                severity="advisory",
                file=file_path,
                line=index + 1,
                detail="Exception path does not emit structured telemetry or logging.",
            )
        )
    return findings


def check_file_size_limit(file_path: str, added_line_count: int, limit: int = 400) -> list[Finding]:
    if added_line_count <= limit:
        return []
    return [
        Finding(
            check="file-size-limit",
            severity="advisory",
            file=file_path,
            line=None,
            detail=f"Added line count {added_line_count} exceeds limit {limit}.",
        )
    ]


def run_critic(diff_text: str, *, llm_pass: bool = False, settings: Settings | None = None) -> CriticReport:
    if llm_pass:
        raise NotImplementedError("LLM critic pass is reserved for a future phase.")

    try:
        _ = settings
        files = parse_unified_diff(diff_text)
        if not files:
            raise ValueError("No unified diff content was found.")

        findings: list[Finding] = []
        for diff_file in files:
            findings.extend(check_bare_except(diff_file.path, diff_file.added_lines))
            findings.extend(check_missing_telemetry(diff_file.path, diff_file.added_lines))
            findings.extend(check_file_size_limit(diff_file.path, len(diff_file.added_lines)))

        blocking_count = sum(1 for finding in findings if finding.severity == "blocking")
        advisory_count = sum(1 for finding in findings if finding.severity == "advisory")
        return CriticReport(
            findings=findings,
            blocking_count=blocking_count,
            advisory_count=advisory_count,
            exit_code=1 if blocking_count > 0 else 0,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"critic error: {exc}", file=sys.stderr)
        finding = Finding(
            check="critic-error",
            severity="advisory",
            file="<critic>",
            line=None,
            detail=str(exc),
        )
        return CriticReport(findings=[finding], blocking_count=0, advisory_count=1, exit_code=0)
