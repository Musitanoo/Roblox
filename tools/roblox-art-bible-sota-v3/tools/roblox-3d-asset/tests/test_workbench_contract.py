from __future__ import annotations

import copy
import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.bounded_operations import source_bindings, validate_change_set
from mcp.session_manager import _compare_promoted_contract
from mcp.security_policy import (
    WorkbenchError,
    ensure_asset_contract,
    sanitized_blender_environment,
    sanitized_subprocess_environment,
)


REPO = ROOT.parents[1]
CONTRACT_PATH = REPO / "assets-3d" / "defense-barricade-small" / "asset.json"
HASH = "a" * 64


def valid_change_set() -> dict:
    return {
        "schemaVersion": "1.0.0",
        "changeSetId": "bounded-change-001",
        "sessionId": "bounded-session-001",
        "assetKey": "defense_barricade_small",
        "baseBuildSha256": HASH,
        "assetContractSha256": HASH,
        "visualCanonId": "vc_barricade__salvaged-frontier__v1",
        "visualCanonSha256": HASH,
        "intent": "Test a bounded dimension change",
        "observation": "The support reads too narrowly",
        "probableCause": "The declared width is small",
        "targets": ["DEF_BarricadeSmall_FootL"],
        "operations": [
            {
                "type": "SET_COMPONENT_DIMENSION",
                "target": "DEF_BarricadeSmall_FootL",
                "axis": "designX",
                "before": 1.6,
                "after": 1.8,
            }
        ],
        "preservedInvariants": ["overallWidth", "referenceImmutability"],
        "requiredViews": ["front", "mobile_distance"],
        "expectedEffects": ["stronger support"],
        "maximumTriangleDelta": 0,
        "rollbackMethod": "Restore the candidate backup",
        "productionAuthorized": False,
    }


class WorkbenchContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
        self.session = {
            "sessionId": "bounded-session-001",
            "reference": {"sha256": HASH},
            "contract": {"sha256": HASH},
            "visualCanon": {
                "canonId": "vc_barricade__salvaged-frontier__v1",
                "sha256": HASH,
            },
        }

    def test_declared_dimension_change_is_source_bound(self) -> None:
        change_set = valid_change_set()
        validate_change_set(change_set, self.session, self.contract)
        bindings = source_bindings(change_set, self.contract)
        self.assertEqual("/geometry/parts/0/size/0", bindings[0]["jsonPointer"])
        self.assertTrue(bindings[0]["sourcePromotable"])

    def test_rejects_arbitrary_python_operation(self) -> None:
        change_set = valid_change_set()
        change_set["operations"][0]["type"] = "EXECUTE_ARBITRARY_PYTHON"
        with self.assertRaisesRegex(WorkbenchError, "forbidden"):
            validate_change_set(change_set, self.session, self.contract)

    def test_rejects_undeclared_component(self) -> None:
        change_set = valid_change_set()
        change_set["operations"][0]["target"] = "InventedPart"
        change_set["targets"] = ["InventedPart"]
        with self.assertRaisesRegex(WorkbenchError, "undeclared"):
            validate_change_set(change_set, self.session, self.contract)

    def test_rejects_stale_reference_hash(self) -> None:
        change_set = valid_change_set()
        change_set["baseBuildSha256"] = "b" * 64
        with self.assertRaisesRegex(WorkbenchError, "stale"):
            validate_change_set(change_set, self.session, self.contract)

    def test_rejects_out_of_repo_contract(self) -> None:
        with self.assertRaises(WorkbenchError):
            ensure_asset_contract(Path(os.environ.get("WINDIR", "C:/Windows")) / "asset.json", REPO)

    def test_sanitized_environment_drops_roblox_secrets(self) -> None:
        previous = os.environ.get("ROBLOX_OPEN_CLOUD_API_KEY")
        os.environ["ROBLOX_OPEN_CLOUD_API_KEY"] = "must-not-escape"
        try:
            environment = sanitized_blender_environment()
        finally:
            if previous is None:
                os.environ.pop("ROBLOX_OPEN_CLOUD_API_KEY", None)
            else:
                os.environ["ROBLOX_OPEN_CLOUD_API_KEY"] = previous
        self.assertNotIn("ROBLOX_OPEN_CLOUD_API_KEY", environment)
        self.assertEqual("true", environment["DISABLE_TELEMETRY"])

    def test_configured_child_environment_cannot_reintroduce_secrets(self) -> None:
        environment = sanitized_subprocess_environment(
            {
                "BROWSER_USE_AVAILABLE_BACKENDS": "chrome,iab",
                "OPENAI_API_KEY": "must-not-escape",
                "ROBLOX_OPEN_CLOUD_API_KEY": "must-not-escape",
                "CUSTOM_TOKEN": "must-not-escape",
            }
        )
        self.assertEqual("chrome,iab", environment["BROWSER_USE_AVAILABLE_BACKENDS"])
        self.assertNotIn("OPENAI_API_KEY", environment)
        self.assertNotIn("ROBLOX_OPEN_CLOUD_API_KEY", environment)
        self.assertNotIn("CUSTOM_TOKEN", environment)

    def test_rejects_operation_beyond_bound(self) -> None:
        change_set = valid_change_set()
        change_set["operations"][0]["after"] = 4.0
        with self.assertRaisesRegex(WorkbenchError, "bounded"):
            validate_change_set(change_set, self.session, self.contract)

    def test_promoted_source_requires_exact_semantic_equivalence(self) -> None:
        expected = copy.deepcopy(self.contract)
        expected["revision"] = self.contract["revision"] + 1
        session = {
            "contract": {
                "path": str(CONTRACT_PATH.resolve()),
                "revision": self.contract["revision"],
            },
            "visualCanon": {"sha256": expected["visualCanon"]["sha256"]},
        }
        comparison = _compare_promoted_contract(
            session=session,
            expected=expected,
            authoritative=copy.deepcopy(expected),
            authoritative_path=CONTRACT_PATH,
        )
        self.assertTrue(comparison["passed"])

        extended = copy.deepcopy(expected)
        extended["geometry"]["parts"][0]["size"][0] += 0.01
        comparison = _compare_promoted_contract(
            session=session,
            expected=expected,
            authoritative=extended,
            authoritative_path=CONTRACT_PATH,
        )
        self.assertFalse(comparison["passed"])
        self.assertFalse(comparison["checks"]["semanticSource"]["passed"])

    def test_promoted_source_rejects_wrong_authoritative_path(self) -> None:
        expected = copy.deepcopy(self.contract)
        expected["revision"] = self.contract["revision"] + 1
        session = {
            "contract": {
                "path": str(CONTRACT_PATH.resolve()),
                "revision": self.contract["revision"],
            },
            "visualCanon": {"sha256": expected["visualCanon"]["sha256"]},
        }
        comparison = _compare_promoted_contract(
            session=session,
            expected=expected,
            authoritative=copy.deepcopy(expected),
            authoritative_path=CONTRACT_PATH.parent / "other.json",
        )
        self.assertFalse(comparison["passed"])
        self.assertFalse(comparison["checks"]["authoritativePath"]["passed"])


if __name__ == "__main__":
    unittest.main()
