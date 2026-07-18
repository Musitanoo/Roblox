from __future__ import annotations

"""Create a reviewed visual-canon lock overlay without mutating the candidate."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.art.build_visual_canons import ASSETS, TERRITORIES, build_all
from tools.art.common import (
    ArtSystemError,
    ROOT,
    load_json,
    sha256_bytes,
    sha256_file,
    validate_with_schema,
    write_json,
)
from tools.art.visual_canon_evidence import (
    validate_evidence_manifest,
    validate_human_review,
)

LOCK_SCHEMA = ROOT / "schemas/visual-canon-lock.schema.json"


def create_lock(
    asset_id: str,
    territory_id: str,
    evidence_manifest_path: Path,
    approved_by: str | None,
    decision_record: str | None,
    revision_reason: str | None,
    apply: bool,
    human_review_path: Path | None = None,
) -> dict[str, Any]:
    art = load_json(ROOT / "art/art-direction.json")
    if art["finalTerritory"] != territory_id:
        return {
            "status": "BLOCKED",
            "reason": "visual canon lock requires the human-selected final territory",
        }
    canons, _catalog = build_all()
    relative = (
        Path("art/canonical-visuals")
        / territory_id
        / f"{asset_id}.json"
    ).as_posix()
    candidate = canons[relative]
    if candidate["status"] != "CANDIDATE":
        return {
            "status": "BLOCKED",
            "reason": "lock creation must start from the current generated CANDIDATE",
        }
    evidence_manifest_path = evidence_manifest_path.resolve()
    try:
        evidence_relative = evidence_manifest_path.relative_to(ROOT.resolve())
    except ValueError:
        return {
            "status": "FAIL",
            "issues": ["evidence manifest must remain inside the art-direction package"],
        }
    evidence = load_json(evidence_manifest_path)
    required_boards = [
        board["id"] for board in candidate["visualPacket"]["boards"]
    ]
    candidate_path = ROOT / relative
    issues = validate_evidence_manifest(
        evidence,
        required_boards=required_boards,
        candidate_path=candidate_path,
        candidate=candidate,
        apply=apply,
    )
    package_sha = evidence.get("evidencePackageSha256")
    human_review: dict[str, Any] | None = None
    human_review_target = evidence_manifest_path.parent / "human-review.completed.json"
    human_review_sha = "0" * 64
    if human_review_path is not None:
        human_review_path = human_review_path.resolve()
        if not human_review_path.is_file():
            issues.append("human review file is missing")
        else:
            try:
                human_review = load_json(human_review_path)
            except ArtSystemError as error:
                issues.append(str(error))
            if human_review is not None:
                issues.extend(
                    validate_human_review(
                        human_review,
                        evidence_manifest_path=evidence_manifest_path,
                        evidence=evidence,
                        required_boards=required_boards,
                        require_lock=True,
                    )
                )
                review_bytes = (
                    json.dumps(human_review, indent=2, ensure_ascii=False) + "\n"
                ).encode("utf-8")
                human_review_sha = sha256_bytes(review_bytes)
                approved_by = human_review.get("reviewer")
                decision_record = human_review.get("decisionRecord")
    elif evidence["evidenceClass"] == "REAL_RENDERED" or apply:
        issues.append(
            "a validated visual-canon human review file is required for a real lock"
        )

    if not approved_by or not decision_record:
        issues.append("lock approval requires reviewer and decision record")
    if apply and str(approved_by).upper().startswith("SIMULATED"):
        issues.append("simulated reviewer identities cannot apply production locks")
    if issues:
        return {"status": "FAIL", "issues": issues}
    overlay = {
        "$schema": "https://roblox-top1.local/schemas/visual-canon-lock.schema.json",
        "schemaVersion": "1.1.0",
        "assetId": asset_id,
        "territoryId": territory_id,
        "version": candidate["version"],
        "status": "LOCKED",
        "baseCandidateSha256": sha256_file(candidate_path),
        "evidenceClass": evidence["evidenceClass"],
        "evidenceManifest": {
            "path": evidence_relative.as_posix(),
            "sha256": sha256_file(evidence_manifest_path),
        },
        "humanReview": {
            "path": human_review_target.relative_to(ROOT).as_posix(),
            "sha256": human_review_sha,
        },
        "visualEvidencePackageSha256": package_sha,
        "boards": evidence["boards"],
        "approval": {
            "approvedBy": approved_by,
            "approvedAt": (
                human_review["reviewedAt"]
                if human_review is not None
                else datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            ),
            "decisionRecord": decision_record,
            "revisionReason": revision_reason,
        },
    }
    errors = validate_with_schema(overlay, LOCK_SCHEMA)
    if errors and (apply or evidence["evidenceClass"] == "REAL_RENDERED"):
        return {"status": "FAIL", "issues": errors}
    output = (
        ROOT
        / "art/canonical-visuals/locks"
        / territory_id
        / f"{asset_id}.json"
    )
    if not apply:
        return {
            "status": "PARTIAL",
            "dryRun": True,
            "mutationPerformed": False,
            "lockEligible": not errors,
            "previewIssues": errors,
            "output": str(output),
            "overlay": overlay,
        }
    assert human_review is not None
    write_json(human_review_target, human_review)
    write_json(output, overlay)
    return {
        "status": "PASS",
        "dryRun": False,
        "mutationPerformed": True,
        "output": str(output),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a human-approved visual canon lock overlay."
    )
    parser.add_argument("--asset", required=True, choices=ASSETS)
    parser.add_argument("--territory", required=True, choices=TERRITORIES)
    parser.add_argument("--evidence-manifest", required=True, type=Path)
    parser.add_argument("--approved-by")
    parser.add_argument("--decision-record")
    parser.add_argument("--human-review", type=Path)
    parser.add_argument("--revision-reason")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    result = create_lock(
        args.asset,
        args.territory,
        args.evidence_manifest.resolve(),
        args.approved_by,
        args.decision_record,
        args.revision_reason,
        args.apply,
        args.human_review,
    )
    print(result)
    return 0 if result["status"] in {"PASS", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
