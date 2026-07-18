from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, load_json, sha256_file, validate_with_schema

ASSET_ID = "turret_fast_v1"
STATES = {"intact", "damaged", "critical"}
INPUT_PATHS = {
    "contract": "art/transfer/turret-fast-v1.json",
    "calibration": "art/calibration/calibration-kit.json",
    "shapeLanguage": "art/shape-language/rules.json",
    "camera": "art/calibration/camera-rig.json",
    "lighting": "art/lighting/lighting-profiles.json",
    "materials": "art/materials/material-rules.json",
    "baseCompiler": "tools/blender/build_art_direction.py",
    "generator": "tools/blender/build_transfer_asset.py",
}


def _artifact(
    report_dir: Path,
    relative: str,
    expected_sha256: str,
    label: str,
    issues: list[str],
) -> None:
    candidate = (report_dir / relative).resolve()
    try:
        candidate.relative_to(report_dir.resolve())
    except ValueError:
        issues.append(f"{label}: path escapes report directory: {relative}")
        return
    if not candidate.is_file():
        issues.append(f"{label}: missing artifact: {relative}")
        return
    if sha256_file(candidate) != expected_sha256:
        issues.append(f"{label}: SHA-256 drift: {relative}")


def validate_report(
    report_path: Path,
    *,
    require_full: bool = False,
    root: Path = ROOT,
) -> list[str]:
    report_path = report_path.resolve()
    report = load_json(report_path)
    issues = validate_with_schema(
        report, root / "schemas/transfer-build-report.schema.json"
    )
    if report.get("assetId") != ASSET_ID:
        issues.append("assetId is not turret_fast_v1")
    territory_id = report.get("territoryId")
    territory_path = root / f"art/territories/{territory_id}.json"
    expected_inputs = {
        name: sha256_file(root / relative) for name, relative in INPUT_PATHS.items()
    }
    if territory_path.is_file():
        expected_inputs["territory"] = sha256_file(territory_path)
    if report.get("inputHashes") != expected_inputs:
        issues.append("input hash drift; transfer rebuild required")

    variants = report.get("variants", [])
    exports = report.get("exports", [])
    if {item.get("stateId") for item in variants} != STATES:
        issues.append("variant state set must be intact/damaged/critical exactly once")
    if len({item.get("stateId") for item in variants}) != len(variants):
        issues.append("duplicate variant state")
    if {item.get("stateId") for item in exports} != STATES:
        issues.append("export state set must be intact/damaged/critical exactly once")
    if len({item.get("stateId") for item in exports}) != len(exports):
        issues.append("duplicate export state")
    if any(item.get("status") != "PASS" for item in variants):
        issues.append("one or more geometry variants did not pass")
    if report.get("grammarAudit", {}).get("status") != "PASS":
        issues.append("grammar audit did not pass")
    if report.get("status") != "PASS":
        issues.append("build report status is not PASS")

    report_dir = report_path.parent
    for item in exports:
        _artifact(
            report_dir,
            item["path"],
            item["sha256"],
            f"export {item['stateId']}",
            issues,
        )
    blend = report.get("blendFile")
    if blend:
        _artifact(
            report_dir,
            blend["path"],
            blend["sha256"],
            "blend file",
            issues,
        )
        blend_path = report_dir / blend["path"]
        if blend_path.is_file() and blend_path.stat().st_size != blend["bytes"]:
            issues.append("blend file byte count drift")
    for item in report.get("renderEvidence", []):
        _artifact(
            report_dir,
            item["path"],
            item["sha256"],
            f"render {item['stateId']}/{item['caseId']}",
            issues,
        )

    mode = report.get("renderMode")
    if require_full and mode != "full":
        issues.append("full transfer render evidence is required")
    if mode == "full":
        renders = report.get("renderEvidence", [])
        if len(renders) != 36:
            issues.append(f"full render count {len(renders)} != 36")
        case_counts: dict[tuple[str, str], int] = {}
        for item in renders:
            key = (item["stateId"], item["caseId"])
            case_counts[key] = case_counts.get(key, 0) + 1
        for state in STATES:
            expected = {
                "hero": 1,
                "state_silhouette": 1,
                "front_silhouette": 1,
                "back_silhouette": 1,
                "far_mobile": 4,
                "portrait_mobile": 4,
            }
            for case_id, count in expected.items():
                if case_counts.get((state, case_id), 0) != count:
                    issues.append(
                        f"{state}/{case_id}: count "
                        f"{case_counts.get((state, case_id), 0)} != {count}"
                    )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Schema-, hash-, and coverage-validate a transfer Blender report."
    )
    parser.add_argument("report", type=Path)
    parser.add_argument("--require-full", action="store_true")
    args = parser.parse_args()
    issues = validate_report(args.report, require_full=args.require_full)
    if issues:
        for issue in issues:
            print(f"[FAIL] {issue}")
        return 1
    print(f"[PASS] Transfer Blender report validated: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
