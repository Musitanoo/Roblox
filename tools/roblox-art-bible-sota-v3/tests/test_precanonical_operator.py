from __future__ import annotations

import base64
import json
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from PIL import Image

from tools.art.common import ArtSystemError, ROOT, load_json, validate_with_schema
from tools.art.precanonical import ASSESSMENT_KEYS, init_packet
from tools.art.precanonical_operator import (
    OperatorHttpServer,
    OperatorSession,
    prepare_operator_session,
)

BRIEF = ROOT / "art/precanonical/examples/defense-barricade-small-brief.json"


def _request(tmp_path: Path) -> Path:
    return init_packet(
        BRIEF,
        "operator-web-001",
        tmp_path
        / "asset"
        / "precanonical"
        / "requests"
        / "operator-web-001",
        "exploration",
        4,
        True,
        False,
        browser_adapter="codex_iab",
    )


def _png_bytes(tmp_path: Path) -> bytes:
    path = tmp_path / "download.png"
    Image.new("RGB", (512, 512), (47, 62, 67)).save(path, format="PNG")
    return path.read_bytes()


def _attestation() -> dict[str, bool]:
    return {
        "exactSubmissionTextUsed": True,
        "noPromptRewrite": True,
        "exactlyOneGenerationRequested": True,
        "oneResultDownloaded": True,
        "noAutomaticRetry": True,
    }


def _assessment(value: str) -> dict[str, str]:
    return {key: value for key in ASSESSMENT_KEYS}


def test_operator_prepares_hash_bound_browser_independent_session(
    tmp_path: Path,
) -> None:
    request = _request(tmp_path)
    manifest = prepare_operator_session(request, tmp_path / "operator")
    session = load_json(manifest)
    assert session["status"] == "READY_FOR_HUMAN_WEB_SUBMISSION"
    assert session["browserAutomationUsed"] is False
    assert session["apiUsed"] is False
    assert session["automaticRetryUsed"] is False
    assert session["attachments"] == []
    assert session["submissionText"].endswith(
        "- independent redesign of damage states\n"
        "- additional decorative weapons\n"
        "- baked cinematic lighting"
    )
    assert (
        validate_with_schema(
            session,
            ROOT / "schemas/precanonical-operator-session.schema.json",
        )
        == []
    )


def test_operator_imports_once_and_resumes_for_review(tmp_path: Path) -> None:
    request = _request(tmp_path)
    manifest = prepare_operator_session(request, tmp_path / "operator")
    operator = OperatorSession(manifest)
    state = operator.import_image(
        "download.png",
        _png_bytes(tmp_path),
        _attestation(),
        None,
        False,
    )
    assert state["status"] == "VISUAL_REVIEW_REQUIRED"
    assert state["reviewDefaults"]["preserve"]
    assert state["reviewDefaults"]["editable"] is True
    assert state["reviewDefaults"]["humanConfirmationRequired"] is True
    assert {
        source["kind"] for source in state["reviewDefaults"]["sources"]
    } == {"CANON_STATE_INVARIANTS"}
    assert state["humanAttestation"]["exactSubmissionTextUsed"] is True
    result_path = Path(state["result"]["path"])
    result = load_json(result_path)
    assert result["provenance"]["downloadMethod"] == "manual_download"
    assert result["generationIndex"] == 1
    assert result["canonical"] is False
    resumed = prepare_operator_session(request, tmp_path / "operator")
    assert resumed == manifest
    assert OperatorSession(resumed).public_state()["status"] == "VISUAL_REVIEW_REQUIRED"
    with pytest.raises(ArtSystemError, match="already imported"):
        operator.import_image(
            "second.png",
            _png_bytes(tmp_path),
            _attestation(),
            None,
            False,
        )


def test_operator_rejects_unattested_upload(tmp_path: Path) -> None:
    manifest = prepare_operator_session(_request(tmp_path), tmp_path / "operator")
    attestation = _attestation()
    attestation["noPromptRewrite"] = False
    with pytest.raises(ArtSystemError, match="attestation"):
        OperatorSession(manifest).import_image(
            "download.png",
            _png_bytes(tmp_path),
            attestation,
            None,
            False,
        )


def test_operator_rejects_tampered_output_path(tmp_path: Path) -> None:
    manifest = prepare_operator_session(_request(tmp_path), tmp_path / "operator")
    value = load_json(manifest)
    value["plannedResultOutput"] = str(tmp_path / "outside")
    manifest.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(ArtSystemError, match="escapes"):
        OperatorSession(manifest)


def test_operator_records_hash_bound_human_selection(tmp_path: Path) -> None:
    manifest = prepare_operator_session(_request(tmp_path), tmp_path / "operator")
    operator = OperatorSession(manifest)
    operator.import_image(
        "download.png",
        _png_bytes(tmp_path),
        _attestation(),
        None,
        False,
    )
    state = operator.record_review(
        {
            "decision": "HUMAN_SELECTED",
            "reviewer": "Founder",
            "assessment": _assessment("PASS"),
            "preserve": ["Preserve the broad grounded silhouette."],
            "correct": [],
            "forbidNext": ["Do not invent a fourth armor panel."],
        }
    )
    assert state["status"] == "REVIEW_RECORDED"
    assert state["reviewDecision"] == "HUMAN_SELECTED"
    review = load_json(Path(state["review"]["path"]))
    assert review["canonicalizationAuthorized"] is True
    assert review["canonical"] is False
    assert review["productionApproved"] is False


def test_operator_ui_and_runner_expose_single_command_bridge() -> None:
    ui = (ROOT / "tools/art/precanonical-operator.html").read_text(encoding="utf-8")
    assert "Copier le texte exact" in ui
    assert "Ouvrir ChatGPT Web" in ui
    assert "Glisse l’image téléchargée ici" in ui
    assert "/api/import" in ui
    assert "/api/review" in ui
    assert "/api/task-image" in ui
    assert "Explorateur objet × état" in ui
    assert "Pas encore générés" in ui
    assert "Historique des générations" in ui
    assert "Revenir à la tâche active" in ui
    assert "Choisis ensuite librement une autre voie disponible" in ui
    assert "Prompt de cet objet × état" in ui
    assert "Générer cet état maintenant" in ui
    assert "/api/task-prompt" in ui
    assert "/api/select-task" in ui
    assert 'const reviewerAllowed = decision === "HUMAN_SELECTED";' in ui
    assert "reviewerInput.disabled = !reviewerAllowed;" in ui
    assert 'reviewer: decision === "HUMAN_SELECTED"' in ui
    assert "applyReviewDefaults()" in ui
    assert "Restaurer les invariants proposés" in ui
    assert 'source.kind === "PREVIOUS_ACCEPTED_REVIEW"' in ui
    runner = (ROOT / "scripts/art-direction.ps1").read_text(encoding="utf-8")
    assert "precanon-operator" in runner
    assert "precanon-campaign-operator" in runner
    assert "tools.art.precanonical_operator" in runner
    assert "$IdleTimeoutMinutes" in runner
    assert "$NoOpen" in runner


def test_operator_http_bridge_is_token_bound_and_imports_image(
    tmp_path: Path,
) -> None:
    manifest = prepare_operator_session(_request(tmp_path), tmp_path / "operator")
    server = OperatorHttpServer(
        ("127.0.0.1", 0),
        OperatorSession(manifest),
        "test-token",
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urllib.request.urlopen(root + "/", timeout=5) as response:
            assert response.status == 200
            assert b"Poste op\xc3\xa9rateur pr\xc3\xa9canonique" in response.read()
        with pytest.raises(urllib.error.HTTPError) as unauthorized:
            urllib.request.urlopen(root + "/api/session", timeout=5)
        assert unauthorized.value.code == 401

        session_request = urllib.request.Request(
            root + "/api/session",
            headers={"X-Operator-Token": "test-token"},
        )
        with urllib.request.urlopen(session_request, timeout=5) as response:
            payload = json.loads(response.read())
        assert payload["session"]["status"] == "READY_FOR_HUMAN_WEB_SUBMISSION"

        import_body = json.dumps(
            {
                "filename": "download.png",
                "imageBase64": base64.b64encode(_png_bytes(tmp_path)).decode(
                    "ascii"
                ),
                "modelName": None,
                "modelNameConfirmed": False,
                "attestation": _attestation(),
            }
        ).encode("utf-8")
        import_request = urllib.request.Request(
            root + "/api/import",
            data=import_body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "X-Operator-Token": "test-token",
            },
        )
        with urllib.request.urlopen(import_request, timeout=10) as response:
            imported = json.loads(response.read())
        assert imported["session"]["status"] == "VISUAL_REVIEW_REQUIRED"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
