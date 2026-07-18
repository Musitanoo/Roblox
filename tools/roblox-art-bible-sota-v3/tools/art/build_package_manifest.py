from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, canonical_json_bytes, load_json, sha256_bytes, sha256_file, write_json

EXCLUDED_PARTS = {".pytest_cache", "__pycache__", ".git", ".venv"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".zip"}
EXCLUDED_FILES = {"PACKAGE_MANIFEST.json"}
VOLATILE_EVIDENCE_FILES = {
    "evidence/static-validation-report.json",
    "evidence/static-verification-report.json",
}
LOCAL_EVIDENCE_ROOTS = {
    "evidence/human",
}


def included_files(root: Path = ROOT) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] == "build":
            continue
        if any(
            relative.as_posix() == local_root
            or relative.as_posix().startswith(local_root + "/")
            for local_root in LOCAL_EVIDENCE_ROOTS
        ) and relative.name != ".gitkeep":
            continue
        if relative.as_posix() in VOLATILE_EVIDENCE_FILES:
            continue
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.suffix in EXCLUDED_SUFFIXES or path.name in EXCLUDED_FILES:
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def build_value(root: Path = ROOT) -> dict[str, Any]:
    entries = [
        {
            "path": path.relative_to(root).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in included_files(root)
    ]
    status = load_json(root / "STATUS.json")
    return {
        "schemaVersion": "1.0.0",
        "artifact": "roblox-art-bible-sota-v3",
        "artifactVersion": status["artifactVersion"],
        "generatedAt": status["generatedAt"],
        "fileCount": len(entries),
        "treeSha256": sha256_bytes(canonical_json_bytes(entries)),
        "files": entries,
        "selfExcluded": "PACKAGE_MANIFEST.json is intentionally excluded from its own digest.",
    }


def verify_manifest(path: Path, root: Path = ROOT) -> list[str]:
    manifest = load_json(path)
    expected = build_value(root)
    issues: list[str] = []
    if manifest.get("files") != expected["files"]:
        issues.append("Package file list, sizes, or SHA-256 digests differ from the manifest")
    if manifest.get("fileCount") != expected["fileCount"]:
        issues.append("Package fileCount differs from the current tree")
    if manifest.get("treeSha256") != expected["treeSha256"]:
        issues.append("Package treeSha256 differs from the current tree")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or verify the release package manifest.")
    parser.add_argument("--output", type=Path, default=ROOT / "PACKAGE_MANIFEST.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        issues = verify_manifest(args.output)
        if issues:
            for issue in issues:
                print(f"[FAIL] {issue}")
            return 1
        print(f"[PASS] Package manifest matches {len(included_files())} files.")
        return 0
    value = build_value()
    write_json(args.output, value)
    print(f"[PASS] Package manifest written for {value['fileCount']} files: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
