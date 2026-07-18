from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.art.common import ROOT, sha256_file


def verify_artifacts(records: list[dict[str, Any]], *, required_prefix: str) -> list[str]:
    """Verify evidence paths, byte sizes and SHA-256 digests inside the repository."""
    issues: list[str] = []
    seen_paths: set[str] = set()
    repo_root = ROOT.resolve()
    for index, record in enumerate(records):
        label = f"artifacts[{index}]"
        relative = record.get("path")
        if not isinstance(relative, str):
            issues.append(f"{label}: path is not a string")
            continue
        if not relative.startswith(required_prefix):
            issues.append(f"{label}: path must begin with {required_prefix}")
        if relative in seen_paths:
            issues.append(f"{label}: duplicate path {relative}")
        seen_paths.add(relative)
        path = (ROOT / relative).resolve()
        try:
            path.relative_to(repo_root)
        except ValueError:
            issues.append(f"{label}: path escapes repository root")
            continue
        if not path.is_file():
            issues.append(f"{label}: file does not exist: {relative}")
            continue
        actual_size = path.stat().st_size
        if actual_size != record.get("bytes"):
            issues.append(
                f"{label}: byte-size mismatch for {relative}; "
                f"expected {record.get('bytes')}, observed {actual_size}"
            )
        actual_hash = sha256_file(path)
        if actual_hash != record.get("sha256"):
            issues.append(f"{label}: SHA-256 mismatch for {relative}")
    return issues


def metric_order_issues(label: str, metrics: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    frame = metrics["frameTimeMs"]
    if not (frame["median"] <= frame["p95"] <= frame["p99"] <= frame["max"]):
        issues.append(f"{label}: frame-time order must satisfy median <= p95 <= p99 <= max")
    memory = metrics["memoryMb"]
    if not (memory["median"] <= memory["p95"] <= memory["max"]):
        issues.append(f"{label}: memory order must satisfy median <= p95 <= max")
    fps = metrics["fps"]
    if fps["minimum"] > fps["median"]:
        issues.append(f"{label}: minimum FPS cannot exceed median FPS")
    return issues
