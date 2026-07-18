from __future__ import annotations

import io
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tools.art import build_transfer_proof, verify_blender, verify_static
from tools.art.studio_mcp import StudioMcpClient


def test_studio_mcp_child_receives_only_sanitized_environment(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-reach-studio")
    monkeypatch.setenv("ROBLOX_OPEN_CLOUD_API_KEY", "must-not-reach-studio")
    fake_process = SimpleNamespace(
        stdin=io.StringIO(),
        stdout=io.StringIO(),
        stderr=io.StringIO(),
        poll=lambda: None,
    )
    popen = Mock(return_value=fake_process)
    monkeypatch.setattr("tools.art.studio_mcp.subprocess.Popen", popen)
    monkeypatch.setattr(
        StudioMcpClient,
        "request",
        lambda _self, method, _params, **_kwargs: (
            {"result": {"tools": []}}
            if method == "tools/list"
            else {"result": {}}
        ),
    )
    monkeypatch.setattr(
        StudioMcpClient,
        "notify",
        lambda _self, _method, _params: None,
    )

    StudioMcpClient(tmp_path / "StudioMCP.exe")

    environment = popen.call_args.kwargs["env"]
    assert "OPENAI_API_KEY" not in environment
    assert "ROBLOX_OPEN_CLOUD_API_KEY" not in environment
    assert environment["DISABLE_TELEMETRY"] == "true"


def test_transfer_blender_child_is_sanitized_and_bounded(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ROBLOX_OPEN_CLOUD_API_KEY", "must-not-reach-blender")
    run = Mock(
        return_value=build_transfer_proof.subprocess.CompletedProcess(
            args=["blender.exe"],
            returncode=0,
            stdout="",
            stderr="",
        )
    )
    monkeypatch.setattr(build_transfer_proof.subprocess, "run", run)

    build_transfer_proof._run_blender(
        tmp_path / "blender.exe",
        tmp_path / "output",
        "salvaged-frontier",
        "build-only",
        tmp_path / "blender.log",
    )

    environment = run.call_args.kwargs["env"]
    assert "ROBLOX_OPEN_CLOUD_API_KEY" not in environment
    assert environment["PYTHONHASHSEED"] == "0"
    assert run.call_args.kwargs["timeout"] > 0


def test_verification_children_are_sanitized_and_bounded(
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-reach-checks")
    blender_run = Mock(
        return_value=verify_blender.subprocess.CompletedProcess(
            args=["blender.exe"],
            returncode=0,
            stdout="",
            stderr="",
        )
    )
    static_run = Mock(
        return_value=verify_static.subprocess.CompletedProcess(
            args=["python"],
            returncode=0,
            stdout="",
            stderr="",
        )
    )
    monkeypatch.setattr(verify_blender.subprocess, "run", blender_run)
    verify_blender._run(
        tmp_path / "blender.exe",
        tmp_path / "output",
        "salvaged-frontier",
    )
    blender_environment = blender_run.call_args.kwargs["env"]
    assert "OPENAI_API_KEY" not in blender_environment
    assert blender_run.call_args.kwargs["timeout"] > 0

    monkeypatch.setattr(verify_static.subprocess, "run", static_run)
    verify_static._run("bounded-check", ["python", "--version"])
    static_environment = static_run.call_args.kwargs["env"]
    assert "OPENAI_API_KEY" not in static_environment
    assert static_run.call_args.kwargs["timeout"] > 0
