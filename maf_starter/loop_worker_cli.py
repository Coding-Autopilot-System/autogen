from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any

from maf_starter.loop_workers import (
    REQUIRED_SPECIALIST_ROLES,
    SpecialistResult,
    SpecialistSpec,
    run_bounded_specialists,
)

MAX_REQUEST_BYTES = 1_000_000


@dataclass(frozen=True)
class WorkerEnvelope:
    succeeded: bool
    peakConcurrency: int
    roles: tuple[str, ...]
    evidenceUris: tuple[str, ...]
    summary: str


async def execute_request(payload: dict[str, Any]) -> WorkerEnvelope:
    required = ("goalId", "workItemId", "attempt", "isRepair", "correlationId")
    missing = [name for name in required if name not in payload]
    if missing:
        raise ValueError(f"Missing worker request fields: {', '.join(missing)}")

    active = 0
    peak = 0
    lock = asyncio.Lock()

    async def execute(spec: SpecialistSpec) -> SpecialistResult:
        nonlocal active, peak
        async with lock:
            active += 1
            peak = max(peak, active)
        try:
            await asyncio.sleep(0.01)
            uri = f"cas://evidence/worker/{payload['goalId']}/{payload['attempt']}/{spec.role}"
            return SpecialistResult(spec.role, "succeeded", f"{spec.role} analysis complete", (uri,))
        finally:
            async with lock:
                active -= 1

    aggregate = await run_bounded_specialists(
        [SpecialistSpec(role) for role in REQUIRED_SPECIALIST_ROLES],
        execute,
        max_fan_out=3,
        timeout_seconds=30,
    )
    evidence = tuple(uri for result in aggregate.results for uri in result.artifacts)
    return WorkerEnvelope(
        aggregate.complete,
        peak,
        tuple(result.role for result in aggregate.results),
        evidence,
        "repair fan-out completed" if payload["isRepair"] else "feature fan-out completed",
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", help="JSON worker request; stdin is used when omitted")
    args = parser.parse_args()
    try:
        if args.request is not None:
            request_text = args.request
            request_size = len(request_text.encode("utf-8"))
        else:
            request_text = sys.stdin.read(MAX_REQUEST_BYTES + 1)
            request_size = len(request_text.encode("utf-8"))
        if request_size > MAX_REQUEST_BYTES:
            raise ValueError(f"Worker request exceeds {MAX_REQUEST_BYTES} bytes")
        payload = json.loads(request_text)
        result = asyncio.run(execute_request(payload))
    except (ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(asdict(result), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
