from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.art.common import (
    PROJECT_ROOT,
    ROOT,
    ArtSystemError,
    load_json,
    sha256_file,
    validate_with_schema,
    write_json,
)
from tools.art.validate_transfer_report import validate_report

R3D_ROOT = ROOT / "tools/roblox-3d-asset"
if str(R3D_ROOT) not in sys.path:
    sys.path.insert(0, str(R3D_ROOT))

from publisher.http_client import ApiError, get_json, mutate_asset, poll_operation  # noqa: E402

SCHEMA = "https://roblox-top1.local/schemas/transfer-publication-report.schema.json"
DEFAULT_MANIFEST = ROOT / "build/studio-import-transfer/manifest.json"
PORTABLE_MANIFEST = (
    ROOT
    / "evidence/transfer/turret-fast-v1/studio-import-manifest.json"
)
DEFAULT_REGISTRY = (
    PROJECT_ROOT
    / "assets-3d/registry/turret-transfer-staging.local.json"
)
DEFAULT_REPORT = (
    ROOT
    / "evidence/transfer/turret-fast-v1/studio-publication-report.json"
)
MAX_MODEL_BYTES = 20_000_000
REQUIRED_ENV = (
    "ROBLOX_OPEN_CLOUD_API_KEY",
    "ROBLOX_STAGING_CREATOR_ID",
    "ROBLOX_3D_ALLOWED_CREATOR_IDS",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    ).encode("utf-8")
    handle, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(handle, "wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _creator(creator_id: str) -> dict[str, str]:
    return {"userId": creator_id}


def _creator_matches(remote: dict[str, Any], expected: dict[str, str]) -> bool:
    actual = remote.get("creationContext", {}).get("creator", {})
    return all(str(actual.get(key)) == str(value) for key, value in expected.items())


def _safe_issue(error: Exception) -> str:
    if isinstance(error, ApiError):
        if error.status_code is not None:
            return f"Open Cloud request failed with HTTP {error.status_code}"
        if error.retryable:
            return "Open Cloud request failed with a retryable network or polling error"
        return "Open Cloud request failed"
    message = str(error)
    message = re.sub(r"\b\d{6,}\b", "[REDACTED]", message)
    message = re.sub(
        r"\b[0-9a-f]{8}-[0-9a-f-]{27,}\b",
        "[REDACTED]",
        message,
        flags=re.IGNORECASE,
    )
    return message[:300]


def _load_registry(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {
            "schemaVersion": "1.0.0",
            "environment": "staging",
            "assetId": "turret_fast_v1",
            "assets": {},
        }
    registry = load_json(path)
    if (
        registry.get("schemaVersion") != "1.0.0"
        or registry.get("environment") != "staging"
        or registry.get("assetId") != "turret_fast_v1"
        or not isinstance(registry.get("assets"), dict)
    ):
        raise ArtSystemError(
            "local transfer publication registry is not a staging turret_fast_v1 registry"
        )
    return registry


def _validated_manifest(path: Path) -> dict[str, Any]:
    manifest = load_json(path)
    issues = validate_with_schema(
        manifest,
        ROOT / "schemas/transfer-import-queue.schema.json",
    )
    if issues:
        raise ArtSystemError(
            "transfer import manifest is invalid: " + "; ".join(issues)
        )
    transfer_report_path = ROOT / "evidence/transfer/turret-fast-v1/report.json"
    transfer_validation = validate_report(transfer_report_path)
    if transfer_validation["status"] != "PASS":
        raise ArtSystemError(
            "transfer evidence is stale: "
            + "; ".join(transfer_validation["issues"])
        )
    if manifest["transferReportSha256"] != sha256_file(transfer_report_path):
        raise ArtSystemError("transfer import manifest is bound to a stale report")
    transfer_report = load_json(transfer_report_path)
    if (
        manifest["evidencePackageSha256"]
        != transfer_report["evidencePackageSha256"]
    ):
        raise ArtSystemError(
            "transfer import manifest evidence digest does not match the current proof"
        )
    for entry in manifest["entries"]:
        artifact = ROOT / entry["path"]
        try:
            artifact.resolve().relative_to((ROOT / "build").resolve())
        except ValueError as exc:
            raise ArtSystemError(
                f"publication artifact escapes the generated build root: {entry['path']}"
            ) from exc
        if not artifact.is_file():
            raise ArtSystemError(
                f"publication artifact is missing: {entry['path']}"
            )
        if artifact.stat().st_size != entry["bytes"]:
            raise ArtSystemError(
                f"publication artifact byte count drift: {entry['uploadName']}"
            )
        if artifact.stat().st_size > MAX_MODEL_BYTES:
            raise ArtSystemError(
                f"publication artifact exceeds Roblox 20 MB limit: {entry['uploadName']}"
            )
        if sha256_file(artifact) != entry["sha256"]:
            raise ArtSystemError(
                f"publication artifact hash drift: {entry['uploadName']}"
            )
    if not PORTABLE_MANIFEST.is_file():
        raise ArtSystemError("portable transfer import manifest is missing")
    if sha256_file(PORTABLE_MANIFEST) != sha256_file(path):
        raise ArtSystemError(
            "portable transfer import manifest differs from the generated upload queue"
        )
    return manifest


def _guard_state() -> tuple[dict[str, bool], str, str, set[str]]:
    api_key = os.environ.get(REQUIRED_ENV[0], "")
    creator_id = os.environ.get(REQUIRED_ENV[1], "")
    allowlist = {
        value.strip()
        for value in os.environ.get(REQUIRED_ENV[2], "").split(",")
        if value.strip()
    }
    state = {
        "credentialsPresent": bool(api_key and creator_id and allowlist),
        "creatorNumeric": creator_id.isdigit(),
        "creatorAllowlisted": bool(creator_id and creator_id in allowlist),
        "manifestCurrent": True,
        "artifactHashesVerified": True,
        "remoteIdentityVerified": False,
    }
    return state, api_key, creator_id, allowlist


def _base_report(
    manifest: dict[str, Any],
    manifest_path: Path,
    guards: dict[str, bool],
) -> dict[str, Any]:
    return {
        "$schema": SCHEMA,
        "schemaVersion": "1.0.0",
        "status": "BLOCKED",
        "generatedAt": _utc_now(),
        "environment": "staging",
        "assetId": "turret_fast_v1",
        "assetCount": 9,
        "mutationPerformed": False,
        "manifestSha256": sha256_file(manifest_path),
        "evidencePackageSha256": manifest["evidencePackageSha256"],
        "inputHashes": {
            "transferReport": sha256_file(
                ROOT / "evidence/transfer/turret-fast-v1/report.json"
            ),
            "publisher": sha256_file(Path(__file__)),
            "httpClient": sha256_file(
                ROOT / "tools/roblox-3d-asset/publisher/http_client.py"
            ),
            "importQueueBuilder": sha256_file(
                ROOT / "tools/art/build_transfer_import_queue.py"
            ),
        },
        "privacy": {
            "rawAssetIdsIncluded": False,
            "rawCreatorIdIncluded": False,
            "rawApiKeyIncluded": False,
            "operationPathsIncluded": False,
        },
        "guardChecks": guards,
        "entries": [],
        "issues": [],
    }


def _validate_public_report(report: dict[str, Any]) -> None:
    issues = validate_with_schema(
        report,
        ROOT / "schemas/transfer-publication-report.schema.json",
    )
    if issues:
        raise ArtSystemError(
            "generated transfer publication report is invalid: "
            + "; ".join(issues)
        )


def publish(
    manifest_path: Path = DEFAULT_MANIFEST,
    registry_path: Path = DEFAULT_REGISTRY,
    report_path: Path = DEFAULT_REPORT,
    *,
    dry_run: bool,
    confirm_publish: bool,
) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    registry_path = registry_path.resolve()
    report_path = report_path.resolve()
    manifest = _validated_manifest(manifest_path)
    guards, api_key, creator_id, _allowlist = _guard_state()
    report = _base_report(manifest, manifest_path, guards)

    if dry_run:
        return {
            "status": "PARTIAL",
            "dryRun": True,
            "mutationPerformed": False,
            "environment": "staging",
            "assetCount": 9,
            "manifestSha256": report["manifestSha256"],
            "evidencePackageSha256": report["evidencePackageSha256"],
            "requiredEnvironmentVariablesPresent": {
                name: bool(os.environ.get(name)) for name in REQUIRED_ENV
            },
            "plannedUploads": [
                {
                    "uploadName": entry["uploadName"],
                    "sourceSha256": entry["sha256"],
                    "bytes": entry["bytes"],
                }
                for entry in manifest["entries"]
            ],
        }
    if not confirm_publish:
        report["issues"] = ["explicit --confirm-publish authorization is required"]
        _validate_public_report(report)
        write_json(report_path, report)
        return report
    if not all(
        guards[key]
        for key in (
            "credentialsPresent",
            "creatorNumeric",
            "creatorAllowlisted",
        )
    ):
        report["issues"] = [
            "staging credentials or explicit creator allowlist are incomplete"
        ]
        _validate_public_report(report)
        write_json(report_path, report)
        return report

    registry = _load_registry(registry_path)
    creator = _creator(creator_id)
    mutation_performed = False
    public_entries: list[dict[str, Any]] = []
    failures: list[str] = []

    for entry in manifest["entries"]:
        upload_name = entry["uploadName"]
        artifact = ROOT / entry["path"]
        local = registry["assets"].get(upload_name)
        action = "CREATE"
        remote_identity_verified = False
        try:
            if (
                isinstance(local, dict)
                and str(local.get("assetId", "")).isdigit()
                and local.get("sourceSha256") == entry["sha256"]
            ):
                remote = get_json(f"/assets/{local['assetId']}", api_key)
                if (
                    str(remote.get("assetId")) != str(local["assetId"])
                    or not _creator_matches(remote, creator)
                ):
                    raise ArtSystemError(
                        f"{upload_name}: existing local registry identity does not match staging creator"
                    )
                action = "REUSE"
                remote_identity_verified = True
            else:
                request_value = {
                    "assetType": "Model",
                    "displayName": upload_name,
                    "description": (
                        "STAGING CANDIDATE ONLY - automated sixth-asset transfer "
                        f"proof for {upload_name}; not production canon."
                    ),
                    "creationContext": {"creator": creator},
                }
                operation_start = mutate_asset(
                    "POST",
                    "/assets",
                    api_key,
                    request_value,
                    artifact,
                    "model/gltf-binary",
                )
                operation_path = operation_start.get("path")
                if (
                    not isinstance(operation_path, str)
                    or not operation_path.startswith("operations/")
                ):
                    raise ApiError(
                        "Open Cloud mutation did not return a valid operation path"
                    )
                operation = poll_operation(operation_path, api_key)
                remote = operation.get("response")
                if not isinstance(remote, dict):
                    raise ApiError(
                        "completed operation did not contain an asset response"
                    )
                asset_id = str(remote.get("assetId", ""))
                if not asset_id.isdigit():
                    raise ApiError(
                        "completed operation did not contain a numeric assetId"
                    )
                reread = get_json(f"/assets/{asset_id}", api_key)
                if (
                    str(reread.get("assetId")) != asset_id
                    or not _creator_matches(reread, creator)
                ):
                    raise ApiError(
                        "remote asset reread failed the staging identity postcondition"
                    )
                prior_history = (
                    list(local.get("history", []))
                    if isinstance(local, dict)
                    else []
                )
                prior_history.append(
                    {
                        "publishedAt": _utc_now(),
                        "assetId": int(asset_id),
                        "sourceSha256": entry["sha256"],
                        "operationPath": operation_path,
                        "remoteRevisionId": reread.get("revisionId"),
                    }
                )
                registry["assets"][upload_name] = {
                    "assetId": int(asset_id),
                    "sourceSha256": entry["sha256"],
                    "remoteRevisionId": reread.get("revisionId"),
                    "history": prior_history,
                }
                registry["manifestSha256"] = report["manifestSha256"]
                registry["evidencePackageSha256"] = manifest[
                    "evidencePackageSha256"
                ]
                registry["updatedAt"] = _utc_now()
                _atomic_write_json(registry_path, registry)
                mutation_performed = True
                remote_identity_verified = True
            public_entries.append(
                {
                    "territoryId": entry["territoryId"],
                    "stateId": entry["stateId"],
                    "uploadName": upload_name,
                    "sourceSha256": entry["sha256"],
                    "bytes": entry["bytes"],
                    "action": action,
                    "remoteIdentityVerified": remote_identity_verified,
                }
            )
        except Exception as error:
            failures.append(f"{upload_name}: {_safe_issue(error)}")
            public_entries.append(
                {
                    "territoryId": entry["territoryId"],
                    "stateId": entry["stateId"],
                    "uploadName": upload_name,
                    "sourceSha256": entry["sha256"],
                    "bytes": entry["bytes"],
                    "action": "FAILED",
                    "remoteIdentityVerified": False,
                }
            )
            break

    all_remote_verified = (
        len(public_entries) == 9
        and not failures
        and all(item["remoteIdentityVerified"] for item in public_entries)
    )
    report["generatedAt"] = _utc_now()
    report["status"] = (
        "PASS"
        if all_remote_verified
        else ("PARTIAL" if public_entries else "BLOCKED")
    )
    report["mutationPerformed"] = mutation_performed
    report["guardChecks"]["remoteIdentityVerified"] = all_remote_verified
    report["entries"] = public_entries
    report["issues"] = failures
    _validate_public_report(report)
    evidence_preserved = False
    if (
        all_remote_verified
        and not mutation_performed
        and report_path.is_file()
    ):
        try:
            existing_report = load_json(report_path)
            existing_issues = validate_with_schema(
                existing_report,
                ROOT
                / "schemas/transfer-publication-report.schema.json",
            )
            evidence_preserved = (
                not existing_issues
                and existing_report.get("status") == "PASS"
                and existing_report.get("manifestSha256")
                == report["manifestSha256"]
                and existing_report.get("evidencePackageSha256")
                == report["evidencePackageSha256"]
                and existing_report.get("inputHashes")
                == report["inputHashes"]
                and {
                    (
                        item.get("uploadName"),
                        item.get("sourceSha256"),
                    )
                    for item in existing_report.get("entries", [])
                }
                == {
                    (
                        item.get("uploadName"),
                        item.get("sourceSha256"),
                    )
                    for item in report["entries"]
                }
            )
        except (ArtSystemError, OSError, ValueError):
            evidence_preserved = False
    if not evidence_preserved:
        write_json(report_path, report)
    report["evidencePreserved"] = evidence_preserved
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Publish the nine immutable turret transfer candidates to the "
            "explicitly allowlisted Roblox staging creator."
        )
    )
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--confirm-publish", action="store_true")
    args = parser.parse_args()
    try:
        result = publish(
            args.manifest,
            args.registry,
            args.report,
            dry_run=args.dry_run,
            confirm_publish=args.confirm_publish,
        )
    except (ArtSystemError, OSError, ValueError) as error:
        print(f"[FAIL] {_safe_issue(error)}")
        return 1
    if result.get("dryRun"):
        print(
            "[PARTIAL] Staging transfer publication dry-run: "
            f"{result['assetCount']} immutable candidates planned; "
            "no mutation performed."
        )
        return 0
    if result["status"] == "PASS":
        creates = sum(
            item["action"] == "CREATE" for item in result["entries"]
        )
        reuses = sum(item["action"] == "REUSE" for item in result["entries"])
        print(
            "[PASS] Staging transfer publication: "
            f"9/9 remote identities verified ({creates} created, {reuses} reused). "
            "Raw asset and creator identifiers remain local."
            + (
                " Canonical evidence preserved byte-for-byte."
                if result.get("evidencePreserved")
                else ""
            )
        )
        return 0
    for issue in result["issues"]:
        print(f"[{result['status']}] {issue}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
