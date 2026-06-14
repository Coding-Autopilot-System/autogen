from __future__ import annotations

import asyncio
import unittest

from maf_starter.worker_boundary import WorkerBoundary, WorkerProfile


class WorkerProfileTests(unittest.TestCase):
    def test_profile_values(self) -> None:
        self.assertEqual(WorkerProfile.LOCAL.value, "local")
        self.assertEqual(WorkerProfile.CLOUD_SAFE.value, "cloud-safe")

    def test_profile_is_string_enum(self) -> None:
        self.assertIsInstance(WorkerProfile.LOCAL, str)
        self.assertEqual(WorkerProfile.LOCAL, "local")

    def test_profile_round_trips_from_value(self) -> None:
        self.assertEqual(WorkerProfile("local"), WorkerProfile.LOCAL)
        self.assertEqual(WorkerProfile("cloud-safe"), WorkerProfile.CLOUD_SAFE)


class WorkerBoundaryTests(unittest.IsolatedAsyncioTestCase):
    def test_default_profile_is_local(self) -> None:
        boundary = WorkerBoundary()
        self.assertEqual(boundary.profile, WorkerProfile.LOCAL)

    def test_submit_async_returns_run_id_immediately(self) -> None:
        boundary = WorkerBoundary()

        async def _inner():
            async def slow():
                await asyncio.sleep(10)

            run_id = boundary.submit_async("run-1", slow)
            self.assertEqual(run_id, "run-1")
            # Cancel the pending task to avoid leaking coroutines
            task = boundary._tasks.get("run-1")
            if task:
                task.cancel()
                try:
                    await task
                except (asyncio.CancelledError, Exception):
                    pass

        asyncio.run(_inner())

    async def test_status_starts_as_pending_then_running_then_done(self) -> None:
        boundary = WorkerBoundary()
        reached_running: asyncio.Event = asyncio.Event()
        proceed: asyncio.Event = asyncio.Event()

        async def controlled_workflow():
            reached_running.set()
            await proceed.wait()

        run_id = boundary.submit_async("run-2", controlled_workflow)
        self.assertEqual(run_id, "run-2")

        # Yield control so the task can start
        await asyncio.sleep(0)
        await reached_running.wait()
        self.assertEqual(boundary.get_status("run-2"), "running")
        self.assertFalse(boundary.is_done("run-2"))

        proceed.set()
        # Yield so the task can finish
        await asyncio.sleep(0)
        self.assertEqual(boundary.get_status("run-2"), "done")
        self.assertTrue(boundary.is_done("run-2"))

    async def test_status_records_error_on_exception(self) -> None:
        boundary = WorkerBoundary()

        async def failing_workflow():
            raise ValueError("something went wrong")

        boundary.submit_async("run-3", failing_workflow)
        # Yield so the task can run and fail
        await asyncio.sleep(0)

        status = boundary.get_status("run-3")
        assert status is not None
        self.assertTrue(status.startswith("error:"), f"Expected error: prefix, got: {status!r}")
        self.assertIn("something went wrong", status)
        self.assertTrue(boundary.is_done("run-3"))

    def test_get_status_returns_none_for_unknown_run(self) -> None:
        boundary = WorkerBoundary()
        self.assertIsNone(boundary.get_status("nonexistent"))

    async def test_all_run_ids_tracks_submissions_in_order(self) -> None:
        boundary = WorkerBoundary()
        finished: asyncio.Event = asyncio.Event()

        async def quick():
            finished.set()

        boundary.submit_async("r1", quick)
        boundary.submit_async("r2", quick)
        boundary.submit_async("r3", quick)

        self.assertEqual(boundary.all_run_ids(), ("r1", "r2", "r3"))
        # Clean up
        await asyncio.sleep(0)

    def test_boundary_accepts_cloud_safe_profile(self) -> None:
        boundary = WorkerBoundary(profile=WorkerProfile.CLOUD_SAFE)
        self.assertEqual(boundary.profile, WorkerProfile.CLOUD_SAFE)


if __name__ == "__main__":
    unittest.main()
