from __future__ import annotations

import argparse
from pathlib import Path
import sys

from maf_starter.critic import run_critic


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="critic", description="Run the Resilience First peer critic against a unified diff")
    parser.add_argument("--diff", required=True, help="Diff file path or '-' to read from stdin")
    parser.add_argument(
        "--severity-gate",
        choices=("blocking", "advisory"),
        default="blocking",
        help="Exit non-zero on blocking findings only, or on any finding in advisory mode",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.diff == "-":
            diff_text = sys.stdin.read()
        else:
            diff_text = Path(args.diff).read_text(encoding="utf-8", errors="replace")
    except (FileNotFoundError, OSError) as exc:
        print(f"critic: unable to read diff: {exc}", file=sys.stderr)
        return 2

    report = run_critic(diff_text)
    for finding in report.findings:
        print(f"{finding.file}:{finding.line or '-'} [{finding.severity}] {finding.check} - {finding.detail}")
    print(f"critic: {report.blocking_count} blocking, {report.advisory_count} advisory")

    if args.severity_gate == "advisory":
        return 1 if (report.blocking_count + report.advisory_count) > 0 else 0
    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
