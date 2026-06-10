from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from autogen_core.models import ModelFamily, ModelInfo

from autogen_starter.cli_clients import (
    build_claude_cli_client,
    build_codex_cli_client,
    build_gemini_cli_client_with_model,
)
from autogen_starter.config import Settings


class ProviderConfigError(RuntimeError):
    """Raised when the selected provider is not configured correctly."""


_DEFAULT_GEMINI_MODEL_INFO: ModelInfo = {
    "vision": True,
    "function_calling": True,
    "json_output": True,
    "structured_output": True,
    "family": ModelFamily.UNKNOWN,
    "multiple_system_messages": True,
}


@dataclass(frozen=True)
class ProviderStatus:
    name: str
    ready: bool
    detail: str


def collect_provider_statuses(settings: Settings) -> list[ProviderStatus]:
    return [
        _ollama_status(settings),
        _openai_status(settings),
        _gemini_status(settings),
        _anthropic_status(settings),
        _azure_openai_status(settings),
        _codex_cli_status(settings),
        _gemini_cli_status(settings),
        _claude_cli_status(settings),
    ]


def create_model_client(
    settings: Settings,
    model_override: str | None = None,
    working_directory: str | None = None,
):
    provider = settings.provider
    model_override = _normalize_model_override(model_override)

    if provider == "ollama":
        from autogen_ext.models.ollama import OllamaChatCompletionClient

        kwargs: dict[str, object] = {"model": model_override or settings.ollama_model}
        if settings.ollama_host:
            kwargs["host"] = settings.ollama_host
        return OllamaChatCompletionClient(**kwargs)

    if provider == "openai":
        raise ProviderConfigError("Provider 'openai' is disabled by local policy.")

    if provider == "gemini":
        from autogen_ext.models.openai import OpenAIChatCompletionClient

        _require(
            settings.gemini_api_key, "GEMINI_API_KEY is required for provider 'gemini'."
        )
        model_name = model_override or settings.gemini_model
        return OpenAIChatCompletionClient(
            model=model_name,
            api_key=settings.gemini_api_key,
            base_url=settings.gemini_base_url,
            model_info=_gemini_model_info(model_name),
        )

    if provider == "anthropic":
        try:
            from autogen_ext.models.anthropic import AnthropicChatCompletionClient
        except ModuleNotFoundError as exc:
            raise ProviderConfigError(
                "Anthropic support is not installed. Install requirements.txt so "
                "'autogen-ext[anthropic]' is available."
            ) from exc

        _require(
            settings.anthropic_api_key,
            "ANTHROPIC_API_KEY is required for provider 'anthropic'.",
        )
        return AnthropicChatCompletionClient(
            model=model_override or settings.anthropic_model,
            api_key=settings.anthropic_api_key,
        )

    if provider == "azure-openai":
        from autogen_ext.models.openai import AzureOpenAIChatCompletionClient

        _require(
            settings.azure_openai_deployment,
            "AZURE_OPENAI_DEPLOYMENT is required for provider 'azure-openai'.",
        )
        _require(
            settings.azure_openai_endpoint,
            "AZURE_OPENAI_ENDPOINT is required for provider 'azure-openai'.",
        )
        _require(
            settings.azure_openai_api_key,
            "AZURE_OPENAI_API_KEY is required for provider 'azure-openai' in this starter.",
        )
        return AzureOpenAIChatCompletionClient(
            model=model_override or settings.azure_openai_model,
            azure_deployment=settings.azure_openai_deployment,
            azure_endpoint=settings.azure_openai_endpoint,
            api_version=settings.azure_openai_api_version,
            api_key=settings.azure_openai_api_key,
        )

    if provider == "codex-cli":
        return build_codex_cli_client(
            settings.codex_cli_command,
            model_override or settings.codex_cli_model,
            working_directory,
        )

    if provider == "gemini-cli":
        return build_gemini_cli_client_with_model(
            settings.gemini_cli_command,
            model_override,
            working_directory,
        )

    if provider == "claude-cli":
        return build_claude_cli_client(
            settings.claude_cli_command,
            model_override or settings.claude_cli_model,
            settings.claude_code_git_bash_path,
            working_directory,
        )

    raise ProviderConfigError(f"Unsupported provider '{provider}'.")


def _require(value: str | None, message: str) -> None:
    if not value:
        raise ProviderConfigError(message)


def _normalize_model_override(model_override: str | None) -> str | None:
    if model_override is None:
        return None
    value = model_override.strip()
    return value or None


def _gemini_model_info(model_name: str) -> ModelInfo:
    normalized = model_name.strip().lower()
    family = ModelFamily.UNKNOWN

    if normalized.startswith("gemini-2.5-pro"):
        family = ModelFamily.GEMINI_2_5_PRO
    elif normalized.startswith("gemini-2.5-flash"):
        family = ModelFamily.GEMINI_2_5_FLASH
    elif normalized.startswith("gemini-2.0-flash"):
        family = ModelFamily.GEMINI_2_0_FLASH
    elif normalized.startswith("gemini-1.5-pro"):
        family = ModelFamily.GEMINI_1_5_PRO
    elif normalized.startswith("gemini-1.5-flash"):
        family = ModelFamily.GEMINI_1_5_FLASH

    return {
        **_DEFAULT_GEMINI_MODEL_INFO,
        "family": family,
    }


def _ollama_status(settings: Settings) -> ProviderStatus:
    if shutil.which("ollama") is None:
        return ProviderStatus("ollama", False, "Ollama CLI not found.")

    try:
        completed = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except OSError as exc:
        return ProviderStatus("ollama", False, f"Ollama probe failed: {exc}")

    if completed.returncode != 0:
        return ProviderStatus(
            "ollama", False, "Ollama is installed but did not return model list."
        )

    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if len(lines) <= 1:
        return ProviderStatus(
            "ollama", True, "Ollama reachable, but no local models were listed."
        )

    model_names = []
    for line in lines[1:]:
        model_names.append(line.split()[0])

    detail = f"Local models detected: {', '.join(model_names[:5])}"
    if settings.ollama_model not in model_names:
        detail += f". Current OLLAMA_MODEL is '{settings.ollama_model}'."
    return ProviderStatus("ollama", True, detail)


def _openai_status(settings: Settings) -> ProviderStatus:
    return ProviderStatus(
        "openai",
        False,
        "Disabled by local policy. OpenAI API is not used in this repo.",
    )


def _gemini_status(settings: Settings) -> ProviderStatus:
    if settings.gemini_api_key:
        return ProviderStatus(
            "gemini",
            True,
            f"Configured for model '{settings.gemini_model}' via OpenAI-compatible endpoint.",
        )
    return ProviderStatus(
        "gemini",
        False,
        "Missing GEMINI_API_KEY. A Google account or Gemini app login is not the same as API access.",
    )


def _anthropic_status(settings: Settings) -> ProviderStatus:
    try:
        __import__("autogen_ext.models.anthropic")
        anthropic_installed = True
    except ModuleNotFoundError:
        anthropic_installed = False

    if not anthropic_installed:
        return ProviderStatus(
            "anthropic",
            False,
            "Anthropic extra is not installed yet. Install requirements.txt first.",
        )
    if settings.anthropic_api_key:
        return ProviderStatus(
            "anthropic", True, f"Configured for model '{settings.anthropic_model}'."
        )
    return ProviderStatus(
        "anthropic",
        False,
        "Missing ANTHROPIC_API_KEY. Claude app login or company seat alone is not enough for AutoGen.",
    )


def _azure_openai_status(settings: Settings) -> ProviderStatus:
    missing = [
        name
        for name, value in (
            ("AZURE_OPENAI_DEPLOYMENT", settings.azure_openai_deployment),
            ("AZURE_OPENAI_ENDPOINT", settings.azure_openai_endpoint),
            ("AZURE_OPENAI_API_KEY", settings.azure_openai_api_key),
        )
        if not value
    ]
    if missing:
        return ProviderStatus(
            "azure-openai",
            False,
            f"Missing {', '.join(missing)}.",
        )
    return ProviderStatus(
        "azure-openai",
        True,
        f"Configured for deployment '{settings.azure_openai_deployment}' and model '{settings.azure_openai_model}'.",
    )


def _codex_cli_status(settings: Settings) -> ProviderStatus:
    if shutil.which(settings.codex_cli_command) is None:
        return ProviderStatus(
            "codex-cli", False, f"Command not found: {settings.codex_cli_command}"
        )
    detail = "Codex CLI detected."
    if settings.codex_cli_model:
        detail += f" Model override: '{settings.codex_cli_model}'."
    else:
        detail += " Using the CLI's configured default model."
    return ProviderStatus("codex-cli", True, detail)


def _gemini_cli_status(settings: Settings) -> ProviderStatus:
    if shutil.which(settings.gemini_cli_command) is None:
        return ProviderStatus(
            "gemini-cli", False, f"Command not found: {settings.gemini_cli_command}"
        )
    return ProviderStatus(
        "gemini-cli",
        True,
        "Gemini CLI detected. It will use the CLI's cached login session.",
    )


def _claude_cli_status(settings: Settings) -> ProviderStatus:
    if shutil.which(settings.claude_cli_command) is None:
        return ProviderStatus(
            "claude-cli", False, f"Command not found: {settings.claude_cli_command}"
        )
    if not settings.claude_code_git_bash_path:
        return ProviderStatus(
            "claude-cli",
            False,
            "Claude CLI detected, but CLAUDE_CODE_GIT_BASH_PATH is not set.",
        )
    if not shutil.which(settings.claude_cli_command):
        return ProviderStatus(
            "claude-cli", False, f"Command not found: {settings.claude_cli_command}"
        )
    return ProviderStatus(
        "claude-cli",
        True,
        "Claude CLI detected. Runtime success still depends on the Git Bash path being valid on this machine.",
    )
