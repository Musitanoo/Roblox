from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from PIL import Image

from tools.art.common import (
    ArtSystemError,
    ROOT,
    canonical_json_bytes,
    load_json,
    sanitized_subprocess_environment,
    sha256_bytes,
    sha256_file,
    validate_with_schema,
    write_json,
)

POLICY_PATH = ROOT / "art/precanonical/policy.json"
CONSTITUTION_PATH = ROOT / "art/selected/salvaged-frontier-constitution.json"
SCHEMAS = {
    "policy": ROOT / "schemas/precanonical-policy.schema.json",
    "brief": ROOT / "schemas/precanonical-brief.schema.json",
    "request": ROOT / "schemas/precanonical-request.schema.json",
    "preflight": ROOT / "schemas/precanonical-preflight.schema.json",
    "browser_doctor": ROOT / "schemas/precanonical-browser-doctor.schema.json",
    "handoff": ROOT / "schemas/precanonical-handoff.schema.json",
    "result": ROOT / "schemas/precanonical-result.schema.json",
    "review": ROOT / "schemas/precanonical-review.schema.json",
}
ASSESSMENT_KEYS = (
    "functionalConformity",
    "artDirectionConformity",
    "visualHierarchy",
    "internalCoherence",
    "stateCoherence",
)
STAGE_VIEWS = {
    "exploration": ["exploration_sheet"],
    "consolidation": [
        "hero_three_quarter_front",
        "three_quarter_rear",
        "black_silhouette",
    ],
    "precanonical_board": [
        "hero_three_quarter_front",
        "three_quarter_rear",
        "front",
        "rear",
        "left",
        "right",
        "top",
        "bottom",
        "black_silhouette",
        "component_breakdown",
        "functional_zones",
        "state_lineup",
        "mobile_landscape",
        "mobile_portrait",
    ],
    "state_definition": [
        "hero_three_quarter_front",
        "three_quarter_rear",
        "black_silhouette",
        "mobile_landscape",
    ],
    "correction": [
        "hero_three_quarter_front",
        "three_quarter_rear",
        "black_silhouette",
    ],
}
BROWSER_ADAPTERS = ("codex_chrome", "codex_iab")
REQUIRED_BROWSER_TOOL = "mcp__node_repl__js"
ADAPTER_BACKENDS = {
    "codex_chrome": "chrome",
    "codex_iab": "iab",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _assert_schema(value: Any, name: str) -> None:
    errors = validate_with_schema(value, SCHEMAS[name])
    if errors:
        raise ArtSystemError(f"{name} schema validation failed: {'; '.join(errors)}")


def _binding(path: Path, *, base: Path) -> dict[str, str]:
    resolved = path.resolve()
    try:
        portable_path = resolved.relative_to(base.resolve()).as_posix()
    except ValueError:
        portable_path = str(resolved)
    return {
        "path": portable_path,
        "sha256": sha256_file(path),
    }


def _resolve_binding(
    request_path: Path,
    binding: dict[str, str],
) -> Path:
    raw = Path(binding["path"])
    if raw.is_absolute():
        return raw.resolve()
    if raw.parts and raw.parts[0] in {"art", "schemas", "docs", "tools"}:
        return (ROOT / raw).resolve()
    return (request_path.parent / raw).resolve()


def _verify_binding(
    request_path: Path,
    binding: dict[str, str],
    label: str,
) -> tuple[Path | None, str | None]:
    path = _resolve_binding(request_path, binding)
    if not path.is_file():
        return None, f"{label} is missing: {binding['path']}"
    observed = sha256_file(path)
    if observed != binding["sha256"]:
        return None, f"{label} hash drift: {binding['path']}"
    return path, None


def _list_text(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _compile_prompt(
    brief: dict[str, Any],
    constitution: dict[str, Any],
    stage: str,
    revision_instructions: list[str],
) -> str:
    dimensions = brief["dimensionsStuds"]
    components = "\n".join(
        f"- {item['id']}: {item['function']} ({item['mobility']})"
        for item in brief["components"]
    )
    states = "\n".join(
        f"- {item['id']}: {item['visualChange']} | invariants: "
        + ", ".join(item["invariants"])
        for item in brief["states"]
    )
    interaction = "\n".join(
        f"- {item['id']} at {item['location']}: {item['purpose']}; "
        f"cue: {item['requiredCue']}"
        for item in brief["interactionZones"]
    )
    stage_contract = {
        "exploration": (
            "Produce one clean 2x2 exploration sheet containing four genuinely "
            "different silhouette solutions. Each candidate must change at least "
            "two primary-mass or negative-space decisions while preserving the "
            "same required components, dimensions, front direction and gameplay "
            "function. A brace-angle, fastener, wear or trim swap alone is not a "
            "different silhouette. Keep the same scale, neutral camera and "
            "simplified materials. Do not label the candidates with generated text."
        ),
        "consolidation": (
            "Produce one consolidated object with a hero three-quarter front view, "
            "a three-quarter rear view and a black silhouette. These must depict "
            "the same construction and the same components."
        ),
        "precanonical_board": (
            "Produce a coherent precanonical design board for one single object. "
            "Cover the requested views, component logic, functional zones and state "
            "lineup while preserving the exact same object identity across panels."
        ),
        "state_definition": (
            "Produce exactly one state-specific verification board for one single "
            "object and one single gameplay state. Every panel must depict the "
            "same construction in the same state: hero three-quarter front, "
            "three-quarter rear, black silhouette and elevated Roblox gameplay "
            "camera. Do not show or invent any other state."
        ),
        "correction": (
            "Edit the attached previous result. Preserve every element not listed "
            "for correction. Do not redesign the object or introduce new components."
        ),
    }[stage]
    revision = (
        "\nTARGETED CORRECTIONS\n" + _list_text(revision_instructions)
        if revision_instructions
        else ""
    )
    grammar = constitution["quantitativeGrammar"]
    return f"""PRECANONICAL VISUALIZATION — NOT A 3D OR CANONICAL AUTHORITY

Reconstruct the following gameplay object as a visual design proposal. Do not
invent missing functions, hidden mechanisms, logos, text or additional parts.

ART-DIRECTION PRECEDENCE
- Salvaged Frontier is the sole identity authority.
- Industrial Toy Defense contributes readability discipline only.
- Never create a fifty-fifty hybrid or a literal construction toy.
- Thesis: {constitution['thesis']}
- Standardized chassis share: {grammar['standardizedChassisShare']['min']:.0%}–{grammar['standardizedChassisShare']['max']:.0%}.
- Authored adaptation share: {grammar['authoredAdaptationShare']['min']:.0%}–{grammar['authoredAdaptationShare']['max']:.0%}.
- Detail hierarchy: {grammar['detailHierarchy']['primary']:.0%} primary, {grammar['detailHierarchy']['secondary']:.0%} secondary, {grammar['detailHierarchy']['tertiary']:.0%} tertiary.
- Global asymmetry target: {grammar['globalAsymmetry']['target']:.2f}, maximum {grammar['globalAsymmetry']['max']:.2f}.

OBJECT IDENTITY
- Name: {brief['displayName']}
- Gameplay function: {brief['gameplayFunction']}
- One-second read: {brief['oneSecondRead']}
- World role: {brief['worldRole']}
- Emotional intent: {brief['emotionalIntent']}
- Dimensions: {dimensions['width']} × {dimensions['height']} × {dimensions['depth']} Roblox studs.
- Front: {brief['orientation']['front']}
- Player side: {brief['orientation']['playerSide']}
- Threat side: {brief['orientation']['threatSide']}
- Collision promise: {brief['collisionPromise']}
- Expected simultaneous instances: {brief['expectedSimultaneousInstances']}

REQUIRED COMPONENTS
{components}

INTERACTION ZONES
{interaction}

STATES — ALL DERIVE FROM THE SAME OBJECT
{states}

OBLIGATIONS
{_list_text(brief['obligations'])}

CONSTRAINTS
{_list_text(brief['constraints'])}

BOUNDED FREEDOMS
{_list_text(brief['freedoms'])}

STAGE INSTRUCTION
{stage_contract}{revision}

OUTPUT DISCIPLINE
- Stylized, chunky, purposefully repaired and readable on mobile.
- Broad calm planes, explicit load paths, thick joints and protected apertures.
- Deep slate chassis, bone-sand reclaimed composite and bounded sun-copper repair history.
- Mint is local interaction information only; never broad decoration.
- Neutral studio lighting and a neutral background.
- No cinematic depth of field, environmental scene or unrelated props.
- The proposal is visual evidence only and must not imply validated hidden geometry.
"""


def _compile_negative_constraints(brief: dict[str, Any]) -> list[str]:
    fixed = [
        "No text, captions, labels, logos or invented alphabet inside the image.",
        "No floating, intersecting or mechanically unsupported components.",
        "No random scrap cloud, cable spaghetti, micro-greebles or uniform distress.",
        "No photorealism, military realism, bleak monochrome or literal construction-toy identity.",
        "No color-only gameplay state; use shape, posture, value and component changes.",
        "No thin wires, paper-thin essential parts or tiny silhouette-critical details.",
        "No redesign between views or states.",
        "No invented rear, underside or hidden mechanism presented as resolved fact.",
        "No additional component added merely to fill empty space.",
        "No geometric emblem, badge, pseudo-logo, triangular mark or unexplained assembly symbol.",
        "No stone, concrete, parchment or ceramic reading for reclaimed composite panels.",
        "No friendly interaction light on the threat-facing armor or front presentation face.",
        "No decorative brace that fails to connect two plausible load-bearing structural joints.",
    ]
    return list(dict.fromkeys(fixed + brief["prohibitions"]))


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def init_packet(
    brief_path: Path,
    request_id: str,
    output: Path,
    stage: str,
    maximum_generations: int,
    human_confirmation_required: bool,
    automatic_submission_authorized: bool,
    parent_result: Path | None = None,
    revision_instructions: list[str] | None = None,
    browser_adapter: str = "codex_chrome",
) -> Path:
    brief_path = brief_path.resolve()
    output = output.resolve()
    if output.exists() and any(output.iterdir()):
        raise ArtSystemError(f"Refusing to overwrite non-empty request directory: {output}")
    brief = load_json(brief_path)
    policy = load_json(POLICY_PATH)
    constitution = load_json(CONSTITUTION_PATH)
    _assert_schema(brief, "brief")
    _assert_schema(policy, "policy")
    if brief["artDirection"] != policy["selectedArtDirection"]:
        raise ArtSystemError("Brief art direction differs from selected precanonical policy")
    if policy["constitution"]["sha256"] != sha256_file(CONSTITUTION_PATH):
        raise ArtSystemError("Precanonical policy constitution hash is stale")
    if browser_adapter not in policy["providerContract"]["allowedBrowserAdapters"]:
        raise ArtSystemError(
            f"Browser adapter is not allowed by policy: {browser_adapter}"
        )
    revisions = revision_instructions or []
    if stage == "correction" and parent_result is None:
        raise ArtSystemError("Correction stage requires --parent-result")
    if stage != "correction" and parent_result is not None:
        raise ArtSystemError("--parent-result is only valid for correction stage")
    if stage == "correction" and not revisions:
        raise ArtSystemError("Correction stage requires at least one --revision-instruction")
    if stage != "correction" and revisions:
        raise ArtSystemError("--revision-instruction is only valid for correction stage")
    if maximum_generations < 1 or maximum_generations > policy["defaultBudget"]["maximumTotal"]:
        raise ArtSystemError(
            f"Maximum generations must be between 1 and {policy['defaultBudget']['maximumTotal']}"
        )

    output.mkdir(parents=True, exist_ok=True)
    source_brief_path = output / "source-brief.json"
    source_brief_path.write_bytes(brief_path.read_bytes())
    prompt_path = output / "prompt.txt"
    negative_path = output / "negative-constraints.txt"
    views_path = output / "requested-views.json"
    states_path = output / "requested-states.json"
    brief_md_path = output / "brief.md"
    prompt = _compile_prompt(brief, constitution, stage, revisions)
    negatives = _compile_negative_constraints(brief)
    views = {
        "schemaVersion": "1.0.0",
        "stage": stage,
        "views": STAGE_VIEWS[stage],
        "sameObjectAcrossViews": True,
    }
    states = {
        "schemaVersion": "1.0.0",
        "states": [
            {
                "id": item["id"],
                "visualChange": item["visualChange"],
                "invariants": item["invariants"],
            }
            for item in brief["states"]
        ],
        "independentStateDesignForbidden": True,
    }
    _write_text(prompt_path, prompt)
    _write_text(negative_path, "\n".join(f"- {item}" for item in negatives))
    write_json(views_path, views)
    write_json(states_path, states)
    _write_text(
        brief_md_path,
        f"""# {brief['displayName']} — Precanonical brief

Status: `PRECANONICAL_SPEC_COMPLETE`

This packet is a visual exploration contract. It is not a visual canon, a
geometry contract or production approval.

## Function

{brief['gameplayFunction']}

## One-second read

{brief['oneSecondRead']}

## Art direction

Salvaged Frontier owns identity. Industrial Toy Defense contributes only the
readability discipline defined by the selected constitution.

## Stage

`{stage}`

## Authority boundary

- Images may be selected for canonicalization.
- Images do not define hidden geometry.
- Human selection remains mandatory.
- `productionApproved=false`.
""",
    )

    parent_binding: dict[str, str] | None = None
    if parent_result is not None:
        parent_result = parent_result.resolve()
        parent = load_json(parent_result)
        _assert_schema(parent, "result")
        parent_binding = _binding(parent_result, base=output)

    request = {
        "$schema": "https://roblox-top1.local/schemas/precanonical-request.schema.json",
        "schemaVersion": "1.0.0",
        "requestId": request_id,
        "assetKey": brief["assetKey"],
        "artDirection": brief["artDirection"],
        "generationSurface": "chatgpt_web_images",
        "status": "PRECANONICAL_SPEC_COMPLETE",
        "stage": stage,
        "policy": {
            "path": "art/precanonical/policy.json",
            "sha256": sha256_file(POLICY_PATH),
        },
        "constitution": {
            "path": "art/selected/salvaged-frontier-constitution.json",
            "sha256": sha256_file(CONSTITUTION_PATH),
        },
        "compiler": {
            "path": "tools/art/precanonical.py",
            "sha256": sha256_file(Path(__file__).resolve()),
        },
        "sourceBrief": _binding(source_brief_path, base=output),
        "parentResult": parent_binding,
        "revisionInstructions": revisions,
        "files": {
            "brief": _binding(brief_md_path, base=output),
            "prompt": _binding(prompt_path, base=output),
            "negativeConstraints": _binding(negative_path, base=output),
            "requestedViews": _binding(views_path, base=output),
            "requestedStates": _binding(states_path, base=output),
        },
        "promptHash": sha256_file(prompt_path),
        "requestedViewIds": views["views"],
        "requestedStateIds": [item["id"] for item in brief["states"]],
        "imageSpec": {
            "aspectRatio": "1:1" if stage == "exploration" else "4:3",
            "background": "neutral_mid_gray",
            "lighting": "neutral_studio",
            "singleObjectOnly": True,
        },
        "budget": {
            "maximumWebGenerations": maximum_generations,
            "consumedWebGenerations": 0,
            "reserveForCorrections": 1 if maximum_generations > 1 else 0,
            "humanConfirmationRequired": human_confirmation_required,
        },
        "automation": {
            "browserAdapter": browser_adapter,
            "automaticSubmissionAuthorized": automatic_submission_authorized,
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
    _assert_schema(request, "request")
    request_path = output / "request.json"
    write_json(request_path, request)
    return request_path


def _result_manifests(request_path: Path) -> list[Path]:
    packet = request_path.parent
    if packet.parent.name != "requests":
        return []
    results_root = packet.parent.parent / "results"
    if not results_root.is_dir():
        return []
    return sorted(results_root.glob("*/result.json"))


def preflight(request_path: Path, output: Path | None = None) -> dict[str, Any]:
    request_path = request_path.resolve()
    checks: list[dict[str, str]] = []
    blocking: list[str] = []
    schema_errors: list[str] = []

    def record(check_id: str, passed: bool, detail: str, blocked: bool = False) -> None:
        status = "PASS" if passed else ("BLOCKED" if blocked else "FAIL")
        checks.append({"id": check_id, "status": status, "detail": detail})
        if not passed:
            blocking.append(detail)

    try:
        request = load_json(request_path)
        schema_errors = validate_with_schema(request, SCHEMAS["request"])
        record(
            "request_schema",
            not schema_errors,
            "Request schema is valid."
            if not schema_errors
            else "; ".join(schema_errors),
        )
    except ArtSystemError as exc:
        request = {}
        record("request_schema", False, str(exc))

    if request and not schema_errors:
        required_attachment_count = 0
        for label, binding in (
            ("policy", request["policy"]),
            ("constitution", request["constitution"]),
            ("compiler", request["compiler"]),
            ("source_brief", request["sourceBrief"]),
            *(
                (
                    {
                        "brief": "file_brief",
                        "prompt": "file_prompt",
                        "negativeConstraints": "file_negative_constraints",
                        "requestedViews": "file_requested_views",
                        "requestedStates": "file_requested_states",
                    }[name],
                    binding,
                )
                for name, binding in request["files"].items()
            ),
        ):
            _, issue = _verify_binding(request_path, binding, label)
            record(label, issue is None, f"{label} binding is current." if issue is None else issue)
        if request["parentResult"] is not None:
            parent_path, issue = _verify_binding(
                request_path,
                request["parentResult"],
                "parent_result",
            )
            record(
                "parent_result",
                issue is None,
                "Parent result binding is current." if issue is None else issue,
            )
            parent_integrity_issues: list[str] = []
            if parent_path is not None:
                try:
                    parent_result = load_json(parent_path)
                    required_attachment_count = len(parent_result.get("images", []))
                    parent_integrity_issues.extend(
                        validate_with_schema(parent_result, SCHEMAS["result"])
                    )
                    for image in parent_result.get("images", []):
                        image_path = parent_path.parent / image["path"]
                        if not image_path.is_file():
                            parent_integrity_issues.append(
                                f"missing parent image: {image['path']}"
                            )
                        elif sha256_file(image_path) != image["sha256"]:
                            parent_integrity_issues.append(
                                f"parent image hash drift: {image['path']}"
                            )
                except ArtSystemError as exc:
                    parent_integrity_issues.append(str(exc))
            record(
                "parent_result_integrity",
                not parent_integrity_issues,
                "Parent result schema and image hashes are current."
                if not parent_integrity_issues
                else "; ".join(parent_integrity_issues),
            )

        policy = load_json(POLICY_PATH)
        record(
            "selected_art_direction",
            request["artDirection"] == policy["selectedArtDirection"] == "salvaged-frontier",
            "Request uses selected Salvaged Frontier identity."
            if request["artDirection"] == policy["selectedArtDirection"] == "salvaged-frontier"
            else "Request art direction differs from the selected policy.",
        )
        record(
            "generation_surface",
            request["generationSurface"] == policy["providerContract"]["allowedSurface"],
            "Generation surface is the allowed replaceable Web adapter."
            if request["generationSurface"] == policy["providerContract"]["allowedSurface"]
            else "Generation surface is not allowed by policy.",
        )
        adapter = request["automation"]["browserAdapter"]
        allowed_adapters = policy["providerContract"]["allowedBrowserAdapters"]
        adapter_allowed = adapter in allowed_adapters
        record(
            "browser_adapter_allowed",
            adapter_allowed,
            f"Browser adapter {adapter} is explicitly allowed by policy."
            if adapter_allowed
            else f"Browser adapter {adapter} is not allowed by policy.",
        )
        attachment_adapter = policy["providerContract"][
            "attachmentCapableBrowserAdapter"
        ]
        fallback_adapter = policy["providerContract"][
            "attachmentlessFallbackBrowserAdapter"
        ]
        adapter_attachment_compatible = (
            required_attachment_count == 0 or adapter == attachment_adapter
        )
        if adapter == fallback_adapter and required_attachment_count == 0:
            adapter_detail = (
                f"{fallback_adapter} is allowed because this request has no "
                "file attachments."
            )
        elif adapter_attachment_compatible:
            adapter_detail = (
                f"{adapter} is compatible with {required_attachment_count} "
                "required attachment(s)."
            )
        else:
            adapter_detail = (
                f"{adapter} cannot execute this request because "
                f"{required_attachment_count} hash-bound attachment(s) require "
                f"{attachment_adapter}."
            )
        record(
            "browser_adapter_attachment_compatibility",
            adapter_attachment_compatible,
            adapter_detail,
        )
        fallbacks_safe = (
            request["automation"]["automaticCodexImageFallback"] is False
            and request["automation"]["automaticApiFallback"] is False
            and request["automation"]["automaticRetry"] is False
            and policy["fallbackPolicy"]["browserAdapterAutomatic"] is False
        )
        record(
            "fallback_policy",
            fallbacks_safe,
            "Automatic imagegen/API/browser-adapter fallback and silent retry are disabled."
            if fallbacks_safe
            else "An automatic fallback, browser-adapter switch or retry is enabled.",
        )
        prompt_binding = request["files"]["prompt"]
        record(
            "prompt_hash",
            request["promptHash"] == prompt_binding["sha256"],
            "Prompt hash matches the bound prompt file."
            if request["promptHash"] == prompt_binding["sha256"]
            else "promptHash differs from the prompt binding.",
        )
        stage_views_valid = request["requestedViewIds"] == STAGE_VIEWS[request["stage"]]
        record(
            "stage_view_scope",
            stage_views_valid,
            "Requested views match the bounded stage."
            if stage_views_valid
            else "Requested views exceed or differ from the bounded stage.",
        )
        manifests = []
        for path in _result_manifests(request_path):
            try:
                value = load_json(path)
                if not validate_with_schema(value, SCHEMAS["result"]):
                    manifests.append((path, value))
            except ArtSystemError:
                continue
        matching = [
            (path, value)
            for path, value in manifests
            if value["requestId"] == request["requestId"]
        ]
        consumed = max(
            request["budget"]["consumedWebGenerations"],
            len(matching),
        )
        remaining = max(0, request["budget"]["maximumWebGenerations"] - consumed)
        record(
            "generation_budget",
            remaining > 0,
            f"{remaining} bounded Web generation(s) remain."
            if remaining > 0
            else "Web generation budget is exhausted.",
            blocked=True,
        )
        duplicates = [
            path
            for path, value in manifests
            if value["promptHash"] == request["promptHash"]
        ]
        record(
            "duplicate_prompt",
            not duplicates,
            "No imported result already uses this exact prompt hash."
            if not duplicates
            else "An imported result already uses this exact prompt hash; create a targeted revision request.",
            blocked=True,
        )
        authority_safe = (
            request["authority"]["canonical"] is False
            and request["authority"]["geometryAuthority"] is False
            and request["authority"]["productionApproved"] is False
        )
        record(
            "authority_boundary",
            authority_safe,
            "Request remains non-canonical and non-production."
            if authority_safe
            else "Request illegally claims canonical, geometry or production authority.",
        )
    else:
        remaining = 0

    failed = any(item["status"] == "FAIL" for item in checks)
    blocked = any(item["status"] == "BLOCKED" for item in checks)
    status = "FAIL" if failed else ("BLOCKED" if blocked else "PASS")
    next_state = "RESULT_AMBIGUOUS"
    if not failed and remaining == 0:
        next_state = "BUDGET_EXHAUSTED"
    elif not failed and not blocked:
        next_state = "WEB_PREFLIGHT_PASS"
    report = {
        "$schema": "https://roblox-top1.local/schemas/precanonical-preflight.schema.json",
        "schemaVersion": "1.0.0",
        "generatedAt": _utc_now(),
        "request": {
            "path": str(request_path),
            "sha256": sha256_file(request_path) if request_path.is_file() else "0" * 64,
        },
        "requestId": request.get("requestId", "invalid-request"),
        "promptHash": request.get("promptHash", "0" * 64),
        "status": status,
        "nextState": next_state,
        "remainingGenerations": remaining,
        "checks": checks,
        "blockingReasons": list(dict.fromkeys(blocking)),
        "quotaRemaining": "UNKNOWN",
        "consumesQuota": False,
        "productionApproved": False,
    }
    _assert_schema(report, "preflight")
    if output:
        write_json(output.resolve(), report)
    return report


def _version_key(path: Path) -> tuple[int, ...]:
    try:
        return tuple(int(part) for part in path.name.split("."))
    except ValueError:
        return (0,)


def _latest_plugin_dir(codex_home: Path, plugin_name: str) -> Path | None:
    plugin_root = (
        codex_home
        / "plugins"
        / "cache"
        / "openai-bundled"
        / plugin_name
    )
    if not plugin_root.is_dir():
        return None
    versions = [path for path in plugin_root.iterdir() if path.is_dir()]
    return max(versions, key=_version_key) if versions else None


def _probe_node_repl_tools(
    executable: Path,
    configured_environment: dict[str, Any],
) -> tuple[bool, list[str], str]:
    environment = sanitized_subprocess_environment(configured_environment)
    messages = (
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {
                    "name": "roblox-precanonical-browser-doctor",
                    "version": "1.0.0",
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {},
        },
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        },
    )
    input_value = "".join(
        json.dumps(message, separators=(",", ":")) + "\n"
        for message in messages
    )
    try:
        completed = subprocess.run(
            [str(executable), "--disable-sandbox"],
            input=input_value,
            text=True,
            capture_output=True,
            env=environment,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, [], f"node_repl MCP probe failed: {exc}"
    tool_names: list[str] = []
    for line in completed.stdout.splitlines():
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if message.get("id") != 2:
            continue
        tools = message.get("result", {}).get("tools", [])
        tool_names = sorted(
            str(tool.get("name"))
            for tool in tools
            if isinstance(tool, dict) and tool.get("name")
        )
    passed = completed.returncode == 0 and "js" in tool_names
    if passed:
        return True, tool_names, "node_repl exposes the required js MCP tool."
    stderr = completed.stderr.strip()
    detail = "node_repl did not expose the required js MCP tool."
    if stderr:
        detail += f" Process error: {stderr[:500]}"
    return False, tool_names, detail


def _chrome_native_host_check() -> tuple[str, str]:
    if os.name != "nt":
        return (
            "UNKNOWN",
            "Chrome native-host registration is only diagnosed automatically on Windows.",
        )
    try:
        import winreg

        key_path = (
            r"Software\Google\Chrome\NativeMessagingHosts"
            r"\com.openai.codexextension"
        )
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
            manifest_value, _ = winreg.QueryValueEx(key, None)
        manifest_path = Path(str(manifest_value))
        if not manifest_path.is_file():
            return (
                "FAIL",
                "Chrome native-host registry entry exists but its manifest is missing.",
            )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        host_path = Path(str(manifest.get("path", "")))
        if not host_path.is_file():
            return (
                "FAIL",
                "Chrome native-host manifest exists but its executable is missing.",
            )
        return (
            "PASS",
            "Chrome native-host registry entry, manifest and executable are present.",
        )
    except FileNotFoundError:
        return (
            "FAIL",
            "Chrome native-host registry entry is missing; repair it through the official Chrome plugin setup.",
        )
    except (OSError, json.JSONDecodeError, TypeError) as exc:
        return "FAIL", f"Chrome native-host validation failed: {exc}"


def browser_doctor(
    browser_adapter: str,
    output: Path | None = None,
    codex_home: Path | None = None,
) -> dict[str, Any]:
    if browser_adapter not in BROWSER_ADAPTERS:
        raise ArtSystemError(f"Unsupported browser adapter: {browser_adapter}")
    home = (
        codex_home.resolve()
        if codex_home is not None
        else Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).resolve()
    )
    checks: list[dict[str, str]] = []
    local_failures: list[str] = []

    def record(
        check_id: str,
        status: str,
        detail: str,
        *,
        required_locally: bool = True,
    ) -> None:
        checks.append({"id": check_id, "status": status, "detail": detail})
        if required_locally and status != "PASS":
            local_failures.append(detail)

    config_path = home / "config.toml"
    config: dict[str, Any] = {}
    if config_path.is_file():
        try:
            config = tomllib.loads(config_path.read_text(encoding="utf-8"))
            record("codex_config", "PASS", "Codex configuration is readable.")
        except (OSError, tomllib.TOMLDecodeError) as exc:
            record("codex_config", "FAIL", f"Codex configuration is invalid: {exc}")
    else:
        record("codex_config", "FAIL", "Codex configuration is missing.")

    plugin_name = "browser" if browser_adapter == "codex_iab" else "chrome"
    plugin_dir = _latest_plugin_dir(home, plugin_name)
    record(
        "selected_plugin",
        "PASS" if plugin_dir else "FAIL",
        (
            f"Installed {plugin_name} plugin version {plugin_dir.name} was found."
            if plugin_dir
            else f"Installed {plugin_name} plugin was not found."
        ),
    )

    plugins = config.get("plugins", {}) if isinstance(config, dict) else {}
    plugin_key = f"{plugin_name}@openai-bundled"
    plugin_enabled = bool(
        isinstance(plugins, dict)
        and isinstance(plugins.get(plugin_key), dict)
        and plugins[plugin_key].get("enabled") is True
    )
    record(
        "selected_plugin_enabled",
        "PASS" if plugin_enabled else "FAIL",
        (
            f"{plugin_key} is enabled in Codex."
            if plugin_enabled
            else f"{plugin_key} is not enabled in Codex."
        ),
    )

    servers = config.get("mcp_servers", {}) if isinstance(config, dict) else {}
    node_repl = servers.get("node_repl", {}) if isinstance(servers, dict) else {}
    executable_raw = node_repl.get("command") if isinstance(node_repl, dict) else None
    executable = Path(str(executable_raw)) if executable_raw else None
    executable_present = bool(executable and executable.is_file())
    record(
        "node_repl_configured",
        "PASS" if executable_present else "FAIL",
        (
            "The app-managed node_repl MCP server is configured and its executable exists."
            if executable_present
            else "The app-managed node_repl MCP server is missing or its executable does not exist."
        ),
    )

    configured_environment = (
        node_repl.get("env", {})
        if isinstance(node_repl, dict) and isinstance(node_repl.get("env"), dict)
        else {}
    )
    backend = ADAPTER_BACKENDS[browser_adapter]
    configured_backends = {
        item.strip()
        for item in str(
            configured_environment.get("BROWSER_USE_AVAILABLE_BACKENDS", "")
        ).split(",")
        if item.strip()
    }
    record(
        "selected_backend_declared",
        "PASS" if backend in configured_backends else "FAIL",
        (
            f"The app-managed node_repl declares the {backend} backend."
            if backend in configured_backends
            else f"The app-managed node_repl does not declare the {backend} backend."
        ),
    )

    tool_names: list[str] = []
    if executable_present and executable is not None:
        probe_passed, tool_names, probe_detail = _probe_node_repl_tools(
            executable,
            configured_environment,
        )
        record(
            "node_repl_tools",
            "PASS" if probe_passed else "FAIL",
            probe_detail,
        )
    else:
        record(
            "node_repl_tools",
            "FAIL",
            "node_repl tools cannot be probed without its configured executable.",
        )

    if browser_adapter == "codex_chrome":
        native_host_status, native_host_detail = _chrome_native_host_check()
        record(
            "chrome_native_host",
            native_host_status,
            native_host_detail,
        )
    else:
        record(
            "chrome_native_host",
            "SKIP",
            "Chrome native-host registration is not applicable to codex_iab.",
            required_locally=False,
        )

    record(
        "current_task_tool_exposure",
        "UNKNOWN",
        (
            f"Repository tooling cannot prove that the current Codex task exposes "
            f"{REQUIRED_BROWSER_TOOL}; this must be observed in the task capability manifest."
        ),
        required_locally=False,
    )
    local_status = "PASS" if not local_failures else "FAIL"
    status = "BLOCKED" if local_status == "PASS" else "FAIL"
    blocking = list(local_failures)
    blocking.append(
        f"Current-task exposure of {REQUIRED_BROWSER_TOOL} remains UNKNOWN outside the Codex host."
    )
    report = {
        "$schema": "https://roblox-top1.local/schemas/precanonical-browser-doctor.schema.json",
        "schemaVersion": "1.0.0",
        "generatedAt": _utc_now(),
        "browserAdapter": browser_adapter,
        "requiredBackend": backend,
        "requiredTaskTool": REQUIRED_BROWSER_TOOL,
        "status": status,
        "localInstallationStatus": local_status,
        "currentTaskToolExposureStatus": "UNKNOWN",
        "repositoryCanLaunchBrowser": False,
        "submissionReady": False,
        "checks": checks,
        "exposedNodeReplTools": tool_names,
        "blockingReasons": list(dict.fromkeys(blocking)),
        "recommendedAction": (
            "Use a fresh Codex task that visibly exposes mcp__node_repl__js. "
            "For Chrome native-host failures, remove and re-add the official Chrome plugin; "
            "do not copy app-managed node_repl or pipe values by hand."
        ),
        "productionApproved": False,
    }
    _assert_schema(report, "browser_doctor")
    if output:
        write_json(output.resolve(), report)
    return report


def create_handoff(
    request_path: Path,
    preflight_path: Path,
    browser_doctor_path: Path,
    output: Path,
) -> dict[str, Any]:
    request_path = request_path.resolve()
    preflight_path = preflight_path.resolve()
    browser_doctor_path = browser_doctor_path.resolve()
    request = load_json(request_path)
    report = load_json(preflight_path)
    browser_report = load_json(browser_doctor_path)
    _assert_schema(request, "request")
    _assert_schema(report, "preflight")
    _assert_schema(browser_report, "browser_doctor")
    if report["status"] != "PASS":
        raise ArtSystemError("Web handoff requires a PASS preflight")
    if report["request"]["sha256"] != sha256_file(request_path):
        raise ArtSystemError("Preflight is not bound to the current request")
    adapter = request["automation"]["browserAdapter"]
    if browser_report["browserAdapter"] != adapter:
        raise ArtSystemError("Browser doctor adapter differs from the request")
    if browser_report["localInstallationStatus"] != "PASS":
        raise ArtSystemError(
            "Web handoff requires a PASS local browser installation doctor: "
            + "; ".join(browser_report["blockingReasons"])
        )
    prompt_path = _resolve_binding(request_path, request["files"]["prompt"])
    negative_path = _resolve_binding(
        request_path, request["files"]["negativeConstraints"]
    )
    negatives = [
        line.removeprefix("- ").strip()
        for line in negative_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    attachments: list[dict[str, str]] = []
    parent = request["parentResult"]
    if parent:
        parent_path = _resolve_binding(request_path, parent)
        parent_result = load_json(parent_path)
        _assert_schema(parent_result, "result")
        for image in parent_result["images"]:
            image_path = (parent_path.parent / image["path"]).resolve()
            if not image_path.is_file() or sha256_file(image_path) != image["sha256"]:
                raise ArtSystemError(
                    f"Parent result image binding is stale: {image['path']}"
                )
            attachments.append(
                {"path": str(image_path), "sha256": sha256_file(image_path)}
            )
    policy = load_json(POLICY_PATH)
    attachment_adapter = policy["providerContract"]["attachmentCapableBrowserAdapter"]
    if attachments and adapter != attachment_adapter:
        raise ArtSystemError(
            f"{adapter} cannot carry file attachments; use {attachment_adapter}"
        )
    if adapter == "codex_iab":
        instructions = [
            "Reuse one existing authenticated ChatGPT Web tab in the Codex in-app Browser when available.",
            "Submit the bound prompt without rewriting it in the browser.",
            "Keep this handoff attachment-free and do not attempt a file upload.",
            "After one result is ready, download it once and import the local file through the workflow.",
        ]
    else:
        instructions = [
            "Reuse one existing authenticated ChatGPT Web tab in Chrome when available.",
            "Submit the bound prompt without rewriting it in the browser.",
            "Attach only the hash-bound local references listed in this handoff.",
            "After one result is ready, download it once and import the local file through the workflow.",
        ]
    handoff = {
        "$schema": "https://roblox-top1.local/schemas/precanonical-handoff.schema.json",
        "schemaVersion": "1.1.0",
        "generatedAt": _utc_now(),
        "status": "AWAITING_TASK_BROWSER_CAPABILITY",
        "requestId": request["requestId"],
        "generationSurface": "chatgpt_web_images",
        "browserAdapter": adapter,
        "request": {"path": str(request_path), "sha256": sha256_file(request_path)},
        "preflight": {
            "path": str(preflight_path),
            "sha256": sha256_file(preflight_path),
        },
        "browserDoctor": {
            "path": str(browser_doctor_path),
            "sha256": sha256_file(browser_doctor_path),
        },
        "transportReadiness": {
            "status": "UNVERIFIED",
            "scope": "current_codex_task",
            "requiredTaskTool": REQUIRED_BROWSER_TOOL,
            "requiredBackend": ADAPTER_BACKENDS[adapter],
            "localInstallationIsSufficient": False,
        },
        "prompt": prompt_path.read_text(encoding="utf-8").strip(),
        "negativeConstraints": negatives,
        "attachments": attachments,
        "imageSpec": {
            "aspectRatio": request["imageSpec"]["aspectRatio"],
            "background": request["imageSpec"]["background"],
            "lighting": request["imageSpec"]["lighting"],
        },
        "humanConfirmationRequired": request["budget"]["humanConfirmationRequired"],
        "submissionAuthorized": False,
        "remainingGenerations": report["remainingGenerations"],
        "quotaRemaining": "UNKNOWN",
        "instructions": instructions,
        "forbiddenActions": [
            "Do not inspect cookies, authentication storage or account secrets.",
            "Do not retry or regenerate automatically after an error.",
            "Do not switch to Codex imagegen or an API automatically.",
            "Do not infer or record a precise internal model name unless the UI explicitly confirms it.",
            "Do not treat the generated image as canonical geometry or production approval.",
            "Do not switch browser adapters automatically; change the request explicitly and rerun preflight.",
            f"Do not submit automatically unless the current task visibly exposes {REQUIRED_BROWSER_TOOL}; use the explicit human operator route otherwise.",
        ],
        "productionApproved": False,
    }
    _assert_schema(handoff, "handoff")
    write_json(output.resolve(), handoff)
    return handoff


def import_result(
    request_path: Path,
    result_id: str,
    images: list[Path],
    output_dir: Path,
    download_method: str,
    model_name: str | None,
    model_name_confirmed: bool,
) -> Path:
    request_path = request_path.resolve()
    request = load_json(request_path)
    _assert_schema(request, "request")
    preflight_report = preflight(request_path)
    if preflight_report["status"] != "PASS":
        raise ArtSystemError(
            "Result import requires a current PASS preflight: "
            + "; ".join(preflight_report["blockingReasons"])
        )
    if model_name and not model_name_confirmed:
        raise ArtSystemError("A precise model name requires explicit UI confirmation")
    if model_name_confirmed and not model_name:
        raise ArtSystemError("--model-name-ui-confirmed requires --model-name")
    existing = []
    for path in _result_manifests(request_path):
        try:
            value = load_json(path)
            if not validate_with_schema(value, SCHEMAS["result"]):
                existing.append(value)
        except ArtSystemError:
            continue
    request_results = [
        value for value in existing if value["requestId"] == request["requestId"]
    ]
    generation_index = len(request_results) + 1
    if generation_index > request["budget"]["maximumWebGenerations"]:
        raise ArtSystemError("Web generation budget is exhausted")
    known_hashes = {
        image["sha256"]
        for result in existing
        for image in result["images"]
    }
    output_dir = output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ArtSystemError(f"Refusing to overwrite non-empty result directory: {output_dir}")
    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    image_records: list[dict[str, Any]] = []
    for index, source in enumerate(images, start=1):
        source = source.resolve()
        if not source.is_file():
            raise ArtSystemError(f"Downloaded image is missing: {source}")
        digest = sha256_file(source)
        if digest in known_hashes or any(item["sha256"] == digest for item in image_records):
            raise ArtSystemError(f"Duplicate image bytes are not accepted: {source}")
        try:
            with Image.open(source) as opened:
                opened.verify()
            with Image.open(source) as opened:
                width, height = opened.size
                image_format = (opened.format or "").upper()
        except Exception as exc:
            raise ArtSystemError(f"Invalid image file {source}: {exc}") from exc
        if image_format not in {"PNG", "JPEG", "WEBP"}:
            raise ArtSystemError(f"Unsupported image format: {image_format}")
        if width < 64 or height < 64:
            raise ArtSystemError("Imported image is too small for review")
        extension = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}[image_format]
        destination = raw_dir / f"generated-{index:03d}{extension}"
        shutil.copyfile(source, destination)
        image_records.append(
            {
                "path": destination.relative_to(output_dir).as_posix(),
                "sha256": digest,
                "bytes": destination.stat().st_size,
                "width": width,
                "height": height,
                "format": image_format,
            }
        )
    digest_value = {
        "requestSha256": sha256_file(request_path),
        "promptHash": request["promptHash"],
        "generationIndex": generation_index,
        "images": image_records,
        "surface": "ChatGPT Web / ChatGPT Images",
    }
    result = {
        "$schema": "https://roblox-top1.local/schemas/precanonical-result.schema.json",
        "schemaVersion": "1.0.0",
        "resultId": result_id,
        "requestId": request["requestId"],
        "status": "WEB_RESULT_IMPORTED",
        "importedAt": _utc_now(),
        "request": {"path": str(request_path), "sha256": sha256_file(request_path)},
        "promptHash": request["promptHash"],
        "generationIndex": generation_index,
        "provenance": {
            "surface": "ChatGPT Web / ChatGPT Images",
            "modelName": model_name,
            "modelNameEvidence": "UI_CONFIRMED" if model_name_confirmed else "NOT_CONFIRMED",
            "downloadMethod": download_method,
        },
        "images": image_records,
        "resultDigest": sha256_bytes(canonical_json_bytes(digest_value)),
        "canonical": False,
        "geometryAuthority": False,
        "humanReviewStatus": "PENDING",
        "productionApproved": False,
    }
    _assert_schema(result, "result")
    result_path = output_dir / "result.json"
    write_json(result_path, result)
    return result_path


def create_review(
    result_path: Path,
    review_id: str,
    decision: str,
    output: Path,
    assessment: dict[str, str],
    reviewer: str | None,
    preserve: list[str],
    correct: list[str],
    forbid_next: list[str],
) -> dict[str, Any]:
    result_path = result_path.resolve()
    result = load_json(result_path)
    _assert_schema(result, "result")
    for image in result["images"]:
        image_path = result_path.parent / image["path"]
        if not image_path.is_file() or sha256_file(image_path) != image["sha256"]:
            raise ArtSystemError(f"Result image binding is stale: {image['path']}")
    missing = set(ASSESSMENT_KEYS) - set(assessment)
    extra = set(assessment) - set(ASSESSMENT_KEYS)
    if missing or extra:
        raise ArtSystemError(
            f"Assessment keys differ: missing={sorted(missing)}, extra={sorted(extra)}"
        )
    if any(value not in {"PASS", "FAIL", "UNKNOWN"} for value in assessment.values()):
        raise ArtSystemError("Assessment values must be PASS, FAIL or UNKNOWN")
    if decision == "HUMAN_SELECTED":
        if not reviewer:
            raise ArtSystemError("HUMAN_SELECTED requires a named human reviewer")
    elif reviewer:
        raise ArtSystemError("A named reviewer is reserved for HUMAN_SELECTED authority")
    if decision in {"PRECANONICAL_CANDIDATE", "HUMAN_SELECTED"}:
        if any(value != "PASS" for value in assessment.values()):
            raise ArtSystemError(
                f"{decision} requires every assessment dimension to PASS"
            )
        if not preserve:
            raise ArtSystemError(
                f"{decision} requires at least one explicit preserve rule"
            )
    if decision in {"REVISION_REQUIRED", "REJECTED"} and not correct:
        raise ArtSystemError(
            f"{decision} requires at least one explicit correction rule"
        )
    if decision == "REJECTED" and not forbid_next:
        raise ArtSystemError(
            "REJECTED requires at least one explicit prohibition for the next attempt"
        )
    review = {
        "$schema": "https://roblox-top1.local/schemas/precanonical-review.schema.json",
        "schemaVersion": "1.0.0",
        "reviewId": review_id,
        "result": {"path": str(result_path), "sha256": sha256_file(result_path)},
        "resultDigest": result["resultDigest"],
        "decision": decision,
        "reviewer": reviewer,
        "reviewedAt": _utc_now() if reviewer else None,
        "assessment": assessment,
        "preserve": list(dict.fromkeys(preserve)),
        "correct": list(dict.fromkeys(correct)),
        "forbidNext": list(dict.fromkeys(forbid_next)),
        "canonicalizationAuthorized": decision == "HUMAN_SELECTED",
        "canonical": False,
        "productionApproved": False,
    }
    _assert_schema(review, "review")
    write_json(output.resolve(), review)
    return review


def status(request_path: Path) -> dict[str, Any]:
    request_path = request_path.resolve()
    request = load_json(request_path)
    _assert_schema(request, "request")
    manifests = []
    reviews = []
    for result_path in _result_manifests(request_path):
        try:
            result = load_json(result_path)
            _assert_schema(result, "result")
        except ArtSystemError:
            continue
        if result["requestId"] != request["requestId"]:
            continue
        manifests.append(result_path)
        review_path = result_path.parent / "review.json"
        if review_path.is_file():
            try:
                review = load_json(review_path)
                _assert_schema(review, "review")
                reviews.append((review_path, review["decision"]))
            except ArtSystemError:
                reviews.append((review_path, "INVALID"))
    return {
        "requestId": request["requestId"],
        "stage": request["stage"],
        "sourceStatus": request["status"],
        "resultCount": len(manifests),
        "remainingGenerations": max(
            0, request["budget"]["maximumWebGenerations"] - len(manifests)
        ),
        "results": [str(path) for path in manifests],
        "reviews": [
            {"path": str(path), "decision": decision}
            for path, decision in reviews
        ],
        "canonical": False,
        "productionApproved": False,
    }


def _assessment_arg(path: Path | None) -> dict[str, str]:
    if path is None:
        return {key: "UNKNOWN" for key in ASSESSMENT_KEYS}
    value = load_json(path.resolve())
    if not isinstance(value, dict):
        raise ArtSystemError("Assessment must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic precanonical request, Web handoff, intake and review workflow."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--brief", type=Path, required=True)
    init_parser.add_argument("--request-id", required=True)
    init_parser.add_argument("--output", type=Path, required=True)
    init_parser.add_argument(
        "--stage",
        choices=tuple(STAGE_VIEWS),
        default="exploration",
    )
    init_parser.add_argument("--maximum-generations", type=int, default=4)
    init_parser.add_argument(
        "--browser-adapter",
        choices=BROWSER_ADAPTERS,
        default="codex_chrome",
        help=(
            "Explicit browser transport. codex_iab is valid only when the "
            "resulting handoff has no file attachments."
        ),
    )
    init_parser.add_argument(
        "--no-human-confirmation",
        action="store_true",
        help="Only valid when the user has authorized bounded automatic submission.",
    )
    init_parser.add_argument("--authorize-automatic-submission", action="store_true")
    init_parser.add_argument("--parent-result", type=Path)
    init_parser.add_argument("--revision-instruction", action="append", default=[])

    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("request", type=Path)
    preflight_parser.add_argument("--output", type=Path)

    doctor_parser = subparsers.add_parser("browser-doctor")
    doctor_parser.add_argument(
        "--browser-adapter",
        choices=BROWSER_ADAPTERS,
        required=True,
    )
    doctor_parser.add_argument("--output", type=Path)
    doctor_parser.add_argument("--codex-home", type=Path)

    handoff_parser = subparsers.add_parser("handoff")
    handoff_parser.add_argument("request", type=Path)
    handoff_parser.add_argument("--preflight", type=Path, required=True)
    handoff_parser.add_argument("--browser-doctor", type=Path, required=True)
    handoff_parser.add_argument("--output", type=Path, required=True)

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("request", type=Path)
    import_parser.add_argument("--result-id", required=True)
    import_parser.add_argument("--image", type=Path, action="append", required=True)
    import_parser.add_argument("--output", type=Path, required=True)
    import_parser.add_argument(
        "--download-method",
        choices=("browser_download", "manual_download"),
        default="browser_download",
    )
    import_parser.add_argument("--model-name")
    import_parser.add_argument("--model-name-ui-confirmed", action="store_true")

    review_parser = subparsers.add_parser("review")
    review_parser.add_argument("result", type=Path)
    review_parser.add_argument("--review-id", required=True)
    review_parser.add_argument(
        "--decision",
        choices=(
            "REJECTED",
            "REVISION_REQUIRED",
            "PRECANONICAL_CANDIDATE",
            "HUMAN_SELECTED",
        ),
        required=True,
    )
    review_parser.add_argument("--output", type=Path, required=True)
    review_parser.add_argument("--assessment", type=Path)
    review_parser.add_argument("--reviewer")
    review_parser.add_argument("--preserve", action="append", default=[])
    review_parser.add_argument("--correct", action="append", default=[])
    review_parser.add_argument("--forbid-next", action="append", default=[])

    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("request", type=Path)

    args = parser.parse_args()
    try:
        if args.command == "init":
            if args.no_human_confirmation and not args.authorize_automatic_submission:
                raise ArtSystemError(
                    "--no-human-confirmation requires --authorize-automatic-submission"
                )
            path = init_packet(
                args.brief,
                args.request_id,
                args.output,
                args.stage,
                args.maximum_generations,
                not args.no_human_confirmation,
                args.authorize_automatic_submission,
                args.parent_result,
                args.revision_instruction,
                args.browser_adapter,
            )
            print(f"[PASS] Precanonical request packet: {path}")
            return 0
        if args.command == "preflight":
            report = preflight(args.request, args.output)
            print(
                f"[{report['status']}] {report['requestId']} | "
                f"remaining={report['remainingGenerations']} | "
                f"next={report['nextState']}"
            )
            for reason in report["blockingReasons"]:
                print(f"[{report['status']}] {reason}")
            return 0 if report["status"] == "PASS" else (2 if report["status"] == "BLOCKED" else 1)
        if args.command == "browser-doctor":
            report = browser_doctor(
                args.browser_adapter,
                args.output,
                args.codex_home,
            )
            print(
                f"[{report['status']}] {report['browserAdapter']} | "
                f"local={report['localInstallationStatus']} | "
                f"taskTool={report['currentTaskToolExposureStatus']}"
            )
            for reason in report["blockingReasons"]:
                print(f"[{report['status']}] {reason}")
            return 0 if report["localInstallationStatus"] == "PASS" else 1
        if args.command == "handoff":
            handoff = create_handoff(
                args.request,
                args.preflight,
                args.browser_doctor,
                args.output,
            )
            print(
                f"[PASS] Web handoff prepared without quota consumption; "
                f"task capability remains required: "
                f"{args.output.resolve()} | remaining={handoff['remainingGenerations']}"
            )
            return 0
        if args.command == "import":
            path = import_result(
                args.request,
                args.result_id,
                args.image,
                args.output,
                args.download_method,
                args.model_name,
                args.model_name_ui_confirmed,
            )
            print(f"[PASS] Web result imported with conservative provenance: {path}")
            return 0
        if args.command == "review":
            review = create_review(
                args.result,
                args.review_id,
                args.decision,
                args.output,
                _assessment_arg(args.assessment),
                args.reviewer,
                args.preserve,
                args.correct,
                args.forbid_next,
            )
            print(
                f"[PASS] Review recorded: {review['decision']} | "
                f"canonicalizationAuthorized={review['canonicalizationAuthorized']}"
            )
            return 0
        if args.command == "status":
            print(json.dumps(status(args.request), indent=2, ensure_ascii=False))
            return 0
    except ArtSystemError as exc:
        print(f"[FAIL] {exc}")
        return 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
