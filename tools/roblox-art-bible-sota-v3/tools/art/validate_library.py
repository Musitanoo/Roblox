from __future__ import annotations

import argparse
import json
import math
import platform
from datetime import datetime, timezone
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.art.common import (
    PROJECT_ROOT,
    ROOT,
    load_json,
    require,
    sha256_file,
    validate_with_schema,
    write_json,
)
from tools.art.generate_luau import generate
from tools.art.pixel_math import required_thickness
from tools.art.validate_transfer_report import validate_report as validate_transfer_report
from tools.art.recipe_contract import (
    EXECUTABLE_RECIPE_FIELDS,
    STATE_STRATEGY_PROFILES,
    VALIDATION_TARGET_RECIPE_FIELDS,
    declared_recipe_fields,
)
from tools.art.build_visual_canons import check_all as check_visual_canons
from tools.art.precanonical import preflight as precanonical_preflight
from tools.art.product_art_authority import validate_product_art_authority

TERRITORIES = ["industrial-toy-defense", "salvaged-frontier", "clean-tactical-diorama"]
ASSETS = ["barricade", "objective_core", "enemy_standard", "floor_module", "damage_effect"]
STATES = ["intact", "damaged", "critical"]
PROFILES = ["Lighting_Gameplay_Default", "Lighting_HighContrast", "Lighting_Adverse_Night", "Lighting_Neutral_QA"]
TASK_GATE_IDS = {"silhouette_recognition_60", "function_recognition_mobile", "state_recognition"}
TECH_GATE_IDS = {
    "not_color_only", "grayscale_and_cvd", "materials_four_lights", "group_30_visual",
    "provenance_complete", "deterministic_rules", "roblox_technical_budgets",
    "studio_golden_scene", "real_device_mobile",
}


def _sum_close(values: list[float], target: float, tolerance: float = 1e-9) -> bool:
    return math.isclose(sum(values), target, abs_tol=tolerance)


def semantic_checks() -> list[str]:
    issues: list[str] = []
    art = load_json(ROOT / "art/art-direction.json")
    constitution_path = (
        ROOT / "art/selected/salvaged-frontier-constitution.json"
    )
    constitution = load_json(constitution_path)
    founder_decision = load_json(
        ROOT / "art/decision/founder-direction-decision.json"
    )
    precanonical_policy_path = ROOT / "art/precanonical/policy.json"
    precanonical_policy = load_json(precanonical_policy_path)
    precanonical_reference_request = (
        ROOT
        / "assets-3d/defense-barricade-small/precanonical/requests"
        / "defense-barricade-web-001/request.json"
    )
    calibration = load_json(ROOT / "art/calibration/calibration-kit.json")
    camera = load_json(ROOT / "art/calibration/camera-rig.json")
    matrix = load_json(ROOT / "art/calibration/render-matrix.json")
    palette = load_json(ROOT / "art/palettes/semantic-palette.json")
    materials = load_json(ROOT / "art/materials/material-rules.json")
    shape = load_json(ROOT / "art/shape-language/rules.json")
    lighting = load_json(ROOT / "art/lighting/lighting-profiles.json")
    provenance = load_json(ROOT / "art/references/provenance.json")
    rubric = load_json(ROOT / "art/qa/visual-rubric.json")
    protocol = load_json(ROOT / "art/qa/task-protocol.json")
    transfer = load_json(ROOT / "art/transfer/turret-fast-v1.json")
    visual_canon_catalog = load_json(
        ROOT / "art/canonical-visuals/catalog.json"
    )

    require(art["territories"] == TERRITORIES, "art-direction territory order/set is not canonical", issues)
    require(art["axisContract"]["designAndRoblox"] == {"x": "width", "y": "height", "z": "depth", "upAxis": "Y"}, "Roblox axis contract differs from X=width, Y=height, Z=depth", issues)
    require(art["axisContract"]["blender"] == {"x": "width", "y": "depth", "z": "height", "upAxis": "Z"}, "Blender axis contract differs from X=width, Y=depth, Z=height", issues)

    if art["status"] == "EXPLORATION":
        require(art["productionApproved"] is False, "EXPLORATION cannot be productionApproved", issues)
        require(art["finalTerritory"] is None, "EXPLORATION cannot have finalTerritory", issues)
    if art["status"] == "CANDIDATE_SELECTED":
        require(
            art["productionApproved"] is False,
            "CANDIDATE_SELECTED cannot be productionApproved",
            issues,
        )
        require(
            art["finalTerritory"] == "salvaged-frontier",
            "founder-selected candidate must be salvaged-frontier",
            issues,
        )

    require(
        constitution["selectedTerritory"] == art["finalTerritory"],
        "creative constitution territory differs from art-direction selection",
        issues,
    )
    require(
        constitution["identityAuthority"] == "salvaged-frontier"
        and constitution["readabilityDiscipline"]
        == "industrial-toy-defense",
        "creative constitution precedence contract drifted",
        issues,
    )
    require(
        constitution["precedenceContract"]["hybridizationForbidden"] is True,
        "creative constitution must forbid a fifty-fifty visual hybrid",
        issues,
    )
    require(
        founder_decision["selectedTerritory"]
        == constitution["selectedTerritory"],
        "founder decision territory differs from creative constitution",
        issues,
    )
    require(
        founder_decision["selectedConstitutionSha256"]
        == sha256_file(constitution_path),
        "founder decision is not bound to the current creative constitution",
        issues,
    )
    require(
        founder_decision["productionApproved"] is False,
        "founder creative selection cannot claim production approval",
        issues,
    )
    require(
        precanonical_policy["selectedArtDirection"]
        == constitution["selectedTerritory"]
        == "salvaged-frontier",
        "precanonical policy differs from the founder-selected identity",
        issues,
    )
    require(
        precanonical_policy["constitution"]["sha256"]
        == sha256_file(constitution_path),
        "precanonical policy is not bound to the current creative constitution",
        issues,
    )
    require(
        precanonical_policy["providerContract"]["replaceableSurface"] is True
        and precanonical_policy["providerContract"]["browserIsTransportOnly"]
        is True,
        "precanonical Web surface must remain replaceable transport only",
        issues,
    )
    require(
        all(
            value is False
            for value in precanonical_policy["fallbackPolicy"].values()
        ),
        "precanonical policy must disable automatic fallbacks and retries",
        issues,
    )
    require(
        sum(
            precanonical_policy["defaultBudget"][key]
            for key in (
                "exploration",
                "consolidation",
                "precanonicalBoard",
                "correctionReserve",
            )
        )
        == precanonical_policy["defaultBudget"]["maximumTotal"],
        "precanonical stage budgets must close exactly to maximumTotal",
        issues,
    )
    require(
        precanonical_policy["authorityBoundary"]["productionApproved"] is False
        and precanonical_policy["authorityBoundary"][
            "imageMayBecomeCanonicalDirectly"
        ]
        is False
        and precanonical_policy["authorityBoundary"]["imageProvesHiddenGeometry"]
        is False,
        "precanonical images cannot claim canon, geometry or production authority",
        issues,
    )
    reference_preflight = precanonical_preflight(
        precanonical_reference_request
    )
    require(
        reference_preflight["status"] == "PASS"
        and reference_preflight["consumesQuota"] is False,
        "reference precanonical request does not pass a zero-consumption preflight: "
        + "; ".join(reference_preflight["blockingReasons"]),
        issues,
    )
    for authority_id, authority in constitution["sourceAuthorities"].items():
        authority_path = (
            PROJECT_ROOT / authority["path"]
            if authority_id == "retention"
            else ROOT / authority["path"]
        )
        require(
            authority_path.is_file(),
            f"creative constitution authority is missing: {authority_id}",
            issues,
        )
        if authority_path.is_file():
            require(
                sha256_file(authority_path) == authority["sha256"],
                f"creative constitution authority hash drift: {authority_id}",
                issues,
            )
    issues.extend(
        "product art authority: " + issue
        for issue in validate_product_art_authority()
    )

    visual_canon_issues = check_visual_canons(require_locked=False)
    issues.extend(
        f"visual canon: {issue}" for issue in visual_canon_issues
    )
    for lock_path in sorted(
        (ROOT / "art/canonical-visuals/locks").glob("*/*.json")
    ):
        lock_errors = validate_with_schema(
            load_json(lock_path),
            ROOT / "schemas/visual-canon-lock.schema.json",
        )
        issues.extend(
            f"{lock_path.relative_to(ROOT).as_posix()}{error}"
            for error in lock_errors
        )
    coverage = visual_canon_catalog["coverage"]
    require(
        coverage["canonCount"] == len(TERRITORIES) * 6,
        "visual canon catalog must cover 18 object x territory pairs",
        issues,
    )
    require(
        coverage["stateDefinitionCount"] == 48,
        "visual canon catalog must cover exactly 48 required states",
        issues,
    )
    canon_pairs = {
        (entry["territoryId"], entry["assetId"])
        for entry in visual_canon_catalog["entries"]
    }
    require(
        len(canon_pairs) == 18,
        "visual canon catalog contains duplicate or missing object x territory pairs",
        issues,
    )
    for entry in visual_canon_catalog["entries"]:
        canon_path = ROOT / entry["path"]
        require(
            canon_path.is_file(),
            f"visual canon file missing: {entry['path']}",
            issues,
        )
        if not canon_path.is_file():
            continue
        require(
            sha256_file(canon_path) == entry["sha256"],
            f"visual canon hash drift: {entry['path']}",
            issues,
        )
        canon = load_json(canon_path)
        require(
            canon["status"] != "DRAFT",
            f"{entry['canonId']}: DRAFT canon cannot authorize generation",
            issues,
        )
        require(
            canon["status"] == entry["status"],
            f"{entry['canonId']}: catalog status differs from canon",
            issues,
        )
        require(
            sorted(state["id"] for state in canon["states"])
            == sorted(entry["stateIds"]),
            f"{entry['canonId']}: catalog state coverage differs from canon",
            issues,
        )
        require(
            all(
                all(state["cues"][cue] for cue in (
                    "shape",
                    "silhouette",
                    "value",
                    "color",
                    "light",
                    "motion",
                    "vfx",
                    "audio",
                ))
                for state in canon["states"]
            ),
            f"{entry['canonId']}: a state lacks redundant non-color cues",
            issues,
        )
        require(
            canon["generationContract"]["silentCanonMutationForbidden"] is True,
            f"{entry['canonId']}: silent canon mutation must be forbidden",
            issues,
        )
        require(
            canon["generationContract"]["minimumStatusForProduction"]
            == "LOCKED",
            f"{entry['canonId']}: production must require a LOCKED canon",
            issues,
        )
    if art["status"] == "EXPLORATION":
        require(
            visual_canon_catalog["productionGate"]["status"] == "BLOCKED",
            "EXPLORATION visual canon production gate must remain BLOCKED",
            issues,
        )
        require(
            visual_canon_catalog["productionGate"]["selectedTerritory"] is None,
            "EXPLORATION cannot select a visual canon territory",
            issues,
        )
        require(
            all(
                entry["status"] == "CANDIDATE"
                and entry["productionEligible"] is False
                for entry in visual_canon_catalog["entries"]
            ),
            "EXPLORATION canons must remain non-production CANDIDATE contracts",
            issues,
        )
    if art["status"] == "CANDIDATE_SELECTED":
        selected_entries = [
            entry
            for entry in visual_canon_catalog["entries"]
            if entry["territoryId"] == art["finalTerritory"]
        ]
        require(
            len(selected_entries) == 6,
            "selected territory must expose exactly six visual canons",
            issues,
        )
        require(
            visual_canon_catalog["productionGate"]["selectedTerritory"]
            == art["finalTerritory"],
            "visual canon catalog selection differs from art direction",
            issues,
        )
        require(
            visual_canon_catalog["productionGate"]["requiredCanonCount"] == 6
            and visual_canon_catalog["productionGate"]["status"] == "BLOCKED",
            "selected candidate must require six locked canons and remain BLOCKED",
            issues,
        )
        require(
            all(
                entry["status"] == "CANDIDATE"
                and entry["productionEligible"] is False
                for entry in selected_entries
            ),
            "selected visual canons must remain non-production CANDIDATE contracts until human board locks",
            issues,
        )

    for territory_id in TERRITORIES:
        path = ROOT / f"art/territories/{territory_id}.json"
        territory = load_json(path)
        require(territory["territoryId"] == territory_id, f"{path.name}: territoryId mismatch", issues)
        known_surfaces = set(materials["materials"])
        require(set(territory["materialBias"]).issubset(known_surfaces), f"{territory_id}: materialBias references an unknown surface", issues)
        require(set(territory["surfaceAssignments"].values()).issubset(known_surfaces), f"{territory_id}: surfaceAssignments references an unknown surface", issues)
        require(set(territory["surfaceAssignments"]) == set(territory["blockoutPalette"]), f"{territory_id}: every semantic role must have exactly one surface assignment", issues)
        require(set(territory["assetRecipes"]) == set(ASSETS), f"{territory_id}: asset recipe set must equal calibration kit", issues)
        for asset_id, recipe in territory["assetRecipes"].items():
            require(recipe["assetId"] == asset_id, f"{territory_id}/{asset_id}: embedded assetId mismatch", issues)
            require(set(recipe) == declared_recipe_fields(), f"{territory_id}/{asset_id}: unclassified recipe fields", issues)
            require(recipe["stateBreakStrategy"] in STATE_STRATEGY_PROFILES, f"{territory_id}/{asset_id}: state strategy is not implemented", issues)
            require(bool(recipe["primaryPrimitives"]), f"{territory_id}/{asset_id}: primary primitive targets are empty", issues)
            require(bool(recipe["secondaryPrimitives"]), f"{territory_id}/{asset_id}: secondary primitive targets are empty", issues)
            require(recipe["moduleCountTarget"] >= len(recipe["primaryPrimitives"]) + len(recipe["secondaryPrimitives"]), f"{territory_id}/{asset_id}: module target is smaller than declared semantic primitive groups", issues)
            ratios = recipe["detailBandTargets"]
            require(_sum_close(list(ratios.values()), 1.0), f"{territory_id}/{asset_id}: detail bands must sum exactly to 1.0", issues)

    selected_territory = load_json(
        ROOT / "art/territories/salvaged-frontier.json"
    )
    quantitative = constitution["quantitativeGrammar"]
    require(
        selected_territory["shapeLanguage"]["asymmetry"]
        == quantitative["globalAsymmetry"],
        "salvaged-frontier asymmetry differs from creative constitution",
        issues,
    )
    require(
        selected_territory["shapeLanguage"]["primarySecondarySizeRatio"]
        == quantitative["primarySecondarySizeRatio"],
        "salvaged-frontier mass hierarchy differs from creative constitution",
        issues,
    )
    require(
        selected_territory["blockoutPalette"] == {
            key: constitution["palette"][key]
            for key in (
                "primary",
                "secondary",
                "accent",
                "interaction",
                "threat",
                "warning",
                "critical",
                "rubber",
                "bareMetal",
            )
        },
        "salvaged-frontier executable palette differs from creative constitution",
        issues,
    )
    require(
        {
            asset_id: recipe["asymmetryTarget"]
            for asset_id, recipe in selected_territory["assetRecipes"].items()
        }
        == {
            asset_id: target
            for asset_id, target in quantitative[
                "assetAsymmetryTargets"
            ].items()
            if asset_id != "turret_fast_v1"
        },
        "salvaged-frontier asset asymmetry targets differ from creative constitution",
        issues,
    )
    require(
        selected_territory["repairGrammar"]["maxPatchFamiliesPerAsset"]
        == quantitative["patchFamiliesMax"],
        "salvaged-frontier patch-family cap differs from creative constitution",
        issues,
    )
    require(
        selected_territory["surfaceAssignments"]["secondary"]
        == "reclaimed_composite",
        "salvaged-frontier secondary surface must use reclaimed composite",
        issues,
    )

    transfer_roles = set(transfer["grammarClosure"]["paletteRoles"])
    require(
        transfer["assetId"] not in ASSETS,
        "sixth transfer asset must remain outside the five-asset calibration kit",
        issues,
    )
    require(
        transfer["novelty"] == "UNSEEN_DURING_FIVE_ASSET_TERRITORY_CALIBRATION",
        "sixth transfer asset novelty declaration drifted",
        issues,
    )
    require(
        set(transfer["grammarClosure"]["primaryShapes"])
        == set(shape["functionFamilies"]["defense"]["primary"]),
        "transfer primary shapes invent or omit defense grammar",
        issues,
    )
    require(
        set(transfer["grammarClosure"]["secondaryShapes"])
        == set(shape["functionFamilies"]["defense"]["secondary"]) | {"socket"},
        "transfer secondary shapes must be defense grammar plus the global interaction socket",
        issues,
    )
    require(
        set(transfer["grammarClosure"]["forbidden"])
        == set(shape["functionFamilies"]["defense"]["forbidden"]) | set(shape["forbidden"]),
        "transfer forbidden set differs from the frozen defense/global grammar",
        issues,
    )
    require(
        transfer_roles.issubset(set(materials["semanticRoleProfiles"])),
        "transfer contract references an unknown compiler semantic material role",
        issues,
    )
    require(
        "threat" not in transfer_roles,
        "player defense transfer asset must not consume the enemy threat role",
        issues,
    )
    transfer_extent = max(transfer["dimensions"].values())
    transfer_texture_class = calibration["textureClasses"][
        transfer["textureBudgetClass"]
    ]
    require(
        transfer_extent <= transfer_texture_class["maxAssetExtentStuds"],
        "transfer dimensions exceed its frozen texture budget class",
        issues,
    )
    for territory_id in TERRITORIES:
        territory = load_json(ROOT / f"art/territories/{territory_id}.json")
        binding = transfer["territoryBindings"][territory_id]
        require(
            binding["territoryRef"] == f"art/territories/{territory_id}.json",
            f"{territory_id}: transfer territory reference drifted",
            issues,
        )
        require(
            binding["allowedAnglesDegrees"]
            == territory["shapeLanguage"]["angleFamiliesDegrees"],
            f"{territory_id}: transfer angle family differs from frozen territory",
            issues,
        )
        require(
            binding["asymmetryTarget"]
            == territory["shapeLanguage"]["asymmetry"]["target"],
            f"{territory_id}: transfer asymmetry target differs from frozen territory",
            issues,
        )
        source_asset = binding["bevelSourceAsset"]
        require(
            binding["bevelRatio"]
            == territory["assetRecipes"][source_asset]["bevelRatioTarget"],
            f"{territory_id}: transfer bevel is not reused from its declared source asset",
            issues,
        )
        require(
            set(territory["surfaceAssignments"]) >= transfer_roles,
            f"{territory_id}: transfer role has no frozen surface assignment",
            issues,
        )

    require(EXECUTABLE_RECIPE_FIELDS.isdisjoint(VALIDATION_TARGET_RECIPE_FIELDS), "recipe field classifications overlap", issues)

    class_limits = calibration["textureClasses"]
    for asset_id, asset in calibration["assets"].items():
        dims = asset["dimensions"]
        require(all(float(v) > 0 for v in dims.values()), f"{asset_id}: all dimensions must be positive", issues)
        require(asset["triangleBudgetMax"] > 0, f"{asset_id}: triangle budget must be positive", issues)
        variants = asset["requiredStateVariants"]
        require(bool(variants), f"{asset_id}: at least one state variant is required", issues)
        require(len(variants) == len(set(variants)), f"{asset_id}: duplicate state variants", issues)
        require(set(variants).issubset(STATES), f"{asset_id}: unknown state variant", issues)
        extent = max(dims.values())
        cls = class_limits[asset["textureBudgetClass"]]
        require(extent <= cls["maxAssetExtentStuds"], f"{asset_id}: {extent} stud extent exceeds texture class {asset['textureBudgetClass']}", issues)

    fov = art["screenSpaceRules"]["verticalFieldOfViewDegrees"]
    viewport = art["screenSpaceRules"]["calibrationViewport"]
    for band_id, band in art["screenSpaceRules"]["bands"].items():
        nominal = required_thickness(band["minimumPixels"], band["distanceStuds"], fov, viewport["height"])
        require(math.isclose(nominal, band["nominalThicknessStuds"], abs_tol=1e-6), f"screen-space nominal mismatch for {band_id}", issues)
        require(math.isclose(nominal * band["productionSafetyFactor"], band["productionMinimumThicknessStuds"], abs_tol=1e-6), f"screen-space safety thickness mismatch for {band_id}", issues)

    detail = art["detailHierarchy"]
    require(_sum_close(list(detail["targetProjectedAreaRatio"].values()), 1.0), "art-direction detail targets must sum exactly to 1.0", issues)
    require(_sum_close(list(shape["global"]["volumeHierarchyTarget"].values()), 1.0), "shape-rule detail targets must sum exactly to 1.0", issues)

    required_resolution_ids = {entry["id"] for entry in camera["resolutions"] if entry["required"]}
    all_passes = {"beauty", "silhouette", "flat_albedo", "detail_band"}
    for mode_id, mode in matrix["modes"].items():
        job_ids = [job["jobId"] for job in mode["jobs"]]
        require(len(job_ids) == len(set(job_ids)), f"{mode_id}: render job IDs must be unique", issues)
        expected_count = 0
        for job in mode["jobs"]:
            pair_count = sum(
                state_id in calibration["assets"][asset_id]["requiredStateVariants"]
                for asset_id in job["assetIds"]
                for state_id in job["stateIds"]
            )
            require(pair_count > 0, f"{mode_id}/{job['jobId']}: render job has no applicable asset/state pair", issues)
            count = pair_count
            for axis in ("cameraIds", "lightingProfileIds", "backgroundIds", "resolutionIds", "passIds"):
                count *= len(job[axis])
            expected_count += count
        require(expected_count == mode["expectedRenderCount"], f"{mode_id}: expectedRenderCount mismatch", issues)
        require(expected_count <= 2000, f"{mode_id}: render matrix exceeds the bounded preflight cap", issues)

    full_jobs = matrix["modes"]["full"]["jobs"]
    union = lambda key, jobs=full_jobs: {value for job in jobs for value in job[key]}
    require(union("assetIds") == set(ASSETS), "full render matrix must include all assets", issues)
    require(union("lightingProfileIds") == set(PROFILES), "full render matrix must include all lighting profiles", issues)
    require(required_resolution_ids.issubset(union("resolutionIds")), "full render matrix omits a required resolution", issues)
    require(union("passIds") == all_passes, "full render matrix pass set is incomplete", issues)
    beauty_jobs = [job for job in full_jobs if "beauty" in job["passIds"]]
    beauty_union = lambda key: {value for job in beauty_jobs for value in job[key]}
    applicable_pairs = {
        (asset_id, state_id)
        for asset_id, asset in calibration["assets"].items()
        for state_id in asset["requiredStateVariants"]
    }
    beauty_pairs = {
        (asset_id, state_id)
        for job in beauty_jobs
        for asset_id in job["assetIds"]
        for state_id in job["stateIds"]
        if state_id in calibration["assets"][asset_id]["requiredStateVariants"]
    }
    require(beauty_pairs == applicable_pairs, "full beauty evidence must cover every applicable asset/state pair", issues)
    require({"near", "mid", "far"}.issubset(beauty_union("cameraIds")), "full beauty evidence must cover near/mid/far", issues)
    require(beauty_union("lightingProfileIds") == set(PROFILES), "full beauty evidence must cover all lighting profiles", issues)
    require({"world_neutral_light", "world_neutral_dark"}.issubset(beauty_union("backgroundIds")), "full beauty evidence must cover both backgrounds", issues)
    silhouette_jobs = [job for job in full_jobs if "silhouette" in job["passIds"]]
    silhouette_cameras = {value for job in silhouette_jobs for value in job["cameraIds"]}
    require({"far", "front", "back", "three_quarter"}.issubset(silhouette_cameras), "silhouette evidence must cover far/front/back/three_quarter", issues)
    silhouette_pairs = {
        (asset_id, state_id)
        for job in silhouette_jobs
        for asset_id in job["assetIds"]
        for state_id in job["stateIds"]
        if state_id in calibration["assets"][asset_id]["requiredStateVariants"]
    }
    require(silhouette_pairs == applicable_pairs, "full silhouette evidence must cover every applicable asset/state pair", issues)

    palette_roles = set(palette["roles"])
    for state_id, encoding in palette["stateEncoding"].items():
        require(encoding["primaryRole"] in palette_roles, f"state {state_id} references missing palette role", issues)
        require(bool(encoding["shapeCue"] and encoding["motionCue"] and encoding["audioCue"]), f"state {state_id} lacks redundant cues", issues)
    require(palette["accessibility"]["colorNeverSoleCarrier"] is True, "palette must forbid color-only encoding", issues)
    high_salience = ["player_buildable", "interactive_ready", "warning", "critical", "enemy_threat", "objective_anchor"]
    require(sum(palette["roles"][r]["maxVisibleAreaRatio"] for r in high_salience) <= 0.74, "high-salience semantic colors can occupy too much of a frame", issues)

    contract = materials["robloxContract"]
    require(contract["materialSlotsMaxPerMeshObject"] == 1, "Roblox material-slot max must be 1", issues)
    require(contract["uvSetsMaxPerMeshComponent"] == 1, "Roblox UV-set max must be 1", issues)
    require(contract["uvRange"] == {"min": 0.0, "max": 1.0}, "UV range must be 0-1", issues)
    require(contract["internalTextureDimensionMax"] <= 1024, "internal mobile texture cap exceeds 1024", issues)
    for material_id, material in materials["materials"].items():
        require(material["roughness"]["min"] <= material["roughness"]["max"], f"{material_id}: inverted roughness range", issues)
        require(material["metalness"]["min"] <= material["metalness"]["max"], f"{material_id}: inverted metalness range", issues)
        require(material["patternScaleStuds"]["min"] <= material["patternScaleStuds"]["max"], f"{material_id}: inverted pattern scale", issues)
        require(material["baseColorRole"] in palette_roles, f"{material_id}: unknown baseColorRole", issues)

    protected = set(lighting["protectedPropertyPolicy"]["properties"])
    require(protected == {"LightingStyle", "PrioritizeLightingQuality"}, "protected Lighting property set is unexpected", issues)
    require(set(lighting["profiles"]) == set(PROFILES), "lighting profile set is not canonical", issues)
    for profile_id, profile in lighting["profiles"].items():
        mutable_keys = set(profile["scriptMutable"].get("Lighting", {}))
        require(not (protected & mutable_keys), f"{profile_id}: protected property appears in scriptMutable", issues)
        require(set(profile["studioManualPreconditions"]) == protected, f"{profile_id}: protected preconditions incomplete", issues)

    counts = Counter(ref["territoryId"] for ref in provenance["references"] if ref["approvedStatus"].startswith("approved"))
    minimum = provenance["policy"]["minimumReferencesPerTerritory"]
    for territory_id in TERRITORIES:
        require(counts[territory_id] >= minimum, f"{territory_id}: fewer than {minimum} approved references", issues)
    reference_ids = [ref["referenceId"] for ref in provenance["references"]]
    require(len(reference_ids) == len(set(reference_ids)), "duplicate provenance referenceId", issues)
    for ref in provenance["references"]:
        if ref["embeddedInRepository"]:
            require(ref["licenseStatus"] in {"public_domain", "cc0"}, f"{ref['referenceId']}: embedded source is not redistributable", issues)
        require(ref["licenseStatus"] != "unknown_blocked", f"{ref['referenceId']}: unknown license blocks candidate board", issues)
    approval = provenance["humanApproval"]
    if approval["status"] == "APPROVED":
        require(bool(approval["reviewer"] and approval["reviewedAt"] and approval["decisionRecord"]), "approved provenance requires a signed human decision record", issues)

    weights = [dimension["weight"] for dimension in rubric["dimensions"].values()]
    require(_sum_close(weights, 100.0), "visual rubric weights must sum to 100", issues)
    gate_ids = set(rubric["hardGates"])
    require(TASK_GATE_IDS | TECH_GATE_IDS == gate_ids, "visual rubric hard-gate set differs from scorer contract", issues)
    require(protocol["minimumParticipants"] >= rubric["reviewPolicy"]["minimumTaskParticipants"], "task protocol participant minimum below rubric", issues)
    require(protocol["presentation"]["randomizeBlindLabelOrder"] is True, "blind label order must be randomized", issues)
    require(protocol["privacy"]["blindMapExcludedFromReviewerPackage"] is True, "blind map must be excluded from reviewer package", issues)
    task_ids: list[str] = []
    for group_id, group in protocol["taskGroups"].items():
        task_ids.extend(task["taskId"] for task in group["tasks"])
        gate = next((g for g in rubric["hardGates"].values() if g.get("taskGroupId") == group_id), None)
        require(gate is not None, f"task group {group_id} has no hard-gate mapping", issues)
    require(len(task_ids) == len(set(task_ids)), "task IDs must be unique", issues)

    visual_quality_path = ROOT / "evidence/blender/visual-quality-report.json"
    if visual_quality_path.is_file():
        visual_quality = load_json(visual_quality_path)
        expected_inputs = {
            "generator": sha256_file(ROOT / "tools/blender/build_art_direction.py"),
            "renderMatrix": sha256_file(ROOT / "art/calibration/render-matrix.json"),
        }
        require(
            visual_quality.get("inputHashes") == expected_inputs,
            "visual-quality evidence input hashes are stale",
            issues,
        )
        for territory in visual_quality.get("territories", []):
            for case in territory.get("cases", []):
                artifact_path = ROOT / case["path"]
                require(
                    artifact_path.is_file(),
                    f"visual-quality artifact is missing: {case['path']}",
                    issues,
                )
                if artifact_path.is_file():
                    require(
                        sha256_file(artifact_path) == case["sha256"],
                        f"visual-quality artifact hash drift: {case['path']}",
                        issues,
                    )

    transfer_report_path = ROOT / "evidence/transfer/turret-fast-v1/report.json"
    if transfer_report_path.is_file():
        transfer_result = validate_transfer_report(transfer_report_path)
        require(
            transfer_result["status"] == "PASS",
            "portable sixth-asset transfer report is stale or invalid: "
            + "; ".join(transfer_result["issues"]),
            issues,
        )

    transfer_manifest_path = (
        ROOT
        / "evidence/transfer/turret-fast-v1/studio-import-manifest.json"
    )
    transfer_manifest: dict[str, Any] | None = None
    if transfer_manifest_path.is_file():
        transfer_manifest = load_json(transfer_manifest_path)
        for entry in transfer_manifest.get("entries", []):
            source = ROOT / entry["sourcePath"]
            require(
                source.is_file(),
                f"portable transfer upload source is missing: {entry['sourcePath']}",
                issues,
            )
            if source.is_file():
                require(
                    source.stat().st_size == entry["bytes"],
                    f"portable transfer upload byte count drift: {entry['uploadName']}",
                    issues,
                )
                require(
                    sha256_file(source) == entry["sha256"],
                    f"portable transfer upload hash drift: {entry['uploadName']}",
                    issues,
                )

    publication_path = (
        ROOT
        / "evidence/transfer/turret-fast-v1/studio-publication-report.json"
    )
    publication: dict[str, Any] | None = None
    if publication_path.is_file():
        publication = load_json(publication_path)
        require(
            publication.get("status") == "PASS",
            "transfer staging publication report is not PASS",
            issues,
        )
        require(
            transfer_manifest is not None,
            "transfer staging publication exists without portable import manifest",
            issues,
        )
        if transfer_manifest is not None:
            require(
                publication.get("manifestSha256")
                == sha256_file(transfer_manifest_path),
                "transfer staging publication manifest hash is stale",
                issues,
            )
            require(
                {
                    (item["uploadName"], item["sourceSha256"])
                    for item in publication.get("entries", [])
                }
                == {
                    (item["uploadName"], item["sha256"])
                    for item in transfer_manifest["entries"]
                },
                "transfer staging publication entries differ from portable import manifest",
                issues,
            )
        expected_publication_inputs = {
            "transferReport": sha256_file(transfer_report_path),
            "publisher": sha256_file(
                ROOT / "tools/art/publish_transfer_candidates.py"
            ),
            "httpClient": sha256_file(
                ROOT / "tools/roblox-3d-asset/publisher/http_client.py"
            ),
            "importQueueBuilder": sha256_file(
                ROOT / "tools/art/build_transfer_import_queue.py"
            ),
        }
        require(
            publication.get("inputHashes") == expected_publication_inputs,
            "transfer staging publication implementation hashes are stale",
            issues,
        )

    studio_transfer_path = (
        ROOT / "evidence/transfer/turret-fast-v1/studio-transfer-report.json"
    )
    if studio_transfer_path.is_file():
        studio_transfer = load_json(studio_transfer_path)
        require(
            studio_transfer.get("status") in {"PASS", "PARTIAL"},
            "transfer Studio integration report is neither PASS nor truthful PARTIAL",
            issues,
        )
        if studio_transfer.get("status") == "PARTIAL":
            require(
                studio_transfer.get("captureChecks", {}).get("status")
                in {"BLOCKED", "NOT_REQUESTED", "FAIL"},
                "PARTIAL transfer Studio report must identify an incomplete capture gate",
                issues,
            )
            require(
                studio_transfer.get("playtestChecks", {}).get("pass") is True,
                "PARTIAL transfer Studio report lost its required core playtest proof",
                issues,
            )
        require(
            publication is not None and transfer_manifest is not None,
            "transfer Studio integration exists without publication/manifest evidence",
            issues,
        )
        if publication is not None and transfer_manifest is not None:
            expected_studio_inputs = {
                "transferManifest": sha256_file(transfer_manifest_path),
                "transferPublicationReport": sha256_file(publication_path),
                "transferEvidencePackage": transfer_manifest[
                    "evidencePackageSha256"
                ],
                "stageTransferTool": sha256_file(
                    ROOT / "tools/art/stage_transfer_studio.py"
                ),
                "studioMcpClient": sha256_file(
                    ROOT / "tools/art/studio_mcp.py"
                ),
                "materialRules": sha256_file(
                    ROOT / "art/materials/material-rules.json"
                ),
                "industrialTerritory": sha256_file(
                    ROOT / "art/territories/industrial-toy-defense.json"
                ),
                "salvagedTerritory": sha256_file(
                    ROOT / "art/territories/salvaged-frontier.json"
                ),
                "cleanTerritory": sha256_file(
                    ROOT / "art/territories/clean-tactical-diorama.json"
                ),
            }
            require(
                studio_transfer.get("inputHashes") == expected_studio_inputs,
                "transfer Studio integration input hashes are stale",
                issues,
            )
            require(
                {
                    (item["territoryId"], item["stateId"], item["sourceSha256"])
                    for item in studio_transfer.get("assetChecks", [])
                }
                == {
                    (item["territoryId"], item["stateId"], item["sha256"])
                    for item in transfer_manifest["entries"]
                },
                "transfer Studio asset readback differs from portable import manifest",
                issues,
            )
            require(
                all(
                    item.get("materialBindingsPass") is True
                    and item.get("styledMeshPartCount")
                    == item.get("meshPartCount")
                    and item.get("unboundStyleRoleCount") == 0
                    and item.get("maximumColorChannelError", 1) <= 0.00001
                    for item in studio_transfer.get("assetChecks", [])
                ),
                "transfer Studio material-role bindings are incomplete",
                issues,
            )
            captures = studio_transfer.get("captureChecks", {}).get(
                "captures", []
            )
            require(
                len(captures)
                == studio_transfer.get("captureChecks", {}).get(
                    "captureCount"
                ),
                "transfer Studio capture records differ from captureCount",
                issues,
            )
            for capture in captures:
                capture_path = ROOT / capture["path"]
                require(
                    capture_path.is_file(),
                    f"transfer Studio capture is missing: {capture['path']}",
                    issues,
                )
                if capture_path.is_file():
                    require(
                        capture_path.stat().st_size == capture["bytes"],
                        f"transfer Studio capture byte count drift: {capture['path']}",
                        issues,
                    )
                    require(
                        sha256_file(capture_path) == capture["sha256"],
                        f"transfer Studio capture hash drift: {capture['path']}",
                        issues,
                    )
            if studio_transfer.get("status") == "PASS":
                require(
                    {capture["territoryId"] for capture in captures}
                    == {
                        "industrial-toy-defense",
                        "salvaged-frontier",
                        "clean-tactical-diorama",
                    },
                    "PASS transfer Studio report lacks one capture per territory",
                    issues,
                )

    return issues


def validate_all() -> dict[str, Any]:
    report: dict[str, Any] = {
        "schemaVersion": "1.0.0",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "validator": "tools.art.validate_library",
        "pythonVersion": platform.python_version(),
        "status": "PASS",
        "schemaChecks": [],
        "manifestInstanceCount": 0,
        "semanticIssues": [],
        "generatedCodeIssues": [],
    }
    issues: list[str] = []

    for schema_path in sorted((ROOT / "schemas").glob("*.schema.json")):
        try:
            Draft202012Validator.check_schema(load_json(schema_path))
            report["schemaChecks"].append({"path": schema_path.relative_to(ROOT).as_posix(), "status": "PASS"})
        except Exception as exc:  # jsonschema raises different subclasses across versions
            message = f"Invalid schema {schema_path.relative_to(ROOT)}: {exc}"
            issues.append(message)
            report["schemaChecks"].append({"path": schema_path.relative_to(ROOT).as_posix(), "status": "FAIL", "error": str(exc)})

    manifest = load_json(ROOT / "schemas/manifest.json")
    report["manifestInstanceCount"] = len(manifest["mappings"])
    for mapping in manifest["mappings"]:
        instance_path = ROOT / mapping["path"]
        schema_path = ROOT / mapping["schema"]
        if not instance_path.exists():
            if mapping.get("required", True):
                issues.append(f"Missing manifest instance: {mapping['path']}")
            continue
        instance = load_json(instance_path)
        errors = validate_with_schema(instance, schema_path)
        issues.extend(f"{mapping['path']}{error}" for error in errors)

    semantic = semantic_checks()
    report["semanticIssues"] = semantic
    issues.extend(semantic)

    generated = generate(check=True)
    report["generatedCodeIssues"] = generated
    issues.extend(generated)

    if issues:
        report["status"] = "FAIL"
        report["issues"] = issues
    else:
        report["issues"] = []
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Strict schema and semantic validator for the art-direction system.")
    parser.add_argument("--report", type=Path, default=ROOT / "evidence/static-validation-report.json")
    args = parser.parse_args()
    report = validate_all()
    write_json(args.report, report)
    if report["status"] == "PASS":
        print(
            f"[PASS] {len(report['schemaChecks'])} schemas, "
            f"{report['manifestInstanceCount']} manifest instances, semantics and generated code validated."
        )
        return 0
    for issue in report["issues"]:
        print(f"[FAIL] {issue}")
    print(f"[FAIL] Validation report: {args.report}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
