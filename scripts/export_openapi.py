"""Export the autogen_dashboard FastAPI OpenAPI spec to openapi.json."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from autogen_dashboard.app import app  # noqa: E402

OUTPUT = REPO_ROOT / "openapi.json"


def main() -> None:
    spec = app.openapi()
    with OUTPUT.open("w", encoding="utf-8") as f:
        json.dump(spec, f, indent=2, ensure_ascii=False)
        f.write("\n")
    paths = len(spec.get("paths", {}))
    schemas = len(spec.get("components", {}).get("schemas", {}))
    print(f"Exported OpenAPI {spec.get('openapi')} spec: {OUTPUT}")
    print(f"  {paths} paths, {schemas} schemas")


if __name__ == "__main__":
    main()
