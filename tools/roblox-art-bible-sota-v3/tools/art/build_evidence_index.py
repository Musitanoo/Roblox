from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from tools.art.common import ROOT, load_json, sha256_file, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or refresh a strict evidence-index template.")
    parser.add_argument("--territory", required=True, choices=["industrial-toy-defense", "salvaged-frontier", "clean-tactical-diorama"])
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/evidence-index.json")
    args = parser.parse_args()
    art = load_json(ROOT / "art/art-direction.json")
    items = []
    for gate_id in art["gates"]["requiredHardGateIds"]:
        items.append({"gateId": gate_id, "status": "UNKNOWN", "path": None, "sha256": None, "observedAt": None, "notes": "Evidence not attached."})
    value = {
        "$schema": "https://roblox-top1.local/schemas/evidence-index.schema.json",
        "schemaVersion": "2.0.0",
        "status": "INCOMPLETE",
        "selectedTerritory": args.territory,
        "items": items,
    }
    write_json(args.output, value)
    print(f"[PASS] Evidence index template created: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
