from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any


def emit_failure_telemetry(event: str, **fields: Any) -> None:
    payload = {
        "event": event,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    try:
        sys.stderr.write(json.dumps(payload, separators=(",", ":")) + "\n")
        sys.stderr.flush()
    except Exception:  # pragma: no cover - telemetry must never mask the original failure
        return
