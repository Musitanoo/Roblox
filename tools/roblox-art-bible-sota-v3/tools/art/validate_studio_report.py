from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, load_json, validate_with_schema
from tools.art.evidence_validation import verify_artifacts

ASSETS = ["barricade", "objective_core", "enemy_standard", "floor_module", "damage_effect"]
STATES = ["intact", "damaged", "critical"]
STRESS_GROUPS = {
    "Stress_barricade_30": 30,
    "Stress_enemy_standard_30": 30,
    "Stress_barricade_100": 100,
    "Stress_enemy_standard_100": 100,
}


def validate_report(path: Path, *, require_pass: bool = False) -> dict[str, Any]:
    report = load_json(path)
    issues = validate_with_schema(report, ROOT / "schemas/studio-report.schema.json")
    if issues:
        return {"status": "INVALID", "issues": issues}

    issues.extend(verify_artifacts(report["artifacts"], required_prefix="evidence/studio/"))
    if report["status"] == "PASS":
        for check_id, passed in report["environmentChecks"].items():
            if not passed:
                issues.append(f"environmentChecks.{check_id} was not proven")
        calibration = load_json(ROOT / "art/calibration/calibration-kit.json")
        for asset_id in ASSETS:
            for state_id in calibration["assets"][asset_id]["requiredStateVariants"]:
                check = report["assetChecks"][asset_id][state_id]
                if not check["pass"]:
                    issues.append(f"{asset_id}/{state_id}: asset check did not pass")
                if not check["sourceSha256Present"] or not check["sourceIdentityMatches"]:
                    issues.append(f"{asset_id}/{state_id}: source identity was not proven")
        for group_id, expected_count in STRESS_GROUPS.items():
            check = report["reuseChecks"][group_id]
            if check["observedCount"] != expected_count:
                issues.append(f"{group_id}: expected {expected_count} clones")
            if check["meshPartCount"] < expected_count:
                issues.append(f"{group_id}: fewer than {expected_count} MeshPart observations")
            if check["sourceSha256Count"] != 1:
                issues.append(f"{group_id}: expected exactly one source SHA-256")
    if require_pass and report["status"] != "PASS":
        issues.append(f"Studio report status is {report['status']}; PASS required")

    return {
        "status": "PASS" if not issues else "FAIL",
        "reportedStatus": report["status"],
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Roblox Studio Golden Scene evidence.")
    parser.add_argument("report", type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()
    result = validate_report(args.report, require_pass=args.require_pass)
    if result["status"] == "PASS":
        print(f"[PASS] Studio report validated ({result['reportedStatus']}): {args.report}")
        return 0
    for issue in result["issues"]:
        print(f"[FAIL] {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
