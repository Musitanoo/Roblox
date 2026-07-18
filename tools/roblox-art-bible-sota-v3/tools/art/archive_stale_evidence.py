from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, sha256_file


CURRENT_FILES = (
    ROOT / "evidence/blender/blender-verification-report.json",
    ROOT / "evidence/blender/smoke-evidence.json",
    ROOT / "evidence/blender/full-evidence.json",
    ROOT / "evidence/blender/visual-quality-report.json",
)


def _generator_hashes(value: Any) -> set[str]:
    hashes: set[str] = set()
    if isinstance(value, dict):
        inputs = value.get("inputHashes")
        if isinstance(inputs, dict) and isinstance(inputs.get("generator"), str):
            hashes.add(inputs["generator"])
        for child in value.values():
            hashes.update(_generator_hashes(child))
    elif isinstance(value, list):
        for child in value:
            hashes.update(_generator_hashes(child))
    return hashes


def archive_stale() -> list[str]:
    current = sha256_file(ROOT / "tools/blender/build_art_direction.py")
    archive_dir = ROOT / "evidence/blender/archive"
    archived: list[str] = []
    for path in CURRENT_FILES:
        if not path.is_file():
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            observed = _generator_hashes(value)
        except (OSError, json.JSONDecodeError):
            observed = set()
        if observed == {current}:
            continue
        label = sorted(observed)[0][:12] if observed else "unbound"
        archive_dir.mkdir(parents=True, exist_ok=True)
        destination = archive_dir / f"{path.stem}__generator-{label}.json"
        if destination.exists():
            if sha256_file(destination) == sha256_file(path):
                path.unlink()
            else:
                destination = archive_dir / f"{path.stem}__generator-{label}__{sha256_file(path)[:12]}.json"
                shutil.move(path, destination)
        else:
            shutil.move(path, destination)
        archived.append(destination.relative_to(ROOT).as_posix())
    return archived


def main() -> int:
    archived = archive_stale()
    if archived:
        for path in archived:
            print(f"[ARCHIVE] {path}")
    else:
        print("[PASS] No stale Blender evidence required archival.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
