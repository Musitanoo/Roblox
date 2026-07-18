from __future__ import annotations

"""Render real, stabilized Blender evidence for a canonical visual packet."""

import hashlib
import json
import math
import os
import sys
import traceback
from pathlib import Path

import bpy
from mathutils import Vector

TOOL_ROOT = Path(__file__).resolve().parents[1]
if str(TOOL_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOL_ROOT))

from blender.compile_asset import (  # noqa: E402
    RENDER_PIXEL_TOLERANCE,
    add_render_environment,
    point_camera,
    render_verified_frame,
    resolve_visual_canon_path,
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    os.replace(temporary, path)


def parse_arguments() -> tuple[Path, Path, Path]:
    if "--" not in sys.argv:
        raise ValueError(
            "expected -- <contract.json> <source.blend> <output-directory>"
        )
    arguments = sys.argv[sys.argv.index("--") + 1 :]
    if len(arguments) != 3:
        raise ValueError(
            "expected three arguments: "
            "<contract.json> <source.blend> <output-directory>"
        )
    return tuple(Path(value).resolve() for value in arguments)  # type: ignore[return-value]


def _asset_objects(contract: dict) -> list[bpy.types.Object]:
    expected = {part["name"] for part in contract["geometry"]["parts"]}
    observed = {
        obj.name: obj
        for obj in bpy.data.objects
        if obj.type == "MESH" and not obj.name.startswith("QA_")
    }
    missing = sorted(expected - set(observed))
    unexpected = sorted(set(observed) - expected)
    if missing or unexpected:
        raise RuntimeError(
            f"source scene component drift: missing={missing}, unexpected={unexpected}"
        )
    return [observed[name] for name in sorted(expected)]


def _configure_scene() -> tuple[bpy.types.Scene, bpy.types.Object, list[bpy.types.Object]]:
    scene = bpy.context.scene
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    camera, lights = add_render_environment()
    camera.data.type = "ORTHO"
    return scene, camera, lights


def _render(
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    output: Path,
    view_id: str,
    location: tuple[float, float, float],
    target: tuple[float, float, float],
    scale: float,
    maximum_black_ratio: float = 0.2,
) -> dict:
    camera.data.ortho_scale = scale
    point_camera(camera, location, Vector(target))
    path = output / f"{view_id}.png"
    diagnostic = render_verified_frame(
        scene,
        path,
        maximum_black_ratio=maximum_black_ratio,
        maximum_attempts=5,
    )
    diagnostic.update(
        {
            "viewId": view_id,
            "path": path.name,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "width": 1280,
            "height": 720,
            "camera": {
                "type": "ORTHO",
                "location": list(location),
                "target": list(target),
                "orthoScale": scale,
            },
        }
    )
    return diagnostic


def _apply_lighting_profile(
    scene: bpy.types.Scene,
    lights: list[bpy.types.Object],
    profile: dict,
) -> None:
    scene.world.color = tuple(profile["world"])
    for light, specification in zip(lights, profile["lights"], strict=True):
        light.data.energy = specification["energy"]
        light.data.color = tuple(specification["color"])
        light.data.size = specification["size"]


def _lighting_profiles() -> list[dict]:
    return [
        {
            "id": "neutral_qa",
            "world": [0.025, 0.03, 0.045],
            "lights": [
                {"energy": 1000.0, "color": [1.0, 0.94, 0.84], "size": 5.0},
                {"energy": 650.0, "color": [0.72, 0.86, 1.0], "size": 4.0},
                {"energy": 450.0, "color": [0.75, 1.0, 0.92], "size": 3.0},
            ],
        },
        {
            "id": "gameplay_default",
            "world": [0.035, 0.045, 0.055],
            "lights": [
                {"energy": 1250.0, "color": [1.0, 0.72, 0.46], "size": 6.0},
                {"energy": 720.0, "color": [0.48, 0.72, 1.0], "size": 5.0},
                {"energy": 380.0, "color": [0.62, 1.0, 0.84], "size": 3.0},
            ],
        },
        {
            "id": "high_contrast",
            "world": [0.012, 0.014, 0.02],
            "lights": [
                {"energy": 1550.0, "color": [1.0, 0.9, 0.7], "size": 3.0},
                {"energy": 240.0, "color": [0.35, 0.58, 1.0], "size": 2.5},
                {"energy": 160.0, "color": [0.45, 1.0, 0.78], "size": 2.0},
            ],
        },
        {
            "id": "adverse_night",
            "world": [0.006, 0.01, 0.025],
            "lights": [
                {"energy": 520.0, "color": [0.28, 0.48, 1.0], "size": 5.0},
                {"energy": 260.0, "color": [0.18, 0.72, 1.0], "size": 4.0},
                {"energy": 300.0, "color": [1.0, 0.38, 0.16], "size": 2.5},
            ],
        },
    ]


def _grid_offsets(count: int) -> tuple[list[tuple[float, float, float]], int, int]:
    if count == 1:
        columns, rows = 1, 1
    elif count == 30:
        columns, rows = 6, 5
    elif count == 100:
        columns, rows = 10, 10
    else:
        raise ValueError(f"unsupported repetition count: {count}")
    offsets = []
    for row in range(rows):
        for column in range(columns):
            x = (column - (columns - 1) / 2.0) * 9.5
            y = (row - (rows - 1) / 2.0) * 4.25
            offsets.append((x, y, 0.0))
    return offsets, columns, rows


def _render_repetition(
    scene: bpy.types.Scene,
    camera: bpy.types.Object,
    output: Path,
    objects: list[bpy.types.Object],
    count: int,
) -> dict:
    copies: list[bpy.types.Object] = []
    sun_data = bpy.data.lights.new(
        f"QA_Repetition_{count}_Sun_Data",
        type="SUN",
    )
    sun_data.energy = 2.0
    sun_data.color = (0.82, 0.9, 1.0)
    if hasattr(sun_data, "use_shadow"):
        sun_data.use_shadow = False
    sun = bpy.data.objects.new(f"QA_Repetition_{count}_Sun", sun_data)
    sun.rotation_euler = (
        math.radians(28.0),
        math.radians(-18.0),
        math.radians(-32.0),
    )
    scene.collection.objects.link(sun)
    original_world = tuple(scene.world.color)
    offsets, columns, rows = _grid_offsets(count)
    try:
        scene.world.color = (0.05, 0.06, 0.075)
        if count > 1:
            for source in objects:
                source.hide_render = True
            for model_index, offset in enumerate(offsets):
                for source in objects:
                    duplicate = source.copy()
                    duplicate.data = source.data
                    duplicate.name = (
                        f"QA_Reuse_{count}_{model_index:03d}_{source.name}"
                    )
                    duplicate.hide_render = False
                    duplicate.location = source.location + Vector(offset)
                    scene.collection.objects.link(duplicate)
                    copies.append(duplicate)
        settings = {
            1: ((12.0, -17.0, 10.0), 15.0),
            30: ((48.0, -58.0, 52.0), 62.0),
            100: ((82.0, -92.0, 86.0), 108.0),
        }
        location, scale = settings[count]
        result = _render(
            scene,
            camera,
            output,
            f"repetition_{count}",
            location,
            (0.0, 0.0, 1.5),
            scale,
            maximum_black_ratio=0.2,
        )
        result["repetition"] = {
            "modelCount": count,
            "layout": {"columns": columns, "rows": rows},
            "reuseMode": "LINKED_MESH_DATA",
            "uniqueMeshDataCount": len({obj.data.name for obj in objects}),
            "renderObjectCount": len(objects) * count,
        }
        return result
    finally:
        for duplicate in copies:
            bpy.data.objects.remove(duplicate, do_unlink=True)
        for source in objects:
            source.hide_render = False
        bpy.data.objects.remove(sun, do_unlink=True)
        bpy.data.lights.remove(sun_data)
        scene.world.color = original_world


def render_packet(
    contract_path: Path,
    source_blend: Path,
    output: Path,
) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    canon_path = resolve_visual_canon_path(
        contract_path,
        contract["visualCanon"]["path"],
    )
    canon_sha = sha256_file(canon_path)
    if canon_sha != contract["visualCanon"]["sha256"]:
        raise RuntimeError("visual canon hash drift before packet rendering")
    build_manifest_path = contract_path.parent / "build" / "manifest.json"
    build_manifest = json.loads(build_manifest_path.read_text(encoding="utf-8"))
    expected_blend_sha = build_manifest["artifacts"]["blend"]["sha256"]
    if sha256_file(source_blend) != expected_blend_sha:
        raise RuntimeError("source.blend hash differs from the current build manifest")
    if build_manifest.get("status") != "PASS":
        raise RuntimeError("main build manifest is not PASS")
    if build_manifest.get("assetKey") != contract["assetKey"]:
        raise RuntimeError("main build manifest assetKey drift")
    if build_manifest.get("revision") != contract["revision"]:
        raise RuntimeError("main build manifest revision drift")

    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(source_blend))
    bpy.context.preferences.filepaths.save_version = 0
    objects = _asset_objects(contract)
    scene, camera, lights = _configure_scene()
    target = (0.0, 0.0, 2.0)
    renders: list[dict] = []

    mobile_definitions = [
        ("mobile_near", (10.0, -14.0, 7.0), 8.5),
        ("mobile_mid", (12.0, -17.0, 10.0), 14.0),
        ("mobile_far", (14.0, -20.0, 12.0), 22.0),
    ]
    for view_id, location, scale in mobile_definitions:
        renders.append(
            _render(
                scene,
                camera,
                output,
                view_id,
                location,
                target,
                scale,
            )
        )

    for profile in _lighting_profiles():
        _apply_lighting_profile(scene, lights, profile)
        result = _render(
            scene,
            camera,
            output,
            f"lighting_{profile['id']}",
            (9.0, -11.0, 8.0),
            target,
            10.0,
            maximum_black_ratio=0.3,
        )
        result["lightingProfile"] = profile
        renders.append(result)

    _apply_lighting_profile(scene, lights, _lighting_profiles()[0])
    for count in (1, 30, 100):
        renders.append(
            _render_repetition(
                scene,
                camera,
                output,
                objects,
                count,
            )
        )

    manifest = {
        "schemaVersion": "1.0.0",
        "status": "PASS",
        "evidenceClass": "REAL_RENDERED",
        "assetKey": contract["assetKey"],
        "revision": contract["revision"],
        "contractSha256": sha256_file(contract_path),
        "canonId": contract["visualCanon"]["canonId"],
        "canonSha256": canon_sha,
        "sourceBlendSha256": sha256_file(source_blend),
        "buildManifestSha256": sha256_file(build_manifest_path),
        "rendererScriptSha256": sha256_file(Path(__file__).resolve()),
        "renderer": {
            "blenderVersion": bpy.app.version_string,
            "engine": scene.render.engine,
            "resolution": [1280, 720],
            "colorMode": "RGBA8",
            "ditherIntensity": scene.render.dither_intensity,
            "requiredConsecutiveStableFrames": 2,
            "acceptedModes": ["EXACT", "BOUNDED_PIXEL_TOLERANCE"],
            "pixelTolerance": RENDER_PIXEL_TOLERANCE,
            "factoryStartup": True,
            "sourceBlendReadOnly": True,
        },
        "renders": renders,
        "productionApproved": False,
    }
    write_json(output / "raw-manifest.json", manifest)
    return manifest


def main() -> int:
    output: Path | None = None
    try:
        contract_path, source_blend, output = parse_arguments()
        result = render_packet(contract_path, source_blend, output)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except Exception as error:
        failure = {
            "status": "FAIL",
            "error": str(error),
            "traceback": traceback.format_exc(),
            "productionApproved": False,
        }
        if output is not None:
            write_json(output / "raw-manifest.json", failure)
        print(json.dumps(failure, ensure_ascii=False, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
