from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.state_variants import (
    StateVariantError,
    available_state_ids,
    resolve_state_variant,
)


REPO = ROOT.parents[1]
EXAMPLE = REPO / "assets-3d" / "defense-barricade-small" / "asset.json"


class StateVariantTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def test_default_state_is_intact_and_does_not_mutate_source(self) -> None:
        resolved = resolve_state_variant(self.contract)
        self.assertEqual("intact", resolved["_compiledStateId"])
        self.assertEqual(
            ["intact", "damaged", "critical"],
            available_state_ids(self.contract),
        )
        self.assertNotIn("_compiledStateId", self.contract)

    def test_damaged_state_changes_transform_and_material_only(self) -> None:
        resolved = resolve_state_variant(self.contract, "damaged")
        source_parts = {
            part["name"]: part for part in self.contract["geometry"]["parts"]
        }
        resolved_parts = {
            part["name"]: part for part in resolved["geometry"]["parts"]
        }
        self.assertEqual(set(source_parts), set(resolved_parts))
        self.assertEqual(
            len(source_parts),
            len(resolved_parts),
        )
        self.assertNotEqual(
            source_parts["DEF_BarricadeSmall_PanelL"]["position"],
            resolved_parts["DEF_BarricadeSmall_PanelL"]["position"],
        )
        self.assertEqual(
            "WarningGold",
            resolved_parts["DEF_BarricadeSmall_Light"]["material"],
        )
        for name, source in source_parts.items():
            self.assertEqual(source["type"], resolved_parts[name]["type"])
            self.assertEqual(source["size"], resolved_parts[name]["size"])

    def test_unknown_state_fails_closed(self) -> None:
        with self.assertRaises(StateVariantError):
            resolve_state_variant(self.contract, "invented")


if __name__ == "__main__":
    unittest.main()
