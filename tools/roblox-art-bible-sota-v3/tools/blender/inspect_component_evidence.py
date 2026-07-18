from __future__ import annotations

"""Read stable semantic Blender object metadata without changing the compiler."""

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy


SCHEMA = "https://roblox-top1.local/schemas/component-evidence-report.schema.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def arguments() -> argparse.Namespace:
    raw = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(raw)


def main() -> int:
    args = arguments()
    build_report_path = args.build_report.resolve()
    build = json.loads(build_report_path.read_text(encoding="utf-8"))
    blend_path = (build_report_path.parent / build["blendFile"]["path"]).resolve()
    issues: list[str] = []
    if sha256_file(blend_path) != build["blendFile"]["sha256"]:
        issues.append("blend SHA-256 differs from the build report")
    bpy.ops.wm.open_mainfile(filepath=str(blend_path), load_ui=False)

    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for obj in bpy.data.objects:
        if obj.type != "MESH":
            continue
        asset_id = obj.get("art_asset_id")
        state_id = obj.get("art_state")
        material_role = obj.get("art_role")
        detail_band = obj.get("art_detail_band")
        if not all(
            isinstance(value, str) and value
            for value in (asset_id, state_id, material_role, detail_band)
        ):
            continue
        grouped.setdefault((asset_id, state_id), []).append(
            {
                "name": obj.name,
                "materialRole": material_role,
                "detailBand": detail_band,
            }
        )

    expected_pairs = {
        (row["assetId"], row["stateId"]) for row in build["assets"]
    }
    observed_pairs = set(grouped)
    if observed_pairs != expected_pairs:
        issues.append(
            f"semantic object coverage differs: observed={sorted(observed_pairs)} expected={sorted(expected_pairs)}"
        )
    rows = [
        {
            "assetId": asset_id,
            "stateId": state_id,
            "semanticObjects": sorted(
                objects, key=lambda item: (item["name"], item["materialRole"])
            ),
        }
        for (asset_id, state_id), objects in sorted(grouped.items())
    ]
    report = {
        "$schema": SCHEMA,
        "schemaVersion": "1.0.0",
        "generatedAt": datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "status": "PASS" if not issues else "FAIL",
        "territoryId": build["territoryId"],
        "source": {
            "blendPath": str(blend_path),
            "blendSha256": sha256_file(blend_path),
            "buildReportPath": str(build_report_path),
            "buildReportSha256": sha256_file(build_report_path),
            "inspectorSha256": sha256_file(Path(__file__).resolve()),
        },
        "assets": rows,
        "issues": issues,
    }
    write_json(args.output.resolve(), report)
    print(
        json.dumps(
            {
                "status": report["status"],
                "territoryId": report["territoryId"],
                "rowCount": len(rows),
                "output": str(args.output.resolve()),
            },
            indent=2,
        )
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
