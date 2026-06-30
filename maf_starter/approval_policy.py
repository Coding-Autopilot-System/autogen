from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import PurePosixPath
from typing import Any, Literal

from maf_starter.validation_runner import ValidationCommand


RiskLevel = Literal["routine_safe", "destructive", "externally_visible", "blocked"]


@dataclass
class ApprovalScope:
    action_kind: str
    risk_level: RiskLevel
    reason: str
    affected_paths: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    external_targets: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_kind": self.action_kind,
            "risk_level": self.risk_level,
            "reason": self.reason,
            "affected_paths": list(self.affected_paths),
            "commands": list(self.commands),
            "external_targets": list(self.external_targets),
        }


@dataclass
class ExecutionRiskDecision:
    classification: RiskLevel
    approval_required: bool
    blocked: bool
    scope: ApprovalScope

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification,
            "approval_required": self.approval_required,
            "blocked": self.blocked,
            "scope": self.scope.to_dict(),
        }


def classify_write_operations(operations: list[dict[str, Any]]) -> ExecutionRiskDecision:
    if not operations:
        return _decision(
            "routine_safe",
            action_kind="file_write",
            reason="No write operations were requested.",
        )

    affected_paths = [str(operation.get("path", "")).strip() for operation in operations if str(operation.get("path", "")).strip()]
    unsupported_actions = [
        str(operation.get("action", "")).strip()
        for operation in operations
        if str(operation.get("action", "")).strip() not in {"create_file", "update_file", "append_file"}
    ]
    destructive_actions = [action for action in unsupported_actions if action in {"delete_file", "move_file", "rename_file"}]
    if destructive_actions:
        return _decision(
            "destructive",
            action_kind="file_write",
            reason=f"Destructive file operations require explicit approval: {', '.join(sorted(set(destructive_actions)))}.",
            affected_paths=affected_paths,
        )
    if unsupported_actions:
        return _decision(
            "blocked",
            action_kind="file_write",
            reason=f"Unsupported write actions are blocked: {', '.join(sorted(set(unsupported_actions)))}.",
            affected_paths=affected_paths,
        )
    blocked_paths = [path for path in affected_paths if _is_blocked_write_path(path)]
    if blocked_paths:
        return _decision(
            "blocked",
            action_kind="file_write",
            reason="Secret-bearing or out-of-policy paths are blocked from autonomous writes.",
            affected_paths=blocked_paths,
        )

    return _decision(
        "routine_safe",
        action_kind="file_write",
        reason="Only routine-safe repo-local text edits were requested.",
        affected_paths=affected_paths,
    )


def classify_validation_commands(commands: list[ValidationCommand]) -> ExecutionRiskDecision:
    if not commands:
        return _decision(
            "routine_safe",
            action_kind="validation",
            reason="No validation commands were required.",
        )

    serialized = [" ".join(command.command) for command in commands]
    for command in commands:
        normalized = " ".join(command.command).strip().lower()
        if normalized.startswith("git diff --check"):
            continue
        if normalized.startswith("python -m compileall"):
            continue
        if normalized.startswith("python -m unittest discover -s tests -v"):
            continue
        if normalized.startswith("node --check "):
            continue
        if _looks_externally_visible(normalized):
            return _decision(
                "externally_visible",
                action_kind="validation",
                reason="Validation commands would touch external services or visibility boundaries.",
                commands=serialized,
                external_targets=[normalized],
            )
        return _decision(
            "blocked",
            action_kind="validation",
            reason="Validation commands outside the safe allowlist are blocked.",
            commands=serialized,
        )

    return _decision(
        "routine_safe",
        action_kind="validation",
        reason="Validation commands stayed within the safe local command ladder.",
        commands=serialized,
    )


def is_execution_approved(prompt: str, approval_word: str) -> bool:
    normalized = str(prompt or "").strip().lower()
    if not normalized:
        return False
    approval_token = str(approval_word or "APPROVE").strip().lower()
    return normalized == approval_token or normalized.startswith("approve") or normalized.startswith("approved") or normalized.startswith("proceed")


def classify_external_action(action: str, target: str) -> ExecutionRiskDecision:
    normalized = str(action or "").strip().lower()
    external = {"push", "deploy", "message", "production_mutation"}
    destructive = {"delete"}
    if normalized in external:
        return _decision(
            "externally_visible",
            action_kind=normalized,
            reason=f"{normalized} requires deterministic approval before execution.",
            external_targets=[target],
        )
    if normalized in destructive:
        return _decision(
            "destructive",
            action_kind=normalized,
            reason=f"{normalized} requires deterministic approval before execution.",
            external_targets=[target],
        )
    return _decision("blocked", action_kind=normalized or "unknown", reason="Unknown external action is blocked.")


def require_action_approval(action: str, target: str, *, approved: bool) -> None:
    decision = classify_external_action(action, target)
    if decision.blocked:
        raise PermissionError(decision.scope.reason)
    if decision.approval_required and not approved:
        raise PermissionError(decision.scope.reason)


def _decision(
    classification: RiskLevel,
    *,
    action_kind: str,
    reason: str,
    affected_paths: list[str] | None = None,
    commands: list[str] | None = None,
    external_targets: list[str] | None = None,
) -> ExecutionRiskDecision:
    return ExecutionRiskDecision(
        classification=classification,
        approval_required=classification in {"destructive", "externally_visible"},
        blocked=classification == "blocked",
        scope=ApprovalScope(
            action_kind=action_kind,
            risk_level=classification,
            reason=reason,
            affected_paths=affected_paths or [],
            commands=commands or [],
            external_targets=external_targets or [],
        ),
    )


def _looks_externally_visible(command: str) -> bool:
    normalized = f" {command.strip()} "
    return any(
        token in normalized
        for token in (" git push ", " az ", " docker push ", " deploy ", " service ", " notify ", " send ")
    )


def _is_blocked_write_path(raw_path: str) -> bool:
    normalized = str(raw_path or "").replace("\\", "/").strip().lower()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if not normalized:
        return True
    path = PurePosixPath(normalized)
    if any(part in {".git", ".venv", "__pycache__", "state", ".tmp-tests"} for part in path.parts):
        return True
    name = path.name
    if name == ".env" or name.startswith(".env."):
        return True
    return False
