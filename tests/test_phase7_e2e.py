from __future__ import annotations

"""Phase 7 end-to-end integration tests.

Validates three Phase 7 success criteria:
  1. Cloud-safe profile rejects subprocess providers with IncompatibleProviderError.
  2. Local profile accepts all providers without raising.
  3. Async dispatch via WorkerBoundary.submit_async returns run_id without blocking.
"""

import asyncio
import unittest

from maf_starter.execution_profile import (
    CLOUD_SAFE_PROFILE,
    LOCAL_PROFILE,
    SUBPROCESS_PROVIDERS,
    IncompatibleProviderError,
)
from maf_starter.worker_boundary import WorkerBoundary, WorkerProfile


class Phase7CloudSafeRejectionTests(unittest.TestCase):
    """WRKR-02: Cloud-safe profile rejects local-only providers."""

    def test_cloud_safe_rejects_gemini_cli(self) -> None:
        with self.assertRaises(IncompatibleProviderError) as ctx:
            CLOUD_SAFE_PROFILE.assert_provider_allowed("gemini-cli")
        self.assertIn("gemini-cli", str(ctx.exception))
        self.assertIn("cloud-safe", str(ctx.exception))

    def test_cloud_safe_rejects_claude_cli(self) -> None:
        with self.assertRaises(IncompatibleProviderError) as ctx:
            CLOUD_SAFE_PROFILE.assert_provider_allowed("claude-cli")
        self.assertIn("claude-cli", str(ctx.exception))

    def test_cloud_safe_rejects_codex_cli(self) -> None:
        with self.assertRaises(IncompatibleProviderError) as ctx:
            CLOUD_SAFE_PROFILE.assert_provider_allowed("codex-cli")
        self.assertIn("codex-cli", str(ctx.exception))

    def test_cloud_safe_rejects_all_known_subprocess_providers(self) -> None:
        for provider in SUBPROCESS_PROVIDERS:
            with self.subTest(provider=provider):
                with self.assertRaises(IncompatibleProviderError):
                    CLOUD_SAFE_PROFILE.assert_provider_allowed(provider)

    def test_cloud_safe_error_is_informative(self) -> None:
        exc = IncompatibleProviderError("gemini-cli", WorkerProfile.CLOUD_SAFE)
        msg = str(exc)
        # Message must name the provider, the profile, and explain why
        self.assertIn("gemini-cli", msg)
        self.assertIn("cloud-safe", msg)
        self.assertIn("subprocess", msg)


class Phase7LocalProfileAcceptsAllTests(unittest.TestCase):
    """WRKR-03: Local profile keeps existing providers working."""

    def test_local_profile_accepts_gemini_api(self) -> None:
        LOCAL_PROFILE.assert_provider_allowed("gemini")

    def test_local_profile_accepts_anthropic_api(self) -> None:
        LOCAL_PROFILE.assert_provider_allowed("anthropic")

    def test_local_profile_accepts_gemini_cli(self) -> None:
        LOCAL_PROFILE.assert_provider_allowed("gemini-cli")

    def test_local_profile_accepts_claude_cli(self) -> None:
        LOCAL_PROFILE.assert_provider_allowed("claude-cli")

    def test_local_profile_accepts_codex_cli(self) -> None:
        LOCAL_PROFILE.assert_provider_allowed("codex-cli")

    def test_local_profile_is_unrestricted_for_all_subprocess_providers(self) -> None:
        for provider in SUBPROCESS_PROVIDERS:
            with self.subTest(provider=provider):
                # Should not raise
                LOCAL_PROFILE.assert_provider_allowed(provider)


class Phase7AsyncDispatchTests(unittest.IsolatedAsyncioTestCase):
    """WRKR-01: HTTP ingress never waits for full long-running execution to complete."""

    async def test_submit_async_returns_run_id_before_workflow_completes(self) -> None:
        boundary = WorkerBoundary(profile=WorkerProfile.LOCAL)
        workflow_started = asyncio.Event()
        workflow_unblocked = asyncio.Event()

        async def long_running_workflow():
            workflow_started.set()
            # Block until test explicitly allows completion
            await workflow_unblocked.wait()

        # submit_async must return the run_id immediately
        returned_id = boundary.submit_async("e2e-run-1", long_running_workflow)
        self.assertEqual(returned_id, "e2e-run-1")

        # The caller does not await the workflow — status is pending/running
        status_before = boundary.get_status("e2e-run-1")
        self.assertIn(status_before, ("pending", "running"))
        self.assertFalse(boundary.is_done("e2e-run-1"))

        # Allow the workflow to finish and verify terminal state
        workflow_unblocked.set()
        await asyncio.sleep(0)
        self.assertEqual(boundary.get_status("e2e-run-1"), "done")
        self.assertTrue(boundary.is_done("e2e-run-1"))

    async def test_multiple_runs_are_dispatched_independently(self) -> None:
        boundary = WorkerBoundary(profile=WorkerProfile.LOCAL)
        done_events = {f"run-{i}": asyncio.Event() for i in range(3)}

        async def make_workflow(run_id: str):
            async def workflow():
                done_events[run_id].set()
            return workflow

        for run_id in done_events:
            workflow = await make_workflow(run_id)
            returned = boundary.submit_async(run_id, workflow)
            self.assertEqual(returned, run_id)

        # All three were accepted immediately
        self.assertEqual(len(boundary.all_run_ids()), 3)

        # Let tasks complete
        await asyncio.sleep(0)
        for run_id in done_events:
            with self.subTest(run_id=run_id):
                self.assertTrue(boundary.is_done(run_id))

    async def test_cloud_safe_boundary_can_dispatch_api_only_workflow(self) -> None:
        boundary = WorkerBoundary(profile=WorkerProfile.CLOUD_SAFE)
        result_container: list[str] = []

        async def api_only_workflow():
            result_container.append("completed")

        run_id = boundary.submit_async("cloud-run-1", api_only_workflow)
        self.assertEqual(run_id, "cloud-run-1")
        self.assertEqual(boundary.profile, WorkerProfile.CLOUD_SAFE)

        await asyncio.sleep(0)
        self.assertEqual(boundary.get_status("cloud-run-1"), "done")
        self.assertEqual(result_container, ["completed"])


if __name__ == "__main__":
    unittest.main()
