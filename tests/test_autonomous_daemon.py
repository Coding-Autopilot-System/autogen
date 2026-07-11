from __future__ import annotations

import importlib.util
import os
import shutil
import unittest
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, patch


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRATCH_ROOT = REPO_ROOT / ".tmp-tests"

_MODULE_SPEC = importlib.util.spec_from_file_location(
    "autonomous_daemon_module",
    REPO_ROOT / "scripts" / "autonomous_daemon.py",
)
assert _MODULE_SPEC and _MODULE_SPEC.loader
autonomous_daemon = importlib.util.module_from_spec(_MODULE_SPEC)
_MODULE_SPEC.loader.exec_module(autonomous_daemon)


class AutonomousDaemonTests(unittest.IsolatedAsyncioTestCase):
    def make_scratch_dir(self) -> Path:
        path = SCRATCH_ROOT / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path

    async def test_run_once_propagates_process_errors(self) -> None:
        root = self.make_scratch_dir()
        previous_cwd = Path.cwd()
        os.chdir(root)
        self.addCleanup(lambda: os.chdir(previous_cwd))

        with patch.object(autonomous_daemon, "process_inbox", new=AsyncMock(side_effect=RuntimeError("boom"))):
            with patch.object(autonomous_daemon, "log"):
                with self.assertRaises(RuntimeError):
                    await autonomous_daemon.run_daemon(run_once=True)

    async def test_run_once_processes_single_cycle(self) -> None:
        root = self.make_scratch_dir()
        previous_cwd = Path.cwd()
        os.chdir(root)
        self.addCleanup(lambda: os.chdir(previous_cwd))

        with patch.object(autonomous_daemon, "process_inbox", new=AsyncMock()) as process_inbox:
            with patch.object(autonomous_daemon, "log"):
                await autonomous_daemon.run_daemon(run_once=True)

        process_inbox.assert_awaited_once()

    def test_extract_pending_plan_precedes_frontier_mode(self) -> None:
        roadmap = """
- [x] **Phase 9: GSD Autonomous Bridge** - Connect roadmap to daemon

Plans:
- [ ] 09-01: Implement Roadmap parser and automatic phase-to-inbox injection in `autonomous_daemon.py`
"""
        self.assertEqual(
            ("09-01", "Implement Roadmap parser and automatic phase-to-inbox injection in `autonomous_daemon.py`"),
            autonomous_daemon._extract_pending_plan(roadmap),
        )
        self.assertIsNone(autonomous_daemon._extract_pending_phase(roadmap))

    def test_frontier_task_uses_active_checkboxes(self) -> None:
        root = self.make_scratch_dir()
        task_path = root / "gsd-frontier-planner.md"
        autonomous_daemon._build_frontier_task(task_path)
        content = task_path.read_text(encoding="utf-8")
        self.assertIn("active `[ ]` checkboxes, not `[?]`", content)
        self.assertNotIn("human operator can approve", content)

    def test_mark_plan_complete_updates_roadmap(self) -> None:
        root = self.make_scratch_dir()
        roadmap_path = root / "ROADMAP.md"
        roadmap_path.write_text(
            "Plans:\n- [ ] 09-01: Implement parser\n",
            encoding="utf-8",
        )

        label = autonomous_daemon._mark_roadmap_item_complete(roadmap_path, file_name="gsd-plan-09-01.md")

        self.assertEqual("Plan 09-01", label)
        self.assertIn("- [x] 09-01: Implement parser", roadmap_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
