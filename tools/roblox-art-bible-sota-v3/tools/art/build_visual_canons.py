from __future__ import annotations

"""Compile and verify the canonical visual definition for every asset x territory.

The authored source intentionally separates invariant object identity from
territory expression. The generated canon files are the closed, reviewable
contracts consumed by exploration and, once human-locked, production.
"""

import argparse
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from tools.art.common import (
    PROJECT_ROOT,
    ROOT,
    canonical_json_bytes,
    load_json,
    sha256_bytes,
    sha256_file,
    validate_with_schema,
    write_json,
)
from tools.art.product_art_authority import validate_product_art_authority

SOURCE_PATH = ROOT / "art/canonical-visuals/source.json"
CATALOG_PATH = ROOT / "art/canonical-visuals/catalog.json"
SOURCE_SCHEMA = ROOT / "schemas/visual-canon-source.schema.json"
CANON_SCHEMA = ROOT / "schemas/visual-canon.schema.json"
CATALOG_SCHEMA = ROOT / "schemas/visual-canon-catalog.schema.json"
LOCK_SCHEMA = ROOT / "schemas/visual-canon-lock.schema.json"
OBJECT_PRODUCT_CONTRACTS_PATH = (
    ROOT / "art/canonical-visuals/object-product-contracts.json"
)
OBJECT_PRODUCT_CONTRACTS_SCHEMA = (
    ROOT / "schemas/object-product-contracts.schema.json"
)
TERRITORIES = (
    "industrial-toy-defense",
    "salvaged-frontier",
    "clean-tactical-diorama",
)
ASSETS = (
    "barricade",
    "objective_core",
    "enemy_standard",
    "floor_module",
    "damage_effect",
    "turret_fast_v1",
)
STATUS_ORDER = {
    "DRAFT": 0,
    "CANDIDATE": 1,
    "ACCEPTED": 2,
    "LOCKED": 3,
    "REVISED": 3,
}


def _serialized(value: Any) -> bytes:
    return (
        json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


def _authority_path(name: str, relative: str) -> Path:
    if name == "retention":
        return PROJECT_ROOT / relative
    return ROOT / relative


def verify_authority(source: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for name, authority in source["authority"].items():
        path = _authority_path(name, authority["path"])
        if not path.is_file():
            issues.append(f"authority file missing: {name} -> {path}")
            continue
        observed = sha256_file(path)
        if observed != authority["sha256"]:
            issues.append(
                f"authority hash drift: {name} expected={authority['sha256']} observed={observed}"
            )
    return issues


def _asset_contracts() -> tuple[dict[str, Any], dict[str, Any]]:
    calibration = load_json(ROOT / "art/calibration/calibration-kit.json")
    transfer = load_json(ROOT / "art/transfer/turret-fast-v1.json")
    return calibration, transfer


def _technical_contract(
    asset_id: str,
    calibration: dict[str, Any],
    transfer: dict[str, Any],
) -> dict[str, Any]:
    if asset_id == "turret_fast_v1":
        return {
            "dimensions": transfer["dimensions"],
            "pivot": transfer["pivot"],
            "triangleBudgetMax": transfer["triangleBudgetMax"],
            "textureBudgetClass": transfer["textureBudgetClass"],
            "targetReadDistanceStuds": transfer["targetReadDistanceStuds"],
            "function": transfer["function"],
            "requiredStateVariants": transfer["requiredStateVariants"],
        }
    return calibration["assets"][asset_id]


def build_canon(
    source: dict[str, Any],
    object_product_contracts: dict[str, Any],
    asset_id: str,
    territory_id: str,
    calibration: dict[str, Any],
    transfer: dict[str, Any],
) -> dict[str, Any]:
    asset = source["assets"][asset_id]
    territory = source["territories"][territory_id]
    expression = territory["assetExpressions"][asset_id]
    product_contract = object_product_contracts["assets"][asset_id]
    technical = _technical_contract(asset_id, calibration, transfer)
    dimensions = technical["dimensions"]
    state_ids = technical["requiredStateVariants"]
    declared_state_ids = product_contract["runtimeStateModel"][
        "primaryGenerationStates"
    ]
    if state_ids != declared_state_ids:
        raise RuntimeError(
            f"{asset_id} primary generation states differ between technical "
            f"contract {state_ids} and product contract {declared_state_ids}"
        )
    art_overrides = expression.get("artDirectionOverrides", {})

    def art_value(name: str) -> Any:
        return art_overrides.get(name, territory[name])

    global_forbidden = load_json(
        ROOT / "art/shape-language/rules.json"
    )["forbidden"]
    combined_forbidden = _unique(
        asset["forbidden"] + art_value("forbidden") + global_forbidden
    )
    input_hashes = {
        "source": sha256_file(SOURCE_PATH),
        "productArtContract": source["authority"]["productArtContract"][
            "sha256"
        ],
        "retention": source["authority"]["retention"]["sha256"],
        "objectProductContracts": source["authority"][
            "objectProductContracts"
        ]["sha256"],
        "artDirection": source["authority"]["artDirection"]["sha256"],
        "calibration": source["authority"]["calibration"]["sha256"],
        "shapeLanguage": source["authority"]["shapeLanguage"]["sha256"],
        "materials": source["authority"]["materials"]["sha256"],
        "selectedConstitution": source["authority"]["selectedConstitution"][
            "sha256"
        ],
        "territory": sha256_file(
            ROOT / f"art/territories/{territory_id}.json"
        ),
        "generator": sha256_file(Path(__file__).resolve()),
    }
    materials = []
    for item in asset["materialIntent"]:
        translated = deepcopy(item)
        translated["territoryTranslation"] = expression.get(
            "materialTranslation",
            (
                f"{art_value('materialLanguage')} "
                f"{art_value('surfaceTreatment')} "
                f"Palette rule: {art_value('paletteLogic')}"
            ),
        )
        materials.append(translated)
    states = []
    for state_id in state_ids:
        authored = asset["states"][state_id]
        states.append(
            {
                "id": state_id,
                "summary": authored["summary"],
                "gameplayTruth": product_contract["stateTruth"][state_id],
                "invariants": asset["invariants"],
                "changes": authored["changes"],
                "cues": {
                    "shape": authored["silhouetteCues"],
                    "silhouette": authored["silhouetteCues"],
                    "value": authored["valueCues"],
                    "color": authored["colorCues"],
                    "light": authored["lightCues"],
                    "motion": authored["motionCues"],
                    "vfx": authored["vfxCues"],
                    "audio": authored["audioCues"],
                },
                "componentOperations": authored["componentOperations"],
                "transitions": authored["transitions"],
                "territoryTranslation": expression.get(
                    "stateTranslations", {}
                ).get(state_id, expression["stateTranslation"]),
            }
        )
    tolerance = calibration["sharedRules"]["dimensionToleranceStuds"]
    canon = {
        "$schema": "https://roblox-top1.local/schemas/visual-canon.schema.json",
        "schemaVersion": "2.0.0",
        "canonId": f"vc_{asset_id}__{territory_id}__v1",
        "assetId": asset_id,
        "territoryId": territory_id,
        "version": 1,
        "status": "CANDIDATE",
        "authority": source["authority"],
        "productIntent": {
            "retentionBinding": product_contract["retentionBinding"],
            "evidenceBoundary": object_product_contracts["globalRules"][
                "evidenceBoundary"
            ],
        },
        "runtimeStateModel": product_contract["runtimeStateModel"],
        "identity": {
            "canonicalName": asset["canonicalName"],
            "category": asset["category"],
            "gameplayFunction": technical["function"],
            "worldRole": asset["worldRole"],
            "affiliation": asset["affiliation"],
            "manufactureContext": asset["manufactureContext"],
            "emotionalIntent": asset["emotionalIntent"],
            "technologyLevel": asset["technologyLevel"],
            "character": asset["character"],
            "territoryVisualThesis": expression["visualThesis"],
        },
        "instantRead": {
            "oneSecondPromise": asset["oneSecondPromise"],
            "orientationCue": asset["orientationCue"],
            "interactionCue": asset["interactionCue"],
            "dangerCue": asset["dangerCue"],
            "relationToPlayer": asset["relationToPlayer"],
            "responsibleElements": _unique(
                asset["recognitionLandmarks"]
                + [
                    asset["orientationCue"],
                    asset["interactionCue"],
                    asset["dangerCue"],
                ]
            ),
        },
        "dimensions": {
            "unit": "stud",
            "width": dimensions["width"],
            "height": dimensions["height"],
            "depth": dimensions["depth"],
            "toleranceStuds": tolerance,
            "pivot": technical["pivot"],
            "proportionRules": asset["proportionRules"],
        },
        "silhouette": {
            "targetReadDistanceStuds": technical["targetReadDistanceStuds"],
            "views": asset["viewDescriptions"],
            "recognitionLandmarks": asset["recognitionLandmarks"],
            "negativeSpaces": asset["negativeSpaces"],
            "intentionalAsymmetry": art_value("asymmetry"),
            "distanceRule": (
                f"The primary function, orientation and state must remain readable "
                f"at {technical['targetReadDistanceStuds']} studs in the canonical "
                "mobile landscape and portrait views."
            ),
        },
        "formHierarchy": {
            "targetRatios": source["globalRules"]["detailHierarchy"],
            "primary": asset["primaryForms"],
            "secondary": asset["secondaryForms"],
            "tertiary": asset["tertiaryForms"],
            "territoryConstructionTranslation": expression[
                "constructionTranslation"
            ],
        },
        "construction": {
            "components": asset["components"],
            "plausibilityRules": [
                "Every visible part belongs to a named component and has a functional relationship to at least one neighboring component.",
                "No part floats, interpenetrates without an approved joint, or relies on unexplained support.",
                "Moving, replaceable and destructible components preserve declared axes, anchors and clearance.",
                "The compiler may simplify tertiary finish but may not remove a primary or secondary semantic component.",
            ],
            "stableNamingRule": "Component IDs and gameplay anchors never change without an approved canon revision.",
        },
        "artDirection": {
            "territoryThesis": art_value("thesis"),
            "shapeGrammar": art_value("shapeGrammar"),
            "exaggeration": art_value("exaggeration"),
            "edgeLanguage": art_value("edgeLanguage"),
            "detailDensity": art_value("detailDensity"),
            "asymmetry": art_value("asymmetry"),
            "materialLanguage": art_value("materialLanguage"),
            "paletteLogic": art_value("paletteLogic"),
            "surfaceTreatment": art_value("surfaceTreatment"),
            "wearLogic": art_value("wearLogic"),
            "signatureDetails": expression["signatureDetails"],
            "forbidden": art_value("forbidden"),
        },
        "materials": materials,
        "semanticZones": asset["semanticZones"],
        "states": states,
        "invariants": asset["invariants"],
        "allowedVariations": asset["allowedVariations"],
        "forbidden": combined_forbidden,
        "visualPacket": {
            "status": "SPECIFIED",
            "coverageRule": "If a component or state is absent from every bound board, the canon is incomplete and cannot be LOCKED.",
            "boards": [
                {
                    "id": board_id,
                    "required": True,
                    "status": "SPECIFIED",
                    "evidence": [],
                }
                for board_id in source["visualPacketBoards"]
            ],
        },
        "generationContract": {
            "mode": "RECONSTRUCT_CANON_DO_NOT_AUTHOR_OBJECT",
            "obligations": [
                "Reconstruct every primary and secondary component defined by this canon.",
                "Produce every required state from the same component structure and stable anchors.",
                "Preserve the one-second function, front, interaction, danger and state readings.",
                "Record this canon ID and exact SHA-256 in the compliance envelope.",
            ],
            "constraints": [
                f"Dimensions are {dimensions['width']} x {dimensions['height']} x {dimensions['depth']} studs with tolerance {tolerance}.",
                f"Triangle budget maximum is {technical['triangleBudgetMax']}.",
                f"Texture class is {technical['textureBudgetClass']}.",
                f"Pivot is {technical['pivot']} and component anchors remain stable.",
                "One UV set and one material slot maximum per production mesh component.",
            ],
            "tolerances": [
                f"Dimension error may not exceed {tolerance} stud.",
                "Only the explicitly listed allowedVariations may vary.",
                "Tertiary details may be simplified when they fall below the minimum mobile screen-space band.",
            ],
            "forbidden": combined_forbidden,
            "promptDiscipline": product_contract["promptDiscipline"],
            "complianceReportRequired": True,
            "minimumStatusForExploration": "CANDIDATE",
            "minimumStatusForProduction": "LOCKED",
            "silentCanonMutationForbidden": True,
        },
        "approval": {
            "required": True,
            "status": "PENDING",
            "approvedBy": None,
            "approvedAt": None,
            "decisionRecord": None,
            "approvedEvidencePackageSha256": None,
            "revisionReason": None,
        },
        "provenance": {
            "sourceKind": "AUTHORED_CANON_COMPILED_FROM_GDD_RETENTION_AND_ART_GRAMMAR",
            "authoredAt": source["authoredAt"],
            "authoredBy": source["authoredBy"],
            "generator": "tools.art.build_visual_canons",
            "inputHashes": input_hashes,
        },
    }
    lock_path = (
        ROOT
        / "art/canonical-visuals/locks"
        / territory_id
        / f"{asset_id}.json"
    )
    if not lock_path.is_file():
        return canon
    overlay = load_json(lock_path)
    overlay_errors = validate_with_schema(overlay, LOCK_SCHEMA)
    if overlay_errors:
        raise RuntimeError(
            f"{territory_id}/{asset_id} lock overlay invalid: "
            + "; ".join(overlay_errors)
        )
    candidate_sha = sha256_bytes(_serialized(canon))
    if overlay["baseCandidateSha256"] != candidate_sha:
        raise RuntimeError(
            f"{territory_id}/{asset_id} lock overlay targets a stale candidate"
        )
    expected_boards = {
        board["id"] for board in canon["visualPacket"]["boards"]
    }
    if set(overlay["boards"]) != expected_boards:
        raise RuntimeError(
            f"{territory_id}/{asset_id} lock overlay board set differs from canon"
        )
    for artifacts in overlay["boards"].values():
        for artifact in artifacts:
            artifact_path = ROOT / artifact["path"]
            if not artifact_path.is_file():
                raise RuntimeError(
                    f"locked visual evidence missing: {artifact['path']}"
                )
            if sha256_file(artifact_path) != artifact["sha256"]:
                raise RuntimeError(
                    f"locked visual evidence hash drift: {artifact['path']}"
                )
    canon["version"] = overlay["version"]
    canon["canonId"] = f"vc_{asset_id}__{territory_id}__v{overlay['version']}"
    canon["status"] = overlay["status"]
    canon["visualPacket"]["status"] = "COMPLETE"
    for board in canon["visualPacket"]["boards"]:
        board["status"] = "BOUND"
        board["evidence"] = overlay["boards"][board["id"]]
    canon["approval"] = {
        "required": True,
        "status": "APPROVED",
        "approvedBy": overlay["approval"]["approvedBy"],
        "approvedAt": overlay["approval"]["approvedAt"],
        "decisionRecord": overlay["approval"]["decisionRecord"],
        "approvedEvidencePackageSha256": overlay[
            "visualEvidencePackageSha256"
        ],
        "revisionReason": overlay["approval"]["revisionReason"],
    }
    canon["provenance"]["inputHashes"]["lockOverlay"] = sha256_file(lock_path)
    return canon


def build_all() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    source = load_json(SOURCE_PATH)
    source_errors = validate_with_schema(source, SOURCE_SCHEMA)
    if source_errors:
        raise RuntimeError(
            "visual canon source is invalid: " + "; ".join(source_errors)
        )
    authority_issues = verify_authority(source)
    if authority_issues:
        raise RuntimeError("; ".join(authority_issues))
    product_art_path = _authority_path(
        "productArtContract",
        source["authority"]["productArtContract"]["path"],
    )
    product_art_issues = validate_product_art_authority(product_art_path)
    if product_art_issues:
        raise RuntimeError(
            "product art authority is invalid: "
            + "; ".join(product_art_issues)
        )
    object_product_contracts = load_json(OBJECT_PRODUCT_CONTRACTS_PATH)
    object_contract_errors = validate_with_schema(
        object_product_contracts,
        OBJECT_PRODUCT_CONTRACTS_SCHEMA,
    )
    if object_contract_errors:
        raise RuntimeError(
            "object product contracts are invalid: "
            + "; ".join(object_contract_errors)
        )
    if (
        object_product_contracts["authority"]["productArtContract"]
        != source["authority"]["productArtContract"]
    ):
        raise RuntimeError(
            "object product contracts do not bind the active product art "
            "authority"
        )
    expected_retention = {
        "path": source["authority"]["retention"]["path"],
        "sha256": source["authority"]["retention"]["sha256"],
    }
    if (
        object_product_contracts["authority"]["retentionDoctrine"]
        != expected_retention
    ):
        raise RuntimeError(
            "object product contracts do not bind the active accepted "
            "retention doctrine"
        )
    source = deepcopy(source)
    source["globalRules"] = load_json(product_art_path)["globalRules"]
    calibration, transfer = _asset_contracts()
    canons: dict[str, dict[str, Any]] = {}
    entries: list[dict[str, Any]] = []
    state_count = 0
    for territory_id in TERRITORIES:
        for asset_id in ASSETS:
            canon = build_canon(
                source,
                object_product_contracts,
                asset_id,
                territory_id,
                calibration,
                transfer,
            )
            errors = validate_with_schema(canon, CANON_SCHEMA)
            if errors:
                raise RuntimeError(
                    f"{territory_id}/{asset_id} canon invalid: "
                    + "; ".join(errors)
                )
            relative = (
                Path("art/canonical-visuals")
                / territory_id
                / f"{asset_id}.json"
            )
            serialized = _serialized(canon)
            digest = sha256_bytes(serialized)
            canons[relative.as_posix()] = canon
            state_ids = [state["id"] for state in canon["states"]]
            state_count += len(state_ids)
            production_eligible = (
                canon["status"] == "LOCKED"
                and canon["visualPacket"]["status"] == "COMPLETE"
                and canon["approval"]["status"] == "APPROVED"
            )
            entries.append(
                {
                    "canonId": canon["canonId"],
                    "assetId": asset_id,
                    "territoryId": territory_id,
                    "version": canon["version"],
                    "status": canon["status"],
                    "path": relative.as_posix(),
                    "sha256": digest,
                    "stateIds": state_ids,
                    "visualPacketStatus": canon["visualPacket"]["status"],
                    "productionEligible": production_eligible,
                }
            )
    art_direction = load_json(ROOT / "art/art-direction.json")
    selected_territory = art_direction["finalTerritory"]
    selected_entries = [
        entry
        for entry in entries
        if entry["territoryId"] == selected_territory
    ]
    eligible_count = sum(
        entry["productionEligible"] for entry in selected_entries
    )
    required_count = len(ASSETS) if selected_territory else 0
    catalog = {
        "$schema": "https://roblox-top1.local/schemas/visual-canon-catalog.schema.json",
        "schemaVersion": "1.0.0",
        "generatedAt": source["authoredAt"],
        "status": "PASS",
        "sourcePath": "art/canonical-visuals/source.json",
        "sourceSha256": sha256_file(SOURCE_PATH),
        "authorityHashes": {
            name: value["sha256"]
            for name, value in source["authority"].items()
        },
        "coverage": {
            "territoryCount": len(TERRITORIES),
            "assetCount": len(ASSETS),
            "canonCount": len(entries),
            "stateDefinitionCount": state_count,
            "territories": list(TERRITORIES),
            "assets": list(ASSETS),
        },
        "entries": entries,
        "productionGate": {
            "selectedTerritory": selected_territory,
            "requiredCanonStatus": "LOCKED",
            "requiredVisualPacketStatus": "COMPLETE",
            "humanApprovalRequired": True,
            "requiredCanonCount": required_count,
            "eligibleCanonCount": eligible_count,
            "status": (
                "PASS"
                if selected_territory and eligible_count == required_count
                else "BLOCKED"
            ),
            "reason": (
                "Every canon in the selected territory is locked, visually bound and human-approved."
                if selected_territory and eligible_count == required_count
                else (
                    "The selected territory is fixed, but its six canons still require complete multimodal board binding and explicit human lock."
                    if selected_territory
                    else "Candidate canons are complete as textual contracts, but human territory selection is still required."
                )
            ),
        },
    }
    catalog_errors = validate_with_schema(catalog, CATALOG_SCHEMA)
    if catalog_errors:
        raise RuntimeError(
            "visual canon catalog invalid: " + "; ".join(catalog_errors)
        )
    return canons, catalog


def write_all() -> dict[str, Any]:
    canons, catalog = build_all()
    for relative, canon in canons.items():
        write_json(ROOT / relative, canon)
    write_json(CATALOG_PATH, catalog)
    return catalog


def check_all(require_locked: bool = False) -> list[str]:
    canons, catalog = build_all()
    issues: list[str] = []
    expected_paths = set(canons)
    for relative, expected in canons.items():
        path = ROOT / relative
        if not path.is_file():
            issues.append(f"missing generated canon: {relative}")
            continue
        observed = load_json(path)
        if canonical_json_bytes(observed) != canonical_json_bytes(expected):
            issues.append(f"generated canon drift: {relative}")
        errors = validate_with_schema(observed, CANON_SCHEMA)
        issues.extend(f"{relative}{error}" for error in errors)
    generated_root = ROOT / "art/canonical-visuals"
    observed_paths = {
        path.relative_to(ROOT).as_posix()
        for path in generated_root.glob("*/*.json")
    }
    for extra in sorted(observed_paths - expected_paths):
        issues.append(f"unexpected generated canon: {extra}")
    if not CATALOG_PATH.is_file():
        issues.append("missing visual canon catalog")
    else:
        observed_catalog = load_json(CATALOG_PATH)
        if canonical_json_bytes(observed_catalog) != canonical_json_bytes(
            catalog
        ):
            issues.append("visual canon catalog drift")
        errors = validate_with_schema(observed_catalog, CATALOG_SCHEMA)
        issues.extend(f"catalog{error}" for error in errors)
    if require_locked:
        selected_territory = catalog["productionGate"]["selectedTerritory"]
        if not selected_territory:
            issues.append("production requires a selected territory")
        blocked = [
            entry["canonId"]
            for entry in catalog["entries"]
            if entry["territoryId"] == selected_territory
            and not entry["productionEligible"]
        ]
        if blocked:
            issues.append(
                "production requires LOCKED + COMPLETE + APPROVED canons: "
                + ", ".join(blocked)
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build or verify every object x art-direction visual canon."
    )
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--require-locked", action="store_true")
    args = parser.parse_args()
    if args.check:
        issues = check_all(require_locked=args.require_locked)
        if issues:
            blocked_only = args.require_locked and all(
                issue.startswith(
                    "production requires LOCKED + COMPLETE + APPROVED canons:"
                )
                for issue in issues
            )
            for issue in issues:
                print(f"[{'BLOCKED' if blocked_only else 'FAIL'}] {issue}")
            return 2 if blocked_only else 1
        print("[PASS] 18 visual canons and 48 state definitions are current.")
        return 0
    catalog = write_all()
    print(
        "[PASS] Compiled "
        f"{catalog['coverage']['canonCount']} visual canons covering "
        f"{catalog['coverage']['stateDefinitionCount']} states. "
        f"Production gate: {catalog['productionGate']['status']}."
    )
    if args.require_locked and catalog["productionGate"]["status"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
