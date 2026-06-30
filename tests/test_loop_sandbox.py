from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from maf_starter.approval_policy import classify_external_action, require_action_approval
from maf_starter.loop_sandbox import GitWorktreeSandbox, MutationContract


class LoopSandboxTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="cas-sandbox-"))
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self._git("init", "-b", "main")
        self._git("config", "user.email", "test@example.invalid")
        self._git("config", "user.name", "CAS Test")
        (self.repo / "README.md").write_text("baseline\n", encoding="utf-8")
        self._git("add", "README.md")
        self._git("commit", "-m", "baseline")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def test_mutating_item_gets_distinct_worktree_manifest_and_preserves_default_sha(self) -> None:
        before = self._git("rev-parse", "main").stdout.strip()
        contract = self._contract()
        sandbox = GitWorktreeSandbox(contract)

        manifest = sandbox.create()
        sandbox.authorize_mutation("implementer")
        target = sandbox.resolve_write_path("src/change.txt")
        target.parent.mkdir(parents=True)
        target.write_text("change\n", encoding="utf-8")
        artifact = sandbox.capture_artifacts()

        self.assertTrue(contract.worktree_path.is_dir())
        self.assertNotEqual(contract.worktree_path.resolve(), self.repo.resolve())
        self.assertEqual(manifest.base_sha, before)
        self.assertEqual(artifact.changed_files, ("src/change.txt",))
        self.assertEqual(self._git("rev-parse", "main").stdout.strip(), before)
        self.assertEqual(artifact.idempotency_key, "goal-1:work-1")

    def test_owner_deadline_and_path_allowlist_are_enforced(self) -> None:
        sandbox = GitWorktreeSandbox(self._contract())
        sandbox.create()
        with self.assertRaises(PermissionError):
            sandbox.authorize_mutation("research")
        with self.assertRaises(ValueError):
            sandbox.resolve_write_path("../escape.txt")
        with self.assertRaises(ValueError):
            sandbox.resolve_write_path("secrets/token.txt")
        with self.assertRaises(TimeoutError):
            GitWorktreeSandbox(self._contract(deadline=datetime.now(UTC) - timedelta(seconds=1))).create()

    def test_external_and_destructive_actions_cannot_run_before_approval(self) -> None:
        for action in ("push", "deploy", "delete", "message", "production_mutation"):
            decision = classify_external_action(action, "target")
            self.assertTrue(decision.approval_required, action)
            with self.assertRaises(PermissionError):
                require_action_approval(action, "target", approved=False)
            require_action_approval(action, "target", approved=True)

    def _contract(self, *, deadline: datetime | None = None) -> MutationContract:
        return MutationContract(
            goal_id="goal-1",
            work_item_id="work-1",
            repo_root=self.repo,
            worktree_path=self.root / "worktrees" / "goal-1" / "work-1",
            base_ref="main",
            deadline=deadline or datetime.now(UTC) + timedelta(minutes=5),
            path_allowlist=("src/**",),
            idempotency_key="goal-1:work-1",
            implementation_owner="implementer",
        )

    def _git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True, text=True)


if __name__ == "__main__":
    unittest.main()
