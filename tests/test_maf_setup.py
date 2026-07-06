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
from maf_starter.config import (
    activate_run_scope,
    current_checkpoint_dir,
    current_repo_root,
    load_settings,
    mask_secret,
    reset_run_scope,
)
from maf_starter.devui_overrides import OLD_GD_RENDERER
from maf_starter.devui_overrides import _patch_devui_bundle
from maf_starter.devui_overrides import install_devui_ui_overrides
from maf_starter.provider_fallback import (
    ResponseStream,
    _is_fallback_worthy_error,
    _merge_route_metadata,
    _response_from_updates,
    _resolve_run_scope,
    _sanitize_messages,
    _wrap_stream_with_fallback,
)
from maf_starter.routing_policy import RoutingPlan, build_routing_plan
from maf_starter.routing_types import ChainStep, parse_chain_steps
from maf_starter.team_factory import build_repo_team
from maf_starter.tools import (
    _iter_repo_files,
    _read_text_file,
    build_repo_context_snapshot,
    build_repo_tools,
    is_write_blocked_path,
    resolve_repo_path,
)
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

    def test_mask_secret_handles_missing_and_short_values(self) -> None:
        self.assertEqual(mask_secret(""), "<missing>")
        self.assertEqual(mask_secret("short"), "*****")

    def test_resolve_repo_path_blocks_escape(self) -> None:
        root = self.make_scratch_dir().resolve()
        allowed = root / "notes.txt"
        allowed.write_text("ok", encoding="utf-8")
        self.assertEqual(resolve_repo_path(root, "notes.txt"), allowed)
        for unsafe_path in ("../outside.txt", "..\\outside.txt", "C:\\outside.txt"):
            with self.subTest(path=unsafe_path):
                with self.assertRaises(ValueError):
                    resolve_repo_path(root, unsafe_path)

    def test_resolve_repo_path_allows_missing_and_blocks_write_protected_paths(self) -> None:
        root = self.make_scratch_dir().resolve()
        missing = resolve_repo_path(root, "new-file.txt", allow_missing=True)
        self.assertEqual(missing, root / "new-file.txt")

        protected = root / ".env.local"
        protected.write_text("SECRET=1", encoding="utf-8")
        self.assertTrue(is_write_blocked_path(root, protected))
        with self.assertRaisesRegex(ValueError, "blocked for write operations"):
            resolve_repo_path(root, ".env.local", for_write=True)

    def test_iter_repo_files_skips_internal_dirs_and_binary_reads_return_none(self) -> None:
        root = self.make_scratch_dir().resolve()
        visible = root / "visible.txt"
        visible.write_text("ok", encoding="utf-8")
        skipped_dir = root / ".venv"
        skipped_dir.mkdir()
        (skipped_dir / "hidden.txt").write_text("ignore", encoding="utf-8")
        binary = root / "data.bin"
        binary.write_bytes(b"\x00\x01\x02")

        files = [path.relative_to(root).as_posix() for path in _iter_repo_files(root, "*")]
        self.assertIn("visible.txt", files)
        self.assertIn("data.bin", files)
        self.assertNotIn(".venv/hidden.txt", files)
        self.assertIsNone(_read_text_file(binary))

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

    def test_build_repo_context_snapshot_captures_git_branch(self) -> None:
        root = self.make_scratch_dir().resolve()
        (root / "README.md").write_text("hello", encoding="utf-8")
        subprocess_root = str(root)
        __import__("subprocess").run(["git", "init", "-b", "main"], cwd=subprocess_root, check=True, capture_output=True)

        snapshot = build_repo_context_snapshot(root)

        self.assertEqual(snapshot["root"], str(root))
        self.assertIn("README.md", snapshot["top_level_items"])
        self.assertIn("main", str(snapshot["branch"]))
        self.assertGreaterEqual(int(snapshot["file_count_hint"]), 1)

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

    def test_load_settings_supports_ollama_without_api_key(self) -> None:
        root = self.make_scratch_dir()
        (root / "entities").mkdir()
        (root / "repo").mkdir()

        with patch.dict(
            "os.environ",
            {
                "MAF_API_KEY": "",
                "GEMINI_API_KEY": "",
                "MAF_REPO_ROOT": str(root / "repo"),
                "MAF_ENTITIES_DIR": str(root / "entities"),
                "OLLAMA_BASE_URL": "http://localhost:11434",
                "OLLAMA_MODEL": "llama3.2",
            },
            clear=False,
        ):
            settings = load_settings(project_root=root, env_path=root / ".missing-env")

        self.assertEqual(settings.api_key, "")
        self.assertEqual(settings.ollama_base_url, "http://localhost:11434")
        self.assertEqual(settings.fallback_chain[0], "ollama:llama3.2")

    def test_load_settings_rejects_missing_repo_root(self) -> None:
        root = self.make_scratch_dir()
        (root / "entities").mkdir()
        missing_repo = root / "missing-repo"

        with patch.dict(
            "os.environ",
            {
                "MAF_API_KEY": "test-key",
                "MAF_REPO_ROOT": str(missing_repo),
                "MAF_ENTITIES_DIR": str(root / "entities"),
            },
            clear=False,
        ):
            with self.assertRaisesRegex(ValueError, "Configured repo root does not exist"):
                load_settings(project_root=root, env_path=root / ".missing-env")

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

    def test_sanitize_messages_strips_unsupported_reasoning_properties(self) -> None:
        messages = [
            Message(
                role="assistant",
                text="intermediate",
                additional_properties={"reasoning_details": {"token_count": 3}, "keep": "yes"},
                raw_representation={"reasoningDetails": {"step": 1}, "other": "ok"},
            ),
            Message(role="user", text="final"),
        ]

        sanitized = _sanitize_messages(messages)

        self.assertEqual(len(sanitized), 2)
        self.assertNotIn("reasoning_details", sanitized[0].additional_properties)
        self.assertEqual(sanitized[0].additional_properties["keep"], "yes")
        self.assertEqual(sanitized[0].raw_representation, {"other": "ok"})
        self.assertIs(sanitized[1], messages[1])

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
            reset_run_scope(tokens)

    def test_activate_run_scope_updates_repo_and_checkpoint_contextvars(self) -> None:
        root = self.make_scratch_dir()
        entities = root / "entities"
        repo = root / "repo"
        entities.mkdir()
        repo.mkdir()

        with patch.dict(
            "os.environ",
            {
                "MAF_API_KEY": "test-key",
                "MAF_REPO_ROOT": str(repo),
                "MAF_ENTITIES_DIR": str(entities),
                "MAF_CHECKPOINT_DIR": str(root / "state"),
            },
            clear=False,
        ):
            settings = load_settings(project_root=root, env_path=root / ".missing-env")

        run_repo = root / "alternate-repo"
        run_repo.mkdir()
        run_checkpoint = root / "alternate-state"
        scoped, tokens = activate_run_scope(settings, repo_root=run_repo, checkpoint_dir=run_checkpoint)
        try:
            self.assertEqual(scoped.repo_root, run_repo.resolve())
            self.assertEqual(scoped.checkpoint_dir, run_checkpoint.resolve())
            self.assertEqual(current_repo_root(settings.repo_root), run_repo.resolve())
            self.assertEqual(current_checkpoint_dir(settings.checkpoint_dir), run_checkpoint.resolve())
        finally:
            reset_run_scope(tokens)

    def test_response_from_updates_handles_empty_and_populated_streams(self) -> None:
        empty = _response_from_updates([])
        self.assertEqual(empty.text, "")

        populated = _response_from_updates(
            [
                ChatResponseUpdate(
                    role="assistant",
                    contents=[Content.from_text("READY")],
                    model_id="fallback-model",
                    additional_properties={"fallback_used": True},
                )
            ]
        )
        self.assertEqual(populated.text, "READY")
        self.assertEqual(populated.model_id, "fallback-model")
        self.assertTrue(populated.additional_properties["fallback_used"])

    def test_fallback_worthy_error_matches_quota_markers_only(self) -> None:
        self.assertTrue(_is_fallback_worthy_error(RuntimeError("429 RESOURCE_EXHAUSTED from upstream")))
        self.assertTrue(_is_fallback_worthy_error(RuntimeError("provider hit rate limit")))
        self.assertFalse(_is_fallback_worthy_error(RuntimeError("syntax error in local prompt")))

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


    def test_load_settings_ollama_no_api_key(self) -> None:
        root = self.make_scratch_dir()
        (root / "entities").mkdir()
        (root / "repo").mkdir()

        with patch.dict(
            "os.environ",
            {
                "OLLAMA_BASE_URL": "http://localhost:11434/v1",
                "OLLAMA_MODEL": "gemma3",
                "MAF_REPO_ROOT": str(root / "repo"),
                "MAF_ENTITIES_DIR": str(root / "entities"),
            },
            clear=False,
        ):
            # Must not raise even though MAF_API_KEY and GEMINI_API_KEY are absent
            with patch.dict("os.environ", {"MAF_API_KEY": "", "GEMINI_API_KEY": ""}, clear=False):
                settings = load_settings(project_root=root, env_path=root / ".missing-env")

        self.assertEqual(settings.ollama_base_url, "http://localhost:11434/v1")
        self.assertEqual(settings.ollama_model, "gemma3")

    def test_load_settings_requires_key_or_ollama(self) -> None:
        root = self.make_scratch_dir()
        (root / "entities").mkdir()
        (root / "repo").mkdir()

        with patch.dict(
            "os.environ",
            {
                "MAF_API_KEY": "",
                "GEMINI_API_KEY": "",
                "OLLAMA_BASE_URL": "",
                "MAF_REPO_ROOT": str(root / "repo"),
                "MAF_ENTITIES_DIR": str(root / "entities"),
            },
            clear=False,
        ):
            with self.assertRaises(ValueError) as ctx:
                load_settings(project_root=root, env_path=root / ".missing-env")

        self.assertIn("OLLAMA_BASE_URL", str(ctx.exception))

    def test_ollama_is_tier_0_when_configured(self) -> None:
        root = self.make_scratch_dir()
        (root / "entities").mkdir()
        (root / "repo").mkdir()

        with patch.dict(
            "os.environ",
            {
                "OLLAMA_BASE_URL": "http://localhost:11434/v1",
                "OLLAMA_MODEL": "gemma3",
                "MAF_API_KEY": "",
                "GEMINI_API_KEY": "",
                "MAF_REPO_ROOT": str(root / "repo"),
                "MAF_ENTITIES_DIR": str(root / "entities"),
            },
            clear=False,
        ):
            settings = load_settings(project_root=root, env_path=root / ".missing-env")

        self.assertTrue(settings.fallback_chain[0].startswith("ollama:"))
        self.assertIn("gemma3", settings.fallback_chain[0])

    def test_build_agent_uses_ollama_client(self) -> None:
        root = self.make_scratch_dir()
        (root / "entities").mkdir()
        (root / "repo").mkdir()

        with patch.dict(
            "os.environ",
            {
                "OLLAMA_BASE_URL": "http://localhost:11434/v1",
                "OLLAMA_MODEL": "gemma3",
                "MAF_API_KEY": "",
                "GEMINI_API_KEY": "",
                "MAF_REPO_ROOT": str(root / "repo"),
                "MAF_ENTITIES_DIR": str(root / "entities"),
            },
            clear=False,
        ):
            settings = load_settings(project_root=root, env_path=root / ".missing-env")

        with patch("maf_starter.agent_factory.build_fallback_middleware") as mock_mw:
            mock_mw.return_value = object()
            build_agent(settings)
            _, kwargs = mock_mw.call_args
            self.assertEqual(kwargs["primary_provider"], "ollama")
            self.assertEqual(kwargs["primary_model"], "gemma3")

    def test_env_example_documents_ollama(self) -> None:
        env_example = (
            Path(__file__).resolve().parents[1] / ".env.example"
        )
        text = env_example.read_text(encoding="utf-8")
        self.assertIn("OLLAMA_BASE_URL", text)
        self.assertIn("OLLAMA_MODEL", text)
        self.assertIn("gemma3", text)


if __name__ == "__main__":
    unittest.main()
