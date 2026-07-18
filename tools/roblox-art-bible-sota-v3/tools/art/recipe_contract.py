from __future__ import annotations

from typing import Final

EXECUTABLE_RECIPE_FIELDS: Final = {
    "assetId",
    "bevelRatioTarget",
    "stateBreakStrategy",
}

VALIDATION_TARGET_RECIPE_FIELDS: Final = {
    "primaryPrimitives",
    "secondaryPrimitives",
    "asymmetryTarget",
    "moduleCountTarget",
    "detailBandTargets",
}

# The strings are deliberately closed. A territory cannot silently invent a
# state strategy that the Blender compiler ignores.
STATE_STRATEGY_PROFILES: Final = {
    "one_panel_displaces_then_center_splits": {"targets": ("Panel", "TopRail"), "axis": "Z"},
    "outer_ring_opens_then_core_exposes": {"targets": ("Ring", "Core"), "axis": "X"},
    "one_shoulder_drops_then_chest_core_exposes": {"targets": ("Hand", "Torso"), "axis": "Y"},
    "bloom_side_shoulder_drops_then_same_knee_buckles": {
        "targets": ("ShamblingArm", "StaggerLeg"),
        "axis": "Y",
    },
    "one_edge_key_breaks_then_inset_cracks": {"targets": ("Key", "Inset"), "axis": "Z"},
    "wedge_widens_and_ring_breaks": {"targets": ("ImpactRing", "ImpactWedge"), "axis": "Y"},
    "repaired_panel_fails_then_central_beam_bends": {"targets": ("RecoveredPanel", "CentralBeam"), "axis": "Z"},
    "service_box_opens_then_core_shield_tears": {"targets": ("ServiceBox", "Core"), "axis": "X"},
    "repair_side_collapses_then_torso_opens": {"targets": ("RepairedArm", "LeaningTorso"), "axis": "Y"},
    "bloom_side_collapses_then_same_fracture_widens_and_knee_buckles": {
        "targets": ("FrontierBloom", "HunchedBody", "StaggerLeg"),
        "axis": "Y",
    },
    "replacement_quadrant_lifts_then_plate_splits": {"targets": ("ReplacementQuadrant", "SalvagedPlate"), "axis": "X"},
    "arc_frays_toward_failed_repair": {"targets": ("RerouteArc", "AsymmetricArcMass"), "axis": "Y"},
    "one_clean_notch_then_center_plane_divides": {"targets": ("CenterPlate", "Support"), "axis": "Z"},
    "outer_ring_segments_switch_off_then_core_aperture_opens": {"targets": ("ConcentricRing", "Core"), "axis": "X"},
    "one_semantic_panel_detaches_then_center_wedge_opens": {"targets": ("PairedHand", "ForwardWedgeTorso"), "axis": "Y"},
    "one_shoulder_drops_then_same_bloom_break_widens": {
        "targets": ("ShamblingArm", "FrontierBloom"),
        "axis": "Y",
    },
    "one_quadrant_dims_then_center_hex_splits": {"targets": ("CenterHex", "Tile"), "axis": "Z"},
    "ring_segments_reduce_from_four_to_two": {"targets": ("CleanImpactRing", "CleanDirectionCone"), "axis": "Y"},
}


def declared_recipe_fields() -> set[str]:
    return EXECUTABLE_RECIPE_FIELDS | VALIDATION_TARGET_RECIPE_FIELDS
