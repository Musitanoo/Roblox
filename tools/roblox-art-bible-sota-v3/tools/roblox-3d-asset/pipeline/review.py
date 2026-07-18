from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


ASSET_REVIEW_SCHEMA = (
    "https://roblox-top-1.local/schemas/roblox-3d-asset-review-1.0.0.json"
)
ASSET_REVIEW_SCHEMA_VERSION = "1.2.0"
EVIDENCE_DIGEST_SCHEME = "sha256-canonical-json-path-sha256-v1"
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalize_evidence_path(value: Any) -> tuple[str | None, str | None]:
    if not isinstance(value, str) or not value:
        return None, "is not a non-empty path"
    if "\\" in value:
        return None, "must use repository-portable forward slashes"
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return None, "must be relative to the asset root"
    path = PurePosixPath(value)
    if any(part in {".", ".."} for part in path.parts):
        return None, "must not contain '.' or '..' segments"
    normalized = path.as_posix()
    if normalized != value:
        return None, "must be a normalized repository-relative path"
    return normalized, None


def evidence_bindings(
    asset_root: Path,
    evidence: Any,
) -> tuple[list[dict[str, Any]], list[str]]:
    if not isinstance(evidence, list) or not evidence:
        return [], ["review evidence must be a non-empty list"]

    root = asset_root.resolve()
    bindings: list[dict[str, Any]] = []
    issues: list[str] = []
    seen: set[str] = set()
    for index, value in enumerate(evidence):
        relative, path_issue = _normalize_evidence_path(value)
        if path_issue is not None or relative is None:
            issues.append(f"review evidence[{index}] {path_issue}")
            continue
        if relative in seen:
            issues.append(f"review evidence[{index}] duplicates path: {relative}")
            continue
        seen.add(relative)
        candidate = root.joinpath(*PurePosixPath(relative).parts).resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            issues.append(f"review evidence[{index}] escapes the asset root")
            continue
        if not candidate.is_file():
            issues.append(f"review evidence[{index}] is missing: {relative}")
            continue
        bindings.append(
            {
                "path": relative,
                "bytes": candidate.stat().st_size,
                "sha256": _sha256_file(candidate),
            }
        )

    return sorted(bindings, key=lambda item: item["path"]), issues


def compute_evidence_digest(
    asset_root: Path,
    evidence: Any,
) -> tuple[dict[str, Any] | None, list[str]]:
    bindings, issues = evidence_bindings(asset_root, evidence)
    if issues:
        return None, issues
    encoded = json.dumps(
        bindings,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    digest = hashlib.sha256(
        EVIDENCE_DIGEST_SCHEME.encode("ascii") + b"\n" + encoded
    ).hexdigest()
    return {
        "scheme": EVIDENCE_DIGEST_SCHEME,
        "sha256": digest,
        "fileCount": len(bindings),
    }, []


def review_binding_issues(
    review: dict[str, Any],
    *,
    asset_root: Path,
    contract: dict[str, Any],
    contract_sha256: str | None,
) -> list[str]:
    issues: list[str] = []
    if review.get("$schema") != ASSET_REVIEW_SCHEMA:
        issues.append("review $schema is missing or unsupported")
    if review.get("schemaVersion") != ASSET_REVIEW_SCHEMA_VERSION:
        issues.append(
            f"review schemaVersion must be {ASSET_REVIEW_SCHEMA_VERSION}"
        )
    if review.get("assetKey") != contract.get("assetKey"):
        issues.append("review assetKey does not match the asset contract")
    if review.get("revision") != contract.get("revision"):
        issues.append("review revision does not match the asset contract")

    declared_contract_hash = review.get("contractSha256")
    if not isinstance(declared_contract_hash, str) or not SHA256.fullmatch(
        declared_contract_hash
    ):
        issues.append("review contractSha256 must be a lowercase SHA-256")
    elif contract_sha256 is None or declared_contract_hash != contract_sha256:
        issues.append(
            "review contractSha256 does not match the exact asset contract bytes"
        )

    declared_canon_hash = review.get("visualCanonSha256")
    if not isinstance(declared_canon_hash, str) or not SHA256.fullmatch(
        declared_canon_hash
    ):
        issues.append("review visualCanonSha256 must be a lowercase SHA-256")
    elif declared_canon_hash != contract.get("visualCanon", {}).get("sha256"):
        issues.append(
            "review visualCanonSha256 does not match the asset contract"
        )

    computed_digest, evidence_issues = compute_evidence_digest(
        asset_root,
        review.get("evidence"),
    )
    issues.extend(evidence_issues)
    declared_digest = review.get("evidenceDigest")
    if not isinstance(declared_digest, dict):
        issues.append("review evidenceDigest must be an object")
    elif computed_digest is not None:
        if declared_digest.get("scheme") != EVIDENCE_DIGEST_SCHEME:
            issues.append("review evidenceDigest.scheme is unsupported")
        declared_sha = declared_digest.get("sha256")
        if not isinstance(declared_sha, str) or not SHA256.fullmatch(
            declared_sha
        ):
            issues.append(
                "review evidenceDigest.sha256 must be a lowercase SHA-256"
            )
        elif declared_sha != computed_digest["sha256"]:
            issues.append("review evidenceDigest.sha256 drift")
        if declared_digest.get("fileCount") != computed_digest["fileCount"]:
            issues.append("review evidenceDigest.fileCount drift")

    return issues
