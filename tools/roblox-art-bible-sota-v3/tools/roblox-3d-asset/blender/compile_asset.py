from __future__ import annotations

import bmesh
import hashlib
import json
import math
import os
import subprocess
import sys
import traceback
from array import array
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector

TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

from pipeline.determinism import (
    RENDER_PIXEL_TOLERANCE,
    canonical_png_content_sha256,
    compare_png_render,
)
from pipeline.state_variants import resolve_state_variant


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def resolve_visual_canon_path(contract_path: Path, configured_path: str) -> Path:
    requested = Path(configured_path)
    if requested.is_absolute():
        return requested
    repo = contract_path.parents[2]
    candidates = [repo / requested]
    package_prefix = ("tools", "roblox-art-bible-sota-v3")
    if requested.parts[:2] == package_prefix:
        candidates.append(repo.joinpath(*requested.parts[2:]))
    else:
        candidates.append(repo.joinpath(*package_prefix, requested))
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return candidates[0]


def parse_arguments() -> tuple[Path, Path, str | None]:
    if "--" not in sys.argv:
        raise ValueError(
            "expected arguments after --: "
            "<contract.json> <output-directory> [state-id]"
        )
    arguments = sys.argv[sys.argv.index("--") + 1 :]
    if len(arguments) not in {2, 3}:
        raise ValueError(
            "expected two or three arguments: "
            "<contract.json> <output-directory> [state-id]"
        )
    return (
        Path(arguments[0]).resolve(),
        Path(arguments[1]).resolve(),
        arguments[2] if len(arguments) == 3 else None,
    )


def hex_color(value: str) -> tuple[float, float, float, float]:
    # Blender expects linear values. Convert the versioned sRGB palette explicitly.
    channels = [int(value[index : index + 2], 16) / 255.0 for index in (1, 3, 5)]

    def to_linear(channel: float) -> float:
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    return (to_linear(channels[0]), to_linear(channels[1]), to_linear(channels[2]), 1.0)


def reset_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(collection):
            if block.users == 0:
                collection.remove(block)


def create_materials(contract: dict) -> dict[str, bpy.types.Material]:
    result: dict[str, bpy.types.Material] = {}
    for specification in contract["materials"]:
        material = bpy.data.materials.new(specification["name"])
        material.diffuse_color = hex_color(specification["color"])
        material.use_nodes = True
        principled = material.node_tree.nodes.get("Principled BSDF")
        principled.inputs["Base Color"].default_value = material.diffuse_color
        principled.inputs["Metallic"].default_value = specification["metallic"]
        principled.inputs["Roughness"].default_value = specification["roughness"]
        emission_strength = float(specification.get("emissionStrength", 0.0))
        if emission_strength > 0:
            emission_color = hex_color(
                specification.get("emissionColor", specification["color"])
            )
            emission_input = principled.inputs.get("Emission Color")
            if emission_input is None:
                emission_input = principled.inputs.get("Emission")
            strength_input = principled.inputs.get("Emission Strength")
            if emission_input is not None:
                emission_input.default_value = emission_color
            if strength_input is not None:
                strength_input.default_value = emission_strength
        result[specification["name"]] = material
    return result


def design_position_to_blender(position: list[float]) -> tuple[float, float, float]:
    # Design/Roblox axes: X width, Y height, Z depth. Blender: X width, Y depth, Z height.
    return (position[0], position[2], position[1])


def design_size_to_blender(size: list[float]) -> tuple[float, float, float]:
    return (size[0], size[2], size[1])


def add_box(part: dict, material: bpy.types.Material) -> bpy.types.Object:
    bpy.ops.mesh.primitive_cube_add(location=design_position_to_blender(part["position"]))
    obj = bpy.context.object
    obj.name = part["name"]
    obj.data.name = part["name"] + "_Mesh"
    obj.dimensions = design_size_to_blender(part["size"])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    rotation = part.get("rotationDegrees", [0, 0, 0])
    # The vertical slice uses zero rotations. This mapping keeps Y as the design up axis.
    obj.rotation_euler = tuple(math.radians(value) for value in (rotation[0], rotation[2], rotation[1]))
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    bevel_width = float(part.get("bevel", 0.0))
    if bevel_width > 0:
        modifier = obj.modifiers.new(name="ControlledBevel", type="BEVEL")
        modifier.width = bevel_width
        modifier.segments = 1
        modifier.limit_method = "ANGLE"
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)

    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.uv.smart_project(island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    return obj


def add_chamfered_box(
    part: dict,
    material: bpy.types.Material,
) -> bpy.types.Object:
    width, height, depth = (float(value) for value in part["size"])
    chamfer = float(part["chamfer"])
    half_width = width / 2.0
    half_height = height / 2.0
    half_depth = depth / 2.0
    profile = [
        (-half_width + chamfer, -half_height),
        (half_width - chamfer, -half_height),
        (half_width, -half_height + chamfer),
        (half_width, half_height - chamfer),
        (half_width - chamfer, half_height),
        (-half_width + chamfer, half_height),
        (-half_width, half_height - chamfer),
        (-half_width, -half_height + chamfer),
    ]
    design_vertices = [
        (x, y, z)
        for z in (-half_depth, half_depth)
        for x, y in profile
    ]
    vertices = [design_position_to_blender(list(vertex)) for vertex in design_vertices]
    faces: list[tuple[int, ...]] = [
        tuple(reversed(range(8))),
        tuple(range(8, 16)),
    ]
    for index in range(8):
        next_index = (index + 1) % 8
        faces.append((index, next_index, next_index + 8, index + 8))

    mesh = bpy.data.meshes.new(part["name"] + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(part["name"], mesh)
    bpy.context.collection.objects.link(obj)
    obj.location = design_position_to_blender(part["position"])

    rotation = part.get("rotationDegrees", [0, 0, 0])
    obj.rotation_euler = tuple(
        math.radians(value) for value in (rotation[0], rotation[2], rotation[1])
    )
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    bevel_width = float(part.get("bevel", 0.0))
    if bevel_width > 0:
        modifier = obj.modifiers.new(name="ControlledBevel", type="BEVEL")
        modifier.width = bevel_width
        modifier.segments = 1
        modifier.limit_method = "ANGLE"
        bpy.ops.object.modifier_apply(modifier=modifier.name)

    obj.data.materials.append(material)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.uv.smart_project(island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    return obj


def add_cylinder(part: dict, material: bpy.types.Material) -> bpy.types.Object:
    segments = int(part.get("segments", 12))
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=segments,
        radius=0.5,
        depth=1.0,
        location=design_position_to_blender(part["position"]),
    )
    obj = bpy.context.object
    obj.name = part["name"]
    obj.data.name = part["name"] + "_Mesh"

    axis = part.get("axis", "Z")
    axis_rotation = {
        "X": (0.0, math.pi / 2.0, 0.0),
        "Y": (0.0, 0.0, 0.0),
        "Z": (math.pi / 2.0, 0.0, 0.0),
    }[axis]
    obj.rotation_euler = axis_rotation
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    obj.dimensions = design_size_to_blender(part["size"])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

    rotation = part.get("rotationDegrees", [0, 0, 0])
    obj.rotation_euler = tuple(
        math.radians(value) for value in (rotation[0], rotation[2], rotation[1])
    )
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    bevel_width = float(part.get("bevel", 0.0))
    if bevel_width > 0:
        modifier = obj.modifiers.new(name="ControlledBevel", type="BEVEL")
        modifier.width = bevel_width
        modifier.segments = 2
        modifier.limit_method = "ANGLE"
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=modifier.name)

    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.uv.smart_project(island_margin=0.02)
    bpy.ops.object.mode_set(mode="OBJECT")
    return obj


def add_part(part: dict, material: bpy.types.Material) -> bpy.types.Object:
    part_type = part["type"]
    if part_type == "box":
        return add_box(part, material)
    if part_type == "chamfered_box":
        return add_chamfered_box(part, material)
    if part_type == "cylinder":
        return add_cylinder(part, material)
    raise ValueError(f"Unsupported geometry part type: {part_type}")


def world_bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    minimum = Vector((min(point.x for point in points), min(point.y for point in points), min(point.z for point in points)))
    maximum = Vector((max(point.x for point in points), max(point.y for point in points), max(point.z for point in points)))
    return minimum, maximum


def validate_geometry(contract: dict, objects: list[bpy.types.Object]) -> dict:
    errors: list[str] = []
    object_reports: list[dict] = []
    total_triangles = 0
    for obj in objects:
        mesh = obj.data
        corrected = mesh.validate(verbose=False, clean_customdata=False)
        if corrected:
            errors.append(f"{obj.name}: Mesh.validate corrected invalid data")
        mesh.calc_loop_triangles()
        triangles = len(mesh.loop_triangles)
        total_triangles += triangles

        bm = bmesh.new()
        bm.from_mesh(mesh)
        non_manifold_edges = sum(1 for edge in bm.edges if not edge.is_manifold)
        loose_vertices = sum(1 for vertex in bm.verts if not vertex.link_faces)
        degenerate_faces = sum(1 for face in bm.faces if face.calc_area() <= 1e-10)
        bm.free()
        if non_manifold_edges:
            errors.append(f"{obj.name}: {non_manifold_edges} non-manifold edges")
        if loose_vertices:
            errors.append(f"{obj.name}: {loose_vertices} loose vertices")
        if degenerate_faces:
            errors.append(f"{obj.name}: {degenerate_faces} degenerate faces")
        if len(mesh.materials) != 1:
            errors.append(f"{obj.name}: expected exactly one material slot")
        if not mesh.uv_layers:
            errors.append(f"{obj.name}: missing UV layer")
            uv_outside = None
        else:
            uv_values = [loop.uv for loop in mesh.uv_layers.active.data]
            uv_outside = sum(
                1
                for uv in uv_values
                if uv.x < -1e-6 or uv.x > 1.000001 or uv.y < -1e-6 or uv.y > 1.000001
            )
            if uv_outside:
                errors.append(f"{obj.name}: {uv_outside} UV coordinates outside 0-1")
        if any(abs(value - 1.0) > 1e-6 for value in obj.scale):
            errors.append(f"{obj.name}: scale is not applied")
        object_reports.append(
            {
                "name": obj.name,
                "vertices": len(mesh.vertices),
                "triangles": triangles,
                "nonManifoldEdges": non_manifold_edges,
                "looseVertices": loose_vertices,
                "degenerateFaces": degenerate_faces,
                "uvOutsideZeroOne": uv_outside,
                "materialSlots": len(mesh.materials),
            }
        )

    minimum, maximum = world_bounds(objects)
    actual = {
        "width": maximum.x - minimum.x,
        "height": maximum.z - minimum.z,
        "depth": maximum.y - minimum.y,
    }
    target = contract["dimensionsStuds"]
    tolerance = target["tolerancePercent"] / 100.0
    for key in ("width", "height", "depth"):
        if abs(actual[key] - target[key]) > target[key] * tolerance:
            errors.append(f"dimension {key} is {actual[key]:.6f}, expected {target[key]:.6f} ± {target[key] * tolerance:.6f}")
    if abs(minimum.z) > target["height"] * tolerance:
        errors.append(f"base pivot contract failed: minimum height is {minimum.z:.6f}, expected 0")
    if total_triangles > contract["triangleBudget"]["absoluteMaximum"]:
        errors.append(
            f"triangle count {total_triangles} exceeds absolute maximum {contract['triangleBudget']['absoluteMaximum']}"
        )

    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "triangleCount": total_triangles,
        "targetTriangleCount": contract["triangleBudget"]["target"],
        "absoluteMaximumTriangles": contract["triangleBudget"]["absoluteMaximum"],
        "dimensionsStuds": actual,
        "targetDimensionsStuds": {key: target[key] for key in ("width", "height", "depth")},
        "boundsBlender": {"minimum": list(minimum), "maximum": list(maximum)},
        "pivot": {"contract": contract["pivot"], "baseHeight": minimum.z},
        "objects": object_reports,
    }


def select_only(objects: list[bpy.types.Object]) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


def configure_deterministic_fbx_export() -> None:
    """Remove Blender FBX exporter process randomness and wall-clock metadata."""
    import io_scene_fbx.export_fbx_bin as export_fbx_bin
    import io_scene_fbx.fbx_utils as fbx_utils

    def stable_key(value: object) -> str:
        if value is None or isinstance(value, (bool, int, float, str, bytes)):
            return f"{type(value).__name__}:{value!r}"
        if isinstance(value, tuple):
            return "tuple:(" + ",".join(stable_key(item) for item in value) + ")"
        if isinstance(value, frozenset):
            return "frozenset:(" + ",".join(sorted(stable_key(item) for item in value)) + ")"
        nested_key = getattr(value, "key", None)
        if nested_key is not None:
            return f"key:{stable_key(nested_key)}"
        name = getattr(value, "name_full", None) or getattr(value, "name", None)
        if isinstance(name, str):
            return f"named:{type(value).__module__}.{type(value).__qualname__}:{name}"
        return f"fallback:{type(value).__module__}.{type(value).__qualname__}:{value!r}"

    def deterministic_uuid(uuids: dict, key: object):
        if isinstance(key, int) and 0 <= key < 2**63:
            value = key
        else:
            digest = hashlib.sha256(stable_key(key).encode("utf-8")).digest()
            value = int.from_bytes(digest[:8], "big") & ((1 << 63) - 1)
        if value == 0:
            value = 1
        while value in uuids:
            value = 1 if value == (1 << 63) - 1 else value + 1
        return fbx_utils.UUID(value)

    original_header = export_fbx_bin.fbx_header_elements

    def deterministic_header(root, scene_data, time=None):
        return original_header(root, scene_data, time=datetime(2000, 1, 1, 0, 0, 0))

    fbx_utils._keys_to_uuids.clear()
    fbx_utils._uuids_to_keys.clear()
    fbx_utils._key_to_uuid = deterministic_uuid
    export_fbx_bin.fbx_header_elements = deterministic_header


def normalize_fbx_source_path(fbx_path: Path, blend_path: Path) -> None:
    """Remove the output-directory-dependent source path embedded by FBX."""
    payload = fbx_path.read_bytes()
    candidates = {
        str(blend_path).encode("utf-8"),
        blend_path.as_posix().encode("utf-8"),
    }
    replacements = 0
    for candidate in sorted(candidates, key=len, reverse=True):
        count = payload.count(candidate)
        if count == 0:
            continue
        marker = b"r3d-source.blend"
        if len(marker) > len(candidate):
            raise RuntimeError("FBX source path is too short for deterministic normalization")
        normalized = marker + (b"_" * (len(candidate) - len(marker)))
        payload = payload.replace(candidate, normalized)
        replacements += count
    if replacements != 1:
        raise RuntimeError(
            f"expected exactly one FBX source path to normalize, observed {replacements}"
        )
    fbx_path.write_bytes(payload)


def add_camera(name: str) -> bpy.types.Object:
    camera_data = bpy.data.cameras.new(name + "_Data")
    camera = bpy.data.objects.new(name, camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 10.5
    camera.data.lens = 50
    return camera


def point_camera(camera: bpy.types.Object, location: tuple[float, float, float], target: Vector) -> None:
    camera.location = location
    direction = target - camera.location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_render_environment() -> tuple[bpy.types.Object, list[bpy.types.Object]]:
    scene = bpy.context.scene
    available_engines = {item.identifier for item in scene.render.bl_rna.properties["engine"].enum_items}
    for preferred in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT", "BLENDER_WORKBENCH"):
        if preferred in available_engines:
            scene.render.engine = preferred
            break
    else:
        raise RuntimeError(f"no supported render engine found; available={sorted(available_engines)}")
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.render.dither_intensity = 0.0
    if hasattr(scene, "eevee"):
        scene.eevee.taa_render_samples = 64
        scene.eevee.taa_samples = 16
        scene.eevee.use_taa_reprojection = False
    scene.render.film_transparent = False
    scene.world.color = (0.025, 0.03, 0.045)

    ground_material = bpy.data.materials.new("QA_Ground_Material")
    ground_material.diffuse_color = (0.055, 0.06, 0.06, 1.0)
    ground_material.roughness = 0.92
    ground_material.use_nodes = True
    ground_bsdf = ground_material.node_tree.nodes.get("Principled BSDF")
    if ground_bsdf is not None:
        ground_bsdf.inputs["Base Color"].default_value = (
            0.055,
            0.06,
            0.06,
            1.0,
        )
        ground_bsdf.inputs["Roughness"].default_value = 0.92
    bpy.ops.mesh.primitive_plane_add(size=120.0, location=(0.0, 0.0, -0.01))
    ground = bpy.context.object
    ground.name = "QA_Ground"
    ground.data.materials.append(ground_material)

    camera = add_camera("QA_Camera")
    scene.camera = camera
    lights: list[bpy.types.Object] = []
    for index, (location, energy, size) in enumerate(
        [((5.0, -6.0, 9.0), 1000.0, 5.0), ((-5.0, 3.0, 6.0), 650.0, 4.0), ((0.0, 5.0, 3.0), 450.0, 3.0)]
    ):
        data = bpy.data.lights.new(f"QA_Light_{index}_Data", type="AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(f"QA_Light_{index}", data)
        light.location = location
        light.rotation_euler = (math.radians(25), 0, math.radians(25 + index * 90))
        scene.collection.objects.link(light)
        lights.append(light)
    return camera, lights


def near_black_pixel_ratio(path: Path) -> float:
    image = bpy.data.images.load(str(path), check_existing=False)
    try:
        values = array("f", [0.0]) * (image.size[0] * image.size[1] * 4)
        image.pixels.foreach_get(values)
        sampled = 0
        near_black = 0
        for index in range(0, len(values), 16):
            sampled += 1
            if max(values[index], values[index + 1], values[index + 2]) < 0.002:
                near_black += 1
        return near_black / sampled if sampled else 1.0
    finally:
        bpy.data.images.remove(image)


def render_verified_frame(
    scene: bpy.types.Scene,
    path: Path,
    maximum_black_ratio: float,
    maximum_attempts: int = 5,
) -> dict:
    attempts: list[dict] = []
    previous_accepted_path: Path | None = None
    temporary_paths: list[Path] = []
    # A failed rebuild must never leave an earlier frame looking current.
    path.unlink(missing_ok=True)
    try:
        for attempt in range(1, maximum_attempts + 1):
            temporary = path.with_name(
                f".{path.stem}.attempt-{attempt}{path.suffix}"
            )
            temporary_paths.append(temporary)
            scene.render.filepath = str(temporary)
            bpy.ops.render.render(write_still=True)
            content_hash = canonical_png_content_sha256(temporary)
            black_ratio = near_black_pixel_ratio(temporary)
            accepted = black_ratio <= maximum_black_ratio
            comparison = (
                compare_png_render(previous_accepted_path, temporary)
                if accepted and previous_accepted_path is not None
                else None
            )
            attempt_evidence = {
                "attempt": attempt,
                "contentSha256": content_hash,
                "nearBlackPixelRatio": round(black_ratio, 6),
                "maximumNearBlackPixelRatio": maximum_black_ratio,
                "accepted": accepted,
            }
            if comparison is not None:
                attempt_evidence["stabilityComparison"] = comparison
            attempts.append(attempt_evidence)
            if (
                accepted
                and comparison is not None
                and bool(comparison["passed"])
            ):
                os.replace(temporary, path)
                return {
                    "status": "PASS",
                    "path": str(path),
                    "attemptCount": attempt,
                    "contentSha256": content_hash,
                    "stabilityMode": comparison["mode"],
                    "stabilityComparison": comparison,
                    "attempts": attempts,
                }
            previous_accepted_path = temporary if accepted else None
        raise RuntimeError(
            f"render did not stabilize after {maximum_attempts} attempts: "
            f"{path}; attempts={attempts}"
        )
    finally:
        for temporary in temporary_paths:
            temporary.unlink(missing_ok=True)


def render_views(
    contract: dict,
    output: Path,
    objects: list[bpy.types.Object],
) -> tuple[list[str], list[dict]]:
    scene = bpy.context.scene
    resolution = contract["renders"]["resolution"]
    scene.render.resolution_x = resolution
    scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    camera, _lights = add_render_environment()
    target = Vector((0.0, 0.0, 2.0))
    definitions = {
        "front": ((0.0, -12.0, 2.3), 9.5),
        "rear": ((0.0, 12.0, 2.3), 9.5),
        "left": ((-12.0, 0.0, 2.3), 6.0),
        "right": ((12.0, 0.0, 2.3), 6.0),
        "top": ((0.0, 0.0, 14.0), 10.0),
        "perspective": ((9.0, -11.0, 8.0), 10.0),
        "mobile_distance": ((12.0, -17.0, 10.0), 15.0),
    }
    render_paths: list[str] = []
    render_diagnostics: list[dict] = []
    renders = output / "renders"
    renders.mkdir(parents=True, exist_ok=True)
    for view in contract["renders"]["views"]:
        if view == "silhouette":
            continue
        if view not in definitions:
            continue
        location, scale = definitions[view]
        camera.data.ortho_scale = scale
        point_camera(camera, location, target)
        path = renders / f"{view}.png"
        diagnostic = render_verified_frame(
            scene,
            path,
            maximum_black_ratio=0.12,
        )
        diagnostic["view"] = view
        render_diagnostics.append(diagnostic)
        render_paths.append(str(path))

    if "silhouette" in contract["renders"]["views"]:
        original_world = scene.world.color
        original_materials = {obj.name: obj.data.materials[0] for obj in objects}
        ground = bpy.data.objects.get("QA_Ground")
        if ground is not None:
            ground.hide_render = True
        silhouette = bpy.data.materials.new("QA_Silhouette")
        silhouette.diffuse_color = (0.0, 0.0, 0.0, 1.0)
        silhouette.use_nodes = True
        silhouette.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.0, 0.0, 0.0, 1.0)
        for obj in objects:
            obj.data.materials[0] = silhouette
        scene.world.color = (1.0, 1.0, 1.0)
        camera.data.ortho_scale = 9.5
        point_camera(camera, (0.0, -12.0, 2.3), target)
        path = renders / "silhouette.png"
        diagnostic = render_verified_frame(
            scene,
            path,
            maximum_black_ratio=0.35,
        )
        diagnostic["view"] = "silhouette"
        render_diagnostics.append(diagnostic)
        render_paths.append(str(path))
        for obj in objects:
            obj.data.materials[0] = original_materials[obj.name]
        scene.world.color = original_world
        if ground is not None:
            ground.hide_render = False
    return render_paths, render_diagnostics


def git_provenance(repo: Path) -> dict:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
        ).stdout.strip()
        dirty = bool(
            subprocess.run(
                ["git", "status", "--porcelain=v1"], cwd=repo, check=True, capture_output=True, text=True
            ).stdout.strip()
        )
        return {"status": "PASS" if not dirty else "PARTIAL", "commit": commit, "dirty": dirty}
    except (OSError, subprocess.SubprocessError) as error:
        return {"status": "UNKNOWN", "commit": None, "dirty": None, "reason": str(error)}


def compile_asset(
    contract_path: Path,
    output: Path,
    state_id: str | None = None,
) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    source_contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract = resolve_state_variant(source_contract, state_id)
    compiled_state_id = contract["_compiledStateId"]
    visual_canon_path = resolve_visual_canon_path(
        contract_path, contract["visualCanon"]["path"]
    )
    visual_canon = json.loads(visual_canon_path.read_text(encoding="utf-8"))
    observed_canon_sha256 = sha256_file(visual_canon_path)
    if observed_canon_sha256 != contract["visualCanon"]["sha256"]:
        raise RuntimeError("visual canon hash drift before Blender compilation")
    if visual_canon["canonId"] != contract["visualCanon"]["canonId"]:
        raise RuntimeError("visual canon identity drift before Blender compilation")
    reset_scene()
    materials = create_materials(contract)
    objects = [
        add_part(part, materials[part["material"]])
        for part in contract["geometry"]["parts"]
    ]
    geometry = validate_geometry(contract, objects)
    write_json(output / "geometry.json", geometry)
    if geometry["status"] != "PASS":
        return {"status": "FAIL", "errors": geometry["errors"], "geometry": str(output / "geometry.json")}

    select_only(objects)
    blend_path = output / "source.blend"
    blend_backup_path = blend_path.with_suffix(blend_path.suffix + "1")
    bpy.context.preferences.filepaths.save_version = 0
    blend_backup_path.unlink(missing_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path), check_existing=False)
    blend_backup_path.unlink(missing_ok=True)
    select_only(objects)
    glb_path = output / "asset.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
    )
    select_only(objects)
    fbx_path = output / "asset-update.fbx"
    configure_deterministic_fbx_export()
    bpy.ops.export_scene.fbx(
        filepath=str(fbx_path),
        use_selection=True,
        apply_unit_scale=True,
        bake_space_transform=False,
        axis_forward="-Z",
        axis_up="Y",
        add_leaf_bones=False,
        bake_anim=False,
    )
    normalize_fbx_source_path(fbx_path, blend_path)

    render_paths, render_diagnostics = render_views(contract, output, objects)
    semantic = {
        "axisContract": "DESIGN_XYZ_TO_BLENDER_XZY",
        "stateId": compiled_state_id,
        "dimensionsStuds": contract["dimensionsStuds"],
        "geometry": contract["geometry"],
        "materials": contract["materials"],
        "pivot": contract["pivot"],
        "visualCanon": {
            "canonId": visual_canon["canonId"],
            "sha256": observed_canon_sha256,
            "status": visual_canon["status"],
            "territoryId": visual_canon["territoryId"],
        },
    }
    repo = contract_path.parents[2]
    resolved_repo = repo.resolve()

    def portable_path(path: Path) -> str:
        resolved = path.resolve()
        try:
            return resolved.relative_to(resolved_repo).as_posix()
        except ValueError:
            return str(resolved)

    provenance = {
        "schemaVersion": "1.0.0",
        "assetKey": contract["assetKey"],
        "revision": contract["revision"],
        "stateId": compiled_state_id,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "generator": "tools/roblox-3d-asset/blender/compile_asset.py",
        "generatorSha256": sha256_file(Path(__file__).resolve()),
        "blenderVersion": bpy.app.version_string,
        "contractSha256": sha256_file(contract_path),
        "visualCanon": {
            "path": portable_path(visual_canon_path),
            "canonId": visual_canon["canonId"],
            "sha256": observed_canon_sha256,
            "status": visual_canon["status"],
        },
        "semanticSha256": canonical_hash(semantic),
        "git": git_provenance(repo),
    }
    write_json(output / "provenance.json", provenance)
    manifest = {
        "schemaVersion": "1.0.0",
        "assetKey": contract["assetKey"],
        "revision": contract["revision"],
        "stateId": compiled_state_id,
        "status": "PASS",
        "triangleCount": geometry["triangleCount"],
        "meshCount": len(objects),
        "materialCount": len(
            {part["material"] for part in contract["geometry"]["parts"]}
        ),
        "dimensionsStuds": geometry["dimensionsStuds"],
        "visualCanon": {
            "canonId": visual_canon["canonId"],
            "sha256": observed_canon_sha256,
            "status": visual_canon["status"],
            "productionEligible": (
                visual_canon["status"] == "LOCKED"
                and visual_canon["visualPacket"]["status"] == "COMPLETE"
                and visual_canon["approval"]["status"] == "APPROVED"
            ),
        },
        "binaryDeterminism": {
            "canonicalOutputPathRequired": True,
            "glb": "stable",
            "fbxUpdate": "stable after deterministic UUID and header normalization",
        },
        "renderVerification": {
            "status": "PASS",
            "requiredConsecutiveStableFrames": 2,
            "acceptedModes": ["EXACT", "BOUNDED_PIXEL_TOLERANCE"],
            "pixelTolerance": RENDER_PIXEL_TOLERANCE,
            "views": render_diagnostics,
        },
        "artifacts": {
            "glb": {"path": portable_path(glb_path), "sha256": sha256_file(glb_path), "bytes": glb_path.stat().st_size},
            "fbxUpdate": {"path": portable_path(fbx_path), "sha256": sha256_file(fbx_path), "bytes": fbx_path.stat().st_size},
            "blend": {"path": portable_path(blend_path), "sha256": sha256_file(blend_path), "bytes": blend_path.stat().st_size},
            "geometry": portable_path(output / "geometry.json"),
            "provenance": portable_path(output / "provenance.json"),
            "renders": [portable_path(Path(path)) for path in render_paths],
        },
    }
    write_json(output / "manifest.json", manifest)
    return {
        "status": "PASS",
        "assetKey": contract["assetKey"],
        "revision": contract["revision"],
        "stateId": compiled_state_id,
        "manifest": str(output / "manifest.json"),
        "geometry": str(output / "geometry.json"),
        "glb": str(glb_path),
        "fbxUpdate": str(fbx_path),
        "renders": render_paths,
        "renderVerification": "PASS",
    }


def main() -> int:
    output: Path | None = None
    state_id: str | None = None
    try:
        contract, output, state_id = parse_arguments()
        result = compile_asset(contract, output, state_id)
        write_json(output / "compile-result.json", result)
        return 0 if result["status"] == "PASS" else 2
    except Exception as error:  # Blender must always leave machine-readable evidence.
        result = {"status": "FAIL", "errors": [str(error)], "traceback": traceback.format_exc()}
        if state_id is not None:
            result["stateId"] = state_id
        if output is not None:
            write_json(output / "compile-result.json", result)
        print(json.dumps(result, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
