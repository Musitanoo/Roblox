from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from PIL import Image

from tools.art import precanonical as precanonical_module
from tools.art.common import (
    ArtSystemError,
    PROJECT_ROOT,
    ROOT,
    load_json,
    validate_with_schema,
)
from tools.art.precanonical import (
    ASSESSMENT_KEYS,
    browser_doctor,
    create_handoff,
    create_review,
    import_result,
    init_packet,
    preflight,
    status,
)

BRIEF = ROOT / "art/precanonical/examples/defense-barricade-small-brief.json"


def _packet(
    tmp_path: Path,
    request_id: str = "test-web-001",
    maximum: int = 4,
    browser_adapter: str = "codex_chrome",
) -> Path:
    return init_packet(
        BRIEF,
        request_id,
        tmp_path
        / "asset"
        / "precanonical"
        / "requests"
        / request_id,
        "exploration",
        maximum,
        True,
        False,
        browser_adapter=browser_adapter,
    )


def _image(path: Path, color: tuple[int, int, int] = (45, 55, 60)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (256, 256), color).save(path, format="PNG")
    return path


def _assessment(value: str = "PASS") -> dict[str, str]:
    return {key: value for key in ASSESSMENT_KEYS}


def _browser_report(
    tmp_path: Path,
    browser_adapter: str = "codex_chrome",
) -> Path:
    backend = "chrome" if browser_adapter == "codex_chrome" else "iab"
    report = {
        "$schema": "https://roblox-top1.local/schemas/precanonical-browser-doctor.schema.json",
        "schemaVersion": "1.0.0",
        "generatedAt": "2026-07-16T00:00:00Z",
        "browserAdapter": browser_adapter,
        "requiredBackend": backend,
        "requiredTaskTool": "mcp__node_repl__js",
        "status": "BLOCKED",
        "localInstallationStatus": "PASS",
        "currentTaskToolExposureStatus": "UNKNOWN",
        "repositoryCanLaunchBrowser": False,
        "submissionReady": False,
        "checks": [
            {"id": "codex_config", "status": "PASS", "detail": "Config present."},
            {"id": "selected_plugin", "status": "PASS", "detail": "Plugin present."},
            {
                "id": "selected_plugin_enabled",
                "status": "PASS",
                "detail": "Plugin enabled.",
            },
            {
                "id": "node_repl_configured",
                "status": "PASS",
                "detail": "node_repl configured.",
            },
            {
                "id": "selected_backend_declared",
                "status": "PASS",
                "detail": "Backend declared.",
            },
            {
                "id": "node_repl_tools",
                "status": "PASS",
                "detail": "js tool exposed by MCP server.",
            },
            {
                "id": "chrome_native_host",
                "status": "PASS" if browser_adapter == "codex_chrome" else "SKIP",
                "detail": "Native host applicable state recorded.",
            },
            {
                "id": "current_task_tool_exposure",
                "status": "UNKNOWN",
                "detail": "Task-scoped capability is not locally provable.",
            },
        ],
        "exposedNodeReplTools": ["js", "js_add_node_module_dir", "js_reset"],
        "blockingReasons": [
            "Current-task exposure of mcp__node_repl__js remains UNKNOWN outside the Codex host."
        ],
        "recommendedAction": (
            "Use a fresh Codex task that visibly exposes mcp__node_repl__js "
            "before any browser submission."
        ),
        "productionApproved": False,
    }
    assert (
        validate_with_schema(
            report,
            ROOT / "schemas/precanonical-browser-doctor.schema.json",
        )
        == []
    )
    path = tmp_path / f"{browser_adapter}-browser-doctor.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path


def test_precanonical_policy_and_reference_brief_are_schema_valid() -> None:
    policy = load_json(ROOT / "art/precanonical/policy.json")
    brief = load_json(BRIEF)
    assert (
        validate_with_schema(
            policy, ROOT / "schemas/precanonical-policy.schema.json"
        )
        == []
    )
    assert (
        validate_with_schema(
            brief, ROOT / "schemas/precanonical-brief.schema.json"
        )
        == []
    )
    assert policy["selectedArtDirection"] == "salvaged-frontier"
    assert policy["fallbackPolicy"] == {
        "codexImagegenAutomatic": False,
        "apiAutomatic": False,
        "silentRetry": False,
        "unboundedRegeneration": False,
        "browserAdapterAutomatic": False,
    }
    assert policy["providerContract"]["allowedBrowserAdapters"] == [
        "codex_chrome",
        "codex_iab",
    ]
    assert (
        policy["providerContract"]["attachmentCapableBrowserAdapter"]
        == "codex_chrome"
    )
    assert (
        policy["providerContract"]["attachmentlessFallbackBrowserAdapter"]
        == "codex_iab"
    )
    assert policy["providerContract"]["taskScopedCapability"] is True
    assert policy["providerContract"]["repositoryLaunchable"] is False
    assert policy["providerContract"]["requiredTaskTool"] == "mcp__node_repl__js"
    assert policy["providerContract"]["localInstallationProvesTaskExposure"] is False
    assert policy["providerContract"]["humanOperatorBridgeAllowed"] is True
    assert (
        policy["providerContract"]["humanOperatorBridgeRequiresTaskTool"] is False
    )
    assert policy["providerContract"]["humanOperatorBridgeLoopbackOnly"] is True
    assert (
        policy["providerContract"]["humanOperatorBridgeRequiresBoundAttestation"]
        is True
    )


def test_request_compilation_is_deterministic(tmp_path: Path) -> None:
    first = _packet(tmp_path / "a")
    second = _packet(tmp_path / "b")
    first_root = first.parent
    second_root = second.parent
    assert {
        path.relative_to(first_root).as_posix(): path.read_bytes()
        for path in first_root.rglob("*")
        if path.is_file()
    } == {
        path.relative_to(second_root).as_posix(): path.read_bytes()
        for path in second_root.rglob("*")
        if path.is_file()
    }


def test_preflight_passes_without_consuming_quota(tmp_path: Path) -> None:
    request = _packet(tmp_path)
    report = preflight(request, tmp_path / "preflight.json")
    assert report["status"] == "PASS"
    assert report["nextState"] == "WEB_PREFLIGHT_PASS"
    assert report["remainingGenerations"] == 4
    assert report["quotaRemaining"] == "UNKNOWN"
    assert report["consumesQuota"] is False
    assert report["productionApproved"] is False


def test_preflight_rejects_stale_prompt_hash(tmp_path: Path) -> None:
    request = _packet(tmp_path)
    (request.parent / "prompt.txt").write_text(
        "silently changed prompt\n", encoding="utf-8"
    )
    report = preflight(request)
    assert report["status"] == "FAIL"
    assert any("hash drift" in reason for reason in report["blockingReasons"])


def test_browser_doctor_separates_local_runtime_from_task_capability(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    codex_home = tmp_path / ".codex"
    plugin_dir = (
        codex_home
        / "plugins/cache/openai-bundled/browser/26.707.91948"
    )
    plugin_dir.mkdir(parents=True)
    executable = tmp_path / "node_repl.exe"
    executable.write_bytes(b"test")
    (codex_home / "config.toml").write_text(
        "\n".join(
            (
                '[plugins."browser@openai-bundled"]',
                "enabled = true",
                "",
                "[mcp_servers.node_repl]",
                f'command = "{executable.as_posix()}"',
                "",
                "[mcp_servers.node_repl.env]",
                'BROWSER_USE_AVAILABLE_BACKENDS = "chrome,iab"',
                "",
            )
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        precanonical_module,
        "_probe_node_repl_tools",
        lambda _executable, _environment: (
            True,
            ["js", "js_add_node_module_dir", "js_reset"],
            "node_repl exposes the required js MCP tool.",
        ),
    )
    report = browser_doctor("codex_iab", codex_home=codex_home)
    assert report["status"] == "BLOCKED"
    assert report["localInstallationStatus"] == "PASS"
    assert report["currentTaskToolExposureStatus"] == "UNKNOWN"
    assert report["repositoryCanLaunchBrowser"] is False
    assert report["submissionReady"] is False
    assert any(
        check["id"] == "current_task_tool_exposure"
        and check["status"] == "UNKNOWN"
        for check in report["checks"]
    )


def test_node_repl_probe_sanitizes_inherited_and_configured_secrets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, str] = {}

    def fake_run(*_args: object, **kwargs: object) -> object:
        observed.update(kwargs["env"])
        return precanonical_module.subprocess.CompletedProcess(
            args=["node_repl.exe"],
            returncode=0,
            stdout=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "result": {"tools": [{"name": "js"}]},
                }
            ),
            stderr="",
        )

    monkeypatch.setenv("OPENAI_API_KEY", "must-not-reach-node")
    monkeypatch.setenv("ROBLOX_OPEN_CLOUD_API_KEY", "must-not-reach-node")
    monkeypatch.setattr(precanonical_module.subprocess, "run", fake_run)

    passed, tools, _detail = precanonical_module._probe_node_repl_tools(
        tmp_path / "node_repl.exe",
        {
            "BROWSER_USE_AVAILABLE_BACKENDS": "chrome,iab",
            "CUSTOM_TOKEN": "must-not-reach-node",
        },
    )

    assert passed is True
    assert tools == ["js"]
    assert observed["BROWSER_USE_AVAILABLE_BACKENDS"] == "chrome,iab"
    assert "OPENAI_API_KEY" not in observed
    assert "ROBLOX_OPEN_CLOUD_API_KEY" not in observed
    assert "CUSTOM_TOKEN" not in observed


def test_handoff_is_sanitized_and_never_authorizes_submission(tmp_path: Path) -> None:
    request = _packet(tmp_path)
    preflight_path = tmp_path / "preflight.json"
    assert preflight(request, preflight_path)["status"] == "PASS"
    handoff = create_handoff(
        request,
        preflight_path,
        _browser_report(tmp_path),
        tmp_path / "handoff.json",
    )
    assert handoff["status"] == "AWAITING_TASK_BROWSER_CAPABILITY"
    assert handoff["transportReadiness"]["status"] == "UNVERIFIED"
    assert handoff["transportReadiness"]["requiredTaskTool"] == "mcp__node_repl__js"
    assert handoff["transportReadiness"]["localInstallationIsSufficient"] is False
    assert handoff["submissionAuthorized"] is False
    assert handoff["quotaRemaining"] == "UNKNOWN"
    assert handoff["productionApproved"] is False
    assert "OPENAI_API_KEY" not in json.dumps(handoff)
    assert any(
        "imagegen" in action.lower() and "api" in action.lower()
        for action in handoff["forbiddenActions"]
    )
    assert any("retry" in action.lower() for action in handoff["forbiddenActions"])


def test_iab_handoff_passes_only_when_attachment_free(tmp_path: Path) -> None:
    request = _packet(tmp_path, browser_adapter="codex_iab")
    preflight_path = tmp_path / "preflight.json"
    report = preflight(request, preflight_path)
    assert report["status"] == "PASS"
    assert any(
        check["id"] == "browser_adapter_attachment_compatibility"
        and check["status"] == "PASS"
        for check in report["checks"]
    )
    handoff = create_handoff(
        request,
        preflight_path,
        _browser_report(tmp_path, "codex_iab"),
        tmp_path / "handoff.json",
    )
    assert handoff["browserAdapter"] == "codex_iab"
    assert handoff["attachments"] == []
    assert any("in-app Browser" in instruction for instruction in handoff["instructions"])


def test_import_records_conservative_provenance_and_blocks_repeat_prompt(
    tmp_path: Path,
) -> None:
    request = _packet(tmp_path)
    source = _image(tmp_path / "download.png")
    result_path = import_result(
        request,
        "test-result-001",
        [source],
        tmp_path / "asset/precanonical/results/test-result-001",
        "browser_download",
        None,
        False,
    )
    result = load_json(result_path)
    assert result["provenance"]["surface"] == "ChatGPT Web / ChatGPT Images"
    assert result["provenance"]["modelName"] is None
    assert result["provenance"]["modelNameEvidence"] == "NOT_CONFIRMED"
    assert result["canonical"] is False
    blocked = preflight(request)
    assert blocked["status"] == "BLOCKED"
    assert blocked["remainingGenerations"] == 3
    assert any(
        "exact prompt hash" in reason for reason in blocked["blockingReasons"]
    )


def test_budget_exhaustion_is_blocked_without_retry(tmp_path: Path) -> None:
    request = _packet(tmp_path, maximum=1)
    import_result(
        request,
        "test-result-001",
        [_image(tmp_path / "download.png")],
        tmp_path / "asset/precanonical/results/test-result-001",
        "manual_download",
        None,
        False,
    )
    report = preflight(request)
    assert report["status"] == "BLOCKED"
    assert report["nextState"] == "BUDGET_EXHAUSTED"
    assert report["remainingGenerations"] == 0


def test_precise_model_name_requires_ui_confirmation(tmp_path: Path) -> None:
    request = _packet(tmp_path)
    source = _image(tmp_path / "download.png")
    with pytest.raises(ArtSystemError, match="UI confirmation"):
        import_result(
            request,
            "test-result-001",
            [source],
            tmp_path / "asset/precanonical/results/test-result-001",
            "browser_download",
            "unverified-model-name",
            False,
        )


def test_human_selection_requires_named_reviewer_and_all_pass(
    tmp_path: Path,
) -> None:
    request = _packet(tmp_path)
    result = import_result(
        request,
        "test-result-001",
        [_image(tmp_path / "download.png")],
        tmp_path / "asset/precanonical/results/test-result-001",
        "browser_download",
        None,
        False,
    )
    with pytest.raises(ArtSystemError, match="named human reviewer"):
        create_review(
            result,
            "review-001",
            "HUMAN_SELECTED",
            result.parent / "review.json",
            _assessment(),
            None,
            [],
            [],
            [],
        )
    failing = _assessment()
    failing["stateCoherence"] = "FAIL"
    with pytest.raises(ArtSystemError, match="every assessment"):
        create_review(
            result,
            "review-001",
            "HUMAN_SELECTED",
            result.parent / "review.json",
            failing,
            "Founder",
            [],
            [],
            [],
        )


def test_precanonical_candidate_requires_complete_pass_and_preserve_rule(
    tmp_path: Path,
) -> None:
    request = _packet(tmp_path)
    result = import_result(
        request,
        "test-result-001",
        [_image(tmp_path / "download.png")],
        tmp_path / "asset/precanonical/results/test-result-001",
        "manual_download",
        None,
        False,
    )
    incomplete = _assessment()
    incomplete["internalCoherence"] = "UNKNOWN"
    with pytest.raises(ArtSystemError, match="every assessment dimension"):
        create_review(
            result,
            "review-001",
            "PRECANONICAL_CANDIDATE",
            result.parent / "review.json",
            incomplete,
            None,
            ["Preserve the silhouette."],
            [],
            [],
        )
    with pytest.raises(ArtSystemError, match="preserve rule"):
        create_review(
            result,
            "review-001",
            "PRECANONICAL_CANDIDATE",
            result.parent / "review.json",
            _assessment(),
            None,
            [],
            [],
            [],
        )


def test_negative_review_decisions_require_actionable_rules(
    tmp_path: Path,
) -> None:
    request = _packet(tmp_path)
    result = import_result(
        request,
        "test-result-001",
        [_image(tmp_path / "download.png")],
        tmp_path / "asset/precanonical/results/test-result-001",
        "manual_download",
        None,
        False,
    )
    with pytest.raises(ArtSystemError, match="correction rule"):
        create_review(
            result,
            "review-001",
            "REVISION_REQUIRED",
            result.parent / "review.json",
            _assessment("UNKNOWN"),
            None,
            [],
            [],
            [],
        )
    with pytest.raises(ArtSystemError, match="prohibition"):
        create_review(
            result,
            "review-001",
            "REJECTED",
            result.parent / "review.json",
            _assessment("FAIL"),
            None,
            [],
            ["Rebuild the front and rear relationship."],
            [],
        )


def test_human_selected_authorizes_only_canonicalization(tmp_path: Path) -> None:
    request = _packet(tmp_path)
    result = import_result(
        request,
        "test-result-001",
        [_image(tmp_path / "download.png")],
        tmp_path / "asset/precanonical/results/test-result-001",
        "manual_download",
        None,
        False,
    )
    review = create_review(
        result,
        "review-001",
        "HUMAN_SELECTED",
        result.parent / "review.json",
        _assessment(),
        "Founder",
        ["primary silhouette"],
        [],
        ["new components"],
    )
    assert review["canonicalizationAuthorized"] is True
    assert review["canonical"] is False
    assert review["productionApproved"] is False
    request_status = status(request)
    assert request_status["reviews"][0]["decision"] == "HUMAN_SELECTED"
    assert request_status["productionApproved"] is False


def test_schema_forbids_direct_canonical_promotion(tmp_path: Path) -> None:
    request = _packet(tmp_path)
    result = import_result(
        request,
        "test-result-001",
        [_image(tmp_path / "download.png")],
        tmp_path / "asset/precanonical/results/test-result-001",
        "manual_download",
        None,
        False,
    )
    review = {
        "$schema": "https://roblox-top1.local/schemas/precanonical-review.schema.json",
        "schemaVersion": "1.0.0",
        "reviewId": "review-001",
        "result": {"path": str(result), "sha256": "a" * 64},
        "resultDigest": "b" * 64,
        "decision": "CANONICAL",
        "reviewer": "Founder",
        "reviewedAt": "2026-07-16T12:00:00Z",
        "assessment": _assessment(),
        "preserve": [],
        "correct": [],
        "forbidNext": [],
        "canonicalizationAuthorized": True,
        "canonical": False,
        "productionApproved": False,
    }
    errors = validate_with_schema(
        review, ROOT / "schemas/precanonical-review.schema.json"
    )
    assert errors


def test_correction_requires_parent_result_and_targeted_instructions(
    tmp_path: Path,
) -> None:
    with pytest.raises(ArtSystemError, match="parent-result"):
        init_packet(
            BRIEF,
            "correction-001",
            tmp_path / "correction",
            "correction",
            1,
            True,
            False,
        )


def test_correction_binds_exact_parent_result_and_images(tmp_path: Path) -> None:
    request = _packet(tmp_path, request_id="exploration-001")
    result = import_result(
        request,
        "exploration-result-001",
        [_image(tmp_path / "download.png")],
        tmp_path / "asset/precanonical/results/exploration-result-001",
        "browser_download",
        None,
        False,
    )
    correction = init_packet(
        BRIEF,
        "correction-001",
        tmp_path / "asset/precanonical/requests/correction-001",
        "correction",
        1,
        True,
        False,
        result,
        ["Preserve the silhouette and shorten the left reinforcement brace."],
    )
    preflight_path = tmp_path / "correction-preflight.json"
    report = preflight(correction, preflight_path)
    assert report["status"] == "PASS"
    handoff = create_handoff(
        correction,
        preflight_path,
        _browser_report(tmp_path, "codex_chrome"),
        tmp_path / "correction-handoff.json",
    )
    assert handoff["browserAdapter"] == "codex_chrome"
    assert len(handoff["attachments"]) == 1
    assert handoff["submissionAuthorized"] is False
    invalid_iab_handoff = copy.deepcopy(handoff)
    invalid_iab_handoff["browserAdapter"] = "codex_iab"
    assert validate_with_schema(
        invalid_iab_handoff,
        ROOT / "schemas/precanonical-handoff.schema.json",
    )


def test_iab_correction_is_blocked_when_parent_image_requires_upload(
    tmp_path: Path,
) -> None:
    request = _packet(tmp_path, request_id="exploration-001")
    result = import_result(
        request,
        "exploration-result-001",
        [_image(tmp_path / "download.png")],
        tmp_path / "asset/precanonical/results/exploration-result-001",
        "browser_download",
        None,
        False,
    )
    correction = init_packet(
        BRIEF,
        "correction-001",
        tmp_path / "asset/precanonical/requests/correction-001",
        "correction",
        1,
        True,
        False,
        result,
        ["Preserve the silhouette and shorten the left reinforcement brace."],
        "codex_iab",
    )
    report = preflight(correction)
    assert report["status"] == "FAIL"
    assert any(
        "require codex_chrome" in reason for reason in report["blockingReasons"]
    )


def test_request_schema_rejects_hidden_imagegen_fallback(tmp_path: Path) -> None:
    request_path = _packet(tmp_path)
    request = copy.deepcopy(load_json(request_path))
    request["automation"]["automaticCodexImageFallback"] = True
    errors = validate_with_schema(
        request, ROOT / "schemas/precanonical-request.schema.json"
    )
    assert errors


def test_first_result_visual_audit_is_hash_bound_and_schema_valid() -> None:
    audit_path = (
        PROJECT_ROOT
        / "assets-3d/defense-barricade-small/precanonical/results"
        / "defense-barricade-web-001-result-001/audit/first-result-audit.json"
    )
    audit = load_json(audit_path)
    assert not validate_with_schema(
        audit,
        ROOT / "schemas/precanonical-visual-audit.schema.json",
    )
    assert len(audit["findings"]) == 32
    for binding in audit["evidence"].values():
        if not isinstance(binding, dict):
            continue
        evidence_path = PROJECT_ROOT / binding["path"]
        assert evidence_path.is_file()
        assert precanonical_module.sha256_file(evidence_path) == binding["sha256"]


def test_runner_and_installer_expose_the_bounded_integration() -> None:
    runner = (ROOT / "scripts/art-direction.ps1").read_text(encoding="utf-8")
    for command in (
        "precanon-init",
        "precanon-preflight",
        "precanon-browser-doctor",
        "precanon-handoff",
        "precanon-operator",
        "precanon-import",
        "precanon-review",
        "precanon-status",
    ):
        assert command in runner
    assert "Resolve-WorkflowPath" in runner
    assert "$ProjectRootCandidate" in runner
    assert "$BrowserAdapter" in runner
    assert "$BrowserDoctor" in runner
    assert "codex_iab" in runner
    installer = (ROOT / "scripts/install-workflow.ps1").read_text(
        encoding="utf-8"
    )
    assert "$PrecanonicalReferenceDestination" in installer
    assert "precanonicalReferencePath" in installer
    assert "precanonicalReference" in installer
