from __future__ import annotations

import argparse
import base64
import binascii
import json
import mimetypes
import secrets
import threading
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from tools.art.common import (
    ArtSystemError,
    ROOT,
    load_json,
    sha256_bytes,
    sha256_file,
    validate_with_schema,
    write_json,
)
from tools.art.precanonical import (
    ASSESSMENT_KEYS,
    SCHEMAS as PRECANONICAL_SCHEMAS,
    _result_manifests,
    _resolve_binding,
    create_review,
    import_result,
    preflight,
)
from tools.art.precanonical_campaign import (
    REQUIRED_MODEL,
    activate_campaign_task,
    campaign_task_prompt,
    record_import as record_campaign_import,
    record_review_and_advance,
    verify_campaign,
)

SCHEMA_PATH = ROOT / "schemas/precanonical-operator-session.schema.json"
UI_PATH = ROOT / "tools/art/precanonical-operator.html"
MAX_IMAGE_BYTES = 25 * 1024 * 1024
MAX_JSON_BYTES = 36 * 1024 * 1024
CHATGPT_URL = "https://chatgpt.com/"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _binding(path: Path) -> dict[str, str]:
    resolved = path.resolve()
    return {"path": str(resolved), "sha256": sha256_file(resolved)}


def _assert_operator_schema(value: Any) -> None:
    errors = validate_with_schema(value, SCHEMA_PATH)
    if errors:
        raise ArtSystemError(
            "operator session schema validation failed: " + "; ".join(errors)
        )


def _verify_binding(binding: dict[str, str], label: str) -> Path:
    path = Path(binding["path"]).resolve()
    if not path.is_file():
        raise ArtSystemError(f"{label} is missing: {path}")
    if sha256_file(path) != binding["sha256"]:
        raise ArtSystemError(f"{label} hash drift: {path}")
    return path


def _operator_attachments(
    request_path: Path,
    request: dict[str, Any],
) -> list[dict[str, str]]:
    parent = request["parentResult"]
    if parent is None:
        return []
    parent_path = _resolve_binding(request_path, parent)
    parent_result = load_json(parent_path)
    errors = validate_with_schema(
        parent_result,
        PRECANONICAL_SCHEMAS["result"],
    )
    if errors:
        raise ArtSystemError("Parent result is invalid: " + "; ".join(errors))
    attachments: list[dict[str, str]] = []
    for image in parent_result["images"]:
        image_path = (parent_path.parent / image["path"]).resolve()
        if not image_path.is_file() or sha256_file(image_path) != image["sha256"]:
            raise ArtSystemError(
                f"Parent result image binding is stale: {image['path']}"
            )
        attachments.append(_binding(image_path))
    return attachments


def _next_result_identity(
    request_path: Path,
    request_id: str,
) -> tuple[int, str, Path]:
    results_root = request_path.parent.parent.parent / "results"
    existing_count = 0
    for manifest_path in _result_manifests(request_path):
        try:
            result = load_json(manifest_path)
            if (
                not validate_with_schema(
                    result,
                    PRECANONICAL_SCHEMAS["result"],
                )
                and result["requestId"] == request_id
            ):
                existing_count += 1
        except ArtSystemError:
            continue
    generation_index = existing_count + 1
    for identity_index in range(1, 1000):
        result_id = f"{request_id}-result-{identity_index:03d}"
        output = results_root / result_id
        if not output.exists():
            return generation_index, result_id, output.resolve()
    raise ArtSystemError("No bounded result identity remains available")


def _submission_text(prompt: str, negatives: list[str]) -> str:
    lines = [
        prompt.strip(),
        "",
        "STRICT BOUND NEGATIVE CONSTRAINTS",
        *[f"- {item}" for item in negatives],
    ]
    return "\n".join(lines).strip()


def _review_defaults(request_path: Path) -> dict[str, Any]:
    request = load_json(request_path)
    source_brief_path = _resolve_binding(request_path, request["sourceBrief"])
    source_brief = load_json(source_brief_path)
    brief_errors = validate_with_schema(
        source_brief,
        PRECANONICAL_SCHEMAS["brief"],
    )
    if brief_errors:
        raise ArtSystemError(
            "Operator source brief is invalid: " + "; ".join(brief_errors)
        )

    preserve: list[str] = []
    sources: list[dict[str, Any]] = []

    parent = request["parentResult"]
    if parent is not None:
        parent_result_path = _resolve_binding(request_path, parent)
        parent_review_path = parent_result_path.parent / "review.json"
        if parent_review_path.is_file():
            parent_review = load_json(parent_review_path)
            review_errors = validate_with_schema(
                parent_review,
                PRECANONICAL_SCHEMAS["review"],
            )
            if review_errors:
                raise ArtSystemError(
                    "Parent review is invalid: " + "; ".join(review_errors)
                )
            bound_parent = _verify_binding(
                parent_review["result"],
                "Parent review result",
            )
            if bound_parent != parent_result_path:
                raise ArtSystemError(
                    "Parent review is not bound to the continuity result"
                )
            inherited = [
                str(item).strip()
                for item in parent_review["preserve"]
                if str(item).strip()
            ]
            preserve.extend(inherited)
            if inherited:
                sources.append(
                    {
                        "kind": "PREVIOUS_ACCEPTED_REVIEW",
                        "reviewId": parent_review["reviewId"],
                        "count": len(inherited),
                    }
                )

    requested_states = set(request["requestedStateIds"])
    canon_invariants: list[str] = []
    for state in source_brief["states"]:
        if state["id"] not in requested_states:
            continue
        canon_invariants.extend(
            str(item).strip()
            for item in state["invariants"]
            if str(item).strip()
        )
    preserve.extend(canon_invariants)
    if canon_invariants:
        sources.append(
            {
                "kind": "CANON_STATE_INVARIANTS",
                "stateIds": sorted(requested_states),
                "count": len(canon_invariants),
            }
        )

    unique_preserve = list(dict.fromkeys(preserve))
    if not unique_preserve:
        raise ArtSystemError(
            "The bound source brief provides no review invariant to preserve"
        )
    return {
        "preserve": unique_preserve,
        "sources": sources,
        "editable": True,
        "humanConfirmationRequired": True,
    }


def _verify_operator_semantics(value: dict[str, Any]) -> Path:
    request_path = _verify_binding(value["request"], "Operator request")
    preflight_path = _verify_binding(value["preflight"], "Operator preflight")
    request = load_json(request_path)
    request_errors = validate_with_schema(
        request,
        PRECANONICAL_SCHEMAS["request"],
    )
    if request_errors:
        raise ArtSystemError(
            "Operator request is invalid: " + "; ".join(request_errors)
        )
    report = load_json(preflight_path)
    report_errors = validate_with_schema(
        report,
        PRECANONICAL_SCHEMAS["preflight"],
    )
    if report_errors:
        raise ArtSystemError(
            "Operator preflight is invalid: " + "; ".join(report_errors)
        )
    if report["status"] != "PASS":
        raise ArtSystemError("Operator session requires its original PASS preflight")
    if report["request"]["sha256"] != value["request"]["sha256"]:
        raise ArtSystemError("Operator preflight is not bound to the operator request")
    if request["requestId"] != value["requestId"]:
        raise ArtSystemError("Operator requestId differs from the bound request")
    if request["stage"] != value["stage"]:
        raise ArtSystemError("Operator stage differs from the bound request")
    if request["promptHash"] != value["promptHash"]:
        raise ArtSystemError("Operator promptHash differs from the bound request")
    prompt_path = _resolve_binding(request_path, request["files"]["prompt"])
    negatives_path = _resolve_binding(
        request_path,
        request["files"]["negativeConstraints"],
    )
    negatives = [
        line.removeprefix("- ").strip()
        for line in negatives_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    expected_submission = _submission_text(
        prompt_path.read_text(encoding="utf-8").strip(),
        negatives,
    )
    if value["submissionText"] != expected_submission:
        raise ArtSystemError("Operator submission text differs from bound source files")
    if value["submissionTextSha256"] != sha256_bytes(
        expected_submission.encode("utf-8")
    ):
        raise ArtSystemError("Operator submission text hash drift")
    if value["negativeConstraints"] != negatives:
        raise ArtSystemError("Operator negative constraints differ from bound source")
    expected_attachments = _operator_attachments(request_path, request)
    if value["attachments"] != expected_attachments:
        raise ArtSystemError("Operator attachments differ from the bound parent result")
    for attachment in value["attachments"]:
        _verify_binding(attachment, "Operator attachment")
    expected_result_output = (
        request_path.parent.parent.parent
        / "results"
        / value["plannedResultId"]
    ).resolve()
    if Path(value["plannedResultOutput"]).resolve() != expected_result_output:
        raise ArtSystemError("Operator planned result output escapes its request results root")
    if not value["plannedResultId"].startswith(f"{request['requestId']}-result-"):
        raise ArtSystemError("Operator planned result identity differs from request identity")
    if value["plannedReviewId"] != f"{value['plannedResultId']}-review-001":
        raise ArtSystemError("Operator planned review identity is inconsistent")
    if value["result"] is not None:
        result_path = _verify_binding(value["result"], "Operator result")
        if result_path != expected_result_output / "result.json":
            raise ArtSystemError("Operator result binding differs from planned output")
    if value["review"] is not None:
        review_path = _verify_binding(value["review"], "Operator review")
        if review_path != expected_result_output / "review.json":
            raise ArtSystemError("Operator review binding differs from planned output")
    return request_path


def prepare_operator_session(
    request_path: Path,
    output_dir: Path,
) -> Path:
    request_path = request_path.resolve()
    output_dir = output_dir.resolve()
    manifest_path = output_dir / "operator-session.json"
    if manifest_path.is_file():
        session = load_json(manifest_path)
        _assert_operator_schema(session)
        bound_request = _verify_operator_semantics(session)
        if bound_request != request_path:
            raise ArtSystemError(
                "Existing operator session is bound to a different request"
            )
        request = load_json(request_path)
        if request["promptHash"] != session["promptHash"]:
            raise ArtSystemError("Existing operator session prompt hash drift")
        if session["status"] == "READY_FOR_HUMAN_WEB_SUBMISSION":
            current = preflight(request_path)
            if current["status"] != "PASS":
                raise ArtSystemError(
                    "Existing operator session request no longer passes preflight: "
                    + "; ".join(current["blockingReasons"])
                )
        return manifest_path
    if output_dir.exists() and any(output_dir.iterdir()):
        raise ArtSystemError(
            f"Refusing to overwrite non-empty operator directory: {output_dir}"
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    preflight_path = output_dir / "preflight.json"
    report = preflight(request_path, preflight_path)
    if report["status"] != "PASS":
        raise ArtSystemError(
            "Operator preparation requires a current PASS preflight: "
            + "; ".join(report["blockingReasons"])
        )
    request = load_json(request_path)
    request_errors = validate_with_schema(
        request,
        PRECANONICAL_SCHEMAS["request"],
    )
    if request_errors:
        raise ArtSystemError("Request is invalid: " + "; ".join(request_errors))
    prompt_path = _resolve_binding(request_path, request["files"]["prompt"])
    negatives_path = _resolve_binding(
        request_path,
        request["files"]["negativeConstraints"],
    )
    negatives = [
        line.removeprefix("- ").strip()
        for line in negatives_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    prompt = prompt_path.read_text(encoding="utf-8").strip()
    submission = _submission_text(prompt, negatives)
    generation_index, result_id, result_output = _next_result_identity(
        request_path,
        request["requestId"],
    )
    review_id = f"{result_id}-review-001"
    session = {
        "$schema": "https://roblox-top1.local/schemas/precanonical-operator-session.schema.json",
        "schemaVersion": "1.0.0",
        "operatorVersion": "1.0.0",
        "sessionId": f"{request['requestId']}-operator-{generation_index:03d}",
        "createdAt": _utc_now(),
        "updatedAt": _utc_now(),
        "status": "READY_FOR_HUMAN_WEB_SUBMISSION",
        "requestId": request["requestId"],
        "stage": request["stage"],
        "request": _binding(request_path),
        "preflight": _binding(preflight_path),
        "promptHash": request["promptHash"],
        "submissionText": submission,
        "submissionTextSha256": sha256_bytes(submission.encode("utf-8")),
        "negativeConstraints": negatives,
        "attachments": _operator_attachments(request_path, request),
        "imageSpec": request["imageSpec"],
        "chatgptUrl": CHATGPT_URL,
        "plannedGenerationIndex": generation_index,
        "plannedResultId": result_id,
        "plannedResultOutput": str(result_output),
        "plannedReviewId": review_id,
        "humanActions": [
            "Copy the exact bound submission text.",
            "Paste it into an authenticated ChatGPT Web conversation.",
            "Request exactly one image generation and download one result.",
            "Drop the downloaded image into this local operator interface.",
            "Review the imported result in the same interface.",
        ],
        "automatedActions": [
            "Recompute and bind the zero-consumption precanonical preflight.",
            "Compose and hash the exact prompt plus negative constraints.",
            "Validate uploaded image bytes, dimensions and format.",
            "Import immutable result bytes with conservative provenance.",
            "Assign bounded result and review identifiers.",
            "Validate and hash-bind the human review.",
        ],
        "humanAttestation": None,
        "result": None,
        "review": None,
        "reviewDecision": None,
        "browserAutomationUsed": False,
        "apiUsed": False,
        "automaticRetryUsed": False,
        "canonical": False,
        "productionApproved": False,
    }
    _assert_operator_schema(session)
    write_json(manifest_path, session)
    return manifest_path


class OperatorSession:
    def __init__(self, manifest_path: Path):
        self.manifest_path = manifest_path.resolve()
        self._lock = threading.RLock()
        self._load_verified()

    def _load_verified(self) -> dict[str, Any]:
        value = load_json(self.manifest_path)
        _assert_operator_schema(value)
        _verify_operator_semantics(value)
        self.value = value
        return value

    def _save(self) -> None:
        self.value["updatedAt"] = _utc_now()
        _assert_operator_schema(self.value)
        write_json(self.manifest_path, self.value)

    def public_state(self) -> dict[str, Any]:
        with self._lock:
            self._load_verified()
            public = json.loads(json.dumps(self.value))
            request_path = _verify_binding(
                self.value["request"],
                "Operator request",
            )
            public["reviewDefaults"] = _review_defaults(request_path)
            return public

    def import_image(
        self,
        filename: str,
        data: bytes,
        attestation: dict[str, Any],
        model_name: str | None,
        model_name_confirmed: bool,
    ) -> dict[str, Any]:
        with self._lock:
            self._load_verified()
            if self.value["status"] != "READY_FOR_HUMAN_WEB_SUBMISSION":
                raise ArtSystemError("This operator session already imported a result")
            if not data:
                raise ArtSystemError("Uploaded image is empty")
            if len(data) > MAX_IMAGE_BYTES:
                raise ArtSystemError(
                    f"Uploaded image exceeds {MAX_IMAGE_BYTES} bytes"
                )
            required_attestations = (
                "exactSubmissionTextUsed",
                "noPromptRewrite",
                "exactlyOneGenerationRequested",
                "oneResultDownloaded",
                "noAutomaticRetry",
            )
            if any(attestation.get(key) is not True for key in required_attestations):
                raise ArtSystemError(
                    "Every bounded human attestation must be explicitly confirmed"
                )
            suffix = Path(filename).suffix.lower()
            if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
                suffix = ".bin"
            inbox = self.manifest_path.parent / "inbox"
            inbox.mkdir(parents=True, exist_ok=True)
            source = inbox / f"upload-{sha256_bytes(data)[:20]}{suffix}"
            if source.exists():
                raise ArtSystemError("These uploaded bytes were already received")
            source.write_bytes(data)
            request_path = _verify_binding(self.value["request"], "Operator request")
            result_output = Path(self.value["plannedResultOutput"]).resolve()
            try:
                result_path = import_result(
                    request_path,
                    self.value["plannedResultId"],
                    [source],
                    result_output,
                    "manual_download",
                    model_name,
                    model_name_confirmed,
                )
            finally:
                source.unlink(missing_ok=True)
            recorded_attestation = {
                **{key: True for key in required_attestations},
                "surface": "ChatGPT Web / ChatGPT Images",
                "attestedAt": _utc_now(),
            }
            self.value["humanAttestation"] = recorded_attestation
            self.value["result"] = _binding(result_path)
            self.value["status"] = "VISUAL_REVIEW_REQUIRED"
            self._save()
            return self.public_state()

    def record_review(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._load_verified()
            if self.value["status"] != "VISUAL_REVIEW_REQUIRED":
                raise ArtSystemError("A current imported result is required for review")
            result_path = _verify_binding(self.value["result"], "Operator result")
            decision = str(payload.get("decision", ""))
            reviewer_raw = payload.get("reviewer")
            reviewer = str(reviewer_raw).strip() if reviewer_raw else None
            assessment_raw = payload.get("assessment")
            if not isinstance(assessment_raw, dict):
                raise ArtSystemError("Assessment must be an object")
            assessment = {
                key: str(assessment_raw.get(key, "UNKNOWN"))
                for key in ASSESSMENT_KEYS
            }

            def text_list(name: str) -> list[str]:
                value = payload.get(name, [])
                if not isinstance(value, list):
                    raise ArtSystemError(f"{name} must be an array")
                return [
                    str(item).strip()
                    for item in value
                    if str(item).strip()
                ]

            review_path = result_path.parent / "review.json"
            if review_path.exists():
                raise ArtSystemError("A review already exists for this result")
            review = create_review(
                result_path,
                self.value["plannedReviewId"],
                decision,
                review_path,
                assessment,
                reviewer,
                text_list("preserve"),
                text_list("correct"),
                text_list("forbidNext"),
            )
            self.value["review"] = _binding(review_path)
            self.value["reviewDecision"] = review["decision"]
            self.value["status"] = "REVIEW_RECORDED"
            self._save()
            return self.public_state()

    def result_image(self) -> tuple[bytes, str]:
        with self._lock:
            self._load_verified()
            if self.value["result"] is None:
                raise ArtSystemError("No imported result image is available")
            result_path = _verify_binding(self.value["result"], "Operator result")
            result = load_json(result_path)
            image_path = (result_path.parent / result["images"][0]["path"]).resolve()
            if not image_path.is_file():
                raise ArtSystemError("Imported result image is missing")
            mime_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
            return image_path.read_bytes(), mime_type


class CampaignOperatorSession:
    def __init__(self, campaign_path: Path, runtime_dir: Path):
        self.campaign_path = campaign_path.resolve()
        self.runtime_dir = runtime_dir.resolve()
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        verify_campaign(self.campaign_path)
        self._reconcile()

    def _campaign_binding_path(self, binding: dict[str, str]) -> Path:
        raw = Path(binding["path"])
        path = raw.resolve() if raw.is_absolute() else (
            self.campaign_path.parent / raw
        ).resolve()
        if not path.is_file():
            raise ArtSystemError(f"Campaign binding is missing: {path}")
        if sha256_file(path) != binding["sha256"]:
            raise ArtSystemError(f"Campaign binding hash drift: {path}")
        return path

    def _current_task(
        self,
        campaign: dict[str, Any],
    ) -> dict[str, Any] | None:
        current_id = campaign["currentTaskId"]
        if current_id is None:
            return None
        for task in campaign["tasks"]:
            if task["taskId"] == current_id:
                return task
        raise ArtSystemError(f"Campaign current task is missing: {current_id}")

    def _active_operator(
        self,
        campaign: dict[str, Any],
    ) -> OperatorSession | None:
        task = self._current_task(campaign)
        if task is None:
            return None
        if not task["attempts"]:
            raise ArtSystemError(f"Campaign task has no active attempt: {task['taskId']}")
        request_path = self._campaign_binding_path(task["attempts"][-1]["request"])
        output = self.runtime_dir / "sessions" / request_path.parent.name
        manifest = prepare_operator_session(request_path, output)
        return OperatorSession(manifest)

    def _reconcile(self) -> None:
        for _ in range(3):
            campaign = verify_campaign(self.campaign_path)
            operator = self._active_operator(campaign)
            if operator is None:
                return
            task = self._current_task(campaign)
            if task is None:
                return
            state = operator.public_state()
            if (
                state["status"] == "VISUAL_REVIEW_REQUIRED"
                and task["status"] == "READY"
                and state["result"] is not None
            ):
                record_campaign_import(
                    self.campaign_path,
                    Path(state["result"]["path"]),
                )
                continue
            if (
                state["status"] == "REVIEW_RECORDED"
                and task["status"] == "VISUAL_REVIEW_REQUIRED"
                and state["review"] is not None
            ):
                record_review_and_advance(
                    self.campaign_path,
                    Path(state["review"]["path"]),
                )
                continue
            return
        raise ArtSystemError("Campaign/operator reconciliation did not converge")

    def _attempt_summary(
        self,
        task: dict[str, Any],
        attempt: dict[str, Any],
    ) -> dict[str, Any]:
        request_path = self._campaign_binding_path(attempt["request"])
        request = load_json(request_path)
        result = attempt["result"]
        review = attempt["review"]
        decision = attempt["decision"]
        is_accepted = (
            result is not None
            and task["acceptedResult"] is not None
            and result == task["acceptedResult"]
        )
        if is_accepted:
            status = "ACCEPTED"
        elif decision == "REVISION_REQUIRED":
            status = "REVISION_REQUIRED"
        elif decision == "REJECTED":
            status = "REJECTED"
        elif result is not None and review is None:
            status = "VISUAL_REVIEW_REQUIRED"
        elif result is None:
            status = "READY"
        else:
            status = "REVIEW_RECORDED"
        if attempt["revisionSource"] is not None:
            source_kind = "REVISION"
        elif attempt["continuitySource"] is not None:
            source_kind = "CONTINUITY"
        else:
            source_kind = "CANON"
        return {
            "attemptIndex": attempt["attemptIndex"],
            "requestId": request["requestId"],
            "promptHash": request["promptHash"],
            "status": status,
            "decision": decision,
            "sourceKind": source_kind,
            "hasResult": result is not None,
            "hasReview": review is not None,
            "viewable": result is not None,
            "isAccepted": is_accepted,
            "resultSha256": result["sha256"] if result is not None else None,
            "reviewSha256": review["sha256"] if review is not None else None,
        }

    def _task_summary(
        self,
        task: dict[str, Any],
        campaign: dict[str, Any],
    ) -> dict[str, Any]:
        attempts = [
            self._attempt_summary(task, attempt)
            for attempt in task["attempts"]
        ]
        if task["status"] == "ACCEPTED":
            generation_status = "ACCEPTED"
        elif task["status"] == "VISUAL_REVIEW_REQUIRED":
            generation_status = "TO_REVIEW"
        elif task["status"] == "READY":
            generation_status = "TO_GENERATE"
        elif task["status"] == "BLOCKED":
            generation_status = "BLOCKED"
        else:
            generation_status = "NOT_GENERATED"
        predecessor_id = task["predecessorTaskId"]
        predecessor_accepted = predecessor_id is None
        if predecessor_id is not None:
            predecessor = next(
                item
                for item in campaign["tasks"]
                if item["taskId"] == predecessor_id
            )
            predecessor_accepted = predecessor["status"] == "ACCEPTED"
        generation_eligible = (
            task["status"] in {"PENDING", "READY"}
            and predecessor_accepted
        )
        activation_eligible = (
            generation_eligible
            or task["status"] == "VISUAL_REVIEW_REQUIRED"
        )
        return {
            "taskId": task["taskId"],
            "ordinal": task["ordinal"],
            "objectOrdinal": task["objectOrdinal"],
            "assetId": task["assetId"],
            "displayName": task["displayName"],
            "stateId": task["stateId"],
            "stateOrdinal": task["stateOrdinal"],
            "stateCount": task["stateCount"],
            "predecessorTaskId": task["predecessorTaskId"],
            "status": task["status"],
            "generationStatus": generation_status,
            "attemptCount": len(task["attempts"]),
            "attempts": attempts,
            "acceptedDecision": (
                next(
                    (
                        attempt["decision"]
                        for attempt in reversed(attempts)
                        if attempt["isAccepted"]
                    ),
                    None,
                )
                if task["status"] == "ACCEPTED"
                else None
            ),
            "latestDecision": (
                next(
                    (
                        attempt["decision"]
                        for attempt in reversed(attempts)
                        if attempt["decision"] is not None
                    ),
                    None,
                )
            ),
            "viewable": any(attempt["viewable"] for attempt in attempts),
            "selectable": True,
            "promptAccessible": True,
            "generationEligible": generation_eligible,
            "activationEligible": activation_eligible,
        }

    def _campaign_ui(
        self,
        campaign: dict[str, Any],
    ) -> dict[str, Any]:
        objects: list[dict[str, Any]] = []
        summaries = {
            task["taskId"]: self._task_summary(task, campaign)
            for task in campaign["tasks"]
        }
        for task in campaign["tasks"]:
            summary = summaries[task["taskId"]]
            predecessor_id = task["predecessorTaskId"]
            if predecessor_id is None:
                summary["predecessor"] = None
            else:
                predecessor = summaries[predecessor_id]
                summary["predecessor"] = {
                    "taskId": predecessor["taskId"],
                    "displayName": predecessor["displayName"],
                    "stateId": predecessor["stateId"],
                    "status": predecessor["status"],
                }
        for asset_id in campaign["objectOrder"]:
            states = [
                summaries[task["taskId"]]
                for task in campaign["tasks"]
                if task["assetId"] == asset_id
            ]
            if all(item["status"] == "ACCEPTED" for item in states):
                status = "COMPLETE"
            elif any(
                item["status"] in {"READY", "VISUAL_REVIEW_REQUIRED", "BLOCKED"}
                for item in states
            ):
                status = "ACTIVE"
            else:
                status = "PENDING"
            objects.append(
                {
                    "assetId": asset_id,
                    "displayName": states[0]["displayName"],
                    "objectOrdinal": states[0]["objectOrdinal"],
                    "status": status,
                    "states": states,
                }
            )
        current = self._current_task(campaign)
        next_task = None
        if current is not None:
            next_task = next(
                (
                    task
                    for task in campaign["tasks"]
                    if task["assetId"] == current["assetId"]
                    and task["stateOrdinal"] == current["stateOrdinal"] + 1
                ),
                None,
            )
            if next_task is None:
                next_task = next(
                    (
                        task
                        for task in campaign["tasks"]
                        if task["taskId"] != current["taskId"]
                        and task["status"] in {"READY", "VISUAL_REVIEW_REQUIRED"}
                    ),
                    None,
                )
        return {
            "campaignId": campaign["campaignId"],
            "status": campaign["status"],
            "requiredModel": campaign["requiredModel"],
            "progress": campaign["progress"],
            "objects": objects,
            "tasks": [
                summaries[task["taskId"]]
                for task in campaign["tasks"]
            ],
            "currentTask": (
                summaries[current["taskId"]]
                if current is not None
                else None
            ),
            "nextTask": (
                summaries[next_task["taskId"]]
                if next_task is not None
                else None
            ),
            "maxAttemptsPerTask": campaign["maxAttemptsPerTask"],
            "selectionPolicy": campaign.get("selectionPolicy"),
        }

    def public_state(self) -> dict[str, Any]:
        with self._lock:
            self._reconcile()
            campaign = verify_campaign(self.campaign_path)
            campaign_ui = self._campaign_ui(campaign)
            operator = self._active_operator(campaign)
            if operator is None:
                return {
                    "mode": "campaign",
                    "status": "CAMPAIGN_COMPLETE",
                    "chatgptUrl": CHATGPT_URL,
                    "campaign": campaign_ui,
                    "canonical": False,
                    "productionApproved": False,
                }
            state = operator.public_state()
            state["mode"] = "campaign"
            state["campaign"] = campaign_ui
            return state

    def import_image(
        self,
        filename: str,
        data: bytes,
        attestation: dict[str, Any],
        model_name: str | None,
        model_name_confirmed: bool,
    ) -> dict[str, Any]:
        with self._lock:
            if model_name != REQUIRED_MODEL or not model_name_confirmed:
                raise ArtSystemError(
                    f"This campaign requires visible UI confirmation of {REQUIRED_MODEL}"
                )
            campaign = verify_campaign(self.campaign_path)
            operator = self._active_operator(campaign)
            if operator is None:
                raise ArtSystemError("The campaign is already complete")
            state = operator.import_image(
                filename,
                data,
                attestation,
                model_name,
                model_name_confirmed,
            )
            if state["result"] is None:
                raise ArtSystemError("Operator import did not produce a result binding")
            record_campaign_import(
                self.campaign_path,
                Path(state["result"]["path"]),
            )
            return self.public_state()

    def record_review(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            campaign = verify_campaign(self.campaign_path)
            operator = self._active_operator(campaign)
            if operator is None:
                raise ArtSystemError("The campaign is already complete")
            state = operator.record_review(payload)
            if state["review"] is None:
                raise ArtSystemError("Operator review did not produce a review binding")
            record_review_and_advance(
                self.campaign_path,
                Path(state["review"]["path"]),
            )
            return self.public_state()

    def select_task(self, task_id: str) -> dict[str, Any]:
        with self._lock:
            self._reconcile()
            activate_campaign_task(self.campaign_path, task_id)
            return self.public_state()

    def task_prompt(self, task_id: str) -> dict[str, Any]:
        with self._lock:
            self._reconcile()
            return campaign_task_prompt(self.campaign_path, task_id)

    def result_image(self) -> tuple[bytes, str]:
        with self._lock:
            campaign = verify_campaign(self.campaign_path)
            operator = self._active_operator(campaign)
            if operator is None:
                raise ArtSystemError("No active campaign result is available")
            return operator.result_image()

    def task_image(
        self,
        task_id: str,
        attempt_index: int | None = None,
    ) -> tuple[bytes, str]:
        with self._lock:
            campaign = verify_campaign(self.campaign_path)
            task = next(
                (item for item in campaign["tasks"] if item["taskId"] == task_id),
                None,
            )
            if task is None:
                raise ArtSystemError(f"Unknown campaign task: {task_id}")
            if attempt_index is None:
                result_binding = task["acceptedResult"]
                if result_binding is None:
                    result_binding = next(
                        (
                            attempt["result"]
                            for attempt in reversed(task["attempts"])
                            if attempt["result"] is not None
                        ),
                        None,
                    )
            else:
                attempt = next(
                    (
                        item
                        for item in task["attempts"]
                        if item["attemptIndex"] == attempt_index
                    ),
                    None,
                )
                if attempt is None:
                    raise ArtSystemError(
                        f"Unknown attempt {attempt_index} for campaign task {task_id}"
                    )
                result_binding = attempt["result"]
            if result_binding is None:
                raise ArtSystemError(
                    "This campaign task attempt has no imported image"
                )
            result_path = self._campaign_binding_path(result_binding)
            result = load_json(result_path)
            errors = validate_with_schema(
                result,
                PRECANONICAL_SCHEMAS["result"],
            )
            if errors:
                raise ArtSystemError(
                    "Campaign task result is invalid: " + "; ".join(errors)
                )
            image_path = (result_path.parent / result["images"][0]["path"]).resolve()
            if not image_path.is_file():
                raise ArtSystemError("Campaign task image is missing")
            if sha256_file(image_path) != result["images"][0]["sha256"]:
                raise ArtSystemError("Campaign task image hash drift")
            mime_type = (
                mimetypes.guess_type(image_path.name)[0]
                or "application/octet-stream"
            )
            return image_path.read_bytes(), mime_type


class OperatorHttpServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        address: tuple[str, int],
        session: OperatorSession | CampaignOperatorSession,
        token: str,
    ):
        super().__init__(address, OperatorRequestHandler)
        self.operator_session = session
        self.operator_token = token


class OperatorRequestHandler(BaseHTTPRequestHandler):
    server: OperatorHttpServer

    def log_message(self, format: str, *args: Any) -> None:
        print(f"[operator] {self.address_string()} {format % args}")

    def _security_headers(self, content_type: str) -> None:
        self.send_header("Content-Type", content_type)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data: blob:; style-src 'unsafe-inline'; "
            "script-src 'unsafe-inline'; connect-src 'self'; base-uri 'none'; "
            "frame-ancestors 'none'; form-action 'self'",
        )

    def _authorized(self) -> bool:
        return secrets.compare_digest(
            self.headers.get("X-Operator-Token", ""),
            self.server.operator_token,
        )

    def _send_json(self, status: int, value: Any) -> None:
        body = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self._security_headers("application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status: int, message: str) -> None:
        self._send_json(status, {"ok": False, "error": message})

    def _read_json(self) -> dict[str, Any]:
        raw_length = self.headers.get("Content-Length")
        if raw_length is None:
            raise ArtSystemError("Content-Length is required")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ArtSystemError("Invalid Content-Length") from exc
        if length < 1 or length > MAX_JSON_BYTES:
            raise ArtSystemError("Request body size is outside the allowed range")
        try:
            value = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ArtSystemError(f"Invalid JSON body: {exc}") from exc
        if not isinstance(value, dict):
            raise ArtSystemError("JSON body must be an object")
        return value

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            body = UI_PATH.read_bytes()
            self.send_response(HTTPStatus.OK)
            self._security_headers("text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if not self._authorized():
            self._send_error_json(HTTPStatus.UNAUTHORIZED, "Invalid operator token")
            return
        try:
            if parsed.path == "/api/session":
                self._send_json(
                    HTTPStatus.OK,
                    {"ok": True, "session": self.server.operator_session.public_state()},
                )
                return
            if parsed.path == "/api/result-image":
                data, mime_type = self.server.operator_session.result_image()
                self.send_response(HTTPStatus.OK)
                self._security_headers(mime_type)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if parsed.path == "/api/task-image":
                task_id = parse_qs(parsed.query).get("taskId", [""])[0]
                if not task_id:
                    raise ArtSystemError("taskId is required")
                raw_attempt = parse_qs(parsed.query).get("attemptIndex", [""])[0]
                attempt_index = None
                if raw_attempt:
                    try:
                        attempt_index = int(raw_attempt)
                    except ValueError as exc:
                        raise ArtSystemError(
                            "attemptIndex must be an integer"
                        ) from exc
                    if attempt_index < 1:
                        raise ArtSystemError(
                            "attemptIndex must be greater than zero"
                        )
                if not isinstance(
                    self.server.operator_session,
                    CampaignOperatorSession,
                ):
                    raise ArtSystemError("Task images require campaign mode")
                data, mime_type = self.server.operator_session.task_image(
                    task_id,
                    attempt_index,
                )
                self.send_response(HTTPStatus.OK)
                self._security_headers(mime_type)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            if parsed.path == "/api/task-prompt":
                task_id = parse_qs(parsed.query).get("taskId", [""])[0]
                if not task_id:
                    raise ArtSystemError("taskId is required")
                if not isinstance(
                    self.server.operator_session,
                    CampaignOperatorSession,
                ):
                    raise ArtSystemError("Task prompts require campaign mode")
                self._send_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "prompt": self.server.operator_session.task_prompt(task_id),
                    },
                )
                return
            self._send_error_json(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        except ArtSystemError as exc:
            self._send_error_json(HTTPStatus.CONFLICT, str(exc))

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if not self._authorized():
            self._send_error_json(HTTPStatus.UNAUTHORIZED, "Invalid operator token")
            return
        try:
            if parsed.path == "/api/import":
                payload = self._read_json()
                encoded = payload.get("imageBase64")
                if not isinstance(encoded, str):
                    raise ArtSystemError("imageBase64 is required")
                try:
                    data = base64.b64decode(encoded, validate=True)
                except (ValueError, binascii.Error) as exc:
                    raise ArtSystemError("Uploaded image base64 is invalid") from exc
                state = self.server.operator_session.import_image(
                    str(payload.get("filename", "downloaded-image")),
                    data,
                    payload.get("attestation", {}),
                    (
                        str(payload["modelName"]).strip()
                        if payload.get("modelName")
                        else None
                    ),
                    payload.get("modelNameConfirmed") is True,
                )
                self._send_json(HTTPStatus.OK, {"ok": True, "session": state})
                return
            if parsed.path == "/api/review":
                state = self.server.operator_session.record_review(self._read_json())
                self._send_json(HTTPStatus.OK, {"ok": True, "session": state})
                return
            if parsed.path == "/api/select-task":
                if not isinstance(
                    self.server.operator_session,
                    CampaignOperatorSession,
                ):
                    raise ArtSystemError("Task selection requires campaign mode")
                task_id = self._read_json().get("taskId")
                if not isinstance(task_id, str) or not task_id:
                    raise ArtSystemError("taskId is required")
                state = self.server.operator_session.select_task(task_id)
                self._send_json(HTTPStatus.OK, {"ok": True, "session": state})
                return
            if parsed.path == "/api/close":
                self._send_json(HTTPStatus.OK, {"ok": True})
                threading.Thread(
                    target=self.server.shutdown,
                    daemon=True,
                ).start()
                return
            self._send_error_json(HTTPStatus.NOT_FOUND, "Unknown endpoint")
        except ArtSystemError as exc:
            self._send_error_json(HTTPStatus.CONFLICT, str(exc))
        except Exception as exc:
            self._send_error_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Unexpected operator error: {exc}",
            )


def serve_operator(
    manifest_path: Path,
    host: str,
    port: int,
    open_browser: bool,
    idle_timeout_minutes: int,
) -> None:
    if host not in {"127.0.0.1", "localhost"}:
        raise ArtSystemError("Operator server must bind to loopback")
    session = OperatorSession(manifest_path)
    token = secrets.token_urlsafe(32)
    server = OperatorHttpServer((host, port), session, token)
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}/#{token}"
    print(f"[PASS] Precanonical operator ready: {url}")
    print("[INFO] The server is loopback-only and stores no browser credentials.")
    if idle_timeout_minutes > 0:
        timer = threading.Timer(
            idle_timeout_minutes * 60,
            server.shutdown,
        )
        timer.daemon = True
        timer.start()
    else:
        timer = None
    if open_browser:
        webbrowser.open(url, new=2)
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        if timer is not None:
            timer.cancel()
        server.server_close()
        print("[PASS] Precanonical operator stopped.")


def serve_campaign_operator(
    campaign_path: Path,
    runtime_dir: Path,
    host: str,
    port: int,
    open_browser: bool,
    idle_timeout_minutes: int,
) -> None:
    if host not in {"127.0.0.1", "localhost"}:
        raise ArtSystemError("Operator server must bind to loopback")
    session = CampaignOperatorSession(campaign_path, runtime_dir)
    token = secrets.token_urlsafe(32)
    server = OperatorHttpServer((host, port), session, token)
    actual_port = server.server_address[1]
    url = f"http://127.0.0.1:{actual_port}/#{token}"
    print(f"[PASS] Precanonical campaign operator ready: {url}")
    print(
        "[INFO] One gpt-image-2 generation is required for each of the "
        "sixteen object-state tasks."
    )
    if idle_timeout_minutes > 0:
        timer = threading.Timer(
            idle_timeout_minutes * 60,
            server.shutdown,
        )
        timer.daemon = True
        timer.start()
    else:
        timer = None
    if open_browser:
        webbrowser.open(url, new=2)
    try:
        server.serve_forever(poll_interval=0.25)
    finally:
        if timer is not None:
            timer.cancel()
        server.server_close()
        print("[PASS] Precanonical campaign operator stopped.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Loopback-only human bridge for bounded ChatGPT Web image generation."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument("--request", type=Path, required=True)
    prepare_parser.add_argument("--output", type=Path, required=True)

    serve_parser = subparsers.add_parser("serve")
    serve_parser.add_argument("--request", type=Path, required=True)
    serve_parser.add_argument("--output", type=Path, required=True)
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=0)
    serve_parser.add_argument("--open", action="store_true")
    serve_parser.add_argument("--idle-timeout-minutes", type=int, default=120)

    prepare_campaign_parser = subparsers.add_parser("prepare-campaign")
    prepare_campaign_parser.add_argument("--campaign", type=Path, required=True)
    prepare_campaign_parser.add_argument("--output", type=Path, required=True)

    serve_campaign_parser = subparsers.add_parser("serve-campaign")
    serve_campaign_parser.add_argument("--campaign", type=Path, required=True)
    serve_campaign_parser.add_argument("--output", type=Path, required=True)
    serve_campaign_parser.add_argument("--host", default="127.0.0.1")
    serve_campaign_parser.add_argument("--port", type=int, default=0)
    serve_campaign_parser.add_argument("--open", action="store_true")
    serve_campaign_parser.add_argument("--idle-timeout-minutes", type=int, default=120)

    args = parser.parse_args()
    try:
        if args.command in {"prepare-campaign", "serve-campaign"}:
            session = CampaignOperatorSession(args.campaign, args.output)
            state = session.public_state()
            progress = state["campaign"]["progress"]
            print(
                "[PASS] Precanonical campaign operator prepared: "
                f"{progress['completedTasks']}/{progress['totalTasks']} accepted"
            )
            if args.command == "prepare-campaign":
                return 0
            serve_campaign_operator(
                args.campaign,
                args.output,
                args.host,
                args.port,
                args.open,
                args.idle_timeout_minutes,
            )
            return 0
        manifest = prepare_operator_session(args.request, args.output)
        print(f"[PASS] Precanonical operator session: {manifest}")
        if args.command == "prepare":
            return 0
        serve_operator(
            manifest,
            args.host,
            args.port,
            args.open,
            args.idle_timeout_minutes,
        )
        return 0
    except ArtSystemError as exc:
        print(f"[FAIL] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
