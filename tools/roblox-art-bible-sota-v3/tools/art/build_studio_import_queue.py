from __future__ import annotations

import json
import shutil
import struct
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, load_json, sha256_file
from tools.art.validate_build_report import validate_report


TERRITORIES = (
    "industrial-toy-defense",
    "salvaged-frontier",
    "clean-tactical-diorama",
)
OUTPUT = ROOT / "build/studio-import"


def read_glb_scene_name(path: Path) -> str:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        raise ValueError(f"Not a GLB file: {path}")
    version, total_length = struct.unpack_from("<II", data, 4)
    if version != 2 or total_length != len(data):
        raise ValueError(f"Invalid GLB header: {path}")
    json_length, json_type = struct.unpack_from("<II", data, 12)
    if json_type != 0x4E4F534A or 20 + json_length > len(data):
        raise ValueError(f"Invalid GLB JSON chunk: {path}")
    document = json.loads(data[20 : 20 + json_length].decode("utf-8").rstrip(" \t\r\n\x00"))
    scenes = document.get("scenes", [])
    scene_index = document.get("scene", 0)
    if not isinstance(scene_index, int) or scene_index < 0 or scene_index >= len(scenes):
        raise ValueError(f"GLB has no valid default scene: {path}")
    scene_name = scenes[scene_index].get("name")
    if not isinstance(scene_name, str) or not scene_name:
        raise ValueError(f"GLB default scene has no stable name: {path}")
    return scene_name


def build(output: Path = OUTPUT) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    for territory_id in TERRITORIES:
        report_path = ROOT / "build" / territory_id / "build-report.json"
        issues = validate_report(report_path, require_complete=True)
        if issues:
            raise ValueError(f"{territory_id} is not current FULL_COMPLETE evidence: {issues}")
        report = load_json(report_path)
        reports.append(report)

    if output.exists():
        resolved = output.resolve()
        resolved.relative_to((ROOT / "build").resolve())
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    for report in reports:
        territory_id = report["territoryId"]
        report_dir = ROOT / "build" / territory_id
        for item in report["exports"]:
            source = report_dir / item["path"]
            filename = f"{territory_id}__{item['assetId']}__{item['stateId']}.glb"
            upload_name = filename.removesuffix(".glb")
            source_scene_name = read_glb_scene_name(source)
            if source_scene_name != upload_name:
                raise ValueError(
                    f"Studio import name mismatch: {filename} embeds {source_scene_name!r}"
                )
            destination = output / filename
            shutil.copyfile(source, destination)
            observed_hash = sha256_file(destination)
            if observed_hash != item["sha256"]:
                raise ValueError(f"Studio queue copy hash mismatch: {filename}")
            entries.append(
                {
                    "territoryId": territory_id,
                    "assetId": item["assetId"],
                    "stateId": item["stateId"],
                    "uploadName": upload_name,
                    "path": destination.relative_to(ROOT).as_posix(),
                    "sourcePath": (report_dir / item["path"]).relative_to(ROOT).as_posix(),
                    "sha256": observed_hash,
                    "bytes": destination.stat().st_size,
                    "meshCount": item["meshCount"],
                    "materialRoles": item["materialRoles"],
                }
            )

    entries.sort(key=lambda item: (item["territoryId"], item["assetId"], item["stateId"]))
    if len(entries) != 39 or len({item["uploadName"] for item in entries}) != 39:
        raise ValueError("Studio import queue must contain exactly 39 uniquely named GLBs")
    generator_hashes = {report["inputHashes"]["generator"] for report in reports}
    materials_hashes = {report["inputHashes"]["materials"] for report in reports}
    if len(generator_hashes) != 1 or len(materials_hashes) != 1:
        raise ValueError("Studio queue reports disagree on generator or material rules")
    manifest = {
        "schemaVersion": "1.0.0",
        "status": "PASS",
        "generatedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "assetCount": len(entries),
        "generatorSha256": next(iter(generator_hashes)),
        "materialRulesSha256": next(iter(materials_hashes)),
        "entries": entries,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    manifest = build()
    print(
        json.dumps(
            {"status": manifest["status"], "assetCount": manifest["assetCount"], "output": str(OUTPUT)},
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
