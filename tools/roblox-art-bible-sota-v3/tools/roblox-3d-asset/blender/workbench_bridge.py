from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import traceback
from pathlib import Path
from typing import Any

import bpy
from mathutils import Vector

SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))
from compile_asset import render_views


AXIS_TO_BLENDER = {"designX": 0, "designY": 2, "designZ": 1}


def canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def arguments() -> tuple[Path, Path]:
    if "--" not in sys.argv:
        raise ValueError("workbench bridge expects request and response paths after --")
    values = sys.argv[sys.argv.index("--") + 1 :]
    if len(values) != 2:
        raise ValueError("workbench bridge expects exactly two arguments")
    return Path(values[0]).resolve(), Path(values[1]).resolve()


def _round_vector(values) -> list[float]:
    return [round(float(value), 6) for value in values]


def _blender_to_design(values) -> list[float]:
    return _round_vector((values[0], values[2], values[1]))


def _world_bounds(obj: bpy.types.Object) -> tuple[list[float], list[float]]:
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = [min(corner[index] for corner in corners) for index in range(3)]
    maximum = [max(corner[index] for corner in corners) for index in range(3)]
    return _blender_to_design(minimum), _blender_to_design(maximum)


def _material_record(material: bpy.types.Material) -> dict[str, Any]:
    principled = (
        material.node_tree.nodes.get("Principled BSDF")
        if material.use_nodes and material.node_tree
        else None
    )
    return {
        "name": material.name,
        "diffuseColor": _round_vector(material.diffuse_color),
        "metallic": round(
            float(principled.inputs["Metallic"].default_value)
            if principled
            else float(material.metallic),
            6,
        ),
        "roughness": round(
            float(principled.inputs["Roughness"].default_value)
            if principled
            else float(material.roughness),
            6,
        ),
    }


def inspect_scene(contract: dict[str, Any]) -> dict[str, Any]:
    required_names = [part["name"] for part in contract["geometry"]["parts"]]
    missing = [name for name in required_names if bpy.data.objects.get(name) is None]
    if missing:
        raise RuntimeError(f"scene is missing declared components: {missing}")
    objects: list[dict[str, Any]] = []
    total_triangles = 0
    overall_minimum = [float("inf")] * 3
    overall_maximum = [float("-inf")] * 3
    used_materials: dict[str, bpy.types.Material] = {}
    for name in required_names:
        obj = bpy.data.objects[name]
        if obj.type != "MESH":
            raise RuntimeError(f"declared component is not a mesh: {name}")
        mesh = obj.data
        mesh.calc_loop_triangles()
        triangle_count = len(mesh.loop_triangles)
        total_triangles += triangle_count
        minimum, maximum = _world_bounds(obj)
        for index in range(3):
            overall_minimum[index] = min(overall_minimum[index], minimum[index])
            overall_maximum[index] = max(overall_maximum[index], maximum[index])
        materials = [slot.material.name for slot in obj.material_slots if slot.material]
        for slot in obj.material_slots:
            if slot.material:
                used_materials[slot.material.name] = slot.material
        objects.append(
            {
                "name": name,
                "type": obj.type,
                "designLocation": _blender_to_design(obj.location),
                "designDimensions": _blender_to_design(obj.dimensions),
                "designRotationDegrees": _blender_to_design(
                    [math.degrees(value) for value in obj.rotation_euler]
                ),
                "boundsDesign": {"minimum": minimum, "maximum": maximum},
                "mesh": {
                    "vertices": len(mesh.vertices),
                    "edges": len(mesh.edges),
                    "polygons": len(mesh.polygons),
                    "triangles": triangle_count,
                },
                "materials": materials,
                "modifiers": [
                    {"name": modifier.name, "type": modifier.type}
                    for modifier in obj.modifiers
                ],
                "visible": not obj.hide_render and not obj.hide_viewport,
            }
        )
    overall_dimensions = [
        round(overall_maximum[index] - overall_minimum[index], 6)
        for index in range(3)
    ]
    base_center = [
        round((overall_minimum[0] + overall_maximum[0]) / 2, 6),
        round(overall_minimum[1], 6),
        round((overall_minimum[2] + overall_maximum[2]) / 2, 6),
    ]
    semantic = {
        "objects": objects,
        "overallBoundsDesign": {
            "minimum": _round_vector(overall_minimum),
            "maximum": _round_vector(overall_maximum),
            "dimensions": overall_dimensions,
        },
        "triangleCount": total_triangles,
        "materials": [
            _material_record(used_materials[name])
            for name in sorted(used_materials)
        ],
    }
    return {
        "$schema": "https://roblox-top1.local/schemas/blender-scene-manifest.schema.json",
        "schemaVersion": "1.0.0",
        "blenderVersion": bpy.app.version_string,
        "axisContract": "DESIGN_XYZ_TO_BLENDER_XZY",
        "assetKey": contract["assetKey"],
        "componentCount": len(objects),
        "objects": objects,
        "materials": semantic["materials"],
        "triangleCount": total_triangles,
        "overallBoundsDesign": semantic["overallBoundsDesign"],
        "pivotAndGrounding": {
            "declaredPivot": contract["pivot"],
            "groundY": round(overall_minimum[1], 6),
            "baseCenter": base_center,
        },
        "semanticSha256": canonical_hash(semantic),
        "status": "PASS",
    }


def _assert_before(actual: float, expected: float, operation: dict[str, Any]) -> None:
    if not math.isclose(actual, expected, abs_tol=1e-4):
        raise RuntimeError(
            f"stale before value for {operation['target']}: expected={expected} actual={actual}"
        )


def _active_object(obj: bpy.types.Object) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def apply_operations(
    operations: list[dict[str, Any]],
    contract: dict[str, Any],
) -> None:
    declared_materials = {item["name"] for item in contract["materials"]}
    for operation in operations:
        operation_type = operation["type"]
        target = operation["target"]
        if operation_type == "SET_MATERIAL_VALUE":
            material = bpy.data.materials.get(target)
            if material is None:
                raise RuntimeError(f"material target is missing: {target}")
            property_name = operation["property"]
            principled = material.node_tree.nodes.get("Principled BSDF")
            current = float(principled.inputs[property_name.title()].default_value)
            _assert_before(current, float(operation["before"]), operation)
            principled.inputs[property_name.title()].default_value = float(
                operation["after"]
            )
            setattr(material, property_name, float(operation["after"]))
            continue

        obj = bpy.data.objects.get(target)
        if obj is None or obj.type != "MESH":
            raise RuntimeError(f"component target is missing or not a mesh: {target}")
        if operation_type == "SET_COMPONENT_VISIBILITY":
            current = not obj.hide_render and not obj.hide_viewport
            if current is not operation["before"]:
                raise RuntimeError(f"stale visibility before value for {target}")
            visible = bool(operation["after"])
            obj.hide_render = not visible
            obj.hide_viewport = not visible
        elif operation_type == "SET_MATERIAL_ROLE":
            if operation["after"] not in declared_materials:
                raise RuntimeError("material role is not declared by the contract")
            current = obj.material_slots[0].material.name
            if current != operation["before"]:
                raise RuntimeError(f"stale material role before value for {target}")
            obj.material_slots[0].material = bpy.data.materials[operation["after"]]
        else:
            index = AXIS_TO_BLENDER[operation["axis"]]
            before = float(operation["before"])
            after = float(operation["after"])
            if operation_type == "SET_COMPONENT_DIMENSION":
                _assert_before(float(obj.dimensions[index]), before, operation)
                obj.dimensions[index] = after
                _active_object(obj)
                bpy.ops.object.transform_apply(
                    location=False,
                    rotation=False,
                    scale=True,
                )
            elif operation_type == "MOVE_COMPONENT":
                _assert_before(float(obj.location[index]), before, operation)
                obj.location[index] = after
            elif operation_type == "ROTATE_COMPONENT":
                # Production meshes have transforms applied. Rotate by the
                # declared source delta, then apply that rotation so Candidate
                # and a fresh deterministic compilation share the same form.
                obj.rotation_euler[index] += math.radians(after - before)
                _active_object(obj)
                bpy.ops.object.transform_apply(
                    location=False,
                    rotation=True,
                    scale=False,
                )
            else:
                raise RuntimeError(f"unimplemented bounded operation: {operation_type}")


def execute(request: dict[str, Any]) -> dict[str, Any]:
    action = request["action"]
    if action not in {"inspect", "preview", "mutate"}:
        raise RuntimeError(f"unsupported bridge action: {action}")
    blend_path = Path(request["blendPath"]).resolve()
    contract_path = Path(request["contractPath"]).resolve()
    if not blend_path.is_file() or not contract_path.is_file():
        raise RuntimeError("bridge input file is missing")
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    bpy.ops.wm.open_mainfile(filepath=str(blend_path), load_ui=False)
    if action in {"preview", "mutate"}:
        apply_operations(request["operations"], contract)
    manifest = inspect_scene(contract)
    if action == "mutate":
        save_path = Path(request["savePath"]).resolve()
        if save_path != blend_path:
            raise RuntimeError("mutate may save only over the declared candidate copy")
        bpy.ops.wm.save_as_mainfile(filepath=str(save_path), check_existing=False)
    render_paths: list[str] = []
    if request.get("capture"):
        output = Path(request["captureRoot"]).resolve()
        objects = [bpy.data.objects[item["name"]] for item in manifest["objects"]]
        render_paths = render_views(contract, output, objects)
    return {
        "status": "PASS",
        "action": action,
        "sceneManifest": manifest,
        "captures": render_paths,
    }


def main() -> int:
    response_path: Path | None = None
    try:
        request_path, response_path = arguments()
        request = json.loads(request_path.read_text(encoding="utf-8"))
        write_json(response_path, execute(request))
        return 0
    except Exception as error:
        result = {
            "status": "FAIL",
            "errors": [str(error)],
            "traceback": traceback.format_exc(),
        }
        if response_path is not None:
            write_json(response_path, result)
        print(json.dumps(result, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
