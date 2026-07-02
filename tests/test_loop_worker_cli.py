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
                    "contract": {
                        "contractId": "goal-1:work-1:attempt-1",
                        "contextBundleId": "corr-1:work-1:feature:1",
                        "objective": "Produce bounded specialist analysis",
                        "downstreamConsumer": "loop_verifier",
                        "outputSchema": "cas.loop.step-result.v1",
                        "toolScope": {
                            "mutationAllowed": False,
                            "mutationOwner": "implementation-owner",
                            "allowedTools": ["read_repo", "search_repo"],
                        },
                        "fanOut": {
                            "maxConcurrency": 3,
                            "requiredRoles": ["research", "architecture", "security", "test"],
                            "aggregatorRole": "loop_verifier",
                        },
                        "inputs": [{"name": "goalId", "value": "goal-1"}],
                        "completionCriteria": [{"id": "all-terminal", "description": "All roles terminal", "mandatory": True}],
                    },
                }
            )
        )

        self.assertTrue(result.succeeded)
        self.assertEqual(3, result.peakConcurrency)
        self.assertEqual(("research", "architecture", "security", "test"), result.roles)
        self.assertEqual(4, len(result.evidenceUris))
        self.assertEqual("goal-1:work-1:attempt-1", result.contractId)
        self.assertEqual("corr-1:work-1:feature:1", result.contextBundleId)
        self.assertEqual("cas.loop.step-result.v1", result.outputSchema)

    def test_cli_request_rejects_missing_or_mutating_contract(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing worker request fields: contract"):
            asyncio.run(execute_request({"goalId": "goal-1", "workItemId": "work-1", "attempt": 1, "isRepair": False, "correlationId": "corr-1"}))

        with self.assertRaisesRegex(ValueError, "read-only"):
            asyncio.run(
                execute_request(
                    {
                        "goalId": "goal-1",
                        "workItemId": "work-1",
                        "attempt": 1,
                        "isRepair": False,
                        "correlationId": "corr-1",
                        "contract": {
                            "contractId": "goal-1:work-1:attempt-1",
                            "contextBundleId": "corr-1:work-1:feature:1",
                            "objective": "bad contract",
                            "downstreamConsumer": "loop_verifier",
                            "outputSchema": "cas.loop.step-result.v1",
                            "toolScope": {
                                "mutationAllowed": True,
                                "mutationOwner": "implementation-owner",
                                "allowedTools": ["read_repo", "write_repo"],
                            },
                            "fanOut": {
                                "maxConcurrency": 3,
                                "requiredRoles": ["research", "architecture", "security", "test"],
                                "aggregatorRole": "loop_verifier",
                            },
                            "inputs": [{"name": "goalId", "value": "goal-1"}],
                            "completionCriteria": [{"id": "all-terminal", "description": "All roles terminal", "mandatory": True}],
                        },
                    }
                )
            )
