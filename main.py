from __future__ import annotations

import sys


def _dispatch() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "smoke":
        from maf_starter.cli import main as maf_main
        return maf_main()
    from autogen_starter.cli import main as legacy_main
    return legacy_main()


if __name__ == "__main__":
    raise SystemExit(_dispatch())
