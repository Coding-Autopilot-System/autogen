from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.auto_improver_loop import build_improver_payload, trigger_prompt_improver


class AutoImproverLoopTests(unittest.TestCase):
    def test_build_improver_payload_uses_prompt_and_error_files(self) -> None:
        run_dir = Path(tempfile.mkdtemp(prefix="auto-improver-run-"))
        payload = build_improver_payload(run_dir)
        self.assertEqual(run_dir.name, payload["run_id"])
        self.assertTrue(payload["original_prompt_file"].endswith("prompt.txt"))
        self.assertTrue(payload["error_trace_file"].endswith("error.log"))

    def test_trigger_prompt_improver_invokes_standalone_optimizer(self) -> None:
        payload = {
            "run_id": "repo-team",
            "original_prompt_file": "C:/repo/autogen/state/prompt.txt",
            "error_trace_file": "C:/repo/autogen/state/error.log",
        }
        improver_path = Path("/mnt/c/PersonalRepo/portfolio/Promptimprover")

        with patch("scripts.auto_improver_loop.subprocess.run") as run:
            trigger_prompt_improver(payload, improver_path)

        command = run.call_args.args[0]
        self.assertEqual(command[0], "node")
        self.assertTrue(command[1].endswith("optimize-prompt.mjs"))
        self.assertIn("--prompt-file", command)
        self.assertIn("--context-file", command)
        self.assertEqual(run.call_args.kwargs["cwd"], improver_path / "universal-refiner")


if __name__ == "__main__":
    unittest.main()
