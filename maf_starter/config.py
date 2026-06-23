from __future__ import annotations

import os
from contextvars import ContextVar, Token
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TypeAlias

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_MODEL = "gemini-2.5-flash"
DEFAULT_MODEL_CANDIDATES = (
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite-preview",
    "gemini-2.5-pro",
    "gemini-3.1-pro-preview",
)
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-6"

PathLike: TypeAlias = str | Path
_ACTIVE_REPO_ROOT: ContextVar[Path | None] = ContextVar("maf_active_repo_root", default=None)
_ACTIVE_CHECKPOINT_DIR: ContextVar[Path | None] = ContextVar("maf_active_checkpoint_dir", default=None)


@dataclass(frozen=True)
class Settings:
    project_root: Path
    entities_dir: Path
    repo_root: Path
    checkpoint_dir: Path
    model: str
    base_url: str
    api_key: str = field(repr=False)
    route_lane: str = "auto"
    requested_provider: str | None = None
    requested_model: str | None = None
    fallback_chain: tuple[str, ...] = ()
    anthropic_api_key: str | None = field(default=None, repr=False)
    anthropic_model: str | None = None
    gemini_cli_command: str = "gemini.cmd"
    gemini_cli_model: str | None = None
    claude_cli_command: str = "claude"
    claude_cli_model: str | None = None
    claude_code_git_bash_path: str | None = None
    codex_cli_command: str = "codex.cmd"
    codex_cli_model: str | None = None
    model_candidates: tuple[str, ...] = DEFAULT_MODEL_CANDIDATES
    ollama_base_url: str | None = None
    ollama_model: str = "gemma3"

    def with_run_scope(
        self,
        *,
        repo_root: PathLike | None = None,
        checkpoint_dir: PathLike | None = None,
    ) -> Settings:
        scoped_repo_root = _coerce_path(
            project_root=self.project_root,
            value=repo_root if repo_root is not None else self.repo_root,
            label="repo root",
            must_exist=True,
        )
        scoped_checkpoint_dir = _coerce_path(
            project_root=self.project_root,
            value=checkpoint_dir if checkpoint_dir is not None else self.checkpoint_dir,
            label="checkpoint dir",
            must_exist=False,
        )
        return replace(self, repo_root=scoped_repo_root, checkpoint_dir=scoped_checkpoint_dir)


@dataclass(frozen=True)
class RunScopeTokens:
    repo_root_token: Token[Path | None]
    checkpoint_dir_token: Token[Path | None]


def _resolve_project_path(project_root: Path, raw_value: str | None, default_value: str) -> Path:
    value = (raw_value or default_value).strip()
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = (project_root / candidate).resolve()
    return candidate.resolve()


def _coerce_path(
    *,
    project_root: Path,
    value: PathLike,
    label: str,
    must_exist: bool,
) -> Path:
    candidate = Path(value).expanduser()
    if not candidate.is_absolute():
        candidate = (project_root / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if must_exist and not candidate.exists():
        raise ValueError(f"Configured {label} does not exist: {candidate}")
    return candidate


def _split_candidates(raw_value: str | None) -> tuple[str, ...]:
    if not raw_value:
        return DEFAULT_MODEL_CANDIDATES
    values = tuple(part.strip() for part in raw_value.split(",") if part.strip())
    return values or DEFAULT_MODEL_CANDIDATES


def _default_fallback_chain(
    *,
    anthropic_model: str | None,
    anthropic_api_key: str | None,
    ollama_base_url: str | None = None,
    ollama_model: str = "gemma3",
) -> tuple[str, ...]:
    chain: list[str] = [
        "gemini:gemini-2.5-pro",
        "gemini:gemini-2.5-flash",
        "gemini:gemini-2.5-flash-lite",
    ]
    if anthropic_api_key:
        chain.insert(1, f"anthropic:{anthropic_model or DEFAULT_ANTHROPIC_MODEL}")
    if ollama_base_url:
        chain.insert(0, f"ollama:{ollama_model}")
    chain.extend(
        [
            "claude-cli",
            "codex-cli",
            "gemini-cli:gemini-2.5-pro",
        ]
    )
    return tuple(chain)


def _split_fallback_chain(
    raw_value: str | None,
    *,
    anthropic_model: str | None,
    anthropic_api_key: str | None,
    ollama_base_url: str | None = None,
    ollama_model: str = "gemma3",
) -> tuple[str, ...]:
    if not raw_value:
        return _default_fallback_chain(
            anthropic_model=anthropic_model,
            anthropic_api_key=anthropic_api_key,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model,
        )
    values = tuple(part.strip() for part in raw_value.split(",") if part.strip())
    return values


def mask_secret(secret: str) -> str:
    if not secret:
        return "<missing>"
    if len(secret) <= 8:
        return "*" * len(secret)
    return f"{secret[:4]}...{secret[-4:]}"


def activate_run_scope(
    settings: Settings,
    *,
    repo_root: PathLike | None = None,
    checkpoint_dir: PathLike | None = None,
) -> tuple[Settings, RunScopeTokens]:
    scoped = settings.with_run_scope(repo_root=repo_root, checkpoint_dir=checkpoint_dir)
    tokens = RunScopeTokens(
        repo_root_token=_ACTIVE_REPO_ROOT.set(scoped.repo_root),
        checkpoint_dir_token=_ACTIVE_CHECKPOINT_DIR.set(scoped.checkpoint_dir),
    )
    return scoped, tokens


def reset_run_scope(tokens: RunScopeTokens) -> None:
    _ACTIVE_REPO_ROOT.reset(tokens.repo_root_token)
    _ACTIVE_CHECKPOINT_DIR.reset(tokens.checkpoint_dir_token)


def current_repo_root(default_repo_root: Path) -> Path:
    return (_ACTIVE_REPO_ROOT.get() or default_repo_root).resolve()


def current_checkpoint_dir(default_checkpoint_dir: Path) -> Path:
    return (_ACTIVE_CHECKPOINT_DIR.get() or default_checkpoint_dir).resolve()


def load_settings(*, env_path: Path | None = None, project_root: Path | None = None) -> Settings:
    root = (project_root or PROJECT_ROOT).resolve()
    dotenv_path = env_path or (root / ".env")
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path, override=False)

    api_key = (os.getenv("MAF_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
    ollama_base_url = (os.getenv("OLLAMA_BASE_URL") or "").strip() or None
    ollama_model = (os.getenv("OLLAMA_MODEL") or "gemma3").strip()
    if not api_key and not ollama_base_url:
        raise ValueError(
            "Set GEMINI_API_KEY or MAF_API_KEY in the repo .env file, "
            "or set OLLAMA_BASE_URL for local-only operation."
        )

    model = (os.getenv("MAF_MODEL") or os.getenv("GEMINI_MODEL") or DEFAULT_MODEL).strip()
    base_url = (os.getenv("MAF_BASE_URL") or os.getenv("GEMINI_BASE_URL") or DEFAULT_GEMINI_BASE_URL).strip()
    entities_dir = _resolve_project_path(root, os.getenv("MAF_ENTITIES_DIR"), "entities")
    repo_root = _resolve_project_path(root, os.getenv("MAF_REPO_ROOT"), ".")
    checkpoint_dir = _resolve_project_path(root, os.getenv("MAF_CHECKPOINT_DIR"), r"state\maf-checkpoints")

    if not repo_root.exists():
        raise ValueError(f"Configured repo root does not exist: {repo_root}")

    anthropic_api_key = (os.getenv("ANTHROPIC_API_KEY") or "").strip() or None
    anthropic_model = (os.getenv("ANTHROPIC_MODEL") or "").strip() or None

    return Settings(
        project_root=root,
        entities_dir=entities_dir,
        repo_root=repo_root,
        checkpoint_dir=checkpoint_dir,
        model=model,
        route_lane=(os.getenv("MAF_ROUTE_LANE") or "auto").strip() or "auto",
        requested_provider=(os.getenv("MAF_REQUESTED_PROVIDER") or "").strip() or None,
        requested_model=(os.getenv("MAF_REQUESTED_MODEL") or "").strip() or None,
        base_url=base_url,
        api_key=api_key,
        fallback_chain=_split_fallback_chain(
            os.getenv("MAF_FALLBACK_CHAIN"),
            anthropic_model=anthropic_model,
            anthropic_api_key=anthropic_api_key,
            ollama_base_url=ollama_base_url,
            ollama_model=ollama_model,
        ),
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
        anthropic_api_key=anthropic_api_key,
        anthropic_model=anthropic_model or DEFAULT_ANTHROPIC_MODEL,
        gemini_cli_command=(os.getenv("GEMINI_CLI_COMMAND") or "gemini.cmd").strip(),
        gemini_cli_model=(os.getenv("GEMINI_CLI_MODEL") or "").strip() or None,
        claude_cli_command=(os.getenv("CLAUDE_CLI_COMMAND") or "claude").strip(),
        claude_cli_model=(os.getenv("CLAUDE_CLI_MODEL") or "").strip() or None,
        claude_code_git_bash_path=(os.getenv("CLAUDE_CODE_GIT_BASH_PATH") or "").strip() or None,
        codex_cli_command=(os.getenv("CODEX_CLI_COMMAND") or "codex.cmd").strip(),
        codex_cli_model=(os.getenv("CODEX_CLI_MODEL") or "").strip() or None,
        model_candidates=_split_candidates(os.getenv("MAF_MODEL_CANDIDATES")),
    )
