from __future__ import annotations

"""Create a pre-generation authority envelope bound to exact visual canons."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.art.build_visual_canons import ASSETS, check_all
from tools.art.common import ROOT, load_json, sha256_file, validate_with_schema, write_json

CALIBRATION_ASSETS = tuple(asset for asset in ASSETS if asset != "turret_fast_v1")
TERRITORIES = (
    "industrial-toy-defense",
    "salvaged-frontier",
    "clean-tactical-diorama",
)
SCHEMA = ROOT / "schemas/generation-authority.schema.json"


def prepare(
    territory_id: str,
    scope: str,
    production: bool,
    output: Path,
) -> dict[str, Any]:
    drift = check_all(require_locked=False)
    if drift:
        raise RuntimeError("visual canon drift: " + "; ".join(drift))
    catalog_path = ROOT / "art/canonical-visuals/catalog.json"
    catalog = load_json(catalog_path)
    assets = CALIBRATION_ASSETS if scope == "calibration" else ("turret_fast_v1",)
    entries = [
        entry
        for entry in catalog["entries"]
        if entry["territoryId"] == territory_id and entry["assetId"] in assets
    ]
    if len(entries) != len(assets):
        raise RuntimeError(
            f"canon coverage mismatch for {territory_id}/{scope}: "
            f"{len(entries)} != {len(assets)}"
        )
    compiler_relative = (
        "tools/blender/build_art_direction.py"
        if scope == "calibration"
        else "tools/blender/build_transfer_asset.py"
    )
    blocking: list[str] = []
    if production:
        for entry in entries:
            if not entry["productionEligible"]:
                blocking.append(
                    f"{entry['canonId']} is not LOCKED + COMPLETE + APPROVED"
                )
    value = {
        "$schema": "https://roblox-top1.local/schemas/generation-authority.schema.json",
        "schemaVersion": "1.0.0",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "BLOCKED" if blocking else "PASS",
        "mode": "PRODUCTION" if production else "EXPLORATION",
        "scope": scope,
        "territoryId": territory_id,
        "catalogPath": "art/canonical-visuals/catalog.json",
        "catalogSha256": sha256_file(catalog_path),
        "compilerPath": compiler_relative,
        "compilerSha256": sha256_file(ROOT / compiler_relative),
        "canonBindings": [
            {
                "canonId": entry["canonId"],
                "assetId": entry["assetId"],
                "path": entry["path"],
                "sha256": entry["sha256"],
                "status": entry["status"],
                "visualPacketStatus": entry["visualPacketStatus"],
                "productionEligible": entry["productionEligible"],
            }
            for entry in entries
        ],
        "blockingReasons": blocking,
    }
    errors = validate_with_schema(value, SCHEMA)
    if errors:
        raise RuntimeError("generation authority invalid: " + "; ".join(errors))
    write_json(output, value)
    return value


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bind a generation run to exact visual canon hashes."
    )
    parser.add_argument("--territory", required=True, choices=TERRITORIES)
    parser.add_argument(
        "--scope", required=True, choices=("calibration", "transfer")
    )
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or (
        ROOT
        / "build/canon-authority"
        / f"{args.territory}__{args.scope}.json"
    )
    result = prepare(
        args.territory, args.scope, args.production, output.resolve()
    )
    print(
        f"[{result['status']}] {result['mode']} {result['scope']} "
        f"bound to {len(result['canonBindings'])} canon(s): {output}"
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
