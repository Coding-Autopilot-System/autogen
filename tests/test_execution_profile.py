from __future__ import annotations

import unittest

from maf_starter.execution_profile import (
    CLOUD_SAFE_PROFILE,
    LOCAL_PROFILE,
    SUBPROCESS_PROVIDERS,
    ExecutionProfile,
    IncompatibleProviderError,
)
from maf_starter.worker_boundary import WorkerProfile


class IncompatibleProviderErrorTests(unittest.TestCase):
    def test_message_contains_provider_and_profile(self) -> None:
        exc = IncompatibleProviderError("gemini-cli", WorkerProfile.CLOUD_SAFE)
        msg = str(exc)
        self.assertIn("gemini-cli", msg)
        self.assertIn("cloud-safe", msg)
        self.assertIn("subprocess", msg)

    def test_attributes_are_accessible(self) -> None:
        exc = IncompatibleProviderError("claude-cli", WorkerProfile.CLOUD_SAFE)
        self.assertEqual(exc.provider, "claude-cli")
        self.assertEqual(exc.profile, WorkerProfile.CLOUD_SAFE)

    def test_is_runtime_error(self) -> None:
        exc = IncompatibleProviderError("codex-cli", WorkerProfile.CLOUD_SAFE)
        self.assertIsInstance(exc, RuntimeError)


class ExecutionProfileTests(unittest.TestCase):
    def test_local_profile_allows_subprocess(self) -> None:
        self.assertTrue(LOCAL_PROFILE.allows_subprocess())

    def test_cloud_safe_profile_disallows_subprocess(self) -> None:
        self.assertFalse(CLOUD_SAFE_PROFILE.allows_subprocess())

    def test_local_profile_capabilities(self) -> None:
        self.assertIn("subprocess", LOCAL_PROFILE.capabilities)
        self.assertIn("api", LOCAL_PROFILE.capabilities)
        self.assertIn("repo-execution", LOCAL_PROFILE.capabilities)

    def test_cloud_safe_profile_capabilities(self) -> None:
        self.assertIn("api-only", CLOUD_SAFE_PROFILE.capabilities)
        self.assertIn("no-subprocess", CLOUD_SAFE_PROFILE.capabilities)
        self.assertNotIn("subprocess", CLOUD_SAFE_PROFILE.capabilities)

    def test_local_profile_accepts_all_provider_types(self) -> None:
        for provider in ("gemini", "anthropic", "gemini-cli", "claude-cli", "codex-cli"):
            # Should not raise
            LOCAL_PROFILE.assert_provider_allowed(provider)

    def test_cloud_safe_profile_rejects_subprocess_providers(self) -> None:
        for provider in SUBPROCESS_PROVIDERS:
            with self.assertRaises(IncompatibleProviderError) as ctx:
                CLOUD_SAFE_PROFILE.assert_provider_allowed(provider)
            self.assertEqual(ctx.exception.provider, provider)
            self.assertEqual(ctx.exception.profile, WorkerProfile.CLOUD_SAFE)

    def test_cloud_safe_profile_accepts_api_providers(self) -> None:
        for provider in ("gemini", "anthropic"):
            # Should not raise
            CLOUD_SAFE_PROFILE.assert_provider_allowed(provider)

    def test_profiles_are_frozen(self) -> None:
        with self.assertRaises((AttributeError, TypeError)):
            LOCAL_PROFILE.profile = WorkerProfile.CLOUD_SAFE  # type: ignore[misc]

    def test_custom_profile_with_no_capabilities_rejects_subprocess(self) -> None:
        empty = ExecutionProfile(profile=WorkerProfile.CLOUD_SAFE, capabilities=())
        with self.assertRaises(IncompatibleProviderError):
            empty.assert_provider_allowed("gemini-cli")

    def test_subprocess_providers_set_covers_known_cli_providers(self) -> None:
        self.assertIn("gemini-cli", SUBPROCESS_PROVIDERS)
        self.assertIn("claude-cli", SUBPROCESS_PROVIDERS)
        self.assertIn("codex-cli", SUBPROCESS_PROVIDERS)


if __name__ == "__main__":
    unittest.main()
