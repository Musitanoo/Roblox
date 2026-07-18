from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from publisher.publish import publish


REPO = ROOT.parents[1]
CONTRACT = REPO / "assets-3d" / "defense-barricade-small" / "asset.json"


class PublisherTests(unittest.TestCase):
    def test_dry_run_never_calls_network(self) -> None:
        with mock.patch("publisher.publish.mutate_asset") as mutate:
            result = publish(CONTRACT, dry_run=True, confirm_publish=False)
        self.assertEqual("PARTIAL", result["status"])
        self.assertFalse(result["mutationPerformed"])
        self.assertEqual("CREATE", result["plan"]["action"])
        self.assertEqual("glb", result["plan"]["format"])
        mutate.assert_not_called()

    def test_existing_package_dry_run_uses_fbx_for_update(self) -> None:
        registry = {
            "schemaVersion": "1.0.0",
            "environment": "staging",
            "assets": {
                "defense_barricade_small": {
                    "packageId": 123,
                    "semanticSha256": "different-build",
                    "history": [],
                }
            },
        }
        with mock.patch("publisher.publish._load_registry", return_value=registry), mock.patch(
            "publisher.publish.mutate_asset"
        ) as mutate:
            result = publish(CONTRACT, dry_run=True, confirm_publish=False)
        self.assertEqual("PARTIAL", result["status"])
        self.assertEqual("UPDATE", result["plan"]["action"])
        self.assertEqual("fbx", result["plan"]["format"])
        mutate.assert_not_called()

    def test_confirm_without_credentials_is_blocked_before_network(self) -> None:
        cleared = {
            "ROBLOX_OPEN_CLOUD_API_KEY": "",
            "ROBLOX_STAGING_CREATOR_ID": "",
            "ROBLOX_3D_ALLOWED_CREATOR_IDS": "",
        }
        with mock.patch.dict(os.environ, cleared, clear=False), mock.patch("publisher.publish.mutate_asset") as mutate:
            result = publish(CONTRACT, dry_run=False, confirm_publish=True)
        self.assertEqual("BLOCKED", result["status"])
        mutate.assert_not_called()

    def test_creator_must_be_in_explicit_allowlist(self) -> None:
        environment = {
            "ROBLOX_OPEN_CLOUD_API_KEY": "not-a-real-key",
            "ROBLOX_STAGING_CREATOR_ID": "123",
            "ROBLOX_3D_ALLOWED_CREATOR_IDS": "456",
        }
        with mock.patch.dict(os.environ, environment, clear=False), mock.patch("publisher.publish.mutate_asset") as mutate:
            result = publish(CONTRACT, dry_run=False, confirm_publish=True)
        self.assertEqual("BLOCKED", result["status"])
        mutate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
