from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from typing import Any, Literal


REQUIRED_SPECIALIST_ROLES = ("research", "architecture", "security", "test")
TerminalStatus = Literal["succeeded", "failed", "cancelled", "timed_out"]


@dataclass(frozen=True)
class SpecialistSpec:
    role: str
    read_only: bool = True
    capabilities: tuple[str, ...] = ("read_repo", "search_repo")

    def __post_init__(self) -> None:
        if self.role not in REQUIRED_SPECIALIST_ROLES:
            raise ValueError(f"Unsupported specialist role: {self.role}")
        if not self.read_only or any(capability.startswith(("write", "delete", "execute")) for capability in self.capabilities):
            raise ValueError("Specialists must remain read-only")


@dataclass(frozen=True)
class SpecialistResult:
    role: str
    status: str
    summary: str
    artifacts: tuple[str, ...]


@dataclass(frozen=True)
class SpecialistAggregate:
    results: tuple[SpecialistResult, ...]

    @property
    def complete(self) -> bool:
        return all(result.status == "succeeded" for result in self.results)


def aggregate_specialist_results(results: Sequence[SpecialistResult]) -> SpecialistAggregate:
    by_role: dict[str, SpecialistResult] = {}
    for result in results:
        if result.role in by_role:
            raise ValueError(f"Duplicate specialist result: {result.role}")
        if result.status not in {"succeeded", "failed", "cancelled", "timed_out"}:
            raise ValueError(f"Specialist result is not terminal: {result.role}")
        by_role[result.role] = result
    missing = set(REQUIRED_SPECIALIST_ROLES) - set(by_role)
    extra = set(by_role) - set(REQUIRED_SPECIALIST_ROLES)
    if missing or extra:
        raise ValueError(f"Specialist fan-in mismatch; missing={sorted(missing)}, extra={sorted(extra)}")
    return SpecialistAggregate(tuple(by_role[role] for role in REQUIRED_SPECIALIST_ROLES))


async def run_bounded_specialists(
    specs: Sequence[SpecialistSpec],
    execute: Callable[[SpecialistSpec], Awaitable[SpecialistResult]],
    *,
    max_fan_out: int = 3,
    timeout_seconds: float = 1800,
) -> SpecialistAggregate:
    if max_fan_out < 1:
        raise ValueError("max_fan_out must be positive")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    roles = tuple(spec.role for spec in specs)
    if len(set(roles)) != len(roles) or set(roles) != set(REQUIRED_SPECIALIST_ROLES):
        raise ValueError("Exactly one specialist for every required role is required")

    semaphore = asyncio.Semaphore(max_fan_out)

    async def invoke(spec: SpecialistSpec) -> SpecialistResult:
        async with semaphore:
            result = await execute(spec)
            if result.role != spec.role:
                raise ValueError(f"Specialist {spec.role} returned result for {result.role}")
            return result

    try:
        async with asyncio.timeout(timeout_seconds):
            results = await asyncio.gather(*(invoke(spec) for spec in specs))
    except TimeoutError:
        raise TimeoutError("Specialist fan-out exceeded its task-attempt deadline") from None
    return aggregate_specialist_results(results)


def build_maf_fanout_workflow(
    dispatcher: Any,
    specialists: Sequence[Any],
    aggregator: Any,
    *,
    builder: Any | None = None,
    max_iterations: int = 3,
) -> Any:
    if len(specialists) != len(REQUIRED_SPECIALIST_ROLES):
        raise ValueError("MAF workflow requires all four specialist executors")
    if builder is None:
        from agent_framework import WorkflowBuilder

        builder = WorkflowBuilder(
            start_executor=dispatcher,
            max_iterations=max_iterations,
            name="cas_task_worker",
            description="Bounded read-only specialist fan-out with typed terminal fan-in",
        )
    return builder.add_fan_out_edges(dispatcher, specialists).add_fan_in_edges(specialists, aggregator).build()
