from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from agent_framework import Message

from maf_starter.config import Settings
from maf_starter.routing_types import CapabilityChange, ChainStep, RouteAttempt, RouteLane


SIMPLE_KEYWORDS = (
    "hello",
    "hi",
    "thanks",
    "thank you",
    "summarize",
    "explain briefly",
    "quick",
)
DEEP_KEYWORDS = (
    "architecture",
    "implement",
    "implementation",
    "workflow",
    "multi-agent",
    "multi agent",
    "review",
    "refactor",
    "debug",
    "investigate",
    "analyze repo",
    "codebase",
    "bicep",
    "azure",
    "function",
    "terraform",
    "design",
    "trace",
    "fallback",
)


@dataclass(frozen=True)
class RoutingPlan:
    mode: str
    route_lane: str = "auto"
    tier: str = "standard"
    rationale: str = ""
    primary_provider: str = ""
    primary_model: str = ""
    requested_provider: str | None = None
    requested_model: str | None = None
    route_plan: tuple[ChainStep, ...] = ()
    fallback_steps: tuple[ChainStep, ...] = ()
    route_attempts: tuple[RouteAttempt, ...] = ()
    fallback_count: int = 0
    capability_changes: tuple[CapabilityChange, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "route_lane": self.route_lane,
            "tier": self.tier,
            "rationale": self.rationale,
            "primary_provider": self.primary_provider,
            "primary_model": self.primary_model,
            "requested_provider": self.requested_provider,
            "requested_model": self.requested_model,
            "route_plan": [step.to_dict() for step in self.route_plan],
            "fallback_steps": [step.to_dict() for step in self.fallback_steps],
            "route_attempts": [attempt.to_dict() for attempt in self.route_attempts],
            "fallback_count": self.fallback_count,
            "capability_changes": [change.to_dict() for change in self.capability_changes],
        }


def build_routing_plan(
    settings: Settings,
    *,
    routing_mode: str,
    messages: Iterable[Message],
    primary_provider: str,
    primary_model: str,
    route_lane: str | None = None,
    requested_provider: str | None = None,
    requested_model: str | None = None,
) -> RoutingPlan:
    lane = _normalize_route_lane(route_lane or settings.route_lane or ("auto" if routing_mode == "auto" else "balanced"))
    requested_provider = (requested_provider or settings.requested_provider or "").strip() or None
    requested_model = (requested_model or settings.requested_model or "").strip() or None

    if lane == "auto":
        last_user_text = _extract_last_user_text(messages)
        tier, rationale = _classify_tier(last_user_text)
    else:
        tier, rationale = _tier_for_lane(lane)

    primary, fallback_steps = _build_lane_chain(
        settings,
        lane=lane,
        tier=tier,
        requested_provider=requested_provider,
        requested_model=requested_model,
        default_provider=primary_provider,
        default_model=primary_model,
    )
    return RoutingPlan(
        mode="auto" if lane == "auto" and routing_mode == "auto" else "fixed",
        route_lane=lane,
        tier=tier,
        rationale=rationale,
        primary_provider=primary.provider,
        primary_model=primary.model or primary_model,
        requested_provider=requested_provider,
        requested_model=requested_model,
        route_plan=(primary, *fallback_steps),
        fallback_steps=fallback_steps,
        fallback_count=len(fallback_steps),
    )


def _build_lane_chain(
    settings: Settings,
    *,
    lane: RouteLane,
    tier: str,
    requested_provider: str | None,
    requested_model: str | None,
    default_provider: str,
    default_model: str,
) -> tuple[ChainStep, tuple[ChainStep, ...]]:
    lane_primary, lane_fallbacks = _lane_default_chain(settings, lane=lane, tier=tier)
    primary = ChainStep(
        requested_provider or lane_primary.provider,
        requested_model or lane_primary.model,
    )
    fallbacks = [step for step in lane_fallbacks if step.label != primary.label]

    if settings.anthropic_api_key:
        insert_at = 1 if lane == "fast" else 0
        anthropic_step = ChainStep("anthropic", settings.anthropic_model)
        if anthropic_step.label != primary.label and anthropic_step.label not in {step.label for step in fallbacks}:
            fallbacks.insert(insert_at, anthropic_step)

    if primary.label == lane_primary.label:
        return primary, tuple(fallbacks)

    if lane == "auto":
        return primary, tuple(fallbacks)

    fallback_chain = [lane_primary, *fallbacks]
    if primary.label in {step.label for step in fallback_chain}:
        fallback_chain = [step for step in fallback_chain if step.label != primary.label]
    return primary, tuple(fallback_chain)


def _lane_default_chain(settings: Settings, *, lane: RouteLane, tier: str) -> tuple[ChainStep, tuple[ChainStep, ...]]:
    normalized_tier = tier if lane == "auto" else _tier_for_lane(lane)[0]
    if settings.ollama_base_url:
        ollama_primary = ChainStep("ollama", settings.ollama_model)
        gemini_fallbacks = _gemini_fallbacks_for_tier(settings, normalized_tier)
        return ollama_primary, gemini_fallbacks
    if normalized_tier == "simple":
        primary = ChainStep("gemini", "gemini-2.5-flash-lite")
        fallbacks = [
            ChainStep("gemini", "gemini-2.5-flash"),
            ChainStep("gemini", "gemini-2.5-pro"),
            ChainStep("claude-cli", settings.claude_cli_model or "haiku"),
            ChainStep("codex-cli", settings.codex_cli_model or "gpt-5-mini"),
            ChainStep("gemini-cli", settings.gemini_cli_model or "gemini-2.5-flash"),
        ]
    elif normalized_tier == "deep":
        primary = ChainStep("gemini", "gemini-2.5-pro")
        fallbacks = [
            ChainStep("gemini", "gemini-2.5-flash"),
            ChainStep("gemini", "gemini-2.5-flash-lite"),
            ChainStep("claude-cli", settings.claude_cli_model or "sonnet"),
            ChainStep("codex-cli", settings.codex_cli_model or "gpt-5-codex"),
            ChainStep("gemini-cli", settings.gemini_cli_model or "gemini-2.5-pro"),
        ]
    else:
        primary = ChainStep("gemini", "gemini-2.5-flash")
        fallbacks = [
            ChainStep("gemini", "gemini-2.5-pro"),
            ChainStep("gemini", "gemini-2.5-flash-lite"),
            ChainStep("claude-cli", settings.claude_cli_model or "sonnet"),
            ChainStep("codex-cli", settings.codex_cli_model or "gpt-5"),
            ChainStep("gemini-cli", settings.gemini_cli_model or "gemini-2.5-flash"),
        ]
    return primary, tuple(fallbacks)


def _gemini_fallbacks_for_tier(settings: Settings, tier: str) -> tuple[ChainStep, ...]:
    if tier == "simple":
        return (
            ChainStep("gemini", "gemini-2.5-flash-lite"),
            ChainStep("gemini", "gemini-2.5-flash"),
        )
    if tier == "deep":
        return (
            ChainStep("gemini", "gemini-2.5-pro"),
            ChainStep("gemini", "gemini-2.5-flash"),
        )
    return (
        ChainStep("gemini", "gemini-2.5-flash"),
        ChainStep("gemini", "gemini-2.5-pro"),
    )


def _tier_for_lane(lane: RouteLane) -> tuple[str, str]:
    if lane == "deep":
        return "deep", "The deep lane was selected explicitly."
    if lane == "fast":
        return "simple", "The fast lane was selected explicitly."
    if lane == "balanced":
        return "standard", "The balanced lane was selected explicitly."
    return "standard", "A non-auto lane was not provided, so the balanced route was used."


def _normalize_route_lane(value: str) -> RouteLane:
    lane = value.strip().lower()
    if lane not in {"auto", "deep", "balanced", "fast"}:
        return "auto"
    return lane  # type: ignore[return-value]


def _classify_tier(last_user_text: str) -> tuple[str, str]:
    lowered = last_user_text.lower().strip()
    word_count = len(lowered.split())
    if not lowered:
        return "standard", "No user text found, so the standard route was used."
    if any(keyword in lowered for keyword in DEEP_KEYWORDS) or word_count >= 80 or "```" in lowered:
        return "deep", "The prompt looks codebase-heavy or planning-heavy, so the deep route was used."
    if word_count <= 12 and any(keyword in lowered for keyword in SIMPLE_KEYWORDS):
        return "simple", "The prompt looks lightweight, so the low-cost route was used first."
    return "standard", "The prompt looks like normal repo work, so the standard route was used."


def _extract_last_user_text(messages: Iterable[Message]) -> str:
    for message in reversed(list(messages)):
        role = str(getattr(message, "role", "")).lower()
        if role != "user":
            continue
        parts: list[str] = []
        for content in getattr(message, "contents", []):
            if isinstance(content, str):
                parts.append(content)
            elif getattr(content, "type", None) == "text":
                parts.append(str(content.text))
        if parts:
            return "\n".join(part for part in parts if part).strip()
    return ""
