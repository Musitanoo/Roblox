from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, load_json, sha256_file, validate_with_schema

ASSETS = ["barricade", "objective_core", "enemy_standard", "floor_module", "damage_effect"]
STATES = ["intact", "damaged", "critical"]
INPUT_PATHS = {
    "calibration": "art/calibration/calibration-kit.json",
    "camera": "art/calibration/camera-rig.json",
    "renderMatrix": "art/calibration/render-matrix.json",
    "lighting": "art/lighting/lighting-profiles.json",
    "materials": "art/materials/material-rules.json",
    "generator": "tools/blender/build_art_direction.py",
}


def _inside(base: Path, relative: str) -> Path | None:
    candidate = (base / relative).resolve()
    try:
        candidate.relative_to(base.resolve())
    except ValueError:
        return None
    return candidate


def _verify_artifact(base: Path, relative: str, expected_hash: str, label: str, issues: list[str]) -> None:
    path = _inside(base, relative)
    if path is None:
        issues.append(f"{label}: path escapes build directory: {relative}")
    elif not path.is_file():
        issues.append(f"{label}: file missing: {relative}")
    elif sha256_file(path) != expected_hash:
        issues.append(f"{label}: SHA-256 mismatch: {relative}")


def validate_report(report_path: Path, require_complete: bool = False) -> list[str]:
    report = load_json(report_path)
    issues = validate_with_schema(report, ROOT / "schemas/build-report.schema.json")
    if issues:
        return issues

    calibration = load_json(ROOT / "art/calibration/calibration-kit.json")
    expected_pairs = {
        (asset_id, state_id)
        for asset_id in ASSETS
        for state_id in calibration["assets"][asset_id]["requiredStateVariants"]
    }
    asset_pairs = {(item["assetId"], item["stateId"]) for item in report["assets"]}
    export_pairs = {(item["assetId"], item["stateId"]) for item in report["exports"]}
    if asset_pairs != expected_pairs:
        issues.append(f"asset report pair set mismatch: {sorted(asset_pairs)}")
    if export_pairs != expected_pairs:
        issues.append(f"export pair set mismatch: {sorted(export_pairs)}")
    if len(asset_pairs) != len(report["assets"]):
        issues.append("duplicate asset/state report entries")
    if len(export_pairs) != len(report["exports"]):
        issues.append("duplicate asset/state exports")
    if any(item["status"] != "PASS" for item in report["assets"]):
        issues.append("one or more asset variants is not PASS")
    for item in report["exports"]:
        if item["meshCount"] != len(item["materialRoles"]):
            issues.append(f"export {item['assetId']}/{item['stateId']} meshCount does not match semantic roles")

    render_matrix = load_json(ROOT / "art/calibration/render-matrix.json")
    mode = report["renderMode"]
    expected_count = 0 if mode == "build-only" else render_matrix["modes"][mode]["expectedRenderCount"]
    if report["expectedRenderCount"] != expected_count:
        issues.append(f"expectedRenderCount {report['expectedRenderCount']} != canonical {expected_count}")
    if report["actualRenderCount"] != len(report["renderEvidence"]):
        issues.append("actualRenderCount does not equal renderEvidence length")
    if report["actualRenderCount"] > report["expectedRenderCount"]:
        issues.append("actualRenderCount exceeds expectedRenderCount")

    expected_territory_path = ROOT / "art/territories" / f"{report['territoryId']}.json"
    expected_inputs = {"territory": expected_territory_path, **{key: ROOT / rel for key, rel in INPUT_PATHS.items()}}
    for key, path in expected_inputs.items():
        if report["inputHashes"][key] != sha256_file(path):
            issues.append(f"input hash drift for {key}; rebuild required")

    base = report_path.parent
    if "blendFile" in report:
        _verify_artifact(base, report["blendFile"]["path"], report["blendFile"]["sha256"], "blendFile", issues)
    for item in report["exports"]:
        _verify_artifact(base, item["path"], item["sha256"], f"export {item['assetId']}/{item['stateId']}", issues)
    for item in report["renderEvidence"]:
        _verify_artifact(base, item["path"], item["sha256"], f"render {item['path']}", issues)
    for item in report["stressEvidence"]:
        _verify_artifact(base, item["path"], item["sha256"], f"stress {item['sceneId']}", issues)
    for item in report["reviewEvidence"]:
        _verify_artifact(base, item["path"], item["sha256"], f"review {item['assetId']}/{item['stateId']}", issues)

    if report["reviewRequested"]:
        review_pairs = {(item["assetId"], item["stateId"]) for item in report["reviewEvidence"]}
        if review_pairs != expected_pairs or len(report["reviewEvidence"]) != len(expected_pairs):
            issues.append("review evidence does not cover each applicable asset/state pair exactly once")
    elif report["reviewEvidence"]:
        issues.append("review evidence exists although reviewRequested is false")

    if require_complete and report["evidenceCompleteness"] != "FULL_COMPLETE":
        issues.append("full Blender preflight evidence was required but report is not FULL_COMPLETE")
    if report["evidenceCompleteness"] == "FULL_COMPLETE":
        if report["actualRenderCount"] != expected_count or not report["renderEvidenceComplete"]:
            issues.append("FULL_COMPLETE report has incomplete render evidence")
        if len(report["stressEvidence"]) != 2:
            issues.append("FULL_COMPLETE report must contain both 30-instance stress renders")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and hash-check a Blender build report and every referenced artifact.")
    parser.add_argument("report", type=Path)
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args()
    issues = validate_report(args.report, args.require_complete)
    if issues:
        for issue in issues:
            print(f"[FAIL] {issue}")
        return 1
    print(f"[PASS] Blender build report and referenced artifacts validated: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
