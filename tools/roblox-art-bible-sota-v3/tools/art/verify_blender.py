from __future__ import annotations

import argparse
import copy
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.art.common import (
    ROOT,
    canonical_json_bytes,
    load_json,
    sanitized_subprocess_environment,
    sha256_bytes,
    sha256_file,
    validate_with_schema,
    write_json,
)
from tools.art.validate_build_report import validate_report

TERRITORIES = ["industrial-toy-defense", "salvaged-frontier", "clean-tactical-diorama"]
SCHEMA = "https://roblox-top1.local/schemas/blender-verification-report.schema.json"
EXPECTED_BLENDER_VERSION = "5.2.0 LTS"
BLENDER_TIMEOUT_SECONDS = 1200


def _canonical_report(report: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(report)
    value.pop("generatedAt", None)
    # Blender's native .blend container is not a Roblox delivery artifact and
    # may contain serialization metadata. Determinism is required for the
    # semantic report and every exported GLB.
    value.pop("blendFile", None)
    return value


def _exports(report: dict[str, Any]) -> dict[str, str]:
    return {
        f"{item['assetId']}/{item['stateId']}": item["sha256"]
        for item in report["exports"]
    }


def _run(blender: Path, output: Path, territory: str) -> subprocess.CompletedProcess[str]:
    command = [
        str(blender),
        "--background",
        "--factory-startup",
        "--threads",
        "1",
        "--python-exit-code",
        "19",
        "--python",
        str(ROOT / "tools/blender/build_art_direction.py"),
        "--",
        "--root",
        str(ROOT),
        "--territory",
        territory,
        "--render-mode",
        "build-only",
        "--output",
        str(output),
    ]
    try:
        return subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=sanitized_subprocess_environment(deterministic=True),
            timeout=BLENDER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        stdout = (
            error.stdout.decode(errors="replace")
            if isinstance(error.stdout, bytes)
            else (error.stdout or "")
        )
        stderr = (
            error.stderr.decode(errors="replace")
            if isinstance(error.stderr, bytes)
            else (error.stderr or "")
        )
        return subprocess.CompletedProcess(
            command,
            124,
            stdout,
            stderr + f"\nBlender timed out after {BLENDER_TIMEOUT_SECONDS} seconds.",
        )


def verify(blender: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "$schema": SCHEMA,
        "schemaVersion": "3.0.0",
        "status": "PASS",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "blenderExecutable": str(blender),
        "inputHashes": {
            "generator": sha256_file(ROOT / "tools/blender/build_art_direction.py"),
            "materials": sha256_file(ROOT / "art/materials/material-rules.json"),
        },
        "territories": [],
        "issues": [],
    }
    with tempfile.TemporaryDirectory(prefix="roblox-art-v3-blender-") as raw_temp:
        temp = Path(raw_temp)
        for territory in TERRITORIES:
            territory_result: dict[str, Any] = {
                "territoryId": territory,
                "status": "PASS",
                "runExitCodes": [],
                "canonicalReportSha256": None,
                "exportSha256": {},
                "issues": [],
            }
            reports: list[dict[str, Any]] = []
            for run_id in ("a", "b"):
                output = temp / run_id / territory
                completed = _run(blender, output, territory)
                territory_result["runExitCodes"].append(completed.returncode)
                report_path = output / "build-report.json"
                if completed.returncode != 0:
                    territory_result["issues"].append(
                        f"run {run_id} exited {completed.returncode}: {(completed.stderr or completed.stdout)[-1200:]}"
                    )
                    continue
                if not report_path.is_file():
                    territory_result["issues"].append(f"run {run_id} did not produce build-report.json")
                    continue
                validation_issues = validate_report(report_path)
                territory_result["issues"].extend(f"run {run_id}: {issue}" for issue in validation_issues)
                reports.append(load_json(report_path))

            if len(reports) == 2 and not territory_result["issues"]:
                observed_versions = {item["toolchain"]["blenderVersion"] for item in reports}
                if observed_versions != {EXPECTED_BLENDER_VERSION}:
                    territory_result["issues"].append(
                        f"Blender versions {sorted(observed_versions)} do not match pinned {EXPECTED_BLENDER_VERSION}"
                    )
                canonical_a = canonical_json_bytes(_canonical_report(reports[0]))
                canonical_b = canonical_json_bytes(_canonical_report(reports[1]))
                exports_a = _exports(reports[0])
                exports_b = _exports(reports[1])
                if canonical_a != canonical_b:
                    territory_result["issues"].append("canonical build reports differ between run A and B")
                if exports_a != exports_b:
                    territory_result["issues"].append("exported GLB SHA-256 map differs between run A and B")
                territory_result["canonicalReportSha256"] = sha256_bytes(canonical_a)
                territory_result["exportSha256"] = exports_a

            if territory_result["issues"]:
                territory_result["status"] = "FAIL"
                report["issues"].extend(f"{territory}: {issue}" for issue in territory_result["issues"])
            report["territories"].append(territory_result)

        if report["issues"]:
            diagnostic = ROOT / "build/determinism-failure"
            if diagnostic.exists():
                shutil.rmtree(diagnostic)
            shutil.copytree(temp, diagnostic)

    if report["issues"]:
        report["status"] = "FAIL"
    schema_issues = validate_with_schema(report, ROOT / "schemas/blender-verification-report.schema.json")
    if schema_issues:
        report["status"] = "FAIL"
        report["issues"].extend(f"report schema: {issue}" for issue in schema_issues)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run two Blender builds and prove deterministic GLB output.")
    parser.add_argument("--blender", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evidence/blender/blender-verification-report.json",
    )
    args = parser.parse_args()
    result = verify(args.blender.resolve())
    write_json(args.output, result)
    for territory in result["territories"]:
        print(f"[{territory['status']}] {territory['territoryId']} A/B determinism")
    for issue in result["issues"]:
        print(f"[FAIL] {issue}")
    print(f"[{result['status']}] Blender integration report: {args.output}")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
