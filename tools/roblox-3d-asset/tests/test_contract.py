from __future__ import annotations

import copy
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.contract import (
    resolve_visual_canon_path,
    validate_contract,
    validate_contract_data,
)


REPO = ROOT.parents[1]
EXAMPLE = REPO / "assets-3d" / "defense-barricade-small" / "asset.json"
SCHEMA = ROOT / "schemas" / "asset.schema.json"


class ContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def _validate_in_temporary_repo(
        self,
        data: dict[str, object],
    ) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            contract_path = repo / "assets-3d" / "sample" / "asset.json"
            contract_path.parent.mkdir(parents=True)
            canon_source = resolve_visual_canon_path(
                EXAMPLE,
                self.data["visualCanon"]["path"],
            )
            canon_relative = PurePosixPath(
                str(data["visualCanon"]["path"])
            )
            canon_target = repo.joinpath(*canon_relative.parts)
            canon_target.parent.mkdir(parents=True)
            canon_target.write_bytes(canon_source.read_bytes())
            contract_path.write_text(
                json.dumps(data, indent=2) + "\n",
                encoding="utf-8",
            )
            return validate_contract(contract_path)

    def test_vertical_slice_contract_passes(self) -> None:
        self.assertEqual([], validate_contract_data(self.data))

    def test_rejects_non_staging_publication(self) -> None:
        invalid = copy.deepcopy(self.data)
        invalid["publication"]["environment"] = "production"
        self.assertIn("publication.environment must be staging", validate_contract_data(invalid))

    def test_rejects_triangle_budget_above_roblox_limit(self) -> None:
        invalid = copy.deepcopy(self.data)
        invalid["triangleBudget"]["absoluteMaximum"] = 20_001
        self.assertTrue(any("20000" in error for error in validate_contract_data(invalid)))

    def test_accepts_bounded_cylinder_and_emission(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["materials"][0]["emissionColor"] = "#5FE0C1"
        candidate["materials"][0]["emissionStrength"] = 2.5
        candidate["geometry"]["parts"][0].update(
            {
                "type": "cylinder",
                "axis": "Z",
                "segments": 12,
            }
        )
        self.assertEqual([], validate_contract_data(candidate))

    def test_accepts_chamfered_box_and_rejects_oversized_chamfer(self) -> None:
        candidate = copy.deepcopy(self.data)
        candidate["geometry"]["parts"][0].update(
            {
                "type": "chamfered_box",
                "chamfer": 0.1,
            }
        )
        self.assertEqual([], validate_contract_data(candidate))

        candidate["geometry"]["parts"][0]["chamfer"] = 1.0
        self.assertTrue(
            any(
                ".chamfer must be finite, > 0 and less than half the X/Y size"
                in error
                for error in validate_contract_data(candidate)
            )
        )

    def test_rejects_oversized_or_non_finite_bevel(self) -> None:
        oversized = copy.deepcopy(self.data)
        oversized["geometry"]["parts"][0]["bevel"] = 0.11
        self.assertTrue(
            any(
                ".bevel must be less than half the smallest size" in error
                for error in validate_contract_data(oversized)
            )
        )

        non_finite = copy.deepcopy(self.data)
        non_finite["geometry"]["parts"][0]["bevel"] = float("inf")
        self.assertTrue(
            any(
                ".bevel must be finite and >= 0" in error
                for error in validate_contract_data(non_finite)
            )
        )

    def test_rejects_unbounded_cylinder_configuration(self) -> None:
        invalid = copy.deepcopy(self.data)
        invalid["geometry"]["parts"][0].update(
            {
                "type": "cylinder",
                "axis": "Q",
                "segments": 64,
            }
        )
        errors = validate_contract_data(invalid)
        self.assertTrue(any(".axis must be X, Y or Z" in error for error in errors))
        self.assertTrue(
            any(".segments must be an integer between 8 and 32" in error for error in errors)
        )

    def test_rejects_invalid_emission_strength(self) -> None:
        invalid = copy.deepcopy(self.data)
        invalid["materials"][0]["emissionStrength"] = 21
        self.assertTrue(
            any(
                ".emissionStrength must be finite and between 0 and 20" in error
                for error in validate_contract_data(invalid)
            )
        )

    def test_rejects_state_override_for_unknown_component(self) -> None:
        invalid = copy.deepcopy(self.data)
        invalid["states"]["variants"][1]["partOverrides"][0]["name"] = (
            "DEF_InventedComponent"
        )
        self.assertTrue(
            any(
                ".name must reference a declared part" in error
                for error in validate_contract_data(invalid)
            )
        )

    def test_rejects_state_topology_mutation(self) -> None:
        invalid = copy.deepcopy(self.data)
        invalid["states"]["variants"][1]["partOverrides"][0]["size"] = [
            1.0,
            1.0,
            1.0,
        ]
        self.assertTrue(
            any(
                "contains unsupported keys" in error
                for error in validate_contract_data(invalid)
            )
        )

    def test_rejects_missing_visual_canon(self) -> None:
        invalid = copy.deepcopy(self.data)
        del invalid["visualCanon"]
        self.assertIn(
            "visualCanon must be an object",
            validate_contract_data(invalid),
        )

    def test_rejects_non_locked_production_status(self) -> None:
        invalid = copy.deepcopy(self.data)
        invalid["visualCanon"]["productionStatus"] = "CANDIDATE"
        self.assertIn(
            "visualCanon.productionStatus must be LOCKED",
            validate_contract_data(invalid),
        )

    def test_visual_canon_path_must_be_normalized_and_repo_relative(self) -> None:
        invalid_paths = [
            "C:/Project/Roblox/tools/canonical-visuals/asset.json",
            "/tmp/canonical-visuals/asset.json",
            "../canonical-visuals/asset.json",
            "tools/../canonical-visuals/asset.json",
            r"tools\canonical-visuals\asset.json",
        ]
        for configured_path in invalid_paths:
            with self.subTest(configured_path=configured_path):
                invalid = copy.deepcopy(self.data)
                invalid["visualCanon"]["path"] = configured_path
                self.assertTrue(
                    any(
                        error.startswith("visualCanon.path")
                        for error in validate_contract_data(invalid)
                    )
                )

    def test_asset_schema_rejects_absolute_and_parent_paths(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        pattern = schema["properties"]["visualCanon"]["properties"]["path"][
            "pattern"
        ]
        configured_path = self.data["visualCanon"]["path"]
        self.assertIsNotNone(re.search(pattern, configured_path))
        for invalid_path in (
            "C:/repo/canonical-visuals/asset.json",
            "/repo/canonical-visuals/asset.json",
            "../canonical-visuals/asset.json",
            r"repo\canonical-visuals\asset.json",
        ):
            with self.subTest(invalid_path=invalid_path):
                self.assertIsNone(re.search(pattern, invalid_path))

    def test_invalid_json_is_fail_not_pass(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "asset.json"
            path.write_text("not json", encoding="utf-8")
            self.assertEqual("FAIL", validate_contract(path)["status"])

    def test_rejects_asset_budget_above_visual_canon_maximum(self) -> None:
        invalid = copy.deepcopy(self.data)
        invalid["triangleBudget"]["absoluteMaximum"] = 2_001
        report = self._validate_in_temporary_repo(invalid)
        self.assertIn(
            "asset triangle maximum 2001 exceeds visual canon maximum 2000",
            report["errors"],
        )

    def test_rejects_state_coverage_drift_from_visual_canon(self) -> None:
        invalid = copy.deepcopy(self.data)
        invalid["states"]["variants"].pop()
        report = self._validate_in_temporary_repo(invalid)
        self.assertTrue(
            any(
                "asset state order or coverage differs from visual canon" in error
                for error in report["errors"]
            )
        )

    def test_installed_package_visual_canon_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            contract_path = repo / "assets-3d" / "sample" / "asset.json"
            contract_path.parent.mkdir(parents=True)
            canon_path = (
                repo
                / "tools"
                / "roblox-art-bible-sota-v3"
                / "art"
                / "canonical-visuals"
                / "territory"
                / "asset.json"
            )
            canon_path.parent.mkdir(parents=True)
            canon_path.write_text("{}\n", encoding="utf-8")
            self.assertEqual(
                canon_path,
                resolve_visual_canon_path(
                    contract_path,
                    "tools/roblox-art-bible-sota-v3/art/"
                    "canonical-visuals/territory/asset.json",
                ),
            )

    def test_source_package_visual_canon_resolution_stays_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            package = Path(folder) / "roblox-art-bible-sota-v3"
            contract_path = package / "assets-3d" / "sample" / "asset.json"
            contract_path.parent.mkdir(parents=True)
            canon_path = (
                package
                / "art"
                / "canonical-visuals"
                / "territory"
                / "asset.json"
            )
            canon_path.parent.mkdir(parents=True)
            canon_path.write_text("{}\n", encoding="utf-8")
            self.assertEqual(
                canon_path.resolve(),
                resolve_visual_canon_path(
                    contract_path,
                    "tools/roblox-art-bible-sota-v3/art/"
                    "canonical-visuals/territory/asset.json",
                ),
            )

    def test_visual_canon_resolver_rejects_escape_before_io(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            contract_path = (
                Path(folder) / "assets-3d" / "sample" / "asset.json"
            )
            contract_path.parent.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "must not contain"):
                resolve_visual_canon_path(
                    contract_path,
                    "tools/../canonical-visuals/asset.json",
                )


if __name__ == "__main__":
    unittest.main()
