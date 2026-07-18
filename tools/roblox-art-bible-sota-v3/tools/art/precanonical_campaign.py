from __future__ import annotations

import argparse
import re
import shutil
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.art.common import (
    ArtSystemError,
    ROOT,
    load_json,
    sha256_bytes,
    sha256_file,
    validate_with_schema,
    write_json,
)
from tools.art.precanonical import (
    CONSTITUTION_PATH,
    POLICY_PATH,
    SCHEMAS as PRECANONICAL_SCHEMAS,
    STAGE_VIEWS,
)

CAMPAIGN_SCHEMA = ROOT / "schemas/precanonical-campaign.schema.json"
CANON_SCHEMA = ROOT / "schemas/visual-canon.schema.json"
CANON_ROOT = ROOT / "art/canonical-visuals/salvaged-frontier"
REQUIRED_MODEL = "gpt-image-2"
DEFAULT_CAMPAIGN_ID = "salvaged-frontier-states-v2"
CAMPAIGN_VERSION = "2.0.0"
REVISED_CAMPAIGN_VERSION = "2.1.0"
FLEXIBLE_CAMPAIGN_VERSION = "2.2.0"
ACCEPTED_DECISIONS = {"PRECANONICAL_CANDIDATE", "HUMAN_SELECTED"}
ASSET_ORDER = (
    "barricade",
    "damage_effect",
    "enemy_standard",
    "floor_module",
    "objective_core",
    "turret_fast_v1",
)
EXPECTED_INSTANCE_COUNTS = {
    "barricade": 30,
    "damage_effect": 100,
    "enemy_standard": 100,
    "floor_module": 100,
    "objective_core": 1,
    "turret_fast_v1": 30,
}

FLEXIBLE_SELECTION_POLICY = {
    "globalOrderRequired": False,
    "promptAccess": "ALL_TASKS",
    "generationEligibility": "OBJECT_LOCAL_CONTINUITY",
    "activeTaskMutable": True,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _binding(path: Path, *, base: Path | None = None) -> dict[str, str]:
    resolved = path.resolve()
    rendered = str(resolved)
    if base is not None:
        try:
            rendered = resolved.relative_to(base.resolve()).as_posix()
        except ValueError:
            pass
    return {"path": rendered, "sha256": sha256_file(resolved)}


def _resolve_binding(
    binding: dict[str, str],
    *,
    base: Path,
) -> Path:
    raw = Path(binding["path"])
    return raw.resolve() if raw.is_absolute() else (base / raw).resolve()


def _verify_binding(
    binding: dict[str, str],
    *,
    base: Path,
    label: str,
) -> Path:
    path = _resolve_binding(binding, base=base)
    if not path.is_file():
        raise ArtSystemError(f"{label} is missing: {path}")
    if sha256_file(path) != binding["sha256"]:
        raise ArtSystemError(f"{label} hash drift: {path}")
    return path


def _rebase_binding(
    binding: dict[str, str] | None,
    *,
    source_base: Path,
    target_base: Path,
) -> dict[str, str] | None:
    if binding is None:
        return None
    return _binding(
        _verify_binding(
            binding,
            base=source_base,
            label="campaign revision evidence",
        ),
        base=target_base,
    )


def _assert_schema(value: Any, schema: Path, label: str) -> None:
    errors = validate_with_schema(value, schema)
    if errors:
        raise ArtSystemError(f"{label} schema validation failed: {'; '.join(errors)}")


def _snake(value: str) -> str:
    first = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    second = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", first)
    normalized = re.sub(r"[^a-zA-Z0-9]+", "_", second).strip("_").lower()
    return normalized or "component"


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in values if item.strip()))


def _load_canons() -> list[tuple[Path, dict[str, Any]]]:
    loaded: list[tuple[Path, dict[str, Any]]] = []
    for asset_id in ASSET_ORDER:
        path = CANON_ROOT / f"{asset_id}.json"
        canon = load_json(path)
        _assert_schema(canon, CANON_SCHEMA, f"visual canon {asset_id}")
        if canon["assetId"] != asset_id:
            raise ArtSystemError(f"Visual canon asset mismatch: {path}")
        if canon["territoryId"] != "salvaged-frontier":
            raise ArtSystemError(f"Visual canon territory mismatch: {path}")
        loaded.append((path, canon))
    return loaded


def _fresh_tasks(output: Path) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    ordinal = 0
    for object_ordinal, (canon_path, canon) in enumerate(_load_canons(), start=1):
        predecessor: str | None = None
        state_count = len(canon["states"])
        for state_ordinal, state in enumerate(canon["states"], start=1):
            ordinal += 1
            task_id = (
                f"{ordinal:02d}-{canon['assetId'].replace('_', '-')}-{state['id']}"
            )
            tasks.append(
                {
                    "taskId": task_id,
                    "ordinal": ordinal,
                    "objectOrdinal": object_ordinal,
                    "assetId": canon["assetId"],
                    "displayName": canon["identity"]["canonicalName"],
                    "stateId": state["id"],
                    "stateOrdinal": state_ordinal,
                    "stateCount": state_count,
                    "canon": _binding(canon_path, base=output),
                    "predecessorTaskId": predecessor,
                    "status": "PENDING",
                    "attempts": [],
                    "acceptedResult": None,
                    "acceptedReview": None,
                }
            )
            predecessor = task_id
    if len(tasks) != 16:
        raise ArtSystemError(
            f"Selected canons define {len(tasks)} states; campaign contract requires 16"
        )
    return tasks


def _source_brief(canon: dict[str, Any]) -> dict[str, Any]:
    components = []
    for component in canon["construction"]["components"]:
        mobility = component["mobility"]
        if mobility == "ephemeral":
            mobility = "mobile"
        components.append(
            {
                "id": _snake(component["id"]),
                "function": component["function"],
                "mobility": mobility,
            }
        )
    interaction_zones = [
        {
            "id": zone["id"],
            "purpose": zone["purpose"],
            "location": zone["vfxAnchor"],
            "requiredCue": (
                f"{zone['shapeRule']} {zone['valueRule']} "
                f"Color role: {zone['colorRole']}."
            ),
        }
        for zone in canon["semanticZones"]
    ]
    movements = _unique(
        cue
        for state in canon["states"]
        for cue in state["cues"]["motion"]
    )
    states = [
        {
            "id": state["id"],
            "visualChange": state["summary"] + " " + " ".join(state["changes"]),
            "invariants": state["invariants"],
        }
        for state in canon["states"]
    ]
    freedoms = [
        f"{item['id']}: {item['range']}. {item['justification']}"
        for item in canon["allowedVariations"]
    ]
    far = canon["silhouette"]["targetReadDistanceStuds"]
    dimensions = canon["dimensions"]
    return {
        "$schema": "https://roblox-top1.local/schemas/precanonical-brief.schema.json",
        "schemaVersion": "1.0.0",
        "briefId": f"{canon['assetId']}-salvaged-frontier-state-campaign",
        "assetKey": canon["assetId"],
        "displayName": canon["identity"]["canonicalName"],
        "artDirection": "salvaged-frontier",
        "gameplayFunction": canon["identity"]["gameplayFunction"],
        "oneSecondRead": canon["instantRead"]["oneSecondPromise"],
        "worldRole": canon["identity"]["worldRole"],
        "emotionalIntent": canon["identity"]["emotionalIntent"],
        "dimensionsStuds": {
            "width": dimensions["width"],
            "height": dimensions["height"],
            "depth": dimensions["depth"],
        },
        "orientation": {
            "front": canon["silhouette"]["views"]["front"],
            "playerSide": canon["instantRead"]["interactionCue"],
            "threatSide": canon["instantRead"]["dangerCue"],
        },
        "interactionZones": interaction_zones,
        "components": components,
        "movements": movements,
        "states": states,
        "collisionPromise": (
            f"Keep the {dimensions['pivot']} pivot, footprint and gameplay anchors "
            "identical in every generated state."
        ),
        "viewDistanceStuds": {
            "near": 3,
            "mid": max(10, round(far / 2)),
            "far": far,
        },
        "expectedSimultaneousInstances": EXPECTED_INSTANCE_COUNTS[canon["assetId"]],
        "obligations": canon["generationContract"]["obligations"],
        "constraints": canon["generationContract"]["constraints"],
        "freedoms": freedoms,
        "prohibitions": canon["forbidden"],
        "productionApproved": False,
    }


def _list_block(values: list[str]) -> str:
    return "\n".join(f"- {item}" for item in values)


def _component_block(canon: dict[str, Any]) -> str:
    return "\n".join(
        (
            f"- {item['id']}: {item['form']} at {item['position']}; "
            f"{item['function']} Relationship: {item['relationship']} "
            f"Reading role: {item['readingRole']}"
        )
        for item in canon["construction"]["components"]
    )


def _material_block(canon: dict[str, Any]) -> str:
    return "\n".join(
        (
            f"- {item['zoneId']}: {item['family']}; {item['semanticRole']}; "
            f"{item['valueRange']}; {item['surfaceFinish']} Wear: {item['wear']}"
        )
        for item in canon["materials"]
    )


def _style_discipline(canon: dict[str, Any]) -> str:
    profile = canon["generationContract"]["promptDiscipline"]
    return _list_block(
        profile["styleRules"]
        + [
            "The image is precanonical visual evidence only. It does not authorize hidden geometry, canon lock or production."
        ]
    )


def _state_prompt(
    canon: dict[str, Any],
    state: dict[str, Any],
    *,
    reference_kind: str | None,
    revision_instructions: list[str],
) -> str:
    dimensions = canon["dimensions"]
    cues = state["cues"]
    operations = "\n".join(
        (
            f"- {item['componentId']} / {item['operation']}: "
            f"{item['description']}"
        )
        for item in state["componentOperations"]
    )
    reference = (
        "\nCONTINUITY REFERENCE\n"
        "- Attach the exact hash-bound image shown by the operator.\n"
        "- It is the accepted previous gameplay state of this same object.\n"
        "- Transform that construction into the target state; do not redesign it.\n"
        "- Preserve footprint, camera-facing identity, component count, anchors, "
        "materials and recognition landmarks unless the target state explicitly "
        "changes a named component.\n"
        if reference_kind == "continuity"
        else (
            "\nTARGETED REVISION REFERENCE\n"
            "- Attach the exact hash-bound image shown by the operator.\n"
            "- It is the previous attempt for this same object and state.\n"
            "- Correct only the review findings while preserving every accepted "
            "identity, component and state cue.\n"
            if reference_kind == "revision"
            else "\nNO IMAGE REFERENCE\n- Construct only from this closed canon contract.\n"
        )
    )
    revisions = (
        "\nBOUND REVIEW INSTRUCTIONS\n" + _list_block(revision_instructions) + "\n"
        if revision_instructions
        else ""
    )
    prompt_discipline = canon["generationContract"]["promptDiscipline"]
    identity_lock = _list_block(prompt_discipline["identityLockRules"])
    gameplay_truth = state["gameplayTruth"]
    runtime_model = canon["runtimeStateModel"]
    overlay_ids = [
        item["id"] for item in runtime_model["operationalOverlays"]
    ]
    transient_ids = [item["id"] for item in runtime_model["transientStates"]]
    terminal = runtime_model["terminalState"]
    terminal_id = terminal["id"] if terminal is not None else "none"
    return f"""GPT IMAGE 2 — ONE OBJECT, ONE GAMEPLAY STATE, ONE IMAGE

Use the `gpt-image-2` image model. If that exact model is not selected or
visible in the interface, stop and do not substitute another model.

Generate exactly one image: a clean 2x2 state-definition board. Every quadrant
must depict the exact same object construction in the exact same target state.

CROSS-VIEW IDENTITY LOCK — THIS IS NOT A FOUR-CONCEPT SHEET
{identity_lock}

TARGET
- Object: {canon['identity']['canonicalName']} (`{canon['assetId']}`)
- State: `{state['id']}` only
- Art direction: Salvaged Frontier owns world identity; Industrial Toy Defense
  contributes disciplined one-second readability only.
- Canon: {canon['canonId']}
- Gameplay function: {canon['identity']['gameplayFunction']}
- One-second promise: {canon['instantRead']['oneSecondPromise']}
- Dimensions: {dimensions['width']} x {dimensions['height']} x
  {dimensions['depth']} Roblox studs; pivot {dimensions['pivot']}.

BOARD LAYOUT
- Top left: hero three-quarter front, complete object visible.
- Top right: three-quarter rear, same construction and state.
- Bottom left: solid black silhouette, no internal shading.
- Bottom right: elevated Roblox third-person mobile gameplay camera.
- Keep identical scale and recognizable proportions across the two perspective
  views; this is a turnaround proof, not a concept-variation sheet.
- Neutral mid-gray background, neutral studio light, no environment or props.
- No captions, labels, letters, numbers, logos or generated text in the image.
- Do not show intact/damaged/critical comparisons or any second gameplay state.

IDENTITY AND CONSTRUCTION
- World role: {canon['identity']['worldRole']}
- Emotional intent: {canon['identity']['emotionalIntent']}
- Territory thesis: {canon['identity']['territoryVisualThesis']}
- Front/orientation: {canon['instantRead']['orientationCue']}
- Interaction read: {canon['instantRead']['interactionCue']}
- Danger read: {canon['instantRead']['dangerCue']}
- Recognition landmarks: {", ".join(canon['silhouette']['recognitionLandmarks'])}
- Negative spaces: {", ".join(canon['silhouette']['negativeSpaces'])}

REQUIRED COMPONENTS
{_component_block(canon)}

FORM HIERARCHY
- Primary 72%: {", ".join(canon['formHierarchy']['primary'])}
- Secondary 23%: {", ".join(canon['formHierarchy']['secondary'])}
- Tertiary 5% maximum: {", ".join(canon['formHierarchy']['tertiary'])}
- Construction translation: {canon['formHierarchy']['territoryConstructionTranslation']}

MATERIAL SYSTEM
{_material_block(canon)}

TARGET STATE CONTRACT — `{state['id']}`
- Summary: {state['summary']}
- Required changes:
{_list_block(state['changes'])}
- Shape and silhouette cues:
{_list_block(cues['shape'])}
- Value cues:
{_list_block(cues['value'])}
- Color cues:
{_list_block(cues['color'])}
- Light cues:
{_list_block(cues['light'])}
- Motion posture implied in the still:
{_list_block(cues['motion'])}
- VFX cues, kept sparse and non-obscuring:
{_list_block(cues['vfx'])}
- Component operations:
{operations}
- Territory translation: {state['territoryTranslation']}

GAMEPLAY TRUTH BOUNDARY — DO NOT VISUALIZE UNPROVEN BEHAVIOR
- Contract status: {gameplay_truth['status']}
- Contract reference: {gameplay_truth['contractRef'] or 'none; visual candidate only'}
- Trigger: {gameplay_truth['trigger']}
- Capability effect: {gameplay_truth['capabilityEffect']}
- Collision effect: {gameplay_truth['collisionEffect']}
- Permitted visual claim: {gameplay_truth['visualClaim']}
- Hard claim boundary: {gameplay_truth['claimBoundary']}

RUNTIME STATE SCOPE — ONE PRIMARY STATE ONLY
- Primary generation states for this object:
  {", ".join(runtime_model['primaryGenerationStates'])}.
- This image depicts only `{state['id']}`. Do not compose operational overlays,
  transients or the terminal state into this primary reference.
- Operational overlays excluded from this image:
  {", ".join(overlay_ids) if overlay_ids else "none"}.
- Transient states excluded from this image:
  {", ".join(transient_ids) if transient_ids else "none"}.
- Terminal runtime-only state excluded from primary generation: {terminal_id}.
- Composition rule: {runtime_model['compositionRule']}
- Coverage boundary: {runtime_model['coverageBoundary']}

INVARIANTS — NEVER CHANGE
{_list_block(state['invariants'])}
{reference}{revisions}
STYLE DISCIPLINE
{_style_discipline(canon)}

FINAL OUTPUT SELF-CHECK — FAIL RATHER THAN IMPROVISE
{_list_block(prompt_discipline['outputSelfChecks'])}
"""


def _negative_constraints(canon: dict[str, Any], state_id: str) -> list[str]:
    shared = [
        "No text, captions, labels, letters, numbers, logos or invented alphabet.",
        "No four alternative concepts, silhouette variants or design options inside the four quadrants.",
        "No second gameplay state and no state comparison in the same image.",
        f"No interpretation other than the single target state {state_id}.",
        "No independent redesign between quadrants or between gameplay states.",
        "No photorealism, military realism, bleak monochrome or literal construction-toy identity.",
        "No color-only gameplay state; shape, silhouette, posture and value must agree.",
        "No invented rear, underside, mechanism, component, weapon or decoration.",
        "No geometric emblem, badge, pseudo-logo, triangular mark or unexplained assembly symbol.",
        "No cinematic depth of field, environmental scene or unrelated prop.",
        "No operational overlay, transient event or terminal runtime state mixed into the primary target state.",
        "No visual claim that exceeds the explicit gameplay-truth boundary.",
    ]
    prompt_discipline = canon["generationContract"]["promptDiscipline"]
    return _unique(
        shared + prompt_discipline["negativeRules"] + canon["forbidden"]
    )


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def _state_by_id(canon: dict[str, Any], state_id: str) -> dict[str, Any]:
    for state in canon["states"]:
        if state["id"] == state_id:
            return state
    raise ArtSystemError(f"State {state_id} is absent from canon {canon['canonId']}")


def _create_request(
    campaign_path: Path,
    task: dict[str, Any],
    *,
    parent_result: Path | None,
    reference_kind: str | None,
    revision_instructions: list[str],
) -> dict[str, Any]:
    campaign_root = campaign_path.parent
    attempt_index = len(task["attempts"]) + 1
    request_id = (
        f"{load_json(campaign_path)['campaignId']}-"
        f"{task['assetId'].replace('_', '-')}-{task['stateId']}-a{attempt_index:03d}"
    )
    request_dir = campaign_root / "requests" / request_id
    if request_dir.exists() and any(request_dir.iterdir()):
        raise ArtSystemError(f"Refusing to overwrite request directory: {request_dir}")
    request_dir.mkdir(parents=True, exist_ok=True)

    canon_path = _verify_binding(
        task["canon"],
        base=campaign_root,
        label=f"canon for {task['taskId']}",
    )
    canon = load_json(canon_path)
    state = _state_by_id(canon, task["stateId"])
    brief = _source_brief(canon)
    _assert_schema(brief, PRECANONICAL_SCHEMAS["brief"], "campaign source brief")

    source_brief = request_dir / "source-brief.json"
    brief_md = request_dir / "brief.md"
    prompt_path = request_dir / "prompt.txt"
    negative_path = request_dir / "negative-constraints.txt"
    views_path = request_dir / "requested-views.json"
    states_path = request_dir / "requested-states.json"
    write_json(source_brief, brief)
    _write_text(
        brief_md,
        f"""# {canon['identity']['canonicalName']} — {state['id']}

Status: `PRECANONICAL_SPEC_COMPLETE`

This task generates one image for one object and one gameplay state. It is
part of campaign `{load_json(campaign_path)['campaignId']}` and requires
`{REQUIRED_MODEL}` with visible UI confirmation.

The image remains non-canonical, does not prove hidden geometry and does not
approve production.
""",
    )
    prompt = _state_prompt(
        canon,
        state,
        reference_kind=reference_kind,
        revision_instructions=revision_instructions,
    )
    negatives = _negative_constraints(canon, state["id"])
    _write_text(prompt_path, prompt)
    _write_text(negative_path, "\n".join(f"- {item}" for item in negatives))
    views = {
        "schemaVersion": "1.0.0",
        "stage": "state_definition",
        "views": STAGE_VIEWS["state_definition"],
        "sameObjectAcrossViews": True,
    }
    requested_states = {
        "schemaVersion": "1.0.0",
        "states": [
            {
                "id": state["id"],
                "visualChange": state["summary"] + " " + " ".join(state["changes"]),
                "invariants": state["invariants"],
            }
        ],
        "independentStateDesignForbidden": True,
    }
    write_json(views_path, views)
    write_json(states_path, requested_states)

    parent_binding = (
        _binding(parent_result, base=request_dir)
        if parent_result is not None
        else None
    )
    request = {
        "$schema": "https://roblox-top1.local/schemas/precanonical-request.schema.json",
        "schemaVersion": "1.0.0",
        "requestId": request_id,
        "assetKey": task["assetId"],
        "artDirection": "salvaged-frontier",
        "generationSurface": "chatgpt_web_images",
        "status": "PRECANONICAL_SPEC_COMPLETE",
        "stage": "state_definition",
        "policy": {
            "path": "art/precanonical/policy.json",
            "sha256": sha256_file(POLICY_PATH),
        },
        "constitution": {
            "path": "art/selected/salvaged-frontier-constitution.json",
            "sha256": sha256_file(CONSTITUTION_PATH),
        },
        "compiler": {
            "path": "tools/art/precanonical_campaign.py",
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "sourceBrief": _binding(source_brief, base=request_dir),
        "parentResult": parent_binding,
        "revisionInstructions": revision_instructions,
        "files": {
            "brief": _binding(brief_md, base=request_dir),
            "prompt": _binding(prompt_path, base=request_dir),
            "negativeConstraints": _binding(negative_path, base=request_dir),
            "requestedViews": _binding(views_path, base=request_dir),
            "requestedStates": _binding(states_path, base=request_dir),
        },
        "promptHash": sha256_file(prompt_path),
        "requestedViewIds": views["views"],
        "requestedStateIds": [state["id"]],
        "imageSpec": {
            "aspectRatio": "1:1",
            "background": "neutral_mid_gray",
            "lighting": "neutral_studio",
            "singleObjectOnly": True,
        },
        "budget": {
            "maximumWebGenerations": 1,
            "consumedWebGenerations": 0,
            "reserveForCorrections": 0,
            "humanConfirmationRequired": True,
        },
        "automation": {
            "browserAdapter": "codex_chrome",
            "automaticSubmissionAuthorized": False,
            "automaticRetry": False,
            "automaticCodexImageFallback": False,
            "automaticApiFallback": False,
            "browserReasoningForbidden": True,
        },
        "authority": {
            "canonical": False,
            "geometryAuthority": False,
            "humanSelectionRequired": True,
            "productionApproved": False,
        },
    }
    _assert_schema(request, PRECANONICAL_SCHEMAS["request"], "campaign request")
    request_path = request_dir / "request.json"
    write_json(request_path, request)
    return {
        "attemptIndex": attempt_index,
        "request": _binding(request_path, base=campaign_root),
        "result": None,
        "review": None,
        "decision": None,
        "continuitySource": (
            _binding(parent_result, base=campaign_root)
            if reference_kind == "continuity" and parent_result is not None
            else None
        ),
        "revisionSource": (
            _binding(parent_result, base=campaign_root)
            if reference_kind == "revision" and parent_result is not None
            else None
        ),
    }


def _task(campaign: dict[str, Any], task_id: str) -> dict[str, Any]:
    for task in campaign["tasks"]:
        if task["taskId"] == task_id:
            return task
    raise ArtSystemError(f"Unknown campaign task: {task_id}")


def _accepted_predecessor(
    campaign: dict[str, Any],
    task: dict[str, Any],
    *,
    campaign_root: Path,
) -> Path | None:
    predecessor_id = task["predecessorTaskId"]
    if predecessor_id is None:
        return None
    predecessor = _task(campaign, predecessor_id)
    if predecessor["status"] != "ACCEPTED" or predecessor["acceptedResult"] is None:
        raise ArtSystemError(
            f"Task {task['taskId']} requires accepted predecessor {predecessor_id}"
        )
    return _verify_binding(
        predecessor["acceptedResult"],
        base=campaign_root,
        label=f"accepted predecessor {predecessor_id}",
    )


def _generation_eligible(
    campaign: dict[str, Any],
    task: dict[str, Any],
) -> bool:
    if task["status"] in {"ACCEPTED", "BLOCKED", "VISUAL_REVIEW_REQUIRED"}:
        return False
    predecessor_id = task["predecessorTaskId"]
    if predecessor_id is None:
        return True
    predecessor = _task(campaign, predecessor_id)
    return (
        predecessor["status"] == "ACCEPTED"
        and predecessor["acceptedResult"] is not None
    )


def _ensure_task_request(
    campaign_path: Path,
    campaign: dict[str, Any],
    task: dict[str, Any],
    *,
    revision_instructions: list[str] | None = None,
) -> None:
    if task["attempts"]:
        if task["status"] == "PENDING":
            task["status"] = "READY"
        return
    if not _generation_eligible(campaign, task):
        raise ArtSystemError(
            f"Task {task['taskId']} is not generation-eligible; "
            "its object-local predecessor must be accepted first"
        )
    parent = _accepted_predecessor(
        campaign,
        task,
        campaign_root=campaign_path.parent,
    )
    task["status"] = "READY"
    task["attempts"].append(
        _create_request(
            campaign_path,
            task,
            parent_result=parent,
            reference_kind="continuity" if parent is not None else None,
            revision_instructions=revision_instructions or [],
        )
    )


def _actionable_tasks(
    campaign: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        task
        for task in campaign["tasks"]
        if task["status"] in {"READY", "VISUAL_REVIEW_REQUIRED"}
    ]


def activate_campaign_task(
    campaign_path: Path,
    task_id: str,
) -> dict[str, Any]:
    campaign_path = campaign_path.resolve()
    campaign = verify_campaign(campaign_path)
    if campaign["status"] != "ACTIVE":
        raise ArtSystemError("Only an active campaign can change generation target")
    task = _task(campaign, task_id)
    if task["status"] == "ACCEPTED":
        raise ArtSystemError("This object-state is already accepted and is read-only")
    if task["status"] == "BLOCKED":
        raise ArtSystemError("This object-state exhausted its bounded attempts")
    if task["status"] == "PENDING":
        _ensure_task_request(campaign_path, campaign, task)
    elif not task["attempts"]:
        raise ArtSystemError(f"Actionable task lacks a request: {task_id}")
    campaign["currentTaskId"] = task_id
    _save_campaign(campaign_path, campaign)
    return verify_campaign(campaign_path)


def campaign_task_prompt(
    campaign_path: Path,
    task_id: str,
) -> dict[str, Any]:
    campaign_path = campaign_path.resolve()
    campaign = verify_campaign(campaign_path)
    task = _task(campaign, task_id)
    generation_eligible = _generation_eligible(campaign, task)
    if task["attempts"]:
        request_path = _verify_binding(
            task["attempts"][-1]["request"],
            base=campaign_path.parent,
            label=f"prompt request for {task_id}",
        )
        request = load_json(request_path)
        prompt_path = _verify_binding(
            request["files"]["prompt"],
            base=request_path.parent,
            label=f"prompt file for {task_id}",
        )
        negatives_path = _verify_binding(
            request["files"]["negativeConstraints"],
            base=request_path.parent,
            label=f"negative constraints for {task_id}",
        )
        prompt = prompt_path.read_text(encoding="utf-8").strip()
        negatives = [
            line[2:].strip()
            for line in negatives_path.read_text(encoding="utf-8").splitlines()
            if line.startswith("- ")
        ]
        exact = True
        request_id = request["requestId"]
        prompt_hash = request["promptHash"]
    else:
        canon_path = _verify_binding(
            task["canon"],
            base=campaign_path.parent,
            label=f"preview canon for {task_id}",
        )
        canon = load_json(canon_path)
        state = _state_by_id(canon, task["stateId"])
        prompt = _state_prompt(
            canon,
            state,
            reference_kind=None,
            revision_instructions=[],
        )
        negatives = _negative_constraints(canon, task["stateId"])
        exact = False
        request_id = None
        prompt_hash = sha256_bytes(prompt.encode("utf-8"))
    submission_text = "\n".join(
        [
            prompt.strip(),
            "",
            "STRICT BOUND NEGATIVE CONSTRAINTS",
            *[f"- {item}" for item in negatives],
        ]
    ).strip()
    if task["status"] == "ACCEPTED":
        activation_status = "ACCEPTED"
    elif task["status"] == "VISUAL_REVIEW_REQUIRED":
        activation_status = "REVIEW_REQUIRED"
    elif task["status"] == "BLOCKED":
        activation_status = "BLOCKED"
    elif generation_eligible:
        activation_status = "AVAILABLE"
    else:
        activation_status = "CONTINUITY_REQUIRED"
    return {
        "taskId": task_id,
        "requestId": request_id,
        "exactTransportPrompt": exact,
        "previewOnly": not exact,
        "promptHash": prompt_hash,
        "submissionText": submission_text,
        "submissionTextSha256": sha256_bytes(submission_text.encode("utf-8")),
        "generationEligible": generation_eligible,
        "activationStatus": activation_status,
        "predecessorTaskId": task["predecessorTaskId"],
    }


def _recompute_progress(campaign: dict[str, Any]) -> None:
    completed_tasks = sum(task["status"] == "ACCEPTED" for task in campaign["tasks"])
    completed_objects = 0
    for asset_id in ASSET_ORDER:
        object_tasks = [
            task for task in campaign["tasks"] if task["assetId"] == asset_id
        ]
        if object_tasks and all(task["status"] == "ACCEPTED" for task in object_tasks):
            completed_objects += 1
    campaign["progress"] = {
        "totalObjects": len(ASSET_ORDER),
        "completedObjects": completed_objects,
        "totalTasks": len(campaign["tasks"]),
        "completedTasks": completed_tasks,
        "remainingTasks": len(campaign["tasks"]) - completed_tasks,
    }
    if completed_tasks == len(campaign["tasks"]):
        campaign["status"] = "COMPLETE"
        campaign["currentTaskId"] = None


def _save_campaign(campaign_path: Path, campaign: dict[str, Any]) -> None:
    campaign["updatedAt"] = _utc_now()
    _recompute_progress(campaign)
    _assert_schema(campaign, CAMPAIGN_SCHEMA, "precanonical campaign")
    write_json(campaign_path, campaign)


def init_campaign(
    output: Path,
    campaign_id: str = DEFAULT_CAMPAIGN_ID,
    max_attempts_per_task: int = 3,
) -> Path:
    output = output.resolve()
    campaign_path = output / "campaign.json"
    if campaign_path.is_file():
        verify_campaign(campaign_path)
        return campaign_path
    if output.exists() and any(output.iterdir()):
        raise ArtSystemError(f"Refusing to overwrite non-empty campaign directory: {output}")
    if max_attempts_per_task < 1 or max_attempts_per_task > 5:
        raise ArtSystemError("maxAttemptsPerTask must be between 1 and 5")
    output.mkdir(parents=True, exist_ok=True)
    now = _utc_now()
    tasks = _fresh_tasks(output)
    campaign = {
        "$schema": "https://roblox-top1.local/schemas/precanonical-campaign.schema.json",
        "schemaVersion": "1.0.0",
        "campaignVersion": FLEXIBLE_CAMPAIGN_VERSION,
        "campaignId": campaign_id,
        "createdAt": now,
        "updatedAt": now,
        "status": "ACTIVE",
        "artDirection": "salvaged-frontier",
        "requiredModel": REQUIRED_MODEL,
        "generationSurface": "chatgpt_web_images",
        "oneGenerationPerObjectState": True,
        "independentStateDesignForbidden": True,
        "maxAttemptsPerTask": max_attempts_per_task,
        "currentTaskId": tasks[0]["taskId"],
        "selectionPolicy": dict(FLEXIBLE_SELECTION_POLICY),
        "objectOrder": list(ASSET_ORDER),
        "tasks": tasks,
        "progress": {
            "totalObjects": 6,
            "completedObjects": 0,
            "totalTasks": 16,
            "completedTasks": 0,
            "remainingTasks": 16,
        },
        "canonical": False,
        "productionApproved": False,
    }
    write_json(campaign_path, campaign)
    for task in tasks:
        if task["predecessorTaskId"] is None:
            _ensure_task_request(campaign_path, campaign, task)
    _save_campaign(campaign_path, campaign)
    verify_campaign(campaign_path)
    return campaign_path


def snapshot_campaign_canons(campaign_path: Path) -> dict[str, Any]:
    campaign_path = campaign_path.resolve()
    campaign_root = campaign_path.parent
    campaign = verify_campaign(campaign_path)
    snapshot_root = campaign_root / "canons"
    snapshot_root.mkdir(parents=True, exist_ok=True)
    snapshots: dict[str, dict[str, str]] = {}
    for task in campaign["tasks"]:
        asset_id = task["assetId"]
        if asset_id not in snapshots:
            source = _verify_binding(
                task["canon"],
                base=campaign_root,
                label=f"source canon for {asset_id}",
            )
            target = snapshot_root / f"{asset_id}.json"
            if target.is_file():
                if sha256_file(target) != task["canon"]["sha256"]:
                    raise ArtSystemError(
                        f"Refusing to overwrite different canon snapshot: {target}"
                    )
            else:
                shutil.copyfile(source, target)
            snapshots[asset_id] = _binding(target, base=campaign_root)
        task["canon"] = snapshots[asset_id]
    _save_campaign(campaign_path, campaign)
    return verify_campaign(campaign_path)


def _rebase_carried_task(
    source_task: dict[str, Any],
    *,
    source_base: Path,
    target_base: Path,
) -> dict[str, Any]:
    carried = deepcopy(source_task)
    carried["canon"] = _rebase_binding(
        carried["canon"],
        source_base=source_base,
        target_base=target_base,
    )
    carried["acceptedResult"] = _rebase_binding(
        carried["acceptedResult"],
        source_base=source_base,
        target_base=target_base,
    )
    carried["acceptedReview"] = _rebase_binding(
        carried["acceptedReview"],
        source_base=source_base,
        target_base=target_base,
    )
    for attempt in carried["attempts"]:
        for field in (
            "request",
            "result",
            "review",
            "continuitySource",
            "revisionSource",
        ):
            attempt[field] = _rebase_binding(
                attempt[field],
                source_base=source_base,
                target_base=target_base,
            )
    return carried


def fork_campaign(
    source_campaign_path: Path,
    output: Path,
    campaign_id: str,
    restart_task_id: str,
    reason: str,
) -> Path:
    source_campaign_path = source_campaign_path.resolve()
    source_root = source_campaign_path.parent
    source = verify_campaign(source_campaign_path)
    output = output.resolve()
    campaign_path = output / "campaign.json"
    if campaign_path.is_file():
        verify_campaign(campaign_path)
        return campaign_path
    if output.exists() and any(output.iterdir()):
        raise ArtSystemError(
            f"Refusing to overwrite non-empty revised campaign directory: {output}"
        )
    if len(reason.strip()) < 30:
        raise ArtSystemError("Campaign revision reason must contain at least 30 characters")

    fresh_tasks = _fresh_tasks(output)
    fresh_by_id = {task["taskId"]: task for task in fresh_tasks}
    if restart_task_id not in fresh_by_id:
        raise ArtSystemError(f"Unknown restart task: {restart_task_id}")
    restart_ordinal = fresh_by_id[restart_task_id]["ordinal"]
    source_by_id = {task["taskId"]: task for task in source["tasks"]}
    carried_ids: list[str] = []
    tasks: list[dict[str, Any]] = []
    for fresh in fresh_tasks:
        if fresh["ordinal"] >= restart_ordinal:
            tasks.append(fresh)
            continue
        previous = source_by_id[fresh["taskId"]]
        if previous["status"] != "ACCEPTED":
            raise ArtSystemError(
                f"Cannot carry non-accepted task before restart: {fresh['taskId']}"
            )
        tasks.append(
            _rebase_carried_task(
                previous,
                source_base=source_root,
                target_base=output,
            )
        )
        carried_ids.append(fresh["taskId"])

    superseded_ids = [
        task["taskId"]
        for task in source["tasks"]
        if task["ordinal"] >= restart_ordinal
        and (
            task["status"] == "ACCEPTED"
            or task["taskId"] == restart_task_id
        )
    ]
    if not superseded_ids:
        raise ArtSystemError(
            "Revised campaign must supersede its restart task or accepted evidence"
        )

    source["status"] = "BLOCKED"
    source["currentTaskId"] = None
    _save_campaign(source_campaign_path, source)
    source = verify_campaign(source_campaign_path)

    output.mkdir(parents=True, exist_ok=False)
    now = _utc_now()
    restart_task = next(task for task in tasks if task["taskId"] == restart_task_id)
    campaign = {
        "$schema": "https://roblox-top1.local/schemas/precanonical-campaign.schema.json",
        "schemaVersion": "1.0.0",
        "campaignVersion": FLEXIBLE_CAMPAIGN_VERSION,
        "campaignId": campaign_id,
        "createdAt": now,
        "updatedAt": now,
        "status": "ACTIVE",
        "artDirection": "salvaged-frontier",
        "requiredModel": REQUIRED_MODEL,
        "generationSurface": "chatgpt_web_images",
        "oneGenerationPerObjectState": True,
        "independentStateDesignForbidden": True,
        "maxAttemptsPerTask": source["maxAttemptsPerTask"],
        "currentTaskId": restart_task_id,
        "selectionPolicy": dict(FLEXIBLE_SELECTION_POLICY),
        "objectOrder": list(ASSET_ORDER),
        "revision": {
            "sourceCampaign": _binding(source_campaign_path, base=output),
            "reason": reason.strip(),
            "restartTaskId": restart_task_id,
            "carriedTaskIds": carried_ids,
            "supersededTaskIds": superseded_ids,
        },
        "tasks": tasks,
        "progress": {
            "totalObjects": 6,
            "completedObjects": 0,
            "totalTasks": 16,
            "completedTasks": 0,
            "remainingTasks": 16,
        },
        "canonical": False,
        "productionApproved": False,
    }
    write_json(campaign_path, campaign)
    for task in tasks:
        should_prepare = (
            task["taskId"] == restart_task_id
            or (
                task["predecessorTaskId"] is None
                and task["status"] != "ACCEPTED"
            )
        )
        if not should_prepare:
            continue
        _ensure_task_request(
            campaign_path,
            campaign,
            task,
            revision_instructions=(
                [
                    "Rebuild from the revised visual canon. Do not reuse or imitate "
                    "the superseded robot, mech, armored golem or brute-like result."
                ]
                if task["taskId"] == restart_task_id
                else []
            ),
        )
    _save_campaign(campaign_path, campaign)
    verify_campaign(campaign_path)
    return campaign_path


def fork_campaign_control_revision(
    source_campaign_path: Path,
    output: Path,
    campaign_id: str,
    reason: str,
) -> Path:
    """Refresh unused requests without changing campaign-bound visual canons."""

    source_campaign_path = source_campaign_path.resolve()
    source_root = source_campaign_path.parent
    source = verify_campaign(source_campaign_path)
    if source["status"] != "ACTIVE":
        raise ArtSystemError("Control revision source must be ACTIVE")
    if len(reason.strip()) < 30:
        raise ArtSystemError("Control revision reason must contain at least 30 characters")

    output = output.resolve()
    campaign_path = output / "campaign.json"
    if campaign_path.is_file():
        return campaign_path
    if output.exists() and any(output.iterdir()):
        raise ArtSystemError(
            f"Refusing to overwrite non-empty control revision directory: {output}"
        )

    carried_ids: list[str] = []
    superseded_ids: list[str] = []
    tasks: list[dict[str, Any]] = []
    for source_task in source["tasks"]:
        if source_task["status"] == "ACCEPTED":
            tasks.append(
                _rebase_carried_task(
                    source_task,
                    source_base=source_root,
                    target_base=output,
                )
            )
            carried_ids.append(source_task["taskId"])
            continue
        if source_task["attempts"]:
            superseded_ids.append(source_task["taskId"])
        tasks.append(
            {
                "taskId": source_task["taskId"],
                "ordinal": source_task["ordinal"],
                "objectOrdinal": source_task["objectOrdinal"],
                "assetId": source_task["assetId"],
                "displayName": source_task["displayName"],
                "stateId": source_task["stateId"],
                "stateOrdinal": source_task["stateOrdinal"],
                "stateCount": source_task["stateCount"],
                "canon": _rebase_binding(
                    source_task["canon"],
                    source_base=source_root,
                    target_base=output,
                ),
                "predecessorTaskId": source_task["predecessorTaskId"],
                "status": "PENDING",
                "attempts": [],
                "acceptedResult": None,
                "acceptedReview": None,
            }
        )
    if not superseded_ids:
        raise ArtSystemError("Control revision requires at least one unused request")

    output.mkdir(parents=True, exist_ok=False)
    now = _utc_now()
    campaign = {
        "$schema": "https://roblox-top1.local/schemas/precanonical-campaign.schema.json",
        "schemaVersion": "1.0.0",
        "campaignVersion": FLEXIBLE_CAMPAIGN_VERSION,
        "campaignId": campaign_id,
        "createdAt": now,
        "updatedAt": now,
        "status": "ACTIVE",
        "artDirection": source["artDirection"],
        "requiredModel": source["requiredModel"],
        "generationSurface": source["generationSurface"],
        "oneGenerationPerObjectState": True,
        "independentStateDesignForbidden": True,
        "maxAttemptsPerTask": source["maxAttemptsPerTask"],
        "currentTaskId": source["currentTaskId"],
        "selectionPolicy": dict(FLEXIBLE_SELECTION_POLICY),
        "objectOrder": list(ASSET_ORDER),
        "revision": {
            "sourceCampaign": _binding(source_campaign_path, base=output),
            "reason": reason.strip(),
            "restartTaskId": source["currentTaskId"],
            "carriedTaskIds": carried_ids,
            "supersededTaskIds": superseded_ids,
        },
        "tasks": tasks,
        "progress": {
            "totalObjects": 6,
            "completedObjects": 0,
            "totalTasks": 16,
            "completedTasks": 0,
            "remainingTasks": 16,
        },
        "canonical": False,
        "productionApproved": False,
    }
    write_json(campaign_path, campaign)
    for task in tasks:
        if task["status"] == "ACCEPTED" or not _generation_eligible(campaign, task):
            continue
        _ensure_task_request(campaign_path, campaign, task)
    _save_campaign(campaign_path, campaign)

    source["status"] = "BLOCKED"
    source["currentTaskId"] = None
    _save_campaign(source_campaign_path, source)
    verify_campaign(source_campaign_path)
    campaign["revision"]["sourceCampaign"] = _binding(
        source_campaign_path,
        base=output,
    )
    _save_campaign(campaign_path, campaign)
    verify_campaign(campaign_path)
    return campaign_path


def verify_campaign(campaign_path: Path) -> dict[str, Any]:
    campaign_path = campaign_path.resolve()
    campaign_root = campaign_path.parent
    campaign = load_json(campaign_path)
    _assert_schema(campaign, CAMPAIGN_SCHEMA, "precanonical campaign")
    if campaign["requiredModel"] != REQUIRED_MODEL:
        raise ArtSystemError("Campaign model contract drift")
    if campaign["objectOrder"] != list(ASSET_ORDER):
        raise ArtSystemError("Campaign object order drift")
    if campaign["campaignVersion"] == FLEXIBLE_CAMPAIGN_VERSION:
        if campaign.get("selectionPolicy") != FLEXIBLE_SELECTION_POLICY:
            raise ArtSystemError("Flexible campaign selection policy drift")
    revision = campaign.get("revision")
    if revision is not None:
        source_campaign = _verify_binding(
            revision["sourceCampaign"],
            base=campaign_root,
            label="source campaign for revision",
        )
        source = load_json(source_campaign)
        _assert_schema(source, CAMPAIGN_SCHEMA, "source campaign for revision")
        if source["status"] != "BLOCKED":
            raise ArtSystemError("Revised campaign source must be frozen as BLOCKED")
        carried = set(revision["carriedTaskIds"])
        superseded = set(revision["supersededTaskIds"])
        if carried & superseded:
            raise ArtSystemError("Carried and superseded task sets overlap")
        if revision["restartTaskId"] not in {
            task["taskId"] for task in campaign["tasks"]
        }:
            raise ArtSystemError("Campaign revision restart task is absent")
    expected: list[tuple[str, str]] = []
    canons: dict[str, tuple[Path, dict[str, Any]]] = {}
    for task in campaign["tasks"]:
        asset_id = task["assetId"]
        if asset_id in canons:
            continue
        canon_path = _verify_binding(
            task["canon"],
            base=campaign_root,
            label=f"campaign-bound canon for {asset_id}",
        )
        canon = load_json(canon_path)
        if canon["assetId"] != asset_id:
            raise ArtSystemError(f"Campaign/canon asset mismatch: {asset_id}")
        if canon["territoryId"] != "salvaged-frontier":
            raise ArtSystemError(f"Campaign/canon territory mismatch: {asset_id}")
        canons[asset_id] = (canon_path, canon)
    for asset_id in ASSET_ORDER:
        if asset_id not in canons:
            raise ArtSystemError(f"Campaign is missing canon for {asset_id}")
        expected.extend((asset_id, state["id"]) for state in canons[asset_id][1]["states"])
    observed = [(task["assetId"], task["stateId"]) for task in campaign["tasks"]]
    if observed != expected:
        raise ArtSystemError("Campaign object-state coverage or order drift")
    if len({task["taskId"] for task in campaign["tasks"]}) != len(campaign["tasks"]):
        raise ArtSystemError("Campaign contains duplicate task IDs")

    for task in campaign["tasks"]:
        canon_path = _verify_binding(
            task["canon"],
            base=campaign_root,
            label=f"canon for {task['taskId']}",
        )
        canon = load_json(canon_path)
        if canon["assetId"] != task["assetId"]:
            raise ArtSystemError(f"Task/canon asset mismatch: {task['taskId']}")
        if task["stateId"] not in {state["id"] for state in canon["states"]}:
            raise ArtSystemError(f"Task state absent from canon: {task['taskId']}")
        for index, attempt in enumerate(task["attempts"], start=1):
            if attempt["attemptIndex"] != index:
                raise ArtSystemError(f"Attempt sequence drift: {task['taskId']}")
            request_path = _verify_binding(
                attempt["request"],
                base=campaign_root,
                label=f"request for {task['taskId']} attempt {index}",
            )
            request = load_json(request_path)
            _assert_schema(
                request,
                PRECANONICAL_SCHEMAS["request"],
                f"request for {task['taskId']}",
            )
            if request["stage"] != "state_definition":
                raise ArtSystemError(f"Campaign request stage drift: {request_path}")
            if request["assetKey"] != task["assetId"]:
                raise ArtSystemError(f"Campaign request asset drift: {request_path}")
            if request["requestedStateIds"] != [task["stateId"]]:
                raise ArtSystemError(f"Campaign request state drift: {request_path}")
            if request["budget"]["maximumWebGenerations"] != 1:
                raise ArtSystemError(f"Campaign request must allow one generation: {request_path}")
            for field in ("result", "review", "continuitySource", "revisionSource"):
                if attempt[field] is not None:
                    _verify_binding(
                        attempt[field],
                        base=campaign_root,
                        label=f"{field} for {task['taskId']} attempt {index}",
                    )
        if task["status"] == "ACCEPTED":
            if task["acceptedResult"] is None or task["acceptedReview"] is None:
                raise ArtSystemError(f"Accepted task lacks evidence: {task['taskId']}")
            _verify_binding(
                task["acceptedResult"],
                base=campaign_root,
                label=f"accepted result for {task['taskId']}",
            )
            review_path = _verify_binding(
                task["acceptedReview"],
                base=campaign_root,
                label=f"accepted review for {task['taskId']}",
            )
            review = load_json(review_path)
            if review["decision"] not in ACCEPTED_DECISIONS:
                raise ArtSystemError(f"Accepted task has non-accepting review: {task['taskId']}")
        if task["status"] in {"READY", "VISUAL_REVIEW_REQUIRED"}:
            if not task["attempts"]:
                raise ArtSystemError(
                    f"Actionable task lacks an active attempt: {task['taskId']}"
                )
            _accepted_predecessor(
                campaign,
                task,
                campaign_root=campaign_root,
            )

    expected_progress = dict(campaign["progress"])
    recalculated = load_json(campaign_path)
    _recompute_progress(recalculated)
    if recalculated["progress"] != expected_progress:
        raise ArtSystemError("Campaign progress drift")
    if campaign["status"] == "ACTIVE":
        if campaign["currentTaskId"] is None:
            raise ArtSystemError("Active campaign lacks currentTaskId")
        current = _task(campaign, campaign["currentTaskId"])
        if current["status"] not in {"READY", "VISUAL_REVIEW_REQUIRED"}:
            raise ArtSystemError("Current task is not actionable")
    elif campaign["status"] == "COMPLETE":
        if campaign["currentTaskId"] is not None:
            raise ArtSystemError("Complete campaign must not expose a current task")
        if campaign["progress"]["completedTasks"] != 16:
            raise ArtSystemError("Complete campaign lacks all sixteen accepted tasks")
    return campaign


def record_import(
    campaign_path: Path,
    result_path: Path,
) -> dict[str, Any]:
    campaign_path = campaign_path.resolve()
    campaign_root = campaign_path.parent
    campaign = verify_campaign(campaign_path)
    if campaign["status"] != "ACTIVE" or campaign["currentTaskId"] is None:
        raise ArtSystemError("Campaign has no active task for import")
    task = _task(campaign, campaign["currentTaskId"])
    if task["status"] != "READY":
        raise ArtSystemError("Current campaign task is not ready for import")
    attempt = task["attempts"][-1]
    result_path = result_path.resolve()
    result = load_json(result_path)
    _assert_schema(result, PRECANONICAL_SCHEMAS["result"], "campaign result")
    request_path = _verify_binding(
        attempt["request"],
        base=campaign_root,
        label="active campaign request",
    )
    if result["requestId"] != load_json(request_path)["requestId"]:
        raise ArtSystemError("Imported result does not belong to the active campaign request")
    if result["provenance"]["modelName"] != REQUIRED_MODEL:
        raise ArtSystemError(f"Campaign result must record model {REQUIRED_MODEL}")
    if result["provenance"]["modelNameEvidence"] != "UI_CONFIRMED":
        raise ArtSystemError("Campaign result requires visible UI model confirmation")
    attempt["result"] = _binding(result_path, base=campaign_root)
    task["status"] = "VISUAL_REVIEW_REQUIRED"
    _save_campaign(campaign_path, campaign)
    return verify_campaign(campaign_path)


def record_review_and_advance(
    campaign_path: Path,
    review_path: Path,
) -> dict[str, Any]:
    campaign_path = campaign_path.resolve()
    campaign_root = campaign_path.parent
    campaign = verify_campaign(campaign_path)
    if campaign["status"] != "ACTIVE" or campaign["currentTaskId"] is None:
        raise ArtSystemError("Campaign has no active task for review")
    task = _task(campaign, campaign["currentTaskId"])
    if task["status"] != "VISUAL_REVIEW_REQUIRED":
        raise ArtSystemError("Current campaign task is not awaiting review")
    attempt = task["attempts"][-1]
    if attempt["result"] is None:
        raise ArtSystemError("Current campaign attempt lacks its imported result")
    result_path = _verify_binding(
        attempt["result"],
        base=campaign_root,
        label="active campaign result",
    )
    review_path = review_path.resolve()
    review = load_json(review_path)
    _assert_schema(review, PRECANONICAL_SCHEMAS["review"], "campaign review")
    if Path(review["result"]["path"]).resolve() != result_path:
        raise ArtSystemError("Review is not bound to the active campaign result")
    attempt["review"] = _binding(review_path, base=campaign_root)
    attempt["decision"] = review["decision"]

    if review["decision"] in ACCEPTED_DECISIONS:
        task["status"] = "ACCEPTED"
        task["acceptedResult"] = attempt["result"]
        task["acceptedReview"] = attempt["review"]
        next_state = next(
            (
                candidate
                for candidate in campaign["tasks"]
                if candidate["assetId"] == task["assetId"]
                and candidate["stateOrdinal"] == task["stateOrdinal"] + 1
            ),
            None,
        )
        if next_state is not None and next_state["status"] == "PENDING":
            _ensure_task_request(
                campaign_path,
                campaign,
                next_state,
            )
        actionable = sorted(_actionable_tasks(campaign), key=lambda item: item["ordinal"])
        if (
            next_state is not None
            and next_state["status"] in {"READY", "VISUAL_REVIEW_REQUIRED"}
        ):
            campaign["currentTaskId"] = next_state["taskId"]
        elif actionable:
            campaign["currentTaskId"] = actionable[0]["taskId"]
        elif all(item["status"] == "ACCEPTED" for item in campaign["tasks"]):
            campaign["status"] = "COMPLETE"
            campaign["currentTaskId"] = None
        else:
            campaign["status"] = "BLOCKED"
            campaign["currentTaskId"] = None
    else:
        if len(task["attempts"]) >= campaign["maxAttemptsPerTask"]:
            task["status"] = "BLOCKED"
            actionable = sorted(
                _actionable_tasks(campaign),
                key=lambda item: item["ordinal"],
            )
            if actionable:
                campaign["currentTaskId"] = actionable[0]["taskId"]
            else:
                campaign["status"] = "BLOCKED"
                campaign["currentTaskId"] = None
        else:
            instructions = []
            if review["decision"] == "REJECTED":
                instructions.append(
                    "The previous attempt was rejected. Rebuild this same target state "
                    "without carrying rejected visual inventions."
                )
            instructions.extend(f"PRESERVE: {item}" for item in review["preserve"])
            instructions.extend(f"CORRECT: {item}" for item in review["correct"])
            instructions.extend(
                f"FORBID NEXT: {item}" for item in review["forbidNext"]
            )
            if not instructions:
                instructions.append(
                    "Rebuild this target state with stricter canon conformity and "
                    "clearer one-second mobile readability."
                )
            if review["decision"] == "REVISION_REQUIRED":
                parent = result_path
                reference_kind = "revision"
            else:
                parent = _accepted_predecessor(
                    campaign,
                    task,
                    campaign_root=campaign_root,
                )
                reference_kind = "continuity" if parent is not None else None
            task["status"] = "READY"
            task["attempts"].append(
                _create_request(
                    campaign_path,
                    task,
                    parent_result=parent,
                    reference_kind=reference_kind,
                    revision_instructions=instructions,
                )
            )
    _save_campaign(campaign_path, campaign)
    return verify_campaign(campaign_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build and verify the Salvaged Frontier object-by-state image campaign."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--output", type=Path, required=True)
    init_parser.add_argument(
        "--campaign-id",
        default=DEFAULT_CAMPAIGN_ID,
    )
    init_parser.add_argument("--max-attempts-per-task", type=int, default=3)

    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("campaign", type=Path)

    snapshot_parser = subparsers.add_parser("snapshot")
    snapshot_parser.add_argument("campaign", type=Path)

    fork_parser = subparsers.add_parser("fork")
    fork_parser.add_argument("--source-campaign", type=Path, required=True)
    fork_parser.add_argument("--output", type=Path, required=True)
    fork_parser.add_argument("--campaign-id", required=True)
    fork_parser.add_argument("--restart-task-id", required=True)
    fork_parser.add_argument("--reason", required=True)

    args = parser.parse_args()
    try:
        if args.command == "init":
            campaign_path = init_campaign(
                args.output,
                args.campaign_id,
                args.max_attempts_per_task,
            )
            campaign = verify_campaign(campaign_path)
            print(
                "[PASS] Precanonical campaign ready: "
                f"{campaign_path} ({campaign['progress']['totalTasks']} object-state tasks)"
            )
        elif args.command == "verify":
            campaign = verify_campaign(args.campaign)
            print(
                "[PASS] Precanonical campaign verified: "
                f"{campaign['progress']['completedTasks']}/"
                f"{campaign['progress']['totalTasks']} accepted"
            )
        elif args.command == "snapshot":
            campaign = snapshot_campaign_canons(args.campaign)
            print(
                "[PASS] Campaign canons snapshotted in place: "
                f"{args.campaign.resolve()} ({len(campaign['tasks'])} task bindings)"
            )
        else:
            campaign_path = fork_campaign(
                args.source_campaign,
                args.output,
                args.campaign_id,
                args.restart_task_id,
                args.reason,
            )
            campaign = verify_campaign(campaign_path)
            print(
                "[PASS] Revised precanonical campaign ready: "
                f"{campaign_path} ({campaign['progress']['completedTasks']}/"
                f"{campaign['progress']['totalTasks']} accepted; "
                f"restart={campaign['currentTaskId']})"
            )
        return 0
    except ArtSystemError as exc:
        print(f"[FAIL] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
