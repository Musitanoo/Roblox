from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.canon_packet import (
    BOARD_IDS,
    RAW_VIEW_IDS,
    CanonPacketError,
    _bounded,
    _load_cached_raw,
    _package_digest,
    _run_raw_render,
    _write_gallery,
)
from pipeline.io_utils import sha256_file


class CanonPacketTests(unittest.TestCase):
    def test_board_contract_is_exact_and_unique(self) -> None:
        self.assertEqual(
            BOARD_IDS,
            (
                "orthographic",
                "perspective",
                "black_silhouette",
                "component_breakdown",
                "proportions",
                "materials",
                "semantic_zones",
                "all_states",
                "state_comparison",
                "mobile_near",
                "mobile_mid",
                "mobile_far",
                "lighting_matrix",
                "repetition_1",
                "repetition_30",
                "repetition_100",
                "required_and_forbidden_annotations",
            ),
        )
        self.assertEqual(len(BOARD_IDS), len(set(BOARD_IDS)))

    def test_package_digest_ignores_timestamp_and_self_digest(self) -> None:
        manifest = {
            "$schema": "schema",
            "schemaVersion": "1.0.0",
            "assetKey": "asset",
            "assetId": "asset-id",
            "territoryId": "territory",
            "canonId": "canon",
            "baseCandidateSha256": "a" * 64,
            "evidenceClass": "REAL_RENDERED",
            "generation": {"renderer": "Blender"},
            "authority": {"bindings": []},
            "boards": {},
            "humanReviewStatus": "PENDING",
            "productionApproved": False,
            "generatedAt": "2026-01-01T00:00:00Z",
            "evidencePackageSha256": "old",
        }
        first = _package_digest(manifest)
        manifest["generatedAt"] = "2027-01-01T00:00:00Z"
        manifest["evidencePackageSha256"] = "different"
        self.assertEqual(first, _package_digest(manifest))
        manifest["assetKey"] = "changed"
        self.assertNotEqual(first, _package_digest(manifest))

    def test_hash_bound_raw_cache_rejects_file_and_renderer_drift(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            renders = []
            for index, view_id in enumerate(RAW_VIEW_IDS):
                path = output / f"{view_id}.png"
                path.write_bytes(f"render-{index}".encode("ascii"))
                renders.append(
                    {
                        "viewId": view_id,
                        "path": path.name,
                        "bytes": path.stat().st_size,
                        "sha256": sha256_file(path),
                    }
                )
            manifest = {
                "status": "PASS",
                "evidenceClass": "REAL_RENDERED",
                "assetKey": "asset",
                "revision": 6,
                "contractSha256": "contract",
                "canonId": "canon",
                "canonSha256": "canon-sha",
                "sourceBlendSha256": "source",
                "buildManifestSha256": "build",
                "rendererScriptSha256": "renderer",
                "renders": renders,
            }
            (output / "raw-manifest.json").write_text(
                json.dumps(manifest),
                encoding="utf-8",
            )
            arguments = {
                "asset_key": "asset",
                "revision": 6,
                "contract_sha": "contract",
                "canon_id": "canon",
                "canon_sha": "canon-sha",
                "source_sha": "source",
                "build_manifest_sha": "build",
                "renderer_sha": "renderer",
            }
            self.assertIsNotNone(_load_cached_raw(output, **arguments))

            arguments["renderer_sha"] = "changed"
            self.assertIsNone(_load_cached_raw(output, **arguments))
            arguments["renderer_sha"] = "renderer"

            (output / f"{RAW_VIEW_IDS[0]}.png").write_bytes(b"tampered")
            self.assertIsNone(_load_cached_raw(output, **arguments))

    def test_output_path_must_remain_under_evidence_root(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder) / "evidence"
            root.mkdir()
            self.assertEqual(_bounded(root / "asset", root, "output"), root / "asset")
            with self.assertRaises(CanonPacketError):
                _bounded(root.parent / "escape", root, "output")

    def test_raw_render_sanitizes_blender_environment(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            tool_root = root / "tool"
            renderer = tool_root / "blender" / "render_canon_packet.py"
            renderer.parent.mkdir(parents=True)
            renderer.write_text("# renderer", encoding="utf-8")
            output = root / "output"

            def fake_run(*_args: object, **_kwargs: object) -> SimpleNamespace:
                (output / "raw-manifest.json").write_text(
                    json.dumps(
                        {
                            "status": "PASS",
                            "renders": [
                                {"viewId": view_id}
                                for view_id in RAW_VIEW_IDS
                            ],
                        }
                    ),
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=0, stdout="", stderr="")

            with patch.dict(
                os.environ,
                {"ROBLOX_OPEN_CLOUD_API_KEY": "must-not-reach-blender"},
                clear=False,
            ):
                with patch(
                    "pipeline.canon_packet.subprocess.run",
                    side_effect=fake_run,
                ) as run_blender:
                    result = _run_raw_render(
                        Path("blender.exe"),
                        tool_root,
                        root / "asset.json",
                        root / "source.blend",
                        output,
                    )

        self.assertEqual("PASS", result["status"])
        environment = run_blender.call_args.kwargs["env"]
        self.assertNotIn("ROBLOX_OPEN_CLOUD_API_KEY", environment)
        self.assertEqual("0", environment["PYTHONHASHSEED"])
        self.assertGreater(run_blender.call_args.kwargs["timeout"], 0)

    def test_gallery_contains_complete_local_review_workstation(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            board_paths = {
                board_id: output / f"{index:02d}-{board_id}.png"
                for index, board_id in enumerate(BOARD_IDS, start=1)
            }
            review = {
                "$schema": "https://roblox-top1.local/schemas/visual-canon-human-review.schema.json",
                "schemaVersion": "1.0.0",
                "status": "PENDING",
                "assetKey": "asset",
                "assetId": "barricade",
                "territoryId": "salvaged-frontier",
                "revision": 6,
                "canonId": "vc_barricade__salvaged-frontier__v1",
                "evidenceManifest": "evidence/manifest.json",
                "evidenceManifestSha256": "a" * 64,
                "evidencePackageSha256": "b" * 64,
                "reviewer": None,
                "reviewedAt": None,
                "decision": None,
                "decisionRecord": None,
                "allowedDecisions": ["LOCK", "REVISION_REQUIRED", "REJECT"],
                "boards": {
                    board_id: {"status": "PENDING", "comment": None}
                    for board_id in BOARD_IDS
                },
                "mandatoryChecks": {
                    "oneSecondFunctionRead": "PENDING",
                    "stateReadWithoutColorOnly": "PENDING",
                    "mobileNearMidFar": "PENDING",
                    "lightingRobustness": "PENDING",
                    "repetitionOneThirtyHundred": "PENDING",
                    "requiredAndForbiddenCompliance": "PENDING",
                    "artDirectionQuality": "PENDING",
                },
                "productionApproved": False,
            }
            _write_gallery(
                output,
                {"displayName": "Asset", "revision": 6},
                {"identity": {"territoryVisualThesis": "Thesis"}},
                "b" * 64,
                board_paths,
                review,
            )
            page = (output / "index.html").read_text(encoding="utf-8")
            self.assertEqual(
                page.count('<article class="card" data-board="'),
                len(BOARD_IDS),
            )
            self.assertIn("human-review-completed.json", page)
            self.assertIn("visual-canon-review:", page)
            self.assertIn("17 planches · 0/7 gates", page)


if __name__ == "__main__":
    unittest.main()
