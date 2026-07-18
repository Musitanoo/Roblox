from __future__ import annotations

import copy
from typing import Any


class StateVariantError(ValueError):
    pass


def available_state_ids(contract: dict[str, Any]) -> list[str]:
    states = contract.get("states", {})
    variants = states.get("variants", []) if isinstance(states, dict) else []
    return [
        variant["id"]
        for variant in variants
        if isinstance(variant, dict) and isinstance(variant.get("id"), str)
    ]


def resolve_state_variant(
    contract: dict[str, Any],
    state_id: str | None = None,
) -> dict[str, Any]:
    states = contract.get("states")
    if not isinstance(states, dict):
        raise StateVariantError("asset contract has no states object")
    selected_state = state_id or states.get("default")
    variants = states.get("variants")
    if not isinstance(variants, list):
        raise StateVariantError("asset contract has no state variants")
    variant = next(
        (
            candidate
            for candidate in variants
            if isinstance(candidate, dict)
            and candidate.get("id") == selected_state
        ),
        None,
    )
    if variant is None:
        raise StateVariantError(
            f"unknown state {selected_state!r}; available={available_state_ids(contract)}"
        )

    resolved = copy.deepcopy(contract)
    parts = resolved["geometry"]["parts"]
    parts_by_name = {part["name"]: part for part in parts}
    for override in variant["partOverrides"]:
        target = parts_by_name[override["name"]]
        for key in ("position", "rotationDegrees", "material"):
            if key in override:
                target[key] = copy.deepcopy(override[key])
    resolved["_compiledStateId"] = selected_state
    resolved["_compiledStateDescription"] = variant["description"]
    return resolved
