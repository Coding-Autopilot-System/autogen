import asyncio
import io
import json
import sys
import unittest
from contextlib import redirect_stderr
from unittest.mock import patch

from maf_starter.loop_worker_cli import MAX_REQUEST_BYTES, execute_request, main


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

    def test_cli_rejects_oversized_stdin_before_json_parsing(self) -> None:
        oversized = json.dumps({"padding": "x" * MAX_REQUEST_BYTES})
        stderr = io.StringIO()

        with (
            patch.object(sys, "argv", ["loop_worker_cli"]),
            patch.object(sys, "stdin", io.StringIO(oversized)),
            redirect_stderr(stderr),
        ):
            exit_code = main()

        self.assertEqual(2, exit_code)
        self.assertIn("exceeds", stderr.getvalue())
