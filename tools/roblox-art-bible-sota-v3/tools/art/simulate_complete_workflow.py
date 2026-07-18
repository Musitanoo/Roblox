from __future__ import annotations

"""Run a complete, isolated, non-production workflow simulation.

This module deliberately exercises human and external gates with synthetic
doubles. It never calls a browser, Roblox Open Cloud, Roblox Studio, or a
physical device, and it never writes an authoritative lock.
"""

import argparse
import copy
import json
import shutil
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any

from PIL import Image

from tools.art import evidence_validation
from tools.art import validate_performance_report as performance_validator
from tools.art import validate_studio_simulator_report as simulator_validator
from tools.art.blind_study import (
    _expert_assignments,
    _participant_assignments,
    seal,
)
from tools.art.build_visual_canons import ASSETS, check_all
from tools.art.common import (
    PROJECT_ROOT,
    ROOT,
    ArtSystemError,
    canonical_json_bytes,
    load_json,
    rel,
    sha256_bytes,
    sha256_file,
    validate_with_schema,
    write_json,
)
from tools.art.lock_visual_canon import create_lock
from tools.art.visual_canon_evidence import compute_evidence_package_sha256
from tools.art.precanonical import ASSESSMENT_KEYS
from tools.art.precanonical_campaign import (
    REQUIRED_MODEL,
    init_campaign,
    verify_campaign,
)
from tools.art.precanonical_operator import CampaignOperatorSession
from tools.art.score_territories import score
from tools.art.validate_build_report import validate_report as validate_build_report
from tools.art.validate_studio_report import validate_report as validate_studio_report
from tools.art.validate_transfer_report import validate_report as validate_transfer_report


SIMULATION_ROOT = ROOT / "build/simulations/complete-workflow"
DEFAULT_OUTPUT = SIMULATION_ROOT / "current"
SELECTED_TERRITORY = "salvaged-frontier"
TERRITORIES = (
    "industrial-toy-defense",
    "salvaged-frontier",
    "clean-tactical-diorama",
)
PROTECTED_SURFACES = (
    ROOT / "art/art-lock.json",
    ROOT / "art/canonical-visuals/locks",
    ROOT / "art/decision/founder-direction-decision.json",
    ROOT / "art/references/provenance.json",
    ROOT / "evidence/human/art-direction-study-v1/study-manifest.json",
    PROJECT_ROOT / "assets-3d/defense-barricade-small/qa/final-report.json",
)
STAGE_ORDER = (
    "static_contracts",
    "precanonical_campaign",
    "blender_full_build",
    "sixth_asset_transfer",
    "studio_golden_scene",
    "studio_simulator",
    "physical_mobile",
    "blind_human_study",
    "visual_canon_locks",
    "cloud_publication_update",
    "studio_integration_rollback",
    "production_boundary",
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def assert_simulation_output(output: Path) -> Path:
    resolved = output.resolve()
    root = SIMULATION_ROOT.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ArtSystemError(
            f"Simulation output must remain under {root}: {resolved}"
        ) from exc
    if resolved == root:
        raise ArtSystemError("Simulation output may not replace its root directory")
    return resolved


def _path_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"path": str(path), "kind": "absent", "sha256": "0" * 64}
    if path.is_file():
        return {
            "path": str(path),
            "kind": "file",
            "sha256": sha256_file(path),
        }
    entries = []
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        entries.append(
            {
                "path": item.relative_to(path).as_posix(),
                "sha256": sha256_file(item),
            }
        )
    return {
        "path": str(path),
        "kind": "directory",
        "sha256": sha256_bytes(canonical_json_bytes(entries)),
    }


def protected_surface_digest() -> str:
    states = [_path_state(path) for path in PROTECTED_SURFACES]
    return sha256_bytes(canonical_json_bytes(states))


def _png_bytes(index: int, size: tuple[int, int] = (512, 512)) -> bytes:
    stream = BytesIO()
    color = ((41 * index) % 255, (83 * index) % 255, (127 * index) % 255)
    Image.new("RGB", size, color).save(stream, format="PNG")
    return stream.getvalue()


def _write_bytes(path: Path, value: bytes) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value)
    return {
        "path": path,
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _write_stage(
    output: Path,
    stage_id: str,
    evidence_class: str,
    assertions: list[str],
    details: dict[str, Any],
) -> dict[str, Any]:
    if not assertions:
        raise ArtSystemError(f"{stage_id}: at least one assertion is required")
    stage_path = output / "stages" / f"{STAGE_ORDER.index(stage_id) + 1:02d}-{stage_id}.json"
    payload = {
        "schemaVersion": "1.0.0",
        "simulationOnly": True,
        "stageId": stage_id,
        "status": "PASS",
        "assertions": assertions,
        "details": details,
        "productionApproved": False,
    }
    write_json(stage_path, payload)
    return {
        "id": stage_id,
        "order": STAGE_ORDER.index(stage_id) + 1,
        "evidenceClass": evidence_class,
        "status": "PASS",
        "assertions": len(assertions),
        "artifact": {
            "path": rel(stage_path),
            "bytes": stage_path.stat().st_size,
            "sha256": sha256_file(stage_path),
        },
    }


def _validate_static_contracts(output: Path) -> dict[str, Any]:
    static_report_path = ROOT / "evidence/static-validation-report.json"
    static_report = load_json(static_report_path)
    if static_report.get("status") != "PASS":
        raise ArtSystemError("Static validation report is not PASS")
    canon_issues = check_all(require_locked=False)
    if canon_issues:
        raise ArtSystemError(f"Visual canon drift: {canon_issues}")
    return _write_stage(
        output,
        "static_contracts",
        "REAL_LOCAL",
        [
            "Static schema and semantic validation is PASS.",
            "The generated visual-canon catalog has no drift.",
            "Simulation authority remains non-production.",
        ],
        {
            "staticReport": rel(static_report_path),
            "staticReportSha256": sha256_file(static_report_path),
            "visualCanonIssueCount": 0,
        },
    )


def _simulation_review() -> dict[str, Any]:
    return {
        "decision": "HUMAN_SELECTED",
        "reviewer": "SIMULATED_REVIEWER",
        "assessment": {key: "PASS" for key in ASSESSMENT_KEYS},
        "preserve": [
            "Preserve the simulated canonical silhouette and stable anchors."
        ],
        "correct": [],
        "forbidNext": [
            "Do not invent a component during this simulation."
        ],
    }


def _simulate_precanonical_campaign(output: Path) -> dict[str, Any]:
    campaign_root = output / "precanonical/campaign"
    campaign_path = init_campaign(
        campaign_root,
        campaign_id="complete-workflow-simulation",
    )
    operator = CampaignOperatorSession(
        campaign_path,
        output / "precanonical/runtime",
    )
    accepted_hashes: list[str] = []
    parent_bound_count = 0
    for index in range(1, 17):
        before = operator.public_state()
        if before["status"] != "READY_FOR_HUMAN_WEB_SUBMISSION":
            raise ArtSystemError(
                f"Precanonical task {index} was not ready: {before['status']}"
            )
        imported = operator.import_image(
            f"simulation-state-{index:02d}.png",
            _png_bytes(index),
            {
                "exactSubmissionTextUsed": True,
                "noPromptRewrite": True,
                "exactlyOneGenerationRequested": True,
                "oneResultDownloaded": True,
                "noAutomaticRetry": True,
            },
            REQUIRED_MODEL,
            True,
        )
        if imported["status"] != "VISUAL_REVIEW_REQUIRED":
            raise ArtSystemError(f"Precanonical import {index} did not reach review")
        after = operator.record_review(_simulation_review())
        campaign = load_json(campaign_path)
        task = campaign["tasks"][index - 1]
        result_path = campaign_path.parent / task["acceptedResult"]["path"]
        accepted_hashes.append(sha256_file(result_path))
        request_path = campaign_path.parent / task["attempts"][-1]["request"]["path"]
        request = load_json(request_path)
        if request["parentResult"] is not None:
            parent_bound_count += 1
        expected = (
            "CAMPAIGN_COMPLETE"
            if index == 16
            else "READY_FOR_HUMAN_WEB_SUBMISSION"
        )
        if after["status"] != expected:
            raise ArtSystemError(
                f"Precanonical task {index} ended as {after['status']}, expected {expected}"
            )
    campaign = verify_campaign(campaign_path)
    if campaign["status"] != "COMPLETE":
        raise ArtSystemError("Synthetic precanonical campaign did not complete")
    if len(set(accepted_hashes)) != 16:
        raise ArtSystemError("Every object-state generation must be distinct")
    if parent_bound_count != 10:
        raise ArtSystemError(
            f"Expected ten state-continuity parent bindings, observed {parent_bound_count}"
        )
    return _write_stage(
        output,
        "precanonical_campaign",
        "SYNTHETIC_DOUBLE",
        [
            "Six objects and sixteen applicable states were compiled.",
            "Each object-state received exactly one distinct synthetic image.",
            "All state successors were bound to their accepted predecessor.",
            "All sixteen synthetic reviews advanced to campaign completion.",
            "Every precanonical review retained productionApproved=false.",
        ],
        {
            "campaign": rel(campaign_path),
            "campaignSha256": sha256_file(campaign_path),
            "taskCount": 16,
            "completedTaskCount": campaign["progress"]["completedTasks"],
            "completedObjectCount": campaign["progress"]["completedObjects"],
            "distinctResultCount": len(set(accepted_hashes)),
            "parentBoundStateCount": parent_bound_count,
        },
    )


def _validate_blender_full_build(output: Path) -> dict[str, Any]:
    territory_results: list[dict[str, Any]] = []
    for territory in TERRITORIES:
        report_path = ROOT / f"build/{territory}/build-report.json"
        issues = validate_build_report(report_path, require_complete=True)
        if issues:
            raise ArtSystemError(f"{territory} full build invalid: {issues}")
        report = load_json(report_path)
        territory_results.append(
            {
                "territoryId": territory,
                "renderMode": report["renderMode"],
                "renderCount": report["actualRenderCount"],
                "reportSha256": sha256_file(report_path),
            }
        )
    full_path = ROOT / "evidence/blender/full-evidence.json"
    full = load_json(full_path)
    full_schema_issues = validate_with_schema(
        full,
        ROOT / "schemas/full-evidence.schema.json",
    )
    if full_schema_issues or full.get("status") != "PASS":
        raise ArtSystemError(
            f"Full Blender evidence invalid: {full_schema_issues or full.get('status')}"
        )
    verification_path = ROOT / "evidence/blender/blender-verification-report.json"
    verification = load_json(verification_path)
    verification_issues = validate_with_schema(
        verification,
        ROOT / "schemas/blender-verification-report.schema.json",
    )
    if verification_issues or verification.get("status") != "PASS":
        raise ArtSystemError(
            "Blender A/B verification is not current and passing"
        )
    return _write_stage(
        output,
        "blender_full_build",
        "REAL_LOCAL",
        [
            "All three full build reports pass complete artifact validation.",
            "Every full render referenced by the evidence report is present and hash-bound.",
            "All three A/B Blender determinism checks are PASS.",
            "Blender remains preflight evidence rather than Studio authority.",
        ],
        {
            "territories": territory_results,
            "fullEvidence": rel(full_path),
            "fullEvidenceSha256": sha256_file(full_path),
            "totalExpectedRenderCount": full["totalExpectedRenderCount"],
            "totalActualRenderCount": full["totalActualRenderCount"],
            "totalStressRenderCount": full["totalStressRenderCount"],
            "verificationReport": rel(verification_path),
            "verificationReportSha256": sha256_file(verification_path),
        },
    )


def _validate_sixth_asset_transfer(output: Path) -> dict[str, Any]:
    report_path = ROOT / "evidence/transfer/turret-fast-v1/report.json"
    result = validate_transfer_report(report_path, require_approved=False)
    report = load_json(report_path)
    if result["status"] != "PASS":
        raise ArtSystemError(f"Automated transfer proof invalid: {result['issues']}")
    if report["automatedStatus"] != "PASS":
        raise ArtSystemError("Sixth-asset automated transfer status is not PASS")
    queue_path = ROOT / "build/studio-import-transfer/manifest.json"
    queue = load_json(queue_path)
    entries = queue.get("entries", queue.get("items", []))
    if len(entries) != 9:
        raise ArtSystemError(
            f"Transfer Studio queue must contain nine candidates, observed {len(entries)}"
        )
    return _write_stage(
        output,
        "sixth_asset_transfer",
        "REAL_LOCAL",
        [
            "The independent sixth asset passes automated transfer validation.",
            "Three territories and three states produce nine portable candidates.",
            "Human transfer approval remains outside automated authority.",
        ],
        {
            "report": rel(report_path),
            "reportSha256": sha256_file(report_path),
            "automatedStatus": report["automatedStatus"],
            "realOverallStatus": report["overallStatus"],
            "queue": rel(queue_path),
            "candidateCount": len(entries),
        },
    )


def _validate_studio_reports(output: Path) -> dict[str, Any]:
    reports = []
    for territory in TERRITORIES:
        report_path = ROOT / f"evidence/studio/{territory}/studio-report.json"
        result = validate_studio_report(report_path, require_pass=True)
        if result["status"] != "PASS":
            raise ArtSystemError(f"{territory} Studio report invalid: {result['issues']}")
        reports.append(
            {
                "territoryId": territory,
                "status": result["reportedStatus"],
                "path": rel(report_path),
                "sha256": sha256_file(report_path),
            }
        )
    return _write_stage(
        output,
        "studio_golden_scene",
        "REAL_LOCAL",
        [
            "All three Golden Scene reports pass their closed schema.",
            "Every report contains staging, hierarchy, state, lighting, camera and reuse checks.",
            "No raw creator, place or API key is present.",
        ],
        {"reports": reports},
    )


def _artifact_record(root: Path, relative: str, kind: str, source: str) -> dict[str, Any]:
    path = root / relative
    if path.suffix.lower() in {".png", ".jpg", ".jpeg"}:
        payload = _png_bytes(len(relative), (640, 360))
    elif path.suffix.lower() == ".json":
        payload = canonical_json_bytes(
            {
                "artifactKind": kind,
                "simulationOnly": True,
                "source": source,
            }
        ) + b"\n"
    else:
        payload = f"SIMULATION_ONLY {kind}\n".encode("utf-8")
    written = _write_bytes(path, payload)
    return {
        "kind": kind,
        "path": relative,
        "bytes": written["bytes"],
        "sha256": written["sha256"],
        "source": source,
    }


def _with_simulated_artifact_root(
    root: Path,
    callback: Any,
) -> dict[str, Any]:
    previous = evidence_validation.ROOT
    evidence_validation.ROOT = root
    try:
        return callback()
    finally:
        evidence_validation.ROOT = previous


def _simulate_studio_simulator(
    output: Path,
    evidence_root: Path,
) -> tuple[dict[str, Any], Path]:
    source_path = ROOT / "evidence/mobile/studio-simulator/report.json"
    report = copy.deepcopy(load_json(source_path))
    report["status"] = "PASS"
    report["generatedAt"] = _utc_now()
    report["territoryId"] = SELECTED_TERRITORY
    report["capabilities"] = {
        key: {
            "status": "PASS",
            "diagnostic": f"SIMULATION_ONLY contract double for {key}.",
            "attemptCount": 1,
        }
        for key in ("libmp", "sceneAnalysis", "screenCapture")
    }
    report["visualChecks"] = {
        "landscapeExactPixels": True,
        "portraitExactPixels": True,
        "stateCueReadable": True,
        "interactionCueReadable": True,
        "source": "roblox_studio_capture",
    }
    report["issues"] = []
    report["artifacts"] = [
        _artifact_record(
            evidence_root,
            "evidence/mobile/simulation-only/studio-capture.png",
            "studio_capture",
            "roblox_studio",
        ),
        _artifact_record(
            evidence_root,
            "evidence/mobile/simulation-only/microprofiler.json",
            "microprofiler_dump",
            "roblox_studio",
        ),
        _artifact_record(
            evidence_root,
            "evidence/mobile/simulation-only/scene-analysis.json",
            "scene_analysis_dump",
            "roblox_studio",
        ),
    ]
    report_path = (
        evidence_root / "evidence/mobile/studio-simulator/report.json"
    )
    write_json(report_path, report)
    internal = _with_simulated_artifact_root(
        evidence_root,
        lambda: simulator_validator.validate_report(
            report_path,
            require_pass=True,
        ),
    )
    if internal["status"] != "PASS":
        raise ArtSystemError(f"Synthetic Studio simulator invalid: {internal['issues']}")
    production_probe = simulator_validator.validate_report(
        report_path,
        require_pass=True,
    )
    if production_probe["status"] == "PASS":
        raise ArtSystemError(
            "Synthetic Studio simulator evidence escaped its sandbox"
        )
    stage = _write_stage(
        output,
        "studio_simulator",
        "SYNTHETIC_DOUBLE",
        [
            "Exact landscape and portrait readbacks were simulated.",
            "Graybox/candidate 30 and 100-copy structures were simulated.",
            "Profiler, scene-analysis and capture capabilities reached the PASS branch.",
            "The normal production root rejects every sandbox-only artifact.",
        ],
        {
            "report": rel(report_path),
            "reportSha256": sha256_file(report_path),
            "internalValidation": internal,
            "productionProbeStatus": production_probe["status"],
            "productionProbeIssueCount": len(production_probe["issues"]),
        },
    )
    return stage, report_path


def _metric_summary(
    *,
    frame_median: float,
    frame_p95: float,
    frame_p99: float,
    frame_max: float,
    fps_median: float,
    fps_minimum: float,
    memory_median: float,
    memory_p95: float,
    memory_max: float,
) -> dict[str, Any]:
    return {
        "sampleCount": 900,
        "frameTimeMs": {
            "median": frame_median,
            "p95": frame_p95,
            "p99": frame_p99,
            "mad": 1.0,
            "max": frame_max,
        },
        "fps": {"median": fps_median, "minimum": fps_minimum},
        "memoryMb": {
            "median": memory_median,
            "p95": memory_p95,
            "max": memory_max,
            "byCategory": {
                "Instances": memory_median * 0.4,
                "Graphics": memory_median * 0.6,
            },
        },
        "crashes": 0,
        "thermal": {
            "start": "nominal",
            "end": "fair",
            "throttleObserved": False,
            "method": "SIMULATION_ONLY threshold-contract double",
        },
    }


def _mobile_artifact(
    root: Path,
    filename: str,
    kind: str,
    payload: bytes,
) -> dict[str, Any]:
    relative = f"evidence/mobile/simulation-only/{filename}"
    written = _write_bytes(root / relative, payload)
    return {
        "kind": kind,
        "path": relative,
        "bytes": written["bytes"],
        "sha256": written["sha256"],
    }


def _simulate_physical_mobile(
    output: Path,
    evidence_root: Path,
) -> tuple[dict[str, Any], Path]:
    graybox = _metric_summary(
        frame_median=16.0,
        frame_p95=20.0,
        frame_p99=24.0,
        frame_max=30.0,
        fps_median=60.0,
        fps_minimum=40.0,
        memory_median=600.0,
        memory_p95=650.0,
        memory_max=700.0,
    )
    candidate = _metric_summary(
        frame_median=16.8,
        frame_p95=21.0,
        frame_p99=25.0,
        frame_max=32.0,
        fps_median=58.0,
        fps_minimum=38.0,
        memory_median=615.0,
        memory_p95=670.0,
        memory_max=720.0,
    )
    artifacts = [
        _mobile_artifact(
            evidence_root,
            "raw-metrics.json",
            "raw_metrics",
            b'{"simulationOnly":true,"samples":900}\n',
        ),
        _mobile_artifact(
            evidence_root,
            "device.log",
            "device_log",
            b"SIMULATION_ONLY device log\n",
        ),
        _mobile_artifact(
            evidence_root,
            "landscape.png",
            "landscape_screenshot",
            _png_bytes(101, (640, 360)),
        ),
        _mobile_artifact(
            evidence_root,
            "portrait.png",
            "portrait_screenshot",
            _png_bytes(102, (360, 640)),
        ),
        _mobile_artifact(
            evidence_root,
            "microprofiler.png",
            "microprofiler_screenshot",
            _png_bytes(103, (640, 360)),
        ),
    ]
    report = {
        "$schema": "https://roblox-top1.local/schemas/performance-report.schema.json",
        "schemaVersion": "2.0.0",
        "status": "PASS",
        "territoryId": SELECTED_TERRITORY,
        "generatedAt": _utc_now(),
        "device": {
            "deviceIdHash": sha256_bytes(b"SIMULATION_ONLY_DEVICE"),
            "manufacturer": "Audit Double",
            "model": "Synthetic Low Tier",
            "osName": "SimulationOS",
            "osVersion": "1.0",
            "chipset": "SyntheticChip",
            "ramGb": 4,
            "display": {
                "widthPx": 640,
                "heightPx": 360,
                "densityDpi": 260,
                "orientation": "both",
            },
            "refreshRateHz": 60,
            "graphicsQualityLevel": 1,
        },
        "protocol": {
            "protocolVersion": "2.0.0",
            "placeId": 1,
            "placeVersion": 1,
            "experienceBuildSha256": sha256_bytes(
                b"SIMULATION_ONLY_EXPERIENCE"
            ),
            "coldLaunch": True,
            "warmupSeconds": 60,
            "activeSessionMinutes": 15,
            "grayboxPasses": 5,
            "candidatePasses": 5,
            "sequence": ["A", "B"] * 5,
            "sameCameraPath": True,
            "sameServerState": True,
            "sameGraphicsQuality": True,
        },
        "graybox": graybox,
        "candidate": candidate,
        "regressions": {
            "frameTimeMedianPct": 5.0,
            "frameTimeP95Pct": 5.0,
            "memoryP95Mb": 20.0,
            "minimumFpsDelta": -2.0,
            "thresholds": {
                "maxFrameTimeMedianPct": 10.0,
                "maxFrameTimeP95Pct": 15.0,
                "maxMemoryP95Mb": 64.0,
                "minimumCandidateFps": 30.0,
                "crashesAllowed": 0,
                "thermalThrottleAllowed": False,
            },
            "pass": True,
        },
        "visualChecks": {
            "landscape640x360": True,
            "narrowPortrait360x640": True,
            "stateReadability": True,
            "interactionReadability": True,
            "captureViewportVerified": True,
        },
        "artifacts": artifacts,
        "issues": [],
    }
    report_path = (
        evidence_root / "evidence/mobile/physical/performance-report.json"
    )
    write_json(report_path, report)
    internal = _with_simulated_artifact_root(
        evidence_root,
        lambda: performance_validator.validate_report(
            report_path,
            require_pass=True,
        ),
    )
    if internal["status"] != "PASS":
        raise ArtSystemError(f"Synthetic physical mobile invalid: {internal['issues']}")
    production_probe = performance_validator.validate_report(
        report_path,
        require_pass=True,
    )
    if production_probe["status"] == "PASS":
        raise ArtSystemError("Synthetic physical-device evidence escaped its sandbox")
    stage = _write_stage(
        output,
        "physical_mobile",
        "SYNTHETIC_DOUBLE",
        [
            "The full cold-launch, warm-up, A/B and sustained-session contract was populated.",
            "Metric ordering and derived regression calculations pass.",
            "Required raw, log, landscape, portrait and profiler artifacts are hash-bound.",
            "The normal production root rejects every sandbox-only artifact.",
        ],
        {
            "report": rel(report_path),
            "reportSha256": sha256_file(report_path),
            "internalValidation": internal,
            "productionProbeStatus": production_probe["status"],
            "productionProbeIssueCount": len(production_probe["issues"]),
        },
    )
    return stage, report_path


def _prepare_study_evidence_root(
    output: Path,
    mobile_report_path: Path,
) -> Path:
    evidence_root = output / "synthetic-evidence-root"
    copies = (
        (
            ROOT / "evidence/blender/visual-quality-report.json",
            evidence_root / "evidence/blender/visual-quality-report.json",
        ),
        (
            ROOT / "evidence/blender/blender-verification-report.json",
            evidence_root
            / "evidence/blender/blender-verification-report.json",
        ),
    )
    for source, destination in copies:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    for territory in TERRITORIES:
        source = ROOT / f"evidence/studio/{territory}/studio-report.json"
        destination = (
            evidence_root / f"evidence/studio/{territory}/studio-report.json"
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
    provenance = copy.deepcopy(
        load_json(ROOT / "art/references/provenance.json")
    )
    provenance["humanApproval"] = {
        "status": "APPROVED",
        "reviewer": "SIMULATED_REVIEWER",
        "reviewedAt": _utc_now(),
        "decisionRecord": rel(output / "human-study/selection-decision.json"),
    }
    write_json(evidence_root / "art/references/provenance.json", provenance)
    write_json(
        evidence_root / "evidence/blender/cvd-report.json",
        {
            "schemaVersion": "SIMULATION_ONLY",
            "status": "PASS",
            "productionApproved": False,
        },
    )
    physical_destination = (
        evidence_root / "evidence/mobile/physical/performance-report.json"
    )
    if mobile_report_path.resolve() != physical_destination.resolve():
        physical_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(mobile_report_path, physical_destination)
    return evidence_root


def _refresh_copied_study_manifest(study_root: Path) -> None:
    path_by_kind = {
        "participant_kit": study_root / "participant-kit.zip",
        "expert_kit": study_root / "expert-kit.zip",
        "public_manifest": study_root / "public/study-public-manifest.json",
        "participant_interface": study_root / "public/participant/index.html",
        "expert_interface": study_root / "public/expert/index.html",
        "answer_key": study_root / "operator/answer-key.json",
        "draft_submissions": (
            study_root / "operator/reviewer-submissions.draft.json"
        ),
        "private_blind_map": study_root / "private/blind-map.json",
    }
    manifest_path = study_root / "study-manifest.json"
    manifest = load_json(manifest_path)
    manifest["status"] = "READY_FOR_HUMAN_COLLECTION"
    manifest["artifacts"] = [
        {
            **artifact,
            "path": rel(path_by_kind[artifact["kind"]]),
            "sha256": sha256_file(path_by_kind[artifact["kind"]]),
        }
        for artifact in manifest["artifacts"]
        if artifact["kind"] in path_by_kind
    ]
    write_json(manifest_path, manifest)


def _simulate_blind_study(
    output: Path,
    evidence_root: Path,
) -> tuple[dict[str, Any], Path]:
    source = ROOT / "evidence/human/art-direction-study-v1"
    study_root = output / "human-study"
    shutil.copytree(source, study_root)
    for folder in (
        study_root / "sessions/participants",
        study_root / "sessions/experts",
    ):
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
    _refresh_copied_study_manifest(study_root)

    public = load_json(study_root / "public/study-public-manifest.json")
    answers = load_json(study_root / "operator/answer-key.json")["answers"]
    blind_map = load_json(study_root / "private/blind-map.json")
    selected_label = next(
        label
        for label, territory in blind_map["mapping"].items()
        if territory == SELECTED_TERRITORY
    )
    assignments = _participant_assignments(
        public["publicPackageId"],
        public["stimuli"],
    )
    generated_at = _utc_now()
    device_classes = ("mobile", "tablet", "desktop")
    for participant_index, (participant_id, assignment) in enumerate(
        assignments.items()
    ):
        responses = []
        for trial_index, trial in enumerate(assignment["trials"]):
            responses.append(
                {
                    "trialIndex": trial_index,
                    "blindLabel": trial["blindLabel"],
                    "taskId": trial["taskId"],
                    "answer": answers[trial["taskId"]],
                    "confidence": 0.95,
                    "exposureMs": 5000,
                    "responseTimeMs": 700 + trial_index,
                }
            )
        write_json(
            study_root
            / "sessions/participants"
            / f"participant-{participant_id}.json",
            {
                "$schema": "https://roblox-top1.local/schemas/participant-session.schema.json",
                "schemaVersion": "1.0.0",
                "studyId": public["studyId"],
                "publicPackageId": public["publicPackageId"],
                "participantId": participant_id,
                "deviceClass": device_classes[
                    participant_index % len(device_classes)
                ],
                "startedAt": generated_at,
                "completedAt": generated_at,
                "responses": responses,
                "exitAnswers": {
                    "mostMemorable": selected_label,
                    "easiestToUnderstand": selected_label,
                    "decisiveCue": (
                        "Simulation-only answer exercising the complete review contract."
                    ),
                },
            },
        )

    rubric = load_json(ROOT / "art/qa/visual-rubric.json")
    expert_assignments = _expert_assignments(public["publicPackageId"])
    for reviewer_id, assignment in expert_assignments.items():
        ratings = []
        for label in ("A", "B", "C"):
            for dimension_id in rubric["dimensions"]:
                ratings.append(
                    {
                        "blindLabel": label,
                        "dimensionId": dimension_id,
                        "score": 5 if label == selected_label else 3,
                        "confidence": 0.95,
                    }
                )
        write_json(
            study_root
            / "sessions/experts"
            / f"expert-{reviewer_id}.json",
            {
                "$schema": "https://roblox-top1.local/schemas/expert-session.schema.json",
                "schemaVersion": "1.0.0",
                "studyId": public["studyId"],
                "publicPackageId": public["publicPackageId"],
                "reviewerId": reviewer_id,
                "reviewerRole": assignment["reviewerRole"],
                "startedAt": generated_at,
                "completedAt": generated_at,
                "ratings": ratings,
                "candidateNotes": {
                    label: (
                        "SIMULATION_ONLY score exercising expert review."
                    )
                    for label in ("A", "B", "C")
                },
            },
        )

    sealed_path = seal(study_root, evidence_root)
    blind_map_path = study_root / "private/blind-map.json"
    scoring = score(sealed_path, blind_map_path)
    scoring_path = study_root / "operator/scoring-report.simulated.json"
    write_json(scoring_path, scoring)
    if scoring["status"] != "COMPLETE":
        raise ArtSystemError(f"Synthetic scoring blocked: {scoring['issues']}")
    selected = next(
        candidate
        for candidate in scoring["candidates"]
        if candidate["territoryId"] == SELECTED_TERRITORY
    )
    if not selected["eligible"]:
        raise ArtSystemError("Selected synthetic candidate was not eligible")
    if scoring["ranking"][0]["territoryId"] != SELECTED_TERRITORY:
        raise ArtSystemError("Synthetic ranking did not preserve selected territory")
    if scoring["automaticSelection"] is not None:
        raise ArtSystemError("Scoring performed a forbidden automatic selection")

    selection_path = study_root / "selection-decision.simulated.json"
    selection = {
        "$schema": "https://roblox-top1.local/schemas/selection-decision.schema.json",
        "schemaVersion": "2.0.0",
        "studyId": public["studyId"],
        "status": "APPROVED",
        "selectedBlindLabel": selected_label,
        "selectedTerritory": SELECTED_TERRITORY,
        "approvedBy": "SIMULATED_REVIEWER",
        "approvedAt": generated_at,
        "rationale": (
            "Simulation-only decision used to exercise the complete lock path. "
            "It is deliberately non-human, non-production and confined to the "
            "workflow simulation sandbox."
        ),
        "scoringReportSha256": sha256_file(scoring_path),
        "blindMapSha256": sha256_file(blind_map_path),
        "rejectedAlternatives": [
            {
                "territoryId": territory,
                "reason": (
                    "Simulation-only rejected alternative used solely to test "
                    "the closed selection-decision contract."
                ),
            }
            for territory in TERRITORIES
            if territory != SELECTED_TERRITORY
        ],
    }
    selection_issues = validate_with_schema(
        selection,
        ROOT / "schemas/selection-decision.schema.json",
    )
    if selection_issues:
        raise ArtSystemError(f"Synthetic selection invalid: {selection_issues}")
    write_json(selection_path, selection)
    stage = _write_stage(
        output,
        "blind_human_study",
        "SYNTHETIC_DOUBLE",
        [
            "Twelve synthetic participant sessions cover all thirty blinded trials.",
            "Four synthetic expert sessions cover all twenty-seven ratings.",
            "Raw sessions seal through the production study contract.",
            "Scoring remains non-selecting and returns a complete ranking.",
            "A separate simulated decision selects the intended territory.",
            "Every study artifact remains under the simulation sandbox.",
        ],
        {
            "studyRoot": rel(study_root),
            "sealedSubmissions": rel(sealed_path),
            "sealedSubmissionsSha256": sha256_file(sealed_path),
            "blindMap": rel(blind_map_path),
            "scoringReport": rel(scoring_path),
            "scoringReportSha256": sha256_file(scoring_path),
            "selectionDecision": rel(selection_path),
            "selectionDecisionSha256": sha256_file(selection_path),
            "participantCount": 12,
            "expertCount": 4,
            "selectedBlindLabel": selected_label,
            "selectedTerritory": SELECTED_TERRITORY,
            "automaticSelection": None,
        },
    )
    return stage, selection_path


def _simulate_visual_canon_locks(
    output: Path,
    selection_path: Path,
) -> dict[str, Any]:
    locks = []
    lock_root_before = _path_state(ROOT / "art/canonical-visuals/locks")
    for asset_index, asset_id in enumerate(ASSETS, start=1):
        canon_path = (
            ROOT
            / "art/canonical-visuals"
            / SELECTED_TERRITORY
            / f"{asset_id}.json"
        )
        canon = load_json(canon_path)
        required_boards = [
            board["id"] for board in canon["visualPacket"]["boards"]
        ]
        if len(required_boards) != 17:
            raise ArtSystemError(
                f"{asset_id}: expected 17 canonical board families"
            )
        boards: dict[str, list[dict[str, Any]]] = {}
        for board_index, board_id in enumerate(required_boards, start=1):
            board_path = (
                output
                / "canon-evidence"
                / asset_id
                / f"{board_index:02d}-{board_id}.png"
            )
            _write_bytes(
                board_path,
                _png_bytes(asset_index * 100 + board_index, (640, 360)),
            )
            boards[board_id] = [
                {
                    "path": rel(board_path),
                    "bytes": board_path.stat().st_size,
                    "sha256": sha256_file(board_path),
                    "mediaType": "image/png",
                    "width": 640,
                    "height": 360,
                }
            ]
        canon_sha = sha256_file(canon_path)
        manifest = {
            "$schema": "https://roblox-top1.local/schemas/visual-canon-evidence.schema.json",
            "schemaVersion": "1.0.0",
            "assetKey": f"simulation_{asset_id}",
            "revision": 1,
            "assetId": asset_id,
            "territoryId": SELECTED_TERRITORY,
            "canonId": canon["canonId"],
            "baseCandidateSha256": canon_sha,
            "evidenceClass": "SYNTHETIC_DOUBLE",
            "generatedAt": _utc_now(),
            "generation": {
                "tool": "r3d canon-packet",
                "toolVersion": "1.0.0",
                "deterministicComposition": True,
                "rawRenderStatus": "SIMULATED",
            },
            "authority": {
                "bindings": [
                    {
                        "role": "canon",
                        "root": "PACKAGE_ROOT",
                        "path": rel(canon_path),
                        "bytes": canon_path.stat().st_size,
                        "sha256": canon_sha,
                    }
                ]
            },
            "boards": boards,
            "humanReviewStatus": "PASS",
            "productionApproved": False,
        }
        manifest["evidencePackageSha256"] = (
            compute_evidence_package_sha256(manifest)
        )
        manifest_path = (
            output / "canon-evidence" / asset_id / "evidence-manifest.json"
        )
        write_json(manifest_path, manifest)
        result = create_lock(
            asset_id,
            SELECTED_TERRITORY,
            manifest_path,
            "SIMULATED_REVIEWER",
            rel(selection_path),
            None,
            False,
        )
        if (
            result["status"] != "PARTIAL"
            or not result["dryRun"]
            or result["mutationPerformed"]
        ):
            raise ArtSystemError(
                f"{asset_id}: simulated canon lock was not a non-mutating dry-run"
            )
        overlay = result["overlay"]
        overlay_issues = validate_with_schema(
            overlay,
            ROOT / "schemas/visual-canon-lock.schema.json",
        )
        if not overlay_issues or not any(
            "REAL_RENDERED" in issue for issue in overlay_issues
        ):
            raise ArtSystemError(
                f"{asset_id}: synthetic overlay was not rejected by the production schema: "
                f"{overlay_issues}"
            )
        overlay_path = output / "canon-locks" / f"{asset_id}.json"
        write_json(overlay_path, overlay)
        locks.append(
            {
                "assetId": asset_id,
                "boardFamilyCount": len(boards),
                "manifest": rel(manifest_path),
                "manifestSha256": sha256_file(manifest_path),
                "overlay": rel(overlay_path),
                "overlaySha256": sha256_file(overlay_path),
                "mutationPerformed": False,
            }
        )
    if _path_state(ROOT / "art/canonical-visuals/locks") != lock_root_before:
        raise ArtSystemError("Simulation mutated authoritative visual-canon locks")
    return _write_stage(
        output,
        "visual_canon_locks",
        "SYNTHETIC_DOUBLE",
        [
            "All six selected canons received exactly seventeen board families.",
            "Every board artifact is present and hash-bound.",
            "Every synthetic preview is rejected by the production lock schema.",
            "The real lock builder remained in dry-run mode.",
            "No authoritative lock file changed.",
        ],
        {"lockCount": len(locks), "locks": locks},
    )


def _simulate_cloud_publication(output: Path) -> dict[str, Any]:
    package_identity = f"sim-{sha256_bytes(b'complete-workflow-package')[:24]}"
    v1 = {
        "simulationOnly": True,
        "operation": "CREATE_PACKAGE_V1",
        "packageIdentity": package_identity,
        "version": 1,
        "networkCalls": 0,
        "status": "PASS",
    }
    v2 = {
        "simulationOnly": True,
        "operation": "UPDATE_SAME_PACKAGE_V2",
        "packageIdentity": package_identity,
        "version": 2,
        "networkCalls": 0,
        "status": "PASS",
    }
    replay_v2 = copy.deepcopy(v2)
    transaction = {
        "schemaVersion": "SIMULATION_ONLY",
        "dryRun": True,
        "externalMutation": False,
        "v1": v1,
        "v2": v2,
        "idempotentReplayV2": replay_v2,
        "sameIdentity": v1["packageIdentity"] == v2["packageIdentity"],
        "idempotentReplay": (
            canonical_json_bytes(v2) == canonical_json_bytes(replay_v2)
        ),
        "productionApproved": False,
    }
    transaction_path = output / "external/cloud-publication.json"
    write_json(transaction_path, transaction)
    if not transaction["sameIdentity"] or not transaction["idempotentReplay"]:
        raise ArtSystemError("Synthetic cloud update did not preserve identity")
    return _write_stage(
        output,
        "cloud_publication_update",
        "SYNTHETIC_DOUBLE",
        [
            "A synthetic v1 package creation completed.",
            "A synthetic v2 update preserved the same package identity.",
            "Replaying v2 is idempotent.",
            "No network call or cloud mutation occurred.",
        ],
        {
            "transaction": rel(transaction_path),
            "transactionSha256": sha256_file(transaction_path),
            "sameIdentity": True,
            "idempotentReplay": True,
            "networkCalls": 0,
            "cloudMutations": 0,
        },
    )


def _simulate_studio_transaction(output: Path) -> dict[str, Any]:
    before = {
        "wrapperName": "DefenseBarricadeSmall",
        "collisionAuthority": "INVISIBLE_SIMPLE_PART",
        "tags": ["DefenseAsset", "Buildable"],
        "attributes": {"AssetKey": "defense_barricade_small", "Version": 1},
        "visualMeshVersion": 1,
    }
    candidate = copy.deepcopy(before)
    candidate["attributes"]["Version"] = 2
    candidate["visualMeshVersion"] = 2
    before_hash = sha256_bytes(canonical_json_bytes(before))
    candidate_hash = sha256_bytes(canonical_json_bytes(candidate))
    rollback = copy.deepcopy(before)
    rollback_hash = sha256_bytes(canonical_json_bytes(rollback))
    if before_hash == candidate_hash:
        raise ArtSystemError("Synthetic Studio update produced no delta")
    if rollback_hash != before_hash:
        raise ArtSystemError("Synthetic Studio rollback did not restore baseline")
    transaction = {
        "schemaVersion": "SIMULATION_ONLY",
        "externalMutation": False,
        "before": before,
        "candidate": candidate,
        "rollback": rollback,
        "beforeSha256": before_hash,
        "candidateSha256": candidate_hash,
        "rollbackSha256": rollback_hash,
        "wrapperPreserved": all(
            before[key] == candidate[key]
            for key in ("wrapperName", "collisionAuthority", "tags")
        ),
        "rollbackExact": rollback_hash == before_hash,
        "productionApproved": False,
    }
    transaction_path = output / "external/studio-transaction.json"
    write_json(transaction_path, transaction)
    if not transaction["wrapperPreserved"] or not transaction["rollbackExact"]:
        raise ArtSystemError("Synthetic Studio transaction violated invariants")
    return _write_stage(
        output,
        "studio_integration_rollback",
        "SYNTHETIC_DOUBLE",
        [
            "The visual version changed while wrapper identity stayed stable.",
            "Collision authority and gameplay tags were preserved.",
            "Rollback restored the exact canonical baseline hash.",
            "No Studio instance was contacted or mutated.",
        ],
        {
            "transaction": rel(transaction_path),
            "transactionSha256": sha256_file(transaction_path),
            "wrapperPreserved": True,
            "rollbackExact": True,
            "studioMutations": 0,
        },
    )


def _production_boundary_stage(output: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    report_path = (
        PROJECT_ROOT
        / "assets-3d/defense-barricade-small/qa/final-report.json"
    )
    report = load_json(report_path)
    status = report.get("status", report.get("implementationStatus", "UNKNOWN"))
    implementation = report.get("implementationStatus", "UNKNOWN")
    if report.get("productionApproved") is not False:
        raise ArtSystemError("Simulation must not run against an approved production report")
    if status == "PASS" or implementation == "PASS":
        raise ArtSystemError(
            "Simulation may not be used to preserve or create a production PASS"
        )
    real_status = {
        "status": status,
        "implementationStatus": implementation,
        "productionApproved": False,
        "reportPath": "assets-3d/defense-barricade-small/qa/final-report.json",
        "sha256": sha256_file(report_path),
    }
    stage = _write_stage(
        output,
        "production_boundary",
        "REAL_LOCAL",
        [
            "The authoritative asset report remains non-PASS.",
            "The authoritative implementation status remains non-PASS.",
            "The authoritative productionApproved flag remains false.",
            "No synthetic artifact is referenced by the authoritative report.",
        ],
        real_status,
    )
    return stage, real_status


def run_simulation(output: Path) -> Path:
    output = assert_simulation_output(output)
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)
    before_digest = protected_surface_digest()

    envelope_path = output / "SIMULATION_ONLY.json"
    write_json(
        envelope_path,
        {
            "schemaVersion": "1.0.0",
            "mode": "SIMULATION_ONLY",
            "authority": "NON_PRODUCTION",
            "humanAuthoritySimulated": True,
            "externalSystemsMutated": False,
            "productionApproved": False,
            "warning": (
                "Synthetic evidence exercises contracts only and must never be "
                "copied into authoritative evidence roots."
            ),
        },
    )

    stages: list[dict[str, Any]] = []
    stages.append(_validate_static_contracts(output))
    stages.append(_simulate_precanonical_campaign(output))
    stages.append(_validate_blender_full_build(output))
    stages.append(_validate_sixth_asset_transfer(output))
    stages.append(_validate_studio_reports(output))

    synthetic_evidence_root = output / "synthetic-evidence-root"
    simulator_stage, _simulator_report = _simulate_studio_simulator(
        output,
        synthetic_evidence_root,
    )
    mobile_stage, mobile_report = _simulate_physical_mobile(
        output,
        synthetic_evidence_root,
    )
    stages.append(simulator_stage)
    stages.append(mobile_stage)

    study_evidence_root = _prepare_study_evidence_root(
        output,
        mobile_report,
    )
    study_stage, selection_path = _simulate_blind_study(
        output,
        study_evidence_root,
    )
    stages.append(study_stage)
    stages.append(_simulate_visual_canon_locks(output, selection_path))
    stages.append(_simulate_cloud_publication(output))
    stages.append(_simulate_studio_transaction(output))
    production_stage, real_status = _production_boundary_stage(output)
    stages.append(production_stage)

    stages.sort(key=lambda item: item["order"])
    if [stage["id"] for stage in stages] != list(STAGE_ORDER):
        raise ArtSystemError("Simulation stage set/order is not exact")
    if any(stage["status"] != "PASS" for stage in stages):
        raise ArtSystemError("One or more simulation stages failed")

    after_digest = protected_surface_digest()
    if after_digest != before_digest:
        raise ArtSystemError("A protected authoritative surface changed")

    artifact_bindings = [
        {
            "stageId": stage["id"],
            "path": stage["artifact"]["path"],
            "sha256": stage["artifact"]["sha256"],
        }
        for stage in stages
    ]
    report = {
        "$schema": "https://roblox-top1.local/schemas/workflow-simulation-report.schema.json",
        "schemaVersion": "1.0.0",
        "simulationId": "complete-workflow-current",
        "generatedAt": _utc_now(),
        "mode": "SIMULATION_ONLY",
        "selectedTerritory": SELECTED_TERRITORY,
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
            "outputRoot": rel(output),
            "protectedSurfaceDigestBefore": before_digest,
            "protectedSurfaceDigestAfter": after_digest,
            "protectedSurfacesUnchanged": True,
            "networkCalls": 0,
            "studioMutations": 0,
            "cloudMutations": 0,
            "secretsRead": False,
            "productionValidatorRejectedSyntheticMobile": True,
            "productionValidatorRejectedSyntheticSimulator": True,
        },
        "realProductionStatus": real_status,
        "evidencePackageSha256": sha256_bytes(
            canonical_json_bytes(artifact_bindings)
        ),
        "limitations": [
            "Synthetic participant and expert sessions are contract doubles, not human authority.",
            (
                "Synthetic mobile metrics are threshold tests, not measurements "
                "from a physical device."
            ),
            "Synthetic cloud receipts do not prove Roblox publication or asset moderation.",
            (
                "Synthetic Studio transactions do not prove an active DataModel "
                "integration or playtest."
            ),
            (
                "A simulation PASS never changes the authoritative production "
                "status or approval."
            ),
        ],
        "issues": [],
    }
    report_issues = validate_with_schema(
        report,
        ROOT / "schemas/workflow-simulation-report.schema.json",
    )
    if report_issues:
        raise ArtSystemError(
            f"Generated workflow simulation report invalid: {report_issues}"
        )
    report_path = output / "workflow-simulation-report.json"
    write_json(report_path, report)
    (output / "workflow-simulation-report.sha256").write_text(
        sha256_file(report_path) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return report_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Exercise the complete Roblox 3D workflow with isolated synthetic "
            "human/external doubles. Never produces production approval."
        )
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    try:
        report_path = run_simulation(args.output)
    except Exception as error:
        print(f"[FAIL] Complete workflow simulation failed: {error}")
        return 1
    report = load_json(report_path)
    print(
        "[PASS] Complete workflow simulation passed "
        f"{len(report['stages'])}/{len(STAGE_ORDER)} stages: {report_path}"
    )
    print(
        "[BLOCKED] Real production remains "
        f"{report['realProductionStatus']['status']}; "
        "productionApproved=false."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
