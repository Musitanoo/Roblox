from __future__ import annotations

import math
import re
import hashlib
from pathlib import Path, PurePosixPath
from typing import Any

from pipeline.io_utils import read_json
from pipeline.status import Status


ASSET_KEY = re.compile(r"^[a-z][a-z0-9_]{2,63}$")
OBJECT_NAME = re.compile(r"^[A-Z][A-Za-z0-9_]{2,79}$")
STATE_ID = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
SUPPORTED_PARTS = {"box", "chamfered_box", "cylinder"}
CANON_STATUS_ORDER = {
    "DRAFT": 0,
    "CANDIDATE": 1,
    "ACCEPTED": 2,
    "LOCKED": 3,
    "REVISED": 3,
}
CANON_TRIANGLE_MAXIMUM = re.compile(
    r"^Triangle budget maximum is ([0-9][0-9,]*)\.$"
)
PACKAGE_PREFIX = ("tools", "roblox-art-bible-sota-v3")


def _repo_relative_path(configured_path: str) -> PurePosixPath:
    if not configured_path:
        raise ValueError("visualCanon.path must be a non-empty path")
    if "\\" in configured_path:
        raise ValueError(
            "visualCanon.path must use repository-portable forward slashes"
        )
    if (
        configured_path.startswith("/")
        or re.match(r"^[A-Za-z]:", configured_path)
        or ":" in configured_path
    ):
        raise ValueError("visualCanon.path must be repository-relative")
    requested = PurePosixPath(configured_path)
    if any(part in {".", ".."} for part in requested.parts):
        raise ValueError("visualCanon.path must not contain '.' or '..' segments")
    if requested.as_posix() != configured_path:
        raise ValueError("visualCanon.path must be normalized")
    if "canonical-visuals" not in requested.parts or requested.suffix != ".json":
        raise ValueError(
            "visualCanon.path must reference a JSON file under canonical-visuals"
        )
    return requested


def resolve_visual_canon_path(contract_path: Path, configured_path: str) -> Path:
    requested = _repo_relative_path(configured_path)
    repo = contract_path.resolve().parents[2]
    candidates = [repo.joinpath(*requested.parts)]
    if requested.parts[:2] == PACKAGE_PREFIX:
        candidates.append(repo.joinpath(*requested.parts[2:]))
    bounded_candidates: list[Path] = []
    for candidate in candidates:
        resolved = candidate.resolve()
        try:
            resolved.relative_to(repo)
        except ValueError as error:
            raise ValueError(
                "visualCanon.path resolves outside the repository root"
            ) from error
        bounded_candidates.append(resolved)
    for candidate in bounded_candidates:
        if candidate.is_file():
            return candidate
    return bounded_candidates[0]


def _finite_positive(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def _vector(value: Any, length: int = 3, *, positive: bool = False) -> bool:
    if not isinstance(value, list) or len(value) != length:
        return False
    for item in value:
        if not isinstance(item, (int, float)) or isinstance(item, bool) or not math.isfinite(item):
            return False
        if positive and item <= 0:
            return False
    return True


def _canon_triangle_maximum(canon: dict[str, Any]) -> int | None:
    constraints = canon.get("generationContract", {}).get("constraints", [])
    if not isinstance(constraints, list):
        return None
    matches = [
        CANON_TRIANGLE_MAXIMUM.fullmatch(value)
        for value in constraints
        if isinstance(value, str)
    ]
    parsed = [
        int(match.group(1).replace(",", ""))
        for match in matches
        if match is not None
    ]
    return parsed[0] if len(parsed) == 1 else None


def validate_contract_data(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if data.get("schemaVersion") != "1.0.0":
        errors.append("schemaVersion must be 1.0.0")
    asset_key = data.get("assetKey")
    if not isinstance(asset_key, str) or not ASSET_KEY.fullmatch(asset_key):
        errors.append("assetKey must match ^[a-z][a-z0-9_]{2,63}$")
    if not isinstance(data.get("revision"), int) or data.get("revision", 0) < 1:
        errors.append("revision must be an integer >= 1")

    visual_canon = data.get("visualCanon")
    if not isinstance(visual_canon, dict):
        errors.append("visualCanon must be an object")
    else:
        canon_id = visual_canon.get("canonId")
        if not isinstance(canon_id, str) or not re.fullmatch(
            r"^vc_[a-z0-9_]+__[a-z0-9-]+__v[0-9]+$", canon_id
        ):
            errors.append("visualCanon.canonId is invalid")
        if not isinstance(visual_canon.get("assetId"), str):
            errors.append("visualCanon.assetId must be a string")
        if not isinstance(visual_canon.get("territoryId"), str):
            errors.append("visualCanon.territoryId must be a string")
        path = visual_canon.get("path")
        if not isinstance(path, str):
            errors.append("visualCanon.path must be a string")
        else:
            try:
                _repo_relative_path(path)
            except ValueError as error:
                errors.append(str(error))
        digest = visual_canon.get("sha256")
        if not isinstance(digest, str) or not re.fullmatch(r"^[0-9a-f]{64}$", digest):
            errors.append("visualCanon.sha256 must be a lowercase SHA-256")
        if visual_canon.get("minimumStatus") not in {
            "CANDIDATE",
            "ACCEPTED",
            "LOCKED",
            "REVISED",
        }:
            errors.append("visualCanon.minimumStatus is invalid")
        if visual_canon.get("productionStatus") != "LOCKED":
            errors.append("visualCanon.productionStatus must be LOCKED")

    dimensions = data.get("dimensionsStuds")
    if not isinstance(dimensions, dict):
        errors.append("dimensionsStuds must be an object")
    else:
        for key in ("width", "height", "depth"):
            if not _finite_positive(dimensions.get(key)):
                errors.append(f"dimensionsStuds.{key} must be finite and > 0")
        tolerance = dimensions.get("tolerancePercent")
        if not isinstance(tolerance, (int, float)) or not 0 < tolerance <= 5:
            errors.append("dimensionsStuds.tolerancePercent must be > 0 and <= 5")

    if data.get("pivot") != "BASE_CENTER":
        errors.append("pivot must be BASE_CENTER for this vertical slice")

    budget = data.get("triangleBudget")
    if not isinstance(budget, dict):
        errors.append("triangleBudget must be an object")
    else:
        target = budget.get("target")
        maximum = budget.get("absoluteMaximum")
        if not isinstance(target, int) or target <= 0:
            errors.append("triangleBudget.target must be an integer > 0")
        if not isinstance(maximum, int) or maximum <= 0 or maximum > 20_000:
            errors.append("triangleBudget.absoluteMaximum must be between 1 and 20000")
        if isinstance(target, int) and isinstance(maximum, int) and target > maximum:
            errors.append("triangleBudget.target must not exceed absoluteMaximum")

    materials = data.get("materials")
    material_names: set[str] = set()
    if not isinstance(materials, list) or not materials:
        errors.append("materials must be a non-empty array")
    else:
        for index, material in enumerate(materials):
            prefix = f"materials[{index}]"
            if not isinstance(material, dict):
                errors.append(f"{prefix} must be an object")
                continue
            name = material.get("name")
            if not isinstance(name, str) or not OBJECT_NAME.fullmatch(name):
                errors.append(f"{prefix}.name is invalid")
            elif name in material_names:
                errors.append(f"duplicate material name: {name}")
            else:
                material_names.add(name)
            if not isinstance(material.get("color"), str) or not HEX_COLOR.fullmatch(material["color"]):
                errors.append(f"{prefix}.color must be #RRGGBB")
            for key in ("metallic", "roughness"):
                value = material.get(key)
                if not isinstance(value, (int, float)) or not 0 <= value <= 1:
                    errors.append(f"{prefix}.{key} must be between 0 and 1")
            emission_color = material.get("emissionColor")
            if emission_color is not None and (
                not isinstance(emission_color, str)
                or not HEX_COLOR.fullmatch(emission_color)
            ):
                errors.append(f"{prefix}.emissionColor must be #RRGGBB")
            emission_strength = material.get("emissionStrength", 0)
            if (
                not isinstance(emission_strength, (int, float))
                or isinstance(emission_strength, bool)
                or not math.isfinite(emission_strength)
                or not 0 <= emission_strength <= 20
            ):
                errors.append(
                    f"{prefix}.emissionStrength must be finite and between 0 and 20"
                )

    geometry = data.get("geometry")
    part_names: set[str] = set()
    if not isinstance(geometry, dict):
        errors.append("geometry must be an object")
    else:
        parts = geometry.get("parts")
        if not isinstance(parts, list) or not parts:
            errors.append("geometry.parts must be a non-empty array")
        else:
            for index, part in enumerate(parts):
                prefix = f"geometry.parts[{index}]"
                if not isinstance(part, dict):
                    errors.append(f"{prefix} must be an object")
                    continue
                name = part.get("name")
                if not isinstance(name, str) or not OBJECT_NAME.fullmatch(name):
                    errors.append(f"{prefix}.name is invalid")
                elif name in part_names:
                    errors.append(f"duplicate part name: {name}")
                else:
                    part_names.add(name)
                if part.get("type") not in SUPPORTED_PARTS:
                    errors.append(f"{prefix}.type must be one of {sorted(SUPPORTED_PARTS)}")
                if part.get("type") == "cylinder":
                    if part.get("axis", "Z") not in {"X", "Y", "Z"}:
                        errors.append(f"{prefix}.axis must be X, Y or Z")
                    segments = part.get("segments", 12)
                    if (
                        not isinstance(segments, int)
                        or isinstance(segments, bool)
                        or not 8 <= segments <= 32
                    ):
                        errors.append(
                            f"{prefix}.segments must be an integer between 8 and 32"
                        )
                size = part.get("size")
                if not _vector(size, positive=True):
                    errors.append(f"{prefix}.size must contain three finite positive numbers")
                elif part.get("type") == "chamfered_box":
                    chamfer = part.get("chamfer")
                    maximum_chamfer = min(size[0], size[1]) / 2
                    if (
                        not isinstance(chamfer, (int, float))
                        or isinstance(chamfer, bool)
                        or not math.isfinite(chamfer)
                        or not 0 < chamfer < maximum_chamfer
                    ):
                        errors.append(
                            f"{prefix}.chamfer must be finite, > 0 and less than "
                            "half the X/Y size"
                        )
                if not _vector(part.get("position")):
                    errors.append(f"{prefix}.position must contain three finite numbers")
                if not _vector(part.get("rotationDegrees", [0, 0, 0])):
                    errors.append(f"{prefix}.rotationDegrees must contain three finite numbers")
                bevel = part.get("bevel", 0)
                if (
                    not isinstance(bevel, (int, float))
                    or isinstance(bevel, bool)
                    or not math.isfinite(bevel)
                    or bevel < 0
                ):
                    errors.append(f"{prefix}.bevel must be finite and >= 0")
                elif (
                    isinstance(size, list)
                    and len(size) == 3
                    and all(_finite_positive(value) for value in size)
                    and bevel >= min(size) / 2
                ):
                    errors.append(
                        f"{prefix}.bevel must be less than half the smallest size"
                    )
                if part.get("material") not in material_names:
                    errors.append(f"{prefix}.material must reference a declared material")

    states = data.get("states")
    if not isinstance(states, dict):
        errors.append("states must be an object")
    else:
        variants = states.get("variants")
        state_ids: list[str] = []
        if not isinstance(variants, list) or not variants:
            errors.append("states.variants must be a non-empty array")
        else:
            for state_index, state in enumerate(variants):
                state_prefix = f"states.variants[{state_index}]"
                if not isinstance(state, dict):
                    errors.append(f"{state_prefix} must be an object")
                    continue
                unknown_state_keys = set(state) - {
                    "id",
                    "description",
                    "partOverrides",
                }
                if unknown_state_keys:
                    errors.append(
                        f"{state_prefix} contains unsupported keys: "
                        f"{sorted(unknown_state_keys)}"
                    )
                state_id = state.get("id")
                if not isinstance(state_id, str) or not STATE_ID.fullmatch(state_id):
                    errors.append(f"{state_prefix}.id is invalid")
                elif state_id in state_ids:
                    errors.append(f"duplicate state id: {state_id}")
                else:
                    state_ids.append(state_id)
                if not isinstance(state.get("description"), str) or not state[
                    "description"
                ].strip():
                    errors.append(f"{state_prefix}.description must be non-empty")
                overrides = state.get("partOverrides")
                if not isinstance(overrides, list):
                    errors.append(f"{state_prefix}.partOverrides must be an array")
                    continue
                overridden_names: set[str] = set()
                for override_index, override in enumerate(overrides):
                    prefix = (
                        f"{state_prefix}.partOverrides[{override_index}]"
                    )
                    if not isinstance(override, dict):
                        errors.append(f"{prefix} must be an object")
                        continue
                    unknown_override_keys = set(override) - {
                        "name",
                        "position",
                        "rotationDegrees",
                        "material",
                    }
                    if unknown_override_keys:
                        errors.append(
                            f"{prefix} contains unsupported keys: "
                            f"{sorted(unknown_override_keys)}"
                        )
                    name = override.get("name")
                    if name not in part_names:
                        errors.append(
                            f"{prefix}.name must reference a declared part"
                        )
                    elif name in overridden_names:
                        errors.append(
                            f"{state_prefix} overrides part {name} more than once"
                        )
                    else:
                        overridden_names.add(name)
                    if len(override) == 1:
                        errors.append(
                            f"{prefix} must change a transform or material"
                        )
                    if "position" in override and not _vector(
                        override["position"]
                    ):
                        errors.append(
                            f"{prefix}.position must contain three finite numbers"
                        )
                    if "rotationDegrees" in override and not _vector(
                        override["rotationDegrees"]
                    ):
                        errors.append(
                            f"{prefix}.rotationDegrees must contain three finite numbers"
                        )
                    if (
                        "material" in override
                        and override["material"] not in material_names
                    ):
                        errors.append(
                            f"{prefix}.material must reference a declared material"
                        )
        default_state = states.get("default")
        if default_state not in state_ids:
            errors.append("states.default must reference a declared state")

    publication = data.get("publication")
    if not isinstance(publication, dict):
        errors.append("publication must be an object")
    else:
        if publication.get("environment") != "staging":
            errors.append("publication.environment must be staging")
        if publication.get("createFormat") != "glb":
            errors.append("publication.createFormat must be glb")
        if publication.get("updateFormat") != "fbx":
            errors.append("publication.updateFormat must be fbx while Roblox content update is FBX-only")
        if publication.get("creatorType") not in {"User", "Group"}:
            errors.append("publication.creatorType must be User or Group")
        for key in ("apiKeyEnv", "creatorIdEnv", "creatorAllowlistEnv"):
            value = publication.get(key)
            if not isinstance(value, str) or not value.startswith("ROBLOX_"):
                errors.append(f"publication.{key} must name a ROBLOX_* environment variable")

    renders = data.get("renders")
    if not isinstance(renders, dict):
        errors.append("renders must be an object")
    else:
        resolution = renders.get("resolution")
        if not isinstance(resolution, int) or resolution < 256 or resolution > 2048:
            errors.append("renders.resolution must be between 256 and 2048")

    return errors


def validate_contract(path: Path) -> dict[str, Any]:
    try:
        data = read_json(path)
    except (OSError, ValueError) as error:
        return {"status": Status.FAIL.value, "path": str(path), "errors": [str(error)]}
    errors = validate_contract_data(data)
    visual_canon = data.get("visualCanon", {})
    canon_path: Path | None = None
    try:
        canon_path = resolve_visual_canon_path(
            path, str(visual_canon.get("path", ""))
        )
    except ValueError as error:
        if str(error) not in errors:
            errors.append(str(error))
    canon: dict[str, Any] | None = None
    if canon_path is None:
        pass
    elif not canon_path.is_file():
        errors.append(f"visual canon file is missing: {canon_path}")
    else:
        try:
            raw = canon_path.read_bytes()
            observed_hash = hashlib.sha256(raw).hexdigest()
            if observed_hash != visual_canon.get("sha256"):
                errors.append("visual canon SHA-256 differs from the asset contract")
            canon = read_json(canon_path)
        except (OSError, ValueError) as error:
            errors.append(f"visual canon cannot be read: {error}")
    if canon is not None:
        if canon.get("canonId") != visual_canon.get("canonId"):
            errors.append("visual canon ID differs from the asset contract")
        if canon.get("assetId") != visual_canon.get("assetId"):
            errors.append("visual canon assetId differs from the asset contract")
        if canon.get("territoryId") != visual_canon.get("territoryId"):
            errors.append("visual canon territoryId differs from the asset contract")
        observed_status = canon.get("status")
        minimum_status = visual_canon.get("minimumStatus")
        if (
            observed_status not in CANON_STATUS_ORDER
            or minimum_status not in CANON_STATUS_ORDER
            or CANON_STATUS_ORDER[observed_status]
            < CANON_STATUS_ORDER[minimum_status]
        ):
            errors.append(
                f"visual canon status {observed_status} is below required {minimum_status}"
            )
        dimensions = canon.get("dimensions", {})
        contract_dimensions = data.get("dimensionsStuds", {})
        for key in ("width", "height", "depth"):
            if dimensions.get(key) != contract_dimensions.get(key):
                errors.append(
                    f"visual canon dimension {key} differs from asset contract"
                )
        canon_state_ids = [
            state.get("id")
            for state in canon.get("states", [])
            if isinstance(state, dict)
        ]
        contract_state_ids = [
            state.get("id")
            for state in data.get("states", {}).get("variants", [])
            if isinstance(state, dict)
        ]
        if contract_state_ids != canon_state_ids:
            errors.append(
                "asset state order or coverage differs from visual canon: "
                f"asset={contract_state_ids}, canon={canon_state_ids}"
            )
        canon_triangle_maximum = _canon_triangle_maximum(canon)
        if canon_triangle_maximum is None:
            errors.append(
                "visual canon must declare exactly one machine-readable triangle maximum"
            )
        else:
            asset_triangle_maximum = data.get("triangleBudget", {}).get(
                "absoluteMaximum"
            )
            if (
                isinstance(asset_triangle_maximum, int)
                and asset_triangle_maximum > canon_triangle_maximum
            ):
                errors.append(
                    "asset triangle maximum "
                    f"{asset_triangle_maximum} exceeds visual canon maximum "
                    f"{canon_triangle_maximum}"
                )
    return {
        "status": Status.PASS.value if not errors else Status.FAIL.value,
        "path": str(path.resolve()),
        "assetKey": data.get("assetKey"),
        "revision": data.get("revision"),
        "visualCanon": {
            "path": str(canon_path) if canon_path is not None else None,
            "canonId": visual_canon.get("canonId"),
            "sha256": visual_canon.get("sha256"),
            "status": canon.get("status") if canon else None,
            "productionEligible": bool(
                canon
                and canon.get("status") == "LOCKED"
                and canon.get("visualPacket", {}).get("status") == "COMPLETE"
                and canon.get("approval", {}).get("status") == "APPROVED"
            ),
            "triangleMaximum": (
                _canon_triangle_maximum(canon) if canon is not None else None
            ),
        },
        "errors": errors,
    }
