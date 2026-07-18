from __future__ import annotations

import copy
import json
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image

from tools.art.build_visual_canons import (
    ASSETS,
    TERRITORIES,
    build_all,
    check_all,
)
from tools.art.common import ROOT, load_json, sha256_file, validate_with_schema
from tools.art.prepare_canon_generation import prepare
from tools.art.lock_visual_canon import create_lock
from tools.art.product_art_authority import (
    AUTHORITY_PATH,
    projection_sha256,
    validate_product_art_authority,
)
from tools.art.visual_canon_evidence import (
    compute_evidence_package_sha256,
    validate_evidence_manifest,
    validate_human_review,
)


def test_visual_canon_coverage_and_determinism() -> None:
    canons, catalog = build_all()
    assert len(canons) == 18
    assert catalog["coverage"]["canonCount"] == 18
    assert catalog["coverage"]["stateDefinitionCount"] == 48
    assert not check_all()


def test_product_art_authority_binds_only_selected_gdd_sections() -> None:
    authority = load_json(AUTHORITY_PATH)
    projection = authority["sourceProjection"]
    gdd_path = ROOT.parents[1] / projection["gddPath"]
    markdown = gdd_path.read_text(encoding="utf-8")
    expected = projection["contentSha256"]

    assert not validate_product_art_authority()
    assert projection_sha256(markdown, projection["sectionHeadings"]) == expected
    assert (
        projection_sha256(
            markdown + "\nUnrelated repository-audit note.\n",
            projection["sectionHeadings"],
        )
        == expected
    )

    changed = markdown.replace(
        "construit librement une forteresse persistante",
        "construit librement une forteresse jetable",
        1,
    )
    assert changed != markdown
    assert projection_sha256(changed, projection["sectionHeadings"]) != expected


def test_every_object_x_territory_pair_exists_once() -> None:
    catalog = load_json(ROOT / "art/canonical-visuals/catalog.json")
    pairs = [
        (entry["territoryId"], entry["assetId"])
        for entry in catalog["entries"]
    ]
    assert len(pairs) == len(set(pairs)) == len(TERRITORIES) * len(ASSETS)


def test_catalog_hashes_every_generated_canon() -> None:
    catalog = load_json(ROOT / "art/canonical-visuals/catalog.json")
    for entry in catalog["entries"]:
        assert sha256_file(ROOT / entry["path"]) == entry["sha256"]


def test_every_state_has_redundant_non_color_cues() -> None:
    catalog = load_json(ROOT / "art/canonical-visuals/catalog.json")
    cue_ids = {
        "shape",
        "silhouette",
        "value",
        "color",
        "light",
        "motion",
        "vfx",
        "audio",
    }
    for entry in catalog["entries"]:
        canon = load_json(ROOT / entry["path"])
        for state in canon["states"]:
            assert set(state["cues"]) == cue_ids
            assert all(state["cues"][cue] for cue in cue_ids)
            assert state["cues"]["shape"]
            assert state["cues"]["value"]
            assert state["cues"]["motion"]
            assert state["cues"]["audio"]


def test_selected_canons_bind_product_truth_and_prompt_discipline() -> None:
    source = load_json(ROOT / "art/canonical-visuals/source.json")
    retention = source["authority"]["retention"]
    assert (
        retention["path"]
        == "docs/PRODUCT_INNOVATION_AND_RETENTION_DOCTRINE.md"
    )
    assert (
        sha256_file(ROOT.parents[1] / retention["path"])
        == retention["sha256"]
    )

    expected_states = {
        "barricade": ["intact", "damaged", "critical"],
        "objective_core": ["intact", "damaged", "critical"],
        "enemy_standard": ["intact", "damaged", "critical"],
        "floor_module": ["intact", "damaged"],
        "damage_effect": ["damaged", "critical"],
        "turret_fast_v1": ["intact", "damaged", "critical"],
    }
    for asset_id, state_ids in expected_states.items():
        canon = load_json(
            ROOT
            / "art/canonical-visuals/salvaged-frontier"
            / f"{asset_id}.json"
        )
        assert canon["productIntent"]["retentionBinding"][
            "primaryHypothesis"
        ]["id"] == "H-FAILURE-001"
        assert (
            canon["productIntent"]["retentionBinding"]["evidenceStatus"]
            == "UNPROVEN"
        )
        assert (
            canon["runtimeStateModel"]["primaryGenerationStates"]
            == state_ids
        )
        assert [state["id"] for state in canon["states"]] == state_ids
        assert all(state["gameplayTruth"] for state in canon["states"])
        assert canon["generationContract"]["promptDiscipline"][
            "identityLockRules"
        ]
        assert canon["generationContract"]["promptDiscipline"][
            "outputSelfChecks"
        ]


def test_selected_canon_language_does_not_overclaim_gameplay() -> None:
    root = ROOT / "art/canonical-visuals/salvaged-frontier"
    barricade = load_json(root / "barricade.json")
    floor = load_json(root / "floor_module.json")
    enemy = load_json(root / "enemy_standard.json")
    effect = load_json(root / "damage_effect.json")
    turret = load_json(root / "turret_fast_v1.json")

    barricade_critical = next(
        state for state in barricade["states"] if state["id"] == "critical"
    )
    assert "never a human-sized" in " ".join(
        barricade_critical["changes"]
    )
    assert "passage-like breach" not in json.dumps(barricade_critical)

    assert [state["id"] for state in floor["states"]] == [
        "intact",
        "damaged",
    ]
    assert "critical state" not in " ".join(
        state["territoryTranslation"] for state in floor["states"]
    ).lower()

    enemy_text = json.dumps(enemy, ensure_ascii=False).lower()
    assert "fixed hostile condition" in enemy_text
    assert "hostile adaptation" not in enemy_text
    assert "adaptive learning" in enemy_text
    assert "standardized chassis" not in json.dumps(
        enemy["artDirection"],
        ensure_ascii=False,
    ).lower()

    effect_art = json.dumps(effect["artDirection"], ensure_ascii=False).lower()
    assert "transient salvaged frontier impact sentence" in effect_art
    assert "standardized chassis" not in effect_art

    turret_text = json.dumps(turret, ensure_ascii=False).lower()
    assert "visually ready" in turret_text
    assert "only functional barrel recoils" not in turret_text
    assert "tracking fully stopped" not in turret_text


def test_component_evidence_map_covers_every_calibration_component() -> None:
    mapping = load_json(ROOT / "art/calibration/component-evidence-map.json")
    catalog = load_json(ROOT / "art/canonical-visuals/catalog.json")
    checked_assets: set[str] = set()
    for entry in catalog["entries"]:
        asset_id = entry["assetId"]
        if asset_id == "turret_fast_v1" or asset_id in checked_assets:
            continue
        canon = load_json(ROOT / entry["path"])
        expected = {
            component["id"] for component in canon["construction"]["components"]
        }
        rows = mapping["assets"][asset_id]["components"]
        observed = {row["componentId"] for row in rows}
        assert observed == expected
        assert all(row["objectNamePatterns"] for row in rows)
        checked_assets.add(asset_id)
    assert checked_assets == set(mapping["assets"])


def test_locked_canon_rejects_unbound_visual_packet() -> None:
    canon = load_json(
        ROOT
        / "art/canonical-visuals/industrial-toy-defense/barricade.json"
    )
    invalid = copy.deepcopy(canon)
    invalid["status"] = "LOCKED"
    invalid["approval"]["status"] = "APPROVED"
    invalid["approval"]["approvedBy"] = "Founder"
    invalid["approval"]["approvedAt"] = "2026-07-16T15:00:00Z"
    invalid["approval"]["decisionRecord"] = "decisions/canon-lock.md"
    invalid["approval"][
        "approvedEvidencePackageSha256"
    ] = "a" * 64
    errors = validate_with_schema(
        invalid, ROOT / "schemas/visual-canon.schema.json"
    )
    assert any("COMPLETE" in error or "BOUND" in error for error in errors)


def test_production_preflight_blocks_candidate_canons(
    tmp_path: Path,
) -> None:
    output = tmp_path / "authority.json"
    result = prepare(
        "industrial-toy-defense",
        "calibration",
        True,
        output,
    )
    assert result["status"] == "BLOCKED"
    assert len(result["blockingReasons"]) == 5
    assert output.is_file()


def test_exploration_preflight_binds_exact_hashes(
    tmp_path: Path,
) -> None:
    output = tmp_path / "authority.json"
    result = prepare(
        "industrial-toy-defense",
        "calibration",
        False,
        output,
    )
    assert result["status"] == "PASS"
    assert result["mode"] == "EXPLORATION"
    assert len(result["canonBindings"]) == 5
    catalog = load_json(ROOT / "art/canonical-visuals/catalog.json")
    expected = {
        entry["canonId"]: entry["sha256"]
        for entry in catalog["entries"]
        if entry["territoryId"] == "industrial-toy-defense"
        and entry["assetId"] != "turret_fast_v1"
    }
    assert {
        item["canonId"]: item["sha256"]
        for item in result["canonBindings"]
    } == expected


def test_human_lock_is_blocked_before_final_territory_selection(
    tmp_path: Path,
) -> None:
    result = create_lock(
        "barricade",
        "industrial-toy-defense",
        tmp_path / "missing-evidence.json",
        "Founder",
        "decisions/canon-lock.md",
        None,
        False,
    )
    assert result["status"] == "BLOCKED"
    assert "human-selected final territory" in result["reason"]


def _synthetic_evidence(root: Path) -> tuple[dict, Path, dict, list[str]]:
    canon_path = (
        ROOT / "art/canonical-visuals/salvaged-frontier/barricade.json"
    )
    canon = load_json(canon_path)
    required_boards = [
        board["id"] for board in canon["visualPacket"]["boards"]
    ]
    boards = {}
    for index, board_id in enumerate(required_boards):
        board_path = root / f"{index + 1:02d}-{board_id}.png"
        Image.new("RGB", (640, 360), (31 + index, 47, 61)).save(
            board_path,
            format="PNG",
        )
        boards[board_id] = [
            {
                "path": board_path.relative_to(ROOT).as_posix(),
                "bytes": board_path.stat().st_size,
                "sha256": sha256_file(board_path),
                "mediaType": "image/png",
                "width": 640,
                "height": 360,
            }
        ]
    manifest = {
        "$schema": "https://roblox-top1.local/schemas/visual-canon-evidence.schema.json",
        "schemaVersion": "1.0.0",
        "assetKey": "simulation_barricade",
        "revision": 6,
        "assetId": "barricade",
        "territoryId": "salvaged-frontier",
        "canonId": canon["canonId"],
        "baseCandidateSha256": sha256_file(canon_path),
        "evidenceClass": "SYNTHETIC_DOUBLE",
        "generatedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
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
                    "path": canon_path.relative_to(ROOT).as_posix(),
                    "bytes": canon_path.stat().st_size,
                    "sha256": sha256_file(canon_path),
                }
            ]
        },
        "boards": boards,
        "humanReviewStatus": "PASS",
        "productionApproved": False,
    }
    manifest["evidencePackageSha256"] = compute_evidence_package_sha256(
        manifest
    )
    return manifest, canon_path, canon, required_boards


def test_visual_evidence_digest_and_paths_fail_closed() -> None:
    build_root = ROOT / "build"
    build_root.mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="canon-evidence-test-", dir=build_root))
    try:
        manifest, canon_path, canon, required_boards = _synthetic_evidence(
            folder
        )
        assert not validate_evidence_manifest(
            manifest,
            required_boards=required_boards,
            candidate_path=canon_path,
            candidate=canon,
            apply=False,
        )

        tampered_digest = copy.deepcopy(manifest)
        tampered_digest["evidencePackageSha256"] = "0" * 64
        assert any(
            "canonical payload" in issue
            for issue in validate_evidence_manifest(
                tampered_digest,
                required_boards=required_boards,
                candidate_path=canon_path,
                candidate=canon,
                apply=False,
            )
        )

        escaped = copy.deepcopy(manifest)
        first_board = required_boards[0]
        escaped["boards"][first_board][0]["path"] = "../escape.png"
        escaped["evidencePackageSha256"] = compute_evidence_package_sha256(
            escaped
        )
        assert any(
            "escapes" in issue
            for issue in validate_evidence_manifest(
                escaped,
                required_boards=required_boards,
                candidate_path=canon_path,
                candidate=canon,
                apply=False,
            )
        )

        tampered_board = copy.deepcopy(manifest)
        tampered_board["boards"][first_board][0]["sha256"] = "f" * 64
        tampered_board["evidencePackageSha256"] = (
            compute_evidence_package_sha256(tampered_board)
        )
        assert any(
            "SHA-256 drift" in issue
            for issue in validate_evidence_manifest(
                tampered_board,
                required_boards=required_boards,
                candidate_path=canon_path,
                candidate=canon,
                apply=False,
            )
        )
    finally:
        shutil.rmtree(folder)


def _human_review(
    evidence: dict,
    evidence_manifest_path: Path,
    required_boards: list[str],
) -> dict:
    return {
        "$schema": "https://roblox-top1.local/schemas/visual-canon-human-review.schema.json",
        "schemaVersion": "1.0.0",
        "status": "APPROVED",
        "assetKey": evidence["assetKey"],
        "assetId": evidence["assetId"],
        "territoryId": evidence["territoryId"],
        "revision": 6,
        "canonId": evidence["canonId"],
        "evidenceManifest": evidence_manifest_path.relative_to(ROOT).as_posix(),
        "evidenceManifestSha256": sha256_file(evidence_manifest_path),
        "evidencePackageSha256": evidence["evidencePackageSha256"],
        "reviewer": "Founder",
        "reviewedAt": "2026-07-17T13:00:00Z",
        "decision": "LOCK",
        "decisionRecord": "Approved after complete board-by-board review.",
        "allowedDecisions": ["LOCK", "REVISION_REQUIRED", "REJECT"],
        "boards": {
            board_id: {"status": "PASS", "comment": None}
            for board_id in required_boards
        },
        "mandatoryChecks": {
            "oneSecondFunctionRead": "PASS",
            "stateReadWithoutColorOnly": "PASS",
            "mobileNearMidFar": "PASS",
            "lightingRobustness": "PASS",
            "repetitionOneThirtyHundred": "PASS",
            "requiredAndForbiddenCompliance": "PASS",
            "artDirectionQuality": "PASS",
        },
        "productionApproved": False,
    }


def test_human_review_is_hash_bound_and_fail_closed() -> None:
    build_root = ROOT / "build"
    build_root.mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="canon-human-review-", dir=build_root))
    try:
        evidence, _canon_path, _canon, required_boards = _synthetic_evidence(
            folder
        )
        evidence["evidenceClass"] = "REAL_RENDERED"
        evidence["generation"]["rawRenderStatus"] = "PASS"
        evidence["evidencePackageSha256"] = compute_evidence_package_sha256(
            evidence
        )
        evidence_path = folder / "evidence-manifest.json"
        evidence_path.write_text(
            json.dumps(evidence, indent=2) + "\n",
            encoding="utf-8",
        )
        review = _human_review(evidence, evidence_path, required_boards)
        assert not validate_human_review(
            review,
            evidence_manifest_path=evidence_path,
            evidence=evidence,
            required_boards=required_boards,
            require_lock=True,
        )

        tampered = copy.deepcopy(review)
        tampered["evidencePackageSha256"] = "0" * 64
        assert any(
            "evidencePackageSha256" in issue
            for issue in validate_human_review(
                tampered,
                evidence_manifest_path=evidence_path,
                evidence=evidence,
                required_boards=required_boards,
                require_lock=True,
            )
        )

        incomplete = copy.deepcopy(review)
        incomplete["boards"][required_boards[0]]["status"] = "PENDING"
        assert any(
            "pending boards" in issue or "every reviewed board" in issue
            for issue in validate_human_review(
                incomplete,
                evidence_manifest_path=evidence_path,
                evidence=evidence,
                required_boards=required_boards,
                require_lock=True,
            )
        )

        contradictory = copy.deepcopy(review)
        contradictory["mandatoryChecks"]["artDirectionQuality"] = "FAIL"
        assert any(
            "LOCK requires" in issue
            for issue in validate_human_review(
                contradictory,
                evidence_manifest_path=evidence_path,
                evidence=evidence,
                required_boards=required_boards,
                require_lock=True,
            )
        )
    finally:
        shutil.rmtree(folder)


def test_synthetic_evidence_can_preview_but_never_apply() -> None:
    build_root = ROOT / "build"
    build_root.mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="canon-lock-test-", dir=build_root))
    try:
        manifest, _canon_path, _canon, _required_boards = (
            _synthetic_evidence(folder)
        )
        manifest_path = folder / "evidence-manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        preview = create_lock(
            "barricade",
            "salvaged-frontier",
            manifest_path,
            "SIMULATED_REVIEWER",
            "build/simulated-decision.json",
            None,
            False,
        )
        assert preview["status"] == "PARTIAL"
        assert preview["overlay"]["evidenceClass"] == "SYNTHETIC_DOUBLE"

        applied = create_lock(
            "barricade",
            "salvaged-frontier",
            manifest_path,
            "Founder",
            "docs/decisions/canon-lock.md",
            None,
            True,
        )
        assert applied["status"] == "FAIL"
        assert any("cannot be applied" in issue for issue in applied["issues"])
    finally:
        shutil.rmtree(folder)
