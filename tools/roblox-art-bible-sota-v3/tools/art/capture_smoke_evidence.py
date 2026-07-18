from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, load_json, sha256_file, validate_with_schema, write_json
from tools.art.validate_build_report import validate_report

SCHEMA = "https://roblox-top1.local/schemas/smoke-evidence.schema.json"
TERRITORIES = (
    "industrial-toy-defense",
    "salvaged-frontier",
    "clean-tactical-diorama",
)


def _qualified_path(territory_id: str, relative: str) -> str:
    return f"build/{territory_id}/{relative}"


def capture(output: Path) -> dict[str, Any]:
    territory_evidence: list[dict[str, Any]] = []
    issues: list[str] = []

    for territory_id in TERRITORIES:
        report_path = ROOT / "build" / territory_id / "build-report.json"
        report_issues = validate_report(report_path)
        if report_issues:
            issues.extend(f"{territory_id}: {issue}" for issue in report_issues)
            continue

        report = load_json(report_path)
        if report["status"] != "PASS":
            issues.append(f"{territory_id}: build report status is not PASS")
        if report["renderMode"] != "smoke" or report["evidenceCompleteness"] != "SMOKE_COMPLETE":
            issues.append(f"{territory_id}: build report is not complete smoke evidence")
        if report["expectedRenderCount"] != 108 or report["actualRenderCount"] != 108:
            issues.append(f"{territory_id}: expected exactly 108/108 smoke renders")
        if not report["renderEvidenceComplete"] or report["renderEvidenceCapped"]:
            issues.append(f"{territory_id}: smoke render evidence is incomplete or capped")
        if len(report["stressEvidence"]) != 2:
            issues.append(f"{territory_id}: expected exactly two stress renders")

        territory_evidence.append(
            {
                "territoryId": territory_id,
                "status": report["status"],
                "buildReportSha256": sha256_file(report_path),
                "inputHashes": report["inputHashes"],
                "expectedRenderCount": report["expectedRenderCount"],
                "actualRenderCount": report["actualRenderCount"],
                "renderEvidenceComplete": report["renderEvidenceComplete"],
                "renderEvidence": [
                    {
                        "jobId": item["jobId"],
                        "path": _qualified_path(territory_id, item["path"]),
                        "sha256": item["sha256"],
                    }
                    for item in report["renderEvidence"]
                ],
                "stressEvidence": [
                    {
                        "sceneId": item["sceneId"],
                        "count": item["count"],
                        "path": _qualified_path(territory_id, item["path"]),
                        "sha256": item["sha256"],
                    }
                    for item in report["stressEvidence"]
                ],
            }
        )

    report_value: dict[str, Any] = {
        "$schema": SCHEMA,
        "schemaVersion": "3.0.0",
        "status": "PASS" if not issues and len(territory_evidence) == 3 else "FAIL",
        "generatedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "evidenceTier": "SMOKE_COMPLETE",
        "rendererTruth": "BLENDER_PREFLIGHT_ONLY_STUDIO_IS_CANONICAL",
        "territories": territory_evidence,
        "totalExpectedRenderCount": sum(item["expectedRenderCount"] for item in territory_evidence),
        "totalActualRenderCount": sum(item["actualRenderCount"] for item in territory_evidence),
        "totalStressRenderCount": sum(len(item["stressEvidence"]) for item in territory_evidence),
        "artifactsBundled": False,
        "artifactRetentionNote": (
            "Hashes attest the locally validated build artifacts. The reproducible build/ directory and "
            "render images are intentionally excluded from the release ZIP."
        ),
        "issues": issues,
    }
    schema_issues = validate_with_schema(report_value, ROOT / "schemas/smoke-evidence.schema.json")
    if schema_issues:
        report_value["status"] = "FAIL"
        report_value["issues"].extend(f"schema: {issue}" for issue in schema_issues)
    write_json(output, report_value)
    return report_value


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture a package-safe attestation of complete Blender smoke evidence.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evidence/blender/smoke-evidence.json",
    )
    args = parser.parse_args()
    report = capture(args.output)
    if report["status"] != "PASS":
        for issue in report["issues"]:
            print(f"[FAIL] {issue}")
        return 1
    print(
        f"[PASS] Smoke attestation: {report['totalActualRenderCount']}/"
        f"{report['totalExpectedRenderCount']} renders and "
        f"{report['totalStressRenderCount']} stress renders."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
