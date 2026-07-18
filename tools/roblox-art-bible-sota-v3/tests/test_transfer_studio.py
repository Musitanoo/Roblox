from __future__ import annotations

from tools.art.common import ROOT, load_json
from tools.art.stage_transfer_studio import (
    MANIFEST_PATH,
    _normalize_lua_json,
    _payload_entries,
    _studio_styles,
    glb_bounds,
    stage,
)


def test_all_transfer_glbs_have_finite_positive_bounds() -> None:
    manifest = load_json(MANIFEST_PATH)
    for entry in manifest["entries"]:
        bounds = glb_bounds(ROOT / entry["path"])
        assert len(bounds) == 3
        assert all(value > 0 for value in bounds)


def test_transfer_studio_payload_is_closed_to_nine_entries() -> None:
    manifest = load_json(MANIFEST_PATH)
    entries = _payload_entries(manifest)
    assert len(entries) == 9
    assert len({entry["uploadName"] for entry in entries}) == 9
    assert {entry["territoryId"] for entry in entries} == {
        "industrial-toy-defense",
        "salvaged-frontier",
        "clean-tactical-diorama",
    }
    assert all(
        {
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
        == set(entry["styles"])
        for entry in entries
    )


def test_studio_styles_preserve_territory_palette_and_material_roles() -> None:
    industrial = _studio_styles("industrial-toy-defense")
    salvaged = _studio_styles("salvaged-frontier")
    clean = _studio_styles("clean-tactical-diorama")

    assert industrial["primary"]["color"] == [
        0x35 / 255,
        0x40 / 255,
        0x52 / 255,
    ]
    assert industrial["interaction"]["material"] == "Neon"
    assert industrial["interaction"]["castShadow"] is False
    assert salvaged["secondary"]["material"] == "SmoothPlastic"
    assert clean["secondary"]["material"] == "Concrete"
    assert all(
        styles["bareMetal"]["material"] == "Metal"
        for styles in (industrial, salvaged, clean)
    )


def test_transfer_studio_dry_run_never_opens_mcp() -> None:
    result = stage(dry_run=True, apply=False, capture=False)
    assert result["status"] == "PARTIAL"
    assert result["mutationPerformed"] is False
    assert result["candidateCount"] == 9


def test_luau_numeric_json_objects_normalize_to_lists() -> None:
    assert _normalize_lua_json(
        {
            "1": {"bounds": {"1": 4.8, "2": 5.4, "3": 5.2}},
            "2": {"bounds": {"1": 4.0, "2": 5.0, "3": 4.5}},
        }
    ) == [
        {"bounds": [4.8, 5.4, 5.2]},
        {"bounds": [4.0, 5.0, 4.5]},
    ]
