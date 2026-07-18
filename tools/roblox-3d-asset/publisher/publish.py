from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.contract import validate_contract
from pipeline.io_utils import read_json, sha256_file, write_json
from pipeline.status import Status
from publisher.http_client import ApiError, get_json, mutate_asset, poll_operation


MAX_MODEL_BYTES = 20_000_000


def _creator(publication: dict[str, Any], creator_id: str) -> dict[str, str]:
    key = "userId" if publication["creatorType"] == "User" else "groupId"
    return {key: creator_id}


def _resolve_repo(contract_path: Path) -> Path:
    # assets-3d/<asset>/asset.json
    return contract_path.parents[2]


def _registry_path(repo: Path, publication: dict[str, Any]) -> Path:
    path = Path(publication["registry"])
    return path if path.is_absolute() else repo / path


def _visual_canon_path(contract_path: Path, configured_path: str) -> Path:
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


def _build_evidence(contract_path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    build = contract_path.parent / "build"
    manifest_path = build / "manifest.json"
    geometry_path = build / "geometry.json"
    provenance_path = build / "provenance.json"
    for path in (manifest_path, geometry_path, provenance_path):
        if not path.is_file():
            errors.append(f"missing build evidence: {path}")
    if errors:
        return None, errors
    manifest = read_json(manifest_path)
    geometry = read_json(geometry_path)
    provenance = read_json(provenance_path)
    contract = read_json(contract_path)
    if manifest.get("status") != Status.PASS.value:
        errors.append("manifest status is not PASS")
    if geometry.get("status") != Status.PASS.value:
        errors.append("geometry status is not PASS")
    visual_canon = contract.get("visualCanon", {})
    canon_path = _visual_canon_path(
        contract_path, str(visual_canon.get("path", ""))
    )
    if not canon_path.is_file():
        errors.append(f"visual canon file is missing: {canon_path}")
    else:
        canon_sha256 = sha256_file(canon_path)
        if canon_sha256 != visual_canon.get("sha256"):
            errors.append("asset contract visual canon hash is stale")
        if manifest.get("visualCanon", {}).get("sha256") != canon_sha256:
            errors.append("build manifest visual canon hash is stale")
        if provenance.get("visualCanon", {}).get("sha256") != canon_sha256:
            errors.append("build provenance visual canon hash is stale")
    artifacts = manifest.get("artifacts", {})
    for key in ("glb", "fbxUpdate"):
        artifact = artifacts.get(key)
        if not isinstance(artifact, dict):
            errors.append(f"manifest is missing artifact {key}")
            continue
        path = Path(artifact.get("path", ""))
        if not path.is_absolute():
            path = contract_path.parents[2] / path
        if not path.is_file():
            errors.append(f"artifact file is missing: {path}")
            continue
        if path.stat().st_size > MAX_MODEL_BYTES:
            errors.append(f"artifact exceeds Roblox 20 MB limit: {path}")
        if sha256_file(path) != artifact.get("sha256"):
            errors.append(f"artifact hash does not match manifest: {path}")
    return {
        "manifest": manifest,
        "geometry": geometry,
        "provenance": provenance,
        "manifestPath": manifest_path,
    }, errors


def _load_registry(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"schemaVersion": "1.0.0", "environment": "staging", "assets": {}}
    registry = read_json(path)
    if registry.get("environment") != "staging" or not isinstance(registry.get("assets"), dict):
        raise ValueError("registry must be a staging registry with an assets object")
    return registry


def _cloud_creator_matches(remote: dict[str, Any], expected: dict[str, str]) -> bool:
    actual = remote.get("creationContext", {}).get("creator", {})
    return all(str(actual.get(key)) == str(value) for key, value in expected.items())


def publish(contract_path: Path, *, dry_run: bool, confirm_publish: bool) -> dict[str, Any]:
    validation = validate_contract(contract_path)
    if validation["status"] != Status.PASS.value:
        return validation
    contract = read_json(contract_path)
    evidence, evidence_errors = _build_evidence(contract_path)
    if evidence_errors:
        return {"status": Status.FAIL.value, "errors": evidence_errors}
    assert evidence is not None

    publication = contract["publication"]
    repo = _resolve_repo(contract_path)
    registry_path = _registry_path(repo, publication)
    try:
        registry = _load_registry(registry_path)
    except (OSError, ValueError) as error:
        return {"status": Status.FAIL.value, "errors": [str(error)]}
    entry = registry["assets"].get(contract["assetKey"])
    action = "UPDATE" if entry and entry.get("packageId") else "CREATE"
    artifact_key = "fbxUpdate" if action == "UPDATE" else "glb"
    artifact = evidence["manifest"]["artifacts"][artifact_key]
    artifact_path = Path(artifact["path"])
    if not artifact_path.is_absolute():
        artifact_path = repo / artifact_path
    semantic_hash = evidence["provenance"]["semanticSha256"]

    if entry and entry.get("semanticSha256") == semantic_hash:
        return {
            "status": Status.SKIPPED.value,
            "reason": "semantic asset hash is unchanged",
            "packageId": entry.get("packageId"),
            "semanticSha256": semantic_hash,
        }

    secret_presence = {
        publication["apiKeyEnv"]: bool(os.environ.get(publication["apiKeyEnv"])),
        publication["creatorIdEnv"]: bool(os.environ.get(publication["creatorIdEnv"])),
        publication["creatorAllowlistEnv"]: bool(os.environ.get(publication["creatorAllowlistEnv"])),
    }
    plan = {
        "action": action,
        "environment": "staging",
        "artifact": str(artifact_path),
        "format": artifact_path.suffix.lower().removeprefix("."),
        "artifactSha256": artifact["sha256"],
        "semanticSha256": semantic_hash,
        "packageId": entry.get("packageId") if entry else None,
        "registry": str(registry_path),
        "requiredEnvironmentVariablesPresent": secret_presence,
    }
    if dry_run:
        return {"status": Status.PARTIAL.value, "dryRun": True, "mutationPerformed": False, "plan": plan}
    if not confirm_publish:
        return {"status": Status.BLOCKED.value, "reason": "--confirm-publish is required", "plan": plan}

    api_key = os.environ.get(publication["apiKeyEnv"], "")
    creator_id = os.environ.get(publication["creatorIdEnv"], "")
    allowlist = {
        value.strip()
        for value in os.environ.get(publication["creatorAllowlistEnv"], "").split(",")
        if value.strip()
    }
    if not api_key or not creator_id or not allowlist:
        return {"status": Status.BLOCKED.value, "reason": "staging credentials/allowlist are incomplete", "plan": plan}
    if not creator_id.isdigit() or creator_id not in allowlist:
        return {
            "status": Status.BLOCKED.value,
            "reason": "staging creator ID is not numeric or is absent from the explicit allowlist",
            "plan": plan,
        }

    creator = _creator(publication, creator_id)
    request_value: dict[str, Any]
    method: str
    endpoint: str
    media_type: str
    if action == "CREATE":
        method = "POST"
        endpoint = "/assets"
        media_type = "model/gltf-binary"
        request_value = {
            "assetType": "Model",
            "displayName": contract["displayName"],
            "description": f"Staging package for {contract['assetKey']} revision {contract['revision']}",
            "creationContext": {"creator": creator},
        }
    else:
        package_id = str(entry["packageId"])
        try:
            remote_before = get_json(f"/assets/{package_id}", api_key)
        except ApiError as error:
            return {"status": Status.BLOCKED.value if error.retryable else Status.FAIL.value, "reason": str(error), "plan": plan}
        if str(remote_before.get("assetId")) != package_id or not _cloud_creator_matches(remote_before, creator):
            return {"status": Status.BLOCKED.value, "reason": "remote Package identity/creator does not match staging target", "plan": plan}
        method = "PATCH"
        endpoint = f"/assets/{package_id}"
        media_type = "model/fbx"
        request_value = {
            "assetType": "Model",
            "assetId": int(package_id),
            "creationContext": {"creator": creator, "expectedPrice": 0},
        }

    try:
        operation_start = mutate_asset(method, endpoint, api_key, request_value, artifact_path, media_type)
        operation_path = operation_start.get("path")
        if not isinstance(operation_path, str) or not operation_path.startswith("operations/"):
            raise ApiError("Open Cloud mutation did not return a valid operation path")
        operation = poll_operation(operation_path, api_key)
        remote = operation.get("response")
        if not isinstance(remote, dict):
            raise ApiError("completed operation did not contain an asset response")
        package_id = str(remote.get("assetId", ""))
        if not package_id.isdigit():
            raise ApiError("completed operation did not contain a numeric assetId")
        reread = get_json(f"/assets/{package_id}", api_key)
        if str(reread.get("assetId")) != package_id or not _cloud_creator_matches(reread, creator):
            raise ApiError("remote asset reread failed the identity/creator postcondition")
    except ApiError as error:
        return {
            "status": Status.BLOCKED.value if error.retryable or error.status_code in {401, 403, 429} else Status.FAIL.value,
            "reason": str(error),
            "plan": plan,
        }

    history = list(entry.get("history", [])) if entry else []
    history.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "revision": contract["revision"],
            "operationPath": operation_path,
            "remoteRevisionId": reread.get("revisionId"),
            "artifactFormat": artifact_path.suffix.lower().removeprefix("."),
            "artifactSha256": artifact["sha256"],
            "semanticSha256": semantic_hash,
        }
    )
    registry["assets"][contract["assetKey"]] = {
        "packageId": int(package_id),
        "creatorType": publication["creatorType"],
        "creatorId": creator_id,
        "latestContractRevision": contract["revision"],
        "remoteRevisionId": reread.get("revisionId"),
        "semanticSha256": semantic_hash,
        "history": history,
    }
    write_json(registry_path, registry)
    return {
        "status": Status.PASS.value,
        "action": action,
        "packageId": int(package_id),
        "remoteRevisionId": reread.get("revisionId"),
        "operationPath": operation_path,
        "registry": str(registry_path),
    }
