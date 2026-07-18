from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, load_json, rel, sha256_file, write_json


PROFILES = (
    "Lighting_Gameplay_Default",
    "Lighting_HighContrast",
    "Lighting_Adverse_Night",
    "Lighting_Neutral_QA",
)


def bind(report_path: Path, captures_dir: Path | None = None) -> dict[str, Any]:
    report_path = report_path.resolve()
    report = load_json(report_path)
    territory_id = report["territoryId"]
    captures_dir = (captures_dir or (ROOT / "evidence/studio/captures")).resolve()
    records: list[dict[str, Any]] = []
    for profile_id in PROFILES:
        capture = captures_dir / f"{territory_id}__{profile_id}.jpg"
        if not capture.is_file() or capture.stat().st_size == 0:
            raise ValueError(f"Missing non-empty Studio capture: {capture}")
        capture.resolve().relative_to(ROOT.resolve())
        records.append(
            {
                "kind": "screenshot",
                "path": rel(capture),
                "bytes": capture.stat().st_size,
                "sha256": sha256_file(capture),
            }
        )
    retained = [item for item in report["artifacts"] if item["kind"] != "screenshot"]
    report["artifacts"] = sorted(retained + records, key=lambda item: (item["kind"], item["path"]))
    write_json(report_path, report)
    return {"status": "PASS", "territoryId": territory_id, "captureCount": len(records)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Bind hash-verified Studio captures to a report.")
    parser.add_argument("report", type=Path)
    parser.add_argument("--captures-dir", type=Path)
    args = parser.parse_args()
    result = bind(args.report, args.captures_dir)
    print(
        f"[PASS] Bound {result['captureCount']} Studio captures: "
        f"{result['territoryId']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
