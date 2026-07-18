from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.contract import validate_contract
from pipeline.io_utils import read_json, write_json
from pipeline.review import review_binding_issues
from pipeline.status import Status, aggregate


def _json_or_none(path: Path) -> dict[str, Any] | None:
    try:
        return read_json(path) if path.is_file() else None
    except (OSError, ValueError):
        return None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _visual_review_status(
    review: dict[str, Any] | None,
    *,
    asset_root: Path,
    contract: dict[str, Any],
    contract_sha256: str | None,
) -> tuple[str, list[str]]:
    if review is None:
        return Status.UNKNOWN.value, ["review.json is missing or invalid"]

    issues = review_binding_issues(
        review,
        asset_root=asset_root,
        contract=contract,
        contract_sha256=contract_sha256,
    )
    declared_status = review.get("reviewStatus", Status.UNKNOWN.value)
    allowed_statuses = {status.value for status in Status}
    if declared_status not in allowed_statuses:
        issues.append(f"reviewStatus is invalid: {declared_status!r}")

    if declared_status == Status.PASS.value:
        if review.get("automationReviewStatus") != Status.PASS.value:
            issues.append("PASS review requires automationReviewStatus=PASS")
        if review.get("humanReviewStatus") != Status.PASS.value:
            issues.append("PASS review requires humanReviewStatus=PASS")

    if issues:
        return Status.FAIL.value, issues
    return declared_status, []


def _git(repo: Path) -> dict[str, Any]:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
        ).stdout.strip()
        changes = subprocess.run(
            ["git", "status", "--porcelain=v1"], cwd=repo, check=True, capture_output=True, text=True
        ).stdout.splitlines()
        return {"status": Status.PASS.value if not changes else Status.PARTIAL.value, "commit": commit, "dirty": bool(changes)}
    except (OSError, subprocess.SubprocessError) as error:
        return {"status": Status.UNKNOWN.value, "commit": None, "dirty": None, "reason": str(error)}


def build_report(contract_path: Path, output: Path | None = None) -> dict[str, Any]:
    repo = contract_path.parents[2]
    specification = validate_contract(contract_path)
    contract = _json_or_none(contract_path) or {}
    expected_contract_hash = (
        _sha256_file(contract_path) if contract_path.is_file() else None
    )
    build = contract_path.parent / "build"
    manifest = _json_or_none(build / "manifest.json")
    geometry = _json_or_none(build / "geometry.json")
    provenance = _json_or_none(build / "provenance.json")
    states_manifest = _json_or_none(build / "states" / "states-manifest.json")
    state_determinism = _json_or_none(
        build / "state-determinism" / "determinism-report.json"
    )
    state_review_path = build / "states" / "state-review.html"
    review = _json_or_none(contract_path.parent / "review.json")
    visual_review_status, visual_review_issues = _visual_review_status(
        review,
        asset_root=contract_path.parent,
        contract=contract,
        contract_sha256=expected_contract_hash,
    )
    studio = _json_or_none(contract_path.parent / "evidence" / "studio-environment.json")
    registry = _json_or_none(repo / contract.get("publication", {}).get("registry", ""))
    registry_entry = None
    if registry and isinstance(registry.get("assets"), dict):
        registry_entry = registry["assets"].get(contract.get("assetKey"))
    expected_canon_hash = specification.get("visualCanon", {}).get("sha256")
    build_freshness_status = (
        Status.PASS.value
        if manifest
        and provenance
        and manifest.get("revision") == contract.get("revision")
        and provenance.get("contractSha256") == expected_contract_hash
        and provenance.get("visualCanon", {}).get("sha256")
        == expected_canon_hash
        else Status.UNKNOWN.value
        if manifest is None or provenance is None
        else Status.FAIL.value
    )
    required_states = [
        state.get("id")
        for state in contract.get("states", {}).get("variants", [])
        if isinstance(state, dict)
    ]
    observed_states = (
        states_manifest.get("stateCoverage", []) if states_manifest else []
    )
    state_coverage_status = (
        Status.PASS.value
        if states_manifest
        and states_manifest.get("status") == Status.PASS.value
        and observed_states == required_states
        and states_manifest.get("contractSha256") == expected_contract_hash
        and states_manifest.get("visualCanon", {}).get("sha256")
        == expected_canon_hash
        else Status.UNKNOWN.value
        if states_manifest is None
        else Status.FAIL.value
    )
    state_determinism_status = (
        Status.PASS.value
        if state_determinism
        and state_determinism.get("status") == Status.PASS.value
        and state_determinism.get("contractSha256") == expected_contract_hash
        and state_determinism.get("visualCanon", {}).get("sha256")
        == expected_canon_hash
        and state_determinism.get("stateCoverage") == required_states
        and state_determinism.get("publishedComparison", {}).get("status")
        == Status.PASS.value
        else Status.UNKNOWN.value
        if state_determinism is None
        else Status.FAIL.value
    )
    state_invariants = (
        state_determinism.get("stateInvariants", [])
        if state_determinism
        else []
    )
    state_invariants_status = (
        Status.PASS.value
        if state_determinism
        and state_determinism_status == Status.PASS.value
        and state_determinism.get("contractSha256") == expected_contract_hash
        and state_determinism.get("visualCanon", {}).get("sha256")
        == expected_canon_hash
        and len(state_invariants) == len(required_states)
        and all(item.get("passed") is True for item in state_invariants)
        else Status.UNKNOWN.value
        if state_determinism is None
        else Status.FAIL.value
    )
    state_distinctness = (
        state_determinism.get("stateDistinctness", {})
        if state_determinism
        else {}
    )
    state_distinctness_status = (
        Status.PASS.value
        if state_determinism
        and state_determinism.get("status") == Status.PASS.value
        and state_determinism.get("contractSha256") == expected_contract_hash
        and state_determinism.get("visualCanon", {}).get("sha256")
        == expected_canon_hash
        and state_distinctness.get("semanticHashesUnique") is True
        and state_distinctness.get("glbHashesUnique") is True
        else Status.UNKNOWN.value
        if state_determinism is None
        else Status.FAIL.value
    )

    gates = {
        "contract": specification["status"],
        "visualCanon": Status.PASS.value
        if specification.get("visualCanon", {}).get("status")
        in {"CANDIDATE", "ACCEPTED", "LOCKED", "REVISED"}
        else Status.FAIL.value,
        "visualCanonProductionLock": Status.PASS.value
        if specification.get("visualCanon", {}).get("productionEligible")
        else Status.BLOCKED.value,
        "blenderGeometry": geometry.get("status", Status.UNKNOWN.value) if geometry else Status.UNKNOWN.value,
        "buildManifest": manifest.get("status", Status.UNKNOWN.value) if manifest else Status.UNKNOWN.value,
        "buildFreshness": build_freshness_status,
        "stateCoverage": state_coverage_status,
        "stateDeterminism": state_determinism_status,
        "stateInvariants": state_invariants_status,
        "stateDistinctness": state_distinctness_status,
        "stateReviewBoard": Status.PASS.value
        if state_review_path.is_file()
        and state_coverage_status == Status.PASS.value
        and state_determinism_status == Status.PASS.value
        else Status.UNKNOWN.value,
        "visualReview": visual_review_status,
        "cloudPackageV1": Status.PASS.value if registry_entry and registry_entry.get("packageId") else Status.BLOCKED.value,
        "cloudSamePackageV2": Status.PASS.value
        if registry_entry and len(registry_entry.get("history", [])) >= 2
        else Status.BLOCKED.value,
        "studioEnvironmentProbe": studio.get("status", Status.UNKNOWN.value) if studio else Status.UNKNOWN.value,
        "studioStagingConfirmed": Status.PASS.value
        if studio and studio.get("stagingConfirmed") is True
        else Status.BLOCKED.value,
        "studioPackageIntegration": studio.get("packageIntegrationStatus", Status.BLOCKED.value)
        if studio
        else Status.UNKNOWN.value,
        "benchmark": studio.get("benchmarkStatus", Status.UNKNOWN.value) if studio else Status.UNKNOWN.value,
        "provenance": provenance.get("git", {}).get("status", Status.UNKNOWN.value)
        if provenance
        else Status.UNKNOWN.value,
    }
    required_for_implementation = [
        gates["contract"],
        gates["visualCanon"],
        gates["blenderGeometry"],
        gates["buildManifest"],
        gates["buildFreshness"],
        gates["stateCoverage"],
        gates["stateDeterminism"],
        gates["stateInvariants"],
        gates["stateDistinctness"],
        gates["stateReviewBoard"],
        gates["visualReview"],
        gates["cloudPackageV1"],
        gates["cloudSamePackageV2"],
        gates["studioStagingConfirmed"],
        gates["studioPackageIntegration"],
        gates["benchmark"],
    ]
    implementation = aggregate(required_for_implementation)
    current_git = _git(repo)
    production_requirements = list(gates.values()) + [current_git["status"]]
    production_approved = all(value == Status.PASS.value for value in production_requirements)

    unresolved = [name for name, status in gates.items() if status != Status.PASS.value]
    report = {
        "schemaVersion": "1.0.0",
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "assetKey": contract.get("assetKey"),
        "contractRevision": contract.get("revision"),
        "specificationStatus": specification["status"],
        "implementationStatus": implementation.value,
        "productionApproved": production_approved,
        "gates": gates,
        "evidence": {
            "manifest": str(build / "manifest.json") if manifest else None,
            "geometry": str(build / "geometry.json") if geometry else None,
            "provenance": str(build / "provenance.json") if provenance else None,
            "statesManifest": str(build / "states" / "states-manifest.json")
            if states_manifest
            else None,
            "stateDeterminism": str(
                build / "state-determinism" / "determinism-report.json"
            )
            if state_determinism
            else None,
            "stateReviewBoard": str(state_review_path)
            if state_review_path.is_file()
            else None,
            "visualReview": str(contract_path.parent / "review.json")
            if review
            else None,
            "visualReviewIssues": visual_review_issues,
            "studio": str(contract_path.parent / "evidence" / "studio-environment.json") if studio else None,
            "registry": str(repo / contract.get("publication", {}).get("registry", "")) if registry else None,
            "currentGit": current_git,
        },
        "unresolved": unresolved,
    }
    destination = output or contract_path.parent / "qa" / "final-report.json"
    write_json(destination, report)
    report["reportPath"] = str(destination)
    # Never return PASS merely because a report was generated.
    report["status"] = implementation.value
    return report
