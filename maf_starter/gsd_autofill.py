from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from maf_starter.orchestration import AutoAnswerRecord


DEFAULT_CONTEXT_DOCS = (
    ".planning/PROJECT.md",
    ".planning/REQUIREMENTS.md",
    ".planning/ROADMAP.md",
    ".planning/STATE.md",
)


@dataclass(frozen=True)
class GsdAutoAnswerResult:
    question: str
    answer: str | None
    sources: list[str]
    confidence: float
    decision_type: str
    needs_input: bool
    metadata: dict[str, Any]

    def to_record(self, *, stage: str | None = None) -> AutoAnswerRecord:
        return AutoAnswerRecord(
            question=self.question,
            answer=self.answer,
            sources=self.sources,
            confidence=self.confidence,
            decision_type=self.decision_type,
            needs_input=self.needs_input,
            stage=stage,
            metadata=self.metadata,
        )


def resolve_gsd_question(
    question: str,
    *,
    project_root: Path,
    workspace_snapshot: dict[str, Any] | None = None,
    repo_snapshot: dict[str, Any] | None = None,
    phase_context_path: Path | None = None,
) -> GsdAutoAnswerResult:
    normalized = " ".join(question.strip().split())
    if not normalized:
        return GsdAutoAnswerResult(
            question=question,
            answer=None,
            sources=[],
            confidence=0.0,
            decision_type="needs_input",
            needs_input=True,
            metadata={"reason": "empty_question"},
        )

    documents = _load_context_documents(project_root=project_root, phase_context_path=phase_context_path)
    lowered = normalized.lower()

    if any(
        marker in lowered
        for marker in (
            "resource group",
            "subscription",
            "tenant",
            "endpoint",
            "deployment target",
            "project id",
            "customer",
            "secret",
            "api key",
        )
    ):
        return GsdAutoAnswerResult(
            question=normalized,
            answer=None,
            sources=[],
            confidence=0.0,
            decision_type="needs_input",
            needs_input=True,
            metadata={"reason": "environment_specific_question"},
        )

    workspace_answer = _resolve_workspace_question(lowered, workspace_snapshot, repo_snapshot)
    if workspace_answer is not None:
        return workspace_answer

    best = _best_document_answer(normalized, documents)
    if best is not None:
        return best

    return GsdAutoAnswerResult(
        question=normalized,
        answer=None,
        sources=[],
        confidence=0.0,
        decision_type="needs_input",
        needs_input=True,
        metadata={"reason": "no_confident_match"},
    )


def resolve_gsd_questions(
    questions: list[str],
    *,
    project_root: Path,
    workspace_snapshot: dict[str, Any] | None = None,
    repo_snapshot: dict[str, Any] | None = None,
    phase_context_path: Path | None = None,
) -> list[GsdAutoAnswerResult]:
    return [
        resolve_gsd_question(
            question,
            project_root=project_root,
            workspace_snapshot=workspace_snapshot,
            repo_snapshot=repo_snapshot,
            phase_context_path=phase_context_path,
        )
        for question in questions
    ]


def _load_context_documents(*, project_root: Path, phase_context_path: Path | None) -> list[tuple[Path, str]]:
    docs: list[tuple[Path, str]] = []
    for relative in DEFAULT_CONTEXT_DOCS:
        path = (project_root / relative).resolve()
        if path.exists():
            docs.append((path, path.read_text(encoding="utf-8", errors="replace")))
    if phase_context_path is not None and phase_context_path.exists():
        docs.append((phase_context_path.resolve(), phase_context_path.read_text(encoding="utf-8", errors="replace")))
    return docs


def _resolve_workspace_question(
    lowered: str,
    workspace_snapshot: dict[str, Any] | None,
    repo_snapshot: dict[str, Any] | None,
) -> GsdAutoAnswerResult | None:
    if workspace_snapshot is None and repo_snapshot is None:
        return None

    if any(token in lowered for token in ("workspace", "repo root", "worktree", "branch", "changed file")):
        snapshot = repo_snapshot or workspace_snapshot or {}
        repo_root = snapshot.get("root")
        branch = snapshot.get("branch")
        changed_files = snapshot.get("changed_files") or []
        dirty = snapshot.get("dirty")
        answer = (
            f"Workspace root is {repo_root or 'unknown'}, branch is {branch or 'unknown'}, "
            f"dirty state is {dirty}, and changed file count is {len(changed_files)}."
        )
        return GsdAutoAnswerResult(
            question=lowered,
            answer=answer,
            sources=["workspace_snapshot"],
            confidence=0.9,
            decision_type="workspace_snapshot",
            needs_input=False,
            metadata={"repo_snapshot": snapshot},
        )
    return None


def _best_document_answer(question: str, documents: list[tuple[Path, str]]) -> GsdAutoAnswerResult | None:
    query_tokens = _tokenize(question)
    if not query_tokens:
        return None

    best_path: Path | None = None
    best_line: str | None = None
    best_score = 0

    for path, content in documents:
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if len(line) < 8:
                continue
            score = len(query_tokens & _tokenize(line))
            if score > best_score:
                best_score = score
                best_path = path
                best_line = line

    if best_path is None or best_line is None:
        return None

    confidence = min(0.95, 0.45 + (best_score * 0.12))
    if confidence < 0.55:
        return None

    return GsdAutoAnswerResult(
        question=question,
        answer=best_line,
        sources=[str(best_path.relative_to(best_path.parents[1])) if len(best_path.parents) > 1 else str(best_path)],
        confidence=confidence,
        decision_type="planning_docs",
        needs_input=False,
        metadata={"matched_line": best_line, "token_overlap": best_score},
    )


def _tokenize(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9_\-]{1,}", text.lower())
        if token not in {"the", "and", "for", "with", "that", "this", "from", "what", "when", "where"}
    }
