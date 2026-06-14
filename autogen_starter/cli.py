from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

import uvicorn
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console

from autogen_starter.config import Settings, load_settings
from autogen_starter.providers import (
    ProviderConfigError,
    collect_provider_statuses,
    create_model_client,
)
from maf_starter.execution_profile import CLOUD_SAFE_PROFILE, LOCAL_PROFILE
from maf_starter.worker_boundary import WorkerProfile

DEFAULT_CHAT_SYSTEM_MESSAGE = (
    "You are a collaborative assistant. Work with the human in short iterations. "
    "Ask concise follow-up questions only when they are necessary."
)

DEFAULT_STEP_SYSTEM_MESSAGE = (
    "You are a collaborative assistant. Produce one useful step at a time, then stop. "
    "If you need clarification, ask for it directly and briefly."
)


def _profile_choices() -> tuple[str, ...]:
    return tuple(p.value for p in WorkerProfile)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AutoGen AgentChat starter.")
    parser.add_argument(
        "--profile",
        choices=_profile_choices(),
        default=WorkerProfile.LOCAL.value,
        help=(
            "Execution profile: 'local' (default) allows all providers including "
            "subprocess-backed CLI tools; 'cloud-safe' restricts to API-only providers "
            "and rejects subprocess execution."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("providers", help="Show provider readiness.")

    chat_parser = subparsers.add_parser(
        "chat", help="Run blocking human-in-the-loop chat."
    )
    chat_parser.add_argument(
        "--task", required=True, help="Initial task to send to the team."
    )
    chat_parser.add_argument(
        "--system-message",
        default=DEFAULT_CHAT_SYSTEM_MESSAGE,
        help="System message for the assistant.",
    )

    step_parser = subparsers.add_parser(
        "step", help="Run one resumable assistant turn and save state."
    )
    step_parser.add_argument(
        "--task", required=True, help="New task or human feedback for the next turn."
    )
    step_parser.add_argument(
        "--system-message",
        default=DEFAULT_STEP_SYSTEM_MESSAGE,
        help="System message for the assistant.",
    )

    dashboard_parser = subparsers.add_parser(
        "dashboard", help="Run the local HITL dashboard."
    )
    dashboard_parser.add_argument(
        "--host", default="127.0.0.1", help="Host interface for the dashboard server."
    )
    dashboard_parser.add_argument(
        "--port", type=int, default=8000, help="Port for the dashboard server."
    )

    subparsers.add_parser("reset-state", help="Delete the saved resumable team state.")
    return parser


async def run_blocking_chat(settings: Settings, task: str, system_message: str) -> None:
    model_client = create_model_client(settings)
    try:
        assistant = AssistantAgent(
            "assistant",
            model_client=model_client,
            system_message=system_message,
        )
        user_proxy = UserProxyAgent("user_proxy")
        termination = TextMentionTermination(settings.approval_word)
        team = RoundRobinGroupChat(
            [assistant, user_proxy], termination_condition=termination
        )
        await Console(team.run_stream(task=task), output_stats=True)
    finally:
        await model_client.close()


async def run_resumable_step(
    settings: Settings, task: str, system_message: str
) -> None:
    model_client = create_model_client(settings)
    try:
        assistant = AssistantAgent(
            "assistant",
            model_client=model_client,
            system_message=system_message,
        )
        team = RoundRobinGroupChat([assistant], max_turns=1)

        if settings.state_path.exists():
            state = json.loads(settings.state_path.read_text(encoding="utf-8"))
            await team.load_state(state)

        await Console(team.run_stream(task=task), output_stats=True)

        settings.state_dir.mkdir(parents=True, exist_ok=True)
        state = await team.save_state()
        settings.state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        print(f"Saved resumable state to {settings.state_path}")
    finally:
        await model_client.close()


def reset_state(state_path: Path) -> None:
    if state_path.exists():
        state_path.unlink()
        print(f"Deleted {state_path}")
    else:
        print(f"No state file found at {state_path}")


def print_provider_statuses(settings: Settings) -> None:
    print(f"Active provider: {settings.provider}")
    for status in collect_provider_statuses(settings):
        readiness = "READY" if status.ready else "NOT READY"
        print(f"[{readiness}] {status.name}: {status.detail}")


def run_dashboard(host: str, port: int) -> None:
    uvicorn.run("autogen_dashboard.app:app", host=host, port=port, reload=False)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    # Resolve execution profile from --profile flag (default: local).
    profile = CLOUD_SAFE_PROFILE if args.profile == WorkerProfile.CLOUD_SAFE.value else LOCAL_PROFILE

    try:
        settings = load_settings()
        if profile.profile != WorkerProfile.LOCAL:
            print(f"[profile] Active execution profile: {profile.profile.value} — subprocess providers are disabled.")
        if args.command == "providers":
            print_provider_statuses(settings)
            return 0
        if args.command == "chat":
            asyncio.run(run_blocking_chat(settings, args.task, args.system_message))
            return 0
        if args.command == "step":
            asyncio.run(run_resumable_step(settings, args.task, args.system_message))
            return 0
        if args.command == "dashboard":
            run_dashboard(args.host, args.port)
            return 0
        if args.command == "reset-state":
            reset_state(settings.state_path)
            return 0
        parser.error(f"Unknown command: {args.command}")
    except ProviderConfigError as exc:
        print(f"Provider configuration error: {exc}")
        return 2
    except ValueError as exc:
        print(f"Configuration error: {exc}")
        return 2

    return 0
