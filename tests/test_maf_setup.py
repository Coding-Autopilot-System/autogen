from __future__ import annotations

import unittest
import uuid
import shutil
from pathlib import Path
from unittest.mock import AsyncMock, patch

from agent_framework import ChatContext, ChatResponse, ChatResponseUpdate, Message
from agent_framework._types import Content
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient

from maf_starter.agent_factory import build_agent
from maf_starter.config import current_checkpoint_dir, load_settings, mask_secret
from maf_starter.devui_overrides import OLD_GD_RENDERER
from maf_starter.devui_overrides import _patch_devui_bundle
from maf_starter.devui_overrides import install_devui_ui_overrides
from maf_starter.provider_fallback import ResponseStream, _merge_route_metadata, _resolve_run_scope, _wrap_stream_with_fallback
from maf_starter.routing_policy import RoutingPlan, build_routing_plan
from maf_starter.routing_types import ChainStep, parse_chain_steps
from maf_starter.team_factory import build_repo_team
from maf_starter.tools import build_repo_tools, resolve_repo_path
from maf_starter.workflow_factory import build_workflow


SCRATCH_ROOT = Path(__file__).resolve().parents[1] / ".tmp-tests"


def load_test_settings():
    with patch.dict("os.environ", {"MAF_API_KEY": "test-key"}, clear=False):
        return load_settings(project_root=Path.cwd(), env_path=Path.cwd() / ".missing-env")


class RepoScratchTestCase(unittest.TestCase):
    def make_scratch_dir(self) -> Path:
        path = SCRATCH_ROOT / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path


class MafSetupTests(RepoScratchTestCase):
    def test_parse_chain_steps(self) -> None:
        steps = parse_chain_steps(
            (
                "gemini:gemini-2.5-pro",
                "gemini-cli:gemini-2.5-pro",
                "claude-cli",
            )
        )
        self.assertEqual(
            [(step.provider, step.model) for step in steps],
            [
                ("gemini", "gemini-2.5-pro"),
                ("gemini-cli", "gemini-2.5-pro"),
                ("claude-cli", None),
            ],
        )

    def test_load_settings_prefers_maf_over_gemini_fallbacks(self) -> None:
        root = self.make_scratch_dir()
        (root / "entities").mkdir()
        (root / "repo").mkdir()

        with patch.dict(
            "os.environ",
            {
                "MAF_API_KEY": "maf-secret",
                "GEMINI_API_KEY": "gem-secret",
                "MAF_MODEL": "gemini-2.5-flash",
                "GEMINI_MODEL": "gemini-2.5-pro",
                "MAF_REPO_ROOT": str(root / "repo"),
                "MAF_ENTITIES_DIR": str(root / "entities"),
            },
            clear=False,
        ):
            settings = load_settings(project_root=root, env_path=root / ".missing-env")

        self.assertEqual(settings.api_key, "maf-secret")
        self.assertEqual(settings.model, "gemini-2.5-flash")
        self.assertEqual(settings.repo_root, (root / "repo").resolve())
        self.assertEqual(settings.entities_dir, (root / "entities").resolve())

    def test_default_fallback_chain_includes_anthropic_when_key_exists(self) -> None:
        root = self.make_scratch_dir()
        (root / "entities").mkdir()
        (root / "repo").mkdir()

        with patch.dict(
            "os.environ",
            {
                "MAF_API_KEY": "maf-secret",
                "MAF_REPO_ROOT": str(root / "repo"),
                "MAF_ENTITIES_DIR": str(root / "entities"),
                "MAF_FALLBACK_CHAIN": "",
                "ANTHROPIC_API_KEY": "anthropic-secret",
            },
            clear=False,
        ):
            settings = load_settings(project_root=root, env_path=root / ".missing-env")

        self.assertEqual(settings.anthropic_model, "claude-sonnet-4-6")
        self.assertIn("anthropic:claude-sonnet-4-6", settings.fallback_chain)

    def test_mask_secret_keeps_only_edges(self) -> None:
        self.assertEqual(mask_secret("abcd1234wxyz"), "abcd...wxyz")

    def test_resolve_repo_path_blocks_escape(self) -> None:
        root = self.make_scratch_dir().resolve()
        allowed = root / "notes.txt"
        allowed.write_text("ok", encoding="utf-8")
        self.assertEqual(resolve_repo_path(root, "notes.txt"), allowed)
        with self.assertRaises(ValueError):
            resolve_repo_path(root, "..\\outside.txt")

    def test_build_repo_tools_contains_expected_tool_names(self) -> None:
        tools = build_repo_tools(self.make_scratch_dir())
        names = {tool.name for tool in tools}
        self.assertEqual(
            names,
            {
                "get_repo_overview",
                "list_repo_files",
                "read_repo_file",
                "search_repo",
                "request_human_approval",
                "apply_repo_write_plan",
            },
        )

    def test_build_agent_and_workflow_without_network(self) -> None:
        root = self.make_scratch_dir()
        entities = root / "entities"
        repo = root / "repo"
        entities.mkdir()
        repo.mkdir()
        (repo / "README.md").write_text("hello", encoding="utf-8")

        with patch.dict(
            "os.environ",
            {
                "MAF_API_KEY": "test-key",
                "MAF_MODEL": "gemini-2.5-flash",
                "MAF_REPO_ROOT": str(repo),
                "MAF_ENTITIES_DIR": str(entities),
                "MAF_CHECKPOINT_DIR": str(root / "state"),
            },
            clear=False,
        ):
            settings = load_settings(project_root=root, env_path=root / ".missing-env")
            agent = build_agent(settings)
            workflow = build_workflow(settings)

        self.assertEqual(agent.name, "repo_copilot")
        self.assertEqual(workflow.name, "repo_copilot_workflow")

    def test_build_repo_team_without_network(self) -> None:
        root = self.make_scratch_dir()
        entities = root / "entities"
        repo = root / "repo"
        entities.mkdir()
        repo.mkdir()
        (repo / "README.md").write_text("hello", encoding="utf-8")

        with patch.dict(
            "os.environ",
            {
                "MAF_API_KEY": "test-key",
                "MAF_MODEL": "gemini-2.5-flash",
                "MAF_REPO_ROOT": str(repo),
                "MAF_ENTITIES_DIR": str(entities),
                "MAF_CHECKPOINT_DIR": str(root / "state"),
            },
            clear=False,
        ):
            settings = load_settings(project_root=root, env_path=root / ".missing-env")
            workflow = build_repo_team(settings)

        self.assertTrue(hasattr(workflow, "run"))
        self.assertIn("manager-led", workflow.description.lower())
        self.assertEqual(workflow.canonical_stages[0], "planning")

    def test_streaming_fallback_switches_before_first_update(self) -> None:
        async def failing_stream():
            raise RuntimeError("429 resource_exhausted")
            yield  # pragma: no cover

        original_stream = ResponseStream(failing_stream(), finalizer=lambda updates: ChatResponse(messages=[]))
        context = ChatContext(
            client=object(),
            messages=[Message(role="user", text="Reply with READY")],
            options={},
            stream=True,
        )
        settings = load_test_settings()

        async def fallback_updates():
            yield ChatResponseUpdate(role="assistant", contents=[Content.from_text("READY")], model_id="fallback")

        with patch(
            "maf_starter.provider_fallback._execute_chain_step",
            new=AsyncMock(return_value=ResponseStream(fallback_updates(), finalizer=lambda updates: ChatResponse(messages=[]))),
        ) as execute_chain_step:
            wrapped = _wrap_stream_with_fallback(
                settings=settings,
                original_stream=original_stream,
                context=context,
                route=RoutingPlan(
                    mode="auto",
                    tier="deep",
                    rationale="test",
                    primary_provider="gemini",
                    primary_model="gemini-2.5-pro",
                    fallback_steps=(ChainStep("gemini", "gemini-2.5-flash"),),
                ),
            )
            updates = []

            async def consume():
                async for update in wrapped:
                    updates.append(update.text)
                return await wrapped.get_final_response()

            final = __import__("asyncio").run(consume())

        self.assertEqual(updates, ["READY"])
        self.assertIsInstance(final, ChatResponse)
        execute_chain_step.assert_awaited()

    def test_resolve_run_scope_strips_kwargs_and_persists_scope_metadata(self) -> None:
        root = self.make_scratch_dir()
        entities = root / "entities"
        repo = root / "repo"
        entities.mkdir()
        repo.mkdir()

        with patch.dict(
            "os.environ",
            {
                "MAF_API_KEY": "test-key",
                "MAF_MODEL": "gemini-2.5-flash",
                "MAF_REPO_ROOT": str(repo),
                "MAF_ENTITIES_DIR": str(entities),
                "MAF_CHECKPOINT_DIR": str(root / "state"),
            },
            clear=False,
        ):
            settings = load_settings(project_root=root, env_path=root / ".missing-env")

        run_repo = root / "run-repo"
        run_repo.mkdir()
        run_checkpoint = root / "state" / "sessions" / "run-001" / "runtime" / "checkpoint"
        context = ChatContext(
            client=object(),
            messages=[Message(role="user", text="hello")],
            options={},
            kwargs={"repo_root": str(run_repo), "checkpoint_dir": str(run_checkpoint)},
        )

        scoped, tokens = _resolve_run_scope(settings, context)
        try:
            self.assertEqual(scoped.repo_root, run_repo.resolve())
            self.assertEqual(context.kwargs, {})
            self.assertEqual(context.metadata["repo_root"], str(run_repo.resolve()))
            self.assertEqual(context.metadata["checkpoint_dir"], str(run_checkpoint.resolve()))
            self.assertEqual(current_checkpoint_dir(settings.checkpoint_dir), run_checkpoint.resolve())
        finally:
            from maf_starter.config import reset_run_scope

            reset_run_scope(tokens)

    def test_auto_routing_plan_uses_simple_tier_for_light_prompt(self) -> None:
        settings = load_test_settings()
        plan = build_routing_plan(
            settings,
            routing_mode="auto",
            messages=[Message(role="user", text="hello")],
            primary_provider="gemini",
            primary_model="gemini-2.5-pro",
        )
        self.assertEqual(plan.tier, "simple")
        self.assertEqual(plan.primary_model, "gemini-2.5-flash-lite")

    def test_auto_routing_plan_uses_deep_tier_for_repo_work(self) -> None:
        settings = load_test_settings()
        plan = build_routing_plan(
            settings,
            routing_mode="auto",
            messages=[Message(role="user", text="Review this repo and propose an architecture plan")],
            primary_provider="gemini",
            primary_model="gemini-2.5-pro",
        )
        self.assertEqual(plan.tier, "deep")
        self.assertEqual(plan.primary_model, "gemini-2.5-pro")

    def test_devui_override_injects_route_assets_into_root_html(self) -> None:
        app = FastAPI()

        @app.get("/")
        async def root():
            return HTMLResponse("<html><head></head><body><div id='root'></div></body></html>")

        install_devui_ui_overrides(app)
        client = TestClient(app)
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("codex-route-overrides", response.text)
        self.assertIn("codex-route-panel__label", response.text)

    def test_patch_devui_bundle_rewrites_message_renderer(self) -> None:
        patched = _patch_devui_bundle(OLD_GD_RENDERER)
        self.assertIn("function CdxRouteParse", patched)
        self.assertIn("codex-route-panel", patched)
        self.assertIn("CdxRoutePanel", patched)

    def test_route_metadata_contains_tools_available_flag(self) -> None:
        settings = load_test_settings()
        metadata = _merge_route_metadata(
            None,
            settings=settings,
            route=RoutingPlan(
                mode="auto",
                tier="deep",
                rationale="test",
                primary_provider="gemini",
                primary_model="gemini-2.5-pro",
                fallback_steps=(),
            ),
            active_provider="gemini",
            active_model="gemini-2.5-pro",
            fallback_used=False,
        )
        self.assertIn("tools_available", metadata)


if __name__ == "__main__":
    unittest.main()
