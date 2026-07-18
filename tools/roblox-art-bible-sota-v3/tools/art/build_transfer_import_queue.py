from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import Any

from tools.art.build_studio_import_queue import read_glb_scene_name
from tools.art.common import (
    ROOT,
    load_json,
    sha256_file,
    validate_with_schema,
    write_json,
)
from tools.art.validate_transfer_report import validate_report

ASSET_ID = "turret_fast_v1"
OUTPUT = ROOT / "build/studio-import-transfer"
PORTABLE_MANIFEST = (
    ROOT
    / "evidence/transfer/turret-fast-v1/studio-import-manifest.json"
)
SCHEMA = (
    "https://roblox-top1.local/schemas/transfer-import-queue.schema.json"
)


def build(output: Path = OUTPUT) -> dict[str, Any]:
    report_path = ROOT / "evidence/transfer/turret-fast-v1/report.json"
    validation = validate_report(report_path)
    if validation["status"] != "PASS":
        raise ValueError(
            "portable transfer report is not current: "
            + "; ".join(validation["issues"])
        )
    report = load_json(report_path)
    if output.exists():
        output.resolve().relative_to((ROOT / "build").resolve())
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    entries: list[dict[str, Any]] = []
    for territory in report["territories"]:
        territory_id = territory["territoryId"]
        exports = [
            item
            for item in territory["portableArtifacts"]
            if item["kind"] == "GLB"
        ]
        for item in exports:
            state_id = item["stateId"]
            source = ROOT / item["path"]
            upload_name = f"{territory_id}__{ASSET_ID}__{state_id}"
            if read_glb_scene_name(source) != upload_name:
                raise ValueError(
                    f"{item['path']}: embedded scene name is not {upload_name}"
                )
            destination = output / f"{upload_name}.glb"
            shutil.copyfile(source, destination)
            observed = sha256_file(destination)
            if observed != item["sha256"]:
                raise ValueError(
                    f"transfer Studio queue copy hash mismatch: {upload_name}"
                )
            entries.append(
                {
                    "territoryId": territory_id,
                    "stateId": state_id,
                    "uploadName": upload_name,
                    "path": destination.relative_to(ROOT).as_posix(),
                    "sourcePath": item["path"],
                    "sha256": observed,
                    "bytes": destination.stat().st_size,
                }
            )
    entries.sort(key=lambda item: (item["territoryId"], item["stateId"]))
    if len(entries) != 9 or len({item["uploadName"] for item in entries}) != 9:
        raise ValueError(
            "transfer Studio queue must contain exactly nine unique GLBs"
        )
    manifest = {
        "$schema": SCHEMA,
        "schemaVersion": "1.0.0",
        "status": "PASS",
        "generatedAt": report["generatedAt"],
        "assetId": ASSET_ID,
        "assetCount": 9,
        "evidencePackageSha256": report["evidencePackageSha256"],
        "transferReportSha256": sha256_file(report_path),
        "entries": entries,
    }
    schema_issues = validate_with_schema(
        manifest,
        ROOT / "schemas/transfer-import-queue.schema.json",
    )
    if schema_issues:
        raise ValueError(
            "generated transfer import manifest is invalid: "
            + "; ".join(schema_issues)
        )
    write_json(output / "manifest.json", manifest)
    write_json(PORTABLE_MANIFEST, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build a flat nine-GLB Studio import queue from portable transfer evidence."
    )
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    manifest = build(args.output.resolve())
    print(
        f"[PASS] Transfer Studio import queue: {manifest['assetCount']} GLBs | "
        f"{args.output.resolve()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
