from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import patch

from agent_framework import Message
from agent_framework._types import Content

from maf_starter.config import Settings, load_settings
from maf_starter.provider_fallback import _merge_route_metadata
from maf_starter.routing_policy import (
    RoutingPlan,
    _classify_tier,
    _extract_last_user_text,
    _normalize_route_lane,
    build_routing_plan,
)
from maf_starter.routing_types import ChainStep, RouteAttempt


SCRATCH_ROOT = Path(__file__).resolve().parents[1] / ".tmp-tests"


class RepoScratchTestCase(unittest.TestCase):
    def make_scratch_dir(self) -> Path:
        path = SCRATCH_ROOT / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path


class Phase3RoutingTests(RepoScratchTestCase):
    def _make_settings(self, root: Path, *, route_lane: str = "auto", requested_model: str | None = None) -> Settings:
        entities = root / "entities"
        repo = root / "repo"
        entities.mkdir()
        repo.mkdir()
        env = {
            "MAF_API_KEY": "test-key",
            "MAF_REPO_ROOT": str(repo),
            "MAF_ENTITIES_DIR": str(entities),
            "MAF_ROUTE_LANE": route_lane,
        }
        if requested_model is not None:
            env["MAF_REQUESTED_MODEL"] = requested_model
        with patch.dict("os.environ", env, clear=False):
            return load_settings(project_root=root, env_path=root / ".missing-env")

    def _make_settings_with_env(self, root: Path, **extra_env: str) -> Settings:
        entities = root / "entities"
        repo = root / "repo"
        entities.mkdir()
        repo.mkdir()
        env = {
            "MAF_API_KEY": "test-key",
            "MAF_REPO_ROOT": str(repo),
            "MAF_ENTITIES_DIR": str(entities),
        }
        env.update(extra_env)
        with patch.dict("os.environ", env, clear=False):
            return load_settings(project_root=root, env_path=root / ".missing-env")

    def test_auto_lane_uses_prompt_classification_and_keeps_route_lane_explicit(self) -> None:
        root = self.make_scratch_dir()
        settings = self._make_settings(root, route_lane="auto")

        plan = build_routing_plan(
            settings,
            routing_mode="auto",
            messages=[Message(role="user", text="hello")],
            primary_provider="gemini",
            primary_model="gemini-2.5-pro",
        )

        self.assertEqual(plan.route_lane, "auto")
        self.assertEqual(plan.tier, "simple")
        self.assertEqual(plan.primary_model, "gemini-2.5-flash-lite")
        self.assertEqual(plan.route_plan[0].label, "gemini:gemini-2.5-flash-lite")
        self.assertGreaterEqual(plan.fallback_count, 1)

    def test_balanced_lane_honors_requested_model_override(self) -> None:
        root = self.make_scratch_dir()
        settings = self._make_settings(root, route_lane="balanced", requested_model="gemini-2.5-pro")

        plan = build_routing_plan(
            settings,
            routing_mode="auto",
            messages=[Message(role="user", text="review this repo")],
            primary_provider="gemini",
            primary_model="gemini-2.5-flash",
        )

        self.assertEqual(plan.route_lane, "balanced")
        self.assertEqual(plan.tier, "standard")
        self.assertEqual(plan.requested_model, "gemini-2.5-pro")
        self.assertEqual(plan.primary_model, "gemini-2.5-pro")
        self.assertEqual(plan.route_plan[0].label, "gemini:gemini-2.5-pro")
        self.assertTrue(plan.route_plan)
        self.assertEqual(plan.route_plan[0], ChainStep("gemini", "gemini-2.5-pro"))

    def test_invalid_lane_defaults_back_to_auto(self) -> None:
        self.assertEqual(_normalize_route_lane("SIDEWAYS"), "auto")
        self.assertEqual(_normalize_route_lane(" deep "), "deep")

    def test_classify_tier_handles_empty_and_code_fenced_prompts(self) -> None:
        self.assertEqual(_classify_tier("")[0], "standard")
        self.assertEqual(_classify_tier("```python\nprint('hi')\n```")[0], "deep")

    def test_extract_last_user_text_uses_text_contents_and_ignores_non_user_messages(self) -> None:
        messages = [
            Message(role="assistant", text="ignore this"),
            Message(role="user", contents=[Content.from_text("First"), Content.from_text("Second")]),
        ]

        text = _extract_last_user_text(messages)

        self.assertEqual(text, "First\nSecond")

    def test_fast_lane_inserts_anthropic_after_primary(self) -> None:
        root = self.make_scratch_dir()
        settings = self._make_settings_with_env(
            root,
            MAF_ROUTE_LANE="fast",
            ANTHROPIC_API_KEY="anthropic-secret",
        )

        plan = build_routing_plan(
            settings,
            routing_mode="fixed",
            messages=[Message(role="user", text="quick summary")],
            primary_provider="gemini",
            primary_model="gemini-2.5-flash",
        )

        self.assertEqual(plan.route_lane, "fast")
        self.assertEqual(plan.route_plan[0].label, "gemini:gemini-2.5-flash-lite")
        self.assertEqual(plan.fallback_steps[0].label, "gemini:gemini-2.5-flash")
        self.assertEqual(plan.fallback_steps[1].label, "anthropic:claude-sonnet-4-6")

    def test_requested_provider_reorders_balanced_lane_without_duplicate_primary(self) -> None:
        root = self.make_scratch_dir()
        settings = self._make_settings_with_env(
            root,
            MAF_ROUTE_LANE="balanced",
            MAF_REQUESTED_PROVIDER="codex-cli",
            MAF_REQUESTED_MODEL="gpt-5",
        )

        plan = build_routing_plan(
            settings,
            routing_mode="fixed",
            messages=[Message(role="user", text="review this repo")],
            primary_provider="gemini",
            primary_model="gemini-2.5-flash",
        )

        self.assertEqual(plan.primary_provider, "codex-cli")
        self.assertEqual(plan.primary_model, "gpt-5")
        self.assertEqual(plan.route_plan[0].label, "codex-cli:gpt-5")
        self.assertEqual(sum(1 for step in plan.route_plan if step.label == "codex-cli:gpt-5"), 1)
        self.assertEqual(plan.fallback_steps[0].label, "gemini:gemini-2.5-flash")

    def test_ollama_route_becomes_primary_when_base_url_is_configured(self) -> None:
        root = self.make_scratch_dir()
        settings = self._make_settings_with_env(
            root,
            MAF_ROUTE_LANE="auto",
            OLLAMA_BASE_URL="http://localhost:11434",
            OLLAMA_MODEL="llama3.2",
        )

        plan = build_routing_plan(
            settings,
            routing_mode="auto",
            messages=[Message(role="user", text="debug this architecture")],
            primary_provider="gemini",
            primary_model="gemini-2.5-pro",
        )

        self.assertEqual(plan.primary_provider, "ollama")
        self.assertEqual(plan.primary_model, "llama3.2")
        self.assertEqual(plan.route_plan[1].label, "gemini:gemini-2.5-pro")

    def test_route_metadata_records_attempts_and_capability_drift(self) -> None:
        root = self.make_scratch_dir()
        settings = self._make_settings(root, route_lane="auto")
        route = RoutingPlan(
            mode="auto",
            route_lane="auto",
            tier="deep",
            rationale="test",
            primary_provider="gemini",
            primary_model="gemini-2.5-pro",
            requested_provider="gemini",
            requested_model="gemini-2.5-pro",
            fallback_steps=(ChainStep("gemini-cli", "gemini-2.5-pro"),),
        )
        attempt_log = [
            RouteAttempt(
                provider="gemini",
                model="gemini-2.5-pro",
                status="failed",
                tools_available=True,
                fallback_index=0,
                error="quota exhausted",
            ),
            RouteAttempt(
                provider="gemini-cli",
                model="gemini-2.5-pro",
                status="succeeded",
                tools_available=False,
                fallback_index=1,
            ),
        ]

        metadata = _merge_route_metadata(
            None,
            settings=settings,
            route=route,
            active_provider="gemini-cli",
            active_model="gemini-2.5-pro",
            fallback_used=True,
            tools_available=False,
            attempt_log=attempt_log,
            prior_error="quota exhausted",
        )

        self.assertEqual(metadata["route_lane"], "auto")
        self.assertEqual(metadata["requested_provider"], "gemini")
        self.assertEqual(metadata["requested_model"], "gemini-2.5-pro")
        self.assertEqual(metadata["fallback_count"], 1)
        self.assertEqual(metadata["route_attempts"][0]["provider"], "gemini")
        self.assertEqual(metadata["route_attempts"][1]["provider"], "gemini-cli")
        self.assertFalse(metadata["route_attempts"][1]["tools_available"])
        self.assertEqual(metadata["capability_changes"][0]["name"], "tools_available")
        self.assertFalse(metadata["capability_changes"][0]["after"])
        self.assertEqual(metadata["route_plan"][0]["provider"], "gemini")
        self.assertEqual(metadata["route_plan"][1]["provider"], "gemini-cli")
        self.assertTrue(metadata["fallback_used"])
        self.assertFalse(metadata["tools_available"])

    def test_route_attempt_payload_round_trips_cleanly(self) -> None:
        attempt = RouteAttempt(
            provider="gemini",
            model="gemini-2.5-pro",
            status="succeeded",
            tools_available=True,
            fallback_index=0,
            error=None,
            started_at="2026-03-21T12:00:00Z",
            completed_at="2026-03-21T12:00:02Z",
        )
        payload = attempt.to_dict()
        hydrated = RouteAttempt.from_dict(payload)

        self.assertEqual(hydrated, attempt)
        self.assertEqual(payload["provider"], "gemini")
        self.assertEqual(payload["model"], "gemini-2.5-pro")


if __name__ == "__main__":
    unittest.main()
