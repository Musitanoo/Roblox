from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.art import publish_transfer_candidates as publication
from tools.art.common import ROOT


MANIFEST = ROOT / "build/studio-import-transfer/manifest.json"


def _set_staging_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ROBLOX_OPEN_CLOUD_API_KEY", "test-key")
    monkeypatch.setenv("ROBLOX_STAGING_CREATOR_ID", "123456")
    monkeypatch.setenv("ROBLOX_3D_ALLOWED_CREATOR_IDS", "123456")


def test_transfer_publication_dry_run_never_mutates(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_staging_environment(monkeypatch)
    monkeypatch.setattr(
        publication,
        "mutate_asset",
        lambda *args, **kwargs: pytest.fail("dry-run attempted mutation"),
    )
    result = publication.publish(
        MANIFEST,
        tmp_path / "registry.json",
        tmp_path / "report.json",
        dry_run=True,
        confirm_publish=False,
    )
    assert result["status"] == "PARTIAL"
    assert result["mutationPerformed"] is False
    assert not (tmp_path / "registry.json").exists()
    assert not (tmp_path / "report.json").exists()


def test_transfer_publication_requires_explicit_confirmation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_staging_environment(monkeypatch)
    result = publication.publish(
        MANIFEST,
        tmp_path / "registry.json",
        tmp_path / "report.json",
        dry_run=False,
        confirm_publish=False,
    )
    assert result["status"] == "BLOCKED"
    assert result["mutationPerformed"] is False
    assert not (tmp_path / "registry.json").exists()


def test_transfer_publication_creates_nine_sanitized_records(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_staging_environment(monkeypatch)
    counter = iter(range(700001, 700010))
    pending: list[int] = []

    def fake_mutate(*args, **kwargs):
        value = next(counter)
        pending.append(value)
        return {"path": f"operations/op-{value}"}

    def fake_poll(path: str, api_key: str):
        return {"response": {"assetId": pending[-1]}}

    def fake_get(path: str, api_key: str):
        asset_id = int(path.rsplit("/", 1)[-1])
        return {
            "assetId": asset_id,
            "revisionId": f"revision-{asset_id}",
            "creationContext": {"creator": {"userId": "123456"}},
        }

    monkeypatch.setattr(publication, "mutate_asset", fake_mutate)
    monkeypatch.setattr(publication, "poll_operation", fake_poll)
    monkeypatch.setattr(publication, "get_json", fake_get)
    report_path = tmp_path / "report.json"
    registry_path = tmp_path / "registry.json"
    result = publication.publish(
        MANIFEST,
        registry_path,
        report_path,
        dry_run=False,
        confirm_publish=True,
    )
    assert result["status"] == "PASS"
    assert len(result["entries"]) == 9
    assert all(item["action"] == "CREATE" for item in result["entries"])
    public_text = report_path.read_text(encoding="utf-8")
    assert "700001" not in public_text
    assert "123456" not in public_text
    assert "operations/" not in public_text
    local = json.loads(registry_path.read_text(encoding="utf-8"))
    assert len(local["assets"]) == 9


def test_transfer_publication_blocks_missing_allowlist(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("ROBLOX_OPEN_CLOUD_API_KEY", "test-key")
    monkeypatch.setenv("ROBLOX_STAGING_CREATOR_ID", "123456")
    monkeypatch.setenv("ROBLOX_3D_ALLOWED_CREATOR_IDS", "999999")
    result = publication.publish(
        MANIFEST,
        tmp_path / "registry.json",
        tmp_path / "report.json",
        dry_run=False,
        confirm_publish=True,
    )
    assert result["status"] == "BLOCKED"
    assert result["guardChecks"]["creatorAllowlisted"] is False


def test_transfer_publication_reuses_verified_remote_assets_without_mutation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_staging_environment(monkeypatch)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = {
        entry["uploadName"]: {
            "assetId": 800000 + index,
            "sourceSha256": entry["sha256"],
            "remoteRevisionId": f"revision-{index}",
            "history": [],
        }
        for index, entry in enumerate(manifest["entries"], start=1)
    }
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "schemaVersion": "1.0.0",
                "environment": "staging",
                "assetId": "turret_fast_v1",
                "assets": assets,
            }
        ),
        encoding="utf-8",
    )

    def fake_get(path: str, api_key: str):
        asset_id = int(path.rsplit("/", 1)[-1])
        return {
            "assetId": asset_id,
            "creationContext": {"creator": {"userId": "123456"}},
        }

    monkeypatch.setattr(publication, "get_json", fake_get)
    monkeypatch.setattr(
        publication,
        "mutate_asset",
        lambda *args, **kwargs: pytest.fail("resume attempted mutation"),
    )
    result = publication.publish(
        MANIFEST,
        registry_path,
        tmp_path / "report.json",
        dry_run=False,
        confirm_publish=True,
    )
    assert result["status"] == "PASS"
    assert result["mutationPerformed"] is False
    assert all(item["action"] == "REUSE" for item in result["entries"])


def test_transfer_publication_revalidation_preserves_canonical_evidence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _set_staging_environment(monkeypatch)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assets = {
        entry["uploadName"]: {
            "assetId": 900000 + index,
            "sourceSha256": entry["sha256"],
            "remoteRevisionId": f"revision-{index}",
            "history": [],
        }
        for index, entry in enumerate(manifest["entries"], start=1)
    }
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        json.dumps(
            {
                "schemaVersion": "1.0.0",
                "environment": "staging",
                "assetId": "turret_fast_v1",
                "assets": assets,
            }
        ),
        encoding="utf-8",
    )

    def fake_get(path: str, api_key: str):
        asset_id = int(path.rsplit("/", 1)[-1])
        return {
            "assetId": asset_id,
            "creationContext": {"creator": {"userId": "123456"}},
        }

    monkeypatch.setattr(publication, "get_json", fake_get)
    report_path = tmp_path / "report.json"
    first = publication.publish(
        MANIFEST,
        registry_path,
        report_path,
        dry_run=False,
        confirm_publish=True,
    )
    first_bytes = report_path.read_bytes()
    assert first["evidencePreserved"] is False
    second = publication.publish(
        MANIFEST,
        registry_path,
        report_path,
        dry_run=False,
        confirm_publish=True,
    )
    assert second["evidencePreserved"] is True
    assert report_path.read_bytes() == first_bytes
