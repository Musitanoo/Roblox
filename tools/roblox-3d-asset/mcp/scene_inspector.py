from __future__ import annotations

import json
import subprocess
import uuid
from pathlib import Path
from typing import Any

from mcp.evidence_writer import write_json
from mcp.security_policy import (
    RepositoryOperationLock,
    WorkbenchError,
    ensure_within,
    sanitized_blender_environment,
)
from pipeline.doctor import find_blender


def file_sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_bridge(
    *,
    repo: Path,
    session_root: Path,
    blend_path: Path,
    contract_path: Path,
    action: str,
    operations: list[dict[str, Any]] | None = None,
    capture_root: Path | None = None,
) -> dict[str, Any]:
    """Run the closed Blender dispatcher against one session-contained scene."""
    repo = repo.resolve()
    session_root = ensure_within(session_root, repo / "assets-3d", "session root")
    blend_path = ensure_within(blend_path, session_root, "workbench blend")
    contract_path = ensure_within(contract_path, repo / "assets-3d", "asset contract")
    if action not in {"inspect", "preview", "mutate"}:
        raise WorkbenchError(f"unsupported bridge action: {action}")
    if action in {"preview", "mutate"} and not operations:
        raise WorkbenchError(f"{action} requires declared operations")
    if not blend_path.is_file() or not contract_path.is_file():
        raise WorkbenchError("workbench bridge input is missing")

    blender = find_blender()
    if blender is None:
        raise WorkbenchError("Blender not found")
    runtime = session_root / "Review" / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    call_id = uuid.uuid4().hex
    request_path = runtime / f"{call_id}-request.json"
    response_path = runtime / f"{call_id}-response.json"
    log_path = session_root / "Evidence" / "logs" / f"{call_id}.log"
    request: dict[str, Any] = {
        "action": action,
        "blendPath": str(blend_path),
        "contractPath": str(contract_path),
        "operations": operations or [],
        "capture": capture_root is not None,
    }
    if capture_root is not None:
        request["captureRoot"] = str(
            ensure_within(capture_root, session_root, "capture root")
        )
    if action == "mutate":
        request["savePath"] = str(blend_path)
    write_json(request_path, request)
    command = [
        str(blender),
        "--background",
        "--python",
        str(repo / "tools" / "roblox-3d-asset" / "blender" / "workbench_bridge.py"),
        "--",
        str(request_path),
        str(response_path),
    ]
    with RepositoryOperationLock(repo):
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            env=sanitized_blender_environment(),
            timeout=300,
        )
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        (completed.stdout or "") + (completed.stderr or ""), encoding="utf-8"
    )
    if not response_path.is_file():
        raise WorkbenchError(
            f"Blender bridge produced no response (exit={completed.returncode}, log={log_path})"
        )
    try:
        response = json.loads(response_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkbenchError(f"invalid Blender bridge response: {error}") from error
    response["blenderExecutable"] = str(blender)
    response["commandExitCode"] = completed.returncode
    response["log"] = str(log_path)
    if completed.returncode != 0 or response.get("status") != "PASS":
        raise WorkbenchError(
            "; ".join(response.get("errors", []))
            or f"Blender bridge failed (exit={completed.returncode})"
        )
    return response


def _object_map(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["name"]: item for item in manifest["objects"]}


def scene_diff(
    reference: dict[str, Any], candidate: dict[str, Any]
) -> dict[str, Any]:
    before = _object_map(reference)
    after = _object_map(candidate)
    changes: list[dict[str, Any]] = []
    for name in sorted(set(before) | set(after)):
        left = before.get(name)
        right = after.get(name)
        if left == right:
            continue
        changes.append(
            {
                "name": name,
                "before": left,
                "after": right,
            }
        )
    return {
        "schemaVersion": "1.0.0",
        "status": "PASS",
        "referenceSemanticSha256": reference["semanticSha256"],
        "candidateSemanticSha256": candidate["semanticSha256"],
        "changedComponents": changes,
        "triangleDelta": candidate["triangleCount"] - reference["triangleCount"],
        "boundsBefore": reference["overallBoundsDesign"],
        "boundsAfter": candidate["overallBoundsDesign"],
        "materialsBefore": reference["materials"],
        "materialsAfter": candidate["materials"],
    }


def _close(left: float, right: float, tolerance: float = 1e-4) -> bool:
    return abs(float(left) - float(right)) <= tolerance


def evaluate_invariants(
    *,
    reference: dict[str, Any],
    candidate: dict[str, Any],
    contract: dict[str, Any],
    requested: list[str],
    maximum_triangle_delta: int,
    reference_hash_before: str,
    reference_hash_after: str,
    contract_hash_before: str,
    contract_hash_after: str,
    canon_hash_before: str,
    canon_hash_after: str,
) -> dict[str, Any]:
    reference_objects = _object_map(reference)
    candidate_objects = _object_map(candidate)
    before_dimensions = reference["overallBoundsDesign"]["dimensions"]
    after_dimensions = candidate["overallBoundsDesign"]["dimensions"]

    interaction_names = [
        name
        for name in reference_objects
        if "socket" in name.lower() or "light" in name.lower()
    ]
    interaction_unchanged = all(
        reference_objects[name]["designLocation"]
        == candidate_objects.get(name, {}).get("designLocation")
        for name in interaction_names
    )
    checks: dict[str, dict[str, Any]] = {
        "overallWidth": {
            "passed": _close(before_dimensions[0], after_dimensions[0]),
            "before": before_dimensions[0],
            "after": after_dimensions[0],
        },
        "overallHeight": {
            "passed": _close(before_dimensions[1], after_dimensions[1]),
            "before": before_dimensions[1],
            "after": after_dimensions[1],
        },
        "overallDepth": {
            "passed": _close(before_dimensions[2], after_dimensions[2]),
            "before": before_dimensions[2],
            "after": after_dimensions[2],
        },
        "grounding": {
            "passed": _close(
                reference["pivotAndGrounding"]["groundY"],
                candidate["pivotAndGrounding"]["groundY"],
            ),
            "before": reference["pivotAndGrounding"]["groundY"],
            "after": candidate["pivotAndGrounding"]["groundY"],
        },
        "interactionSocketPosition": {
            "passed": interaction_unchanged,
            "objects": interaction_names,
        },
        "componentNames": {
            "passed": set(reference_objects) == set(candidate_objects),
            "before": sorted(reference_objects),
            "after": sorted(candidate_objects),
        },
        "materialAssignments": {
            "passed": all(
                reference_objects[name]["materials"]
                == candidate_objects.get(name, {}).get("materials")
                for name in reference_objects
            ),
        },
        "triangleBudget": {
            "passed": (
                candidate["triangleCount"]
                <= contract["triangleBudget"]["absoluteMaximum"]
                and abs(candidate["triangleCount"] - reference["triangleCount"])
                <= maximum_triangle_delta
            ),
            "before": reference["triangleCount"],
            "after": candidate["triangleCount"],
            "absoluteMaximum": contract["triangleBudget"]["absoluteMaximum"],
            "allowedDelta": maximum_triangle_delta,
        },
        "collisionContractUnchanged": {
            "passed": contract_hash_before == contract_hash_after,
            "note": "collision remains contract-owned and the contract hash did not change",
        },
        "referenceImmutability": {
            "passed": reference_hash_before == reference_hash_after,
            "before": reference_hash_before,
            "after": reference_hash_after,
        },
        "visualCanonBinding": {
            "passed": canon_hash_before == canon_hash_after,
            "before": canon_hash_before,
            "after": canon_hash_after,
        },
    }
    selected = {name: checks[name] for name in requested}
    passed = all(item["passed"] for item in selected.values())
    return {
        "$schema": "https://roblox-top1.local/schemas/blender-invariant-report.schema.json",
        "schemaVersion": "1.0.0",
        "status": "PASS" if passed else "FAIL",
        "requested": requested,
        "checks": selected,
        "allKnownChecks": checks,
    }
