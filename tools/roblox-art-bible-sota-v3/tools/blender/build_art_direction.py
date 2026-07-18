from __future__ import annotations

"""Deterministic Blender compiler for the three art-direction candidates.

Run only through Blender, preferably via scripts/art-direction.ps1 or .sh. The runner
must include ``--python-exit-code 19`` so uncaught Python errors become process errors.

Blender renders are preflight evidence. Roblox Studio remains the renderer of record.
"""

import argparse
import hashlib
import json
import math
import os
import random
import shutil
import struct
import sys
import traceback
import warnings
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import bpy
import bmesh
from mathutils import Matrix, Vector

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from tools.art.recipe_contract import STATE_STRATEGY_PROFILES
from tools.art.color_math import hex_to_linear_rgba

warnings.filterwarnings(
    "ignore",
    message=r"'(?:Material|World)\.use_nodes'.*",
    category=DeprecationWarning,
)

SCHEMA_BUILD_REPORT = "https://roblox-top1.local/schemas/build-report.schema.json"
ASSETS = ["barricade", "objective_core", "enemy_standard", "floor_module", "damage_effect"]
STATES = ["intact", "damaged", "critical"]
BAND_COLORS = {"primary": "#FF0000", "secondary": "#00FF00", "tertiary": "#0000FF"}
@dataclass
class AssetVariant:
    asset_id: str
    state_id: str
    root: bpy.types.Object
    collection: bpy.types.Collection
    objects: list[bpy.types.Object]
    target_dimensions: dict[str, float]
    pivot: str
    triangle_budget: int
    report: dict[str, Any] | None = None


@dataclass
class BuildContext:
    territory: dict[str, Any]
    calibration: dict[str, Any]
    camera_rig: dict[str, Any]
    render_matrix: dict[str, Any]
    lighting_profiles: dict[str, Any]
    material_rules: dict[str, Any]
    output_dir: Path
    render_mode: str
    max_renders: int | None
    rng: random.Random
    materials: dict[str, bpy.types.Material]
    variants: dict[tuple[str, str], AssetVariant]
    normalization_scales: dict[str, Vector]
    report: dict[str, Any]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    raw = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--territory", choices=["industrial-toy-defense", "salvaged-frontier", "clean-tactical-diorama"], required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--render-mode", choices=["build-only", "smoke", "full"], default="build-only")
    parser.add_argument("--review-renders", action="store_true", help="Render one dynamically framed production-review image per applicable variant.")
    parser.add_argument("--max-renders", type=int, default=None, help="Debug-only cap. Capped runs never count as complete evidence.")
    parser.add_argument("--no-clean-output", action="store_true", help="Debug-only. Preserve existing output files instead of starting from a clean directory.")
    args = parser.parse_args(raw)
    args.root = args.root.resolve()
    args.territory_path = args.root / "art" / "territories" / f"{args.territory}.json"
    args.calibration_path = args.root / "art" / "calibration" / "calibration-kit.json"
    args.camera_path = args.root / "art" / "calibration" / "camera-rig.json"
    args.render_matrix_path = args.root / "art" / "calibration" / "render-matrix.json"
    args.lighting_path = args.root / "art" / "lighting" / "lighting-profiles.json"
    args.material_rules_path = args.root / "art" / "materials" / "material-rules.json"
    args.output = (args.output or (args.root / "build" / args.territory)).resolve()
    if args.max_renders is not None and args.max_renders < 1:
        parser.error("--max-renders must be at least 1")
    return args


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        if collection.name != "Collection":
            bpy.data.collections.remove(collection)
    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)
    for world in list(bpy.data.worlds):
        if world.name != "World":
            bpy.data.worlds.remove(world)


def choose_render_engine(scene: bpy.types.Scene) -> str:
    # Blender 5.2 uses BLENDER_EEVEE; Blender 4.x commonly used BLENDER_EEVEE_NEXT.
    for candidate in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"):
        try:
            scene.render.engine = candidate
            return candidate
        except (TypeError, ValueError):
            continue
    raise RuntimeError("No supported render engine enum found (BLENDER_EEVEE/NEXT/WORKBENCH).")


def hex_to_rgba(value: str, alpha: float = 1.0) -> tuple[float, float, float, float]:
    """Convert authored sRGB hex to Blender's scene-linear RGB contract."""
    return hex_to_linear_rgba(value, alpha)


def make_principled_material(
    name: str,
    color_hex: str,
    roughness: float = 0.65,
    metallic: float = 0.0,
    coat: float = 0.0,
    emission: float = 0.0,
) -> bpy.types.Material:
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = hex_to_rgba(color_hex)
    if not material.use_nodes:
        material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF") if material.node_tree else None
    if bsdf:
        bsdf.inputs["Base Color"].default_value = hex_to_rgba(color_hex)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = coat
        elif "Clearcoat" in bsdf.inputs:
            bsdf.inputs["Clearcoat"].default_value = coat
        if emission > 0:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = hex_to_rgba(color_hex)
            elif "Emission" in bsdf.inputs:
                bsdf.inputs["Emission"].default_value = hex_to_rgba(color_hex)
            if "Emission Strength" in bsdf.inputs:
                bsdf.inputs["Emission Strength"].default_value = emission
    return material


def make_emission_material(name: str, color_hex: str) -> bpy.types.Material:
    material = bpy.data.materials.new(name=name)
    material.diffuse_color = hex_to_rgba(color_hex)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    try:
        emission = nodes.new("ShaderNodeEmission")
        emission.inputs["Color"].default_value = hex_to_rgba(color_hex)
        emission.inputs["Strength"].default_value = 1.0
        material.node_tree.links.new(emission.outputs["Emission"], output.inputs["Surface"])
    except RuntimeError:
        # Forward-compatible fallback for Blender builds that fold emission into Principled BSDF.
        principled = nodes.new("ShaderNodeBsdfPrincipled")
        principled.inputs["Base Color"].default_value = hex_to_rgba(color_hex)
        if "Emission Color" in principled.inputs:
            principled.inputs["Emission Color"].default_value = hex_to_rgba(color_hex)
        elif "Emission" in principled.inputs:
            principled.inputs["Emission"].default_value = hex_to_rgba(color_hex)
        if "Emission Strength" in principled.inputs:
            principled.inputs["Emission Strength"].default_value = 1.0
        principled.inputs["Roughness"].default_value = 1.0
        material.node_tree.links.new(principled.outputs["BSDF"], output.inputs["Surface"])
    return material


def ensure_materials(ctx: BuildContext) -> None:
    palette = ctx.territory["blockoutPalette"]
    profiles = ctx.material_rules["semanticRoleProfiles"]
    surfaces = ctx.material_rules["materials"]
    assignments = ctx.territory["surfaceAssignments"]
    for role, color_hex in palette.items():
        if role not in profiles:
            raise RuntimeError(f"Missing canonical semantic material profile: {role}")
        surface_id = assignments.get(role)
        if surface_id not in surfaces:
            raise RuntimeError(f"Missing surface assignment for {role}: {surface_id}")
        profile = profiles[role]["blender"]
        surface = surfaces[surface_id]
        roughness = (surface["roughness"]["min"] + surface["roughness"]["max"]) * 0.5
        metallic = (surface["metalness"]["min"] + surface["metalness"]["max"]) * 0.5
        material = make_principled_material(
            f"M_{role}",
            color_hex,
            roughness=roughness,
            metallic=metallic,
            coat=profile["coat"],
            emission=profile.get("emission", 0.0),
        )
        material["art_surface_profile"] = surface_id
        ctx.materials[f"beauty:{role}"] = material
        ctx.materials[f"flat:{role}"] = make_emission_material(f"M_FLAT_{role}", color_hex)
    ctx.materials["pass:silhouette"] = make_emission_material("M_PASS_SILHOUETTE", "#000000")
    for band, color_hex in BAND_COLORS.items():
        ctx.materials[f"pass:{band}"] = make_emission_material(f"M_PASS_{band.upper()}", color_hex)


def move_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection) -> None:
    for source in list(obj.users_collection):
        source.objects.unlink(obj)
    collection.objects.link(obj)


def tag_mesh(obj: bpy.types.Object, role: str, band: str, asset_id: str, state_id: str) -> None:
    obj["art_role"] = role
    obj["art_detail_band"] = band
    obj["art_asset_id"] = asset_id
    obj["art_state"] = state_id
    obj["art_original_material"] = obj.data.materials[0].name if obj.data.materials else ""


def apply_bevel(obj: bpy.types.Object, width: float, segments: int = 2) -> None:
    if width <= 0:
        return
    modifier = obj.modifiers.new(name="ART_BEVEL", type="BEVEL")
    modifier.width = width
    modifier.segments = segments
    modifier.limit_method = "ANGLE"
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.select_set(False)


def add_box(ctx: BuildContext, collection: bpy.types.Collection, asset_id: str, state_id: str, name: str, size: tuple[float, float, float], location: tuple[float, float, float], role: str, band: str, rotation: tuple[float, float, float] = (0, 0, 0), bevel_ratio: float = 0.03, bevel_segments: int = 2) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_bevel(obj, min(size) * bevel_ratio, bevel_segments)
    move_to_collection(obj, collection)
    obj.data.materials.append(ctx.materials[f"beauty:{role}"])
    tag_mesh(obj, role, band, asset_id, state_id)
    return obj


def add_chamfered_panel(
    ctx: BuildContext,
    collection: bpy.types.Collection,
    asset_id: str,
    state_id: str,
    name: str,
    size: tuple[float, float, float],
    location: tuple[float, float, float],
    role: str,
    band: str,
    corner_ratio: float = 0.10,
) -> bpy.types.Object:
    """Create a low-triangle, watertight eight-corner armor panel."""
    width, depth, height = size
    corner = min(width, height) * corner_ratio
    outline = [
        (-width / 2 + corner, -height / 2),
        (width / 2 - corner, -height / 2),
        (width / 2, -height / 2 + corner),
        (width / 2, height / 2 - corner),
        (width / 2 - corner, height / 2),
        (-width / 2 + corner, height / 2),
        (-width / 2, height / 2 - corner),
        (-width / 2, -height / 2 + corner),
    ]
    vertices = [(x, -depth / 2, z) for x, z in outline] + [(x, depth / 2, z) for x, z in outline]
    faces: list[tuple[int, ...]] = [tuple(reversed(range(8))), tuple(range(8, 16))]
    for index in range(8):
        next_index = (index + 1) % 8
        faces.append((index, next_index, next_index + 8, index + 8))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = location
    obj.data.materials.append(ctx.materials[f"beauty:{role}"])
    tag_mesh(obj, role, band, asset_id, state_id)
    return obj


def add_cylinder(ctx: BuildContext, collection: bpy.types.Collection, asset_id: str, state_id: str, name: str, radius: float, depth: float, location: tuple[float, float, float], role: str, band: str, vertices: int = 12, rotation: tuple[float, float, float] = (0, 0, 0), bevel_ratio: float = 0.02) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, end_fill_type="NGON", location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    apply_bevel(obj, min(radius * 2, depth) * bevel_ratio)
    move_to_collection(obj, collection)
    obj.data.materials.append(ctx.materials[f"beauty:{role}"])
    tag_mesh(obj, role, band, asset_id, state_id)
    return obj


def add_sphere(ctx: BuildContext, collection: bpy.types.Collection, asset_id: str, state_id: str, name: str, radius: float, location: tuple[float, float, float], role: str, band: str) -> bpy.types.Object:
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    move_to_collection(obj, collection)
    obj.data.materials.append(ctx.materials[f"beauty:{role}"])
    tag_mesh(obj, role, band, asset_id, state_id)
    return obj


def add_ellipsoid(
    ctx: BuildContext,
    collection: bpy.types.Collection,
    asset_id: str,
    state_id: str,
    name: str,
    size: tuple[float, float, float],
    location: tuple[float, float, float],
    role: str,
    band: str,
) -> bpy.types.Object:
    """Create a deliberately faceted toy-like ellipsoid with applied scale."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6, radius=0.5, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to_collection(obj, collection)
    obj.data.materials.append(ctx.materials[f"beauty:{role}"])
    tag_mesh(obj, role, band, asset_id, state_id)
    return obj


def add_torus(ctx: BuildContext, collection: bpy.types.Collection, asset_id: str, state_id: str, name: str, major_radius: float, minor_radius: float, location: tuple[float, float, float], role: str, band: str, rotation: tuple[float, float, float] = (0, 0, 0), major_segments: int = 12, minor_segments: int = 4) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(major_segments=major_segments, minor_segments=minor_segments, major_radius=major_radius, minor_radius=minor_radius, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    move_to_collection(obj, collection)
    obj.data.materials.append(ctx.materials[f"beauty:{role}"])
    tag_mesh(obj, role, band, asset_id, state_id)
    return obj


def add_arc_band(
    ctx: BuildContext,
    collection: bpy.types.Collection,
    asset_id: str,
    state_id: str,
    name: str,
    inner_radius: float,
    outer_radius: float,
    depth: float,
    start_degrees: float,
    end_degrees: float,
    location: tuple[float, float, float],
    role: str,
    band: str,
    segments: int = 6,
    rotation: tuple[float, float, float] = (0, 0, 0),
) -> bpy.types.Object:
    """Create a watertight low-poly annular segment with intentional gaps."""
    if not (0 < inner_radius < outer_radius and depth > 0 and segments >= 1):
        raise ValueError(f"Invalid arc dimensions for {name}")
    angles = [
        math.radians(start_degrees + (end_degrees - start_degrees) * index / segments)
        for index in range(segments + 1)
    ]
    vertices: list[tuple[float, float, float]] = []
    for z in (-depth / 2, depth / 2):
        for radius in (inner_radius, outer_radius):
            vertices.extend((radius * math.cos(angle), radius * math.sin(angle), z) for angle in angles)
    stride = segments + 1
    bottom_inner = 0
    bottom_outer = stride
    top_inner = stride * 2
    top_outer = stride * 3
    faces: list[tuple[int, ...]] = []
    for index in range(segments):
        nxt = index + 1
        faces.extend(
            (
                (bottom_inner + index, bottom_inner + nxt, bottom_outer + nxt, bottom_outer + index),
                (top_inner + index, top_outer + index, top_outer + nxt, top_inner + nxt),
                (bottom_inner + index, top_inner + index, top_inner + nxt, bottom_inner + nxt),
                (bottom_outer + index, bottom_outer + nxt, top_outer + nxt, top_outer + index),
            )
        )
    faces.append((bottom_inner, bottom_outer, top_outer, top_inner))
    faces.append(
        (
            bottom_inner + segments,
            top_inner + segments,
            top_outer + segments,
            bottom_outer + segments,
        )
    )
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    obj.data.materials.append(ctx.materials[f"beauty:{role}"])
    tag_mesh(obj, role, band, asset_id, state_id)
    return obj


def add_wedge(ctx: BuildContext, collection: bpy.types.Collection, asset_id: str, state_id: str, name: str, size: tuple[float, float, float], location: tuple[float, float, float], role: str, band: str, rotation: tuple[float, float, float] = (0, 0, 0)) -> bpy.types.Object:
    w, d, h = size
    verts = [
        (-w / 2, -d / 2, -h / 2), (w / 2, -d / 2, -h / 2), (w / 2, -d / 2, h / 2),
        (-w / 2, d / 2, -h / 2), (w / 2, d / 2, -h / 2), (w / 2, d / 2, h / 2),
    ]
    faces = [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)]
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = rotation
    obj.data.materials.append(ctx.materials[f"beauty:{role}"])
    tag_mesh(obj, role, band, asset_id, state_id)
    return obj


def build_industrial(ctx: BuildContext, collection: bpy.types.Collection, asset_id: str, state_id: str, dims: dict[str, float], bevel: float) -> list[bpy.types.Object]:
    w, d, h = dims["width"], dims["depth"], dims["height"]
    o: list[bpy.types.Object] = []
    if asset_id == "barricade":
        # The frame, not the panels, carries the silhouette. Every visible part
        # has an assembly role that survives mobile-distance simplification.
        for side in (-1, 1):
            x = side * 0.445 * w
            o.append(add_box(ctx, collection, asset_id, state_id, f"FramePost_{side}", (0.13 * w, 0.52 * d, 0.79 * h), (x, 0, 0.49 * h), "primary", "primary", bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"PostGuard_{side}", (0.17 * w, 0.62 * d, 0.18 * h), (x, 0, 0.86 * h), "accent", "secondary", bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"RubberFoot_{side}", (0.22 * w, 0.98 * d, 0.13 * h), (x, 0, 0.065 * h), "rubber", "secondary", bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"FootHousing_{side}", (0.16 * w, 0.68 * d, 0.15 * h), (x, 0, 0.145 * h), "accent", "secondary", bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"RearBrace_{side}", (0.085 * w, 0.13 * d, 0.58 * h), (side * 0.39 * w, 0.31 * d, 0.40 * h), "bareMetal", "secondary", rotation=(math.radians(-20), 0, math.radians(side * 3)), bevel_ratio=0.025, bevel_segments=1))
        o.append(add_box(ctx, collection, asset_id, state_id, "TopRail", (0.82 * w, 0.48 * d, 0.14 * h), (0, 0, 0.88 * h), "primary", "primary", bevel_ratio=bevel, bevel_segments=1))
        o.append(add_box(ctx, collection, asset_id, state_id, "BottomRail", (0.78 * w, 0.42 * d, 0.11 * h), (0, 0, 0.22 * h), "primary", "secondary", bevel_ratio=bevel, bevel_segments=1))
        for index, x in enumerate((-0.27 * w, 0.0, 0.27 * w)):
            panel_parts: list[bpy.types.Object] = []
            panel_parts.append(add_chamfered_panel(ctx, collection, asset_id, state_id, f"Panel_{index}", (0.245 * w, 0.28 * d, 0.56 * h), (x, -0.08 * d, 0.54 * h), "primary", "primary", corner_ratio=0.10))
            panel_parts.append(add_chamfered_panel(ctx, collection, asset_id, state_id, f"PanelInset_{index}", (0.18 * w, 0.045 * d, 0.34 * h), (x, -0.242 * d, 0.54 * h), "secondary", "secondary", corner_ratio=0.16))
            for groove_side in (-1, 1):
                panel_parts.append(add_box(ctx, collection, asset_id, state_id, f"PanelGroove_{index}_{groove_side}", (0.022 * w, 0.025 * d, 0.15 * h), (x + groove_side * 0.035 * w, -0.272 * d, 0.48 * h), "primary", "tertiary", rotation=(0, math.radians(groove_side * 24), 0), bevel_ratio=0.02, bevel_segments=1))
            for z in (0.35 * h, 0.72 * h):
                panel_parts.append(add_cylinder(ctx, collection, asset_id, state_id, f"PanelSocket_{index}", 0.015 * w, 0.075 * d, (x + 0.085 * w, -0.245 * d, z), "bareMetal", "tertiary", vertices=8, rotation=(math.radians(90), 0, 0), bevel_ratio=0.0))
            panel_parts.append(add_box(ctx, collection, asset_id, state_id, f"PanelLatch_{index}", (0.075 * w, 0.055 * d, 0.055 * h), (x, -0.27 * d, 0.275 * h), "accent", "tertiary", bevel_ratio=0.0, bevel_segments=1))
            o.extend(panel_parts)
        for side in (-1, 1):
            o.append(add_cylinder(ctx, collection, asset_id, state_id, f"PostPivot_{side}", 0.038 * w, 0.075 * d, (side * 0.445 * w, -0.305 * d, 0.61 * h), "bareMetal", "secondary", vertices=10, rotation=(math.radians(90), 0, 0), bevel_ratio=0.0))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "LowerServiceRecess", (0.20 * w, 0.035 * d, 0.10 * h), (0, -0.235 * d, 0.275 * h), "rubber", "secondary", corner_ratio=0.18))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "TopRailInset", (0.36 * w, 0.035 * d, 0.065 * h), (0, -0.255 * d, 0.88 * h), "secondary", "secondary", corner_ratio=0.20))
        o.append(add_box(ctx, collection, asset_id, state_id, "InteractionHousing", (0.15 * w, 0.18 * d, 0.17 * h), (0, -0.25 * d, 0.86 * h), "accent", "secondary", bevel_ratio=bevel, bevel_segments=1))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "InteractionLens", 0.047 * w, 0.07 * d, (0, -0.35 * d, 0.86 * h), "interaction", "tertiary", vertices=12, rotation=(math.radians(90), 0, 0), bevel_ratio=0.02))
    elif asset_id == "objective_core":
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "Base", 0.47 * w, 0.15 * h, (0, 0, 0.075 * h), "rubber", "primary", vertices=16, bevel_ratio=bevel))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "ArmoredPedestal", 0.40 * w, 0.25 * h, (0, 0, 0.245 * h), "primary", "primary", vertices=16, bevel_ratio=bevel))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "LowerGuard", 0.34 * w, 0.12 * h, (0, 0, 0.39 * h), "secondary", "secondary", vertices=16, bevel_ratio=bevel))
        o.append(add_sphere(ctx, collection, asset_id, state_id, "Core", 0.23 * w, (0, 0, 0.58 * h), "interaction", "primary"))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "UpperGuard", 0.35 * w, 0.12 * h, (0, 0, 0.76 * h), "secondary", "secondary", vertices=16, bevel_ratio=bevel))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "TopCap", 0.29 * w, 0.12 * h, (0, 0, 0.88 * h), "primary", "primary", vertices=16, bevel_ratio=bevel))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "TopBeaconHousing", 0.10 * w, 0.06 * h, (0, 0, 0.965 * h), "accent", "secondary", vertices=12, bevel_ratio=bevel))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "TopBeaconLens", 0.055 * w, 0.035 * h, (0, 0, 0.995 * h), "interaction", "tertiary", vertices=12, bevel_ratio=0.02))
        for index, (z, radius) in enumerate(((0.43 * h, 0.35 * w), (0.76 * h, 0.36 * w))):
            o.append(add_torus(ctx, collection, asset_id, state_id, f"Ring_{index}", radius, 0.035 * w, (0, 0, z), "accent" if index == 0 else "primary", "secondary", major_segments=16, minor_segments=4))
        for angle in range(0, 360, 90):
            a = math.radians(angle)
            x, y = 0.39 * w * math.cos(a), 0.39 * d * math.sin(a)
            o.append(add_box(ctx, collection, asset_id, state_id, f"Buttress_{angle}", (0.16 * w, 0.20 * d, 0.42 * h), (x, y, 0.25 * h), "primary", "secondary", rotation=(0, 0, a), bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"CageStrut_{angle}", (0.075 * w, 0.075 * d, 0.34 * h), (0.28 * w * math.cos(a), 0.28 * d * math.sin(a), 0.60 * h), "bareMetal", "secondary", rotation=(0, 0, a), bevel_ratio=0.025, bevel_segments=1))
            for collar_index, collar_z in enumerate((0.47 * h, 0.73 * h)):
                o.append(add_box(ctx, collection, asset_id, state_id, f"CageCollar_{angle}_{collar_index}", (0.11 * w, 0.11 * d, 0.07 * h), (0.28 * w * math.cos(a), 0.28 * d * math.sin(a), collar_z), "accent", "tertiary", rotation=(0, 0, a), bevel_ratio=0.04, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"ServiceLatch_{angle}", (0.11 * w, 0.08 * d, 0.08 * h), (0.405 * w * math.cos(a), 0.405 * d * math.sin(a), 0.34 * h), "accent", "tertiary", rotation=(0, 0, a), bevel_ratio=0.04, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"CoreLightBar_{angle}", (0.055 * w, 0.055 * d, 0.18 * h), (0.29 * w * math.cos(a), 0.29 * d * math.sin(a), 0.60 * h), "interaction", "tertiary", rotation=(0, 0, a), bevel_ratio=0.03, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"PedestalArmor_{angle}", (0.16 * w, 0.22 * d, 0.22 * h), (0.37 * w * math.cos(a), 0.37 * d * math.sin(a), 0.23 * h), "secondary", "secondary", rotation=(0, 0, a), bevel_ratio=bevel, bevel_segments=1))
        for index, start in enumerate((8.0, 98.0, 188.0, 278.0)):
            o.append(add_arc_band(ctx, collection, asset_id, state_id, f"CrownArc_{index}", 0.29 * w, 0.38 * w, 0.065 * h, start, start + 66.0, (0, 0, 0.84 * h), "accent", "secondary", segments=5))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "FrontServiceHatch", (0.25 * w, 0.055 * d, 0.18 * h), (0, -0.405 * d, 0.245 * h), "secondary", "secondary", corner_ratio=0.12))
        o.append(add_box(ctx, collection, asset_id, state_id, "FrontServiceHandle", (0.09 * w, 0.055 * d, 0.035 * h), (0, -0.445 * d, 0.31 * h), "accent", "tertiary", bevel_ratio=0.04, bevel_segments=1))
    elif asset_id == "enemy_standard":
        # Compact industrial horde robot: the visor, oversized forearms and
        # compressed torso remain readable at the 60-stud target distance.
        o.append(add_box(ctx, collection, asset_id, state_id, "HipBlock", (0.52 * w, 0.48 * d, 0.12 * h), (0, 0.02 * d, 0.31 * h), "primary", "secondary", bevel_ratio=bevel, bevel_segments=1))
        o.append(add_box(ctx, collection, asset_id, state_id, "TorsoChassis", (0.70 * w, 0.60 * d, 0.35 * h), (0, 0, 0.57 * h), "threat", "primary", bevel_ratio=bevel, bevel_segments=2))
        o.append(add_box(ctx, collection, asset_id, state_id, "Backpack", (0.46 * w, 0.22 * d, 0.27 * h), (0, 0.31 * d, 0.59 * h), "primary", "secondary", bevel_ratio=bevel, bevel_segments=1))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "ChestPanel", (0.48 * w, 0.055 * d, 0.22 * h), (0, -0.325 * d, 0.59 * h), "primary", "secondary", corner_ratio=0.16))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "ChestCore", 0.075 * w, 0.07 * d, (0, -0.37 * d, 0.61 * h), "interaction", "secondary", vertices=10, rotation=(math.radians(90), 0, 0), bevel_ratio=0.02))
        for side in (-1, 1):
            o.append(add_box(ctx, collection, asset_id, state_id, f"ChestChevron_{side}", (0.045 * w, 0.025 * d, 0.09 * h), (side * 0.10 * w, -0.365 * d, 0.53 * h), "accent", "tertiary", rotation=(0, math.radians(side * 17), 0), bevel_ratio=0.02, bevel_segments=1))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "Neck", 0.12 * w, 0.075 * h, (0, 0, 0.785 * h), "bareMetal", "secondary", vertices=8, bevel_ratio=0.02))
        o.append(add_ellipsoid(ctx, collection, asset_id, state_id, "HeadShell", (0.54 * w, 0.52 * d, 0.22 * h), (0, -0.025 * d, 0.89 * h), "primary", "primary"))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "Visor", (0.39 * w, 0.055 * d, 0.075 * h), (0, -0.29 * d, 0.89 * h), "interaction", "secondary", corner_ratio=0.28))
        o.append(add_box(ctx, collection, asset_id, state_id, "HelmetBrow", (0.36 * w, 0.08 * d, 0.035 * h), (0, -0.285 * d, 0.95 * h), "accent", "tertiary", bevel_ratio=0.04, bevel_segments=1))
        for side in (-1, 1):
            o.append(add_box(ctx, collection, asset_id, state_id, f"ShoulderGuard_{side}", (0.23 * w, 0.66 * d, 0.16 * h), (side * 0.42 * w, 0, 0.67 * h), "accent", "secondary", rotation=(0, math.radians(side * 6), math.radians(side * 3)), bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"UpperArm_{side}", (0.17 * w, 0.24 * d, 0.22 * h), (side * 0.44 * w, 0, 0.53 * h), "primary", "secondary", rotation=(0, 0, math.radians(side * 4)), bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"Forearm_{side}", (0.27 * w, 0.34 * d, 0.24 * h), (side * 0.47 * w, -0.04 * d, 0.39 * h), "threat", "primary", rotation=(math.radians(-4), math.radians(side * 7), math.radians(side * 3)), bevel_ratio=bevel, bevel_segments=2))
            o.append(add_box(ctx, collection, asset_id, state_id, f"Fist_{side}", (0.25 * w, 0.35 * d, 0.15 * h), (side * 0.48 * w, -0.11 * d, 0.27 * h), "rubber", "secondary", rotation=(math.radians(-7), 0, math.radians(side * 2)), bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"Shin_{side}", (0.21 * w, 0.27 * d, 0.25 * h), (side * 0.18 * w, 0.01 * d, 0.17 * h), "primary", "secondary", rotation=(0, 0, math.radians(side * 2)), bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"Boot_{side}", (0.25 * w, 0.43 * d, 0.11 * h), (side * 0.18 * w, -0.07 * d, 0.055 * h), "rubber", "secondary", bevel_ratio=bevel, bevel_segments=1))
            o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, f"ForearmInset_{side}", (0.17 * w, 0.035 * d, 0.11 * h), (side * 0.47 * w, -0.225 * d, 0.40 * h), "accent", "tertiary", corner_ratio=0.18))
            o.append(add_cylinder(ctx, collection, asset_id, state_id, f"ShoulderSocket_{side}", 0.055 * w, 0.06 * d, (side * 0.41 * w, -0.34 * d, 0.67 * h), "bareMetal", "tertiary", vertices=8, rotation=(math.radians(90), 0, 0), bevel_ratio=0.0))
            o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, f"KneeGuard_{side}", (0.15 * w, 0.04 * d, 0.08 * h), (side * 0.18 * w, -0.165 * d, 0.22 * h), "accent", "tertiary", corner_ratio=0.20))
    elif asset_id == "floor_module":
        o.append(add_box(ctx, collection, asset_id, state_id, "TileBase", (w, d, 0.58 * h), (0, 0, 0.29 * h), "rubber", "primary", bevel_ratio=bevel, bevel_segments=1))
        o.append(add_box(ctx, collection, asset_id, state_id, "DeckPlate", (0.88 * w, 0.88 * d, 0.12 * h), (0, 0, 0.68 * h), "primary", "primary", bevel_ratio=0.055, bevel_segments=1))
        for side in (-1, 1):
            o.append(add_box(ctx, collection, asset_id, state_id, f"EdgeRailX_{side}", (0.76 * w, 0.075 * d, 0.13 * h), (0, side * 0.445 * d, 0.79 * h), "bareMetal", "secondary", bevel_ratio=0.0, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"EdgeRailY_{side}", (0.075 * w, 0.76 * d, 0.13 * h), (side * 0.445 * w, 0, 0.79 * h), "bareMetal", "secondary", bevel_ratio=0.0, bevel_segments=1))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "CenterInset", 0.27 * w, 0.16 * h, (0, 0, 0.84 * h), "secondary", "secondary", vertices=8, bevel_ratio=0.04))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "CenterMark", 0.11 * w, 0.05 * h, (0, 0, 0.955 * h), "accent", "tertiary", vertices=8, bevel_ratio=0.02))
        for index, (x, y) in enumerate(((0.39 * w, 0.39 * d), (-0.39 * w, 0.39 * d), (-0.39 * w, -0.39 * d), (0.39 * w, -0.39 * d))):
            o.append(add_cylinder(ctx, collection, asset_id, state_id, f"CornerLock_{index}", 0.045 * w, 0.08 * h, (x, y, 0.90 * h), "accent", "tertiary", vertices=8, bevel_ratio=0.0))
    else:
        severity = 1.0 if state_id == "damaged" else 1.18
        o.append(add_wedge(ctx, collection, asset_id, state_id, "ImpactFlash", (0.62 * w * severity, 0.34 * d, 0.50 * h * severity), (0.04 * w, 0, 0), "critical", "primary", rotation=(0, math.radians(18), math.radians(-8))))
        o.append(add_wedge(ctx, collection, asset_id, state_id, "DirectionBladeUpper", (0.46 * w * severity, 0.20 * d, 0.18 * h), (-0.18 * w, 0.03 * d, 0.27 * h), "warning", "secondary", rotation=(math.radians(-8), math.radians(-28), math.radians(22))))
        o.append(add_wedge(ctx, collection, asset_id, state_id, "DirectionBladeLower", (0.42 * w * severity, 0.18 * d, 0.16 * h), (-0.16 * w, -0.04 * d, -0.25 * h), "warning", "secondary", rotation=(math.radians(7), math.radians(24), math.radians(-20))))
        o.append(add_torus(ctx, collection, asset_id, state_id, "ImpactRing", 0.29 * w * severity, 0.025 * w, (0, 0, 0), "interaction", "secondary", rotation=(math.radians(90), 0, 0), major_segments=8, minor_segments=3))
        for index, (x, y, z, rz) in enumerate(((-0.42, 0.10, 0.12, 18), (0.36, 0.16, -0.18, -24), (0.22, -0.22, 0.31, 35))):
            o.append(add_wedge(ctx, collection, asset_id, state_id, f"ImpactFragment_{index}", (0.16 * w, 0.12 * d, 0.18 * h), (x * w, y * d, z * h), "critical" if state_id == "critical" else "warning", "tertiary", rotation=(math.radians(12), math.radians(20), math.radians(rz))))
        for side in (-1, 1):
            o.append(add_box(ctx, collection, asset_id, state_id, "Fragment", (0.15 * w, 0.12 * d, 0.18 * h), (side * 0.34 * w, 0.16 * d, side * 0.14 * h), "warning", "secondary", rotation=(side * 0.3, 0.2, side * 0.4), bevel_ratio=0.0))
        if state_id == "critical":
            o.append(add_wedge(ctx, collection, asset_id, state_id, "CriticalSplit", (0.42 * w, 0.34 * d, 0.46 * h), (-0.08 * w, 0.04 * d, 0), "critical", "secondary", rotation=(math.radians(18), math.radians(-20), math.radians(35))))
    return o


def build_salvaged(ctx: BuildContext, collection: bpy.types.Collection, asset_id: str, state_id: str, dims: dict[str, float], bevel: float) -> list[bpy.types.Object]:
    w, d, h = dims["width"], dims["depth"], dims["height"]
    o: list[bpy.types.Object] = []
    if asset_id == "barricade":
        for side, x, panel_width, panel_height, tilt in ((-1, -0.25, 0.44, 0.61, 2.5), (1, 0.27, 0.40, 0.54, -3.5)):
            panel = add_chamfered_panel(ctx, collection, asset_id, state_id, f"RecoveredPanel_{side}", (panel_width * w, 0.30 * d, panel_height * h), (x * w, -0.04 * d, (0.50 if side < 0 else 0.47) * h), "secondary" if side < 0 else "primary", "primary", corner_ratio=0.07)
            panel.rotation_euler.z = math.radians(tilt)
            if side > 0 and state_id != "intact":
                panel.location += Vector(((0.02 if state_id == "damaged" else 0.07) * w, (0.03 if state_id == "damaged" else 0.13) * d, -(0.06 if state_id == "damaged" else 0.17) * h))
                panel.rotation_euler.z += math.radians(-7 if state_id == "damaged" else -16)
                panel.rotation_euler.x += math.radians(0 if state_id == "damaged" else 12)
            o.append(panel)
            inset = add_chamfered_panel(ctx, collection, asset_id, state_id, f"RecoveredInset_{side}", (0.30 * w, 0.035 * d, (0.35 if side < 0 else 0.30) * h), (x * w, -0.205 * d, (0.50 if side < 0 else 0.47) * h), "primary" if side < 0 else "secondary", "secondary", corner_ratio=0.10)
            inset.rotation_euler.z = panel.rotation_euler.z
            if side > 0 and state_id != "intact":
                inset.location += panel.location - Vector((x * w, -0.04 * d, 0.47 * h))
                inset.rotation_euler.x = panel.rotation_euler.x
            o.append(inset)
        beam_z = 0.50 * h - (0.02 * h if state_id == "damaged" else 0.0)
        beam_rot = -5 if state_id == "intact" else (-10 if state_id == "damaged" else -18)
        o.append(add_box(ctx, collection, asset_id, state_id, "CentralBeam", (0.12 * w, 0.56 * d, 0.88 * h), (0.01 * w, 0, beam_z), "primary", "primary", rotation=(0, 0, math.radians(beam_rot)), bevel_ratio=bevel, bevel_segments=1))
        o.append(add_box(ctx, collection, asset_id, state_id, "RepairBrace", (0.065 * w, 0.10 * d, 0.74 * h), (-0.02 * w, -0.24 * d, 0.52 * h), "bareMetal", "secondary", rotation=(0, 0, math.radians(34)), bevel_ratio=0.02, bevel_segments=1))
        o.append(add_box(ctx, collection, asset_id, state_id, "RepairBraceShort", (0.055 * w, 0.095 * d, 0.38 * h), (0.25 * w, -0.23 * d, 0.51 * h), "accent", "secondary", rotation=(0, 0, math.radians(-29)), bevel_ratio=0.02, bevel_segments=1))
        for side in (-1, 1):
            post_height = 0.72 if side < 0 else 0.64
            post_x = side * (0.455 if side < 0 else 0.445) * w
            o.append(add_box(ctx, collection, asset_id, state_id, f"RecoveredPost_{side}", ((0.11 if side < 0 else 0.095) * w, 0.50 * d, post_height * h), (post_x, 0.02 * d, (0.20 + post_height * 0.5) * h), "bareMetal" if side < 0 else "primary", "primary", rotation=(0, 0, math.radians(side * 2.5)), bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"TopClamp_{side}", (0.16 * w, 0.57 * d, 0.12 * h), (post_x, 0, (0.82 if side < 0 else 0.77) * h), "accent", "secondary", rotation=(0, 0, math.radians(side * 2.5)), bevel_ratio=bevel, bevel_segments=1))
        for index, x in enumerate((-0.36 * w, 0.34 * w)):
            o.append(add_box(ctx, collection, asset_id, state_id, f"WeightedFoot_{index}", (0.26 * w, 0.90 * d, 0.16 * h), (x, 0.04 * d, 0.08 * h), "rubber", "secondary", rotation=(0, 0, math.radians(2 if x > 0 else -2)), bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"FootClamp_{index}", (0.13 * w, 0.56 * d, 0.13 * h), (x, -0.02 * d, 0.17 * h), "accent", "tertiary", rotation=(0, 0, math.radians(2 if x > 0 else -2)), bevel_ratio=0.025, bevel_segments=1))
        for index, (x, z) in enumerate(((-0.38, 0.66), (-0.17, 0.31), (0.18, 0.67), (0.38, 0.34))):
            o.append(add_cylinder(ctx, collection, asset_id, state_id, f"PanelBolt_{index}", 0.025 * w, 0.045 * d, (x * w, -0.235 * d, z * h), "bareMetal", "tertiary", vertices=8, rotation=(math.radians(90), 0, 0), bevel_ratio=0.0))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "ReplacementPatch", (0.20 * w, 0.045 * d, 0.19 * h), (-0.24 * w, -0.235 * d, 0.63 * h), "accent", "secondary", corner_ratio=0.08))
        for index, (x, z) in enumerate(((-0.31, 0.69), (-0.17, 0.69), (-0.31, 0.57), (-0.17, 0.57))):
            o.append(add_cylinder(ctx, collection, asset_id, state_id, f"PatchBolt_{index}", 0.014 * w, 0.035 * d, (x * w, -0.265 * d, z * h), "bareMetal", "tertiary", vertices=8, rotation=(math.radians(90), 0, 0), bevel_ratio=0.0))
    elif asset_id == "objective_core":
        o.append(add_box(ctx, collection, asset_id, state_id, "BaseSkid", (0.90 * w, 0.68 * d, 0.12 * h), (0, 0.05 * d, 0.06 * h), "rubber", "primary", rotation=(0, 0, math.radians(-2)), bevel_ratio=bevel, bevel_segments=1))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "BasePuck", 0.43 * w, 0.16 * h, (-0.02 * w, 0.02 * d, 0.15 * h), "bareMetal", "primary", vertices=12, bevel_ratio=bevel))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "RecoveredTank", 0.39 * w, 0.72 * h, (-0.03 * w, 0.02 * d, 0.44 * h), "primary", "primary", vertices=12, rotation=(math.radians(1.5), math.radians(-2), 0), bevel_ratio=bevel))
        for index, (z, tilt) in enumerate(((0.20 * h, -3), (0.47 * h, 4), (0.74 * h, -2))):
            o.append(add_torus(ctx, collection, asset_id, state_id, f"RepairBand_{index}", 0.405 * w, 0.026 * w, (-0.03 * w, 0.02 * d, z), "bareMetal" if index != 1 else "accent", "secondary", rotation=(math.radians(tilt), 0, math.radians(tilt)), major_segments=12, minor_segments=4))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "CoreSocket", 0.22 * w, 0.12 * d, (0.03 * w, -0.39 * d, 0.55 * h), "rubber", "secondary", vertices=12, rotation=(math.radians(90), 0, 0), bevel_ratio=0.02))
        o.append(add_ellipsoid(ctx, collection, asset_id, state_id, "Core", (0.31 * w, 0.12 * d, 0.27 * h), (0.03 * w, -0.455 * d, 0.55 * h), "critical" if state_id == "critical" else "interaction", "secondary"))
        service_rotation = math.radians(-8 if state_id == "intact" else (-22 if state_id == "damaged" else -38))
        service = add_box(ctx, collection, asset_id, state_id, "ServiceBox", (0.27 * w, 0.23 * d, 0.27 * h), (0.36 * w, -0.13 * d, (0.47 if state_id != "critical" else 0.42) * h), "accent", "secondary", rotation=(0, service_rotation, math.radians(4)), bevel_ratio=bevel, bevel_segments=1)
        o.append(service)
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "ServiceFace", (0.18 * w, 0.035 * d, 0.16 * h), (0.36 * w, -0.26 * d, 0.47 * h), "warning" if state_id != "intact" else "secondary", "tertiary", corner_ratio=0.12))
        o.append(add_box(ctx, collection, asset_id, state_id, "TankPatch", (0.22 * w, 0.055 * d, 0.18 * h), (-0.25 * w, -0.34 * d, 0.31 * h), "secondary", "secondary", rotation=(0, math.radians(3), math.radians(-7)), bevel_ratio=0.02, bevel_segments=1))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "RecoveredLid", 0.31 * w, 0.11 * h, (-0.03 * w, 0.02 * d, 0.865 * h), "secondary", "secondary", vertices=12, bevel_ratio=bevel))
        o.append(add_box(ctx, collection, asset_id, state_id, "ServiceHandle", (0.12 * w, 0.05 * d, 0.035 * h), (0.36 * w, -0.29 * d, 0.55 * h), "bareMetal", "tertiary", rotation=(0, service_rotation, math.radians(4)), bevel_ratio=0.02, bevel_segments=1))
        for index, angle in enumerate((35, 155, 275)):
            a = math.radians(angle)
            o.append(add_box(ctx, collection, asset_id, state_id, f"SkidLeg_{index}", (0.18 * w, 0.22 * d, 0.28 * h), (0.37 * w * math.cos(a), 0.31 * d * math.sin(a), 0.20 * h), "rubber", "secondary", rotation=(0, 0, a), bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"BandClamp_{index}", (0.10 * w, 0.08 * d, 0.11 * h), (0.40 * w * math.cos(a), 0.40 * d * math.sin(a), (0.28 + index * 0.20) * h), "accent", "tertiary", rotation=(0, 0, a), bevel_ratio=0.025, bevel_segments=1))
        o.append(add_arc_band(ctx, collection, asset_id, state_id, "CarryHoop", 0.38 * w, 0.44 * w, 0.055 * h, 205, 335, (-0.03 * w, 0.02 * d, 0.82 * h), "bareMetal", "secondary", segments=7, rotation=(math.radians(68), 0, 0)))
    elif asset_id == "enemy_standard":
        torso = add_box(ctx, collection, asset_id, state_id, "LeaningTorso", (0.68 * w, 0.57 * d, 0.36 * h), (0.03 * w, 0, 0.58 * h), "primary", "primary", rotation=(0, math.radians(-5), math.radians(-5 if state_id != "critical" else -12)), bevel_ratio=bevel, bevel_segments=1)
        o.append(torso)
        o.append(add_box(ctx, collection, asset_id, state_id, "BackScrap", (0.46 * w, 0.22 * d, 0.29 * h), (-0.02 * w, 0.30 * d, 0.60 * h), "primary", "secondary", rotation=(0, 0, math.radians(-4)), bevel_ratio=bevel, bevel_segments=1))
        o.append(add_ellipsoid(ctx, collection, asset_id, state_id, "HoodMass", (0.58 * w, 0.54 * d, 0.24 * h), (-0.04 * w, -0.02 * d, 0.88 * h), "primary", "primary"))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "HoodVisor", (0.34 * w, 0.05 * d, 0.07 * h), (-0.06 * w, -0.30 * d, 0.87 * h), "warning" if state_id == "damaged" else ("critical" if state_id == "critical" else "threat"), "secondary", corner_ratio=0.22))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "HoodPlate", (0.30 * w, 0.045 * d, 0.08 * h), (-0.04 * w, -0.285 * d, 0.955 * h), "secondary", "secondary", corner_ratio=0.20))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "ChestScrap", (0.42 * w, 0.05 * d, 0.20 * h), (0.02 * w, -0.32 * d, 0.58 * h), "primary", "secondary", corner_ratio=0.10))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "ChestCore", 0.065 * w, 0.06 * d, (0.02 * w, -0.36 * d, 0.60 * h), "critical" if state_id == "critical" else ("warning" if state_id == "damaged" else "threat"), "secondary", vertices=8, rotation=(math.radians(90), 0, 0), bevel_ratio=0.0))
        repair_drop = 0.0 if state_id == "intact" else (0.08 if state_id == "damaged" else 0.18)
        repair_rot = -11 if state_id == "intact" else (-24 if state_id == "damaged" else -39)
        o.append(add_box(ctx, collection, asset_id, state_id, "RepairedArm", (0.25 * w, 0.30 * d, 0.38 * h), (0.46 * w, 0.01 * d, (0.51 - repair_drop) * h), "accent", "primary", rotation=(0, math.radians(-12), math.radians(repair_rot)), bevel_ratio=bevel, bevel_segments=1))
        o.append(add_box(ctx, collection, asset_id, state_id, "RepairShoulder", (0.26 * w, 0.48 * d, 0.15 * h), (0.40 * w, 0, (0.68 - repair_drop * 0.5) * h), "bareMetal", "secondary", rotation=(0, 0, math.radians(repair_rot * 0.45)), bevel_ratio=bevel, bevel_segments=1))
        o.append(add_box(ctx, collection, asset_id, state_id, "HeavyArm", (0.34 * w, 0.37 * d, 0.32 * h), (-0.45 * w, -0.01 * d, 0.49 * h), "primary", "primary", rotation=(0, math.radians(7), math.radians(9)), bevel_ratio=bevel, bevel_segments=1))
        o.append(add_box(ctx, collection, asset_id, state_id, "HeavyFist", (0.32 * w, 0.40 * d, 0.17 * h), (-0.46 * w, -0.08 * d, 0.30 * h), "rubber", "secondary", rotation=(0, 0, math.radians(6)), bevel_ratio=bevel, bevel_segments=1))
        for side, zrot, height in ((-1, 5, 0.27), (1, -7, 0.31)):
            o.append(add_box(ctx, collection, asset_id, state_id, f"UnequalLeg_{side}", ((0.21 if side < 0 else 0.25) * w, 0.27 * d, height * h), (side * 0.19 * w, 0, height * h * 0.5), "secondary", "secondary", rotation=(0, 0, math.radians(zrot)), bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"ScrapBoot_{side}", ((0.24 if side < 0 else 0.28) * w, 0.42 * d, 0.10 * h), (side * 0.19 * w, -0.06 * d, 0.05 * h), "rubber", "secondary", rotation=(0, 0, math.radians(zrot)), bevel_ratio=bevel, bevel_segments=1))
            o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, f"KneePatch_{side}", ((0.14 if side < 0 else 0.17) * w, 0.035 * d, 0.09 * h), (side * 0.19 * w, -0.155 * d, 0.22 * h), "accent" if side > 0 else "secondary", "tertiary", corner_ratio=0.15))
        o.append(add_arc_band(ctx, collection, asset_id, state_id, "HoodBand", 0.23 * w, 0.30 * w, 0.045 * h, 195, 345, (-0.04 * w, -0.02 * d, 0.91 * h), "bareMetal", "secondary", segments=6, rotation=(math.radians(90), 0, 0)))
        o.append(add_box(ctx, collection, asset_id, state_id, "ChestRepairStrap", (0.055 * w, 0.035 * d, 0.29 * h), (-0.10 * w, -0.34 * d, 0.58 * h), "bareMetal", "secondary", rotation=(0, 0, math.radians(-11)), bevel_ratio=0.015, bevel_segments=1))
        o.append(add_box(ctx, collection, asset_id, state_id, "ArmClamp", (0.31 * w, 0.34 * d, 0.065 * h), (0.46 * w, 0.01 * d, (0.54 - repair_drop) * h), "bareMetal", "secondary", rotation=(0, math.radians(-12), math.radians(repair_rot)), bevel_ratio=0.02, bevel_segments=1))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "HeavyShoulderScrap", (0.25 * w, 0.055 * d, 0.14 * h), (-0.40 * w, -0.24 * d, 0.64 * h), "secondary", "secondary", corner_ratio=0.12))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "RepairedArmInset", (0.14 * w, 0.035 * d, 0.15 * h), (0.46 * w, -0.16 * d, (0.51 - repair_drop) * h), "secondary", "tertiary", corner_ratio=0.10))
        o.append(add_box(ctx, collection, asset_id, state_id, "HipScrap", (0.42 * w, 0.38 * d, 0.09 * h), (0, 0.01 * d, 0.32 * h), "bareMetal", "secondary", rotation=(0, 0, math.radians(-4)), bevel_ratio=bevel, bevel_segments=1))
        for side in (-1, 1):
            o.append(add_cylinder(ctx, collection, asset_id, state_id, f"AnkleClamp_{side}", 0.075 * w, 0.065 * h, (side * 0.19 * w, -0.02 * d, 0.11 * h), "accent", "tertiary", vertices=8, bevel_ratio=0.0))
    elif asset_id == "floor_module":
        o.append(add_box(ctx, collection, asset_id, state_id, "SalvagedPlate", (w, d, 0.58 * h), (0, 0, 0.29 * h), "rubber", "primary", rotation=(0, 0, math.radians(0.5)), bevel_ratio=bevel, bevel_segments=1))
        o.append(add_box(ctx, collection, asset_id, state_id, "MainDeck", (0.90 * w, 0.90 * d, 0.14 * h), (-0.02 * w, 0.02 * d, 0.69 * h), "primary", "primary", rotation=(0, 0, math.radians(1)), bevel_ratio=bevel, bevel_segments=1))
        lift = 0.0 if state_id == "intact" else 0.09 * h
        quadrant = add_box(ctx, collection, asset_id, state_id, "ReplacementQuadrant", (0.44 * w, 0.44 * d, 0.16 * h), (0.23 * w, -0.23 * d, 0.82 * h + lift), "accent", "secondary", rotation=(math.radians(0 if state_id == "intact" else 9), 0, math.radians(-3)), bevel_ratio=bevel, bevel_segments=1)
        o.append(quadrant)
        for index, (x, y, rot) in enumerate(((-0.32 * w, 0.34 * d, 15), (0.35 * w, 0.30 * d, -10), (-0.36 * w, -0.30 * d, -18))):
            o.append(add_box(ctx, collection, asset_id, state_id, f"EdgeStrap_{index}", (0.075 * w, 0.34 * d, 0.10 * h), (x, y, 0.84 * h), "bareMetal", "tertiary", rotation=(0, 0, math.radians(rot)), bevel_ratio=0.0, bevel_segments=1))
        for index, (x, y) in enumerate(((-0.38, 0.36), (0.37, 0.34), (-0.36, -0.35), (0.35, -0.36))):
            o.append(add_cylinder(ctx, collection, asset_id, state_id, f"DeckRivet_{index}", 0.035 * w, 0.06 * h, (x * w, y * d, 0.88 * h), "secondary", "tertiary", vertices=8, bevel_ratio=0.0))
        for index, (x, y, width, depth, rotation_z) in enumerate(((-0.22, 0.17, 0.36, 0.16, 2), (-0.20, -0.15, 0.38, 0.15, -3), (0.16, 0.18, 0.25, 0.13, -1))):
            o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, f"DeckPlank_{index}", (width * w, depth * d, 0.08 * h), (x * w, y * d, 0.88 * h), "secondary", "secondary", corner_ratio=0.06))
            o[-1].rotation_euler.z = math.radians(rotation_z)
        for index, (x, y) in enumerate(((-0.40, 0.02), (0.38, 0.05), (0.02, 0.39), (-0.04, -0.38))):
            o.append(add_box(ctx, collection, asset_id, state_id, f"PerimeterClamp_{index}", (0.13 * w, 0.09 * d, 0.09 * h), (x * w, y * d, 0.87 * h), "accent", "tertiary", rotation=(0, 0, math.radians(index * 90)), bevel_ratio=0.02, bevel_segments=1))
    else:
        severity = 1.0 if state_id == "damaged" else 1.15
        o.append(add_wedge(ctx, collection, asset_id, state_id, "AsymmetricArcMass", (0.72 * w * severity, 0.56 * d, 0.60 * h * severity), (0, 0, 0), "critical", "primary", rotation=(math.radians(8), math.radians(22), math.radians(-8))))
        for i, (x, y, z) in enumerate(((-0.42, 0.10, 0.18), (0.32, 0.22, -0.14), (0.16, -0.30, 0.28))):
            o.append(add_box(ctx, collection, asset_id, state_id, f"HeavyShard_{i}", (0.14 * w, 0.10 * d, 0.18 * h), (x * 0.82 * w, y * d, z * h), "warning", "secondary", rotation=(0.2 * i, -0.25 * i, 0.35 * i), bevel_ratio=0.0))
        o.append(add_torus(ctx, collection, asset_id, state_id, "RerouteArc", 0.26 * w * severity, 0.025 * w, (0.08 * w, 0, 0), "interaction", "tertiary", rotation=(math.radians(80), math.radians(12), 0), major_segments=8, minor_segments=3))
        if state_id == "critical":
            o.append(add_wedge(ctx, collection, asset_id, state_id, "CriticalFray", (0.34 * w, 0.30 * d, 0.42 * h), (0.06 * w, 0, 0), "critical", "secondary", rotation=(math.radians(-16), math.radians(28), math.radians(-32))))
    return o


def build_clean(ctx: BuildContext, collection: bpy.types.Collection, asset_id: str, state_id: str, dims: dict[str, float], bevel: float) -> list[bpy.types.Object]:
    w, d, h = dims["width"], dims["depth"], dims["height"]
    o: list[bpy.types.Object] = []
    if asset_id == "barricade":
        plate = add_chamfered_panel(ctx, collection, asset_id, state_id, "CenterPlate", (0.74 * w, 0.32 * d, 0.66 * h), (0, -0.02 * d, 0.55 * h), "primary", "primary", corner_ratio=0.06)
        o.append(plate)
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "CenterInset", (0.58 * w, 0.045 * d, 0.44 * h), (0, -0.205 * d, 0.55 * h), "secondary", "secondary", corner_ratio=0.08))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "LowerFrameRail", (0.70 * w, 0.08 * d, 0.09 * h), (0, -0.15 * d, 0.245 * h), "accent", "secondary", corner_ratio=0.16))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "UpperFrameRail", (0.72 * w, 0.08 * d, 0.10 * h), (0, -0.15 * d, 0.865 * h), "secondary", "secondary", corner_ratio=0.16))
        for side, x in ((-1, -0.43 * w), (1, 0.43 * w)):
            o.append(add_box(ctx, collection, asset_id, state_id, f"Support_{side}", (0.14 * w, 0.64 * d, 0.68 * h), (x, 0, 0.43 * h), "secondary", "secondary", bevel_ratio=bevel, bevel_segments=2))
            o.append(add_box(ctx, collection, asset_id, state_id, f"Foot_{side}", (0.22 * w, 0.88 * d, 0.14 * h), (x, 0, 0.07 * h), "rubber", "secondary", bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"FootCap_{side}", (0.14 * w, 0.54 * d, 0.12 * h), (x, 0, 0.16 * h), "accent", "tertiary", bevel_ratio=0.025, bevel_segments=1))
            o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, f"SupportWing_{side}", (0.16 * w, 0.06 * d, 0.22 * h), (side * 0.38 * w, -0.345 * d, 0.54 * h), "accent", "secondary", corner_ratio=0.18))
            o.append(add_cylinder(ctx, collection, asset_id, state_id, f"SupportSocket_{side}", 0.038 * w, 0.055 * d, (side * 0.43 * w, -0.34 * d, 0.35 * h), "bareMetal", "tertiary", vertices=8, rotation=(math.radians(90), 0, 0), bevel_ratio=0.0))
        strip_role = "interaction" if state_id == "intact" else ("warning" if state_id == "damaged" else "critical")
        o.append(add_box(ctx, collection, asset_id, state_id, "InteractionStrip", (0.66 * w, 0.18 * d, 0.075 * h), (0, -0.23 * d, 0.90 * h), strip_role, "secondary", bevel_ratio=bevel, bevel_segments=1))
        for side in (-1, 1):
            o.append(add_box(ctx, collection, asset_id, state_id, f"PanelSeam_{side}", (0.025 * w, 0.025 * d, 0.29 * h), (side * 0.19 * w, -0.235 * d, 0.54 * h), "accent", "tertiary", bevel_ratio=0.0, bevel_segments=1))
            o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, f"PanelBay_{side}", (0.12 * w, 0.025 * d, 0.13 * h), (side * 0.20 * w, -0.24 * d, 0.54 * h), "rubber", "secondary", corner_ratio=0.22))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "CenterStatusSocket", 0.045 * w, 0.055 * d, (0, -0.25 * d, 0.54 * h), strip_role, "secondary", vertices=12, rotation=(math.radians(90), 0, 0), bevel_ratio=0.02))
        if state_id == "damaged":
            o.append(add_box(ctx, collection, asset_id, state_id, "CleanNotch", (0.06 * w, 0.10 * d, 0.17 * h), (0.30 * w, -0.20 * d, 0.70 * h), "rubber", "secondary", rotation=(0, 0, math.radians(18)), bevel_ratio=0.0, bevel_segments=1))
        elif state_id == "critical":
            for side in (-1, 1):
                o.append(add_box(ctx, collection, asset_id, state_id, f"PlaneSplit_{side}", (0.03 * w, 0.08 * d, 0.34 * h), (side * 0.045 * w, -0.22 * d, 0.53 * h), "critical", "secondary", rotation=(0, 0, math.radians(side * 5)), bevel_ratio=0.0, bevel_segments=1))
        if state_id != "intact":
            _transform_group(
                _named_group(o, ("CenterPlate", "CenterInset", "PanelSeam", "PanelBay", "CleanNotch", "PlaneSplit")),
                Vector((0, -0.02 * d, 0.55 * h)),
                Vector(((0.025 if state_id == "damaged" else 0.07) * w, (0.015 if state_id == "damaged" else 0.08) * d, -(0.035 if state_id == "damaged" else 0.12) * h)),
                rotation_x=math.radians(0 if state_id == "damaged" else 10),
                rotation_z=math.radians(-3 if state_id == "damaged" else -9),
            )
    elif asset_id == "objective_core":
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "LowerStage", 0.47 * w, 0.18 * h, (0, 0, 0.09 * h), "rubber", "primary", vertices=12, bevel_ratio=bevel))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "LowerCollar", 0.40 * w, 0.16 * h, (0, 0, 0.22 * h), "accent", "secondary", vertices=12, bevel_ratio=bevel))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "UpperStage", 0.34 * w, 0.28 * h, (0, 0, 0.38 * h), "secondary", "primary", vertices=12, bevel_ratio=bevel))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "CoreAperture", 0.26 * w, 0.11 * h, (0, 0, 0.52 * h), "rubber", "secondary", vertices=12, bevel_ratio=bevel))
        o.append(add_ellipsoid(ctx, collection, asset_id, state_id, "Core", (0.38 * w, 0.38 * d, 0.28 * h), (0, -0.01 * d, 0.62 * h), "critical" if state_id == "critical" else "interaction", "secondary"))
        for index, (z, r) in enumerate(((0.49 * h, 0.38 * w), (0.72 * h, 0.33 * w))):
            ring = add_torus(ctx, collection, asset_id, state_id, f"ConcentricRing_{index}", r, 0.028 * w, (0, 0, z), "warning" if state_id == "damaged" and index == 1 else "accent", "secondary", major_segments=12, minor_segments=4)
            if state_id != "intact" and index == 1:
                ring.rotation_euler.x = math.radians(10 if state_id == "damaged" else 17)
                ring.location.x += (0.04 if state_id == "damaged" else 0.06) * w
                ring.location.z += (0.015 if state_id == "damaged" else 0.0) * h
            o.append(ring)
        for angle in range(0, 360, 90):
            a = math.radians(angle)
            o.append(add_box(ctx, collection, asset_id, state_id, f"IdenticalButtress_{angle}", (0.13 * w, 0.16 * d, 0.34 * h), (0.38 * w * math.cos(a), 0.38 * d * math.sin(a), 0.25 * h), "primary", "secondary", rotation=(0, 0, a), bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"ButtressLight_{angle}", (0.075 * w, 0.035 * d, 0.055 * h), (0.39 * w * math.cos(a), 0.39 * d * math.sin(a), 0.39 * h), "interaction" if state_id == "intact" else ("warning" if state_id == "damaged" else "critical"), "tertiary", rotation=(0, 0, a), bevel_ratio=0.02, bevel_segments=1))
            o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, f"BaseFacet_{angle}", (0.20 * w, 0.045 * d, 0.16 * h), (0.34 * w * math.cos(a), 0.34 * d * math.sin(a), 0.22 * h), "secondary", "secondary", corner_ratio=0.18))
            o[-1].rotation_euler.z = a
            o.append(add_box(ctx, collection, asset_id, state_id, f"HaloBridge_{angle}", (0.09 * w, 0.09 * d, 0.20 * h), (0.30 * w * math.cos(a), 0.30 * d * math.sin(a), 0.64 * h), "accent", "secondary", rotation=(0, 0, a), bevel_ratio=bevel, bevel_segments=1))
        halo_segment_count = 4 if state_id == "intact" else (3 if state_id == "damaged" else 2)
        halo_role = "accent" if state_id == "intact" else ("warning" if state_id == "damaged" else "critical")
        for index in range(halo_segment_count):
            start = 8.0 + index * 90.0
            o.append(add_arc_band(ctx, collection, asset_id, state_id, f"HaloSegment_{index}", 0.31 * w, 0.39 * w, 0.055 * h, start, start + 68.0, (0, 0, 0.65 * h), halo_role, "secondary", segments=5))
        top_cap = add_cylinder(ctx, collection, asset_id, state_id, "TopCap", 0.24 * w, 0.10 * h, (0, 0, 0.82 * h), "primary", "secondary", vertices=12, bevel_ratio=bevel)
        if state_id != "intact":
            top_cap.location.x += (0.035 if state_id == "damaged" else 0.10) * w
            top_cap.location.z += (0.012 if state_id == "damaged" else -0.055) * h
            top_cap.rotation_euler.y = math.radians(9 if state_id == "damaged" else 24)
            detached_bridge = _named(o, "HaloBridge_0")
            detached_bridge.location.x += (0.10 if state_id == "damaged" else 0.16) * w
            detached_bridge.location.z += (0.055 if state_id == "damaged" else 0.11) * h
            detached_bridge.rotation_euler.y = math.radians(16 if state_id == "damaged" else 31)
            if state_id == "critical":
                collapsed_bridge = _named(o, "HaloBridge_90")
                collapsed_bridge.location.y += 0.11 * d
                collapsed_bridge.location.z -= 0.13 * h
                collapsed_bridge.rotation_euler.x = math.radians(24)
        o.append(top_cap)
    elif asset_id == "enemy_standard":
        o.append(add_box(ctx, collection, asset_id, state_id, "HipStage", (0.50 * w, 0.46 * d, 0.10 * h), (0, 0, 0.31 * h), "secondary", "secondary", bevel_ratio=bevel, bevel_segments=1))
        o.append(add_box(ctx, collection, asset_id, state_id, "ForwardWedgeTorso", (0.68 * w, 0.60 * d, 0.34 * h), (0, -0.02 * d, 0.58 * h), "threat", "primary", rotation=(math.radians(-3), 0, 0), bevel_ratio=bevel, bevel_segments=2))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "SemanticChestPanel", (0.47 * w, 0.05 * d, 0.20 * h), (0, -0.34 * d, 0.58 * h), "secondary", "secondary", corner_ratio=0.15))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "CenterWedgeCore", 0.07 * w, 0.06 * d, (0, -0.38 * d, 0.60 * h), "critical" if state_id == "critical" else "interaction", "secondary", vertices=8, rotation=(math.radians(90), 0, 0), bevel_ratio=0.0))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "FacetedHead", 0.25 * w, 0.20 * h, (0, -0.03 * d, 0.88 * h), "primary", "primary", vertices=8, bevel_ratio=bevel))
        o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, "CleanVisor", (0.34 * w, 0.05 * d, 0.07 * h), (0, -0.29 * d, 0.89 * h), "warning" if state_id == "damaged" else ("critical" if state_id == "critical" else "interaction"), "secondary", corner_ratio=0.24))
        o.append(add_box(ctx, collection, asset_id, state_id, "HeadCrown", (0.32 * w, 0.34 * d, 0.055 * h), (0, -0.02 * d, 0.985 * h), "accent", "tertiary", bevel_ratio=bevel, bevel_segments=1))
        for side in (-1, 1):
            detach = side == 1 and state_id != "intact"
            drop = (0.06 if state_id == "damaged" else 0.15) * h if detach else 0.0
            zrot = (-9 if state_id == "damaged" else -20) if detach else side * 2
            o.append(add_box(ctx, collection, asset_id, state_id, f"PairedShoulder_{side}", (0.22 * w, 0.55 * d, 0.14 * h), (side * 0.41 * w, 0, 0.67 * h - drop), "accent", "secondary", rotation=(0, 0, math.radians(zrot)), bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"PairedHand_{side}", (0.25 * w, 0.31 * d, 0.24 * h), (side * 0.45 * w, -0.06 * d, 0.45 * h - drop), "threat", "primary", rotation=(0, math.radians(side * 4), math.radians(zrot)), bevel_ratio=bevel, bevel_segments=2))
            o.append(add_box(ctx, collection, asset_id, state_id, f"PairedShin_{side}", (0.21 * w, 0.25 * d, 0.28 * h), (side * 0.19 * w, 0, 0.18 * h), "primary", "secondary", bevel_ratio=bevel, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"PairedBoot_{side}", (0.25 * w, 0.40 * d, 0.10 * h), (side * 0.19 * w, -0.06 * d, 0.05 * h), "rubber", "secondary", bevel_ratio=bevel, bevel_segments=1))
            o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, f"HandInset_{side}", (0.15 * w, 0.035 * d, 0.10 * h), (side * 0.45 * w, -0.225 * d, 0.45 * h - drop), "secondary", "tertiary", corner_ratio=0.20))
            o.append(add_cylinder(ctx, collection, asset_id, state_id, f"ShoulderLight_{side}", 0.045 * w, 0.045 * d, (side * 0.41 * w, -0.30 * d, 0.67 * h - drop), "interaction" if state_id == "intact" else ("warning" if state_id == "damaged" else "critical"), "tertiary", vertices=8, rotation=(math.radians(90), 0, 0), bevel_ratio=0.0))
            o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, f"ShinGuard_{side}", (0.14 * w, 0.035 * d, 0.11 * h), (side * 0.19 * w, -0.145 * d, 0.20 * h), "accent", "tertiary", corner_ratio=0.18))
        if state_id == "critical":
            panel = _named(o, "SemanticChestPanel")
            panel.rotation_euler.x = math.radians(-26)
            panel.location.y -= 0.10 * d
            panel.location.z -= 0.04 * h
    elif asset_id == "floor_module":
        o.append(add_box(ctx, collection, asset_id, state_id, "Tile", (w, d, 0.58 * h), (0, 0, 0.29 * h), "rubber", "primary", bevel_ratio=bevel, bevel_segments=1))
        o.append(add_box(ctx, collection, asset_id, state_id, "TileSurface", (0.90 * w, 0.90 * d, 0.13 * h), (0, 0, 0.68 * h), "primary", "primary", bevel_ratio=bevel, bevel_segments=1))
        o.append(add_cylinder(ctx, collection, asset_id, state_id, "CenterHex", 0.27 * w, 0.15 * h, (0, 0, 0.84 * h), "warning" if state_id == "damaged" else "accent", "secondary", vertices=6, bevel_ratio=bevel))
        for index, (x, y) in enumerate(((0.43 * w, 0), (-0.43 * w, 0), (0, 0.43 * d), (0, -0.43 * d))):
            o.append(add_box(ctx, collection, asset_id, state_id, f"EdgeKey_{index}", (0.12 * w, 0.12 * d, 0.15 * h), (x, y, 0.83 * h), "secondary", "tertiary", bevel_ratio=0.0, bevel_segments=1))
        for side in (-1, 1):
            o.append(add_box(ctx, collection, asset_id, state_id, f"TileLineX_{side}", (0.54 * w, 0.018 * d, 0.025 * h), (0, side * 0.22 * d, 0.91 * h), "bareMetal", "tertiary", bevel_ratio=0.0, bevel_segments=1))
            o.append(add_box(ctx, collection, asset_id, state_id, f"TileLineY_{side}", (0.018 * w, 0.54 * d, 0.025 * h), (side * 0.22 * w, 0, 0.91 * h), "bareMetal", "tertiary", bevel_ratio=0.0, bevel_segments=1))
        for index, (x, y) in enumerate(((-0.31, -0.31), (0.31, -0.31), (0.31, 0.31), (-0.31, 0.31))):
            o.append(add_chamfered_panel(ctx, collection, asset_id, state_id, f"CornerFacet_{index}", (0.20 * w, 0.20 * d, 0.08 * h), (x * w, y * d, 0.87 * h), "secondary", "secondary", corner_ratio=0.18))
        if state_id == "damaged":
            ejected_key = _named(o, "EdgeKey_0")
            ejected_key.location.x += 0.13 * w
            ejected_key.location.z += 0.10 * h
            ejected_key.rotation_euler.y = math.radians(18)
            lifted_facet = _named(o, "CornerFacet_1")
            lifted_facet.location.z += 0.08 * h
            lifted_facet.rotation_euler.x = math.radians(-12)
    else:
        severity = 1.0 if state_id == "damaged" else 1.16
        o.append(add_wedge(ctx, collection, asset_id, state_id, "CleanDirectionCone", (0.70 * w * severity, 0.58 * d, 0.60 * h * severity), (0, 0, 0), "critical", "primary", rotation=(0, math.radians(15), 0)))
        o.append(add_torus(ctx, collection, asset_id, state_id, "CleanImpactRing", 0.27 * w * severity, 0.028 * w, (0, 0, 0), "warning", "secondary", rotation=(math.radians(90), 0, 0), major_segments=8, minor_segments=3))
        for side in (-1, 1):
            o.append(add_box(ctx, collection, asset_id, state_id, "PairedFragment", (0.14 * w, 0.10 * d, 0.15 * h), (side * 0.33 * w, 0.16 * d, 0.12 * h), "warning", "secondary", rotation=(side * 0.25, 0.15, side * 0.35), bevel_ratio=0.0))
        if state_id == "critical":
            o.append(add_wedge(ctx, collection, asset_id, state_id, "CriticalPlane", (0.38 * w, 0.28 * d, 0.44 * h), (0, 0, 0), "critical", "secondary", rotation=(math.radians(20), math.radians(-18), math.radians(30))))
    return o


def _named(objects: Iterable[bpy.types.Object], name: str) -> bpy.types.Object:
    # Blender adds .001-style suffixes because all state variants coexist in
    # one file. The requested base name remains the stable semantic part ID.
    found = next((obj for obj in objects if obj.name == name or obj.name.startswith(name + ".")), None)
    if found is None:
        raise RuntimeError(f"State language expected named geometry: {name}")
    return found


def _named_group(objects: Iterable[bpy.types.Object], names: Iterable[str]) -> list[bpy.types.Object]:
    """Return every mesh whose Blender-unique name retains a semantic base name."""
    requested = tuple(names)
    found = [
        obj
        for obj in objects
        if any(obj.name == name or obj.name.startswith(name + ".") or obj.name.startswith(name + "_") for name in requested)
    ]
    if not found:
        raise RuntimeError(f"State language expected named geometry group: {', '.join(requested)}")
    return found


def _transform_group(
    objects: Iterable[bpy.types.Object],
    pivot: Vector,
    translation: Vector,
    rotation_x: float = 0.0,
    rotation_z: float = 0.0,
) -> None:
    """Apply one deterministic rigid world transform to a semantic mesh assembly."""
    rotation = Matrix.Rotation(rotation_z, 4, "Z") @ Matrix.Rotation(rotation_x, 4, "X")
    transform = (
        Matrix.Translation(translation)
        @ Matrix.Translation(pivot)
        @ rotation
        @ Matrix.Translation(-pivot)
    )
    for obj in objects:
        obj.matrix_world = transform @ obj.matrix_world
    bpy.context.view_layer.update()


def _retag_material(ctx: BuildContext, obj: bpy.types.Object, role: str) -> None:
    obj.data.materials.clear()
    obj.data.materials.append(ctx.materials[f"beauty:{role}"])
    obj["art_role"] = role
    obj["art_original_material"] = obj.data.materials[0].name


def apply_industrial_state_language(
    ctx: BuildContext,
    collection: bpy.types.Collection,
    asset_id: str,
    state_id: str,
    dims: dict[str, float],
    objects: list[bpy.types.Object],
    bevel: float,
) -> bool:
    if ctx.territory["territoryId"] != "industrial-toy-defense":
        return False
    if state_id == "intact":
        return True
    w, d, h = dims["width"], dims["depth"], dims["height"]
    if asset_id == "barricade":
        center_panel = _named_group(
            objects,
            ("Panel_1", "PanelInset_1", "PanelGroove_1", "PanelSocket_1", "PanelLatch_1"),
        )
        _transform_group(
            center_panel,
            Vector((0.0, -0.08 * d, 0.54 * h)),
            Vector(
                (
                    (0.025 if state_id == "damaged" else 0.065) * w,
                    (0.02 if state_id == "damaged" else 0.18) * d,
                    -(0.045 if state_id == "damaged" else 0.16) * h,
                )
            ),
            rotation_x=0.0 if state_id == "damaged" else math.radians(18),
            rotation_z=math.radians(5 if state_id == "damaged" else 10),
        )
        bent_guard = _named(objects, "PostGuard_1")
        bent_guard.location.x += (0.045 if state_id == "damaged" else 0.11) * w
        bent_guard.location.z -= (0.025 if state_id == "damaged" else 0.065) * h
        bent_guard.rotation_euler.z -= math.radians(11 if state_id == "damaged" else 24)
        if state_id == "damaged":
            _retag_material(ctx, _named(objects, "PanelSocket_1"), "warning")
            reinforcement = add_box(
                ctx, collection, asset_id, state_id, "DamageReinforcement",
                (0.055 * w, 0.11 * d, 0.34 * h), (0.13 * w, 0.02 * d, 0.53 * h),
                "bareMetal", "secondary", rotation=(0, 0, math.radians(-18)),
                bevel_ratio=0.025, bevel_segments=1,
            )
            objects.append(reinforcement)
        else:
            _named(objects, "TopRail").rotation_euler.z -= math.radians(2.5)
            for side in (-1, 1):
                brace = add_box(
                    ctx, collection, asset_id, state_id, f"ExposedCrossBrace_{side}",
                    (0.055 * w, 0.09 * d, 0.55 * h), (side * 0.13 * w, 0.04 * d, 0.52 * h),
                    "bareMetal", "secondary", rotation=(0, 0, math.radians(side * 34)),
                    bevel_ratio=0.02, bevel_segments=1,
                )
                objects.append(brace)
            _retag_material(ctx, _named(objects, "InteractionLens"), "critical")
        return True

    if asset_id == "objective_core":
        _transform_group(
            _named_group(objects, ("Ring_1", "CrownArc")),
            Vector((0, 0, 0.76 * h)),
            Vector(((0.025 if state_id == "damaged" else 0.075) * w, 0, 0)),
            rotation_x=math.radians(8 if state_id == "damaged" else 20),
        )
        if state_id == "damaged":
            _retag_material(ctx, _named(objects, "ServiceLatch_270"), "warning")
            fin = add_box(
                ctx, collection, asset_id, state_id, "OpenedShieldFin_1",
                (0.075 * w, 0.08 * d, 0.24 * h), (0.24 * w, -0.20 * d, 0.60 * h),
                "warning", "secondary", rotation=(0, math.radians(14), math.radians(6)),
                bevel_ratio=0.025, bevel_segments=1,
            )
            objects.append(fin)
        else:
            upper_guard = _named(objects, "UpperGuard")
            upper_guard.rotation_euler.y += math.radians(12)
            upper_guard.location.z += 0.025 * h
            _retag_material(ctx, _named(objects, "Core"), "critical")
            for side in (-1, 1):
                fin = add_box(
                    ctx, collection, asset_id, state_id, f"OpenedShieldFin_{side}",
                    (0.075 * w, 0.08 * d, 0.28 * h), (side * 0.24 * w, -0.20 * d, 0.60 * h),
                    "warning", "secondary", rotation=(0, math.radians(side * 18), math.radians(side * 8)),
                    bevel_ratio=0.025, bevel_segments=1,
                )
                objects.append(fin)
        return True

    if asset_id == "enemy_standard":
        dropped_side = 1
        arm_group = _named_group(
            objects,
            (
                f"ShoulderGuard_{dropped_side}",
                f"UpperArm_{dropped_side}",
                f"Forearm_{dropped_side}",
                f"Fist_{dropped_side}",
                f"ForearmInset_{dropped_side}",
                f"ShoulderSocket_{dropped_side}",
            ),
        )
        _transform_group(
            arm_group,
            Vector((0.42 * w, 0.0, 0.67 * h)),
            Vector((0.015 * w, 0.02 * d, -(0.07 if state_id == "damaged" else 0.14) * h)),
            rotation_x=math.radians(4 if state_id == "damaged" else 10),
            rotation_z=math.radians(-12 if state_id == "damaged" else -24),
        )
        if state_id == "damaged":
            _retag_material(ctx, _named(objects, "Visor"), "warning")
            scar = add_box(
                ctx, collection, asset_id, state_id, "ChestScar",
                (0.04 * w, 0.025 * d, 0.16 * h), (0.11 * w, -0.37 * d, 0.60 * h),
                "bareMetal", "tertiary", rotation=(0, math.radians(12), math.radians(-14)),
                bevel_ratio=0.01, bevel_segments=1,
            )
            objects.append(scar)
        else:
            chest_group = _named_group(objects, ("ChestPanel", "ChestChevron"))
            _transform_group(
                chest_group,
                Vector((0.0, -0.325 * d, 0.59 * h)),
                Vector((0.0, -0.11 * d, -0.035 * h)),
                rotation_x=math.radians(-28),
                rotation_z=math.radians(4),
            )
            _retag_material(ctx, _named(objects, "ChestCore"), "critical")
            _transform_group(
                _named_group(objects, ("HeadShell", "Visor", "HelmetBrow")),
                Vector((0.0, 0.0, 0.785 * h)),
                Vector((0.025 * w, 0.0, -0.025 * h)),
                rotation_z=math.radians(9),
            )
            for side in (-1, 1):
                rib = add_box(
                    ctx, collection, asset_id, state_id, f"ExposedChestRib_{side}",
                    (0.035 * w, 0.055 * d, 0.17 * h), (side * 0.11 * w, -0.34 * d, 0.60 * h),
                    "bareMetal", "secondary", rotation=(0, 0, math.radians(side * 7)),
                    bevel_ratio=0.02, bevel_segments=1,
                )
                objects.append(rib)
        return True

    if asset_id == "floor_module":
        broken_corner = _named_group(objects, ("CornerLock_3",))
        _transform_group(
            broken_corner,
            Vector((0.39 * w, -0.39 * d, 0.90 * h)),
            Vector((0.06 * w, -0.05 * d, -0.06 * h)),
            rotation_x=math.radians(14),
            rotation_z=math.radians(18),
        )
        for index, (x, y, rz) in enumerate(((0.19, -0.11, 38), (0.28, -0.23, 57), (0.08, -0.26, 24))):
            crack = add_box(
                ctx, collection, asset_id, state_id, f"DeckCrack_{index}",
                (0.018 * w, 0.16 * d, 0.025 * h), (x * w, y * d, 0.975 * h),
                "rubber", "tertiary", rotation=(0, 0, math.radians(rz)),
                bevel_ratio=0.0, bevel_segments=1,
            )
            objects.append(crack)
        _retag_material(ctx, _named(objects, "CenterMark"), "warning")
        return True

    if asset_id == "damage_effect":
        return True

    return False


def apply_state_language(ctx: BuildContext, collection: bpy.types.Collection, asset_id: str, state_id: str, dims: dict[str, float], objects: list[bpy.types.Object], bevel: float) -> None:
    if apply_industrial_state_language(ctx, collection, asset_id, state_id, dims, objects, bevel):
        return
    # Salvaged and clean territory compilers build their damage semantics into
    # the assemblies themselves so state cues remain structural and art-directed.
    if ctx.territory["territoryId"] in {"salvaged-frontier", "clean-tactical-diorama"}:
        return
    if state_id == "intact" or asset_id == "damage_effect":
        return
    w, d, h = dims["width"], dims["depth"], dims["height"]
    strategy_id = ctx.territory["assetRecipes"][asset_id]["stateBreakStrategy"]
    profile = STATE_STRATEGY_PROFILES[strategy_id]
    targets = [
        next((obj for obj in objects if token.lower() in obj.name.lower()), None)
        for token in profile["targets"]
    ]
    targets = [obj for obj in targets if obj is not None]
    if not targets:
        raise RuntimeError(f"{asset_id}/{state_id}: state strategy {strategy_id} matched no geometry")
    angle = math.radians(8 if state_id == "damaged" else 16)
    axis = str(profile["axis"]).lower()
    setattr(targets[0].rotation_euler, axis, getattr(targets[0].rotation_euler, axis) + angle)
    targets[0].location.x += (0.025 if state_id == "damaged" else 0.055) * w
    cue_role = "warning" if state_id == "damaged" else "critical"
    cue = add_wedge(ctx, collection, asset_id, state_id, f"StateCue_{state_id}", (0.18 * w, 0.18 * d, 0.28 * h), (0.34 * w, -0.32 * d, 0.56 * h), cue_role, "secondary", rotation=(0, math.radians(12), math.radians(-18)))
    objects.append(cue)
    if state_id == "critical":
        exposed = add_sphere(ctx, collection, asset_id, state_id, "ExposedCriticalCore", 0.11 * min(w, h), (-0.08 * w, -0.36 * d, 0.52 * h), "critical", "secondary")
        objects.append(exposed)
        if len(targets) > 1:
            targets[1].rotation_euler.x += math.radians(18)
            targets[1].location.z -= 0.05 * h


def bake_world_transforms(objects: Iterable[bpy.types.Object]) -> None:
    bpy.context.view_layer.update()
    for obj in objects:
        if obj.type != "MESH":
            continue
        matrix = obj.matrix_world.copy()
        obj.data.transform(matrix)
        obj.matrix_world = Matrix.Identity(4)
        obj.parent = None
        obj.data.update()


def mesh_bounds(objects: Iterable[bpy.types.Object]) -> tuple[Vector, Vector]:
    points: list[Vector] = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        points.extend(obj.matrix_world @ vertex.co for vertex in obj.data.vertices)
    if not points:
        raise RuntimeError("Asset variant contains no mesh vertices.")
    minimum = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maximum = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return minimum, maximum


def normalize_bounds(variant: AssetVariant, reference_scale: Vector | None = None) -> Vector:
    bake_world_transforms(variant.objects)
    minimum, maximum = mesh_bounds(variant.objects)
    current = maximum - minimum
    if min(current) <= 1e-9:
        raise RuntimeError(f"{variant.asset_id}/{variant.state_id}: zero-size bounds {tuple(current)}")
    target = Vector((variant.target_dimensions["width"], variant.target_dimensions["depth"], variant.target_dimensions["height"]))
    scale = reference_scale.copy() if reference_scale is not None else Vector((target.x / current.x, target.y / current.y, target.z / current.z))
    if reference_scale is not None:
        scaled = Vector((current.x * scale.x, current.y * scale.y, current.z * scale.z))
        # Damage may rotate or detach a module beyond the intact envelope. Fit
        # the whole state uniformly so proportions remain intact; never apply a
        # second per-axis stretch to damaged/critical geometry.
        uniform_fit = min(1.0, target.x / scaled.x, target.y / scaled.y, target.z / scaled.z)
        scale *= uniform_fit
    center = (minimum + maximum) * 0.5
    for obj in variant.objects:
        if obj.type != "MESH":
            continue
        for vertex in obj.data.vertices:
            world = vertex.co.copy()
            if variant.pivot in {"bottom_center", "feet_center"}:
                vertex.co = Vector(((world.x - center.x) * scale.x, (world.y - center.y) * scale.y, (world.z - minimum.z) * scale.z))
            elif variant.pivot == "impact_center":
                vertex.co = Vector(((world.x - center.x) * scale.x, (world.y - center.y) * scale.y, (world.z - center.z) * scale.z))
            else:
                raise RuntimeError(f"Unsupported pivot contract: {variant.pivot}")
        obj.data.update()
        obj.parent = variant.root
    return scale


def quantize_mesh_coordinates(objects: Iterable[bpy.types.Object], decimals: int = 6) -> None:
    """Remove sub-micro-unit modifier/UV jitter before validation and GLB export."""
    for obj in objects:
        if obj.type != "MESH":
            continue
        for vertex in obj.data.vertices:
            vertex.co = Vector(tuple(round(float(component), decimals) for component in vertex.co))
        for layer in obj.data.uv_layers:
            for loop in layer.data:
                loop.uv = tuple(round(float(component), 4) for component in loop.uv)
        obj.data.update()


def validate_variant(variant: AssetVariant, calibration: dict[str, Any]) -> dict[str, Any]:
    minimum, maximum = mesh_bounds(variant.objects)
    dimensions = maximum - minimum
    target = Vector((variant.target_dimensions["width"], variant.target_dimensions["depth"], variant.target_dimensions["height"]))
    dim_tol = calibration["sharedRules"]["dimensionToleranceStuds"]
    pivot_tol = calibration["sharedRules"]["pivotToleranceStuds"]
    issues: list[str] = []
    reference_state = calibration["assets"][variant.asset_id]["requiredStateVariants"][0]
    if variant.state_id == reference_state:
        if any(abs(dimensions[i] - target[i]) > dim_tol for i in range(3)):
            issues.append(f"reference bounds {tuple(round(v, 6) for v in dimensions)} != target {tuple(target)}")
    else:
        for index, axis in enumerate(("width", "depth", "height")):
            if dimensions[index] > target[index] + 0.25:
                issues.append(f"{axis} exceeds reference envelope: {dimensions[index]:.6f} > {target[index]:.6f}")
            if dimensions[index] < target[index] * 0.55:
                issues.append(f"{axis} retains less than 55% of reference envelope")
    center = (minimum + maximum) * 0.5
    if variant.pivot in {"bottom_center", "feet_center"}:
        if abs(minimum.z) > pivot_tol or abs(center.x) > pivot_tol or abs(center.y) > pivot_tol:
            issues.append(f"pivot mismatch minZ={minimum.z:.6f} centerXY=({center.x:.6f},{center.y:.6f})")
    else:
        if max(abs(center.x), abs(center.y), abs(center.z)) > pivot_tol:
            issues.append(f"impact-center mismatch center={tuple(round(v, 6) for v in center)}")

    triangles = 0
    material_slots_max = 0
    uv_layers_max = 0
    non_manifold_edges = 0
    nonzero_volume = True
    uv_out_of_range = 0
    for obj in variant.objects:
        mesh = obj.data
        mesh.calc_loop_triangles()
        triangles += len(mesh.loop_triangles)
        material_slots_max = max(material_slots_max, len(mesh.materials))
        uv_layers_max = max(uv_layers_max, len(mesh.uv_layers))
        bm = bmesh.new()
        bm.from_mesh(mesh)
        non_manifold_edges += sum(1 for edge in bm.edges if not edge.is_manifold)
        try:
            volume = abs(bm.calc_volume(signed=False))
        except ValueError:
            volume = 0.0
        nonzero_volume &= volume > 1e-9
        bm.free()
        for layer in mesh.uv_layers:
            for loop in layer.data:
                if not (-1e-6 <= loop.uv.x <= 1.0 + 1e-6 and -1e-6 <= loop.uv.y <= 1.0 + 1e-6):
                    uv_out_of_range += 1
    if triangles > variant.triangle_budget:
        issues.append(f"triangles {triangles} exceed budget {variant.triangle_budget}")
    if material_slots_max > calibration["sharedRules"]["materialSlotsMaxPerMesh"]:
        issues.append(f"material slots per mesh exceed {calibration['sharedRules']['materialSlotsMaxPerMesh']}")
    if uv_layers_max > calibration["sharedRules"]["uvSetsMaxPerMesh"]:
        issues.append(f"UV sets per mesh exceed {calibration['sharedRules']['uvSetsMaxPerMesh']}")
    if non_manifold_edges:
        issues.append(f"non-manifold edges: {non_manifold_edges}")
    if not nonzero_volume:
        issues.append("one or more mesh objects has zero volume")
    if uv_out_of_range:
        issues.append(f"UV loop coordinates outside 0-1: {uv_out_of_range}")
    return {
        "assetId": variant.asset_id,
        "stateId": variant.state_id,
        "status": "PASS" if not issues else "FAIL",
        "boundsBlenderXYZ": {"width": dimensions.x, "depth": dimensions.y, "height": dimensions.z},
        "boundsMin": list(minimum),
        "boundsMax": list(maximum),
        "pivot": variant.pivot,
        "triangles": triangles,
        "triangleBudget": variant.triangle_budget,
        "meshObjectCount": len(variant.objects),
        "materialSlotsMaxPerMesh": material_slots_max,
        "uvLayersMaxPerMesh": uv_layers_max,
        "nonManifoldEdges": non_manifold_edges,
        "nonzeroVolume": nonzero_volume,
        "uvOutOfRange": uv_out_of_range,
        "issues": issues,
    }


def build_variant(ctx: BuildContext, asset_id: str, state_id: str) -> AssetVariant:
    spec = ctx.calibration["assets"][asset_id]
    recipe = ctx.territory["assetRecipes"][asset_id]
    collection = bpy.data.collections.new(f"C_{ctx.territory['territoryId']}__{asset_id}__{state_id}")
    bpy.context.scene.collection.children.link(collection)
    root = bpy.data.objects.new(f"ROOT_{asset_id}__{state_id}", None)
    collection.objects.link(root)
    root["ArtTerritory"] = ctx.territory["territoryId"]
    root["ArtAssetId"] = asset_id
    root["ArtState"] = state_id
    dims = spec["dimensions"]
    bevel = float(recipe["bevelRatioTarget"])
    tid = ctx.territory["territoryId"]
    if tid == "industrial-toy-defense":
        objects = build_industrial(ctx, collection, asset_id, state_id, dims, bevel)
    elif tid == "salvaged-frontier":
        objects = build_salvaged(ctx, collection, asset_id, state_id, dims, bevel)
    elif tid == "clean-tactical-diorama":
        objects = build_clean(ctx, collection, asset_id, state_id, dims, bevel)
    else:
        raise RuntimeError(f"Unsupported territory: {tid}")
    apply_state_language(ctx, collection, asset_id, state_id, dims, objects, bevel)
    variant = AssetVariant(asset_id, state_id, root, collection, objects, dims, spec["pivot"], spec["triangleBudgetMax"])
    reference_state = spec["requiredStateVariants"][0]
    reference_scale = ctx.normalization_scales.get(asset_id)
    if state_id != reference_state and reference_scale is None:
        raise RuntimeError(f"{asset_id}/{state_id}: reference state {reference_state} must be built first")
    scale = normalize_bounds(variant, reference_scale)
    quantize_mesh_coordinates(variant.objects)
    if state_id == reference_state:
        ctx.normalization_scales[asset_id] = scale
    variant.report = validate_variant(variant, ctx.calibration)
    collection.hide_render = True
    collection.hide_viewport = True
    return variant


def set_collection_visible(collection: bpy.types.Collection, visible: bool) -> None:
    collection.hide_render = not visible
    collection.hide_viewport = not visible


def select_variant(variant: AssetVariant) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    variant.root.select_set(True)
    for obj in variant.objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = variant.root


def canonicalize_glb(path: Path) -> None:
    """Canonicalize blockout UV precision and triangle order.

    Blender's exporter may emit topology-equivalent triangle orderings for a
    few beveled primitives. Sorting cyclically-normalized triangles makes the
    delivery artifact byte-stable while preserving each triangle's winding.
    """
    data = bytearray(path.read_bytes())
    if len(data) < 20 or data[:4] != b"glTF":
        raise RuntimeError(f"Invalid GLB header: {path}")
    json_length, json_type = struct.unpack_from("<II", data, 12)
    if json_type != 0x4E4F534A:
        raise RuntimeError(f"GLB first chunk is not JSON: {path}")
    document = json.loads(bytes(data[20 : 20 + json_length]).decode("utf-8"))
    binary_header = 20 + json_length
    binary_length, binary_type = struct.unpack_from("<II", data, binary_header)
    if binary_type != 0x004E4942:
        raise RuntimeError(f"GLB second chunk is not BIN: {path}")
    binary_start = binary_header + 8
    formats = {5121: ("B", 1), 5123: ("H", 2), 5125: ("I", 4)}
    index_accessors = {
        primitive["indices"]
        for mesh in document.get("meshes", [])
        for primitive in mesh.get("primitives", [])
        if "indices" in primitive and primitive.get("mode", 4) == 4
    }
    uv_accessors = {
        accessor_id
        for mesh in document.get("meshes", [])
        for primitive in mesh.get("primitives", [])
        for semantic, accessor_id in primitive.get("attributes", {}).items()
        if semantic.startswith("TEXCOORD_")
    }
    component_counts = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
    for accessor_id in sorted(uv_accessors):
        accessor = document["accessors"][accessor_id]
        if accessor["componentType"] != 5126:
            continue
        components = component_counts[accessor["type"]]
        view = document["bufferViews"][accessor["bufferView"]]
        stride = view.get("byteStride", components * 4)
        offset = binary_start + view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        for element in range(accessor["count"]):
            for component in range(components):
                at = offset + element * stride + component * 4
                value = struct.unpack_from("<f", data, at)[0]
                canonical = round(float(value), 3)
                if canonical == 0:
                    canonical = 0.0
                struct.pack_into("<f", data, at, canonical)
    for accessor_id in sorted(index_accessors):
        accessor = document["accessors"][accessor_id]
        component_type = accessor["componentType"]
        if component_type not in formats or accessor.get("type") != "SCALAR":
            raise RuntimeError(f"Unsupported GLB index accessor {accessor_id} in {path}")
        count = accessor["count"]
        if count % 3 != 0:
            raise RuntimeError(f"Triangle index count is not divisible by 3 in {path}")
        code, width = formats[component_type]
        view = document["bufferViews"][accessor["bufferView"]]
        offset = binary_start + view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        values = list(struct.unpack_from(f"<{count}{code}", data, offset))
        triangles: list[tuple[int, int, int]] = []
        for index in range(0, count, 3):
            triangle = values[index : index + 3]
            minimum_at = triangle.index(min(triangle))
            canonical = tuple(triangle[minimum_at:] + triangle[:minimum_at])
            triangles.append(canonical)
        triangles.sort()
        flattened = [value for triangle in triangles for value in triangle]
        struct.pack_into(f"<{count}{code}", data, offset, *flattened)
        if offset + count * width > binary_start + binary_length:
            raise RuntimeError(f"GLB index accessor escapes BIN chunk: {path}")
    path.write_bytes(data)


def prepare_role_merged_export(variant: AssetVariant) -> tuple[bpy.types.Collection, list[bpy.types.Object], list[str]]:
    """Create a temporary Studio-optimized mesh set with one MeshPart per material role.

    The editable .blend keeps semantic construction pieces. The delivery GLB joins
    disconnected closed pieces that share a semantic material, reducing Roblox
    instance cost without changing silhouette, UVs, material identity, or pivot.
    """
    export_collection = bpy.data.collections.new(f"EXPORT_{variant.asset_id}__{variant.state_id}")
    bpy.context.scene.collection.children.link(export_collection)
    by_role: dict[str, list[bpy.types.Object]] = {}
    for source in sorted(variant.objects, key=lambda item: item.name):
        if source.type != "MESH" or len(source.data.materials) != 1 or source.data.materials[0] is None:
            raise RuntimeError(f"{variant.asset_id}/{variant.state_id}: export source {source.name} must have exactly one material")
        material = source.data.materials[0]
        if not material.name.startswith("M_") or material.name.startswith("M_FLAT_"):
            raise RuntimeError(f"{variant.asset_id}/{variant.state_id}: non-semantic export material {material.name}")
        role = material.name.removeprefix("M_")
        duplicate = source.copy()
        duplicate.data = source.data.copy()
        duplicate.parent = None
        duplicate.matrix_world = source.matrix_world.copy()
        duplicate.data.transform(duplicate.matrix_world)
        duplicate.matrix_world = Matrix.Identity(4)
        export_collection.objects.link(duplicate)
        by_role.setdefault(role, []).append(duplicate)

    merged: list[bpy.types.Object] = []
    for role in sorted(by_role):
        objects = by_role[role]
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        if len(objects) > 1:
            bpy.ops.object.join()
        joined = objects[0]
        material = joined.data.materials[0]
        joined.data.materials.clear()
        joined.data.materials.append(material)
        for polygon in joined.data.polygons:
            polygon.material_index = 0
        joined.name = f"ROLE_{role}"
        joined.data.name = f"ROLE_{role}_Mesh"
        joined.data.update()
        merged.append(joined)
    return export_collection, merged, sorted(by_role)


def export_variant(ctx: BuildContext, variant: AssetVariant) -> dict[str, Any]:
    export_dir = ctx.output_dir / "exports" / variant.asset_id
    export_dir.mkdir(parents=True, exist_ok=True)
    path = export_dir / f"{variant.asset_id}__{variant.state_id}.glb"
    set_collection_visible(variant.collection, True)
    export_collection, export_objects, roles = prepare_role_merged_export(variant)
    scene = bpy.context.scene
    original_scene_name = scene.name
    upload_name = f"{ctx.territory['territoryId']}__{variant.asset_id}__{variant.state_id}"
    try:
        # Roblox Studio uses the glTF scene label as the import content/model
        # name. A stable, globally unique scene label is therefore part of the
        # delivery contract, not presentation-only metadata.
        scene.name = upload_name
        bpy.ops.object.select_all(action="DESELECT")
        for obj in export_objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = export_objects[0]
        bpy.ops.export_scene.gltf(
            filepath=str(path), export_format="GLB", use_selection=True,
            export_yup=True, export_cameras=False, export_lights=False,
        )
    finally:
        scene.name = original_scene_name
        for obj in list(export_collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(export_collection)
        set_collection_visible(variant.collection, False)
    if not path.exists() or path.stat().st_size == 0:
        raise RuntimeError(f"GLB exporter did not create a non-empty file: {path}")
    canonicalize_glb(path)
    return {
        "assetId": variant.asset_id,
        "stateId": variant.state_id,
        "path": path.relative_to(ctx.output_dir).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "meshCount": len(export_objects),
        "materialRoles": roles,
    }


def create_camera(scene: bpy.types.Scene, camera_rig: dict[str, Any]) -> bpy.types.Object:
    data = bpy.data.cameras.new("ArtValidationCamera")
    data.type = "PERSP"
    data.sensor_fit = "VERTICAL"
    data.sensor_height = 32.0
    fov = math.radians(camera_rig["fieldOfView"]["degrees"])
    data.lens = data.sensor_height / (2.0 * math.tan(fov / 2.0))
    camera = bpy.data.objects.new("ArtValidationCamera", data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    return camera


def look_at(obj: bpy.types.Object, target: Vector) -> None:
    direction = target - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def place_camera(camera: bpy.types.Object, spec: dict[str, float]) -> None:
    distance = spec["distanceStuds"]
    azimuth = math.radians(spec["azimuthDegrees"])
    elevation = math.radians(spec["elevationDegrees"])
    target = Vector((0.0, 0.0, spec["targetHeightStuds"]))
    horizontal = distance * math.cos(elevation)
    camera.location = Vector((horizontal * math.sin(azimuth), -horizontal * math.cos(azimuth), target.z + distance * math.sin(elevation)))
    look_at(camera, target)


def configure_world(scene: bpy.types.Scene, color_hex: str, strength: float = 0.8) -> None:
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    if not world.use_nodes:
        world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = hex_to_rgba(color_hex)
    background.inputs["Strength"].default_value = strength


def clear_lights() -> None:
    for obj in list(bpy.data.objects):
        if obj.type == "LIGHT":
            bpy.data.objects.remove(obj, do_unlink=True)


def configure_lighting(ctx: BuildContext, profile_id: str) -> None:
    clear_lights()
    profile = ctx.lighting_profiles["profiles"][profile_id]
    values = profile["scriptMutable"]["Lighting"]
    ambient = values["OutdoorAmbient"]
    ambient_hex = "#" + "".join(f"{int(channel):02X}" for channel in ambient)
    configure_world(bpy.context.scene, ambient_hex, max(0.15, min(1.5, values["EnvironmentDiffuseScale"] + 0.25)))
    light_data = bpy.data.lights.new(name=f"Sun_{profile_id}", type="SUN")
    light_data.energy = max(0.1, values["Brightness"] * 1.2)
    light_data.angle = math.radians(1.0 + values["ShadowSoftness"] * 9.0)
    sun = bpy.data.objects.new(name=f"Sun_{profile_id}", object_data=light_data)
    bpy.context.scene.collection.objects.link(sun)
    clock_angle = (values["ClockTime"] / 24.0) * math.tau
    sun.rotation_euler = (math.radians(35 + values["GeographicLatitude"] * 0.25), 0, clock_angle)
    area_data = bpy.data.lights.new(name=f"Fill_{profile_id}", type="AREA")
    area_data.energy = 250.0 * max(0.2, values["EnvironmentDiffuseScale"])
    area_data.shape = "DISK"
    area_data.size = 12.0
    area = bpy.data.objects.new(name=f"Fill_{profile_id}", object_data=area_data)
    bpy.context.scene.collection.objects.link(area)
    area.location = (4.0, -6.0, 9.0)
    look_at(area, Vector((0, 0, 2.5)))


def configure_review_lighting(ctx: BuildContext, target_height: float) -> None:
    """Neutral three-point studio lighting used only for art-quality review."""
    clear_lights()
    configure_world(bpy.context.scene, "#20252D", 0.56)
    target = Vector((0.0, 0.0, target_height * 0.48))
    lights = (
        ("ReviewKey", 920.0, 7.0, (-5.0, -7.0, target_height * 1.65), "#FFF2DF"),
        ("ReviewFill", 580.0, 6.0, (5.5, -3.5, target_height * 1.10), "#C9E1FF"),
        ("ReviewRim", 760.0, 5.0, (4.0, 5.0, target_height * 1.55), "#FFD3A3"),
    )
    for name, energy, size, location, color in lights:
        data = bpy.data.lights.new(name=name, type="AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        data.color = hex_to_rgba(color)[:3]
        data.use_shadow = name == "ReviewKey"
        obj = bpy.data.objects.new(name=name, object_data=data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = location
        look_at(obj, target)


def _review_camera_distance(variant: AssetVariant, aspect: float, occupancy: float = 0.68) -> float:
    vertical_fov = math.radians(70.0)
    horizontal_fov = 2.0 * math.atan(math.tan(vertical_fov / 2.0) * aspect)
    width = variant.target_dimensions["width"]
    height = variant.target_dimensions["height"]
    vertical_distance = height / (2.0 * math.tan(vertical_fov / 2.0) * occupancy)
    horizontal_distance = width / (2.0 * math.tan(horizontal_fov / 2.0) * min(0.80, occupancy + 0.08))
    return max(vertical_distance, horizontal_distance) * 1.12


def create_review_ground(ctx: BuildContext, asset_id: str, state_id: str) -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(size=40.0, location=(0, 0, -0.012))
    ground = bpy.context.object
    ground.name = f"ReviewGround_{asset_id}_{state_id}"
    material = bpy.data.materials.get("M_REVIEW_GROUND")
    if material is None:
        material = make_principled_material("M_REVIEW_GROUND", "#303640", roughness=0.82, metallic=0.0)
    ground.data.materials.append(material)
    return ground


def render_review_images(ctx: BuildContext, camera: bpy.types.Object) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    scene = bpy.context.scene
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 768
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    try:
        scene.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass
    for asset_id in ASSETS:
        for state_id in ctx.calibration["assets"][asset_id]["requiredStateVariants"]:
            variant = ctx.variants[(asset_id, state_id)]
            set_collection_visible(variant.collection, True)
            set_render_pass(ctx, variant, "beauty")
            distance = _review_camera_distance(variant, 1024 / 768)
            place_camera(
                camera,
                {
                    "distanceStuds": distance,
                    "azimuthDegrees": 38.0,
                    "elevationDegrees": 18.0,
                    "targetHeightStuds": variant.target_dimensions["height"] * 0.48,
                },
            )
            configure_review_lighting(ctx, variant.target_dimensions["height"])
            ground = create_review_ground(ctx, asset_id, state_id)
            relative = Path("renders") / "review" / f"{ctx.territory['territoryId']}__{asset_id}__{state_id}__hero.png"
            path = ctx.output_dir / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            scene.render.filepath = str(path)
            bpy.context.view_layer.update()
            bpy.ops.render.render(write_still=True)
            bpy.data.objects.remove(ground, do_unlink=True)
            set_collection_visible(variant.collection, False)
            if not path.is_file() or path.stat().st_size == 0:
                raise RuntimeError(f"Review render missing: {path}")
            output.append(
                {
                    "assetId": asset_id,
                    "stateId": state_id,
                    "cameraId": "dynamic_hero_three_quarter",
                    "resolution": {"width": 1024, "height": 768},
                    "targetOccupancy": 0.68,
                    "path": relative.as_posix(),
                    "sha256": sha256_file(path),
                }
            )
    return output


def background_color(ctx: BuildContext, background_id: str) -> str:
    return ctx.territory["blockoutPalette"]["secondary"] if background_id == "world_neutral_light" else ctx.territory["blockoutPalette"]["primary"]


def set_render_pass(ctx: BuildContext, variant: AssetVariant, pass_id: str) -> None:
    palette = ctx.territory["blockoutPalette"]
    for obj in variant.objects:
        obj.data.materials.clear()
        if pass_id == "beauty":
            key = f"beauty:{obj['art_role']}"
        elif pass_id == "flat_albedo":
            key = f"flat:{obj['art_role']}"
        elif pass_id == "silhouette":
            key = "pass:silhouette"
        elif pass_id == "detail_band":
            key = f"pass:{obj['art_detail_band']}"
        else:
            raise RuntimeError(f"Unknown render pass: {pass_id}")
        obj.data.materials.append(ctx.materials[key])


def render_matrix(ctx: BuildContext, camera: bpy.types.Object) -> list[dict[str, Any]]:
    if ctx.render_mode == "build-only":
        ctx.report["renderEvidenceComplete"] = False
        ctx.report["renderEvidenceCapped"] = False
        ctx.report["expectedRenderCount"] = 0
        ctx.report["actualRenderCount"] = 0
        return []
    mode = ctx.render_matrix["modes"][ctx.render_mode]
    resolutions = {r["id"]: r for r in ctx.camera_rig["resolutions"]}
    output: list[dict[str, Any]] = []
    emitted_paths: set[str] = set()
    count = 0
    ctx.report["expectedRenderCount"] = mode["expectedRenderCount"]
    for job in mode["jobs"]:
        for asset_id in job["assetIds"]:
            for state_id in job["stateIds"]:
                if state_id not in ctx.calibration["assets"][asset_id]["requiredStateVariants"]:
                    continue
                variant = ctx.variants[(asset_id, state_id)]
                set_collection_visible(variant.collection, True)
                for camera_id in job["cameraIds"]:
                    place_camera(camera, ctx.camera_rig["validationCameras"][camera_id])
                    for profile_id in job["lightingProfileIds"]:
                        configure_lighting(ctx, profile_id)
                        for background_id in job["backgroundIds"]:
                            configure_world(bpy.context.scene, background_color(ctx, background_id), 0.8)
                            for resolution_id in job["resolutionIds"]:
                                resolution = resolutions[resolution_id]
                                bpy.context.scene.render.resolution_x = resolution["width"]
                                bpy.context.scene.render.resolution_y = resolution["height"]
                                bpy.context.scene.render.resolution_percentage = 100
                                for pass_id in job["passIds"]:
                                    if ctx.max_renders is not None and count >= ctx.max_renders:
                                        set_collection_visible(variant.collection, False)
                                        ctx.report["renderEvidenceComplete"] = False
                                        ctx.report["renderEvidenceCapped"] = True
                                        ctx.report["actualRenderCount"] = count
                                        return output
                                    set_render_pass(ctx, variant, pass_id)
                                    relative = Path("renders") / ctx.render_mode / (
                                        f"{ctx.territory['territoryId']}__{asset_id}__{state_id}__{camera_id}__{profile_id}__{background_id}__{resolution_id}__{pass_id}.png"
                                    )
                                    relative_key = relative.as_posix()
                                    if relative_key in emitted_paths:
                                        raise RuntimeError(f"Render matrix emitted a duplicate case: {relative_key}")
                                    emitted_paths.add(relative_key)
                                    path = ctx.output_dir / relative
                                    path.parent.mkdir(parents=True, exist_ok=True)
                                    bpy.context.scene.render.filepath = str(path)
                                    bpy.ops.render.render(write_still=True)
                                    if not path.exists() or path.stat().st_size == 0:
                                        raise RuntimeError(f"Render missing: {path}")
                                    output.append({
                                        "jobId": job["jobId"],
                                        "assetId": asset_id,
                                        "stateId": state_id,
                                        "cameraId": camera_id,
                                        "lightingProfileId": profile_id,
                                        "backgroundId": background_id,
                                        "resolutionId": resolution_id,
                                        "passId": pass_id,
                                        "path": relative_key,
                                        "sha256": sha256_file(path),
                                    })
                                    count += 1
                set_collection_visible(variant.collection, False)
    ctx.report["renderEvidenceComplete"] = count == mode["expectedRenderCount"]
    ctx.report["renderEvidenceCapped"] = False
    ctx.report["actualRenderCount"] = count
    if not ctx.report["renderEvidenceComplete"]:
        raise RuntimeError(f"Render matrix count mismatch: {count} != {mode['expectedRenderCount']}")
    return output

def create_stress_render(ctx: BuildContext, camera: bpy.types.Object, asset_id: str, count: int = 30) -> dict[str, Any]:
    source = ctx.variants[(asset_id, "intact")]
    set_render_pass(ctx, source, "beauty")
    set_collection_visible(source.collection, True)
    instance_collection = bpy.data.collections.new(f"Stress_{asset_id}_{count}")
    bpy.context.scene.collection.children.link(instance_collection)
    columns = math.ceil(math.sqrt(count))
    spacing = max(source.target_dimensions["width"], source.target_dimensions["depth"]) * 1.35
    for index in range(count):
        row, col = divmod(index, columns)
        instance = bpy.data.objects.new(f"Instance_{asset_id}_{index:02d}", None)
        instance.instance_type = "COLLECTION"
        instance.instance_collection = source.collection
        instance.location = ((col - (columns - 1) / 2) * spacing, (row - (columns - 1) / 2) * spacing, 0)
        instance_collection.objects.link(instance)
    instance_collection.hide_render = False
    place_camera(camera, {"distanceStuds": 60.0, "azimuthDegrees": 35.0, "elevationDegrees": 25.0, "targetHeightStuds": 2.75})
    configure_lighting(ctx, "Lighting_Gameplay_Default")
    configure_world(bpy.context.scene, ctx.territory["blockoutPalette"]["secondary"], 0.8)
    bpy.context.scene.render.resolution_x = 640
    bpy.context.scene.render.resolution_y = 360
    path = ctx.output_dir / "renders" / ctx.render_mode / f"{ctx.territory['territoryId']}__stress_{asset_id}_{count}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    if not path.exists():
        raise RuntimeError(f"Stress render missing: {path}")
    bpy.data.collections.remove(instance_collection)
    set_collection_visible(source.collection, False)
    return {"sceneId": f"stress_{asset_id}_{count}", "count": count, "path": path.relative_to(ctx.output_dir).as_posix(), "sha256": sha256_file(path)}


def main() -> int:
    args = parse_args()
    input_paths = {
        "territory": args.territory_path,
        "calibration": args.calibration_path,
        "camera": args.camera_path,
        "renderMatrix": args.render_matrix_path,
        "lighting": args.lighting_path,
        "materials": args.material_rules_path,
        "generator": Path(__file__).resolve(),
    }
    missing = [str(path) for path in input_paths.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"Missing canonical input files: {missing}")
    if args.output.exists() and not args.no_clean_output:
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True, exist_ok=True)
    territory = load_json(args.territory_path)
    calibration = load_json(args.calibration_path)
    camera_rig = load_json(args.camera_path)
    render_spec = load_json(args.render_matrix_path)
    lighting = load_json(args.lighting_path)
    material_rules = load_json(args.material_rules_path)
    if territory["territoryId"] != args.territory:
        raise RuntimeError(f"Territory ID mismatch: CLI={args.territory}, file={territory['territoryId']}")
    seed = int(territory["automation"]["deterministicSeed"])
    random.seed(seed)
    clear_scene()
    scene = bpy.context.scene
    engine = choose_render_engine(scene)
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.frame_set(1)
    report: dict[str, Any] = {
        "$schema": SCHEMA_BUILD_REPORT,
        "schemaVersion": "3.0.0",
        "status": "PASS",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "territoryId": territory["territoryId"],
        "rendererTruth": "BLENDER_PREFLIGHT_ONLY_STUDIO_IS_CANONICAL",
        "renderMode": args.render_mode,
        "reviewRequested": bool(args.review_renders),
        "evidenceCompleteness": "PENDING",
        "toolchain": {
            "blenderVersion": bpy.app.version_string,
            "pythonVersion": sys.version,
            "renderEngine": engine,
            "deterministicSeed": seed,
            "generatorVersion": territory["automation"]["generatorVersion"],
        },
        "inputHashes": {name: sha256_file(path) for name, path in input_paths.items()},
        "cameraValidation": {},
        "assets": [],
        "exports": [],
        "renderEvidence": [],
        "stressEvidence": [],
        "reviewEvidence": [],
        "renderEvidenceComplete": False,
        "renderEvidenceCapped": False,
        "expectedRenderCount": 0,
        "actualRenderCount": 0,
        "issues": [],
        "notes": [],
    }
    ctx = BuildContext(territory, calibration, camera_rig, render_spec, lighting, material_rules, args.output, args.render_mode, args.max_renders, random.Random(seed), {}, {}, {}, report)
    ensure_materials(ctx)
    for asset_id in ASSETS:
        for state_id in calibration["assets"][asset_id]["requiredStateVariants"]:
            variant = build_variant(ctx, asset_id, state_id)
            ctx.variants[(asset_id, state_id)] = variant
            report["assets"].append(variant.report)
            if variant.report["status"] != "PASS":
                report["issues"].extend(f"{asset_id}/{state_id}: {issue}" for issue in variant.report["issues"])
    if report["issues"]:
        report["status"] = "FAIL"
        write_json(args.output / "build-report.json", report)
        raise RuntimeError("Post-build geometry gates failed; see build-report.json")

    camera = create_camera(scene, camera_rig)
    expected_fov = camera_rig["fieldOfView"]["degrees"]
    actual_fov = math.degrees(camera.data.angle_y)
    fov_tolerance = camera_rig["cameraValidation"]["verticalFovToleranceDegrees"]
    report["cameraValidation"] = {"expectedVerticalFovDegrees": expected_fov, "actualVerticalFovDegrees": actual_fov, "toleranceDegrees": fov_tolerance, "pass": abs(actual_fov - expected_fov) <= fov_tolerance}
    if not report["cameraValidation"]["pass"]:
        report["status"] = "FAIL"
        report["issues"].append("Blender camera vertical FOV readback mismatch")
        write_json(args.output / "build-report.json", report)
        raise RuntimeError("Camera FOV validation failed")

    for variant in ctx.variants.values():
        report["exports"].append(export_variant(ctx, variant))

    blend_path = args.output / f"{territory['territoryId']}__calibration.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    report["blendFile"] = {"path": blend_path.name, "sha256": sha256_file(blend_path)}
    report["renderEvidence"] = render_matrix(ctx, camera)
    if args.review_renders:
        report["reviewEvidence"] = render_review_images(ctx, camera)
    if args.render_mode != "build-only" and report["renderEvidenceComplete"]:
        for asset_id in ("barricade", "enemy_standard"):
            report["stressEvidence"].append(create_stress_render(ctx, camera, asset_id, 30))
    if report["renderEvidenceCapped"]:
        report["evidenceCompleteness"] = "PARTIAL_CAPPED"
        report["notes"].append("Render matrix was intentionally capped for debugging and cannot satisfy a visual-evidence gate.")
    elif args.render_mode == "build-only":
        report["evidenceCompleteness"] = "BUILD_ONLY"
        report["notes"].append("Geometry/export gates passed; no Blender render evidence was requested.")
    elif args.render_mode == "smoke":
        report["evidenceCompleteness"] = "SMOKE_COMPLETE"
        report["notes"].append("Smoke render suite is preview evidence only and cannot replace the full suite or Studio evidence.")
    else:
        report["evidenceCompleteness"] = "FULL_COMPLETE"
    write_json(args.output / "build-report.json", report)
    print(json.dumps({"status": report["status"], "territoryId": territory["territoryId"], "report": str(args.output / "build-report.json")}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        raise
