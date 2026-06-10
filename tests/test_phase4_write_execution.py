from __future__ import annotations

import shutil
import subprocess
import unittest
import uuid
from pathlib import Path

from maf_starter.repo_execution import ChangeCaptureResult, WriteOperation, apply_write_operations


SCRATCH_ROOT = Path(__file__).resolve().parents[1] / ".tmp-tests"


def _git(args: list[str], *, cwd: Path) -> None:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=20,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise RuntimeError(detail)


def init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(["init"], cwd=path)
    (path / "README.md").write_text("# repo\n", encoding="utf-8")
    (path / "notes.txt").write_text("alpha\n", encoding="utf-8")
    _git(["add", "README.md", "notes.txt"], cwd=path)
    _git(
        [
            "-c",
            "user.name=Test User",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-m",
            "init",
        ],
        cwd=path,
    )


class Phase4WriteExecutionTests(unittest.TestCase):
    def make_scratch_dir(self) -> Path:
        path = SCRATCH_ROOT / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path

    def test_create_update_append_capture_changed_files_and_diff_patch(self) -> None:
        scratch = self.make_scratch_dir()
        repo_root = scratch / "repo"
        init_repo(repo_root)

        result = apply_write_operations(
            repo_root,
            [
                WriteOperation(action="create_file", path="src/new_module.py", content="print('hi')\n"),
                WriteOperation(action="update_file", path="README.md", content="# repo\n\nupdated\n"),
                WriteOperation(action="append_file", path="notes.txt", content="beta\n"),
            ],
        )

        self.assertIsInstance(result, ChangeCaptureResult)
        self.assertEqual(
            result.changed_files,
            ["README.md", "notes.txt", "src/new_module.py"],
        )
        self.assertEqual(len(result.write_operations), 3)
        self.assertTrue(any(record.action == "create_file" for record in result.write_operations))
        self.assertTrue(any(record.action == "update_file" for record in result.write_operations))
        self.assertTrue(any(record.action == "append_file" for record in result.write_operations))
        self.assertIn("a/README.md", result.diff_patch)
        self.assertIn("b/src/new_module.py", result.diff_patch)
        self.assertEqual((repo_root / "src" / "new_module.py").read_text(encoding="utf-8"), "print('hi')\n")
        self.assertEqual((repo_root / "notes.txt").read_text(encoding="utf-8"), "alpha\nbeta\n")

    def test_blocked_paths_are_rejected_before_write(self) -> None:
        scratch = self.make_scratch_dir()
        repo_root = scratch / "repo"
        init_repo(repo_root)

        with self.assertRaisesRegex(ValueError, "blocked"):
            apply_write_operations(
                repo_root,
                [WriteOperation(action="create_file", path=".env", content="SECRET=1\n")],
            )

        with self.assertRaisesRegex(ValueError, "escapes"):
            apply_write_operations(
                repo_root,
                [WriteOperation(action="create_file", path="..\\outside.txt", content="nope\n")],
            )

    def test_update_with_same_content_is_skipped_but_preserves_result_shape(self) -> None:
        scratch = self.make_scratch_dir()
        repo_root = scratch / "repo"
        init_repo(repo_root)

        result = apply_write_operations(
            repo_root,
            [WriteOperation(action="update_file", path="README.md", content="# repo\n")],
        )

        self.assertEqual(result.changed_files, [])
        self.assertEqual(len(result.write_operations), 1)
        self.assertEqual(result.write_operations[0].status, "skipped")
        self.assertFalse(result.write_operations[0].changed)
        self.assertEqual(result.diff_patch, "")


    def test_write_operations_are_utf8_only_and_leave_no_temp_files(self) -> None:
        scratch = self.make_scratch_dir()
        repo_root = scratch / "repo"
        init_repo(repo_root)

        with self.assertRaisesRegex(ValueError, "UTF-8"):
            apply_write_operations(
                repo_root,
                [WriteOperation(action="update_file", path="README.md", content="changed", encoding="utf-16")],
            )

        self.assertEqual((repo_root / "README.md").read_text(encoding="utf-8"), "# repo\n")
        self.assertEqual(list(repo_root.rglob("*.tmp")), [])

if __name__ == "__main__":
    unittest.main()
