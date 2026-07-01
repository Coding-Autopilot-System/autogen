import asyncio
import unittest

from maf_starter.loop_worker_cli import execute_request


class LoopWorkerCliTests(unittest.TestCase):
    def test_cli_request_executes_real_bounded_specialist_runtime(self) -> None:
        result = asyncio.run(
            execute_request(
                {
                    "goalId": "goal-1",
                    "workItemId": "work-1",
                    "attempt": 1,
                    "isRepair": False,
                    "correlationId": "corr-1",
                }
            )
        )

        self.assertTrue(result.succeeded)
        self.assertEqual(3, result.peakConcurrency)
        self.assertEqual(("research", "architecture", "security", "test"), result.roles)
        self.assertEqual(4, len(result.evidenceUris))
