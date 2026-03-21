from __future__ import annotations

import shutil
import subprocess
import unittest
import uuid
from pathlib import Path

from maf_starter.validation_runner import ValidationPlan, ValidationResult, execute_validation_plan, plan_validation


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
    (path / "maf_starter").mkdir(parents=True, exist_ok=True)
    (path / "maf_starter" / "example.py").write_text("def ok() -> int:\n    return 1\n", encoding="utf-8")
    (path / "autogen_dashboard" / "static").mkdir(parents=True, exist_ok=True)
    (path / "autogen_dashboard" / "static" / "app.js").write_text("const ready = true;\n", encoding="utf-8")
    (path / "tests").mkdir(parents=True, exist_ok=True)
    (path / "tests" / "test_placeholder.py").write_text(
        "import unittest\n\n\nclass Placeholder(unittest.TestCase):\n    def test_ok(self):\n        self.assertTrue(True)\n",
        encoding="utf-8",
    )
    _git(["add", "."], cwd=path)
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


class Phase4ValidationTests(unittest.TestCase):
    def make_scratch_dir(self) -> Path:
        path = SCRATCH_ROOT / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=False)
        self.addCleanup(lambda: shutil.rmtree(path, ignore_errors=True))
        return path

    def test_plan_validation_selects_safe_command_ladder(self) -> None:
        scratch = self.make_scratch_dir()
        repo_root = scratch / "repo"
        init_repo(repo_root)

        plan = plan_validation(
            repo_root,
            [
                "maf_starter/example.py",
                "tests/test_placeholder.py",
                "autogen_dashboard/static/app.js",
            ],
        )

        self.assertIsInstance(plan, ValidationPlan)
        labels = [command.label for command in plan.commands]
        self.assertIn("git diff --check", labels)
        self.assertIn("python -m compileall", labels)
        self.assertIn("python -m unittest discover -s tests -v", labels)
        self.assertIn("node --check autogen_dashboard/static/app.js", labels)

    def test_execute_validation_plan_records_result_shape(self) -> None:
        scratch = self.make_scratch_dir()
        repo_root = scratch / "repo"
        init_repo(repo_root)

        plan = plan_validation(
            repo_root,
            [
                "maf_starter/example.py",
                "tests/test_placeholder.py",
                "autogen_dashboard/static/app.js",
            ],
        )
        results = execute_validation_plan(plan)

        self.assertTrue(results)
        self.assertTrue(all(isinstance(item, ValidationResult) for item in results))
        self.assertTrue(all(item.cwd == str(repo_root.resolve()) for item in results))
        self.assertTrue(all(item.status == "passed" for item in results))
        self.assertTrue(any("git diff --check" in " ".join(item.command) for item in results))
        self.assertTrue(any(item.output_summary for item in results))


if __name__ == "__main__":
    unittest.main()
