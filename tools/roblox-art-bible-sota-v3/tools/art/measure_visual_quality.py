from __future__ import annotations

import argparse
import itertools
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from tools.art.common import ROOT, load_json, sha256_file, validate_with_schema, write_json
from tools.art.validate_build_report import validate_report

SCHEMA = "https://roblox-top1.local/schemas/visual-quality-report.schema.json"
TERRITORIES = ("industrial-toy-defense", "salvaged-frontier", "clean-tactical-diorama")
IDENTITY_ASSETS = ("barricade", "objective_core", "enemy_standard")
MINIMUM_MASK_AREA_RATIO = 0.001
MAXIMUM_FRAME_CONTACT_PIXELS = 0
MINIMUM_STATE_DIFFERENCE = 0.008
MINIMUM_CRITICAL_DIFFERENCE = 0.025
MINIMUM_CRITICAL_LEAD = 0.005
MINIMUM_CROSS_TERRITORY_DIFFERENCE = 0.04
PORTABLE_ARTIFACT_ROOT = ROOT / "evidence/blender/visual-quality-artifacts"


def silhouette_mask(path: Path) -> np.ndarray:
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.uint8)
    return np.max(rgb, axis=2) <= 64


def mask_metrics(mask: np.ndarray) -> dict[str, float | int]:
    height, width = mask.shape
    ys, xs = np.nonzero(mask)
    if len(xs) == 0:
        return {"maskAreaRatio": 0.0, "bboxWidthRatio": 0.0, "bboxHeightRatio": 0.0, "frameContactPixels": 0}
    frame = np.concatenate((mask[0, :], mask[-1, :], mask[1:-1, 0], mask[1:-1, -1]))
    return {
        "maskAreaRatio": float(mask.mean()),
        "bboxWidthRatio": float((xs.max() - xs.min() + 1) / width),
        "bboxHeightRatio": float((ys.max() - ys.min() + 1) / height),
        "frameContactPixels": int(frame.sum()),
    }


def compare_masks(first: np.ndarray, second: np.ndarray) -> tuple[float, float]:
    if first.shape != second.shape:
        raise ValueError(f"silhouette dimensions differ: {first.shape} != {second.shape}")
    union = np.logical_or(first, second).sum()
    if union == 0:
        return 1.0, 0.0
    intersection = np.logical_and(first, second).sum()
    iou = float(intersection / union)
    return iou, 1.0 - iou


def _comparison(asset_id: str, from_state: str, to_state: str, first: np.ndarray, second: np.ndarray, minimum: float) -> dict[str, Any]:
    iou, difference = compare_masks(first, second)
    return {
        "assetId": asset_id,
        "fromState": from_state,
        "toState": to_state,
        "intersectionOverUnion": iou,
        "differenceRatio": difference,
        "minimumDifference": minimum,
        "pass": difference >= minimum,
    }


def measure(build_root: Path) -> dict[str, Any]:
    if PORTABLE_ARTIFACT_ROOT.is_dir():
        shutil.rmtree(PORTABLE_ARTIFACT_ROOT)
    calibration = load_json(ROOT / "art/calibration/calibration-kit.json")
    issues: list[str] = []
    report: dict[str, Any] = {
        "$schema": SCHEMA,
        "schemaVersion": "1.0.0",
        "status": "PASS",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "inputHashes": {
            "generator": sha256_file(ROOT / "tools/blender/build_art_direction.py"),
            "renderMatrix": sha256_file(ROOT / "art/calibration/render-matrix.json"),
        },
        "thresholds": {
            "minimumMaskAreaRatio": MINIMUM_MASK_AREA_RATIO,
            "maximumFrameContactPixels": MAXIMUM_FRAME_CONTACT_PIXELS,
            "minimumStateDifference": MINIMUM_STATE_DIFFERENCE,
            "minimumCriticalDifference": MINIMUM_CRITICAL_DIFFERENCE,
            "minimumCriticalLead": MINIMUM_CRITICAL_LEAD,
            "minimumCrossTerritoryDifference": MINIMUM_CROSS_TERRITORY_DIFFERENCE,
        },
        "territories": [],
        "crossTerritoryComparisons": [],
        "issues": issues,
    }
    all_masks: dict[tuple[str, str, str], np.ndarray] = {}
    for territory_id in TERRITORIES:
        build_report_path = build_root / territory_id / "build-report.json"
        validation_issues = validate_report(build_report_path)
        if validation_issues:
            issues.extend(f"{territory_id}: {issue}" for issue in validation_issues)
            continue
        build_report = load_json(build_report_path)
        evidence = [item for item in build_report["renderEvidence"] if item["jobId"] == "state_silhouette_comparison"]
        cases: list[dict[str, Any]] = []
        for item in evidence:
            path = build_report_path.parent / item["path"]
            mask = silhouette_mask(path)
            metrics = mask_metrics(mask)
            case_pass = metrics["maskAreaRatio"] >= MINIMUM_MASK_AREA_RATIO and metrics["frameContactPixels"] <= MAXIMUM_FRAME_CONTACT_PIXELS
            portable_path = (
                PORTABLE_ARTIFACT_ROOT
                / territory_id
                / f"{item['assetId']}__{item['stateId']}.png"
            )
            portable_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, portable_path)
            case = {
                "assetId": item["assetId"],
                "stateId": item["stateId"],
                "path": portable_path.relative_to(ROOT).as_posix(),
                "sha256": sha256_file(portable_path),
                **metrics,
                "pass": case_pass,
            }
            cases.append(case)
            all_masks[(territory_id, item["assetId"], item["stateId"])] = mask
            if not case_pass:
                issues.append(f"{territory_id}/{item['assetId']}/{item['stateId']}: empty, too small, or clipped silhouette")
        comparisons: list[dict[str, Any]] = []
        for asset_id, asset in calibration["assets"].items():
            states = asset["requiredStateVariants"]
            baseline = states[0]
            for state_id in states[1:]:
                minimum = MINIMUM_CRITICAL_DIFFERENCE if state_id == "critical" else MINIMUM_STATE_DIFFERENCE
                comparison = _comparison(
                    asset_id,
                    baseline,
                    state_id,
                    all_masks[(territory_id, asset_id, baseline)],
                    all_masks[(territory_id, asset_id, state_id)],
                    minimum,
                )
                comparisons.append(comparison)
                if not comparison["pass"]:
                    issues.append(f"{territory_id}/{asset_id}: {baseline}->{state_id} silhouette difference {comparison['differenceRatio']:.4f} < {minimum:.4f}")
        comparison_index = {
            (item["assetId"], item["toState"]): item for item in comparisons
        }
        severity_ordering: list[dict[str, Any]] = []
        for asset_id, asset in calibration["assets"].items():
            if not {"intact", "damaged", "critical"}.issubset(asset["requiredStateVariants"]):
                continue
            damaged_difference = comparison_index[(asset_id, "damaged")]["differenceRatio"]
            critical_difference = comparison_index[(asset_id, "critical")]["differenceRatio"]
            ordering_pass = critical_difference >= damaged_difference + MINIMUM_CRITICAL_LEAD
            severity_ordering.append(
                {
                    "assetId": asset_id,
                    "damagedDifferenceRatio": damaged_difference,
                    "criticalDifferenceRatio": critical_difference,
                    "minimumCriticalLead": MINIMUM_CRITICAL_LEAD,
                    "pass": ordering_pass,
                }
            )
            if not ordering_pass:
                issues.append(
                    f"{territory_id}/{asset_id}: critical silhouette must exceed damaged by "
                    f"{MINIMUM_CRITICAL_LEAD:.4f} ({critical_difference:.4f} vs {damaged_difference:.4f})"
                )
        report["territories"].append(
            {
                "territoryId": territory_id,
                "reportPath": build_report_path.relative_to(ROOT).as_posix(),
                "reportSha256": sha256_file(build_report_path),
                "cases": sorted(cases, key=lambda item: (item["assetId"], item["stateId"])),
                "stateComparisons": sorted(comparisons, key=lambda item: (item["assetId"], item["toState"])),
                "severityOrdering": sorted(severity_ordering, key=lambda item: item["assetId"]),
            }
        )
    if len(report["territories"]) == 3:
        for asset_id in IDENTITY_ASSETS:
            for territory_a, territory_b in itertools.combinations(TERRITORIES, 2):
                comparison = _comparison(
                    asset_id,
                    "intact",
                    "intact",
                    all_masks[(territory_a, asset_id, "intact")],
                    all_masks[(territory_b, asset_id, "intact")],
                    MINIMUM_CROSS_TERRITORY_DIFFERENCE,
                )
                comparison["territoryA"] = territory_a
                comparison["territoryB"] = territory_b
                report["crossTerritoryComparisons"].append(comparison)
                if not comparison["pass"]:
                    issues.append(f"{asset_id}: {territory_a} vs {territory_b} silhouette difference {comparison['differenceRatio']:.4f} < {MINIMUM_CROSS_TERRITORY_DIFFERENCE:.4f}")
    if issues:
        report["status"] = "FAIL"
    schema_issues = validate_with_schema(report, ROOT / "schemas/visual-quality-report.schema.json")
    if schema_issues:
        report["status"] = "FAIL"
        report["issues"].extend(f"report schema: {issue}" for issue in schema_issues)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Measure state readability and territory silhouette distinction.")
    parser.add_argument("--build-root", type=Path, default=ROOT / "build")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/blender/visual-quality-report.json")
    args = parser.parse_args()
    result = measure(args.build_root.resolve())
    write_json(args.output, result)
    for issue in result["issues"]:
        print(f"[FAIL] {issue}")
    print(f"[{result['status']}] visual quality metrics: {args.output}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
