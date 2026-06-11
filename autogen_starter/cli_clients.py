from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from json import JSONDecoder
from typing import Any, AsyncGenerator, Mapping, Sequence

from autogen_core import CancellationToken
from autogen_core.models import (
    ChatCompletionClient,
    CreateResult,
    LLMMessage,
    ModelInfo,
    RequestUsage,
)

_MODEL_INFO: ModelInfo = {
    "vision": False,
    "function_calling": False,
    "json_output": True,
    "structured_output": False,
    "family": "cli-subprocess",
    "multiple_system_messages": True,
}


@dataclass(frozen=True)
class SubprocessResult:
    content: str
    usage: RequestUsage


class SubprocessCliChatCompletionClient(ChatCompletionClient):
    def __init__(
        self,
        *,
        name: str,
        command: Sequence[str],
        parser,
        env: Mapping[str, str] | None = None,
        working_directory: str | None = None,
        timeout_seconds: int = 180,
    ) -> None:
        self._name = name
        self._command = list(command)
        self._parser = parser
        self._env = dict(env or {})
        self._working_directory = working_directory
        self._timeout_seconds = timeout_seconds
        self._actual_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)
        self._total_usage = RequestUsage(prompt_tokens=0, completion_tokens=0)

    @property
    def model_info(self) -> ModelInfo:
        return _MODEL_INFO

    def capabilities(self) -> ModelInfo:  # type: ignore[override]
        return self.model_info

    async def create(
        self,
        messages: Sequence[LLMMessage],
        *,
        tools: Sequence[Any] = (),
        tool_choice: Any = "auto",
        json_output: Any = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: CancellationToken | None = None,
    ) -> CreateResult:
        if tools:
            raise NotImplementedError(
                f"{self._name} does not support AutoGen tool-calling in this starter."
            )
        if tool_choice not in ("auto", "none"):
            raise NotImplementedError(
                f"{self._name} does not support tool_choice={tool_choice!r}."
            )
        if json_output not in (None, False):
            raise NotImplementedError(
                f"{self._name} does not support AutoGen JSON output mode in this starter."
            )
        if extra_create_args:
            raise NotImplementedError(
                f"{self._name} does not support extra_create_args in this starter."
            )
        if cancellation_token and cancellation_token.is_cancelled():
            raise RuntimeError(f"{self._name} request was cancelled before launch.")

        prompt = _messages_to_prompt(messages)
        completed = await asyncio.to_thread(self._run_command, prompt)
        parsed = self._parser(completed.stdout, completed.stderr)
        self._actual_usage = parsed.usage
        self._total_usage = RequestUsage(
            prompt_tokens=self._total_usage.prompt_tokens + parsed.usage.prompt_tokens,
            completion_tokens=self._total_usage.completion_tokens
            + parsed.usage.completion_tokens,
        )
        return CreateResult(
            finish_reason="stop",
            content=parsed.content,
            usage=parsed.usage,
            cached=False,
        )

    async def create_stream(
        self,
        messages: Sequence[LLMMessage],
        *,
        tools: Sequence[Any] = (),
        tool_choice: Any = "auto",
        json_output: Any = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: CancellationToken | None = None,
    ) -> AsyncGenerator[str | CreateResult, None]:
        result = await self.create(
            messages,
            tools=tools,
            tool_choice=tool_choice,
            json_output=json_output,
            extra_create_args=extra_create_args,
            cancellation_token=cancellation_token,
        )
        yield result

    async def close(self) -> None:
        return None

    def actual_usage(self) -> RequestUsage:
        return self._actual_usage

    def total_usage(self) -> RequestUsage:
        return self._total_usage

    def count_tokens(
        self, messages: Sequence[LLMMessage], *, tools: Sequence[Any] = ()
    ) -> int:
        prompt = _messages_to_prompt(messages)
        return max(1, len(prompt) // 4)

    def remaining_tokens(
        self, messages: Sequence[LLMMessage], *, tools: Sequence[Any] = ()
    ) -> int:
        return 100_000

    def _run_command(self, prompt: str) -> subprocess.CompletedProcess[str]:
        resolved = shutil.which(self._command[0]) or self._command[0]
        if not shutil.which(self._command[0]) and not os.path.exists(resolved):
            raise RuntimeError(
                f"Command not found for provider {self._name!r}: {self._command[0]}"
            )

        env = os.environ.copy()
        env.update(self._env)
        command_args = [resolved, *self._command[1:]]
        if "{prompt}" in command_args:
            command_args = [
                prompt if value == "{prompt}" else value for value in command_args
            ]
        else:
            command_args.append(prompt)

        completed = subprocess.run(
            command_args,
            cwd=self._working_directory,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=self._timeout_seconds,
            check=False,
            env=env,
        )
        if completed.returncode != 0:
            stderr = completed.stderr.strip()
            stdout = completed.stdout.strip()
            detail = stderr or stdout or f"exit code {completed.returncode}"
            raise RuntimeError(f"{self._name} failed: {detail}")
        return completed


def build_codex_cli_client(
    command: str,
    model: str | None = None,
    working_directory: str | None = None,
) -> SubprocessCliChatCompletionClient:
    base_command = [command, "exec", "--skip-git-repo-check", "--json"]
    if model:
        base_command.extend(["--model", model])
    return SubprocessCliChatCompletionClient(
        name="codex-cli",
        command=base_command,
        parser=_parse_codex_jsonl,
        working_directory=working_directory,
    )


def build_gemini_cli_client(
    command: str,
    working_directory: str | None = None,
) -> SubprocessCliChatCompletionClient:
    return build_gemini_cli_client_with_model(
        command, working_directory=working_directory
    )


def build_gemini_cli_client_with_model(
    command: str,
    model: str | None = None,
    working_directory: str | None = None,
) -> SubprocessCliChatCompletionClient:
    base_command = [command, "-p", "{prompt}", "--approval-mode", "plan"]
    if model:
        base_command.extend(["--model", model])
    return SubprocessCliChatCompletionClient(
        name="gemini-cli",
        command=base_command,
        parser=_parse_plain_text,
        working_directory=working_directory,
    )


def build_claude_cli_client(
    command: str,
    model: str | None = None,
    git_bash_path: str | None = None,
    working_directory: str | None = None,
) -> SubprocessCliChatCompletionClient:
    base_command = [command, "-p"]
    if model:
        base_command.extend(["--model", model])

    extra_env: dict[str, str] = {}
    if git_bash_path:
        extra_env["CLAUDE_CODE_GIT_BASH_PATH"] = git_bash_path

    return SubprocessCliChatCompletionClient(
        name="claude-cli",
        command=base_command,
        parser=_parse_claude_text,
        env=extra_env,
        working_directory=working_directory,
    )


def _parse_codex_jsonl(stdout: str, stderr: str) -> SubprocessResult:
    response_text = None
    prompt_tokens = 0
    completion_tokens = 0

    for line in stdout.splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        event = json.loads(line)
        if event.get("type") == "item.completed":
            item = event.get("item", {})
            if item.get("type") == "agent_message":
                response_text = item.get("text", "")
        elif event.get("type") == "turn.completed":
            usage = event.get("usage", {})
            prompt_tokens = usage.get("input_tokens", 0)
            completion_tokens = usage.get("output_tokens", 0)

    if response_text is None:
        detail = (
            stderr.strip()
            or stdout.strip()
            or "Codex JSON output did not contain an agent message."
        )
        raise RuntimeError(detail)

    return SubprocessResult(
        content=response_text.strip(),
        usage=RequestUsage(
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
        ),
    )


def _parse_gemini_json(stdout: str, stderr: str) -> SubprocessResult:
    payload_text = stdout.strip()
    if not payload_text:
        raise RuntimeError(stderr.strip() or "Gemini returned empty output.")

    payload, _ = JSONDecoder().raw_decode(payload_text)
    response = payload.get("response", "")
    stats = payload.get("stats", {})
    prompt_tokens = 0
    completion_tokens = 0

    for model_stats in stats.get("models", {}).values():
        tokens = model_stats.get("tokens", {})
        prompt_tokens += int(tokens.get("prompt", 0))
        completion_tokens += int(tokens.get("candidates", 0))

    return SubprocessResult(
        content=str(response).strip(),
        usage=RequestUsage(
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
        ),
    )


def _parse_claude_text(stdout: str, stderr: str) -> SubprocessResult:
    return _parse_plain_text(stdout, stderr)


def _parse_plain_text(stdout: str, stderr: str) -> SubprocessResult:
    response = stdout.strip()
    if not response:
        raise RuntimeError(stderr.strip() or "CLI provider returned empty output.")
    return SubprocessResult(
        content=response,
        usage=RequestUsage(
            prompt_tokens=0, completion_tokens=max(1, len(response) // 4)
        ),
    )


def _messages_to_prompt(messages: Sequence[LLMMessage]) -> str:
    rendered: list[str] = []
    for message in messages:
        role = type(message).__name__.replace("Message", "").upper()
        content = getattr(message, "content", "")
        normalized = (
            _normalize_content(content).replace("\r", " ").replace("\n", " ").strip()
        )
        rendered.append(f"{role}: {normalized}")
    rendered.append("ASSISTANT:")
    return " | ".join(rendered)


def _normalize_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                else:
                    parts.append(json.dumps(item, ensure_ascii=True))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)
