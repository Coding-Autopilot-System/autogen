from __future__ import annotations

import argparse
import asyncio
import sys

from agent_framework import Message

from maf_starter.agent_factory import create_client
from maf_starter.config import load_settings


DEFAULT_SMOKE_MESSAGE = "Reply with exactly: READY"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="maf", description="MAF starter CLI")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("smoke", help="Send a quick probe message to verify the configured provider responds")
    return parser


async def run_smoke() -> None:
    settings = load_settings()
    client = create_client(settings)
    response = await client.get_response([Message(role="user", text=DEFAULT_SMOKE_MESSAGE)])
    provider = "ollama" if settings.ollama_base_url else "gemini"
    model = settings.ollama_model if settings.ollama_base_url else settings.model
    print(f"[smoke] provider={provider} model={model}")
    print(f"[smoke] response: {response.text.strip()}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "smoke":
        try:
            asyncio.run(run_smoke())
            return 0
        except ValueError as exc:
            print(f"[smoke] configuration error: {exc}", file=sys.stderr)
            return 2
        except Exception as exc:
            print(f"[smoke] failed: {exc}", file=sys.stderr)
            return 1
    parser.print_help()
    return 0
