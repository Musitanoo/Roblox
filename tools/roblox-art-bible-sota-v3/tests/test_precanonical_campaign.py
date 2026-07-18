from __future__ import annotations

import base64
import json
import threading
import urllib.request
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from tools.art.common import (
    ArtSystemError,
    ROOT,
    load_json,
    sha256_file,
    validate_with_schema,
)
from tools.art.precanonical import ASSESSMENT_KEYS
from tools.art.precanonical_campaign import (
    ASSET_ORDER,
    REQUIRED_MODEL,
    fork_campaign,
    init_campaign,
    snapshot_campaign_canons,
    verify_campaign,
)
from tools.art.precanonical_operator import (
    CampaignOperatorSession,
    OperatorHttpServer,
)


def _campaign(tmp_path: Path) -> Path:
    return init_campaign(tmp_path / "campaign")


def _png_bytes(index: int) -> bytes:
    stream = BytesIO()
    Image.new(
        "RGB",
        (512, 512),
        ((37 * index) % 255, (73 * index) % 255, (109 * index) % 255),
    ).save(stream, format="PNG")
    return stream.getvalue()


def _attestation() -> dict[str, bool]:
    return {
        "exactSubmissionTextUsed": True,
        "noPromptRewrite": True,
        "exactlyOneGenerationRequested": True,
        "oneResultDownloaded": True,
        "noAutomaticRetry": True,
    }


def _review(decision: str = "PRECANONICAL_CANDIDATE") -> dict[str, object]:
    return {
        "decision": decision,
        "reviewer": "Founder" if decision == "HUMAN_SELECTED" else None,
        "assessment": {key: "PASS" for key in ASSESSMENT_KEYS},
        "preserve": ["Preserve the canonical silhouette and stable anchors."],
        "correct": (
            ["Clarify the target state through shape and posture."]
            if decision in {"REVISION_REQUIRED", "REJECTED"}
            else []
        ),
        "forbidNext": ["Do not invent a new component."],
    }


def test_campaign_compiles_six_objects_and_sixteen_distinct_states(
    tmp_path: Path,
) -> None:
    campaign_path = _campaign(tmp_path)
    campaign = verify_campaign(campaign_path)
    assert campaign["requiredModel"] == REQUIRED_MODEL
    assert campaign["oneGenerationPerObjectState"] is True
    assert campaign["independentStateDesignForbidden"] is True
    assert campaign["objectOrder"] == list(ASSET_ORDER)
    assert len(campaign["tasks"]) == 16
    assert len(
        {(task["assetId"], task["stateId"]) for task in campaign["tasks"]}
    ) == 16
    assert campaign["progress"] == {
        "totalObjects": 6,
        "completedObjects": 0,
        "totalTasks": 16,
        "completedTasks": 0,
        "remainingTasks": 16,
    }
    assert campaign["currentTaskId"] == campaign["tasks"][0]["taskId"]
    first = campaign["tasks"][0]
    assert first["assetId"] == "barricade"
    assert first["stateId"] == "intact"
    assert len(first["attempts"]) == 1
    request_path = campaign_path.parent / first["attempts"][0]["request"]["path"]
    request = load_json(request_path)
    assert request["stage"] == "state_definition"
    assert request["requestedStateIds"] == ["intact"]
    assert request["budget"]["maximumWebGenerations"] == 1
    assert request["parentResult"] is None
    prompt = (request_path.parent / request["files"]["prompt"]["path"]).read_text(
        encoding="utf-8"
    )
    assert "Use the `gpt-image-2` image model" in prompt
    assert "State: `intact` only" in prompt
    assert "Do not show intact/damaged/critical comparisons" in prompt
    assert "THIS IS NOT A FOUR-CONCEPT SHEET" in prompt
    assert "Freeze one exact three-bay frame" in prompt
    assert "GAMEPLAY TRUTH BOUNDARY" in prompt
    assert "RUNTIME STATE SCOPE" in prompt
    assert "FINAL OUTPUT SELF-CHECK" in prompt
    assert "random scrap, dirt or decorative diagonal stripes" in prompt
    negatives = (
        request_path.parent / request["files"]["negativeConstraints"]["path"]
    ).read_text(encoding="utf-8")
    assert "No four alternative concepts" in negatives
    assert "No fourth bay, missing foot" in negatives
    assert "No open human-sized passage" in negatives
    assert "No visual claim that exceeds" in negatives


def test_campaign_schema_is_closed_and_valid(tmp_path: Path) -> None:
    campaign_path = _campaign(tmp_path)
    campaign = load_json(campaign_path)
    assert (
        validate_with_schema(
            campaign,
            ROOT / "schemas/precanonical-campaign.schema.json",
        )
        == []
    )
    campaign["unboundedRetry"] = True
    assert validate_with_schema(
        campaign,
        ROOT / "schemas/precanonical-campaign.schema.json",
    )


def test_all_sixteen_gpt_image_prompts_are_state_truth_bound(
    tmp_path: Path,
) -> None:
    operator = CampaignOperatorSession(
        _campaign(tmp_path),
        tmp_path / "runtime",
    )
    tasks = operator.public_state()["campaign"]["tasks"]
    assert len(tasks) == 16
    prompts: dict[tuple[str, str], str] = {}
    for task in tasks:
        prompt = operator.task_prompt(task["taskId"])["submissionText"]
        prompts[(task["assetId"], task["stateId"])] = prompt
        assert "Use the `gpt-image-2` image model" in prompt
        assert "GAMEPLAY TRUTH BOUNDARY" in prompt
        assert "RUNTIME STATE SCOPE" in prompt
        assert "FINAL OUTPUT SELF-CHECK" in prompt
        assert f"State: `{task['stateId']}` only" in prompt
        assert "No visual claim that exceeds" in prompt

    floor_intact = prompts[("floor_module", "intact")].lower()
    floor_damaged = prompts[("floor_module", "damaged")].lower()
    assert "primary generation states for this object:\n  intact, damaged" in (
        floor_intact
    )
    assert "critical state widens" not in floor_intact
    assert "critical state widens" not in floor_damaged
    assert "visual-only damage cue" in floor_damaged

    effect = prompts[("damage_effect", "critical")].lower()
    assert "frozen transient event" in effect
    assert "no physical chassis" in effect
    assert "deep slate chassis" not in effect
    assert "bounded sun-copper repair history" not in effect

    enemy = prompts[("enemy_standard", "critical")].lower()
    assert "exact same dry fracture" in enemy
    assert "adaptive evolution" in enemy
    assert "standardized chassis" not in enemy

    turret = prompts[("turret_fast_v1", "intact")].lower()
    assert "visually ready" in turret
    assert "without claiming an implemented targeting or firing contract" in (
        turret
    )

    barricade = prompts[("barricade", "critical")].lower()
    assert "smaller than a player passage" in barricade
    assert "false collision promise" in barricade


def test_versioned_revision_preserves_prefix_and_restarts_from_new_canon(
    tmp_path: Path,
) -> None:
    source_path = _campaign(tmp_path)
    operator = CampaignOperatorSession(source_path, tmp_path / "runtime")
    for index in range(1, 7):
        operator.import_image(
            f"state-{index:02d}.png",
            _png_bytes(index),
            _attestation(),
            REQUIRED_MODEL,
            True,
        )
        operator.record_review(_review())

    snapshot_campaign_canons(source_path)
    target_path = fork_campaign(
        source_path,
        tmp_path / "revised",
        "salvaged-frontier-states-revised",
        "06-enemy-standard-intact",
        (
            "The accepted standard enemy contradicted the GDD rôdeur role and "
            "must restart from the violet zombie visual canon."
        ),
    )
    source = verify_campaign(source_path)
    revised = verify_campaign(target_path)

    assert source["status"] == "BLOCKED"
    assert source["currentTaskId"] is None
    assert all(task["canon"]["path"].startswith("canons/") for task in source["tasks"])
    assert revised["campaignVersion"] == "2.2.0"
    assert revised["selectionPolicy"]["globalOrderRequired"] is False
    assert revised["selectionPolicy"]["promptAccess"] == "ALL_TASKS"
    assert revised["currentTaskId"] == "06-enemy-standard-intact"
    assert revised["progress"]["completedTasks"] == 5
    assert revised["revision"]["carriedTaskIds"] == [
        "01-barricade-intact",
        "02-barricade-damaged",
        "03-barricade-critical",
        "04-damage-effect-damaged",
        "05-damage-effect-critical",
    ]
    assert revised["revision"]["supersededTaskIds"] == [
        "06-enemy-standard-intact"
    ]
    assert revised["tasks"][0]["status"] == "ACCEPTED"
    assert revised["tasks"][5]["status"] == "READY"

    request_path = (
        target_path.parent / revised["tasks"][5]["attempts"][0]["request"]["path"]
    ).resolve()
    request = load_json(request_path)
    prompt = (request_path.parent / request["files"]["prompt"]["path"]).read_text(
        encoding="utf-8"
    )
    assert "stylized violet zombie" in prompt
    assert "robot or brute" in prompt
    assert "Deep slate chassis, bone-sand" not in prompt
    assert "superseded robot, mech, armored golem" in prompt
    assert "Freeze one exact anatomy" in prompt
    assert "different brace, foot, panel" not in prompt
    negatives = (
        request_path.parent / request["files"]["negativeConstraints"]["path"]
    ).read_text(encoding="utf-8")
    assert "No robot, mech, armor chassis" in negatives
    assert "No giant fists, brute shoulders" in negatives
    assert "reclaimed composite panels" not in negatives
    assert "decorative brace that fails" not in negatives


def test_campaign_operator_requires_visible_gpt_image_2_confirmation(
    tmp_path: Path,
) -> None:
    operator = CampaignOperatorSession(
        _campaign(tmp_path),
        tmp_path / "runtime",
    )
    with pytest.raises(ArtSystemError, match="gpt-image-2"):
        operator.import_image(
            "image.png",
            _png_bytes(1),
            _attestation(),
            None,
            False,
        )
    with pytest.raises(ArtSystemError, match="gpt-image-2"):
        operator.import_image(
            "image.png",
            _png_bytes(1),
            _attestation(),
            "another-model",
            True,
        )


def test_accepted_review_advances_immediately_to_next_state(
    tmp_path: Path,
) -> None:
    campaign_path = _campaign(tmp_path)
    operator = CampaignOperatorSession(campaign_path, tmp_path / "runtime")
    first = operator.public_state()
    assert first["mode"] == "campaign"
    assert first["campaign"]["currentTask"]["stateId"] == "intact"
    imported = operator.import_image(
        "intact.png",
        _png_bytes(1),
        _attestation(),
        REQUIRED_MODEL,
        True,
    )
    assert imported["status"] == "VISUAL_REVIEW_REQUIRED"
    advanced = operator.record_review(_review())
    assert advanced["status"] == "READY_FOR_HUMAN_WEB_SUBMISSION"
    assert advanced["campaign"]["progress"]["completedTasks"] == 1
    assert advanced["campaign"]["currentTask"]["assetId"] == "barricade"
    assert advanced["campaign"]["currentTask"]["stateId"] == "damaged"
    assert len(advanced["attachments"]) == 1
    request = load_json(Path(advanced["request"]["path"]))
    assert request["requestedStateIds"] == ["damaged"]
    assert request["parentResult"] is not None
    assert "accepted previous gameplay state" in advanced["submissionText"]


def test_every_object_state_is_selectable_before_generation(
    tmp_path: Path,
) -> None:
    state = CampaignOperatorSession(
        _campaign(tmp_path),
        tmp_path / "runtime",
    ).public_state()
    tasks = state["campaign"]["tasks"]
    assert len(tasks) == 16
    assert all(task["selectable"] is True for task in tasks)
    assert tasks[0]["generationStatus"] == "TO_GENERATE"
    assert tasks[0]["attemptCount"] == 1
    assert tasks[0]["attempts"][0]["status"] == "READY"
    assert tasks[1]["generationStatus"] == "NOT_GENERATED"
    assert tasks[1]["viewable"] is False
    assert tasks[1]["attempts"] == []
    assert tasks[1]["predecessor"] == {
        "taskId": tasks[0]["taskId"],
        "displayName": tasks[0]["displayName"],
        "stateId": "intact",
        "status": "READY",
    }
    assert [task["taskId"] for task in tasks] == [
        state_task["taskId"]
        for object_summary in state["campaign"]["objects"]
        for state_task in object_summary["states"]
    ]


def test_global_object_order_is_optional_but_state_continuity_is_preserved(
    tmp_path: Path,
) -> None:
    campaign_path = _campaign(tmp_path)
    operator = CampaignOperatorSession(campaign_path, tmp_path / "runtime")
    initial = operator.public_state()
    tasks = initial["campaign"]["tasks"]
    lane_heads = [task for task in tasks if task["predecessorTaskId"] is None]
    assert len(lane_heads) == 6
    assert all(task["generationEligible"] is True for task in lane_heads)
    assert all(task["generationStatus"] == "TO_GENERATE" for task in lane_heads)
    assert initial["campaign"]["selectionPolicy"] == {
        "globalOrderRequired": False,
        "promptAccess": "ALL_TASKS",
        "generationEligibility": "OBJECT_LOCAL_CONTINUITY",
        "activeTaskMutable": True,
    }

    floor = next(
        task
        for task in tasks
        if task["assetId"] == "floor_module" and task["stateId"] == "intact"
    )
    selected = operator.select_task(floor["taskId"])
    assert selected["campaign"]["currentTask"]["taskId"] == floor["taskId"]
    assert selected["status"] == "READY_FOR_HUMAN_WEB_SUBMISSION"
    assert "Floor Module" in selected["submissionText"]
    exact_prompt = operator.task_prompt(floor["taskId"])
    assert exact_prompt["exactTransportPrompt"] is True
    assert exact_prompt["submissionText"] == selected["submissionText"]
    assert (
        exact_prompt["submissionTextSha256"]
        == selected["submissionTextSha256"]
    )

    operator.import_image(
        "floor-intact.png",
        _png_bytes(8),
        _attestation(),
        REQUIRED_MODEL,
        True,
    )
    advanced = operator.record_review(_review())
    assert advanced["campaign"]["progress"]["completedTasks"] == 1
    assert advanced["campaign"]["currentTask"]["assetId"] == "floor_module"
    assert advanced["campaign"]["currentTask"]["stateId"] == "damaged"
    assert len(advanced["attachments"]) == 1
    assert next(
        task
        for task in advanced["campaign"]["tasks"]
        if task["taskId"].startswith("01-barricade-intact")
    )["generationStatus"] == "TO_GENERATE"


def test_every_prompt_is_accessible_without_mutating_campaign_order(
    tmp_path: Path,
) -> None:
    campaign_path = _campaign(tmp_path)
    operator = CampaignOperatorSession(campaign_path, tmp_path / "runtime")
    before_hash = sha256_file(campaign_path)
    tasks = operator.public_state()["campaign"]["tasks"]
    pending = next(
        task
        for task in tasks
        if task["assetId"] == "enemy_standard" and task["stateId"] == "damaged"
    )
    prompt = operator.task_prompt(pending["taskId"])
    assert prompt["previewOnly"] is True
    assert prompt["exactTransportPrompt"] is False
    assert prompt["activationStatus"] == "CONTINUITY_REQUIRED"
    assert "State: `damaged` only" in prompt["submissionText"]
    assert sha256_file(campaign_path) == before_hash
    with pytest.raises(ArtSystemError, match="object-local predecessor"):
        operator.select_task(pending["taskId"])


def test_revision_stays_on_same_state_and_creates_explicit_attempt(
    tmp_path: Path,
) -> None:
    campaign_path = _campaign(tmp_path)
    operator = CampaignOperatorSession(campaign_path, tmp_path / "runtime")
    operator.import_image(
        "intact.png",
        _png_bytes(1),
        _attestation(),
        REQUIRED_MODEL,
        True,
    )
    revised = operator.record_review(_review("REVISION_REQUIRED"))
    current = revised["campaign"]["currentTask"]
    assert current["assetId"] == "barricade"
    assert current["stateId"] == "intact"
    assert current["attemptCount"] == 2
    assert revised["campaign"]["progress"]["completedTasks"] == 0
    assert revised["status"] == "READY_FOR_HUMAN_WEB_SUBMISSION"
    assert len(revised["attachments"]) == 1
    assert "TARGETED REVISION REFERENCE" in revised["submissionText"]
    assert "CORRECT: Clarify the target state" in revised["submissionText"]


def test_attempt_history_remains_browsable_after_revision(
    tmp_path: Path,
) -> None:
    campaign_path = _campaign(tmp_path)
    operator = CampaignOperatorSession(
        campaign_path,
        tmp_path / "runtime",
    )
    first_bytes = _png_bytes(1)
    operator.import_image(
        "intact.png",
        first_bytes,
        _attestation(),
        REQUIRED_MODEL,
        True,
    )
    revised = operator.record_review(_review("REVISION_REQUIRED"))
    task = revised["campaign"]["currentTask"]
    assert task["viewable"] is True
    assert [attempt["status"] for attempt in task["attempts"]] == [
        "REVISION_REQUIRED",
        "READY",
    ]
    assert task["attempts"][0]["viewable"] is True
    assert task["attempts"][1]["viewable"] is False
    campaign_sha256 = sha256_file(campaign_path)
    current_task_id = load_json(campaign_path)["currentTaskId"]
    assert operator.task_image(task["taskId"])[0] == first_bytes
    assert operator.task_image(task["taskId"], 1)[0] == first_bytes
    assert sha256_file(campaign_path) == campaign_sha256
    assert load_json(campaign_path)["currentTaskId"] == current_task_id
    with pytest.raises(ArtSystemError, match="Unknown attempt"):
        operator.task_image(task["taskId"], 99)


def test_rejected_first_state_rebuilds_without_anchoring_rejected_image(
    tmp_path: Path,
) -> None:
    operator = CampaignOperatorSession(
        _campaign(tmp_path),
        tmp_path / "runtime",
    )
    operator.import_image(
        "intact.png",
        _png_bytes(1),
        _attestation(),
        REQUIRED_MODEL,
        True,
    )
    rejected = operator.record_review(_review("REJECTED"))
    assert rejected["campaign"]["currentTask"]["taskId"].startswith(
        "01-barricade-intact"
    )
    assert rejected["campaign"]["currentTask"]["attemptCount"] == 2
    assert rejected["attachments"] == []
    assert "previous attempt was rejected" in rejected["submissionText"]


def test_campaign_completes_only_after_all_sixteen_state_reviews(
    tmp_path: Path,
) -> None:
    campaign_path = _campaign(tmp_path)
    operator = CampaignOperatorSession(campaign_path, tmp_path / "runtime")
    for index in range(1, 17):
        before = operator.public_state()
        assert before["status"] == "READY_FOR_HUMAN_WEB_SUBMISSION"
        assert before["campaign"]["progress"]["completedTasks"] == index - 1
        operator.import_image(
            f"state-{index:02d}.png",
            _png_bytes(index),
            _attestation(),
            REQUIRED_MODEL,
            True,
        )
        after = operator.record_review(_review())
        if index < 16:
            assert after["status"] == "READY_FOR_HUMAN_WEB_SUBMISSION"
            assert after["campaign"]["progress"]["completedTasks"] == index
        else:
            assert after["status"] == "CAMPAIGN_COMPLETE"
            assert after["campaign"]["progress"]["completedTasks"] == 16
            assert after["campaign"]["progress"]["completedObjects"] == 6
            assert after["campaign"]["currentTask"] is None
    campaign = verify_campaign(campaign_path)
    assert campaign["status"] == "COMPLETE"
    assert campaign["currentTaskId"] is None
    assert all(task["status"] == "ACCEPTED" for task in campaign["tasks"])


def test_campaign_http_bridge_exposes_progress_and_advances(
    tmp_path: Path,
) -> None:
    session = CampaignOperatorSession(
        _campaign(tmp_path),
        tmp_path / "runtime",
    )
    server = OperatorHttpServer(("127.0.0.1", 0), session, "campaign-token")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root = f"http://127.0.0.1:{server.server_address[1]}"
    headers = {
        "Content-Type": "application/json",
        "X-Operator-Token": "campaign-token",
    }
    try:
        state_request = urllib.request.Request(
            root + "/api/session",
            headers={"X-Operator-Token": "campaign-token"},
        )
        with urllib.request.urlopen(state_request, timeout=5) as response:
            state = json.loads(response.read())["session"]
        assert state["campaign"]["progress"]["totalTasks"] == 16
        assert state["campaign"]["currentTask"]["stateId"] == "intact"

        import_request = urllib.request.Request(
            root + "/api/import",
            data=json.dumps(
                {
                    "filename": "intact.png",
                    "imageBase64": base64.b64encode(_png_bytes(1)).decode("ascii"),
                    "modelName": REQUIRED_MODEL,
                    "modelNameConfirmed": True,
                    "attestation": _attestation(),
                }
            ).encode("utf-8"),
            method="POST",
            headers=headers,
        )
        with urllib.request.urlopen(import_request, timeout=10) as response:
            imported = json.loads(response.read())["session"]
        assert imported["status"] == "VISUAL_REVIEW_REQUIRED"
        task_id = imported["campaign"]["currentTask"]["taskId"]
        image_request = urllib.request.Request(
            root + f"/api/task-image?taskId={task_id}&attemptIndex=1",
            headers={"X-Operator-Token": "campaign-token"},
        )
        with urllib.request.urlopen(image_request, timeout=5) as response:
            assert response.read() == _png_bytes(1)

        review_request = urllib.request.Request(
            root + "/api/review",
            data=json.dumps(_review()).encode("utf-8"),
            method="POST",
            headers=headers,
        )
        with urllib.request.urlopen(review_request, timeout=10) as response:
            advanced = json.loads(response.read())["session"]
        assert advanced["campaign"]["progress"]["completedTasks"] == 1
        assert advanced["campaign"]["currentTask"]["stateId"] == "damaged"
        assert advanced["status"] == "READY_FOR_HUMAN_WEB_SUBMISSION"
        assert advanced["reviewDefaults"]["preserve"][0] == (
            "Preserve the canonical silhouette and stable anchors."
        )
        assert {
            source["kind"] for source in advanced["reviewDefaults"]["sources"]
        } == {
            "PREVIOUS_ACCEPTED_REVIEW",
            "CANON_STATE_INVARIANTS",
        }
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_campaign_http_bridge_selects_any_eligible_lane_and_exposes_all_prompts(
    tmp_path: Path,
) -> None:
    session = CampaignOperatorSession(
        _campaign(tmp_path),
        tmp_path / "runtime",
    )
    server = OperatorHttpServer(("127.0.0.1", 0), session, "campaign-token")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root = f"http://127.0.0.1:{server.server_address[1]}"
    headers = {
        "Content-Type": "application/json",
        "X-Operator-Token": "campaign-token",
    }
    try:
        state = session.public_state()
        floor = next(
            task
            for task in state["campaign"]["tasks"]
            if task["assetId"] == "floor_module" and task["stateId"] == "intact"
        )
        enemy_damaged = next(
            task
            for task in state["campaign"]["tasks"]
            if task["assetId"] == "enemy_standard" and task["stateId"] == "damaged"
        )
        prompt_request = urllib.request.Request(
            root + f"/api/task-prompt?taskId={enemy_damaged['taskId']}",
            headers={"X-Operator-Token": "campaign-token"},
        )
        with urllib.request.urlopen(prompt_request, timeout=5) as response:
            prompt = json.loads(response.read())["prompt"]
        assert prompt["previewOnly"] is True
        assert prompt["activationStatus"] == "CONTINUITY_REQUIRED"

        select_request = urllib.request.Request(
            root + "/api/select-task",
            data=json.dumps({"taskId": floor["taskId"]}).encode("utf-8"),
            method="POST",
            headers=headers,
        )
        with urllib.request.urlopen(select_request, timeout=5) as response:
            selected = json.loads(response.read())["session"]
        assert selected["campaign"]["currentTask"]["taskId"] == floor["taskId"]
        assert selected["status"] == "READY_FOR_HUMAN_WEB_SUBMISSION"

        blocked_request = urllib.request.Request(
            root + "/api/select-task",
            data=json.dumps({"taskId": enemy_damaged["taskId"]}).encode("utf-8"),
            method="POST",
            headers=headers,
        )
        with pytest.raises(urllib.error.HTTPError) as blocked:
            urllib.request.urlopen(blocked_request, timeout=5)
        assert blocked.value.code == 409
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_campaign_ui_contains_object_state_navigation_and_completion() -> None:
    ui = (ROOT / "tools/art/precanonical-operator.html").read_text(
        encoding="utf-8"
    )
    for text in (
        "Un objet, un état, une génération GPT Image 2",
        "objectList",
        "state-chip",
        "campaignFilter",
        "Pas encore générés",
        "taskBrowser",
        "Explorateur objet × état",
        "Historique des générations",
        "selectedTaskId",
        "previousTask",
        "nextTask",
        "attemptIndex",
        "Consultation et prompts libres",
        "À générer maintenant",
        "Choisis ensuite librement une autre voie disponible",
        "CAMPAIGN_COMPLETE",
        "/api/task-image",
        "/api/task-prompt",
        "/api/select-task",
        "Générer cet état maintenant",
        "Prompt de cet objet × état",
    ):
        assert text in ui
    assert "chip.disabled = !task.viewable" not in ui
    runner = (ROOT / "scripts/art-direction.ps1").read_text(encoding="utf-8")
    assert "precanon-campaign-init" in runner
    assert "precanon-campaign-operator" in runner
    assert "tools.art.precanonical_campaign" in runner
