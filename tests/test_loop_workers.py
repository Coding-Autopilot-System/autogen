from __future__ import annotations

import asyncio
import unittest

from maf_starter.loop_workers import (
    REQUIRED_SPECIALIST_ROLES,
    SpecialistResult,
    SpecialistSpec,
    aggregate_specialist_results,
    build_maf_fanout_workflow,
    run_bounded_specialists,
)


class LoopWorkerTests(unittest.IsolatedAsyncioTestCase):
    async def test_four_roles_run_with_peak_concurrency_three_and_complete_fan_in(self) -> None:
        active = 0
        peak = 0
        lock = asyncio.Lock()

        async def execute(spec: SpecialistSpec) -> SpecialistResult:
            nonlocal active, peak
            async with lock:
                active += 1
                peak = max(peak, active)
            await asyncio.sleep(0.05)
            async with lock:
                active -= 1
            return SpecialistResult(spec.role, "succeeded", f"{spec.role} complete", ())

        aggregate = await run_bounded_specialists(
            [SpecialistSpec(role) for role in REQUIRED_SPECIALIST_ROLES],
            execute,
            max_fan_out=3,
            timeout_seconds=2,
        )

        self.assertEqual(peak, 3)
        self.assertEqual(tuple(result.role for result in aggregate.results), REQUIRED_SPECIALIST_ROLES)
        self.assertTrue(aggregate.complete)

    async def test_timeout_is_terminal_failure_not_partial_success(self) -> None:
        async def execute(spec: SpecialistSpec) -> SpecialistResult:
            await asyncio.sleep(1)
            return SpecialistResult(spec.role, "succeeded", "late", ())

        with self.assertRaises(TimeoutError):
            await run_bounded_specialists(
                [SpecialistSpec(role) for role in REQUIRED_SPECIALIST_ROLES],
                execute,
                max_fan_out=3,
                timeout_seconds=0.01,
            )

    def test_aggregator_rejects_missing_duplicate_or_nonterminal_results(self) -> None:
        complete = [SpecialistResult(role, "succeeded", "ok", ()) for role in REQUIRED_SPECIALIST_ROLES]
        with self.assertRaises(ValueError):
            aggregate_specialist_results(complete[:-1])
        with self.assertRaises(ValueError):
            aggregate_specialist_results([*complete, complete[0]])
        with self.assertRaises(ValueError):
            aggregate_specialist_results([*complete[:-1], SpecialistResult("test", "running", "", ())])

    def test_specialist_specs_are_read_only_and_maf_builder_uses_native_fan_edges(self) -> None:
        specs = [SpecialistSpec(role) for role in REQUIRED_SPECIALIST_ROLES]
        self.assertTrue(all(spec.read_only for spec in specs))
        self.assertTrue(all("write" not in spec.capabilities for spec in specs))

        class BuilderSpy:
            def __init__(self) -> None:
                self.fan_out = None
                self.fan_in = None
            def add_fan_out_edges(self, source, targets):
                self.fan_out = (source, tuple(targets))
                return self
            def add_fan_in_edges(self, sources, target):
                self.fan_in = (tuple(sources), target)
                return self
            def build(self):
                return self

        builder = BuilderSpy()
        result = build_maf_fanout_workflow("dispatcher", [1, 2, 3, 4], "aggregator", builder=builder)
        self.assertIs(result, builder)
        self.assertEqual(builder.fan_out, ("dispatcher", (1, 2, 3, 4)))
        self.assertEqual(builder.fan_in, ((1, 2, 3, 4), "aggregator"))


if __name__ == "__main__":
    unittest.main()
