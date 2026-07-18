from __future__ import annotations

"""Bind exact build reports to exact visual canons and report truthful compliance."""

import argparse
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, load_json, sha256_file, validate_with_schema, write_json

SCHEMA = ROOT / "schemas/canon-compliance-report.schema.json"
COMPONENT_EVIDENCE_MAP = ROOT / "art/calibration/component-evidence-map.json"
COMPONENT_EVIDENCE_SCHEMA = ROOT / "schemas/component-evidence-report.schema.json"


def _check(
    check_id: str,
    category: str,
    status: str,
    evidence: list[str],
    issues: list[str],
) -> dict[str, Any]:
    return {
        "id": check_id,
        "category": category,
        "status": status,
        "evidence": evidence,
        "issues": issues,
    }


def _variant_rows(
    build: dict[str, Any], asset_id: str
) -> list[dict[str, Any]]:
    rows = build.get("assets", build.get("variants", []))
    return [row for row in rows if row.get("assetId") == asset_id]


def build_report(
    canon_path: Path,
    build_report_path: Path,
    authority_path: Path,
    output: Path,
    component_evidence_path: Path | None = None,
) -> dict[str, Any]:
    canon = load_json(canon_path)
    build = load_json(build_report_path)
    authority = load_json(authority_path)
    expected_binding = next(
        (
            item
            for item in authority["canonBindings"]
            if item["canonId"] == canon["canonId"]
        ),
        None,
    )
    rows = _variant_rows(build, canon["assetId"])
    row_states = sorted(row["stateId"] for row in rows)
    canon_states = sorted(state["id"] for state in canon["states"])
    binding_issues: list[str] = []
    if expected_binding is None:
        binding_issues.append("generation authority does not bind this canon")
    else:
        if expected_binding["sha256"] != sha256_file(canon_path):
            binding_issues.append("canon hash differs from generation authority")
        if authority["compilerSha256"] != build["inputHashes"].get(
            "generator",
            build["inputHashes"].get("baseCompiler"),
        ):
            binding_issues.append(
                "compiler hash in generation authority differs from build report"
            )
    binding_status = "PASS" if not binding_issues else "FAIL"

    geometry_issues: list[str] = []
    if row_states != canon_states:
        geometry_issues.append(
            f"state coverage differs: build={row_states} canon={canon_states}"
        )
    dims = canon["dimensions"]
    for row in rows:
        observed = row["boundsBlenderXYZ"]
        expected = {
            "width": dims["width"],
            "depth": dims["depth"],
            "height": dims["height"],
        }
        for axis, target in expected.items():
            if row["stateId"] == "intact":
                if not math.isclose(
                    observed[axis],
                    target,
                    abs_tol=dims["toleranceStuds"],
                ):
                    geometry_issues.append(
                        f"{row['stateId']} {axis}={observed[axis]} expected={target}"
                    )
            elif observed[axis] > target + dims["toleranceStuds"]:
                geometry_issues.append(
                    f"{row['stateId']} {axis}={observed[axis]} escapes canonical envelope {target}"
                )
        if row["pivot"] != dims["pivot"]:
            geometry_issues.append(
                f"{row['stateId']} pivot={row['pivot']} expected={dims['pivot']}"
            )
        if row["status"] != "PASS":
            geometry_issues.append(f"{row['stateId']} geometry status is not PASS")
    geometry_status = "PASS" if rows and not geometry_issues else "FAIL"

    technical_issues: list[str] = []
    for row in rows:
        if row["triangles"] > row["triangleBudget"]:
            technical_issues.append(f"{row['stateId']} exceeds triangle budget")
        if row["materialSlotsMaxPerMesh"] > 1:
            technical_issues.append(
                f"{row['stateId']} exceeds one material slot"
            )
        if row["uvLayersMaxPerMesh"] > 1:
            technical_issues.append(f"{row['stateId']} exceeds one UV set")
        if (
            row["nonManifoldEdges"] != 0
            or not row["nonzeroVolume"]
            or row["uvOutOfRange"] != 0
        ):
            technical_issues.append(
                f"{row['stateId']} fails topology or UV requirements"
            )
    technical_status = "PASS" if rows and not technical_issues else "FAIL"

    visual_status = (
        "PASS" if canon["visualPacket"]["status"] == "COMPLETE" else "PARTIAL"
    )
    human_status = (
        "PASS" if canon["approval"]["status"] == "APPROVED" else "BLOCKED"
    )
    functional_issues: list[str] = []
    functional_evidence: list[str] = []
    if canon["assetId"] == "turret_fast_v1":
        if build.get("grammarAudit", {}).get("status") != "PASS":
            functional_issues.append("transfer grammar and component audit is not PASS")
        functional_evidence.append("transfer grammar and component audit")
        functional_evidence_binding = {
            "mode": "TRANSFER_GRAMMAR_AUDIT",
            "sources": [
                {
                    "path": build_report_path.relative_to(ROOT).as_posix(),
                    "sha256": sha256_file(build_report_path),
                }
            ],
        }
    else:
        if component_evidence_path is None:
            raise RuntimeError(
                "calibration compliance requires --component-evidence"
            )
        component_report = load_json(component_evidence_path)
        component_errors = validate_with_schema(
            component_report, COMPONENT_EVIDENCE_SCHEMA
        )
        if component_errors:
            raise RuntimeError(
                "component evidence report invalid: "
                + "; ".join(component_errors)
            )
        if component_report["status"] != "PASS":
            functional_issues.extend(component_report["issues"])
        if (
            component_report["source"]["buildReportSha256"]
            != sha256_file(build_report_path)
        ):
            functional_issues.append(
                "component evidence is not bound to the current build report"
            )
        components = canon["construction"]["components"]
        component_map = load_json(COMPONENT_EVIDENCE_MAP)
        mappings = component_map["assets"][canon["assetId"]]["components"]
        mappings_by_id = {
            item["componentId"]: item["objectNamePatterns"]
            for item in mappings
        }
        canonical_ids = {component["id"] for component in components}
        mapped_ids = set(mappings_by_id)
        if mapped_ids != canonical_ids:
            functional_issues.append(
                f"component evidence map differs from canon: mapped={sorted(mapped_ids)} canon={sorted(canonical_ids)}"
            )
        for row in rows:
            component_row = next(
                (
                    item
                    for item in component_report["assets"]
                    if item["assetId"] == canon["assetId"]
                    and item["stateId"] == row["stateId"]
                ),
                None,
            )
            semantic_objects = (
                component_row["semanticObjects"] if component_row else []
            )
            if component_row is None:
                functional_issues.append(
                    f"{row['stateId']} is absent from component evidence"
                )
            for component in components:
                patterns = [
                    pattern.casefold()
                    for pattern in mappings_by_id.get(component["id"], [])
                ]
                matches = [
                    obj
                    for obj in semantic_objects
                    if any(
                        pattern in str(obj.get("name", "")).casefold()
                        for pattern in patterns
                    )
                ]
                if not matches:
                    functional_issues.append(
                        f"{row['stateId']} component {component['id']} has no semantic object readback matching {mappings_by_id.get(component['id'], [])}"
                    )
        functional_evidence.append(
            f"{len(components)} canonical components checked across {len(rows)} states using Blender object names and semantic roles"
        )
        functional_evidence.append(
            f"{COMPONENT_EVIDENCE_MAP.relative_to(ROOT).as_posix()} sha256={sha256_file(COMPONENT_EVIDENCE_MAP)}"
        )
        functional_evidence_binding = {
            "mode": "COMPONENT_OBJECT_MAP",
            "sources": [
                {
                    "path": COMPONENT_EVIDENCE_MAP.relative_to(ROOT).as_posix(),
                    "sha256": sha256_file(COMPONENT_EVIDENCE_MAP),
                },
                {
                    "path": component_evidence_path.relative_to(ROOT).as_posix(),
                    "sha256": sha256_file(component_evidence_path),
                },
            ],
        }
    functional_status = "PASS" if not functional_issues else "FAIL"
    checks = [
        _check(
            "canon_binding",
            "technical",
            binding_status,
            [str(authority_path), str(canon_path), str(build_report_path)],
            binding_issues,
        ),
        _check(
            "geometry_and_states",
            "geometric",
            geometry_status,
            [f"{len(rows)} state rows checked"],
            geometry_issues,
        ),
        _check(
            "technical_budgets",
            "technical",
            technical_status,
            ["triangle, material, UV, topology and volume report fields"],
            technical_issues,
        ),
        _check(
            "functional_components",
            "functional",
            functional_status,
            functional_evidence,
            functional_issues,
        ),
        _check(
            "visual_packet",
            "visual",
            visual_status,
            [f"visualPacket.status={canon['visualPacket']['status']}"],
            (
                []
                if visual_status == "PASS"
                else [
                    "required multimodal boards are specified but not all hash-bound"
                ]
            ),
        ),
        _check(
            "perceptual_readability",
            "perceptual",
            visual_status,
            [
                "one-second, mobile, lighting, state and repetition boards required"
            ],
            (
                []
                if visual_status == "PASS"
                else [
                    "perceptual comparison to the canon still requires bound review evidence"
                ]
            ),
        ),
        _check(
            "human_authority",
            "human",
            human_status,
            [f"approval.status={canon['approval']['status']}"],
            (
                []
                if human_status == "PASS"
                else ["human canon lock is pending"]
            ),
        ),
    ]
    statuses = [item["status"] for item in checks]
    if "FAIL" in statuses:
        status = "FAIL"
    elif "BLOCKED" in statuses:
        status = "BLOCKED"
    elif "UNKNOWN" in statuses:
        status = "UNKNOWN"
    elif "PARTIAL" in statuses:
        status = "PARTIAL"
    else:
        status = "PASS"
    production_eligible = (
        status == "PASS"
        and authority["mode"] == "PRODUCTION"
        and canon["status"] == "LOCKED"
        and canon["visualPacket"]["status"] == "COMPLETE"
        and canon["approval"]["status"] == "APPROVED"
    )
    blocking = _unique(
        [
            issue
            for item in checks
            if item["status"] != "PASS"
            for issue in item["issues"]
        ]
    )
    value = {
        "$schema": "https://roblox-top1.local/schemas/canon-compliance-report.schema.json",
        "schemaVersion": "1.0.0",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": status,
        "canon": {
            "canonId": canon["canonId"],
            "path": canon_path.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(canon_path),
            "status": canon["status"],
        },
        "build": {
            "reportPath": build_report_path.relative_to(ROOT).as_posix(),
            "reportSha256": sha256_file(build_report_path),
            "assetId": canon["assetId"],
            "territoryId": canon["territoryId"],
            "stateIds": row_states,
        },
        "functionalEvidence": functional_evidence_binding,
        "checks": checks,
        "productionEligible": production_eligible,
        "blockingReasons": blocking,
    }
    errors = validate_with_schema(value, SCHEMA)
    if errors:
        raise RuntimeError("canon compliance report invalid: " + "; ".join(errors))
    write_json(output, value)
    return value


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a hash-bound canon compliance report."
    )
    parser.add_argument("canon", type=Path)
    parser.add_argument("build_report", type=Path)
    parser.add_argument("generation_authority", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--component-evidence", type=Path)
    args = parser.parse_args()
    canon_path = args.canon.resolve()
    build_path = args.build_report.resolve()
    authority_path = args.generation_authority.resolve()
    canon = load_json(canon_path)
    output = args.output or (
        ROOT
        / "build/canon-compliance"
        / canon["territoryId"]
        / f"{canon['assetId']}.json"
    )
    result = build_report(
        canon_path,
        build_path,
        authority_path,
        output.resolve(),
        args.component_evidence.resolve()
        if args.component_evidence
        else None,
    )
    print(
        f"[{result['status']}] {result['canon']['canonId']} compliance: {output}"
    )
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
