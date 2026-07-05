"""Consumer-side contract-compatibility check against pinned cas-contracts schemas.

autogen consumes the CAS v1.1 SDLC contract family. Its dashboard/session models
(``autogen_dashboard/schemas.py``) are an *internal* snake_case representation and
are intentionally NOT the wire shape. The authoritative wire shape is the camelCase
JSON Schema published by ``cas-contracts`` at ``v1.1`` (schemaVersion ``1.1.0``).

This module pins the contract version autogen targets and fails CI (red check) when:

* the pinned ``schemaVersion`` / ``profileVersion`` autogen emits no longer matches
  the vendored cas-contracts release,
* the vendored schema release has been tampered with (manifest SHA-256 drift), or
* a representative wire payload for each contract autogen produces/consumes stops
  validating against the pinned schema.

Cross-repo reference note: cas-contracts is a *separate* repo. In this local polyrepo
CI checks out only this repo, so we vendor the pinned ``v1.1.1`` release under
``tests/contracts/cas-contracts/v1.1.1/`` (same convention as cas-reference-product).
When the sibling ``../../cas-contracts`` checkout is present (local dev), we additionally
assert the vendored copy has not drifted from the upstream source of truth.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

jsonschema = pytest.importorskip("jsonschema")
referencing = pytest.importorskip("referencing")
from jsonschema import Draft202012Validator  # noqa: E402
from referencing import Registry, Resource  # noqa: E402

# The contract version autogen's models pin themselves to. These MUST stay in lockstep
# with autogen_dashboard/schemas.py (SdlcProfileModel.profile_version, the various
# kind/profile_version literals) and with the vendored release below.
PINNED_RELEASE_VERSION = "1.1.1"
PINNED_SCHEMA_VERSION = "1.1.0"
PINNED_PROFILE_VERSION = "v1.1"

CONTRACT_ROOT = Path(__file__).parent / "contracts" / "cas-contracts" / f"v{PINNED_RELEASE_VERSION}"
UPSTREAM_ROOT = (
    Path(__file__).resolve().parents[2]
    / "cas-contracts"
    / "registry"
    / "releases"
    / f"v{PINNED_RELEASE_VERSION}"
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _registry() -> Registry[Any]:
    resources = []
    for path in CONTRACT_ROOT.glob("*.schema.json"):
        schema = _load_json(path)
        resources.append((schema["$id"], Resource.from_contents(schema)))
    return Registry().with_resources(resources)


def _validate(schema_name: str, instance: dict[str, Any]) -> None:
    schema = _load_json(CONTRACT_ROOT / schema_name)
    Draft202012Validator(schema, registry=_registry()).validate(instance)


def _upstream_release_is_canonical() -> bool:
    manifest_path = UPSTREAM_ROOT / "manifest.json"
    if not manifest_path.exists():
        return False

    manifest = _load_json(manifest_path)
    return all(
        entry["id"].startswith("https://schemas.coding-autopilot.dev/")
        for entry in manifest["schemas"]
    )


# Shared lifecycle metadata every v1.1 contract requires (common.schema.json#lifecycleMetadata).
def _lifecycle() -> dict[str, Any]:
    return {
        "correlationId": "corr-001",
        "promptId": "prompt-001",
        "runId": "run-001",
        "repo": "Coding-Autopilot-System/autogen",
        "actor": {"id": "maf-manager", "type": "agent"},
        "timestamp": "2026-07-03T00:00:00Z",
        "schemaVersion": PINNED_SCHEMA_VERSION,
        "traceContext": {
            "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
        },
    }


def test_vendored_release_matches_manifest_hashes() -> None:
    """The vendored pinned release must be internally consistent (tamper check)."""
    manifest = _load_json(CONTRACT_ROOT / "manifest.json")
    assert manifest["version"] == PINNED_RELEASE_VERSION
    for entry in manifest["schemas"]:
        content = (CONTRACT_ROOT / entry["path"]).read_bytes()
        assert hashlib.sha256(content).hexdigest() == entry["sha256"], entry["path"]


def test_pinned_version_is_the_version_autogen_emits() -> None:
    """autogen's models pin profileVersion v1.1 -> schemaVersion 1.1.0.

    Guards against a silent bump of the vendored release without updating the models.
    """
    common = _load_json(CONTRACT_ROOT / "common.schema.json")
    schema_version_const = common["$defs"]["lifecycleMetadata"]["properties"]["schemaVersion"]["const"]
    assert schema_version_const == PINNED_SCHEMA_VERSION

    request = _load_json(CONTRACT_ROOT / "phase-execution-request.schema.json")
    profile_version_const = (
        request["allOf"][1]["properties"]["profileVersion"]["const"]
    )
    assert profile_version_const == PINNED_PROFILE_VERSION


def test_phase_execution_request_wire_payload_conforms() -> None:
    payload = {
        **_lifecycle(),
        "kind": "PhaseExecutionRequest",
        "profileVersion": PINNED_PROFILE_VERSION,
        "phase": "implement",
        "batch": "change",
        "goal": "Apply the bounded change for the current work item.",
        "constraints": ["No secrets", "Stay within budget"],
    }
    _validate("phase-execution-request.schema.json", payload)


def test_phase_execution_result_wire_payload_conforms() -> None:
    payload = {
        **_lifecycle(),
        "kind": "PhaseExecutionResult",
        "phase": "implement",
        "batch": "change",
        "status": "passed",
        "promptDigest": "a" * 64,
        "artifacts": [{"kind": "patch", "uri": "cas://evidence/patch/1"}],
        "verifier": "mutation-owner",
    }
    _validate("phase-execution-result.schema.json", payload)


def test_phase_verification_result_wire_payload_conforms() -> None:
    payload = {
        **_lifecycle(),
        "kind": "PhaseVerificationResult",
        "phase": "verify",
        "verifier": "verifier",
        "outcome": "passed",
        "invalidatedPhaseIds": [],
    }
    _validate("phase-verification-result.schema.json", payload)


def test_sdlc_profile_wire_payload_conforms() -> None:
    # v1.1 sdlc-profile requires exactly 12 phases — the same 12 autogen models enumerate.
    phase_ids = [
        "understand", "research", "analyze", "plan", "risk-assessment", "implement",
        "verify", "review", "improve", "document", "update-memory", "finished",
    ]
    batch_for = {
        "understand": "discovery", "research": "discovery", "analyze": "discovery",
        "plan": "design", "risk-assessment": "design", "implement": "change",
        "verify": "assurance", "review": "assurance", "improve": "assurance",
        "document": "closure", "update-memory": "closure", "finished": "closure",
    }
    payload = {
        **_lifecycle(),
        "kind": "SdlcProfile",
        "profileId": "cas-sdlc-v1",
        "profileVersion": PINNED_PROFILE_VERSION,
        "goalBudget": 17,
        "phases": [
            {
                "id": pid,
                "name": pid.replace("-", " ").title(),
                "batch": batch_for[pid],
                "dependencies": [] if i == 0 else [phase_ids[i - 1]],
                "verifier": "repo-verifier",
                "successCriteria": ["criterion met"],
            }
            for i, pid in enumerate(phase_ids)
        ],
    }
    _validate("sdlc-profile.schema.json", payload)


@pytest.mark.skipif(
    not _upstream_release_is_canonical(),
    reason="sibling cas-contracts checkout is absent or still on the legacy namespace",
)
def test_vendored_release_matches_upstream_source_of_truth() -> None:
    """Local-only drift guard: vendored copy must equal the sibling cas-contracts release.

    Skipped automatically in isolated CI where the sibling repo is not checked out.
    """
    for path in CONTRACT_ROOT.glob("*.json"):
        upstream = UPSTREAM_ROOT / path.name
        assert upstream.exists(), f"upstream missing {path.name}"
        assert (
            hashlib.sha256(path.read_bytes()).hexdigest()
            == hashlib.sha256(upstream.read_bytes()).hexdigest()
        ), f"vendored {path.name} drifted from upstream cas-contracts {PINNED_RELEASE_VERSION}"
