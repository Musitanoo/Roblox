from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml
import numpy as np

from tools.art.common import ROOT, load_json, sha256_file, validate_with_schema
from tools.art.color_math import hex_to_linear_rgba, srgb_to_linear
from tools.art.generate_luau import generate, to_luau
from tools.art.pixel_math import projected_pixels, required_thickness
from tools.art.recipe_contract import (
    EXECUTABLE_RECIPE_FIELDS,
    STATE_STRATEGY_PROFILES,
    VALIDATION_TARGET_RECIPE_FIELDS,
    declared_recipe_fields,
)
from tools.art.score_territories import score
from tools.art.validate_library import validate_all
from tools.art.validate_performance_report import validate_report as validate_performance_report
from tools.art.validate_studio_simulator_report import (
    validate_report as validate_studio_simulator_report,
)
from tools.art.validate_studio_report import validate_report as validate_studio_report
from tools.art.validate_transfer_report import validate_report as validate_transfer_report
from tools.art.measure_visual_quality import compare_masks, mask_metrics

TERRITORIES = [
    "industrial-toy-defense",
    "salvaged-frontier",
    "clean-tactical-diorama",
]
LABELS = ["A", "B", "C"]


def _schema_errors(instance: dict, schema_name: str) -> list[str]:
    return validate_with_schema(instance, ROOT / "schemas" / schema_name)


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _valid_study(tmp_path: Path) -> tuple[Path, Path, dict, dict]:
    protocol = load_json(ROOT / "art/qa/task-protocol.json")
    rubric = load_json(ROOT / "art/qa/visual-rubric.json")
    task_ids = [
        task["taskId"]
        for group in protocol["taskGroups"].values()
        for task in group["tasks"]
    ]
    dimension_ids = list(rubric["dimensions"])
    technical_ids = [
        gate_id
        for gate_id, gate in rubric["hardGates"].items()
        if gate["kind"] == "technical_boolean"
    ]

    participants = []
    for index in range(8):
        responses = []
        for label in LABELS:
            for task_id in task_ids:
                responses.append(
                    {
                        "blindLabel": label,
                        "taskId": task_id,
                        "correct": True,
                        "confidence": 0.9,
                        "responseTimeMs": 900,
                    }
                )
        participants.append(
            {
                "participantId": f"P{index + 1:02d}",
                "deviceClass": "mobile",
                "responses": responses,
            }
        )

    expert_reviews = []
    for index in range(2):
        ratings = []
        for label in LABELS:
            for dimension_id in dimension_ids:
                ratings.append(
                    {
                        "blindLabel": label,
                        "dimensionId": dimension_id,
                        "score": 5.0,
                        "confidence": 0.9,
                    }
                )
        expert_reviews.append({"reviewerId": f"R{index + 1:02d}", "ratings": ratings})

    evidence_rel = "tests/fixtures/mock-technical-evidence.json"
    evidence_hash = sha256_file(ROOT / evidence_rel)
    technical = {
        label: {
            gate_id: {
                "pass": True,
                "evidencePath": evidence_rel,
                "sha256": evidence_hash,
            }
            for gate_id in technical_ids
        }
        for label in LABELS
    }

    submissions = {
        "$schema": "https://roblox-top1.local/schemas/reviewer-submissions.schema.json",
        "schemaVersion": "2.0.0",
        "studyId": protocol["studyId"],
        "status": "SEALED",
        "sealedAt": "2026-07-15T12:00:00Z",
        "participants": participants,
        "expertReviews": expert_reviews,
        "technicalEvidenceByBlindLabel": technical,
    }
    submissions_path = tmp_path / "submissions.json"
    _write_json(submissions_path, submissions)

    blind_map = {
        "$schema": "https://roblox-top1.local/schemas/blind-map.schema.json",
        "schemaVersion": "2.0.0",
        "studyId": protocol["studyId"],
        "generatedAt": "2026-07-15T12:01:00Z",
        "mapping": {
            "A": "industrial-toy-defense",
            "B": "salvaged-frontier",
            "C": "clean-tactical-diorama",
        },
        "sealedSubmissionsSha256": sha256_file(submissions_path),
        "saltId": "test-salt-001",
    }
    blind_map_path = tmp_path / "blind-map.json"
    _write_json(blind_map_path, blind_map)
    return submissions_path, blind_map_path, submissions, blind_map


def _rewrite_pair(
    submissions_path: Path,
    blind_map_path: Path,
    submissions: dict,
    blind_map: dict,
) -> None:
    _write_json(submissions_path, submissions)
    blind_map["sealedSubmissionsSha256"] = sha256_file(submissions_path)
    _write_json(blind_map_path, blind_map)


def test_full_static_validator_passes() -> None:
    report = validate_all()
    assert report["status"] == "PASS", report.get("issues")


def test_generated_luau_is_exactly_in_sync() -> None:
    assert generate(check=True) == []


def test_exploration_cannot_claim_production_approval() -> None:
    art = load_json(ROOT / "art/art-direction.json")
    art["productionApproved"] = True
    errors = _schema_errors(art, "art-direction.schema.json")
    assert any("False was expected" in error or "false" in error.lower() for error in errors)


def test_exploration_cannot_name_a_final_territory() -> None:
    art = load_json(ROOT / "art/art-direction.json")
    art["status"] = "EXPLORATION"
    art["finalTerritory"] = "industrial-toy-defense"
    errors = _schema_errors(art, "art-direction.schema.json")
    assert errors


def test_founder_selection_is_bound_to_current_constitution() -> None:
    art = load_json(ROOT / "art/art-direction.json")
    constitution_path = (
        ROOT / "art/selected/salvaged-frontier-constitution.json"
    )
    constitution = load_json(constitution_path)
    decision = load_json(
        ROOT / "art/decision/founder-direction-decision.json"
    )
    assert art["status"] == "CANDIDATE_SELECTED"
    assert art["finalTerritory"] == "salvaged-frontier"
    assert art["productionApproved"] is False
    assert constitution["identityAuthority"] == "salvaged-frontier"
    assert (
        constitution["readabilityDiscipline"]
        == "industrial-toy-defense"
    )
    assert constitution["precedenceContract"]["hybridizationForbidden"] is True
    assert decision["selectedTerritory"] == art["finalTerritory"]
    assert decision["selectedConstitutionSha256"] == sha256_file(
        constitution_path
    )
    assert decision["productionApproved"] is False


def test_selected_territory_matches_constitution_quantitative_grammar() -> None:
    constitution = load_json(
        ROOT / "art/selected/salvaged-frontier-constitution.json"
    )
    territory = load_json(
        ROOT / "art/territories/salvaged-frontier.json"
    )
    quantitative = constitution["quantitativeGrammar"]
    assert (
        territory["shapeLanguage"]["asymmetry"]
        == quantitative["globalAsymmetry"]
    )
    assert (
        territory["shapeLanguage"]["primarySecondarySizeRatio"]
        == quantitative["primarySecondarySizeRatio"]
    )
    assert {
        asset_id: recipe["asymmetryTarget"]
        for asset_id, recipe in territory["assetRecipes"].items()
    } == {
        asset_id: target
        for asset_id, target in quantitative[
            "assetAsymmetryTargets"
        ].items()
        if asset_id != "turret_fast_v1"
    }


def test_nonexistent_final_territory_is_rejected() -> None:
    art = load_json(ROOT / "art/art-direction.json")
    art["status"] = "CANDIDATE_SELECTED"
    art["finalTerritory"] = "territory-that-does-not-exist"
    errors = _schema_errors(art, "art-direction.schema.json")
    assert errors


def test_missing_creative_constraints_is_rejected() -> None:
    art = load_json(ROOT / "art/art-direction.json")
    del art["creativeConstraints"]
    errors = _schema_errors(art, "art-direction.schema.json")
    assert any("creativeConstraints" in error for error in errors)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("width", -100.0),
        ("height", 0.0),
        ("depth", 999999.0),
    ],
)
def test_invalid_calibration_dimensions_are_rejected(field: str, value: float) -> None:
    calibration = load_json(ROOT / "art/calibration/calibration-kit.json")
    calibration["assets"]["barricade"]["dimensions"][field] = value
    errors = _schema_errors(calibration, "calibration-kit.schema.json")
    if value <= 0:
        assert errors
    else:
        # An extreme positive value passes primitive schema constraints but must fail semantic texture-class limits.
        texture_class = calibration["assets"]["barricade"]["textureBudgetClass"]
        max_extent = calibration["textureClasses"][texture_class]["maxAssetExtentStuds"]
        assert value > max_extent


def test_negative_triangle_budget_is_rejected() -> None:
    calibration = load_json(ROOT / "art/calibration/calibration-kit.json")
    calibration["assets"]["barricade"]["triangleBudgetMax"] = -1
    assert _schema_errors(calibration, "calibration-kit.schema.json")


def test_screen_space_formula_round_trips() -> None:
    for pixels, distance, fov, height in [
        (3.0, 60.0, 70.0, 360),
        (3.0, 30.0, 70.0, 360),
        (2.0, 15.0, 70.0, 360),
        (4.0, 45.0, 55.0, 640),
    ]:
        thickness = required_thickness(pixels, distance, fov, height)
        assert projected_pixels(thickness, distance, fov, height) == pytest.approx(pixels, abs=1e-9)


def test_valid_blind_study_scores_but_never_auto_selects(tmp_path: Path) -> None:
    submissions_path, blind_map_path, _, _ = _valid_study(tmp_path)
    report = score(submissions_path, blind_map_path)
    assert report["status"] == "COMPLETE", report.get("issues")
    assert report["selectionAuthority"] == "HUMAN_ONLY"
    assert report["automaticSelection"] is None
    assert all(candidate["eligible"] for candidate in report["candidates"])


def test_invented_hard_gates_cannot_pass(tmp_path: Path) -> None:
    submissions_path, blind_map_path, submissions, blind_map = _valid_study(tmp_path)
    fixture_hash = sha256_file(ROOT / "tests/fixtures/mock-technical-evidence.json")
    for label in LABELS:
        submissions["technicalEvidenceByBlindLabel"][label] = {
            f"invented_gate_{i}": {
                "pass": True,
                "evidencePath": "tests/fixtures/mock-technical-evidence.json",
                "sha256": fixture_hash,
            }
            for i in range(9)
        }
    _rewrite_pair(submissions_path, blind_map_path, submissions, blind_map)
    report = score(submissions_path, blind_map_path)
    assert report["status"] == "BLOCKED"
    assert any("technical evidence IDs" in issue for issue in report["issues"])


def test_incomplete_task_matrix_is_blocked(tmp_path: Path) -> None:
    submissions_path, blind_map_path, submissions, blind_map = _valid_study(tmp_path)
    submissions["participants"][0]["responses"].pop()
    _rewrite_pair(submissions_path, blind_map_path, submissions, blind_map)
    report = score(submissions_path, blind_map_path)
    assert report["status"] == "BLOCKED"
    assert any("response matrix mismatch" in issue for issue in report["issues"])


def test_duplicate_participant_ids_are_blocked(tmp_path: Path) -> None:
    submissions_path, blind_map_path, submissions, blind_map = _valid_study(tmp_path)
    submissions["participants"][1]["participantId"] = submissions["participants"][0]["participantId"]
    _rewrite_pair(submissions_path, blind_map_path, submissions, blind_map)
    report = score(submissions_path, blind_map_path)
    assert report["status"] == "BLOCKED"
    assert "participantId values must be unique" in report["issues"]


def test_out_of_range_confidence_is_blocked_by_schema(tmp_path: Path) -> None:
    submissions_path, blind_map_path, submissions, blind_map = _valid_study(tmp_path)
    submissions["participants"][0]["responses"][0]["confidence"] = 1.1
    _rewrite_pair(submissions_path, blind_map_path, submissions, blind_map)
    report = score(submissions_path, blind_map_path)
    assert report["status"] == "BLOCKED"
    assert any("maximum of 1" in issue for issue in report["issues"])


def test_missing_or_tampered_evidence_is_blocked(tmp_path: Path) -> None:
    submissions_path, blind_map_path, submissions, blind_map = _valid_study(tmp_path)
    gate_id = next(iter(submissions["technicalEvidenceByBlindLabel"]["A"]))
    submissions["technicalEvidenceByBlindLabel"]["A"][gate_id]["sha256"] = "0" * 64
    _rewrite_pair(submissions_path, blind_map_path, submissions, blind_map)
    report = score(submissions_path, blind_map_path)
    assert report["status"] == "BLOCKED"
    assert any("SHA-256 mismatch" in issue for issue in report["issues"])


def test_evidence_path_cannot_escape_repository(tmp_path: Path) -> None:
    submissions_path, blind_map_path, submissions, blind_map = _valid_study(tmp_path)
    gate_id = next(iter(submissions["technicalEvidenceByBlindLabel"]["A"]))
    submissions["technicalEvidenceByBlindLabel"]["A"][gate_id]["evidencePath"] = "../outside.json"
    _rewrite_pair(submissions_path, blind_map_path, submissions, blind_map)
    report = score(submissions_path, blind_map_path)
    assert report["status"] == "BLOCKED"
    assert any("escapes the repository root" in issue for issue in report["issues"])


def test_blind_map_must_be_a_bijection(tmp_path: Path) -> None:
    submissions_path, blind_map_path, _, blind_map = _valid_study(tmp_path)
    blind_map["mapping"]["C"] = "industrial-toy-defense"
    _write_json(blind_map_path, blind_map)
    report = score(submissions_path, blind_map_path)
    assert report["status"] == "BLOCKED"
    assert any("bijection" in issue for issue in report["issues"])


def test_lighting_service_does_not_assign_protected_properties() -> None:
    source = (ROOT / "studio/src/LightingProfileService.luau").read_text(encoding="utf-8")
    assert "Lighting.LightingStyle =" not in source
    assert "Lighting.PrioritizeLightingQuality =" not in source
    assert "Protected property" in source
    lighting = load_json(ROOT / "art/lighting/lighting-profiles.json")
    protected = set(lighting["protectedPropertyPolicy"]["properties"])
    for profile in lighting["profiles"].values():
        assert not protected.intersection(profile["scriptMutable"].get("Lighting", {}))
        assert set(profile["studioManualPreconditions"]) == protected


def test_lighting_profiles_use_fresh_sequential_evidence() -> None:
    service = (ROOT / "studio/src/LightingProfileService.luau").read_text(encoding="utf-8")
    validator = (ROOT / "studio/src/GoldenSceneValidator.luau").read_text(encoding="utf-8")
    builder = (ROOT / "studio/src/GoldenSceneBuilder.luau").read_text(encoding="utf-8")
    assert "applyAndRecord" in service
    assert "collectEvidence" in service
    assert "SceneSessionId" in service
    assert "ProfilesDigest" in service
    assert "collectEvidence(scene, PROFILE_IDS, lightingProfiles)" in validator
    assert "verifyPreconditions(profileId, lightingProfiles)" not in validator
    assert "ArtSceneSessionId" in builder


def test_golden_scene_requires_30_and_100_copy_stress_gates() -> None:
    calibration = load_json(ROOT / "art/calibration/calibration-kit.json")
    assert calibration["goldenScene"]["stressCopyCounts"] == [30, 100]
    assert "stress_100" in calibration["goldenScene"]["zones"]
    builder = (ROOT / "studio/src/GoldenSceneBuilder.luau").read_text(encoding="utf-8")
    validator = (ROOT / "studio/src/GoldenSceneValidator.luau").read_text(encoding="utf-8")
    assert "Zone_Stress_{count}" in builder
    assert "ISOLATION_HEIGHT_STUDS = 2000" in builder
    assert "ArtSceneIsolationY" in builder
    assert "camera.CFrame += Vector3.new(0, ISOLATION_HEIGHT_STUDS, 0)" in builder
    assert "camera.CFrame.Position.Y > isolationY" in validator
    assert "Stress_barricade_100" in validator
    assert "Stress_enemy_standard_100" in validator


def test_render_benchmark_strips_fully_invisible_collision_proxies() -> None:
    builder = (ROOT / "studio/src/PerformanceBenchmarkBuilder.luau").read_text(
        encoding="utf-8"
    )
    assert "descendant.Transparency >= 1" in builder
    assert "descendant:Destroy()" in builder


def test_static_validation_binds_visual_quality_to_current_inputs_and_artifacts() -> None:
    validator = (ROOT / "tools/art/validate_library.py").read_text(encoding="utf-8")
    assert "visual-quality evidence input hashes are stale" in validator
    assert "visual-quality artifact hash drift" in validator
    measurer = (ROOT / "tools/art/measure_visual_quality.py").read_text(encoding="utf-8")
    assert "evidence/blender/visual-quality-artifacts" in measurer
    assert "shutil.copyfile(path, portable_path)" in measurer
    assert "shutil.rmtree(PORTABLE_ARTIFACT_ROOT)" in measurer


def test_release_manifest_excludes_validation_reports_regenerated_after_install() -> None:
    manifest_builder = (ROOT / "tools/art/build_package_manifest.py").read_text(
        encoding="utf-8"
    )
    assert "VOLATILE_EVIDENCE_FILES" in manifest_builder
    assert "evidence/static-validation-report.json" in manifest_builder
    assert "evidence/static-verification-report.json" in manifest_builder


def test_installer_preserves_local_human_evidence_on_replace() -> None:
    installer = (ROOT / "scripts/install-workflow.ps1").read_text(
        encoding="utf-8"
    )
    assert "$ExistingHumanEvidence" in installer
    assert "$StagedHumanEvidence" in installer
    assert "localHumanEvidencePreserved" in installer


def test_blender_compiler_probes_engine_and_validates_vertical_fov() -> None:
    source = (ROOT / "tools/blender/build_art_direction.py").read_text(encoding="utf-8")
    assert 'for candidate in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH")' in source
    assert 'scene.render.engine = "BLENDER_EEVEE_NEXT"' not in source
    assert 'data.sensor_fit = "VERTICAL"' in source
    assert "camera.data.angle_y" in source
    assert "validate_variant" in source
    assert "non-manifold edges" in source


def test_runners_force_blender_python_failure_to_nonzero() -> None:
    ps1 = (ROOT / "scripts/art-direction.ps1").read_text(encoding="utf-8")
    shell = (ROOT / "scripts/art-direction.sh").read_text(encoding="utf-8")
    for source in (ps1, shell):
        assert "--python-exit-code" in source
        assert "19" in source


def test_windows_runner_exposes_every_referenced_gate_switch() -> None:
    source = (ROOT / "scripts/art-direction.ps1").read_text(encoding="utf-8")
    assert "[switch]$RequirePass" in source
    assert "[switch]$RequireEligible" in source


def test_windows_runner_routes_r3d_doctor_from_project_root() -> None:
    source = (ROOT / "scripts/art-direction.ps1").read_text(encoding="utf-8")
    assert "$candidate = Join-Path $ProjectRoot 'scripts/r3d.ps1'" in source
    assert "& $candidate doctor --repo $ProjectRoot" in source
    assert "$candidate = Join-Path (Split-Path $Root -Parent) 'scripts/r3d.ps1'" not in source


def test_workbench_smoke_skips_full_only_studio_import_queue() -> None:
    source = (ROOT / "scripts/art-direction.ps1").read_text(encoding="utf-8")
    workbench = source[source.index("        'workbench' {") : source.index("        'verify-blender' {")]
    assert "if ($RenderMode -eq 'full')" in workbench
    assert "tools.art.build_studio_import_queue" in workbench
    assert "[SKIP] Studio import queue requires RenderMode=full." in workbench


def test_report_commands_resolve_repository_relative_paths() -> None:
    source = (ROOT / "scripts/art-direction.ps1").read_text(encoding="utf-8")
    assert source.count("$reportPath = Resolve-WorkflowPath $Report") == 4
    for module in (
        "tools.art.validate_studio_report",
        "tools.art.bind_studio_captures",
        "tools.art.validate_performance_report",
        "tools.art.validate_studio_simulator_report",
    ):
        assert f"'{module}', $reportPath" in source


def test_studio_capture_binder_requires_all_four_profiles() -> None:
    source = (ROOT / "tools/art/bind_studio_captures.py").read_text(encoding="utf-8")
    for profile_id in (
        "Lighting_Gameplay_Default",
        "Lighting_HighContrast",
        "Lighting_Adverse_Night",
        "Lighting_Neutral_QA",
    ):
        assert profile_id in source
    assert '"sha256": sha256_file(capture)' in source


def test_reference_boards_do_not_embed_unlicensed_binaries() -> None:
    provenance = load_json(ROOT / "art/references/provenance.json")
    assert len(provenance["references"]) >= 36
    for reference in provenance["references"]:
        if reference["embeddedInRepository"]:
            assert reference["licenseStatus"] in {"public_domain", "cc0"}


def test_every_object_schema_is_closed_or_explicitly_patterned() -> None:
    gaps: list[str] = []

    def walk(value: object, path: str, schema_name: str) -> None:
        if isinstance(value, dict):
            if value.get("type") == "object" and not any(
                key in value for key in ("unevaluatedProperties", "additionalProperties", "maxProperties")
            ):
                gaps.append(f"{schema_name}:{path}")
            for key, child in value.items():
                walk(child, f"{path}/{key}", schema_name)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}/{index}", schema_name)

    for schema_path in sorted((ROOT / "schemas").glob("*.schema.json")):
        walk(load_json(schema_path), "$", schema_path.name)
    assert gaps == []


def test_external_evidence_templates_are_schema_valid_but_blocked() -> None:
    studio_path = ROOT / "art/qa/templates/studio-report.template.json"
    mobile_path = ROOT / "art/qa/templates/performance-report.template.json"
    simulator_path = ROOT / "art/qa/templates/studio-simulator-report.template.json"
    assert _schema_errors(load_json(studio_path), "studio-report.schema.json") == []
    assert _schema_errors(load_json(mobile_path), "performance-report.schema.json") == []
    assert _schema_errors(load_json(simulator_path), "studio-simulator-report.schema.json") == []
    assert validate_studio_report(studio_path)["reportedStatus"] == "BLOCKED"
    assert validate_performance_report(mobile_path)["reportedStatus"] == "BLOCKED"
    assert validate_studio_simulator_report(simulator_path)["reportedStatus"] == "BLOCKED"


def test_repository_skill_is_valid_concise_and_self_contained() -> None:
    skill = ROOT / ".agents/skills/roblox-3d-asset"
    skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
    assert len(skill_text.splitlines()) < 500
    assert skill_text.startswith("---\n")
    _, frontmatter_text, body = skill_text.split("---", 2)
    frontmatter = yaml.safe_load(frontmatter_text)
    assert set(frontmatter) == {"name", "description"}
    assert frontmatter["name"] == skill.name
    assert "Roblox 3D" in frontmatter["description"]
    assert body.strip()

    metadata = yaml.safe_load((skill / "agents/openai.yaml").read_text(encoding="utf-8"))
    interface = metadata["interface"]
    assert 25 <= len(interface["short_description"]) <= 64
    assert "$roblox-3d-asset" in interface["default_prompt"]

    for reference in (
        "evidence-and-gates.md",
        "execution-routing.md",
        "studio-mobile-human.md",
        "platform-facts.md",
    ):
        assert (skill / "references" / reference).is_file()
        assert reference in skill_text
    forbidden = {"README.md", "INSTALLATION_GUIDE.md", "QUICK_REFERENCE.md", "CHANGELOG.md"}
    assert not forbidden.intersection(path.name for path in skill.rglob("*") if path.is_file())


def test_installer_is_staged_hash_verified_and_non_destructive() -> None:
    source = (ROOT / "scripts/install-workflow.ps1").read_text(encoding="utf-8")
    assert "PACKAGE_MANIFEST.json" in source
    assert "Get-FileHash" in source
    assert "Bootstrap staged workflow" in source
    assert "Validate staged workflow" in source
    assert "Test staged workflow" in source
    assert ".agents/skills/roblox-3d-asset" in source
    assert "scripts/art-direction.ps1" in source
    assert "tools/roblox-3d-asset" in source
    assert "assets-3d/defense-barricade-small/asset.json" in source
    assert "-Replace" in source
    assert "Move-Item" in source
    assert "Remove-Item -Recurse" not in source


def test_simulator_evidence_is_not_physical_device_evidence() -> None:
    report_path = ROOT / "evidence/mobile/studio-simulator/report.json"
    result = validate_studio_simulator_report(report_path)
    assert result["status"] == "PASS"
    assert result["reportedStatus"] == "PARTIAL"
    physical = validate_performance_report(report_path)
    assert physical["status"] == "INVALID"


def test_blocked_simulator_template_cannot_be_relabelled_pass(tmp_path: Path) -> None:
    report = load_json(ROOT / "art/qa/templates/studio-simulator-report.template.json")
    report["status"] = "PASS"
    report["issues"] = []
    path = tmp_path / "studio-simulator-report.json"
    _write_json(path, report)
    result = validate_studio_simulator_report(path, require_pass=True)
    assert result["status"] in {"INVALID", "FAIL"}


def test_blocked_studio_template_cannot_be_relabelled_pass() -> None:
    report = load_json(ROOT / "art/qa/templates/studio-report.template.json")
    report["status"] = "PASS"
    report["issues"] = []
    errors = _schema_errors(report, "studio-report.schema.json")
    assert errors


def test_studio_validator_requires_real_place_for_pass(tmp_path: Path) -> None:
    report = load_json(ROOT / "art/qa/templates/studio-report.template.json")
    report["status"] = "FAIL"
    report["issues"] = ["real Studio execution failed"]
    path = tmp_path / "studio-report.json"
    _write_json(path, report)
    result = validate_studio_report(path, require_pass=True)
    assert result["status"] == "FAIL"
    assert any("PASS required" in issue for issue in result["issues"])


def test_mobile_template_cannot_be_relabelled_pass(tmp_path: Path) -> None:
    report = load_json(ROOT / "art/qa/templates/performance-report.template.json")
    report["status"] = "PASS"
    report["issues"] = []
    report["device"].update(
        {
            "deviceIdHash": "1" * 64,
            "manufacturer": "Test",
            "model": "Device",
            "osName": "OS",
            "osVersion": "1",
            "chipset": "Chip",
        }
    )
    report["graybox"]["frameTimeMs"] = {"median": 12, "p95": 15, "p99": 18, "mad": 1, "max": 24}
    report["candidate"]["frameTimeMs"] = {"median": 12.6, "p95": 16, "p99": 19, "mad": 1, "max": 25}
    report["graybox"]["fps"] = {"median": 60, "minimum": 45}
    report["candidate"]["fps"] = {"median": 58, "minimum": 43}
    report["graybox"]["memoryMb"] = {"median": 500, "p95": 520, "max": 540, "byCategory": {}}
    report["candidate"]["memoryMb"] = {"median": 510, "p95": 535, "max": 550, "byCategory": {}}
    report["regressions"].update(
        {
            "frameTimeMedianPct": 5.0,
            "frameTimeP95Pct": (16 / 15 - 1) * 100,
            "memoryP95Mb": 15,
            "minimumFpsDelta": -2,
            "pass": True,
        }
    )
    report["visualChecks"] = {key: True for key in report["visualChecks"]}
    path = tmp_path / "performance-report.json"
    _write_json(path, report)
    result = validate_performance_report(path, require_pass=True)
    assert result["status"] == "FAIL"
    assert any("artifact kinds" in issue or "MicroProfiler" in issue for issue in result["issues"])


def test_mobile_regression_math_cannot_be_falsified(tmp_path: Path) -> None:
    report = load_json(ROOT / "art/qa/templates/performance-report.template.json")
    report["status"] = "FAIL"
    report["graybox"]["frameTimeMs"] = {"median": 10, "p95": 12, "p99": 14, "mad": 1, "max": 18}
    report["candidate"]["frameTimeMs"] = {"median": 15, "p95": 18, "p99": 20, "mad": 1, "max": 22}
    report["graybox"]["fps"] = {"median": 60, "minimum": 50}
    report["candidate"]["fps"] = {"median": 40, "minimum": 30}
    report["graybox"]["memoryMb"] = {"median": 400, "p95": 450, "max": 480, "byCategory": {}}
    report["candidate"]["memoryMb"] = {"median": 500, "p95": 600, "max": 620, "byCategory": {}}
    report["regressions"].update(
        {
            "frameTimeMedianPct": 0,
            "frameTimeP95Pct": 0,
            "memoryP95Mb": 0,
            "minimumFpsDelta": 0,
            "pass": True,
        }
    )
    path = tmp_path / "performance-report.json"
    _write_json(path, report)
    result = validate_performance_report(path)
    assert result["status"] == "FAIL"
    assert any("mismatch" in issue for issue in result["issues"])


def test_studio_staging_and_reuse_require_source_hash_identity() -> None:
    stager = (ROOT / "studio/src/AssetKitStager.luau").read_text(encoding="utf-8")
    validator = (ROOT / "studio/src/GoldenSceneValidator.luau").read_text(encoding="utf-8")
    assert "ArtSourceSha256" in stager
    assert "ArtSourceSha256" in validator
    assert "sourceSha256Count ~= 1" in validator
    assert "has no MeshPart identity" in validator
    assert "ArtMaterialRole" in stager
    assert "CollisionHitbox" in stager
    assert "rawPlaceIdIncluded = false" in validator
    assert "placeId = if game.PlaceId" not in validator
    assert "environmentChecks = environmentChecks()" in validator
    assert "TerritoryStyles" in (ROOT / "studio/plugin/ArtDirectionGoldenScene.plugin.luau").read_text(encoding="utf-8")


def test_semantic_material_roles_drive_blender_and_studio() -> None:
    rules = load_json(ROOT / "art/materials/material-rules.json")
    profiles = rules["semanticRoleProfiles"]
    assert set(profiles) == {
        "primary",
        "secondary",
        "accent",
        "interaction",
        "threat",
        "warning",
        "critical",
        "rubber",
        "bareMetal",
    }
    for territory_id in TERRITORIES:
        territory = load_json(ROOT / f"art/territories/{territory_id}.json")
        palette = territory["blockoutPalette"]
        assert set(palette) == set(profiles)
        assert set(territory["surfaceAssignments"]) == set(profiles)
        assert set(territory["surfaceAssignments"].values()).issubset(rules["materials"])
    compiler = (ROOT / "tools/blender/build_art_direction.py").read_text(encoding="utf-8")
    assert 'ctx.material_rules["semanticRoleProfiles"]' in compiler
    assert 'ctx.territory["surfaceAssignments"]' in compiler
    assert 'joined.name = f"ROLE_{role}"' in compiler


def test_authored_hex_colors_are_converted_from_srgb_to_scene_linear() -> None:
    assert srgb_to_linear(0.0) == 0.0
    assert srgb_to_linear(1.0) == 1.0
    assert srgb_to_linear(0.5) == pytest.approx(0.21404114048223255)
    rgba = hex_to_linear_rgba("#354052")
    assert rgba[:3] == pytest.approx((0.03560131487502034, 0.05126945837404324, 0.08437621154414882))
    assert rgba[3] == 1.0
    with pytest.raises(ValueError):
        hex_to_linear_rgba("not-a-color")


def test_visual_mask_metrics_detect_clipping_and_structural_change() -> None:
    first = np.zeros((8, 8), dtype=bool)
    first[2:6, 2:6] = True
    second = first.copy()
    second[1, 3:5] = True
    metrics = mask_metrics(first)
    assert metrics["maskAreaRatio"] == pytest.approx(0.25)
    assert metrics["frameContactPixels"] == 0
    iou, difference = compare_masks(first, second)
    assert iou == pytest.approx(16 / 18)
    assert difference == pytest.approx(2 / 18)
    second[0, 0] = True
    assert mask_metrics(second)["frameContactPixels"] == 1


def test_asset_state_applicability_is_not_a_global_cartesian_product() -> None:
    calibration = load_json(ROOT / "art/calibration/calibration-kit.json")
    observed = {
        asset_id: asset["requiredStateVariants"]
        for asset_id, asset in calibration["assets"].items()
    }
    assert observed == {
        "barricade": ["intact", "damaged", "critical"],
        "objective_core": ["intact", "damaged", "critical"],
        "enemy_standard": ["intact", "damaged", "critical"],
        "floor_module": ["intact", "damaged"],
        "damage_effect": ["damaged", "critical"],
    }


def test_render_counts_expand_only_applicable_pairs() -> None:
    calibration = load_json(ROOT / "art/calibration/calibration-kit.json")
    matrix = load_json(ROOT / "art/calibration/render-matrix.json")
    for mode in matrix["modes"].values():
        observed = 0
        for job in mode["jobs"]:
            pairs = sum(
                state_id in calibration["assets"][asset_id]["requiredStateVariants"]
                for asset_id in job["assetIds"]
                for state_id in job["stateIds"]
            )
            multiplier = 1
            for axis in ("cameraIds", "lightingProfileIds", "backgroundIds", "resolutionIds", "passIds"):
                multiplier *= len(job[axis])
            observed += pairs * multiplier
        assert observed == mode["expectedRenderCount"]


def test_recipe_fields_are_closed_and_every_strategy_is_compiler_consumed() -> None:
    assert EXECUTABLE_RECIPE_FIELDS.isdisjoint(VALIDATION_TARGET_RECIPE_FIELDS)
    compiler = (ROOT / "tools/blender/build_art_direction.py").read_text(encoding="utf-8")
    assert 'recipe["bevelRatioTarget"]' in compiler
    assert '["stateBreakStrategy"]' in compiler
    for territory_id in TERRITORIES:
        territory = load_json(ROOT / f"art/territories/{territory_id}.json")
        for recipe in territory["assetRecipes"].values():
            assert set(recipe) == declared_recipe_fields()
            assert recipe["stateBreakStrategy"] in STATE_STRATEGY_PROFILES


def test_windows_runner_is_powershell_51_compatible_and_bootstraps_locally() -> None:
    source = (ROOT / "scripts/art-direction.ps1").read_text(encoding="utf-8")
    assert "$IsWindows)" not in source
    assert "$IsMacOS)" not in source
    assert "$env:OS -eq 'Windows_NT'" in source
    assert ".venv\\Scripts\\python.exe" in source
    assert "tools.art.check_dependencies" in source
    assert "$exitCode = $LASTEXITCODE" in source


def test_dependency_contract_is_fully_pinned() -> None:
    lines = [
        line.strip()
        for line in (ROOT / "requirements-dev.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert len(lines) >= 10
    assert all(line.count("==") == 1 for line in lines)


def test_blender_delivery_artifacts_are_canonicalized_before_hashing() -> None:
    source = (ROOT / "tools/blender/build_art_direction.py").read_text(encoding="utf-8")
    export_position = source.index("bpy.ops.export_scene.gltf")
    canonical_position = source.index("canonicalize_glb(path)")
    hash_position = source.index('"sha256": sha256_file(path)', canonical_position)
    assert export_position < canonical_position < hash_position


def test_studio_import_queue_is_complete_when_present() -> None:
    path = ROOT / "build/studio-import/manifest.json"
    if not path.is_file():
        return
    manifest = load_json(path)
    assert manifest["status"] == "PASS"
    assert manifest["assetCount"] == 39
    assert len(manifest["entries"]) == 39
    assert len({item["uploadName"] for item in manifest["entries"]}) == 39
    generator_hash = sha256_file(ROOT / "tools/blender/build_art_direction.py")
    assert manifest["generatorSha256"] == generator_hash
    for item in manifest["entries"]:
        artifact = ROOT / item["path"]
        assert artifact.is_file()
        assert sha256_file(artifact) == item["sha256"]
        assert item["meshCount"] == len(item["materialRoles"])


def test_studio_import_queue_rejects_generic_glb_scene_names() -> None:
    compiler = (ROOT / "tools/blender/build_art_direction.py").read_text(encoding="utf-8")
    queue = (ROOT / "tools/art/build_studio_import_queue.py").read_text(encoding="utf-8")
    assert "scene.name = upload_name" in compiler
    assert "source_scene_name != upload_name" in queue


def test_blender_verification_report_is_current_or_explicitly_absent() -> None:
    path = ROOT / "evidence/blender/blender-verification-report.json"
    if not path.is_file():
        status = load_json(ROOT / "STATUS.json")
        assert status["truthModel"]["blenderEvidenceTier"] in {"NONE", "BUILD_ONLY"}
        assert (ROOT / "evidence/blender/baseline-v3/blender-verification-report.json").is_file()
        return
    report = load_json(path)
    assert _schema_errors(report, "blender-verification-report.schema.json") == []
    assert report["status"] == "PASS"
    assert report["inputHashes"]["generator"] == sha256_file(
        ROOT / "tools/blender/build_art_direction.py"
    )
    assert {item["territoryId"] for item in report["territories"]} == set(TERRITORIES)
    assert all(len(item["exportSha256"]) == 13 for item in report["territories"])


def test_smoke_evidence_is_current_or_explicitly_absent() -> None:
    path = ROOT / "evidence/blender/smoke-evidence.json"
    if not path.is_file():
        status = load_json(ROOT / "STATUS.json")
        tier = status["truthModel"]["blenderEvidenceTier"]
        assert tier in {"NONE", "BUILD_ONLY", "FULL_COMPLETE"}
        if tier == "FULL_COMPLETE":
            full = load_json(ROOT / "evidence/blender/full-evidence.json")
            generator_hash = sha256_file(ROOT / "tools/blender/build_art_direction.py")
            assert {item["inputHashes"]["generator"] for item in full["territories"]} == {
                generator_hash
            }
        assert (ROOT / "evidence/blender/baseline-v3/smoke-evidence.json").is_file()
        return
    report = load_json(path)
    assert _schema_errors(report, "smoke-evidence.schema.json") == []
    assert report["status"] == "PASS"
    assert report["totalExpectedRenderCount"] == 324
    assert report["totalActualRenderCount"] == 324
    assert report["totalStressRenderCount"] == 6
    assert report["artifactsBundled"] is False
    assert {item["territoryId"] for item in report["territories"]} == set(TERRITORIES)
    generator_hash = sha256_file(ROOT / "tools/blender/build_art_direction.py")
    assert {item["inputHashes"]["generator"] for item in report["territories"]} == {generator_hash}


def test_full_evidence_is_complete_and_bound_to_current_generator() -> None:
    path = ROOT / "evidence/blender/full-evidence.json"
    if not path.is_file():
        status = load_json(ROOT / "STATUS.json")
        assert status["truthModel"]["blenderEvidenceTier"] in {
            "NONE",
            "BUILD_ONLY",
        }
        return
    report = load_json(path)
    assert _schema_errors(report, "full-evidence.schema.json") == []
    assert report["status"] == "PASS"
    assert report["evidenceTier"] == "FULL_COMPLETE"
    expected_total = load_json(ROOT / "art/calibration/render-matrix.json")["modes"]["full"][
        "expectedRenderCount"
    ] * len(TERRITORIES)
    assert report["totalExpectedRenderCount"] == expected_total
    assert report["totalActualRenderCount"] == expected_total
    assert report["totalStressRenderCount"] == 6
    generator_hash = sha256_file(ROOT / "tools/blender/build_art_direction.py")
    assert {item["inputHashes"]["generator"] for item in report["territories"]} == {generator_hash}


def test_visual_quality_report_is_current_and_machine_validated() -> None:
    path = ROOT / "evidence/blender/visual-quality-report.json"
    if not path.is_file():
        status = load_json(ROOT / "STATUS.json")
        assert status["truthModel"]["blenderEvidenceTier"] in {
            "NONE",
            "BUILD_ONLY",
        }
        return
    report = load_json(path)
    assert _schema_errors(report, "visual-quality-report.schema.json") == []
    assert report["status"] == "PASS"
    assert report["issues"] == []
    assert report["inputHashes"] == {
        "generator": sha256_file(ROOT / "tools/blender/build_art_direction.py"),
        "renderMatrix": sha256_file(ROOT / "art/calibration/render-matrix.json"),
    }
    assert all(comparison["pass"] for territory in report["territories"] for comparison in territory["stateComparisons"])
    assert all(ordering["pass"] for territory in report["territories"] for ordering in territory["severityOrdering"])
    assert all(comparison["pass"] for comparison in report["crossTerritoryComparisons"])


def test_provenance_human_approval_cannot_be_implicit() -> None:
    provenance = load_json(ROOT / "art/references/provenance.json")
    assert provenance["humanApproval"]["status"] == "PENDING"
    source = (ROOT / "tools/art/lock_direction.py").read_text(encoding="utf-8")
    assert 'approval.get("status") != "APPROVED"' in source
    assert "validate_transfer_report" in source
    assert "require_approved=True" in source
    assert 'transfer_review.get("status") != "APPROVED"' in source
    assert "sixthAssetEvidencePackageSha256" in source
    assert "creative-direction-decision.schema.json" in source
    assert "FOUNDER_STRATEGIC_SELECTION" in source
    assert "check_all(require_locked=True)" in source
    assert "selectedConstitutionSha256" in source


def test_production_canon_gate_targets_only_selected_territory() -> None:
    from tools.art.build_visual_canons import check_all

    issues = check_all(require_locked=True)
    gate_issue = next(
        issue
        for issue in issues
        if issue.startswith("production requires LOCKED + COMPLETE + APPROVED canons:")
    )
    assert "salvaged-frontier" in gate_issue
    assert "industrial-toy-defense" not in gate_issue
    assert "clean-tactical-diorama" not in gate_issue


def test_generated_luau_quotes_reserved_object_keys() -> None:
    rendered = to_luau({"function": "value", "local": 1, "safeIdentifier": True})
    assert '["function"] = "value"' in rendered
    assert '["local"] = 1' in rendered
    assert "safeIdentifier = true" in rendered


def test_sixth_asset_contract_is_closed_and_not_in_calibration() -> None:
    transfer = load_json(ROOT / "art/transfer/turret-fast-v1.json")
    calibration = load_json(ROOT / "art/calibration/calibration-kit.json")
    shape = load_json(ROOT / "art/shape-language/rules.json")
    materials = load_json(ROOT / "art/materials/material-rules.json")
    assert _schema_errors(transfer, "transfer-asset.schema.json") == []
    assert transfer["assetId"] == "turret_fast_v1"
    assert transfer["assetId"] not in calibration["assets"]
    assert set(transfer["grammarClosure"]["primaryShapes"]) == set(
        shape["functionFamilies"]["defense"]["primary"]
    )
    assert set(transfer["grammarClosure"]["secondaryShapes"]) == set(
        shape["functionFamilies"]["defense"]["secondary"]
    ) | {"socket"}
    assert set(transfer["grammarClosure"]["paletteRoles"]).issubset(
        materials["semanticRoleProfiles"]
    )
    assert "threat" not in transfer["grammarClosure"]["paletteRoles"]
    assert all(
        transfer["grammarClosure"][field] is True
        for field in (
            "noNewPaletteRole",
            "noNewMaterialClass",
            "noNewAngleFamily",
            "noNewBevelFamily",
            "noNewDamageLanguage",
        )
    )


def test_transfer_compiler_reuses_proven_base_and_keeps_paths_short() -> None:
    source = (ROOT / "tools/blender/build_transfer_asset.py").read_text(
        encoding="utf-8"
    )
    assert "from tools.blender import build_art_direction as base" in source
    assert "base.ensure_materials(ctx)" in source
    assert "base.validate_variant(variant, ctx.calibration)" in source
    assert "base.export_variant(ctx" in source
    assert "base.canonicalize_glb" not in source
    assert 'Path("renders") / (' in source
    assert "ctx.territory['territoryId']}__{ASSET_ID}" not in source
    calibration_compiler = (
        ROOT / "tools/blender/build_art_direction.py"
    ).read_text(encoding="utf-8")
    assert "turret_fast_v1" not in calibration_compiler


def test_transfer_runner_exposes_one_command_and_human_strict_mode() -> None:
    source = (ROOT / "scripts/art-direction.ps1").read_text(encoding="utf-8")
    assert "'transfer'" in source
    assert "'validate-transfer'" in source
    assert "tools.art.build_transfer_proof" in source
    assert "tools.art.validate_transfer_report" in source
    assert "if ($RequirePass) { $args += '--require-approved' }" in source
    assert "turret-fast-v1-review.json" in source
    static = (ROOT / "tools/art/verify_static.py").read_text(encoding="utf-8")
    assert '"transfer_evidence_integrity"' in static
    assert '"runner_powershell_syntax"' in static


def test_transfer_review_cannot_approve_with_low_scores() -> None:
    review = load_json(ROOT / "art/transfer/turret-fast-v1-review.json")
    approved = copy.deepcopy(review)
    approved.update(
        {
            "status": "APPROVED",
            "selectedTerritory": "industrial-toy-defense",
            "reviewer": "Founder",
            "reviewedAt": "2026-07-16T10:00:00Z",
            "evidencePackageSha256": "a" * 64,
            "decision": "APPROVE_TRANSFER",
            "scores": {
                "functionReadability": 20,
                "territoryFidelity": 20,
                "stateReadability": 20,
                "mobileReadability": 20,
                "productionAppeal": 15,
            },
            "scoreTotal": 95,
            "rationale": "The evidence is complete but production appeal remains below the approval threshold.",
        }
    )
    errors = _schema_errors(approved, "transfer-review.schema.json")
    assert any("less than the minimum of 16" in error for error in errors)


def test_transfer_report_is_current_portable_and_automated_pass() -> None:
    path = ROOT / "evidence/transfer/turret-fast-v1/report.json"
    report = load_json(path)
    assert _schema_errors(report, "transfer-report.schema.json") == []
    result = validate_transfer_report(path)
    assert result["status"] == "PASS"
    assert result["reportedStatus"] == "PARTIAL"
    assert report["automatedStatus"] == "PASS"
    assert report["automatedScore"] == 100
    assert report["overallStatus"] == "PARTIAL"
    assert report["humanReview"]["status"] == "PENDING"
    assert len(report["territories"]) == 3
    assert all(len(item["portableArtifacts"]) == 17 for item in report["territories"])
    assert all(item["determinism"]["status"] == "PASS" for item in report["territories"])
    assert all(item["status"] == "PASS" for item in report["territories"])
    assert all(item["pass"] for item in report["crossTerritoryComparisons"])
    assert report["inputHashes"]["generator"] == sha256_file(
        ROOT / "tools/blender/build_transfer_asset.py"
    )
    assert report["inputHashes"]["proofBuilder"] == sha256_file(
        ROOT / "tools/art/build_transfer_proof.py"
    )


def test_transfer_report_rejects_tampered_portable_hash(tmp_path: Path) -> None:
    report = load_json(ROOT / "evidence/transfer/turret-fast-v1/report.json")
    report["territories"][0]["portableArtifacts"][0]["sha256"] = "0" * 64
    path = tmp_path / "tampered-transfer-report.json"
    _write_json(path, report)
    result = validate_transfer_report(path)
    assert result["status"] == "FAIL"
    assert any("SHA-256 drift" in issue for issue in result["issues"])


def test_transfer_studio_import_queue_is_complete_when_present() -> None:
    source = (ROOT / "tools/art/build_transfer_import_queue.py").read_text(
        encoding="utf-8"
    )
    assert "read_glb_scene_name" in source
    assert "exactly nine unique GLBs" in source
    path = ROOT / "build/studio-import-transfer/manifest.json"
    if not path.is_file():
        return
    manifest = load_json(path)
    assert _schema_errors(
        manifest, "transfer-import-queue.schema.json"
    ) == []
    assert manifest["status"] == "PASS"
    assert manifest["assetCount"] == 9
    assert len(manifest["entries"]) == 9
    assert len({item["uploadName"] for item in manifest["entries"]}) == 9
    for item in manifest["entries"]:
        queued = ROOT / item["path"]
        source_path = ROOT / item["sourcePath"]
        assert queued.is_file()
        assert source_path.is_file()
        assert sha256_file(queued) == item["sha256"]
        assert sha256_file(source_path) == item["sha256"]
