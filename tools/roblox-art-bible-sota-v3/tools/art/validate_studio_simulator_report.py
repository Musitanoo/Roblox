from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, load_json, validate_with_schema
from tools.art.evidence_validation import verify_artifacts


EXPECTED_CONDITIONS = {
    ("graybox", 30),
    ("candidate", 30),
    ("graybox", 100),
    ("candidate", 100),
}
EXPECTED_VIEWPORTS = {
    ("landscape", 640, 360),
    ("portrait", 360, 640),
}


def validate_report(path: Path, *, require_pass: bool = False) -> dict[str, Any]:
    report = load_json(path)
    issues = validate_with_schema(
        report, ROOT / "schemas/studio-simulator-report.schema.json"
    )
    if issues:
        return {"status": "INVALID", "issues": issues}

    issues.extend(
        verify_artifacts(report["artifacts"], required_prefix="evidence/mobile/")
    )

    observed_conditions = {
        (entry["conditionId"], entry["copyCount"])
        for entry in report["conditions"]
    }
    if observed_conditions != EXPECTED_CONDITIONS:
        issues.append(
            "conditions must contain each graybox/candidate x 30/100 pair exactly once"
        )

    observed_viewports = {
        (
            entry["orientation"],
            entry["observed"]["width"],
            entry["observed"]["height"],
        )
        for entry in report["deviceSimulator"]["viewports"]
        if entry["status"] == "PASS"
        and entry["requested"] == entry["observed"]
    }
    if not EXPECTED_VIEWPORTS.issubset(observed_viewports):
        issues.append("exact 640x360 landscape and 360x640 portrait readbacks are required")
    if not report["deviceSimulator"]["resetToDefault"]:
        issues.append("device simulator was not reset to default")

    by_key = {
        (entry["conditionId"], entry["copyCount"]): entry
        for entry in report["conditions"]
    }
    for count in (30, 100):
        graybox = by_key.get(("graybox", count))
        candidate = by_key.get(("candidate", count))
        if not graybox or not candidate:
            continue
        if graybox["assetInstances"] != count * 2:
            issues.append(f"graybox_{count} must contain {count * 2} asset instances")
        if candidate["assetInstances"] != graybox["assetInstances"]:
            issues.append(f"candidate_{count} does not match graybox asset-instance count")
        if candidate["uniqueMeshCombos"] < 1:
            issues.append(f"candidate_{count} has no reusable mesh combination")
        if candidate["singletonMeshCombos"] != 0:
            issues.append(f"candidate_{count} contains singleton mesh combinations")
        if candidate["transparentParts"] != 0 or candidate["decals"] != 0:
            issues.append(f"candidate_{count} introduces transparent parts or decals")

    serialized = str(report).lower()
    if "rbxassetid://" in serialized or "placeid" in serialized or "creatorid" in serialized:
        issues.append("simulator report contains a raw Roblox identifier")

    if report["status"] == "PASS":
        if any(
            capability["status"] != "PASS"
            for capability in report["capabilities"].values()
        ):
            issues.append("PASS simulator report contains a blocked capability")
        kinds = {artifact["kind"] for artifact in report["artifacts"]}
        required = {"studio_capture", "microprofiler_dump", "scene_analysis_dump"}
        missing = required - kinds
        if missing:
            issues.append(f"PASS simulator report lacks artifact kinds: {sorted(missing)}")

    if require_pass and report["status"] != "PASS":
        issues.append(f"Studio simulator report status is {report['status']}; PASS required")

    return {
        "status": "PASS" if not issues else "FAIL",
        "reportedStatus": report["status"],
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate Roblox Studio simulator evidence without treating it as physical-device evidence."
    )
    parser.add_argument("report", type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()
    result = validate_report(args.report, require_pass=args.require_pass)
    if result["status"] == "PASS":
        print(
            f"[PASS] Studio simulator report validated "
            f"({result['reportedStatus']}): {args.report}"
        )
        return 0
    for issue in result["issues"]:
        print(f"[FAIL] {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
