from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.report import _visual_review_status, build_report
from pipeline.io_utils import read_json
from pipeline.review import (
    ASSET_REVIEW_SCHEMA,
    ASSET_REVIEW_SCHEMA_VERSION,
    compute_evidence_digest,
)
from pipeline.status import Status


REPO = ROOT.parents[1]
CONTRACT = REPO / "assets-3d" / "defense-barricade-small" / "asset.json"
REVIEW_SCHEMA = ROOT / "schemas" / "asset-review.schema.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bound_review(
    asset_root: Path,
    contract: dict[str, Any],
    contract_sha256: str,
    *,
    review_status: str = Status.PARTIAL.value,
    human_status: str = "PENDING",
) -> dict[str, Any]:
    evidence = asset_root / "report.json"
    evidence.write_text("{}\n", encoding="utf-8")
    digest, issues = compute_evidence_digest(asset_root, ["report.json"])
    if issues or digest is None:
        raise AssertionError(issues)
    return {
        "$schema": ASSET_REVIEW_SCHEMA,
        "schemaVersion": ASSET_REVIEW_SCHEMA_VERSION,
        "assetKey": contract["assetKey"],
        "revision": contract["revision"],
        "contractSha256": contract_sha256,
        "visualCanonSha256": contract["visualCanon"]["sha256"],
        "evidenceDigest": digest,
        "reviewStatus": review_status,
        "automationReviewStatus": Status.PASS.value,
        "humanReviewStatus": human_status,
        "evidence": ["report.json"],
    }


class ReportTests(unittest.TestCase):
    def test_missing_cloud_and_studio_gates_never_approve_production(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            report = build_report(CONTRACT, Path(folder) / "report.json")
        self.assertFalse(report["productionApproved"])
        self.assertNotEqual("PASS", report["implementationStatus"])
        self.assertEqual("BLOCKED", report["gates"]["cloudPackageV1"])
        self.assertEqual("BLOCKED", report["gates"]["studioStagingConfirmed"])
        self.assertIn("stateCoverage", report["gates"])
        self.assertIn("buildFreshness", report["gates"])
        self.assertIn("stateDeterminism", report["gates"])
        self.assertIn("stateInvariants", report["gates"])
        self.assertIn("stateDistinctness", report["gates"])
        self.assertIn("stateReviewBoard", report["gates"])
        review = read_json(CONTRACT.parent / "review.json")
        expected_review_status, expected_review_issues = _visual_review_status(
            review,
            asset_root=CONTRACT.parent,
            contract=read_json(CONTRACT),
            contract_sha256=_sha256(CONTRACT),
        )
        self.assertEqual(expected_review_status, report["gates"]["visualReview"])
        self.assertEqual(
            bool(expected_review_issues),
            bool(report["evidence"]["visualReviewIssues"]),
        )
    def test_visual_review_fails_closed_when_declared_evidence_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            asset_root = Path(folder)
            contract = {
                "assetKey": "test_asset",
                "revision": 4,
                "visualCanon": {"sha256": "2" * 64},
            }
            review = _bound_review(asset_root, contract, "1" * 64)
            (asset_root / "report.json").unlink()
            status, issues = _visual_review_status(
                review,
                asset_root=asset_root,
                contract=contract,
                contract_sha256="1" * 64,
            )
        self.assertEqual(Status.FAIL.value, status)
        self.assertTrue(any("is missing" in issue for issue in issues))

    def test_visual_review_rejects_evidence_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            asset_root = Path(folder) / "asset"
            asset_root.mkdir()
            outside = Path(folder) / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            contract = {
                "assetKey": "test_asset",
                "revision": 4,
                "visualCanon": {"sha256": "2" * 64},
            }
            review = _bound_review(asset_root, contract, "1" * 64)
            review["evidence"] = ["../outside.json"]
            status, issues = _visual_review_status(
                review,
                asset_root=asset_root,
                contract=contract,
                contract_sha256="1" * 64,
            )
        self.assertEqual(Status.FAIL.value, status)
        self.assertTrue(any("must not contain" in issue for issue in issues))

    def test_visual_review_pass_requires_both_approval_classes(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            asset_root = Path(folder)
            contract = {
                "assetKey": "test_asset",
                "revision": 4,
                "visualCanon": {"sha256": "2" * 64},
            }
            review = _bound_review(
                asset_root,
                contract,
                "1" * 64,
                review_status=Status.PASS.value,
            )
            status, issues = _visual_review_status(
                review,
                asset_root=asset_root,
                contract=contract,
                contract_sha256="1" * 64,
            )
        self.assertEqual(Status.FAIL.value, status)
        self.assertIn("PASS review requires humanReviewStatus=PASS", issues)

    def test_bound_partial_review_passes_its_own_gate(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            asset_root = Path(folder)
            contract = {
                "assetKey": "test_asset",
                "revision": 4,
                "visualCanon": {"sha256": "2" * 64},
            }
            review = _bound_review(asset_root, contract, "1" * 64)
            status, issues = _visual_review_status(
                review,
                asset_root=asset_root,
                contract=contract,
                contract_sha256="1" * 64,
            )
        self.assertEqual(Status.PARTIAL.value, status)
        self.assertEqual([], issues)

    def test_same_revision_with_different_contract_bytes_fails(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            asset_root = Path(folder)
            contract = {
                "assetKey": "test_asset",
                "revision": 4,
                "visualCanon": {"sha256": "2" * 64},
            }
            review = _bound_review(asset_root, contract, "0" * 64)
            status, issues = _visual_review_status(
                review,
                asset_root=asset_root,
                contract=contract,
                contract_sha256="1" * 64,
            )
        self.assertEqual(Status.FAIL.value, status)
        self.assertTrue(
            any("exact asset contract bytes" in issue for issue in issues)
        )

    def test_visual_canon_hash_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            asset_root = Path(folder)
            contract = {
                "assetKey": "test_asset",
                "revision": 4,
                "visualCanon": {"sha256": "2" * 64},
            }
            review = _bound_review(asset_root, contract, "1" * 64)
            review["visualCanonSha256"] = "3" * 64
            status, issues = _visual_review_status(
                review,
                asset_root=asset_root,
                contract=contract,
                contract_sha256="1" * 64,
            )
        self.assertEqual(Status.FAIL.value, status)
        self.assertTrue(
            any("visualCanonSha256 does not match" in issue for issue in issues)
        )

    def test_evidence_byte_drift_fails(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            asset_root = Path(folder)
            contract = {
                "assetKey": "test_asset",
                "revision": 4,
                "visualCanon": {"sha256": "2" * 64},
            }
            review = _bound_review(asset_root, contract, "1" * 64)
            (asset_root / "report.json").write_text(
                '{"changed":true}\n',
                encoding="utf-8",
            )
            status, issues = _visual_review_status(
                review,
                asset_root=asset_root,
                contract=contract,
                contract_sha256="1" * 64,
            )
        self.assertEqual(Status.FAIL.value, status)
        self.assertIn("review evidenceDigest.sha256 drift", issues)

    def test_review_schema_declares_all_authority_bindings(self) -> None:
        schema = json.loads(REVIEW_SCHEMA.read_text(encoding="utf-8"))
        self.assertTrue(
            {
                "contractSha256",
                "visualCanonSha256",
                "evidenceDigest",
            }.issubset(schema["required"])
        )
        self.assertEqual(
            "sha256-canonical-json-path-sha256-v1",
            schema["properties"]["evidenceDigest"]["properties"]["scheme"][
                "const"
            ],
        )


if __name__ == "__main__":
    unittest.main()
