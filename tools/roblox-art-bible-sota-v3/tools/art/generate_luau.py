from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, canonical_json_bytes, load_json, sha256_bytes

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_LUAU_RESERVED = {
    "and", "break", "continue", "do", "else", "elseif", "end", "export",
    "false", "for", "function", "if", "in", "local", "nil", "not", "or",
    "repeat", "return", "then", "true", "type", "until", "while",
}


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def to_luau(value: Any, level: int = 0) -> str:
    indent = "\t" * level
    child = "\t" * (level + 1)
    if value is None:
        return "nil"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return f'"{_escape(value)}"'
    if isinstance(value, list):
        if not value:
            return "{}"
        lines = ["{"]
        for item in value:
            lines.append(f"{child}{to_luau(item, level + 1)},")
        lines.append(f"{indent}}}")
        return "\n".join(lines)
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = ["{"]
        for key in sorted(value):
            rendered_key = key if _IDENTIFIER.match(key) and key not in _LUAU_RESERVED else f'["{_escape(key)}"]'
            lines.append(f"{child}{rendered_key} = {to_luau(value[key], level + 1)},")
        lines.append(f"{indent}}}")
        return "\n".join(lines)
    raise TypeError(f"Unsupported value for Luau generation: {type(value)!r}")


def sources() -> dict[str, dict[str, Any]]:
    material_rules = load_json(ROOT / "art/materials/material-rules.json")
    territory_styles = {
        "schemaVersion": "1.0.0",
        "roleProfiles": material_rules["semanticRoleProfiles"],
        "surfaceProfiles": {
            surface_id: {"studioMaterial": profile["studioMaterial"]}
            for surface_id, profile in material_rules["materials"].items()
        },
        "territories": {
            territory_id: {
                "palette": load_json(ROOT / f"art/territories/{territory_id}.json")["blockoutPalette"],
                "surfaceAssignments": load_json(ROOT / f"art/territories/{territory_id}.json")["surfaceAssignments"],
            }
            for territory_id in (
                "industrial-toy-defense",
                "salvaged-frontier",
                "clean-tactical-diorama",
            )
        },
    }
    return {
        "ArtDirectionConfig.luau": {
            "artDirection": load_json(ROOT / "art/art-direction.json"),
            "calibrationKit": load_json(ROOT / "art/calibration/calibration-kit.json"),
            "cameraRig": load_json(ROOT / "art/calibration/camera-rig.json"),
            "renderMatrix": load_json(ROOT / "art/calibration/render-matrix.json"),
            "semanticPalette": load_json(ROOT / "art/palettes/semantic-palette.json"),
            "visualRubric": load_json(ROOT / "art/qa/visual-rubric.json"),
        },
        "LightingProfiles.luau": load_json(ROOT / "art/lighting/lighting-profiles.json"),
        "TerritoryStyles.luau": territory_styles,
    }


def render(name: str, data: dict[str, Any]) -> str:
    digest = sha256_bytes(canonical_json_bytes(data))
    return (
        "--!strict\n"
        "-- AUTO-GENERATED. DO NOT EDIT.\n"
        f"-- Source digest: {digest}\n\n"
        f"local data = {to_luau(data)}\n"
        f'data.sourceDigest = "{digest}"\n\n'
        "return table.freeze(data)\n"
    )


def generate(check: bool) -> list[str]:
    out_dir = ROOT / "studio/generated"
    issues: list[str] = []
    for name, data in sources().items():
        expected = render(name, data)
        path = out_dir / name
        if check:
            if not path.exists():
                issues.append(f"Missing generated file: {path.relative_to(ROOT)}")
            elif path.read_text(encoding="utf-8") != expected:
                issues.append(f"Generated file drift: {path.relative_to(ROOT)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8", newline="\n")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Studio Luau modules from canonical JSON.")
    parser.add_argument("--check", action="store_true", help="Fail if generated files are missing or stale.")
    args = parser.parse_args()
    issues = generate(args.check)
    if issues:
        for issue in issues:
            print(f"[FAIL] {issue}")
        return 1
    print("[PASS] Studio Luau configuration is synchronized." if args.check else "[PASS] Studio Luau configuration generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
