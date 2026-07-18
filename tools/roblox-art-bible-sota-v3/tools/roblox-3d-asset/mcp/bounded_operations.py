from __future__ import annotations

from typing import Any

from mcp.security_policy import (
    ALLOWED_INVARIANTS,
    ALLOWED_OPERATION_TYPES,
    ALLOWED_VIEWS,
    WorkbenchError,
    ensure_change_set_id,
    finite_number,
)


AXIS_INDEX = {"designX": 0, "designY": 1, "designZ": 2}


def _part_map(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {part["name"]: part for part in contract["geometry"]["parts"]}


def _material_map(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {material["name"]: material for material in contract["materials"]}


def _number(operation: dict[str, Any], key: str) -> float:
    value = operation.get(key)
    if not finite_number(value):
        raise WorkbenchError(f"operation {key} must be a finite number")
    return float(value)


def validate_operation(
    operation: dict[str, Any],
    contract: dict[str, Any],
) -> None:
    operation_type = operation.get("type")
    if operation_type not in ALLOWED_OPERATION_TYPES:
        raise WorkbenchError(f"operation type is forbidden: {operation_type}")
    target = operation.get("target")
    if not isinstance(target, str) or not target:
        raise WorkbenchError("operation target must be a non-empty string")
    parts = _part_map(contract)
    materials = _material_map(contract)

    if operation_type == "SET_MATERIAL_VALUE":
        if target not in materials:
            raise WorkbenchError(f"undeclared material target: {target}")
        property_name = operation.get("property")
        if property_name not in {"roughness", "metallic"}:
            raise WorkbenchError("SET_MATERIAL_VALUE property must be roughness or metallic")
        before = _number(operation, "before")
        after = _number(operation, "after")
        if not 0 <= before <= 1 or not 0 <= after <= 1:
            raise WorkbenchError("material values must stay between 0 and 1")
        if abs(after - before) > 0.25:
            raise WorkbenchError("material value delta exceeds the 0.25 workbench bound")
        return

    if target not in parts:
        raise WorkbenchError(f"undeclared component target: {target}")

    if operation_type == "SET_COMPONENT_VISIBILITY":
        if not isinstance(operation.get("before"), bool) or not isinstance(
            operation.get("after"), bool
        ):
            raise WorkbenchError("visibility before/after must be booleans")
        return

    if operation_type == "SET_MATERIAL_ROLE":
        before = operation.get("before")
        after = operation.get("after")
        if before not in materials or after not in materials:
            raise WorkbenchError("material roles must reference declared materials")
        return

    axis = operation.get("axis")
    if axis not in AXIS_INDEX:
        raise WorkbenchError("operation axis must be designX, designY or designZ")
    before = _number(operation, "before")
    after = _number(operation, "after")
    delta = abs(after - before)
    if delta == 0:
        raise WorkbenchError("operation before and after values must differ")
    if operation_type == "SET_COMPONENT_DIMENSION":
        if before <= 0 or after <= 0:
            raise WorkbenchError("component dimensions must remain positive")
        if delta > 2.0 or delta / before > 0.5:
            raise WorkbenchError("dimension delta exceeds bounded exploration limits")
    elif operation_type == "MOVE_COMPONENT":
        if delta > 1.0:
            raise WorkbenchError("component movement exceeds the 1 stud bound")
    elif operation_type == "ROTATE_COMPONENT":
        if delta > 15.0:
            raise WorkbenchError("component rotation exceeds the 15 degree bound")


def validate_change_set(
    change_set: dict[str, Any],
    session: dict[str, Any],
    contract: dict[str, Any],
) -> None:
    ensure_change_set_id(str(change_set.get("changeSetId", "")))
    if change_set.get("schemaVersion") != "1.0.0":
        raise WorkbenchError("change set schemaVersion must be 1.0.0")
    if change_set.get("sessionId") != session["sessionId"]:
        raise WorkbenchError("change set sessionId differs from the open session")
    if change_set.get("assetKey") != contract["assetKey"]:
        raise WorkbenchError("change set assetKey differs from the contract")
    if change_set.get("baseBuildSha256") != session["reference"]["sha256"]:
        raise WorkbenchError("change set base build hash is stale")
    if change_set.get("assetContractSha256") != session["contract"]["sha256"]:
        raise WorkbenchError("change set asset contract hash is stale")
    if change_set.get("visualCanonId") != session["visualCanon"]["canonId"]:
        raise WorkbenchError("change set canon identity is stale")
    if change_set.get("visualCanonSha256") != session["visualCanon"]["sha256"]:
        raise WorkbenchError("change set canon hash is stale")
    if change_set.get("productionAuthorized") is not False:
        raise WorkbenchError("workbench change sets must keep productionAuthorized=false")
    operations = change_set.get("operations")
    if not isinstance(operations, list) or not operations:
        raise WorkbenchError("change set requires at least one operation")
    for operation in operations:
        if not isinstance(operation, dict):
            raise WorkbenchError("every operation must be an object")
        validate_operation(operation, contract)
    targets = change_set.get("targets")
    observed_targets = list(dict.fromkeys(op["target"] for op in operations))
    if targets != observed_targets:
        raise WorkbenchError("change set targets must exactly match operation targets")
    invariants = change_set.get("preservedInvariants")
    if not isinstance(invariants, list) or not invariants:
        raise WorkbenchError("change set requires preserved invariants")
    unknown_invariants = set(invariants) - ALLOWED_INVARIANTS
    if unknown_invariants:
        raise WorkbenchError(
            f"unknown invariants: {sorted(unknown_invariants)}"
        )
    views = change_set.get("requiredViews")
    if not isinstance(views, list) or not views or set(views) - ALLOWED_VIEWS:
        raise WorkbenchError("requiredViews contains an unsupported or empty view set")
    maximum_delta = change_set.get("maximumTriangleDelta")
    if not isinstance(maximum_delta, int) or not 0 <= maximum_delta <= 500:
        raise WorkbenchError("maximumTriangleDelta must be an integer between 0 and 500")


def source_bindings(
    change_set: dict[str, Any],
    contract: dict[str, Any],
) -> list[dict[str, Any]]:
    parts = contract["geometry"]["parts"]
    materials = contract["materials"]
    part_indexes = {part["name"]: index for index, part in enumerate(parts)}
    material_indexes = {
        material["name"]: index for index, material in enumerate(materials)
    }
    bindings: list[dict[str, Any]] = []
    for operation in change_set["operations"]:
        operation_type = operation["type"]
        target = operation["target"]
        if operation_type == "SET_COMPONENT_DIMENSION":
            pointer = (
                f"/geometry/parts/{part_indexes[target]}/size/"
                f"{AXIS_INDEX[operation['axis']]}"
            )
        elif operation_type == "MOVE_COMPONENT":
            pointer = (
                f"/geometry/parts/{part_indexes[target]}/position/"
                f"{AXIS_INDEX[operation['axis']]}"
            )
        elif operation_type == "ROTATE_COMPONENT":
            pointer = (
                f"/geometry/parts/{part_indexes[target]}/rotationDegrees/"
                f"{AXIS_INDEX[operation['axis']]}"
            )
        elif operation_type == "SET_MATERIAL_ROLE":
            pointer = f"/geometry/parts/{part_indexes[target]}/material"
        elif operation_type == "SET_MATERIAL_VALUE":
            pointer = (
                f"/materials/{material_indexes[target]}/{operation['property']}"
            )
        else:
            pointer = None
        bindings.append(
            {
                "operationType": operation_type,
                "target": target,
                "jsonPointer": pointer,
                "before": operation["before"],
                "after": operation["after"],
                "sourcePromotable": pointer is not None,
            }
        )
    return bindings
