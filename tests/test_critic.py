from __future__ import annotations

import io
from pathlib import Path
import textwrap

import pytest

from maf_starter.critic import (
    check_bare_except,
    check_file_size_limit,
    check_missing_telemetry,
    parse_unified_diff,
    run_critic,
)
from maf_starter.critic_cli import build_parser, main


DIRTY_DIFF = textwrap.dedent(
    """\
    diff --git a/app.py b/app.py
    +++ b/app.py
    @@
    +try:
    +    do_work()
    +except Exception:
    +    pass
    """
)

DIRTY_DIFF_WITH_TELEMETRY_GAP = textwrap.dedent(
    """\
    diff --git a/app.py b/app.py
    +++ b/app.py
    @@
    +try:
    +    do_work()
    +except ValueError:
    +    recover()
    """
)

CLEAN_DIFF = textwrap.dedent(
    """\
    diff --git a/app.py b/app.py
    +++ b/app.py
    @@
    +try:
    +    do_work()
    +except Exception as exc:
    +    logger.error("failed", exc_info=exc)
    +    raise RuntimeError("typed failure") from exc
    """
)


def test_parse_unified_diff_returns_changed_files_and_added_lines() -> None:
    diff_text = textwrap.dedent(
        """\
        diff --git a/app.py b/app.py
        +++ b/app.py
        @@
        +first
        diff --git a/worker.py b/worker.py
        +++ b/worker.py
        @@
        +second
        """
    )

    files = parse_unified_diff(diff_text)

    assert len(files) == 2
    assert files[0].path == "app.py"
    assert files[0].added_lines == ["first"]
    assert files[1].path == "worker.py"
    assert files[1].added_lines == ["second"]


def test_check_bare_except_blocks_untyped_unlogged_handler() -> None:
    findings = check_bare_except("app.py", ["except Exception:", "    pass"])

    assert len(findings) == 1
    assert findings[0].check == "bare-except"
    assert findings[0].severity == "blocking"


def test_check_bare_except_allows_logged_typed_reraise() -> None:
    findings = check_bare_except(
        "app.py",
        [
            "except Exception as exc:",
            '    logger.error("boom", exc_info=exc)',
            '    raise RuntimeError("typed failure") from exc',
        ],
    )

    assert findings == []


def test_check_missing_telemetry_returns_advisory_only() -> None:
    findings = check_missing_telemetry("app.py", ["except ValueError:", "    recover()"])

    assert len(findings) == 1
    assert findings[0].check == "missing-telemetry"
    assert findings[0].severity == "advisory"


def test_check_file_size_limit_flags_large_files() -> None:
    findings = check_file_size_limit("big.py", 401, limit=400)

    assert len(findings) == 1
    assert findings[0].check == "file-size-limit"
    assert findings[0].severity == "advisory"


def test_run_critic_blocks_dirty_diff() -> None:
    report = run_critic(DIRTY_DIFF)

    assert report.exit_code == 1
    assert report.blocking_count == 1
    assert any(finding.check == "bare-except" for finding in report.findings)


def test_run_critic_passes_clean_diff() -> None:
    report = run_critic(CLEAN_DIFF)

    assert report.exit_code == 0
    assert report.blocking_count == 0
    assert report.advisory_count == 0


def test_run_critic_returns_advisory_error_on_malformed_input() -> None:
    report = run_critic("not a diff at all")

    assert report.exit_code == 0
    assert report.blocking_count == 0
    assert report.advisory_count == 1
    assert report.findings[0].check == "critic-error"


def test_build_parser_defaults_to_blocking_gate() -> None:
    args = build_parser().parse_args(["--diff", "-"])

    assert args.diff == "-"
    assert args.severity_gate == "blocking"


def test_main_returns_zero_for_clean_diff_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    diff_path = tmp_path / "clean.diff"
    diff_path.write_text(CLEAN_DIFF, encoding="utf-8")

    exit_code = main(["--diff", str(diff_path)])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "critic: 0 blocking, 0 advisory" in out


def test_main_returns_one_for_blocking_diff_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    diff_path = tmp_path / "dirty.diff"
    diff_path.write_text(DIRTY_DIFF, encoding="utf-8")

    exit_code = main(["--diff", str(diff_path)])

    out = capsys.readouterr().out
    assert exit_code == 1
    assert "[blocking] bare-except" in out


def test_main_returns_two_for_missing_diff_path(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--diff", "missing.diff"])

    err = capsys.readouterr().err
    assert exit_code == 2
    assert "unable to read diff" in err


def test_main_reads_diff_from_stdin_and_supports_advisory_gate(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(DIRTY_DIFF_WITH_TELEMETRY_GAP))

    exit_code = main(["--diff", "-", "--severity-gate", "advisory"])

    out = capsys.readouterr().out
    assert exit_code == 1
    assert "critic: 0 blocking, 1 advisory" in out
