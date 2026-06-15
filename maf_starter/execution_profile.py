from __future__ import annotations

from dataclasses import dataclass

from maf_starter.worker_boundary import WorkerProfile


# Providers that require subprocess access and cannot run in a cloud-hosted context.
SUBPROCESS_PROVIDERS: frozenset[str] = frozenset({"gemini-cli", "claude-cli", "codex-cli"})


class IncompatibleProviderError(RuntimeError):
    """Raised when a provider requires capabilities that the active execution
    profile does not allow.

    Example::

        raise IncompatibleProviderError("gemini-cli", WorkerProfile.CLOUD_SAFE)
    """

    def __init__(self, provider: str, profile: WorkerProfile) -> None:
        self.provider = provider
        self.profile = profile
        super().__init__(
            f"Provider {provider!r} requires subprocess access which is not "
            f"available in {profile.value!r} profile."
        )


@dataclass(frozen=True)
class ExecutionProfile:
    """Describes the execution capabilities available in the current hosting context.

    Attributes:
        profile:      The broad classification of the execution environment.
        capabilities: Explicit capability tokens that other modules can inspect
                      to decide whether a feature or provider is allowed.
    """

    profile: WorkerProfile
    capabilities: tuple[str, ...]

    def allows_subprocess(self) -> bool:
        """Return True when subprocess-backed providers are permitted."""
        return "subprocess" in self.capabilities

    def assert_provider_allowed(self, provider: str) -> None:
        """Raise IncompatibleProviderError if *provider* is a subprocess provider
        and the profile does not allow subprocess access.

        Args:
            provider: Provider key such as ``"gemini-cli"``, ``"claude-cli"``,
                      or ``"gemini"``.  Non-subprocess providers are always
                      allowed and this method returns immediately.
        """
        if provider in SUBPROCESS_PROVIDERS and not self.allows_subprocess():
            raise IncompatibleProviderError(provider, self.profile)


# Pre-built profile constants -------------------------------------------------

LOCAL_PROFILE = ExecutionProfile(
    profile=WorkerProfile.LOCAL,
    capabilities=("api", "subprocess", "repo-execution"),
)
"""Local workstation profile — all providers and repo execution are permitted."""

CLOUD_SAFE_PROFILE = ExecutionProfile(
    profile=WorkerProfile.CLOUD_SAFE,
    capabilities=("api-only", "no-subprocess"),
)
"""Cloud-safe profile — API-only providers only; subprocess providers are rejected."""
