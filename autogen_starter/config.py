from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_PROVIDERS = (
    "ollama",
    "openai",
    "gemini",
    "anthropic",
    "azure-openai",
    "codex-cli",
    "gemini-cli",
    "claude-cli",
)


def load_local_env(env_path: Path | None = None) -> None:
    path = env_path or Path(".env")
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    provider: str
    approval_word: str
    state_dir: Path
    state_file_name: str
    repo_scan_root: Path
    ollama_model: str
    ollama_host: str | None
    openai_model: str
    openai_api_key: str | None
    openai_base_url: str | None
    gemini_model: str
    gemini_api_key: str | None
    gemini_base_url: str
    anthropic_model: str
    anthropic_api_key: str | None
    azure_openai_model: str
    azure_openai_deployment: str | None
    azure_openai_endpoint: str | None
    azure_openai_api_version: str
    azure_openai_api_key: str | None
    codex_cli_command: str
    codex_cli_model: str | None
    gemini_cli_command: str
    claude_cli_command: str
    claude_cli_model: str | None
    claude_code_git_bash_path: str | None

    @property
    def state_path(self) -> Path:
        return self.state_dir / self.state_file_name


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if value is None:
        return None
    value = value.strip()
    return value or None


def load_settings() -> Settings:
    load_local_env()

    provider = (_env("AUTOGEN_PROVIDER", "ollama") or "ollama").lower()
    if provider not in SUPPORTED_PROVIDERS:
        valid = ", ".join(SUPPORTED_PROVIDERS)
        raise ValueError(
            f"Unsupported AUTOGEN_PROVIDER '{provider}'. Expected one of: {valid}."
        )

    state_dir = Path(_env("AUTOGEN_STATE_DIR", "state") or "state")
    state_file_name = _env("AUTOGEN_STATE_FILE", "team_state.json") or "team_state.json"

    return Settings(
        provider=provider,
        approval_word=_env("AUTOGEN_APPROVAL_WORD", "APPROVE") or "APPROVE",
        state_dir=state_dir,
        state_file_name=state_file_name,
        repo_scan_root=Path(
            _env("AUTOGEN_REPO_SCAN_ROOT", str(Path.cwd().parent))
            or str(Path.cwd().parent)
        ),
        ollama_model=_env("OLLAMA_MODEL", "phi3:mini") or "phi3:mini",
        ollama_host=_env("OLLAMA_HOST"),
        openai_model=_env("OPENAI_MODEL", "gpt-4.1-mini") or "gpt-4.1-mini",
        openai_api_key=_env("OPENAI_API_KEY"),
        openai_base_url=_env("OPENAI_BASE_URL"),
        gemini_model=_env("GEMINI_MODEL", "gemini-2.5-flash") or "gemini-2.5-flash",
        gemini_api_key=_env("GEMINI_API_KEY"),
        gemini_base_url=_env(
            "GEMINI_BASE_URL",
            "https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        or "https://generativelanguage.googleapis.com/v1beta/openai/",
        anthropic_model=_env("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
        or "claude-sonnet-4-20250514",
        anthropic_api_key=_env("ANTHROPIC_API_KEY"),
        azure_openai_model=_env("AZURE_OPENAI_MODEL", "gpt-4o") or "gpt-4o",
        azure_openai_deployment=_env("AZURE_OPENAI_DEPLOYMENT"),
        azure_openai_endpoint=_env("AZURE_OPENAI_ENDPOINT"),
        azure_openai_api_version=_env("AZURE_OPENAI_API_VERSION", "2024-06-01")
        or "2024-06-01",
        azure_openai_api_key=_env("AZURE_OPENAI_API_KEY"),
        codex_cli_command=_env("CODEX_CLI_COMMAND", "codex.cmd") or "codex.cmd",
        codex_cli_model=_env("CODEX_CLI_MODEL"),
        gemini_cli_command=_env("GEMINI_CLI_COMMAND", "gemini.cmd") or "gemini.cmd",
        claude_cli_command=_env("CLAUDE_CLI_COMMAND", "claude") or "claude",
        claude_cli_model=_env("CLAUDE_CLI_MODEL"),
        claude_code_git_bash_path=_env("CLAUDE_CODE_GIT_BASH_PATH"),
    )
