from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from tools.art.build_visual_canons import ASSETS, check_all
from tools.art.common import ROOT, load_json, sha256_file, validate_with_schema, write_json
from tools.art.validate_transfer_report import validate_report as validate_transfer_report

CREATIVE_DECISION_SCHEMA = (
    "https://roblox-top1.local/schemas/creative-direction-decision.schema.json"
)
BLIND_DECISION_SCHEMA = (
    "https://roblox-top1.local/schemas/selection-decision.schema.json"
)

CANONICAL_FILES = [
    "art/art-direction.json",
    "art/decision/founder-direction-decision.json",
    "art/selected/salvaged-frontier-constitution.json",
    "art/calibration/calibration-kit.json",
    "art/calibration/camera-rig.json",
    "art/calibration/render-matrix.json",
    "art/palettes/semantic-palette.json",
    "art/palettes/faction-palettes.json",
    "art/materials/material-rules.json",
    "art/shape-language/rules.json",
    "art/lighting/lighting-profiles.json",
    "art/references/provenance.json",
    "art/qa/visual-rubric.json",
    "art/qa/task-protocol.json",
    "art/transfer/turret-fast-v1.json",
    "art/transfer/turret-fast-v1-review.json",
]


def _validate_selection_authority(
    decision_path: Path,
    blind_map_path: Path | None,
    scoring_report_path: Path | None,
    issues: list[str],
) -> tuple[dict, str, str]:
    decision = load_json(decision_path)
    schema = decision.get("$schema")

    if schema == CREATIVE_DECISION_SCHEMA:
        issues.extend(
            validate_with_schema(
                decision,
                ROOT / "schemas/creative-direction-decision.schema.json",
            )
        )
        if decision.get("status") != "FOUNDER_APPROVED":
            issues.append("founder creative decision is not FOUNDER_APPROVED")
        if decision.get("selectionKind") != "STRATEGIC_CREATIVE_SELECTION":
            issues.append("founder decision has an unsupported selection kind")
        if decision.get("productionApproved") is not False:
            issues.append(
                "creative selection must remain separate from production approval"
            )
        constitution_path = ROOT / decision.get(
            "selectedConstitutionPath", ""
        )
        if not constitution_path.is_file():
            issues.append("selected constitution is missing")
        elif (
            decision.get("selectedConstitutionSha256")
            != sha256_file(constitution_path)
        ):
            issues.append("founder decision selected constitution hash drifted")
        if bool(blind_map_path) != bool(scoring_report_path):
            issues.append(
                "optional blind-map and scoring-report evidence must be supplied together"
            )
        return (
            decision,
            decision.get("selectedTerritory"),
            "FOUNDER_STRATEGIC_SELECTION",
        )

    if schema == BLIND_DECISION_SCHEMA:
        issues.extend(
            validate_with_schema(
                decision,
                ROOT / "schemas/selection-decision.schema.json",
            )
        )
        if blind_map_path is None or scoring_report_path is None:
            issues.append(
                "blind-study selection requires both blind map and scoring report"
            )
            return (
                decision,
                decision.get("selectedTerritory"),
                "BLIND_STUDY_SELECTION",
            )
        blind_map = load_json(blind_map_path)
        score = load_json(scoring_report_path)
        issues.extend(
            validate_with_schema(
                blind_map,
                ROOT / "schemas/blind-map.schema.json",
            )
        )
        if decision.get("scoringReportSha256") != sha256_file(
            scoring_report_path
        ):
            issues.append("selection decision scoringReportSha256 mismatch")
        if decision.get("blindMapSha256") != sha256_file(blind_map_path):
            issues.append("selection decision blindMapSha256 mismatch")
        label = decision.get("selectedBlindLabel")
        territory = decision.get("selectedTerritory")
        if label and blind_map.get("mapping", {}).get(label) != territory:
            issues.append(
                "selected blind label does not map to selected territory"
            )
        if score.get("status") != "COMPLETE":
            issues.append("scoring report is not COMPLETE")
        candidate = next(
            (
                item
                for item in score.get("candidates", [])
                if item.get("territoryId") == territory
            ),
            None,
        )
        if not candidate or not candidate.get("eligible"):
            issues.append(
                "selected territory is not eligible in the scoring report"
            )
        return decision, territory, "BLIND_STUDY_SELECTION"

    issues.append("selection decision uses an unsupported schema")
    return decision, decision.get("selectedTerritory"), "UNKNOWN"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create a production art lock from either the founder strategic "
            "decision or a sealed blind-study decision, plus complete current evidence."
        )
    )
    parser.add_argument("selection_decision", type=Path)
    parser.add_argument(
        "legacy_blind_map",
        type=Path,
        nargs="?",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "legacy_scoring_report",
        type=Path,
        nargs="?",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "legacy_evidence_index",
        type=Path,
        nargs="?",
        help=argparse.SUPPRESS,
    )
    parser.add_argument("--blind-map", type=Path)
    parser.add_argument("--scoring-report", type=Path)
    parser.add_argument("--evidence-index", type=Path)
    parser.add_argument("--locked-by", required=True)
    parser.add_argument("--art-version", default="1.0.0")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write art/art-lock.json after every gate validates.",
    )
    args = parser.parse_args()

    blind_map_path = args.blind_map or args.legacy_blind_map
    scoring_report_path = (
        args.scoring_report or args.legacy_scoring_report
    )
    evidence_index_path = (
        args.evidence_index or args.legacy_evidence_index
    )
    if evidence_index_path is None:
        parser.error(
            "an evidence index is required via --evidence-index or the legacy fourth positional argument"
        )

    evidence = load_json(evidence_index_path)
    art = load_json(ROOT / "art/art-direction.json")
    provenance = load_json(ROOT / "art/references/provenance.json")
    transfer_report_path = (
        ROOT / "evidence/transfer/turret-fast-v1/report.json"
    )
    transfer_review_path = (
        ROOT / "art/transfer/turret-fast-v1-review.json"
    )

    missing_transfer = [
        str(path)
        for path in (transfer_report_path, transfer_review_path)
        if not path.is_file()
    ]
    if missing_transfer:
        for path in missing_transfer:
            print(
                f"[BLOCKED] missing sixth-asset transfer evidence: {path}"
            )
        return 2

    issues: list[str] = []
    decision, territory, selection_authority_kind = (
        _validate_selection_authority(
            args.selection_decision,
            blind_map_path,
            scoring_report_path,
            issues,
        )
    )

    approval = provenance["humanApproval"]
    if approval.get("status") != "APPROVED":
        issues.append(
            "reference cue extraction lacks explicit human approval"
        )
    if (
        not approval.get("reviewer")
        or not approval.get("reviewedAt")
        or not approval.get("decisionRecord")
    ):
        issues.append(
            "reference human approval is not signed and traceable"
        )

    issues.extend(
        validate_with_schema(
            evidence,
            ROOT / "schemas/evidence-index.schema.json",
        )
    )
    if evidence.get("selectedTerritory") != territory:
        issues.append(
            "evidence index territory differs from selection authority"
        )
    if art.get("finalTerritory") != territory:
        issues.append(
            "art direction territory differs from selection authority"
        )

    transfer_report = load_json(transfer_report_path)
    transfer_review = load_json(transfer_review_path)
    transfer_validation = validate_transfer_report(
        transfer_report_path,
        require_approved=True,
    )
    if transfer_validation["status"] != "PASS":
        issues.extend(
            f"sixth-asset transfer: {issue}"
            for issue in transfer_validation["issues"]
        )
    if transfer_review.get("status") != "APPROVED":
        issues.append("sixth-asset human review is not APPROVED")
    if transfer_review.get("selectedTerritory") != territory:
        issues.append(
            "sixth-asset human review territory differs from selection authority"
        )
    if (
        transfer_review.get("evidencePackageSha256")
        != transfer_report.get("evidencePackageSha256")
    ):
        issues.append(
            "sixth-asset human review is not bound to the current evidence package"
        )

    required_gates = set(art["gates"]["requiredHardGateIds"])
    observed = {
        item["gateId"]: item
        for item in evidence.get("items", [])
    }
    if set(observed) != required_gates:
        issues.append("evidence gate set is not exact")
    for gate_id in sorted(required_gates):
        item = observed.get(gate_id)
        if not item or item.get("status") != "PASS":
            issues.append(f"gate {gate_id} is not PASS")
            continue
        if not item.get("path") or not item.get("sha256"):
            issues.append(f"gate {gate_id} lacks path/hash")
            continue
        evidence_path = ROOT / item["path"]
        if not evidence_path.exists():
            issues.append(
                f"gate {gate_id} evidence path does not exist: {item['path']}"
            )
        elif sha256_file(evidence_path) != item["sha256"]:
            issues.append(f"gate {gate_id} evidence hash mismatch")

    rejected = {
        item["territoryId"]
        for item in decision.get("rejectedAlternatives", [])
    }
    all_territories = {
        "industrial-toy-defense",
        "salvaged-frontier",
        "clean-tactical-diorama",
    }
    if rejected != (all_territories - {territory}):
        issues.append(
            "rejected alternatives must be exactly the two non-selected territories"
        )

    issues.extend(
        f"visual canons: {issue}"
        for issue in check_all(require_locked=True)
    )

    selected_canon_paths = [
        f"art/canonical-visuals/{territory}/{asset_id}.json"
        for asset_id in ASSETS
    ]
    selected_lock_paths = [
        f"art/canonical-visuals/locks/{territory}/{asset_id}.json"
        for asset_id in ASSETS
    ]
    canonical_paths = list(
        dict.fromkeys(
            CANONICAL_FILES
            + selected_canon_paths
            + selected_lock_paths
        )
    )
    for relative in canonical_paths:
        if not (ROOT / relative).is_file():
            issues.append(f"canonical lock input is missing: {relative}")

    if issues:
        for issue in issues:
            print(f"[BLOCKED] {issue}")
        return 2

    selected_constitution = (
        ROOT / "art/selected/salvaged-frontier-constitution.json"
    )
    lock = {
        "$schema": (
            "https://roblox-top1.local/schemas/art-lock.schema.json"
        ),
        "schemaVersion": "3.1.0",
        "artVersion": args.art_version,
        "status": "V1_LOCKED",
        "productionApproved": True,
        "selectedTerritory": territory,
        "selectionAuthorityKind": selection_authority_kind,
        "lockedAt": datetime.now(UTC).isoformat().replace(
            "+00:00", "Z"
        ),
        "lockedBy": args.locked_by,
        "selectionDecisionSha256": sha256_file(
            args.selection_decision
        ),
        "selectedConstitutionSha256": sha256_file(
            selected_constitution
        ),
        "selectedCanonCount": len(selected_canon_paths),
        "evidenceIndexSha256": sha256_file(evidence_index_path),
        "canonicalFiles": [
            {
                "path": relative,
                "sha256": sha256_file(ROOT / relative),
            }
            for relative in canonical_paths
        ],
        "sixthAssetId": "turret_fast_v1",
        "sixthAssetTransferReportSha256": sha256_file(
            transfer_report_path
        ),
        "sixthAssetEvidencePackageSha256": transfer_report[
            "evidencePackageSha256"
        ],
        "sixthAssetReviewSha256": sha256_file(
            transfer_review_path
        ),
    }
    lock_errors = validate_with_schema(
        lock,
        ROOT / "schemas/art-lock.schema.json",
    )
    if lock_errors:
        for issue in lock_errors:
            print(f"[FAIL] generated lock invalid: {issue}")
        return 1

    if not args.apply:
        print(
            "[PASS] Lock preview validated. Re-run with --apply to write art/art-lock.json."
        )
        return 0

    write_json(ROOT / "art/art-lock.json", lock)
    print(
        "[PASS] Art direction production lock written with complete current evidence."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
