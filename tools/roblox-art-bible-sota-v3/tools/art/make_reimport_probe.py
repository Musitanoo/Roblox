from __future__ import annotations

import argparse
import json
import shutil
import struct
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, sha256_file


SOURCE_ASSET = ROOT / "build/industrial-toy-defense/exports/barricade/barricade__intact.glb"
PROBE_DIR = ROOT / "evidence/studio/reimport-probe"
ROLE_NODE = "ROLE_interaction"
VERTICAL_SHIFT_STUDS = 0.25


def _read_glb(path: Path) -> tuple[dict[str, Any], bytes]:
    data = path.read_bytes()
    if len(data) < 28 or data[:4] != b"glTF":
        raise ValueError(f"Invalid GLB: {path}")
    _, version, total_length = struct.unpack_from("<4sII", data, 0)
    if version != 2 or total_length != len(data):
        raise ValueError(f"Unsupported or truncated GLB: {path}")
    json_length, json_type = struct.unpack_from("<II", data, 12)
    if json_type != 0x4E4F534A:
        raise ValueError(f"GLB JSON chunk missing: {path}")
    document = json.loads(data[20 : 20 + json_length].decode("utf-8"))
    binary_header = 20 + json_length
    binary_length, binary_type = struct.unpack_from("<II", data, binary_header)
    if binary_type != 0x004E4942:
        raise ValueError(f"GLB BIN chunk missing: {path}")
    binary = data[binary_header + 8 : binary_header + 8 + binary_length]
    return document, binary


def _write_glb(path: Path, document: dict[str, Any], binary: bytes) -> None:
    json_bytes = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    json_bytes += b" " * ((-len(json_bytes)) % 4)
    binary += b"\x00" * ((-len(binary)) % 4)
    total = 12 + 8 + len(json_bytes) + 8 + len(binary)
    payload = (
        struct.pack("<4sII", b"glTF", 2, total)
        + struct.pack("<II", len(json_bytes), 0x4E4F534A)
        + json_bytes
        + struct.pack("<II", len(binary), 0x004E4942)
        + binary
    )
    path.write_bytes(payload)


def prepare() -> dict[str, Any]:
    if not SOURCE_ASSET.is_file():
        raise FileNotFoundError(f"Current production GLB is missing: {SOURCE_ASSET}")
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    v1 = PROBE_DIR / "v1.glb"
    v2 = PROBE_DIR / "v2.glb"
    source = PROBE_DIR / "source.glb"
    shutil.copyfile(SOURCE_ASSET, v1)
    document, binary = _read_glb(v1)
    matches = [node for node in document.get("nodes", []) if node.get("name") == ROLE_NODE]
    if len(matches) != 1:
        raise ValueError(f"Expected one {ROLE_NODE} node, found {len(matches)}")
    translation = list(matches[0].get("translation", [0.0, 0.0, 0.0]))
    translation[1] = round(float(translation[1]) + VERTICAL_SHIFT_STUDS, 6)
    matches[0]["translation"] = translation
    _write_glb(v2, document, binary)
    shutil.copyfile(v1, source)
    manifest = {
        "schemaVersion": "1.0.0",
        "generatedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "sourceAsset": SOURCE_ASSET.relative_to(ROOT).as_posix(),
        "roleNode": ROLE_NODE,
        "verticalShiftStuds": VERTICAL_SHIFT_STUDS,
        "versions": {
            "v1": {"path": v1.relative_to(ROOT).as_posix(), "sha256": sha256_file(v1)},
            "v2": {"path": v2.relative_to(ROOT).as_posix(), "sha256": sha256_file(v2)},
        },
        "active": "v1",
        "source": {"path": source.relative_to(ROOT).as_posix(), "sha256": sha256_file(source)},
    }
    (PROBE_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def activate(version: str) -> dict[str, Any]:
    manifest_path = PROBE_DIR / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("Prepare the reimport probe before activating a version")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    selected = ROOT / manifest["versions"][version]["path"]
    source = ROOT / manifest["source"]["path"]
    if sha256_file(selected) != manifest["versions"][version]["sha256"]:
        raise ValueError(f"Probe {version} hash drift")
    shutil.copyfile(selected, source)
    manifest["active"] = version
    manifest["source"]["sha256"] = sha256_file(source)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and switch the isolated Studio reimport probe.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("prepare")
    activate_parser = subparsers.add_parser("activate")
    activate_parser.add_argument("version", choices=["v1", "v2"])
    args = parser.parse_args()
    result = prepare() if args.command == "prepare" else activate(args.version)
    print(json.dumps({"status": "PASS", "active": result["active"], "manifest": str(PROBE_DIR / "manifest.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
