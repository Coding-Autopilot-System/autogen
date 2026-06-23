from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

from maf_starter.config import Settings, load_settings
from maf_starter.provider_fallback import build_fallback_middleware
from maf_starter.tools import build_repo_tools


def create_client(settings: Settings, *, routing_mode: str = "auto"):
    if settings.ollama_base_url:
        return OpenAIChatClient(
            model_id=settings.ollama_model,
            api_key="ollama",
            base_url=settings.ollama_base_url,
        )
    return OpenAIChatClient(
        model_id=settings.model,
        api_key=settings.api_key,
        base_url=settings.base_url,
    )


def build_agent(
    settings: Settings | None = None,
    *,
    agent_name: str = "repo_copilot",
    description: str | None = None,
    role_instructions: str | None = None,
    routing_mode: str = "auto",
) -> Agent:
    current = settings or load_settings()
    instructions = (
        "You are a repo-aware software engineering assistant working in the configured local repository. "
        "Use the repo tools before making specific claims about file paths, contents, or configuration. "
        "Keep answers concise and concrete. When you are acting as a workflow specialist, prefer structured stage "
        "handoffs with `summary`, `artifacts`, `next_action`, `needs_approval`, `needs_input`, `blocked_questions`, "
        "`current_task`, `latest_output_summary`, `handoff_to`, and `handoff_reason`. "
        "Before you present a plan that implies file edits, commands, or other risky actions, call "
        "request_human_approval with a short summary so the human can approve or reject it."
    )
    if role_instructions:
        instructions = f"{instructions} {role_instructions}"
    return Agent(
        create_client(current, routing_mode=routing_mode),
        name=agent_name,
        description=description or "Repo assistant with fallback across API models and CLI providers.",
        instructions=instructions,
        tools=build_repo_tools(current.repo_root),
        default_options={"model_id": current.model},
        middleware=[
            build_fallback_middleware(
                current,
                primary_provider="ollama" if current.ollama_base_url else "gemini",
                primary_model=current.ollama_model if current.ollama_base_url else current.model,
                routing_mode=routing_mode,
            )
        ],
    )


def build_run_scoped_agent(
    settings: Settings,
    *,
    repo_root: str | Path | None = None,
    checkpoint_dir: str | Path | None = None,
    agent_name: str = "repo_copilot",
    description: str | None = None,
    role_instructions: str | None = None,
    routing_mode: str = "auto",
) -> Agent:
    return build_agent(
        settings.with_run_scope(repo_root=repo_root, checkpoint_dir=checkpoint_dir),
        agent_name=agent_name,
        description=description,
        role_instructions=role_instructions,
        routing_mode=routing_mode,
    )


def build_agent_for_model(
    model_id: str,
    *,
    settings: Settings | None = None,
    agent_name: str,
    description: str | None = None,
    role_instructions: str | None = None,
    routing_mode: str = "fixed",
) -> Agent:
    current = settings or load_settings()
    return build_agent(
        replace(current, model=model_id),
        agent_name=agent_name,
        description=description,
        role_instructions=role_instructions,
        routing_mode=routing_mode,
    )
