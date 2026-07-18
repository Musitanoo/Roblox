from __future__ import annotations

import argparse
import copy
import html
import itertools
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

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
from tools.art.measure_visual_quality import (
    compare_masks,
    mask_metrics,
    silhouette_mask,
)
from tools.art.validate_transfer_build_report import validate_report as validate_build

ASSET_ID = "turret_fast_v1"
TERRITORIES = (
    "industrial-toy-defense",
    "salvaged-frontier",
    "clean-tactical-diorama",
)
STATES = ("intact", "damaged", "critical")
SCHEMA = "https://roblox-top1.local/schemas/transfer-report.schema.json"
EXPECTED_BLENDER_VERSION = "5.2.0 LTS"
BLENDER_TIMEOUT_SECONDS = 1200
EVIDENCE_ROOT = ROOT / "evidence/transfer/turret-fast-v1"

MINIMUM_MASK_AREA_RATIO = 0.01
MAXIMUM_FRAME_CONTACT_PIXELS = 0
MINIMUM_DAMAGED_DIFFERENCE = 0.012
MINIMUM_CRITICAL_DIFFERENCE = 0.045
MINIMUM_CRITICAL_LEAD = 0.008
MINIMUM_CROSS_TERRITORY_DIFFERENCE = 0.04
MINIMUM_FRONT_BACK_DIFFERENCE = 0.025
MINIMUM_FAR_BBOX_HEIGHT_RATIO = 0.035
MINIMUM_PORTRAIT_BBOX_HEIGHT_RATIO = 0.18

INPUT_PATHS = {
    "contract": "art/transfer/turret-fast-v1.json",
    "humanReview": "art/transfer/turret-fast-v1-review.json",
    "generator": "tools/blender/build_transfer_asset.py",
    "proofBuilder": "tools/art/build_transfer_proof.py",
    "transferBuildValidator": "tools/art/validate_transfer_build_report.py",
    "metricLibrary": "tools/art/measure_visual_quality.py",
    "baseCompiler": "tools/blender/build_art_direction.py",
    "shapeLanguage": "art/shape-language/rules.json",
    "semanticPalette": "art/palettes/semantic-palette.json",
    "materials": "art/materials/material-rules.json",
    "camera": "art/calibration/camera-rig.json",
    "lighting": "art/lighting/lighting-profiles.json",
    "industrial-toy-defense": "art/territories/industrial-toy-defense.json",
    "salvaged-frontier": "art/territories/salvaged-frontier.json",
    "clean-tactical-diorama": "art/territories/clean-tactical-diorama.json",
}


def _run_blender(
    blender: Path,
    output: Path,
    territory: str,
    render_mode: str,
    log_path: Path,
) -> subprocess.CompletedProcess[str]:
    command = [
        str(blender),
        "--background",
        "--factory-startup",
        "--threads",
        "1",
        "--python-exit-code",
        "19",
        "--python",
        str(ROOT / "tools/blender/build_transfer_asset.py"),
        "--",
        "--root",
        str(ROOT),
        "--territory",
        territory,
        "--render-mode",
        render_mode,
        "--output",
        str(output),
    ]
    try:
        completed = subprocess.run(
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
        completed = subprocess.CompletedProcess(
            command,
            124,
            stdout,
            stderr + f"\nBlender timed out after {BLENDER_TIMEOUT_SECONDS} seconds.",
        )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "\n".join(
            (
                "COMMAND:",
                subprocess.list2cmdline(command),
                "",
                "STDOUT:",
                completed.stdout,
                "",
                "STDERR:",
                completed.stderr,
                "",
                f"EXIT_CODE: {completed.returncode}",
            )
        ),
        encoding="utf-8",
        newline="\n",
    )
    return completed


def _canonical_build_report(report: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(report)
    value.pop("generatedAt", None)
    value.pop("blendFile", None)
    return value


def _export_map(report: dict[str, Any]) -> dict[str, str]:
    return {item["stateId"]: item["sha256"] for item in report["exports"]}


def _render_lookup(
    report: dict[str, Any],
    *,
    state: str,
    case_id: str,
    profile: str | None = None,
) -> dict[str, Any]:
    candidates = [
        item
        for item in report["renderEvidence"]
        if item["stateId"] == state
        and item["caseId"] == case_id
        and (profile is None or item["lightingProfileId"] == profile)
    ]
    if len(candidates) != 1:
        raise RuntimeError(
            f"{report['territoryId']}/{state}/{case_id}/{profile}: "
            f"expected one render, got {len(candidates)}"
        )
    return candidates[0]


def _copy_artifact(
    source: Path,
    destination: Path,
    *,
    kind: str,
    state: str,
) -> dict[str, Any]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
    return {
        "kind": kind,
        "stateId": state,
        "path": destination.relative_to(ROOT).as_posix(),
        "bytes": destination.stat().st_size,
        "sha256": sha256_file(destination),
    }


def _portable_artifacts(
    territory: str,
    build_dir: Path,
    build_report: dict[str, Any],
) -> list[dict[str, Any]]:
    destination_root = EVIDENCE_ROOT / territory
    if destination_root.exists():
        shutil.rmtree(destination_root)
    artifacts: list[dict[str, Any]] = []
    export_by_state = {item["stateId"]: item for item in build_report["exports"]}
    for state in STATES:
        export = export_by_state[state]
        artifacts.append(
            _copy_artifact(
                build_dir / export["path"],
                destination_root / "exports" / f"{state}.glb",
                kind="GLB",
                state=state,
            )
        )
        cases = (
            ("hero", None, "hero", "HERO"),
            (
                "state_silhouette",
                None,
                "state-silhouette",
                "STATE_SILHOUETTE",
            ),
            (
                "far_mobile",
                "Lighting_Gameplay_Default",
                "far-mobile",
                "FAR_MOBILE",
            ),
            (
                "portrait_mobile",
                "Lighting_Adverse_Night",
                "portrait-mobile",
                "PORTRAIT_MOBILE",
            ),
        )
        for case_id, profile, folder, kind in cases:
            render = _render_lookup(
                build_report,
                state=state,
                case_id=case_id,
                profile=profile,
            )
            artifacts.append(
                _copy_artifact(
                    build_dir / render["path"],
                    destination_root / folder / f"{state}.png",
                    kind=kind,
                    state=state,
                )
            )
    for case_id, folder, kind in (
        ("front_silhouette", "orientation", "FRONT_SILHOUETTE"),
        ("back_silhouette", "orientation", "BACK_SILHOUETTE"),
    ):
        render = _render_lookup(
            build_report,
            state="intact",
            case_id=case_id,
        )
        artifacts.append(
            _copy_artifact(
                build_dir / render["path"],
                destination_root / folder / f"{case_id}.png",
                kind=kind,
                state="intact",
            )
        )
    if len(artifacts) != 17:
        raise RuntimeError(f"{territory}: portable artifact count {len(artifacts)} != 17")
    return sorted(
        artifacts,
        key=lambda item: (item["kind"], item["stateId"], item["path"]),
    )


def _foreground_mask(path: Path) -> np.ndarray:
    rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.int16)
    border = np.concatenate(
        (
            rgb[0, :, :],
            rgb[-1, :, :],
            rgb[1:-1, 0, :],
            rgb[1:-1, -1, :],
        ),
        axis=0,
    )
    background = np.median(border, axis=0)
    distance = np.sqrt(np.sum((rgb - background) ** 2, axis=2))
    mask = distance >= 12.0
    return mask


def _mobile_metrics(
    artifact: dict[str, Any],
    minimum_height: float,
) -> dict[str, Any]:
    mask = _foreground_mask(ROOT / artifact["path"])
    metrics = mask_metrics(mask)
    passed = (
        metrics["maskAreaRatio"] >= 0.0005
        and metrics["bboxHeightRatio"] >= minimum_height
        and metrics["frameContactPixels"] <= MAXIMUM_FRAME_CONTACT_PIXELS
    )
    return {
        "kind": artifact["kind"],
        "stateId": artifact["stateId"],
        "path": artifact["path"],
        "foregroundAreaRatio": metrics["maskAreaRatio"],
        "foregroundBboxHeightRatio": metrics["bboxHeightRatio"],
        "frameContactPixels": metrics["frameContactPixels"],
        "pass": passed,
    }


def _comparison(
    from_state: str,
    to_state: str,
    first: np.ndarray,
    second: np.ndarray,
    minimum: float,
) -> dict[str, Any]:
    iou, difference = compare_masks(first, second)
    return {
        "fromState": from_state,
        "toState": to_state,
        "intersectionOverUnion": iou,
        "differenceRatio": difference,
        "minimumDifference": minimum,
        "pass": difference >= minimum,
    }


def _contact_sheet(
    kind: str,
    output: Path,
    *,
    folder: str,
) -> None:
    tile_width, tile_height, label_height = 320, 240, 30
    image = Image.new(
        "RGB",
        (tile_width * len(TERRITORIES), (tile_height + label_height) * len(STATES)),
        "#111820",
    )
    draw = ImageDraw.Draw(image)
    for column, territory in enumerate(TERRITORIES):
        for row, state in enumerate(STATES):
            source = EVIDENCE_ROOT / territory / folder / f"{state}.png"
            frame = Image.open(source).convert("RGB")
            frame.thumbnail(
                (tile_width, tile_height),
                Image.Resampling.LANCZOS,
            )
            x = column * tile_width + (tile_width - frame.width) // 2
            y = row * (tile_height + label_height)
            image.paste(frame, (x, y))
            draw.rectangle(
                (
                    column * tile_width,
                    y + tile_height,
                    (column + 1) * tile_width,
                    y + tile_height + label_height,
                ),
                fill="#18232d",
            )
            draw.text(
                (column * tile_width + 8, y + tile_height + 8),
                f"{territory} / {state}",
                fill="#f0f4f7",
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output, "PNG", optimize=True)


def _review_gallery() -> list[dict[str, Any]]:
    review_root = EVIDENCE_ROOT / "review"
    if review_root.exists():
        shutil.rmtree(review_root)
    review_root.mkdir(parents=True)
    hero_sheet = review_root / "hero-contact-sheet.png"
    silhouette_sheet = review_root / "silhouette-contact-sheet.png"
    _contact_sheet("hero", hero_sheet, folder="hero")
    _contact_sheet(
        "silhouette",
        silhouette_sheet,
        folder="state-silhouette",
    )
    sections: list[str] = []
    for territory in TERRITORIES:
        cards: list[str] = []
        for state in STATES:
            images = (
                ("Hero", f"../{territory}/hero/{state}.png"),
                (
                    "Silhouette",
                    f"../{territory}/state-silhouette/{state}.png",
                ),
                ("Far mobile", f"../{territory}/far-mobile/{state}.png"),
                (
                    "Portrait adverse",
                    f"../{territory}/portrait-mobile/{state}.png",
                ),
            )
            frames = "".join(
                f'<figure><img src="{html.escape(path)}" alt="{html.escape(label)}">'
                f"<figcaption>{html.escape(label)}</figcaption></figure>"
                for label, path in images
            )
            cards.append(
                f'<article><h3>{html.escape(state)}</h3><div class="frames">{frames}</div></article>'
            )
        orientation = (
            f'<div class="orientation"><figure><img src="../{territory}/orientation/front_silhouette.png" '
            f'alt="front"><figcaption>Front</figcaption></figure>'
            f'<figure><img src="../{territory}/orientation/back_silhouette.png" '
            f'alt="back"><figcaption>Back</figcaption></figure></div>'
        )
        sections.append(
            f"<section><h2>{html.escape(territory)}</h2>{orientation}{''.join(cards)}</section>"
        )
    gallery = review_root / "index.html"
    gallery.write_text(
        """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>turret_fast_v1 transfer review</title>
<style>
:root{color-scheme:dark;font-family:Inter,system-ui,sans-serif;background:#0b1117;color:#edf3f7}
body{margin:0 auto;max-width:1500px;padding:28px}h1{margin:0 0 8px}p{color:#aebac4}
.sheets,.orientation,.frames{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px}
section{margin:44px 0;padding-top:24px;border-top:1px solid #273440}article{margin:24px 0}
figure{margin:0;background:#111b24;border:1px solid #293744;border-radius:10px;overflow:hidden}
img{display:block;width:100%;height:auto;background:#17212a}figcaption{padding:9px 12px;color:#bfcbd4}
.sheets figure{grid-column:span 1}.orientation{max-width:900px}
</style></head><body>
<h1>turret_fast_v1 — independent transfer proof</h1>
<p>Same frozen semantic, shape, material, camera, lighting, and damage contracts. Blender is preflight; human art authority remains explicit.</p>
<div class="sheets">
<figure><img src="hero-contact-sheet.png" alt="hero contact sheet"><figcaption>Hero comparison</figcaption></figure>
<figure><img src="silhouette-contact-sheet.png" alt="silhouette contact sheet"><figcaption>State silhouette comparison</figcaption></figure>
</div>
"""
        + "".join(sections)
        + "</body></html>\n",
        encoding="utf-8",
        newline="\n",
    )
    return [
        {
            "kind": "HTML_GALLERY",
            "path": gallery.relative_to(ROOT).as_posix(),
            "bytes": gallery.stat().st_size,
            "sha256": sha256_file(gallery),
        },
        {
            "kind": "HERO_CONTACT_SHEET",
            "path": hero_sheet.relative_to(ROOT).as_posix(),
            "bytes": hero_sheet.stat().st_size,
            "sha256": sha256_file(hero_sheet),
        },
        {
            "kind": "SILHOUETTE_CONTACT_SHEET",
            "path": silhouette_sheet.relative_to(ROOT).as_posix(),
            "bytes": silhouette_sheet.stat().st_size,
            "sha256": sha256_file(silhouette_sheet),
        },
    ]


def _evidence_digest(
    input_hashes: dict[str, str],
    territory_results: list[dict[str, Any]],
    review_artifacts: list[dict[str, Any]],
) -> str:
    portable = sorted(
        (
            {
                "territoryId": territory["territoryId"],
                "path": item["path"],
                "bytes": item["bytes"],
                "sha256": item["sha256"],
            }
            for territory in territory_results
            for item in territory["portableArtifacts"]
        ),
        key=lambda item: item["path"],
    )
    stable_inputs = {
        key: value for key, value in input_hashes.items() if key != "humanReview"
    }
    return sha256_bytes(
        canonical_json_bytes(
            {
                "assetId": ASSET_ID,
                "inputHashes": stable_inputs,
                "portableArtifacts": portable,
                "reviewArtifacts": sorted(
                    review_artifacts,
                    key=lambda item: item["path"],
                ),
            }
        )
    )


def build_proof(blender: Path) -> dict[str, Any]:
    contract = load_json(ROOT / "art/transfer/turret-fast-v1.json")
    contract_issues = validate_with_schema(
        contract, ROOT / "schemas/transfer-asset.schema.json"
    )
    if contract_issues:
        raise RuntimeError(
            "transfer contract is invalid:\n" + "\n".join(contract_issues)
        )
    input_hashes = {
        name: sha256_file(ROOT / relative)
        for name, relative in INPUT_PATHS.items()
    }
    global_issues: list[str] = []
    territory_results: list[dict[str, Any]] = []
    state_masks: dict[tuple[str, str], np.ndarray] = {}
    logs = ROOT / "build/logs/transfer"
    build_root = ROOT / "build/transfer" / ASSET_ID

    with tempfile.TemporaryDirectory(prefix="roblox-transfer-proof-") as raw_temp:
        temp = Path(raw_temp)
        for territory in TERRITORIES:
            local_issues: list[str] = []
            run_exit_codes: list[int] = []
            deterministic_reports: list[dict[str, Any]] = []
            for run_id in ("a", "b"):
                output = temp / run_id / territory
                completed = _run_blender(
                    blender,
                    output,
                    territory,
                    "build-only",
                    logs / f"{territory}__determinism_{run_id}.log",
                )
                run_exit_codes.append(completed.returncode)
                report_path = output / "transfer-build-report.json"
                if completed.returncode != 0:
                    local_issues.append(
                        f"determinism run {run_id} exited {completed.returncode}; "
                        f"see build/logs/transfer/{territory}__determinism_{run_id}.log"
                    )
                    continue
                if not report_path.is_file():
                    local_issues.append(
                        f"determinism run {run_id} produced no report"
                    )
                    continue
                validation = validate_build(report_path)
                local_issues.extend(
                    f"determinism run {run_id}: {issue}" for issue in validation
                )
                deterministic_reports.append(load_json(report_path))

            canonical_sha = "0" * 64
            export_sha: dict[str, str] = {
                state: "0" * 64 for state in STATES
            }
            determinism_status = "FAIL"
            if len(deterministic_reports) == 2 and not local_issues:
                observed_versions = {
                    report["toolchain"]["blenderVersion"]
                    for report in deterministic_reports
                }
                if observed_versions != {EXPECTED_BLENDER_VERSION}:
                    local_issues.append(
                        f"Blender versions {sorted(observed_versions)} "
                        f"do not match pinned {EXPECTED_BLENDER_VERSION}"
                    )
                canonical_a = canonical_json_bytes(
                    _canonical_build_report(deterministic_reports[0])
                )
                canonical_b = canonical_json_bytes(
                    _canonical_build_report(deterministic_reports[1])
                )
                exports_a = _export_map(deterministic_reports[0])
                exports_b = _export_map(deterministic_reports[1])
                if canonical_a != canonical_b:
                    local_issues.append(
                        "canonical transfer build reports differ between A and B"
                    )
                if exports_a != exports_b:
                    local_issues.append(
                        "canonical GLB hashes differ between A and B"
                    )
                canonical_sha = sha256_bytes(canonical_a)
                export_sha = exports_a
                if not local_issues:
                    determinism_status = "PASS"

            full_output = build_root / territory
            completed = _run_blender(
                blender,
                full_output,
                territory,
                "full",
                logs / f"{territory}__full.log",
            )
            full_report_path = full_output / "transfer-build-report.json"
            if completed.returncode != 0:
                local_issues.append(
                    f"full build exited {completed.returncode}; "
                    f"see build/logs/transfer/{territory}__full.log"
                )
                raise RuntimeError("\n".join(local_issues))
            validation = validate_build(full_report_path, require_full=True)
            if validation:
                raise RuntimeError(
                    f"{territory} full build invalid:\n" + "\n".join(validation)
                )
            full_report = load_json(full_report_path)
            portable = _portable_artifacts(
                territory,
                full_output,
                full_report,
            )

            silhouette_cases: list[dict[str, Any]] = []
            for state in STATES:
                artifact = next(
                    item
                    for item in portable
                    if item["kind"] == "STATE_SILHOUETTE"
                    and item["stateId"] == state
                )
                mask = silhouette_mask(ROOT / artifact["path"])
                state_masks[(territory, state)] = mask
                metrics = mask_metrics(mask)
                passed = (
                    metrics["maskAreaRatio"] >= MINIMUM_MASK_AREA_RATIO
                    and metrics["frameContactPixels"]
                    <= MAXIMUM_FRAME_CONTACT_PIXELS
                )
                silhouette_cases.append(
                    {
                        "stateId": state,
                        "path": artifact["path"],
                        "sha256": artifact["sha256"],
                        **metrics,
                        "pass": passed,
                    }
                )
                if not passed:
                    local_issues.append(
                        f"{state}: state silhouette is empty, too small, or clipped"
                    )

            intact = state_masks[(territory, "intact")]
            damaged = state_masks[(territory, "damaged")]
            critical = state_masks[(territory, "critical")]
            state_comparisons = [
                _comparison(
                    "intact",
                    "damaged",
                    intact,
                    damaged,
                    MINIMUM_DAMAGED_DIFFERENCE,
                ),
                _comparison(
                    "intact",
                    "critical",
                    intact,
                    critical,
                    MINIMUM_CRITICAL_DIFFERENCE,
                ),
            ]
            local_issues.extend(
                f"{item['fromState']}->{item['toState']} silhouette difference "
                f"{item['differenceRatio']:.4f} < {item['minimumDifference']:.4f}"
                for item in state_comparisons
                if not item["pass"]
            )
            damaged_difference = state_comparisons[0]["differenceRatio"]
            critical_difference = state_comparisons[1]["differenceRatio"]
            severity = {
                "damagedDifferenceRatio": damaged_difference,
                "criticalDifferenceRatio": critical_difference,
                "minimumCriticalLead": MINIMUM_CRITICAL_LEAD,
                "pass": critical_difference
                >= damaged_difference + MINIMUM_CRITICAL_LEAD,
            }
            if not severity["pass"]:
                local_issues.append(
                    "critical silhouette is not sufficiently more severe than damaged"
                )

            front = next(
                item for item in portable if item["kind"] == "FRONT_SILHOUETTE"
            )
            back = next(
                item for item in portable if item["kind"] == "BACK_SILHOUETTE"
            )
            orientation = _comparison(
                "intact",
                "intact",
                silhouette_mask(ROOT / front["path"]),
                silhouette_mask(ROOT / back["path"]),
                MINIMUM_FRONT_BACK_DIFFERENCE,
            )
            if not orientation["pass"]:
                local_issues.append(
                    f"front/back silhouette difference "
                    f"{orientation['differenceRatio']:.4f} "
                    f"< {MINIMUM_FRONT_BACK_DIFFERENCE:.4f}"
                )

            mobile: list[dict[str, Any]] = []
            for artifact in portable:
                if artifact["kind"] == "FAR_MOBILE":
                    mobile.append(
                        _mobile_metrics(
                            artifact,
                            MINIMUM_FAR_BBOX_HEIGHT_RATIO,
                        )
                    )
                elif artifact["kind"] == "PORTRAIT_MOBILE":
                    mobile.append(
                        _mobile_metrics(
                            artifact,
                            MINIMUM_PORTRAIT_BBOX_HEIGHT_RATIO,
                        )
                    )
            local_issues.extend(
                f"{item['kind']}/{item['stateId']}: framing or clipping gate failed"
                for item in mobile
                if not item["pass"]
            )

            result = {
                "territoryId": territory,
                "status": "PASS" if not local_issues else "FAIL",
                "fullBuildReportSha256": sha256_file(full_report_path),
                "geometry": {
                    "variantCount": len(full_report["variants"]),
                    "maximumTriangles": max(
                        item["triangles"] for item in full_report["variants"]
                    ),
                    "triangleBudget": contract["triangleBudgetMax"],
                    "exportCount": len(full_report["exports"]),
                    "fullRenderCount": len(full_report["renderEvidence"]),
                },
                "grammarAuditStatus": full_report["grammarAudit"]["status"],
                "determinism": {
                    "status": determinism_status,
                    "runExitCodes": run_exit_codes,
                    "canonicalReportSha256": canonical_sha,
                    "exportSha256": export_sha,
                },
                "portableArtifacts": portable,
                "silhouetteCases": sorted(
                    silhouette_cases,
                    key=lambda item: item["stateId"],
                ),
                "stateComparisons": state_comparisons,
                "severityOrdering": severity,
                "orientationComparison": orientation,
                "mobileFraming": sorted(
                    mobile,
                    key=lambda item: (item["kind"], item["stateId"]),
                ),
                "issues": local_issues,
            }
            territory_results.append(result)
            global_issues.extend(
                f"{territory}: {issue}" for issue in local_issues
            )

    cross_territory: list[dict[str, Any]] = []
    for territory_a, territory_b in itertools.combinations(TERRITORIES, 2):
        comparison = _comparison(
            "intact",
            "intact",
            state_masks[(territory_a, "intact")],
            state_masks[(territory_b, "intact")],
            MINIMUM_CROSS_TERRITORY_DIFFERENCE,
        )
        comparison["territoryA"] = territory_a
        comparison["territoryB"] = territory_b
        cross_territory.append(comparison)
        if not comparison["pass"]:
            global_issues.append(
                f"{territory_a} vs {territory_b}: silhouette difference "
                f"{comparison['differenceRatio']:.4f} "
                f"< {MINIMUM_CROSS_TERRITORY_DIFFERENCE:.4f}"
            )

    review_artifacts = _review_gallery()
    evidence_sha = _evidence_digest(
        input_hashes,
        territory_results,
        review_artifacts,
    )
    review = load_json(ROOT / "art/transfer/turret-fast-v1-review.json")
    review_issues = validate_with_schema(
        review,
        ROOT / "schemas/transfer-review.schema.json",
    )
    if review_issues:
        global_issues.extend(
            f"human review schema: {issue}" for issue in review_issues
        )
    if review["status"] == "APPROVED":
        observed_total = sum(review["scores"].values())
        if review["scoreTotal"] != observed_total:
            global_issues.append(
                "approved human review scoreTotal does not equal its five scores"
            )
        if observed_total < 90:
            global_issues.append(
                "approved human review total score is below 90/100"
            )
        if review["evidencePackageSha256"] != evidence_sha:
            global_issues.append(
                "approved human review is bound to a different evidence package"
            )

    geometry_pass = all(
        territory["geometry"]["maximumTriangles"]
        <= territory["geometry"]["triangleBudget"]
        and territory["status"] == "PASS"
        for territory in territory_results
    )
    grammar_pass = all(
        territory["grammarAuditStatus"] == "PASS"
        for territory in territory_results
    )
    determinism_pass = all(
        territory["determinism"]["status"] == "PASS"
        for territory in territory_results
    )
    state_pass = all(
        item["pass"]
        for territory in territory_results
        for item in territory["stateComparisons"]
    ) and all(
        territory["severityOrdering"]["pass"]
        and territory["orientationComparison"]["pass"]
        for territory in territory_results
    )
    cross_pass = all(item["pass"] for item in cross_territory)
    mobile_pass = all(
        item["pass"]
        for territory in territory_results
        for item in territory["mobileFraming"]
    )
    automated_score = (
        (25 if geometry_pass else 0)
        + (20 if grammar_pass else 0)
        + (20 if determinism_pass else 0)
        + (20 if state_pass else 0)
        + (10 if cross_pass else 0)
        + (5 if mobile_pass else 0)
    )
    automated_status = (
        "PASS" if automated_score >= 90 and not global_issues else "FAIL"
    )
    blocking: list[str] = []
    if automated_status == "PASS" and review["status"] == "PENDING":
        blocking.append(
            "Human art authority has not approved turret_fast_v1 against the current selected territory and this exact evidence package."
        )
    if automated_status == "PASS" and review["selectedTerritory"] is None:
        blocking.append(
            "No human-selected territory is recorded in the transfer review; the automated proof remains cross-territory preflight."
        )
    if automated_status == "FAIL":
        overall = "FAIL"
    elif (
        review["status"] == "APPROVED"
        and review["evidencePackageSha256"] == evidence_sha
    ):
        overall = "PASS"
    else:
        overall = "PARTIAL"

    report: dict[str, Any] = {
        "$schema": SCHEMA,
        "schemaVersion": "1.0.0",
        "assetId": ASSET_ID,
        "generatedAt": datetime.now(timezone.utc).isoformat().replace(
            "+00:00", "Z"
        ),
        "rendererTruth": "BLENDER_TRANSFER_PREFLIGHT_HUMAN_AND_STUDIO_AUTHORITIES_REMAIN_SEPARATE",
        "automatedStatus": automated_status,
        "automatedScore": automated_score,
        "overallStatus": overall,
        "inputHashes": input_hashes,
        "thresholds": {
            "minimumMaskAreaRatio": MINIMUM_MASK_AREA_RATIO,
            "maximumFrameContactPixels": MAXIMUM_FRAME_CONTACT_PIXELS,
            "minimumDamagedDifference": MINIMUM_DAMAGED_DIFFERENCE,
            "minimumCriticalDifference": MINIMUM_CRITICAL_DIFFERENCE,
            "minimumCriticalLead": MINIMUM_CRITICAL_LEAD,
            "minimumCrossTerritoryDifference": MINIMUM_CROSS_TERRITORY_DIFFERENCE,
            "minimumFrontBackDifference": MINIMUM_FRONT_BACK_DIFFERENCE,
            "minimumFarBboxHeightRatio": MINIMUM_FAR_BBOX_HEIGHT_RATIO,
            "minimumPortraitBboxHeightRatio": MINIMUM_PORTRAIT_BBOX_HEIGHT_RATIO,
        },
        "territories": territory_results,
        "crossTerritoryComparisons": cross_territory,
        "evidencePackageSha256": evidence_sha,
        "reviewArtifacts": review_artifacts,
        "humanReview": {
            "status": review["status"],
            "selectedTerritory": review["selectedTerritory"],
            "reviewer": review["reviewer"],
            "reviewedAt": review["reviewedAt"],
            "evidencePackageSha256": review["evidencePackageSha256"],
            "decision": review["decision"],
            "scoreTotal": review["scoreTotal"],
        },
        "issues": global_issues,
        "blockingReasons": blocking,
    }
    schema_issues = validate_with_schema(
        report,
        ROOT / "schemas/transfer-report.schema.json",
    )
    if schema_issues:
        report["automatedStatus"] = "FAIL"
        report["overallStatus"] = "FAIL"
        report["automatedScore"] = min(report["automatedScore"], 89)
        report["issues"].extend(
            f"transfer report schema: {issue}" for issue in schema_issues
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build, render, measure, and package the independent sixth-asset transfer proof."
    )
    parser.add_argument("--blender", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=EVIDENCE_ROOT / "report.json",
    )
    parser.add_argument("--require-approved", action="store_true")
    args = parser.parse_args()
    report = build_proof(args.blender.resolve())
    write_json(args.output, report)
    for territory in report["territories"]:
        print(
            f"[{territory['status']}] {territory['territoryId']} | "
            f"max triangles={territory['geometry']['maximumTriangles']} | "
            f"renders={territory['geometry']['fullRenderCount']} | "
            f"determinism={territory['determinism']['status']}"
        )
    for issue in report["issues"]:
        print(f"[FAIL] {issue}")
    for reason in report["blockingReasons"]:
        print(f"[BLOCKED] {reason}")
    print(
        f"[{report['overallStatus']}] transfer proof | automated "
        f"{report['automatedStatus']} {report['automatedScore']}/100 | "
        f"report: {args.output}"
    )
    if report["automatedStatus"] != "PASS":
        return 1
    if args.require_approved and report["overallStatus"] != "PASS":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
