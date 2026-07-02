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


@dataclass(frozen=True)
class WorkerEnvelope:
    succeeded: bool
    peakConcurrency: int
    roles: tuple[str, ...]
    evidenceUris: tuple[str, ...]
    summary: str
    contractId: str
    contextBundleId: str
    outputSchema: str


def _validate_step_contract(payload: dict[str, Any]) -> tuple[dict[str, Any], tuple[str, ...]]:
    contract = payload.get("contract")
    if not isinstance(contract, dict):
        raise ValueError("Worker request must include a contract object")
    required = (
        "contractId",
        "contextBundleId",
        "objective",
        "downstreamConsumer",
        "outputSchema",
        "toolScope",
        "fanOut",
        "inputs",
        "completionCriteria",
    )
    missing = [name for name in required if name not in contract]
    if missing:
        raise ValueError(f"Missing contract fields: {', '.join(missing)}")
    if contract["downstreamConsumer"] != "loop_verifier":
        raise ValueError("Step contract downstream consumer must be loop_verifier")
    if contract["outputSchema"] != "cas.loop.step-result.v1":
        raise ValueError("Unsupported step contract output schema")
    tool_scope = contract["toolScope"]
    if not isinstance(tool_scope, dict):
        raise ValueError("toolScope must be an object")
    if tool_scope.get("mutationAllowed") is not False:
        raise ValueError("Loop specialists must remain read-only")
    allowed_tools = tuple(tool_scope.get("allowedTools") or ())
    if not allowed_tools or any(tool.startswith(("write", "delete", "execute")) for tool in allowed_tools):
        raise ValueError("Loop specialists received an unsafe tool scope")
    fan_out = contract["fanOut"]
    if not isinstance(fan_out, dict):
        raise ValueError("fanOut must be an object")
    roles = tuple(fan_out.get("requiredRoles") or ())
    if set(roles) != set(REQUIRED_SPECIALIST_ROLES):
        raise ValueError("Step contract must declare every required specialist role exactly once")
    if fan_out.get("maxConcurrency") != 3:
        raise ValueError("Step contract maxConcurrency must match the bounded runtime of 3")
    if fan_out.get("aggregatorRole") != "loop_verifier":
        raise ValueError("Step contract aggregatorRole must be loop_verifier")
    if not contract.get("inputs") or not contract.get("completionCriteria"):
        raise ValueError("Step contract inputs and completion criteria are required")
    return contract, roles


async def execute_request(payload: dict[str, Any]) -> WorkerEnvelope:
    required = ("goalId", "workItemId", "attempt", "isRepair", "correlationId", "contract")
    missing = [name for name in required if name not in payload]
    if missing:
        raise ValueError(f"Missing worker request fields: {', '.join(missing)}")
    contract, roles = _validate_step_contract(payload)

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
        [SpecialistSpec(role) for role in roles],
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
        contract["contractId"],
        contract["contextBundleId"],
        contract["outputSchema"],
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", help="JSON worker request; stdin is used when omitted")
    args = parser.parse_args()
    try:
        payload = json.loads(args.request if args.request is not None else sys.stdin.read())
        result = asyncio.run(execute_request(payload))
    except (ValueError, json.JSONDecodeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2
    print(json.dumps(asdict(result), separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
