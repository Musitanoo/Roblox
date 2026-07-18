from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.art.common import ArtSystemError, ROOT, validate_with_schema
from tools.art.simulate_complete_workflow import (
    STAGE_ORDER,
    _simulate_physical_mobile,
    _simulate_studio_simulator,
    assert_simulation_output,
)


def _report_fixture() -> dict[str, object]:
    digest = "0" * 64
    stages = []
    for order, stage_id in enumerate(STAGE_ORDER, start=1):
        stages.append(
            {
                "id": stage_id,
                "order": order,
                "evidenceClass": (
                    "REAL_LOCAL"
                    if stage_id
                    in {
                        "static_contracts",
                        "blender_full_build",
                        "sixth_asset_transfer",
                        "studio_golden_scene",
                        "production_boundary",
                    }
                    else "SYNTHETIC_DOUBLE"
                ),
                "status": "PASS",
                "assertions": 1,
                "artifact": {
                    "path": (
                        "build/simulations/complete-workflow/current/"
                        f"stages/{order:02d}-{stage_id}.json"
                    ),
                    "bytes": 1,
                    "sha256": digest,
                },
            }
        )
    return {
        "$schema": "https://roblox-top1.local/schemas/workflow-simulation-report.schema.json",
        "schemaVersion": "1.0.0",
        "simulationId": "complete-workflow-current",
        "generatedAt": "2026-07-17T00:00:00Z",
        "mode": "SIMULATION_ONLY",
        "selectedTerritory": "salvaged-frontier",
        "status": "PASS",
        "productionApproved": False,
        "authorityBoundary": {
            "syntheticEvidenceIsProductionEvidence": False,
            "humanAuthoritySimulated": True,
            "externalSystemsMutated": False,
            "realApprovalUnchanged": True,
            "simulationPassDoesNotImplyProductionPass": True,
        },
        "stages": stages,
        "containment": {
            "outputRoot": "build/simulations/complete-workflow/current",
            "protectedSurfaceDigestBefore": digest,
            "protectedSurfaceDigestAfter": digest,
            "protectedSurfacesUnchanged": True,
            "networkCalls": 0,
            "studioMutations": 0,
            "cloudMutations": 0,
            "secretsRead": False,
            "productionValidatorRejectedSyntheticMobile": True,
            "productionValidatorRejectedSyntheticSimulator": True,
        },
        "realProductionStatus": {
            "status": "BLOCKED",
            "implementationStatus": "BLOCKED",
            "productionApproved": False,
            "reportPath": (
                "assets-3d/defense-barricade-small/qa/final-report.json"
            ),
            "sha256": digest,
        },
        "evidencePackageSha256": digest,
        "limitations": [
            "Synthetic humans are not real approval authority.",
            "Synthetic mobile metrics are not physical measurements.",
            "Synthetic cloud receipts are not Roblox publication evidence.",
            "Synthetic Studio state is not an active DataModel playtest.",
        ],
        "issues": [],
    }


def test_simulation_report_is_closed_and_forbids_production_approval() -> None:
    schema = ROOT / "schemas/workflow-simulation-report.schema.json"
    report = _report_fixture()
    assert validate_with_schema(report, schema) == []
    report["productionApproved"] = True
    assert validate_with_schema(report, schema)


def test_simulation_output_is_confined_to_dedicated_root() -> None:
    valid = ROOT / "build/simulations/complete-workflow/test-run"
    assert assert_simulation_output(valid) == valid.resolve()
    with pytest.raises(ArtSystemError, match="must remain under"):
        assert_simulation_output(ROOT / "evidence/human")
    with pytest.raises(ArtSystemError, match="may not replace"):
        assert_simulation_output(ROOT / "build/simulations/complete-workflow")


def test_synthetic_mobile_and_simulator_pass_only_inside_their_root(
    tmp_path: Path,
) -> None:
    output = tmp_path / "output"
    evidence_root = tmp_path / "evidence-root"
    mobile_stage, _ = _simulate_physical_mobile(output, evidence_root)
    simulator_stage, _ = _simulate_studio_simulator(output, evidence_root)
    assert mobile_stage["status"] == "PASS"
    assert simulator_stage["status"] == "PASS"
    assert mobile_stage["evidenceClass"] == "SYNTHETIC_DOUBLE"
    assert simulator_stage["evidenceClass"] == "SYNTHETIC_DOUBLE"
    for filename in ("microprofiler.json", "scene-analysis.json"):
        payload = json.loads(
            (
                evidence_root
                / "evidence/mobile/simulation-only"
                / filename
            ).read_text(encoding="utf-8")
        )
        assert payload["simulationOnly"] is True
        assert payload["source"] == "roblox_studio"


def test_runner_exposes_simulation_without_external_mutation_flags() -> None:
    runner = (ROOT / "scripts/art-direction.ps1").read_text(encoding="utf-8")
    assert "'simulate-workflow'" in runner
    branch = runner[
        runner.index("        'simulate-workflow' {") :
        runner.index("        'verify-blender' {")
    ]
    for forbidden in (
        "--confirm-publish",
        "--apply",
        "-ConfirmPublish",
        "-Apply",
    ):
        assert forbidden not in branch
    assert "tools.art.simulate_complete_workflow" in branch
    assert "'full'" in branch


def test_simulator_has_no_network_or_process_control_imports() -> None:
    source = (
        ROOT / "tools/art/simulate_complete_workflow.py"
    ).read_text(encoding="utf-8")
    for forbidden in (
        "import requests",
        "import urllib",
        "import subprocess",
        "os.environ",
    ):
        assert forbidden not in source
