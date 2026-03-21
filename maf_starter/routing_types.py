from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


RouteLane = Literal["auto", "deep", "balanced", "fast"]
RouteStatus = Literal["planned", "running", "succeeded", "failed"]


@dataclass(frozen=True)
class ChainStep:
    provider: str
    model: str | None = None

    @property
    def label(self) -> str:
        return f"{self.provider}:{self.model}" if self.model else self.provider

    def to_dict(self) -> dict[str, str | None]:
        return {"provider": self.provider, "model": self.model}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> ChainStep:
        return cls(provider=str(payload.get("provider", "")).strip(), model=(str(payload["model"]).strip() or None) if payload.get("model") else None)


@dataclass(frozen=True)
class RouteAttempt:
    provider: str
    model: str | None = None
    status: str = "planned"
    tools_available: bool = True
    fallback_index: int = 0
    error: str | None = None
    started_at: str | None = None
    completed_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "status": self.status,
            "tools_available": self.tools_available,
            "fallback_index": self.fallback_index,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> RouteAttempt:
        return cls(
            provider=str(payload.get("provider", "")).strip(),
            model=(str(payload["model"]).strip() or None) if payload.get("model") else None,
            status=str(payload.get("status", "planned")),
            tools_available=bool(payload.get("tools_available", True)),
            fallback_index=int(payload.get("fallback_index", 0) or 0),
            error=(str(payload["error"]).strip() or None) if payload.get("error") else None,
            started_at=(str(payload["started_at"]).strip() or None) if payload.get("started_at") else None,
            completed_at=(str(payload["completed_at"]).strip() or None) if payload.get("completed_at") else None,
        )


@dataclass(frozen=True)
class CapabilityChange:
    name: str
    before: Any
    after: Any
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "before": self.before,
            "after": self.after,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> CapabilityChange:
        return cls(
            name=str(payload.get("name", "")).strip(),
            before=payload.get("before"),
            after=payload.get("after"),
            reason=str(payload.get("reason", "")).strip(),
        )


def parse_chain_steps(values: tuple[str, ...]) -> tuple[ChainStep, ...]:
    steps: list[ChainStep] = []
    for value in values:
        provider, sep, model = value.partition(":")
        provider = provider.strip()
        model = model.strip() if sep else None
        if provider:
            steps.append(ChainStep(provider=provider, model=model or None))
    return tuple(steps)
