from __future__ import annotations

import asyncio
from enum import Enum
from typing import Any, Awaitable, Callable

from maf_starter.telemetry import emit_failure_telemetry


class WorkerProfile(str, Enum):
    LOCAL = "local"
    CLOUD_SAFE = "cloud-safe"


_RunStatus = str  # "pending" | "running" | "done" | "error:<message>"


class WorkerBoundary:
    """Dispatch long-running workflow executions asynchronously so HTTP ingress
    returns a run_id immediately instead of waiting for the full execution path.

    Status values returned by get_status:
        "pending"       — task queued, not yet started
        "running"       — task is actively executing
        "done"          — task completed successfully
        "error:<msg>"   — task raised an exception; <msg> is str(exc)
    """

    def __init__(self, profile: WorkerProfile = WorkerProfile.LOCAL) -> None:
        self.profile = profile
        self._status: dict[str, _RunStatus] = {}
        self._tasks: dict[str, asyncio.Task[Any]] = {}

    def submit_async(
        self,
        run_id: str,
        workflow: Callable[[], Awaitable[Any]],
    ) -> str:
        """Dispatch *workflow* as a background asyncio task and return *run_id*
        immediately.  The caller never waits for the workflow to finish.

        Args:
            run_id:   Stable identifier for this run (caller's responsibility to
                      generate a unique value, e.g. via uuid.uuid4().hex).
            workflow: Zero-argument async callable that encapsulates the full
                      long-running execution path for this run.

        Returns:
            run_id — the same value passed in, ready for the HTTP response.
        """
        self._status[run_id] = "pending"
        task = asyncio.create_task(self._run(run_id, workflow))
        self._tasks[run_id] = task
        return run_id

    async def _run(self, run_id: str, workflow: Callable[[], Awaitable[Any]]) -> None:
        self._status[run_id] = "running"
        try:
            await workflow()
            self._status[run_id] = "done"
        except Exception as exc:  # noqa: BLE001
            self._status[run_id] = f"error:{exc}"
            emit_failure_telemetry("worker_task_failed", run_id=run_id, error=str(exc))

    def get_status(self, run_id: str) -> _RunStatus | None:
        """Return the current status string for *run_id*, or None if unknown."""
        return self._status.get(run_id)

    def is_done(self, run_id: str) -> bool:
        """Return True when the run has reached a terminal state (done or error)."""
        status = self._status.get(run_id)
        if status is None:
            return False
        return status == "done" or status.startswith("error:")

    def all_run_ids(self) -> tuple[str, ...]:
        """Return all known run IDs in submission order."""
        return tuple(self._status)
