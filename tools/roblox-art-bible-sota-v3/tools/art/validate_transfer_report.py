from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from tools.art.build_transfer_proof import (
    INPUT_PATHS,
    TERRITORIES,
    _evidence_digest,
)
from tools.art.common import ROOT, load_json, sha256_file, validate_with_schema


def _artifact(item: dict[str, Any], issues: list[str]) -> None:
    path = (ROOT / item["path"]).resolve()
    try:
        path.relative_to(ROOT.resolve())
    except ValueError:
        issues.append(f"artifact escapes package root: {item['path']}")
        return
    if not path.is_file():
        issues.append(f"missing artifact: {item['path']}")
        return
    if path.stat().st_size != item["bytes"]:
        issues.append(f"artifact byte count drift: {item['path']}")
    if sha256_file(path) != item["sha256"]:
        issues.append(f"artifact SHA-256 drift: {item['path']}")


def validate_report(
    path: Path,
    *,
    require_approved: bool = False,
) -> dict[str, Any]:
    report = load_json(path)
    issues = validate_with_schema(
        report,
        ROOT / "schemas/transfer-report.schema.json",
    )
    expected_inputs = {
        name: sha256_file(ROOT / relative)
        for name, relative in INPUT_PATHS.items()
    }
    if report.get("inputHashes") != expected_inputs:
        issues.append("input hash drift; transfer proof must be rebuilt")
    if {item.get("territoryId") for item in report.get("territories", [])} != set(
        TERRITORIES
    ):
        issues.append("territory set is incomplete or duplicated")
    for territory in report.get("territories", []):
        for item in territory.get("portableArtifacts", []):
            _artifact(item, issues)
        if territory.get("status") != "PASS":
            issues.append(
                f"{territory.get('territoryId')}: territory result is not PASS"
            )
        if territory.get("determinism", {}).get("status") != "PASS":
            issues.append(
                f"{territory.get('territoryId')}: determinism result is not PASS"
            )
    for item in report.get("reviewArtifacts", []):
        _artifact(item, issues)
    if not issues:
        observed_digest = _evidence_digest(
            report["inputHashes"],
            report["territories"],
            report["reviewArtifacts"],
        )
        if observed_digest != report["evidencePackageSha256"]:
            issues.append("evidence package digest drift")
    if report.get("automatedStatus") != "PASS":
        issues.append("automated transfer status is not PASS")
    if report.get("automatedScore", 0) < 90:
        issues.append("automated transfer score is below 90")
    human_review = report.get("humanReview", {})
    if human_review.get("status") == "APPROVED":
        review_source = load_json(
            ROOT / "art/transfer/turret-fast-v1-review.json"
        )
        observed_total = sum(review_source["scores"].values())
        if review_source["scoreTotal"] != observed_total:
            issues.append(
                "approved transfer review scoreTotal does not equal its scores"
            )
        if observed_total < 90:
            issues.append("approved transfer review total score is below 90/100")
        art_direction = load_json(ROOT / "art/art-direction.json")
        final_territory = art_direction.get("finalTerritory")
        if (
            final_territory is not None
            and human_review.get("selectedTerritory") != final_territory
        ):
            issues.append(
                "approved transfer territory differs from the locked art direction"
            )
    if require_approved and report.get("overallStatus") != "PASS":
        issues.append("human-approved transfer proof is required")
    return {
        "status": "PASS" if not issues else "FAIL",
        "reportedStatus": report.get("overallStatus", "UNKNOWN"),
        "automatedStatus": report.get("automatedStatus", "UNKNOWN"),
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the portable sixth-asset transfer proof and all artifact hashes."
    )
    parser.add_argument("report", type=Path)
    parser.add_argument("--require-approved", action="store_true")
    args = parser.parse_args()
    result = validate_report(
        args.report,
        require_approved=args.require_approved,
    )
    if result["status"] == "PASS":
        print(
            f"[PASS] Transfer report integrity validated "
            f"({result['reportedStatus']}): {args.report}"
        )
        return 0
    for issue in result["issues"]:
        print(f"[FAIL] {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
