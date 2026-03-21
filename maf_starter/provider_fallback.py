from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
from collections.abc import AsyncIterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent_framework import ChatContext, ChatResponse, ChatResponseUpdate, Content, Message, ResponseStream, chat_middleware
from agent_framework.openai import OpenAIChatClient

try:
    from agent_framework_anthropic import AnthropicClient
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    AnthropicClient = None

from maf_starter.config import Settings, activate_run_scope, reset_run_scope
from maf_starter.routing_policy import RoutingPlan, build_routing_plan
from maf_starter.routing_types import ChainStep


FALLBACK_NOTICE = "[Fallback provider used because the earlier model/provider in the chain failed.]\n"
FALLBACK_ERROR_MARKERS = (
    "resource_exhausted",
    "quota",
    "rate limit",
    "429",
    "too many requests",
    "overloaded",
    "capacity",
)


def build_fallback_middleware(settings: Settings, *, primary_provider: str, primary_model: str, routing_mode: str):
    @chat_middleware
    async def fallback_middleware(context: ChatContext, call_next):
        scoped_settings, scope_tokens = _resolve_run_scope(settings, context)
        try:
            route = build_routing_plan(
                scoped_settings,
                routing_mode=routing_mode,
                messages=context.messages,
                primary_provider=primary_provider,
                primary_model=primary_model,
            )
            context.options = _override_model(context.options, route.primary_model)
            try:
                await call_next()
                if context.stream and context.result is not None:
                    context.result = _wrap_stream_with_fallback(
                        settings=scoped_settings,
                        original_stream=context.result,
                        context=context,
                        route=route,
                    )
                elif isinstance(context.result, ChatResponse):
                    context.result = _decorate_primary_response(
                        context.result,
                        route=route,
                        settings=scoped_settings,
                    )
                return
            except Exception as exc:
                if not _is_fallback_worthy_error(exc):
                    raise

                last_error: Exception = exc
                for step in route.fallback_steps:
                    try:
                        context.result = await _execute_chain_step(
                            settings=scoped_settings,
                            step=step,
                            context=context,
                            route=route,
                            prior_error=last_error,
                        )
                        return
                    except Exception as fallback_exc:
                        last_error = fallback_exc
                        continue

                raise last_error
        finally:
            reset_run_scope(scope_tokens)

    return fallback_middleware


def _resolve_run_scope(settings: Settings, context: ChatContext):
    repo_root = context.metadata.get("repo_root") or context.kwargs.pop("repo_root", None)
    checkpoint_dir = context.metadata.get("checkpoint_dir") or context.kwargs.pop("checkpoint_dir", None)
    scoped_settings, tokens = activate_run_scope(
        settings,
        repo_root=repo_root,
        checkpoint_dir=checkpoint_dir,
    )
    context.metadata["repo_root"] = str(scoped_settings.repo_root)
    context.metadata["checkpoint_dir"] = str(scoped_settings.checkpoint_dir)
    return scoped_settings, tokens


def _wrap_stream_with_fallback(
    *,
    settings: Settings,
    original_stream: ResponseStream[ChatResponseUpdate, ChatResponse] | AsyncIterable[ChatResponseUpdate],
    context: ChatContext,
    route: RoutingPlan,
):
    state: dict[str, ChatResponse | None] = {"final_response": None}

    async def _stream():
        yielded_updates = False
        try:
            async for update in original_stream:
                yielded_updates = True
                if isinstance(update, ChatResponseUpdate):
                    update.additional_properties = _merge_route_metadata(
                        update.additional_properties,
                        settings=settings,
                        route=route,
                        active_provider=route.primary_provider,
                        active_model=route.primary_model,
                        fallback_used=False,
                    )
                yield update
            return
        except Exception as exc:
            if yielded_updates or not _is_fallback_worthy_error(exc):
                raise

            last_error: Exception = exc
            for step in route.fallback_steps:
                try:
                    fallback_result = await _execute_chain_step(
                        settings=settings,
                        step=step,
                        context=context,
                        route=route,
                        prior_error=last_error,
                    )
                    if isinstance(fallback_result, ResponseStream):
                        async for update in fallback_result:
                            yield update
                        state["final_response"] = await fallback_result.get_final_response()
                        return
                    if not isinstance(fallback_result, ChatResponse):
                        async for update in fallback_result:
                            yield update
                        return
                    state["final_response"] = fallback_result
                    yield ChatResponseUpdate(
                        role="assistant",
                        contents=[Content.from_text(fallback_result.text)],
                        model_id=getattr(fallback_result, "model_id", None),
                        created_at=getattr(fallback_result, "created_at", None),
                        additional_properties=getattr(fallback_result, "additional_properties", None),
                    )
                    return
                except Exception as fallback_exc:
                    last_error = fallback_exc
            raise last_error

        if isinstance(original_stream, ResponseStream):
            state["final_response"] = await original_stream.get_final_response()

    async def _finalize(updates: list[ChatResponseUpdate]) -> ChatResponse:
        if state["final_response"] is not None:
            return state["final_response"]
        return _response_from_updates(updates)

    return ResponseStream(_stream(), finalizer=_finalize)


async def _execute_chain_step(
    *,
    settings: Settings,
    step: ChainStep,
    context: ChatContext,
    route: RoutingPlan,
    prior_error: Exception,
):
    if step.provider == "gemini":
        client = OpenAIChatClient(
            model_id=step.model or settings.model,
            api_key=settings.api_key,
            base_url=settings.base_url,
        )
        response = client.get_response(
            context.messages,
            stream=context.stream,
            options=_override_model(context.options, step.model),
            function_invocation_kwargs=context.function_invocation_kwargs,
            **(context.kwargs or {}),
        )
        if not context.stream:
            response = await response
        return _decorate_result(
            response,
            settings=settings,
            step=step,
            route=route,
            prior_error=prior_error,
            add_notice=False,
        )

    if step.provider == "anthropic":
        if not settings.anthropic_api_key:
            raise RuntimeError("Anthropic API key is not configured.")
        if AnthropicClient is None:
            raise RuntimeError("Anthropic support is not installed in this environment.")
        client = AnthropicClient(
            api_key=settings.anthropic_api_key,
            model_id=step.model or settings.anthropic_model,
        )
        response = client.get_response(
            context.messages,
            stream=context.stream,
            options=_override_model(context.options, step.model or settings.anthropic_model),
            function_invocation_kwargs=context.function_invocation_kwargs,
            **(context.kwargs or {}),
        )
        if not context.stream:
            response = await response
        return _decorate_result(
            response,
            settings=settings,
            step=step,
            route=route,
            prior_error=prior_error,
            add_notice=False,
        )

    if step.provider in {"gemini-cli", "claude-cli", "codex-cli"}:
        prompt = _messages_to_prompt(context.messages)
        text = await asyncio.to_thread(
            _run_cli_step,
            settings=settings,
            step=step,
            prompt=prompt,
        )
        response = ChatResponse(
            messages=[Message(role="assistant", text=f"{FALLBACK_NOTICE}{text}")],
            response_id=f"{step.provider}-fallback-{int(datetime.now(timezone.utc).timestamp())}",
            model_id=step.label,
            created_at=datetime.now(timezone.utc),
            additional_properties={
                **_merge_route_metadata(
                    None,
                    settings=settings,
                    route=route,
                    active_provider=step.provider,
                    active_model=step.model or step.label,
                    fallback_used=True,
                    tools_available=False,
                ),
                "primary_error": str(prior_error),
            },
        )
        if context.stream:
            return _stream_from_response(response)
        return response

    raise RuntimeError(f"Unsupported fallback provider: {step.provider}")


def _override_model(options: dict[str, Any] | Any, model: str | None) -> dict[str, Any]:
    merged = dict(options or {})
    if model:
        merged["model_id"] = model
    return merged


def _decorate_result(
    result,
    *,
    settings: Settings,
    step: ChainStep,
    route: RoutingPlan,
    prior_error: Exception,
    add_notice: bool,
):
    metadata = _merge_route_metadata(
        None,
        settings=settings,
        route=route,
        active_provider=step.provider,
        active_model=step.model or step.label,
        fallback_used=True,
    ) | {"primary_error": str(prior_error)}
    if isinstance(result, ChatResponse):
        result.additional_properties = dict(result.additional_properties or {}) | metadata
        if add_notice and result.messages:
            first = result.messages[0]
            first.contents.insert(0, Content.from_text(FALLBACK_NOTICE))
        return result
    if isinstance(result, ResponseStream):
        return (
            result.with_transform_hook(
                lambda update: _decorate_stream_update(update, metadata=metadata),
            ).with_result_hook(
                lambda response: _decorate_stream_response(response, metadata=metadata, add_notice=add_notice),
            )
        )
    return result


def _decorate_primary_response(result: ChatResponse, *, route: RoutingPlan, settings: Settings) -> ChatResponse:
    result.additional_properties = _merge_route_metadata(
        result.additional_properties,
        settings=settings,
        route=route,
        active_provider=route.primary_provider,
        active_model=route.primary_model,
        fallback_used=False,
    )
    return result


def _stream_from_response(response: ChatResponse) -> ResponseStream[ChatResponseUpdate, ChatResponse]:
    async def _updates():
        yield ChatResponseUpdate(
            role="assistant",
            contents=[Content.from_text(response.text)],
            model_id=response.model_id,
            created_at=response.created_at,
            additional_properties=response.additional_properties,
        )

    return ResponseStream(_updates(), finalizer=lambda updates: response)


def _merge_route_metadata(
    existing: dict[str, Any] | None,
    *,
    settings: Settings,
    route: RoutingPlan,
    active_provider: str,
    active_model: str,
    fallback_used: bool,
    tools_available: bool = True,
) -> dict[str, Any]:
    metadata = dict(existing or {})
    metadata.update(
        {
            "routing_mode": route.mode,
            "route_tier": route.tier,
            "route_reason": route.rationale,
            "active_provider": active_provider,
            "active_model": active_model,
            "primary_provider": route.primary_provider,
            "primary_model": route.primary_model,
            "fallback_used": fallback_used,
            "tools_available": tools_available,
            "workspace_root": str(settings.repo_root),
            "checkpoint_dir": str(settings.checkpoint_dir),
        }
    )
    if fallback_used:
        metadata["fallback_provider"] = active_provider
        metadata["fallback_model"] = active_model
    return metadata


def _decorate_stream_update(
    update: ChatResponseUpdate,
    *,
    metadata: dict[str, Any],
) -> ChatResponseUpdate:
    update.additional_properties = dict(update.additional_properties or {}) | metadata
    return update


def _decorate_stream_response(
    response: ChatResponse,
    *,
    metadata: dict[str, Any],
    add_notice: bool,
) -> ChatResponse:
    response.additional_properties = dict(response.additional_properties or {}) | metadata
    if add_notice and response.messages:
        response.messages[0].contents.insert(0, Content.from_text(FALLBACK_NOTICE))
    return response


def _response_from_updates(updates: list[ChatResponseUpdate]) -> ChatResponse:
    if not updates:
        return ChatResponse(messages=[Message(role="assistant", text="")])
    last = updates[-1]
    return ChatResponse(
        messages=[Message(role=last.role or "assistant", contents=list(last.contents or []))],
        response_id=last.response_id,
        conversation_id=last.conversation_id,
        model_id=last.model_id,
        created_at=last.created_at,
        finish_reason=last.finish_reason,
        continuation_token=last.continuation_token,
        additional_properties=last.additional_properties,
        raw_representation=last.raw_representation,
    )


def _is_fallback_worthy_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in FALLBACK_ERROR_MARKERS)


def _run_cli_step(*, settings: Settings, step: ChainStep, prompt: str) -> str:
    if step.provider == "gemini-cli":
        command = settings.gemini_cli_command
        model = step.model or settings.gemini_cli_model
        env = None
        args = [command, "-p", prompt, "--approval-mode", "plan"]
        if model:
            args.extend(["--model", model])
        return _run_subprocess("gemini-cli", args, settings.repo_root, env)

    if step.provider == "claude-cli":
        command = settings.claude_cli_command
        model = step.model or settings.claude_cli_model
        env = {}
        if settings.claude_code_git_bash_path:
            env["CLAUDE_CODE_GIT_BASH_PATH"] = settings.claude_code_git_bash_path
        args = [command, "-p", prompt]
        if model:
            args.extend(["--model", model])
        return _run_subprocess("claude-cli", args, settings.repo_root, env)

    if step.provider == "codex-cli":
        command = settings.codex_cli_command
        model = step.model or settings.codex_cli_model
        args = [command, "exec", "--skip-git-repo-check", prompt]
        if model:
            args[3:3] = ["--model", model]
        return _run_subprocess("codex-cli", args, settings.repo_root, None)

    raise RuntimeError(f"Unsupported CLI fallback provider: {step.provider}")


def _run_subprocess(
    provider_name: str,
    args: list[str],
    working_directory: Path,
    env: dict[str, str] | None,
) -> str:
    resolved = shutil.which(args[0]) or args[0]
    if not shutil.which(args[0]) and not os.path.exists(resolved):
        raise RuntimeError(f"Command not found for {provider_name}: {args[0]}")

    completed = subprocess.run(
        [resolved, *args[1:]],
        cwd=working_directory,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=240,
        check=False,
        env={**os.environ, **(env or {})},
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        raise RuntimeError(f"{provider_name} failed: {detail}")

    output = completed.stdout.strip()
    if not output:
        raise RuntimeError(f"{provider_name} returned empty output")

    if provider_name == "codex-cli":
        try:
            last_message = ""
            for line in output.splitlines():
                if not line.startswith("{"):
                    continue
                event = json.loads(line)
                if event.get("type") == "item.completed":
                    item = event.get("item", {})
                    if item.get("type") == "agent_message":
                        last_message = item.get("text", "")
            if last_message:
                return last_message.strip()
        except Exception:
            pass

    return output


def _messages_to_prompt(messages: list[Message] | tuple[Message, ...]) -> str:
    rendered: list[str] = []
    for message in messages:
        rendered.append(f"{str(message.role).upper()}: {_message_text(message)}")
    rendered.append("ASSISTANT:")
    return "\n\n".join(rendered)


def _message_text(message: Message) -> str:
    parts: list[str] = []
    for content in message.contents:
        if isinstance(content, str):
            parts.append(content)
        elif getattr(content, "type", None) == "text":
            parts.append(str(content.text))
        elif getattr(content, "type", None) == "function_call":
            parts.append(f"[function call: {getattr(content, 'name', 'unknown')}]")
        elif getattr(content, "type", None) == "function_result":
            parts.append(f"[function result: {getattr(content, 'result', '')}]")
        else:
            parts.append(str(content))
    return "\n".join(part for part in parts if part).strip()
