from __future__ import annotations

import contextlib
import io
import json
import subprocess
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from agent_framework import ChatResponse, Message

from maf_starter.config import Settings, load_settings
from maf_starter.provider_fallback import (
    _messages_to_prompt,
    _run_subprocess,
    build_fallback_middleware,
)
from maf_starter.routing_policy import RoutingPlan
from maf_starter.routing_types import ChainStep
from maf_starter.telemetry import emit_failure_telemetry


SCRATCH_ROOT = Path(__file__).resolve().parents[1] / ".tmp-tests"


class RepoScratchTestCase(unittest.TestCase):
    def make_scratch_dir(self) -> Path:
        path = SCRATCH_ROOT / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: path.exists() and __import__("shutil").rmtree(path, ignore_errors=True))
        return path


class ProviderFallbackTelemetryTests(RepoScratchTestCase):
    def _make_settings(self, root: Path) -> Settings:
        entities = root / "entities"
        repo = root / "repo"
        entities.mkdir()
        repo.mkdir()
        env = {
            "MAF_API_KEY": "test-key",
            "MAF_REPO_ROOT": str(repo),
            "MAF_ENTITIES_DIR": str(entities),
            "MAF_FALLBACK_CHAIN": "gemini-cli:gemini-2.5-pro,claude-cli:claude-sonnet-4-6",
        }
        with patch.dict("os.environ", env, clear=False):
            return load_settings(project_root=root, env_path=root / ".missing-env")

    @staticmethod
    def _make_route_plan() -> RoutingPlan:
        return RoutingPlan(
            mode="auto",
            route_lane="auto",
            tier="standard",
            rationale="test route",
            primary_provider="gemini",
            primary_model="gemini-2.5-pro",
            requested_provider="gemini",
            requested_model="gemini-2.5-pro",
            fallback_steps=(
                ChainStep("gemini-cli", "gemini-2.5-pro"),
                ChainStep("claude-cli", "claude-sonnet-4-6"),
            ),
        )

    @staticmethod
    def _make_context() -> SimpleNamespace:
        return SimpleNamespace(
            messages=[Message(role="user", text="hello fallback")],
            options={},
            kwargs={},
            metadata={},
            result=None,
        )

    def test_emit_failure_telemetry_writes_single_parseable_json_line(self) -> None:
        stream = io.StringIO()
        with contextlib.redirect_stderr(stream):
            emit_failure_telemetry("provider_failed", provider="gemini", error="quota exceeded")

        lines = stream.getvalue().strip().splitlines()
        self.assertEqual(len(lines), 1)
        payload = json.loads(lines[0])
        self.assertEqual(payload["event"], "provider_failed")
        self.assertEqual(payload["provider"], "gemini")
        self.assertEqual(payload["error"], "quota exceeded")
        self.assertIn("timestamp", payload)

    def test_emit_failure_telemetry_swallows_stderr_write_failures(self) -> None:
        fake_stderr = SimpleNamespace(
            write=lambda _: (_ for _ in ()).throw(RuntimeError("stderr failed")),
            flush=lambda: None,
        )
        with patch("sys.stderr", fake_stderr):
            self.assertIsNone(emit_failure_telemetry("provider_failed", provider="gemini", error="boom"))

    def test_fallback_middleware_emits_primary_step_and_exhausted_events(self) -> None:
        root = self.make_scratch_dir()
        settings = self._make_settings(root)
        middleware = build_fallback_middleware(
            settings,
            primary_provider="gemini",
            primary_model="gemini-2.5-pro",
            routing_mode="auto",
        )
        context = self._make_context()
        stderr = io.StringIO()

        async def call_next():
            raise RuntimeError("rate limit from primary")

        attempts = [
            RuntimeError("rate limit in gemini-cli fallback"),
            RuntimeError("quota exhausted in claude fallback"),
        ]

        async def fake_execute_chain_step(**_kwargs):
            raise attempts.pop(0)

        with (
            patch("maf_starter.provider_fallback.build_routing_plan", return_value=self._make_route_plan()),
            patch("maf_starter.provider_fallback._execute_chain_step", side_effect=fake_execute_chain_step),
            contextlib.redirect_stderr(stderr),
        ):
            with self.assertRaisesRegex(RuntimeError, "quota exhausted in claude fallback"):
                __import__("asyncio").run(middleware(context, call_next))

        events = [json.loads(line)["event"] for line in stderr.getvalue().strip().splitlines()]
        self.assertEqual(events, ["provider_failed", "fallback_step_failed", "fallback_step_failed", "fallback_exhausted"])

    def test_fallback_middleware_emits_recovery_event_when_fallback_succeeds(self) -> None:
        root = self.make_scratch_dir()
        settings = self._make_settings(root)
        middleware = build_fallback_middleware(
            settings,
            primary_provider="gemini",
            primary_model="gemini-2.5-pro",
            routing_mode="auto",
        )
        context = self._make_context()
        stderr = io.StringIO()

        async def call_next():
            raise RuntimeError("rate limit from primary")

        async def fake_execute_chain_step(**_kwargs):
            return ChatResponse(messages=[Message(role="assistant", text="fallback ok")])

        with (
            patch("maf_starter.provider_fallback.build_routing_plan", return_value=self._make_route_plan()),
            patch("maf_starter.provider_fallback._execute_chain_step", side_effect=fake_execute_chain_step),
            contextlib.redirect_stderr(stderr),
        ):
            __import__("asyncio").run(middleware(context, call_next))

        payloads = [json.loads(line) for line in stderr.getvalue().strip().splitlines()]
        self.assertEqual(payloads[0]["event"], "provider_failed")
        self.assertEqual(payloads[1]["event"], "fallback_succeeded")
        self.assertNotIn("fallback_exhausted", [payload["event"] for payload in payloads])
        self.assertIsInstance(context.result, ChatResponse)

    def test_run_subprocess_rejects_oversized_output(self) -> None:
        completed = subprocess.CompletedProcess(args=["codex.cmd"], returncode=0, stdout="x" * 32, stderr="")
        with (
            patch("maf_starter.provider_fallback.subprocess.run", return_value=completed),
            patch("maf_starter.provider_fallback.shutil.which", return_value="codex.cmd"),
            patch("maf_starter.provider_fallback.MAX_CLI_OUTPUT_BYTES", 8),
        ):
            with self.assertRaisesRegex(RuntimeError, "output exceeds 8 bytes"):
                _run_subprocess("codex-cli", ["codex.cmd", "exec"], Path.cwd(), None)

    def test_messages_to_prompt_rejects_oversized_prompt(self) -> None:
        messages = [Message(role="user", text="x" * 32)]
        with patch("maf_starter.provider_fallback.MAX_CLI_PROMPT_BYTES", 8):
            with self.assertRaisesRegex(ValueError, "Rendered CLI prompt exceeds 8 bytes"):
                _messages_to_prompt(messages)
