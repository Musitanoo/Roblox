from __future__ import annotations

"""Build the frozen sixth-asset transfer challenge without changing calibration assets.

This compiler deliberately imports the proven primitive, material, validation,
camera, lighting, and GLB canonicalization implementation from
``build_art_direction.py``. It only supplies composition for ``turret_fast_v1``.
That separation makes the transfer test independent while preventing a new
palette, material system, camera convention, or export path from appearing.
"""

import argparse
import json
import math
import random
import shutil
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import bpy
from mathutils import Euler, Matrix, Vector

PACKAGE_ROOT = Path(__file__).resolve().parents[2]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from tools.blender import build_art_direction as base

SCHEMA = "https://roblox-top1.local/schemas/transfer-build-report.schema.json"
ASSET_ID = "turret_fast_v1"
STATES = ("intact", "damaged", "critical")
TERRITORIES = (
    "industrial-toy-defense",
    "salvaged-frontier",
    "clean-tactical-diorama",
)
GENERATOR_VERSION = "1.0.0"


def parse_args() -> argparse.Namespace:
    raw = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=PACKAGE_ROOT)
    parser.add_argument("--territory", choices=TERRITORIES, required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--render-mode", choices=("build-only", "full"), default="build-only")
    parser.add_argument("--no-clean-output", action="store_true")
    args = parser.parse_args(raw)
    args.root = args.root.resolve()
    args.output = (
        args.output
        or args.root / "build" / "transfer" / ASSET_ID / args.territory
    ).resolve()
    return args


def mark(obj: bpy.types.Object, component: str) -> bpy.types.Object:
    obj["transfer_component"] = component
    return obj


def box(
    ctx: base.BuildContext,
    collection: bpy.types.Collection,
    state: str,
    component: str,
    name: str,
    size: tuple[float, float, float],
    location: tuple[float, float, float],
    role: str,
    band: str,
    *,
    rotation: tuple[float, float, float] = (0, 0, 0),
    bevel: float,
    segments: int = 1,
) -> bpy.types.Object:
    return mark(
        base.add_box(
            ctx,
            collection,
            ASSET_ID,
            state,
            name,
            size,
            location,
            role,
            band,
            rotation=rotation,
            bevel_ratio=bevel,
            bevel_segments=segments,
        ),
        component,
    )


def panel(
    ctx: base.BuildContext,
    collection: bpy.types.Collection,
    state: str,
    component: str,
    name: str,
    size: tuple[float, float, float],
    location: tuple[float, float, float],
    role: str,
    band: str,
    *,
    corner_ratio: float,
) -> bpy.types.Object:
    return mark(
        base.add_chamfered_panel(
            ctx,
            collection,
            ASSET_ID,
            state,
            name,
            size,
            location,
            role,
            band,
            corner_ratio=corner_ratio,
        ),
        component,
    )


def wedge(
    ctx: base.BuildContext,
    collection: bpy.types.Collection,
    state: str,
    component: str,
    name: str,
    size: tuple[float, float, float],
    location: tuple[float, float, float],
    role: str,
    band: str,
    *,
    rotation: tuple[float, float, float] = (0, 0, 0),
) -> bpy.types.Object:
    return mark(
        base.add_wedge(
            ctx,
            collection,
            ASSET_ID,
            state,
            name,
            size,
            location,
            role,
            band,
            rotation=rotation,
        ),
        component,
    )


def transform_components(
    objects: Iterable[bpy.types.Object],
    components: set[str],
    *,
    pivot: tuple[float, float, float],
    rotation: tuple[float, float, float],
    translation: tuple[float, float, float] = (0, 0, 0),
) -> None:
    pivot_vector = Vector(pivot)
    rotation_matrix = Euler(rotation, "XYZ").to_matrix().to_4x4()
    transform = (
        Matrix.Translation(pivot_vector + Vector(translation))
        @ rotation_matrix
        @ Matrix.Translation(-pivot_vector)
    )
    for obj in objects:
        if obj.get("transfer_component") in components:
            obj.matrix_world = transform @ obj.matrix_world


def add_socket(
    ctx: base.BuildContext,
    collection: bpy.types.Collection,
    state: str,
    objects: list[bpy.types.Object],
    *,
    center: tuple[float, float, float],
    width: float,
    height: float,
    border: float,
    depth: float,
    bevel: float,
    open_socket: bool,
) -> None:
    x, y, z = center
    objects.append(
        box(
            ctx,
            collection,
            state,
            "InteractionCore",
            "InteractionCore",
            (width - 2 * border, depth * 0.55, height - 2 * border),
            (x, y - depth * 0.24, z),
            "interaction" if not open_socket else "critical",
            "secondary",
            bevel=bevel,
        )
    )
    bars = (
        ("SocketL", (-width / 2 + border / 2, 0, 0), (border, depth, height)),
        ("SocketR", (width / 2 - border / 2, 0, 0), (border, depth, height)),
        ("SocketBottom", (0, 0, -height / 2 + border / 2), (width, depth, border)),
        ("SocketTop", (0, 0, height / 2 - border / 2), (width, depth, border)),
    )
    for name, offset, size in bars:
        if open_socket and name in {"SocketR", "SocketTop"}:
            continue
        objects.append(
            box(
                ctx,
                collection,
                state,
                "InteractionSocket",
                name,
                size,
                (x + offset[0], y + offset[1], z + offset[2]),
                "interaction",
                "secondary",
                bevel=bevel,
            )
        )


def add_common_foundation(
    ctx: base.BuildContext,
    collection: bpy.types.Collection,
    state: str,
    *,
    bevel: float,
    territory: str,
) -> list[bpy.types.Object]:
    objects: list[bpy.types.Object] = []
    if territory == "industrial-toy-defense":
        foundation = (3.95, 3.55, 0.42)
        pedestal = (2.72, 2.36, 0.62)
        foot_x, foot_y = 1.52, 1.34
    elif territory == "salvaged-frontier":
        foundation = (4.05, 3.45, 0.40)
        pedestal = (2.55, 2.20, 0.72)
        foot_x, foot_y = 1.48, 1.30
    else:
        foundation = (3.72, 3.72, 0.36)
        pedestal = (2.82, 2.52, 0.58)
        foot_x, foot_y = 1.43, 1.43

    objects.append(
        panel(
            ctx,
            collection,
            state,
            "Foundation",
            "Foundation",
            foundation,
            (0, 0, foundation[2] / 2),
            "primary",
            "primary",
            corner_ratio=0.12 if territory != "salvaged-frontier" else 0.07,
        )
    )
    for index, (x, y) in enumerate(
        ((-foot_x, -foot_y), (foot_x, -foot_y), (-foot_x, foot_y), (foot_x, foot_y))
    ):
        objects.append(
            box(
                ctx,
                collection,
                state,
                "Foot",
                f"Foot_{index}",
                (0.92, 0.82, 0.30),
                (x, y, 0.15),
                "rubber",
                "secondary",
                bevel=bevel,
            )
        )
    objects.append(
        panel(
            ctx,
            collection,
            state,
            "Pedestal",
            "Pedestal",
            pedestal,
            (0, 0.02, 0.69),
            "secondary",
            "primary",
            corner_ratio=0.16 if territory == "clean-tactical-diorama" else 0.10,
        )
    )
    objects.append(
        box(
            ctx,
            collection,
            state,
            "Pedestal",
            "RotationDeck",
            (2.20, 1.98, 0.34),
            (0, -0.03, 1.12),
            "accent" if territory == "industrial-toy-defense" else "primary",
            "secondary",
            bevel=bevel,
        )
    )
    return objects


def build_industrial(
    ctx: base.BuildContext,
    collection: bpy.types.Collection,
    state: str,
    bevel: float,
) -> tuple[list[bpy.types.Object], list[int]]:
    objects = add_common_foundation(
        ctx, collection, state, bevel=bevel, territory="industrial-toy-defense"
    )
    objects.extend(
        [
            box(
                ctx,
                collection,
                state,
                "Pedestal",
                "Column",
                (1.62, 1.48, 1.48),
                (0, 0.06, 1.88),
                "primary",
                "primary",
                bevel=bevel,
            ),
            panel(
                ctx,
                collection,
                state,
                "Body",
                "Body",
                (2.88, 2.10, 1.46),
                (0, 0.02, 3.18),
                "primary",
                "primary",
                corner_ratio=0.12,
            ),
            box(
                ctx,
                collection,
                state,
                "Body",
                "TopArmor",
                (2.18, 1.62, 0.34),
                (0, 0.07, 4.04),
                "secondary",
                "secondary",
                bevel=bevel,
            ),
            box(
                ctx,
                collection,
                state,
                "YokeL",
                "YokeL",
                (0.46, 1.44, 1.72),
                (-1.40, 0.02, 3.15),
                "accent",
                "secondary",
                bevel=bevel,
            ),
            box(
                ctx,
                collection,
                state,
                "YokeR",
                "YokeR",
                (0.46, 1.44, 1.72),
                (1.40, 0.02, 3.15),
                "accent",
                "secondary",
                bevel=bevel,
            ),
            box(
                ctx,
                collection,
                state,
                "GuardL",
                "GuardL",
                (0.28, 1.18, 0.92),
                (-0.96, -0.50, 3.42),
                "accent",
                "secondary",
                bevel=bevel,
            ),
            box(
                ctx,
                collection,
                state,
                "GuardR",
                "GuardR",
                (0.28, 1.18, 0.92),
                (0.96, -0.50, 3.42),
                "accent",
                "secondary",
                bevel=bevel,
            ),
            wedge(
                ctx,
                collection,
                state,
                "FrontCue",
                "ForwardWedge",
                (1.18, 0.48, 0.38),
                (0, -1.13, 4.12),
                "accent",
                "secondary",
                rotation=(0, 0, math.radians(90)),
            ),
            box(
                ctx,
                collection,
                state,
                "ServiceMass",
                "ServiceMass",
                (1.88, 0.64, 1.18),
                (0, 1.29, 3.30),
                "secondary",
                "secondary",
                bevel=bevel,
            ),
        ]
    )
    for side, x in (("L", -0.53), ("R", 0.53)):
        if state == "critical" and side == "R":
            continue
        objects.extend(
            [
                box(
                    ctx,
                    collection,
                    state,
                    f"Barrel{side}",
                    f"Barrel{side}",
                    (0.60, 2.56, 0.58),
                    (x, -1.72, 3.45),
                    "bareMetal",
                    "primary",
                    bevel=0.025,
                ),
                box(
                    ctx,
                    collection,
                    state,
                    f"Muzzle{side}",
                    f"Muzzle{side}",
                    (0.82, 0.42, 0.82),
                    (x, -3.03, 3.45),
                    "accent",
                    "secondary",
                    bevel=bevel,
                ),
                box(
                    ctx,
                    collection,
                    state,
                    f"Muzzle{side}",
                    f"Aperture{side}",
                    (0.42, 0.08, 0.42),
                    (x, -3.25, 3.45),
                    "rubber",
                    "secondary",
                    bevel=0.02,
                ),
            ]
        )
    add_socket(
        ctx,
        collection,
        state,
        objects,
        center=(0, -1.22, 1.68),
        width=0.96,
        height=0.82,
        border=0.16,
        depth=0.18,
        bevel=0.03,
        open_socket=state == "critical",
    )
    if state in {"damaged", "critical"}:
        objects.append(
            box(
                ctx,
                collection,
                state,
                "ExposedStructure",
                "ExposedStructure",
                (0.74, 0.22, 0.76),
                (0.84, -1.10, 3.15),
                "bareMetal",
                "secondary",
                bevel=0.02,
            )
        )
    if state == "critical":
        objects.append(
            panel(
                ctx,
                collection,
                state,
                "CriticalCore",
                "CriticalCore",
                (0.92, 0.22, 0.92),
                (0.56, -1.16, 3.17),
                "critical",
                "secondary",
                corner_ratio=0.16,
            )
        )
    if state == "damaged":
        transform_components(
            objects,
            {"BarrelR", "MuzzleR"},
            pivot=(0.53, -0.42, 3.45),
            rotation=(math.radians(45), 0, 0),
            translation=(0.58, 0, -0.28),
        )
        transform_components(
            objects,
            {"GuardR"},
            pivot=(0.96, -0.06, 3.42),
            rotation=(0, 0, math.radians(45)),
            translation=(0.40, 0, 0.24),
        )
    elif state == "critical":
        transform_components(
            objects,
            {
                "Body",
                "YokeL",
                "YokeR",
                "GuardL",
                "GuardR",
                "BarrelL",
                "MuzzleL",
                "ServiceMass",
                "FrontCue",
                "CriticalCore",
                "ExposedStructure",
            },
            pivot=(0, 0, 1.20),
            rotation=(math.radians(9), 0, math.radians(45)),
            translation=(-0.12, 0.02, -0.16),
        )
    return objects, [0, 45, 90]


def build_salvaged(
    ctx: base.BuildContext,
    collection: bpy.types.Collection,
    state: str,
    bevel: float,
) -> tuple[list[bpy.types.Object], list[int]]:
    objects = add_common_foundation(
        ctx, collection, state, bevel=bevel, territory="salvaged-frontier"
    )
    objects.extend(
        [
            box(
                ctx,
                collection,
                state,
                "Pedestal",
                "OffsetColumn",
                (1.48, 1.34, 1.62),
                (-0.18, 0.12, 1.94),
                "primary",
                "primary",
                rotation=(0, 0, math.radians(-15)),
                bevel=bevel,
            ),
            panel(
                ctx,
                collection,
                state,
                "Body",
                "RecoveredBody",
                (2.76, 1.92, 1.52),
                (0.18, 0.02, 3.24),
                "primary",
                "primary",
                corner_ratio=0.07,
            ),
            box(
                ctx,
                collection,
                state,
                "Body",
                "ReclaimedTop",
                (2.16, 1.50, 0.34),
                (-0.12, 0.07, 4.13),
                "secondary",
                "secondary",
                rotation=(0, math.radians(15), 0),
                bevel=bevel,
            ),
            box(
                ctx,
                collection,
                state,
                "Brace",
                "RepairBrace",
                (0.30, 0.42, 2.28),
                (-1.26, 0.24, 2.72),
                "secondary",
                "secondary",
                rotation=(0, math.radians(30), math.radians(-15)),
                bevel=0.025,
            ),
            box(
                ctx,
                collection,
                state,
                "YokeL",
                "YokeL",
                (0.42, 1.28, 1.52),
                (-1.20, -0.05, 3.25),
                "bareMetal",
                "secondary",
                rotation=(0, 0, math.radians(-15)),
                bevel=0.025,
            ),
            box(
                ctx,
                collection,
                state,
                "YokeR",
                "YokeR",
                (0.52, 1.38, 1.72),
                (1.32, 0.12, 3.28),
                "accent",
                "secondary",
                bevel=bevel,
            ),
            wedge(
                ctx,
                collection,
                state,
                "FrontCue",
                "ForwardWedge",
                (1.10, 0.48, 0.40),
                (-0.14, -1.04, 4.16),
                "accent",
                "secondary",
                rotation=(0, 0, math.radians(90)),
            ),
            box(
                ctx,
                collection,
                state,
                "ServiceMass",
                "ServiceMass",
                (1.08, 0.82, 1.62),
                (1.13, 1.25, 3.50),
                "secondary",
                "secondary",
                rotation=(0, 0, math.radians(15)),
                bevel=bevel,
            ),
            box(
                ctx,
                collection,
                state,
                "RepairBand",
                "RepairBand",
                (2.90, 0.18, 0.28),
                (0.12, -0.98, 3.03),
                "bareMetal",
                "secondary",
                rotation=(0, 0, math.radians(-15)),
                bevel=0.02,
            ),
        ]
    )
    barrel_specs = {
        "L": (-0.48, 0.56, 2.68, 0.58),
        "R": (0.58, 0.68, 2.36, 0.70),
    }
    for side, (x, width, length, height) in barrel_specs.items():
        if state == "critical" and side == "R":
            continue
        objects.extend(
            [
                box(
                    ctx,
                    collection,
                    state,
                    f"Barrel{side}",
                    f"Barrel{side}",
                    (width, length, height),
                    (x, -1.67 if side == "L" else -1.52, 3.50 if side == "L" else 3.40),
                    "bareMetal",
                    "primary",
                    rotation=(0, 0, math.radians(-15 if side == "L" else 0)),
                    bevel=0.02,
                ),
                box(
                    ctx,
                    collection,
                    state,
                    f"Muzzle{side}",
                    f"Muzzle{side}",
                    (width + 0.22, 0.40, height + 0.20),
                    (
                        x - (0.16 if side == "L" else 0),
                        -3.00 if side == "L" else -2.75,
                        3.50 if side == "L" else 3.40,
                    ),
                    "accent" if side == "R" else "secondary",
                    "secondary",
                    rotation=(0, 0, math.radians(-15 if side == "L" else 0)),
                    bevel=bevel,
                ),
                box(
                    ctx,
                    collection,
                    state,
                    f"Muzzle{side}",
                    f"Aperture{side}",
                    (width * 0.58, 0.08, height * 0.54),
                    (
                        x - (0.18 if side == "L" else 0),
                        -3.22 if side == "L" else -2.97,
                        3.50 if side == "L" else 3.40,
                    ),
                    "rubber",
                    "secondary",
                    rotation=(0, 0, math.radians(-15 if side == "L" else 0)),
                    bevel=0.015,
                ),
            ]
        )
    add_socket(
        ctx,
        collection,
        state,
        objects,
        center=(-0.62, -1.14, 1.64),
        width=0.90,
        height=0.78,
        border=0.15,
        depth=0.18,
        bevel=0.025,
        open_socket=state == "critical",
    )
    if state in {"damaged", "critical"}:
        objects.extend(
            [
                box(
                    ctx,
                    collection,
                    state,
                    "ExposedStructure",
                    "ExposedStructure",
                    (0.82, 0.24, 0.88),
                    (0.76, -1.01, 3.18),
                    "bareMetal",
                    "secondary",
                    rotation=(0, 0, math.radians(15)),
                    bevel=0.018,
                ),
                wedge(
                    ctx,
                    collection,
                    state,
                    "WarningCue",
                    "WarningChevron",
                    (0.58, 0.16, 0.50),
                    (0.86, -1.17, 2.73),
                    "warning",
                    "tertiary",
                    rotation=(0, 0, math.radians(90)),
                ),
            ]
        )
    if state == "critical":
        objects.append(
            panel(
                ctx,
                collection,
                state,
                "CriticalCore",
                "CriticalCore",
                (1.06, 0.22, 0.96),
                (0.58, -1.16, 3.26),
                "critical",
                "secondary",
                corner_ratio=0.12,
            )
        )
    if state == "damaged":
        transform_components(
            objects,
            {"BarrelR", "MuzzleR"},
            pivot=(0.58, -0.32, 3.40),
            rotation=(math.radians(30), 0, 0),
            translation=(0.64, 0, -0.30),
        )
        transform_components(
            objects,
            {"YokeR"},
            pivot=(1.32, 0.12, 3.28),
            rotation=(0, 0, math.radians(15)),
            translation=(0.38, 0, 0.24),
        )
    elif state == "critical":
        transform_components(
            objects,
            {
                "Body",
                "YokeL",
                "YokeR",
                "BarrelL",
                "MuzzleL",
                "ServiceMass",
                "FrontCue",
                "RepairBand",
                "CriticalCore",
                "ExposedStructure",
                "WarningCue",
            },
            pivot=(-0.10, 0.05, 1.20),
            rotation=(math.radians(12), 0, math.radians(-30)),
            translation=(0.14, 0.04, -0.22),
        )
    return objects, [0, 15, 30, 45, 90]


def build_clean(
    ctx: base.BuildContext,
    collection: bpy.types.Collection,
    state: str,
    bevel: float,
) -> tuple[list[bpy.types.Object], list[int]]:
    objects = add_common_foundation(
        ctx, collection, state, bevel=bevel, territory="clean-tactical-diorama"
    )
    objects.extend(
        [
            panel(
                ctx,
                collection,
                state,
                "Pedestal",
                "CoreColumn",
                (1.52, 1.42, 1.56),
                (0, 0, 1.94),
                "primary",
                "primary",
                corner_ratio=0.18,
            ),
            panel(
                ctx,
                collection,
                state,
                "Body",
                "Body",
                (2.82, 1.88, 1.48),
                (0, 0, 3.18),
                "primary",
                "primary",
                corner_ratio=0.18,
            ),
            wedge(
                ctx,
                collection,
                state,
                "Body",
                "TopPlaneL",
                (1.42, 1.42, 0.38),
                (-0.68, 0.02, 4.08),
                "secondary",
                "secondary",
                rotation=(0, 0, math.radians(90)),
            ),
            wedge(
                ctx,
                collection,
                state,
                "Body",
                "TopPlaneR",
                (1.42, 1.42, 0.38),
                (0.68, 0.02, 4.08),
                "secondary",
                "secondary",
                rotation=(0, 0, math.radians(-90)),
            ),
            box(
                ctx,
                collection,
                state,
                "YokeL",
                "YokeL",
                (0.36, 1.28, 1.58),
                (-1.28, 0, 3.22),
                "secondary",
                "secondary",
                rotation=(0, 0, math.radians(-30)),
                bevel=bevel,
            ),
            box(
                ctx,
                collection,
                state,
                "YokeR",
                "YokeR",
                (0.36, 1.28, 1.58),
                (1.28, 0, 3.22),
                "secondary",
                "secondary",
                rotation=(0, 0, math.radians(30)),
                bevel=bevel,
            ),
            wedge(
                ctx,
                collection,
                state,
                "FrontCue",
                "ForwardWedge",
                (1.04, 0.42, 0.34),
                (0, -1.03, 4.13),
                "interaction",
                "secondary",
                rotation=(0, 0, math.radians(90)),
            ),
            panel(
                ctx,
                collection,
                state,
                "ServiceMass",
                "ServiceMass",
                (1.62, 0.54, 1.08),
                (0, 1.20, 3.28),
                "secondary",
                "secondary",
                corner_ratio=0.18,
            ),
        ]
    )
    for side, x in (("L", -0.48), ("R", 0.48)):
        if state == "critical" and side == "R":
            continue
        objects.extend(
            [
                panel(
                    ctx,
                    collection,
                    state,
                    f"Barrel{side}",
                    f"Barrel{side}",
                    (0.54, 2.48, 0.54),
                    (x, -1.68, 3.48),
                    "primary",
                    "primary",
                    corner_ratio=0.14,
                ),
                panel(
                    ctx,
                    collection,
                    state,
                    f"Muzzle{side}",
                    f"Muzzle{side}",
                    (0.72, 0.38, 0.72),
                    (x, -2.96, 3.48),
                    "accent",
                    "secondary",
                    corner_ratio=0.16,
                ),
                box(
                    ctx,
                    collection,
                    state,
                    f"Muzzle{side}",
                    f"Aperture{side}",
                    (0.34, 0.07, 0.34),
                    (x, -3.16, 3.48),
                    "rubber",
                    "secondary",
                    bevel=0.015,
                ),
            ]
        )
    add_socket(
        ctx,
        collection,
        state,
        objects,
        center=(0, -1.11, 1.68),
        width=0.90,
        height=0.78,
        border=0.14,
        depth=0.16,
        bevel=0.025,
        open_socket=state == "critical",
    )
    if state in {"damaged", "critical"}:
        objects.append(
            panel(
                ctx,
                collection,
                state,
                "ExposedStructure",
                "ExposedStructure",
                (0.76, 0.20, 0.82),
                (0.72, -1.01, 3.19),
                "bareMetal",
                "secondary",
                corner_ratio=0.14,
            )
        )
    if state == "critical":
        objects.extend(
            [
                panel(
                    ctx,
                    collection,
                    state,
                    "CriticalCore",
                    "CriticalCore",
                    (0.94, 0.22, 0.94),
                    (0.52, -1.14, 3.19),
                    "critical",
                    "secondary",
                    corner_ratio=0.18,
                ),
                wedge(
                    ctx,
                    collection,
                    state,
                    "WarningCue",
                    "BrokenChevronL",
                    (0.44, 0.14, 0.46),
                    (-0.38, -1.16, 2.72),
                    "warning",
                    "tertiary",
                    rotation=(0, 0, math.radians(60)),
                ),
                wedge(
                    ctx,
                    collection,
                    state,
                    "WarningCue",
                    "BrokenChevronR",
                    (0.44, 0.14, 0.46),
                    (0.42, -1.16, 2.66),
                    "critical",
                    "tertiary",
                    rotation=(0, 0, math.radians(-60)),
                ),
            ]
        )
    if state == "damaged":
        transform_components(
            objects,
            {"BarrelR", "MuzzleR"},
            pivot=(0.48, -0.42, 3.48),
            rotation=(math.radians(30), 0, 0),
        )
        transform_components(
            objects,
            {"YokeR"},
            pivot=(1.28, 0, 3.22),
            rotation=(0, 0, math.radians(30)),
            translation=(0.08, 0, -0.08),
        )
    elif state == "critical":
        transform_components(
            objects,
            {
                "Body",
                "YokeL",
                "YokeR",
                "BarrelL",
                "MuzzleL",
                "ServiceMass",
                "FrontCue",
                "CriticalCore",
                "ExposedStructure",
                "WarningCue",
            },
            pivot=(0, 0, 1.22),
            rotation=(math.radians(8), 0, math.radians(30)),
            translation=(-0.10, 0, -0.18),
        )
    return objects, [0, 30, 60, 90]


def bake_transforms_and_uv(objects: Iterable[bpy.types.Object]) -> None:
    for obj in objects:
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        if len(obj.data.uv_layers) == 0:
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.uv.smart_project(
                angle_limit=math.radians(66.0),
                island_margin=0.02,
            )
            bpy.ops.object.mode_set(mode="OBJECT")
        obj.select_set(False)


def build_variant(
    ctx: base.BuildContext,
    contract: dict[str, Any],
    state: str,
) -> tuple[base.AssetVariant, list[int]]:
    territory_id = ctx.territory["territoryId"]
    collection = bpy.data.collections.new(
        f"C_{territory_id}__{ASSET_ID}__{state}"
    )
    bpy.context.scene.collection.children.link(collection)
    root = bpy.data.objects.new(f"ROOT_{ASSET_ID}__{state}", None)
    collection.objects.link(root)
    root["ArtTerritory"] = territory_id
    root["ArtAssetId"] = ASSET_ID
    root["ArtState"] = state

    bevel = contract["territoryBindings"][territory_id]["bevelRatio"]
    if territory_id == "industrial-toy-defense":
        objects, authored_angles = build_industrial(ctx, collection, state, bevel)
    elif territory_id == "salvaged-frontier":
        objects, authored_angles = build_salvaged(ctx, collection, state, bevel)
    else:
        objects, authored_angles = build_clean(ctx, collection, state, bevel)

    bake_transforms_and_uv(objects)
    spec = {
        "dimensions": contract["dimensions"],
        "pivot": contract["pivot"],
        "triangleBudgetMax": contract["triangleBudgetMax"],
    }
    variant = base.AssetVariant(
        ASSET_ID,
        state,
        root,
        collection,
        objects,
        spec["dimensions"],
        spec["pivot"],
        spec["triangleBudgetMax"],
    )
    reference_scale = ctx.normalization_scales.get(ASSET_ID)
    if state != "intact" and reference_scale is None:
        raise RuntimeError("intact must be built before damaged/critical")
    scale = base.normalize_bounds(variant, reference_scale)
    base.quantize_mesh_coordinates(variant.objects)
    if state == "intact":
        ctx.normalization_scales[ASSET_ID] = scale
    variant.report = base.validate_variant(variant, ctx.calibration)
    collection.hide_render = True
    collection.hide_viewport = True
    return variant, authored_angles


def component_presence(variant: base.AssetVariant) -> list[str]:
    return sorted(
        {
            str(obj.get("transfer_component"))
            for obj in variant.objects
            if obj.get("transfer_component")
        }
    )


def grammar_audit(
    ctx: base.BuildContext,
    contract: dict[str, Any],
    authored_angles: list[int],
) -> dict[str, Any]:
    territory_id = ctx.territory["territoryId"]
    binding = contract["territoryBindings"][territory_id]
    roles = sorted(
        {
            str(obj["art_role"])
            for variant in ctx.variants.values()
            for obj in variant.objects
        }
    )
    allowed_roles = set(contract["grammarClosure"]["paletteRoles"])
    surface_ids = set(ctx.material_rules["materials"])
    unknown_materials = sorted(
        set(ctx.territory["surfaceAssignments"].values()) - surface_ids
    )
    presence = {
        state: component_presence(ctx.variants[(ASSET_ID, state)])
        for state in STATES
    }
    issues: list[str] = []
    if set(authored_angles) - set(binding["allowedAnglesDegrees"]):
        issues.append("authored angle escapes frozen territory angle family")
    if binding["bevelRatio"] != ctx.territory["assetRecipes"]["objective_core"][
        "bevelRatioTarget"
    ]:
        issues.append("bevel ratio differs from frozen objective_core recipe")
    unknown_roles = sorted(set(roles) - allowed_roles)
    if unknown_roles:
        issues.append(f"unknown palette roles: {unknown_roles}")
    if unknown_materials:
        issues.append(f"unknown material classes: {unknown_materials}")
    components = contract["componentContract"]
    for state in STATES:
        required = set(components["requiredAllStates"])
        if state != "critical":
            required.update(components["requiredIntactAndDamaged"])
        missing = sorted(required - set(presence[state]))
        if missing:
            issues.append(f"{state}: missing required components {missing}")
    forbidden_critical = set(components["criticalOmissions"])
    observed_forbidden = sorted(forbidden_critical & set(presence["critical"]))
    if observed_forbidden:
        issues.append(
            f"critical: components that must be absent are present {observed_forbidden}"
        )
    return {
        "status": "PASS" if not issues else "FAIL",
        "bevelSourceAsset": binding["bevelSourceAsset"],
        "bevelRatio": binding["bevelRatio"],
        "authoredAnglesDegrees": authored_angles,
        "allowedAnglesDegrees": binding["allowedAnglesDegrees"],
        "semanticRolesUsed": roles,
        "unknownPaletteRoles": unknown_roles,
        "unknownMaterialClasses": unknown_materials,
        "componentPresenceByState": presence,
        "stateCuesByState": {
            state: contract["stateContract"][state]["requiredCues"] for state in STATES
        },
        "issues": issues,
    }


def render_case(
    ctx: base.BuildContext,
    camera: bpy.types.Object,
    variant: base.AssetVariant,
    *,
    case_id: str,
    camera_id: str,
    profile_id: str,
    background_id: str,
    resolution_id: str,
    pass_id: str,
) -> dict[str, Any]:
    resolutions = {
        item["id"]: item for item in ctx.camera_rig["resolutions"]
    }
    if resolution_id == "reference_review":
        width, height = 1024, 768
    else:
        resolution = resolutions[resolution_id]
        width, height = resolution["width"], resolution["height"]
    scene = bpy.context.scene
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    base.set_collection_visible(variant.collection, True)
    ground = None
    if case_id == "hero":
        distance = base._review_camera_distance(variant, width / height)
        base.place_camera(
            camera,
            {
                "distanceStuds": distance,
                "azimuthDegrees": 38.0,
                "elevationDegrees": 18.0,
                "targetHeightStuds": variant.target_dimensions["height"] * 0.48,
            },
        )
        base.configure_review_lighting(ctx, variant.target_dimensions["height"])
        ground = base.create_review_ground(ctx, ASSET_ID, variant.state_id)
    else:
        base.place_camera(camera, ctx.camera_rig["validationCameras"][camera_id])
        base.configure_lighting(ctx, profile_id)
        base.configure_world(
            scene,
            base.background_color(ctx, background_id),
            0.8,
        )
    base.set_render_pass(ctx, variant, pass_id)
    profile_short = {
        "Review_ThreePoint": "review",
        "Lighting_Gameplay_Default": "default",
        "Lighting_HighContrast": "contrast",
        "Lighting_Adverse_Night": "night",
        "Lighting_Neutral_QA": "neutral",
    }[profile_id]
    resolution_short = {
        "reference_review": "review",
        "mobile_landscape_hard": "landscape",
        "mobile_narrow_portrait": "portrait",
    }[resolution_id]
    # Keep generated Windows paths well below MAX_PATH even when the package is
    # installed under a deep repository. Semantic metadata remains in the
    # report, so filenames do not need to duplicate every matrix dimension.
    relative = Path("renders") / (
        f"{variant.state_id}__{case_id}__{profile_short}"
        f"__{resolution_short}__{pass_id}.png"
    )
    path = ctx.output_dir / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(path)
    bpy.context.view_layer.update()
    bpy.ops.render.render(write_still=True)
    if ground is not None:
        bpy.data.objects.remove(ground, do_unlink=True)
    base.set_collection_visible(variant.collection, False)
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"render missing: {path}")
    return {
        "caseId": case_id,
        "assetId": ASSET_ID,
        "stateId": variant.state_id,
        "cameraId": camera_id,
        "lightingProfileId": profile_id,
        "backgroundId": background_id,
        "resolutionId": resolution_id,
        "passId": pass_id,
        "path": relative.as_posix(),
        "sha256": base.sha256_file(path),
    }


def render_full_matrix(
    ctx: base.BuildContext,
    camera: bpy.types.Object,
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    profiles = (
        "Lighting_Gameplay_Default",
        "Lighting_HighContrast",
        "Lighting_Adverse_Night",
        "Lighting_Neutral_QA",
    )
    for state in STATES:
        variant = ctx.variants[(ASSET_ID, state)]
        output.append(
            render_case(
                ctx,
                camera,
                variant,
                case_id="hero",
                camera_id="dynamic_hero_three_quarter",
                profile_id="Review_ThreePoint",
                background_id="review_ground",
                resolution_id="reference_review",
                pass_id="beauty",
            )
        )
        output.append(
            render_case(
                ctx,
                camera,
                variant,
                case_id="state_silhouette",
                camera_id="near",
                profile_id="Lighting_Neutral_QA",
                background_id="world_neutral_light",
                resolution_id="mobile_landscape_hard",
                pass_id="silhouette",
            )
        )
        for case_id, camera_id in (
            ("front_silhouette", "front"),
            ("back_silhouette", "back"),
        ):
            output.append(
                render_case(
                    ctx,
                    camera,
                    variant,
                    case_id=case_id,
                    camera_id=camera_id,
                    profile_id="Lighting_Neutral_QA",
                    background_id="world_neutral_light",
                    resolution_id="mobile_landscape_hard",
                    pass_id="silhouette",
                )
            )
        for profile_id in profiles:
            output.append(
                render_case(
                    ctx,
                    camera,
                    variant,
                    case_id="far_mobile",
                    camera_id="far",
                    profile_id=profile_id,
                    background_id="world_neutral_dark",
                    resolution_id="mobile_landscape_hard",
                    pass_id="beauty",
                )
            )
            output.append(
                render_case(
                    ctx,
                    camera,
                    variant,
                    case_id="portrait_mobile",
                    camera_id="near",
                    profile_id=profile_id,
                    background_id="world_neutral_dark",
                    resolution_id="mobile_narrow_portrait",
                    pass_id="beauty",
                )
            )
    if len(output) != 36:
        raise RuntimeError(f"transfer render matrix mismatch: {len(output)} != 36")
    return output


def main() -> int:
    args = parse_args()
    paths = {
        "contract": args.root / "art/transfer/turret-fast-v1.json",
        "territory": args.root / f"art/territories/{args.territory}.json",
        "calibration": args.root / "art/calibration/calibration-kit.json",
        "shapeLanguage": args.root / "art/shape-language/rules.json",
        "camera": args.root / "art/calibration/camera-rig.json",
        "lighting": args.root / "art/lighting/lighting-profiles.json",
        "materials": args.root / "art/materials/material-rules.json",
        "baseCompiler": args.root / "tools/blender/build_art_direction.py",
        "generator": Path(__file__).resolve(),
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise RuntimeError(f"missing canonical transfer inputs: {missing}")
    if args.output.exists() and not args.no_clean_output:
        shutil.rmtree(args.output)
    args.output.mkdir(parents=True, exist_ok=True)

    contract = base.load_json(paths["contract"])
    territory = base.load_json(paths["territory"])
    calibration = base.load_json(paths["calibration"])
    camera_rig = base.load_json(paths["camera"])
    lighting = base.load_json(paths["lighting"])
    material_rules = base.load_json(paths["materials"])
    if contract["assetId"] != ASSET_ID:
        raise RuntimeError("transfer contract asset ID mismatch")
    if territory["territoryId"] != args.territory:
        raise RuntimeError("territory ID mismatch")
    transfer_calibration = {
        "sharedRules": calibration["sharedRules"],
        "assets": {
            ASSET_ID: {
                "dimensions": contract["dimensions"],
                "pivot": contract["pivot"],
                "triangleBudgetMax": contract["triangleBudgetMax"],
                "textureBudgetClass": contract["textureBudgetClass"],
                "targetReadDistanceStuds": contract["targetReadDistanceStuds"],
                "function": contract["function"],
                "requiredStateVariants": contract["requiredStateVariants"],
            }
        },
    }

    seed = int(territory["automation"]["deterministicSeed"]) + 610_003
    random.seed(seed)
    base.clear_scene()
    scene = bpy.context.scene
    engine = base.choose_render_engine(scene)
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.frame_set(1)
    report: dict[str, Any] = {
        "$schema": SCHEMA,
        "schemaVersion": "1.0.0",
        "status": "PASS",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "assetId": ASSET_ID,
        "territoryId": args.territory,
        "rendererTruth": "BLENDER_TRANSFER_PREFLIGHT_ONLY_STUDIO_REMAINS_CANONICAL",
        "renderMode": args.render_mode,
        "toolchain": {
            "blenderVersion": bpy.app.version_string,
            "pythonVersion": sys.version,
            "renderEngine": engine,
            "deterministicSeed": seed,
            "generatorVersion": GENERATOR_VERSION,
        },
        "inputHashes": {name: base.sha256_file(path) for name, path in paths.items()},
        "cameraValidation": {},
        "grammarAudit": {},
        "variants": [],
        "exports": [],
        "renderEvidence": [],
        "expectedRenderCount": 36 if args.render_mode == "full" else 0,
        "actualRenderCount": 0,
        "issues": [],
        "notes": [
            "This is an independent transfer compiler; the five calibration assets and their generator were not changed.",
            "Blender evidence is preflight only. Human selection, Studio integration, and physical-device evidence remain separate authorities.",
        ],
    }
    ctx = base.BuildContext(
        territory,
        transfer_calibration,
        camera_rig,
        {},
        lighting,
        material_rules,
        args.output,
        args.render_mode,
        None,
        random.Random(seed),
        {},
        {},
        {},
        report,
    )
    base.ensure_materials(ctx)
    authored_angles: list[int] = []
    for state in STATES:
        variant, angles = build_variant(ctx, contract, state)
        authored_angles = angles
        ctx.variants[(ASSET_ID, state)] = variant
        report["variants"].append(variant.report)
        if variant.report["status"] != "PASS":
            report["issues"].extend(
                f"{state}: {issue}" for issue in variant.report["issues"]
            )

    report["grammarAudit"] = grammar_audit(ctx, contract, authored_angles)
    report["issues"].extend(report["grammarAudit"]["issues"])
    if report["issues"]:
        report["status"] = "FAIL"
        base.write_json(args.output / "transfer-build-report.json", report)
        raise RuntimeError("transfer geometry or grammar gate failed")

    camera = base.create_camera(scene, camera_rig)
    expected_fov = camera_rig["fieldOfView"]["degrees"]
    actual_fov = math.degrees(camera.data.angle_y)
    tolerance = camera_rig["cameraValidation"]["verticalFovToleranceDegrees"]
    report["cameraValidation"] = {
        "expectedVerticalFovDegrees": expected_fov,
        "actualVerticalFovDegrees": actual_fov,
        "toleranceDegrees": tolerance,
        "pass": abs(actual_fov - expected_fov) <= tolerance,
    }
    if not report["cameraValidation"]["pass"]:
        report["status"] = "FAIL"
        report["issues"].append("camera vertical FOV readback mismatch")
        base.write_json(args.output / "transfer-build-report.json", report)
        raise RuntimeError("transfer camera validation failed")

    for state in STATES:
        report["exports"].append(
            base.export_variant(ctx, ctx.variants[(ASSET_ID, state)])
        )
    blend_path = args.output / f"{args.territory}__{ASSET_ID}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    report["blendFile"] = {
        "path": blend_path.name,
        "bytes": blend_path.stat().st_size,
        "sha256": base.sha256_file(blend_path),
    }
    if args.render_mode == "full":
        report["renderEvidence"] = render_full_matrix(ctx, camera)
    report["actualRenderCount"] = len(report["renderEvidence"])
    base.write_json(args.output / "transfer-build-report.json", report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "assetId": ASSET_ID,
                "territoryId": args.territory,
                "report": str(args.output / "transfer-build-report.json"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        raise
