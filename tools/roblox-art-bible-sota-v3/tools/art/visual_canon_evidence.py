from __future__ import annotations

"""Validate hash-bound multimodal evidence before a visual-canon lock."""

import json
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from tools.art.common import (
    PROJECT_ROOT,
    ROOT,
    canonical_json_bytes,
    sha256_bytes,
    sha256_file,
    validate_with_schema,
)

EVIDENCE_SCHEMA = ROOT / "schemas/visual-canon-evidence.schema.json"
HUMAN_REVIEW_SCHEMA = ROOT / "schemas/visual-canon-human-review.schema.json"
PACKAGE_DIGEST_FIELDS = (
    "$schema",
    "schemaVersion",
    "assetKey",
    "revision",
    "assetId",
    "territoryId",
    "canonId",
    "baseCandidateSha256",
    "evidenceClass",
    "generation",
    "authority",
    "boards",
    "humanReviewStatus",
    "productionApproved",
)
REAL_AUTHORITY_ROLES = {
    "contract",
    "canon",
    "asset_generator",
    "canon_packet_generator",
    "main_build_manifest",
    "states_manifest",
    "determinism_report",
    "visual_review",
    "raw_render_manifest",
}


def evidence_digest_payload(manifest: dict[str, Any]) -> dict[str, Any]:
    return {field: manifest.get(field) for field in PACKAGE_DIGEST_FIELDS}


def compute_evidence_package_sha256(manifest: dict[str, Any]) -> str:
    return sha256_bytes(canonical_json_bytes(evidence_digest_payload(manifest)))


def _bounded_path(root: Path, configured: Any, label: str) -> tuple[Path | None, str | None]:
    if not isinstance(configured, str) or not configured:
        return None, f"{label}: path must be a non-empty relative string"
    requested = Path(configured)
    if requested.is_absolute():
        return None, f"{label}: absolute paths are forbidden"
    resolved = (root / requested).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError:
        return None, f"{label}: path escapes its declared root"
    return resolved, None


def _read_json(path: Path, label: str, issues: list[str]) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        issues.append(f"{label}: invalid JSON: {error}")
        return None
    if not isinstance(value, dict):
        issues.append(f"{label}: JSON root must be an object")
        return None
    return value


def _validate_binding(
    binding: dict[str, Any],
    role: str,
    issues: list[str],
) -> Path | None:
    root = ROOT if binding.get("root") == "PACKAGE_ROOT" else PROJECT_ROOT
    path, path_issue = _bounded_path(root, binding.get("path"), f"authority/{role}")
    if path_issue:
        issues.append(path_issue)
        return None
    assert path is not None
    if not path.is_file():
        issues.append(f"authority/{role}: file is missing")
        return None
    if path.stat().st_size != binding.get("bytes"):
        issues.append(f"authority/{role}: byte count drift")
    if sha256_file(path) != binding.get("sha256"):
        issues.append(f"authority/{role}: SHA-256 drift")
    return path


def _validate_real_authority(
    manifest: dict[str, Any],
    bindings: dict[str, tuple[dict[str, Any], Path]],
    candidate_path: Path,
    candidate: dict[str, Any],
    issues: list[str],
) -> None:
    roles = set(bindings)
    if roles != REAL_AUTHORITY_ROLES:
        issues.append(
            "REAL_RENDERED authority roles must exactly equal "
            f"{sorted(REAL_AUTHORITY_ROLES)}; observed={sorted(roles)}"
        )
        return

    canon_binding, canon_path = bindings["canon"]
    if canon_path.resolve() != candidate_path.resolve():
        issues.append("authority/canon: path does not identify the current candidate")
    if canon_binding["sha256"] != manifest["baseCandidateSha256"]:
        issues.append("authority/canon: hash differs from baseCandidateSha256")

    contract_binding, contract_path = bindings["contract"]
    contract = _read_json(contract_path, "authority/contract", issues)
    if contract is None:
        return
    if contract.get("assetKey") != manifest["assetKey"]:
        issues.append("authority/contract: assetKey differs from evidence manifest")
    visual_canon = contract.get("visualCanon", {})
    if visual_canon.get("canonId") != manifest["canonId"]:
        issues.append("authority/contract: canonId differs from evidence manifest")
    if visual_canon.get("assetId") != manifest["assetId"]:
        issues.append("authority/contract: assetId differs from evidence manifest")
    if visual_canon.get("territoryId") != manifest["territoryId"]:
        issues.append("authority/contract: territoryId differs from evidence manifest")
    if visual_canon.get("sha256") != manifest["baseCandidateSha256"]:
        issues.append("authority/contract: visual canon hash differs from candidate")
    contract_sha = contract_binding["sha256"]
    revision = contract.get("revision")
    if revision != manifest["revision"]:
        issues.append("authority/contract: revision differs from evidence manifest")

    main = _read_json(
        bindings["main_build_manifest"][1],
        "authority/main_build_manifest",
        issues,
    )
    if main is not None:
        if main.get("status") != "PASS":
            issues.append("authority/main_build_manifest: status must be PASS")
        if main.get("assetKey") != manifest["assetKey"]:
            issues.append("authority/main_build_manifest: assetKey drift")
        if main.get("revision") != revision:
            issues.append("authority/main_build_manifest: revision drift")
        main_canon = main.get("visualCanon", {})
        if main_canon.get("sha256") != manifest["baseCandidateSha256"]:
            issues.append("authority/main_build_manifest: visual canon hash drift")

    states = _read_json(
        bindings["states_manifest"][1],
        "authority/states_manifest",
        issues,
    )
    if states is not None:
        if states.get("status") != "PASS":
            issues.append("authority/states_manifest: status must be PASS")
        if states.get("assetKey") != manifest["assetKey"]:
            issues.append("authority/states_manifest: assetKey drift")
        if states.get("revision") != revision:
            issues.append("authority/states_manifest: revision drift")
        if states.get("contractSha256") != contract_sha:
            issues.append("authority/states_manifest: contract hash drift")

    determinism = _read_json(
        bindings["determinism_report"][1],
        "authority/determinism_report",
        issues,
    )
    if determinism is not None:
        if determinism.get("status") != "PASS":
            issues.append("authority/determinism_report: status must be PASS")
        if determinism.get("assetKey") != manifest["assetKey"]:
            issues.append("authority/determinism_report: assetKey drift")
        if determinism.get("revision") != revision:
            issues.append("authority/determinism_report: revision drift")
        if determinism.get("contractSha256") != contract_sha:
            issues.append("authority/determinism_report: contract hash drift")

    review = _read_json(
        bindings["visual_review"][1],
        "authority/visual_review",
        issues,
    )
    if review is not None:
        if review.get("assetKey") != manifest["assetKey"]:
            issues.append("authority/visual_review: assetKey drift")
        if review.get("revision") != revision:
            issues.append("authority/visual_review: revision drift")
        if review.get("automationReviewStatus") != "PASS":
            issues.append("authority/visual_review: automationReviewStatus must be PASS")

    raw = _read_json(
        bindings["raw_render_manifest"][1],
        "authority/raw_render_manifest",
        issues,
    )
    if raw is not None:
        if raw.get("status") != "PASS":
            issues.append("authority/raw_render_manifest: status must be PASS")
        if raw.get("evidenceClass") != "REAL_RENDERED":
            issues.append(
                "authority/raw_render_manifest: evidenceClass must be REAL_RENDERED"
            )
        if raw.get("assetKey") != manifest["assetKey"]:
            issues.append("authority/raw_render_manifest: assetKey drift")
        if raw.get("contractSha256") != contract_sha:
            issues.append("authority/raw_render_manifest: contract hash drift")
        if raw.get("canonSha256") != manifest["baseCandidateSha256"]:
            issues.append("authority/raw_render_manifest: canon hash drift")

    if candidate.get("canonId") != manifest["canonId"]:
        issues.append("candidate canonId differs from evidence manifest")


def validate_evidence_manifest(
    manifest: dict[str, Any],
    *,
    required_boards: list[str],
    candidate_path: Path,
    candidate: dict[str, Any],
    apply: bool,
) -> list[str]:
    issues = validate_with_schema(manifest, EVIDENCE_SCHEMA)
    if issues:
        return issues

    observed_candidate_sha = sha256_file(candidate_path)
    if manifest["baseCandidateSha256"] != observed_candidate_sha:
        issues.append("baseCandidateSha256 differs from the current candidate")
    for field in ("assetId", "territoryId", "canonId"):
        if manifest[field] != candidate[field]:
            issues.append(f"{field} differs from the current candidate")
    if set(manifest["boards"]) != set(required_boards):
        issues.append("evidence board set must exactly match the canon board set")
    if len(required_boards) != len(set(required_boards)):
        issues.append("canon board IDs must be unique")

    observed_digest = compute_evidence_package_sha256(manifest)
    if manifest["evidencePackageSha256"] != observed_digest:
        issues.append("evidencePackageSha256 does not match the canonical payload")

    bindings_by_role: dict[str, tuple[dict[str, Any], Path]] = {}
    for binding in manifest["authority"]["bindings"]:
        role = binding["role"]
        if role in bindings_by_role:
            issues.append(f"authority/{role}: duplicate role")
            continue
        path = _validate_binding(binding, role, issues)
        if path is not None:
            bindings_by_role[role] = (binding, path)

    for board_id, artifacts in manifest["boards"].items():
        for index, artifact in enumerate(artifacts):
            label = f"boards/{board_id}/{index}"
            path, path_issue = _bounded_path(ROOT, artifact["path"], label)
            if path_issue:
                issues.append(path_issue)
                continue
            assert path is not None
            if not path.is_file():
                issues.append(f"{label}: file is missing")
                continue
            if path.stat().st_size != artifact["bytes"]:
                issues.append(f"{label}: byte count drift")
            if sha256_file(path) != artifact["sha256"]:
                issues.append(f"{label}: SHA-256 drift")
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    if image.format != "PNG":
                        issues.append(f"{label}: file is not a PNG")
                    if image.size != (artifact["width"], artifact["height"]):
                        issues.append(f"{label}: declared dimensions drift")
                    if (
                        manifest["evidenceClass"] == "REAL_RENDERED"
                        and image.size != (1920, 1080)
                    ):
                        issues.append(
                            f"{label}: REAL_RENDERED board must be 1920x1080"
                        )
            except (OSError, UnidentifiedImageError) as error:
                issues.append(f"{label}: invalid image: {error}")

    if manifest["evidenceClass"] == "REAL_RENDERED":
        _validate_real_authority(
            manifest,
            bindings_by_role,
            candidate_path,
            candidate,
            issues,
        )
        if manifest["generation"]["rawRenderStatus"] != "PASS":
            issues.append("REAL_RENDERED evidence requires rawRenderStatus PASS")
    elif apply:
        issues.append("SYNTHETIC_DOUBLE evidence cannot be applied to a production lock")

    return issues


def validate_human_review(
    review: dict[str, Any],
    *,
    evidence_manifest_path: Path,
    evidence: dict[str, Any],
    required_boards: list[str],
    require_lock: bool,
) -> list[str]:
    """Validate a human decision without granting it production authority."""

    issues = validate_with_schema(review, HUMAN_REVIEW_SCHEMA)
    if issues:
        return issues

    expected_manifest_path = evidence_manifest_path.resolve()
    try:
        expected_relative = expected_manifest_path.relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return ["human review evidence manifest must remain inside the package"]

    expected_fields = {
        "assetKey": evidence["assetKey"],
        "revision": evidence["revision"],
        "assetId": evidence["assetId"],
        "territoryId": evidence["territoryId"],
        "canonId": evidence["canonId"],
        "evidenceManifest": expected_relative,
        "evidenceManifestSha256": sha256_file(expected_manifest_path),
        "evidencePackageSha256": evidence["evidencePackageSha256"],
        "productionApproved": False,
    }
    for field, expected in expected_fields.items():
        if review.get(field) != expected:
            issues.append(f"human review {field} differs from the bound evidence")

    if set(review["boards"]) != set(required_boards):
        issues.append("human review board set must exactly match the canon board set")
    if len(required_boards) != len(set(required_boards)):
        issues.append("human review canon board IDs must be unique")

    final_status = review["status"] != "PENDING"
    if final_status:
        if not review["reviewer"]:
            issues.append("completed human review requires a named reviewer")
        if not review["reviewedAt"]:
            issues.append("completed human review requires reviewedAt")
        if not review["decisionRecord"]:
            issues.append("completed human review requires a decision record")
        pending_boards = [
            board_id
            for board_id, value in review["boards"].items()
            if value["status"] == "PENDING"
        ]
        if pending_boards:
            issues.append(
                "completed human review contains pending boards: "
                + ", ".join(sorted(pending_boards))
            )
        pending_checks = [
            check_id
            for check_id, status in review["mandatoryChecks"].items()
            if status == "PENDING"
        ]
        if pending_checks:
            issues.append(
                "completed human review contains pending mandatory checks: "
                + ", ".join(sorted(pending_checks))
            )

    decision_status = {
        None: "PENDING",
        "LOCK": "APPROVED",
        "REVISION_REQUIRED": "REVISION_REQUIRED",
        "REJECT": "REJECTED",
    }
    expected_status = decision_status[review["decision"]]
    if review["status"] != expected_status:
        issues.append(
            f"human review status must be {expected_status} for "
            f"decision {review['decision']}"
        )

    failed_boards = [
        board_id
        for board_id, value in review["boards"].items()
        if value["status"] == "FAIL"
    ]
    failed_checks = [
        check_id
        for check_id, status in review["mandatoryChecks"].items()
        if status == "FAIL"
    ]
    if review["decision"] == "LOCK" and (failed_boards or failed_checks):
        issues.append("LOCK requires every board and mandatory check to PASS")
    if review["decision"] in {"REVISION_REQUIRED", "REJECT"} and not (
        failed_boards or failed_checks
    ):
        issues.append(
            f"{review['decision']} requires at least one explicit failed item"
        )

    if require_lock:
        if evidence["evidenceClass"] != "REAL_RENDERED":
            issues.append("production lock requires REAL_RENDERED evidence")
        if review["decision"] != "LOCK" or review["status"] != "APPROVED":
            issues.append("production lock requires an APPROVED LOCK human review")
        if not all(
            value["status"] == "PASS" for value in review["boards"].values()
        ):
            issues.append("production lock requires every reviewed board to PASS")
        if not all(
            status == "PASS" for status in review["mandatoryChecks"].values()
        ):
            issues.append("production lock requires every mandatory check to PASS")
        reviewer = str(review.get("reviewer") or "").upper()
        if reviewer.startswith("SIMULATED"):
            issues.append("simulated reviewer identities cannot approve production locks")

    return issues
