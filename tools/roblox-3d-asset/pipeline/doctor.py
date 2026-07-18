from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from pipeline.status import Status, aggregate


def _run(command: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        output = (completed.stdout or completed.stderr).strip().splitlines()
        return completed.returncode, output[0] if output else ""
    except (OSError, subprocess.SubprocessError) as error:
        return 1, str(error)


def find_blender() -> Path | None:
    candidates: list[str] = []
    configured = os.environ.get("BLENDER_EXE")
    if configured:
        candidates.append(configured)
    discovered = shutil.which("blender")
    if discovered:
        candidates.append(discovered)
    if os.name == "nt":
        candidates.extend(
            sorted(
                glob.glob(r"C:\Program Files\Blender Foundation\Blender*\blender.exe"),
                reverse=True,
            )
        )
    else:
        candidates.extend(["/Applications/Blender.app/Contents/MacOS/Blender", "/usr/bin/blender"])
    for candidate in candidates:
        path = Path(candidate).expanduser()
        if path.is_file():
            return path.resolve()
    return None


def _git_candidates(*, windows: bool | None = None) -> list[Path]:
    candidates: list[str | Path] = []
    configured = os.environ.get("GIT_EXE")
    if configured:
        candidates.append(configured)
    discovered = shutil.which("git")
    if discovered:
        candidates.append(discovered)
    is_windows = os.name == "nt" if windows is None else windows
    if is_windows:
        candidates.extend(
            [
                Path(
                    os.environ.get("ProgramFiles", r"C:\Program Files")
                )
                / "Git"
                / "cmd"
                / "git.exe",
                Path(r"C:\Program Files\Git\cmd\git.exe"),
                Path(
                    os.environ.get(
                        "ProgramFiles(x86)",
                        r"C:\Program Files (x86)",
                    )
                )
                / "Git"
                / "cmd"
                / "git.exe",
            ]
        )
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            candidates.append(
                Path(local_app_data)
                / "Programs"
                / "Git"
                / "cmd"
                / "git.exe"
            )

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        path = Path(candidate).expanduser()
        key = os.path.normcase(str(path))
        if key not in seen:
            seen.add(key)
            unique.append(path)
    return unique


def find_git(candidates: list[Path] | None = None) -> Path | None:
    for candidate in candidates if candidates is not None else _git_candidates():
        path = Path(candidate).expanduser()
        if not path.is_file():
            continue
        code, _version = _run([str(path), "--version"])
        if code == 0:
            return path.resolve()
    return None


def _git(repo: Path) -> dict[str, Any]:
    git = find_git()
    if git is None:
        return {"status": Status.BLOCKED.value, "reason": "git executable not found"}
    executable = str(git)
    code, root = _run(
        [executable, "rev-parse", "--show-toplevel"],
        repo,
    )
    if code != 0:
        return {"status": Status.BLOCKED.value, "reason": root}
    head_code, head = _run([executable, "rev-parse", "HEAD"], repo)
    try:
        status_process = subprocess.run(
            [executable, "status", "--porcelain=v1"],
            cwd=repo,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return {
            "status": Status.BLOCKED.value,
            "executable": executable,
            "reason": str(error),
        }
    if status_process.returncode != 0:
        reason = (status_process.stderr or status_process.stdout).strip()
        return {
            "status": Status.BLOCKED.value,
            "executable": executable,
            "reason": reason or "git status failed",
        }
    changes = [line for line in status_process.stdout.splitlines() if line]
    status = Status.PASS if head_code == 0 and not changes else Status.PARTIAL
    return {
        "status": status.value,
        "executable": executable,
        "root": root,
        "commit": head if head_code == 0 else None,
        "dirty": bool(changes),
        "changes": changes,
    }


def run_doctor(repo: Path) -> dict[str, Any]:
    blender = find_blender()
    blender_result: dict[str, Any]
    if blender:
        code, version = _run([str(blender), "--version"])
        blender_result = {
            "status": Status.PASS.value if code == 0 else Status.FAIL.value,
            "path": str(blender),
            "version": version,
        }
    else:
        blender_result = {"status": Status.BLOCKED.value, "reason": "Blender not found"}

    codex = shutil.which("codex")
    cloud_envs = {
        "apiKey": bool(os.environ.get("ROBLOX_OPEN_CLOUD_API_KEY")),
        "creatorId": bool(os.environ.get("ROBLOX_STAGING_CREATOR_ID")),
        "creatorAllowlist": bool(os.environ.get("ROBLOX_3D_ALLOWED_CREATOR_IDS")),
    }
    cloud_status = Status.PASS if all(cloud_envs.values()) else Status.BLOCKED
    checks = {
        "python": {"status": Status.PASS.value, "path": sys.executable, "version": sys.version.split()[0]},
        "blender": blender_result,
        "git": _git(repo),
        "codex": {"status": Status.PASS.value if codex else Status.UNKNOWN.value, "path": codex},
        "cloudPublication": {
            "status": cloud_status.value,
            "environmentVariablesPresent": cloud_envs,
            "reason": None if cloud_status is Status.PASS else "staging credentials/allowlist are incomplete",
        },
        "studioMcp": {
            "status": Status.UNKNOWN.value,
            "reason": "verify with Roblox Studio MCP from the active Codex task",
        },
    }
    local_status = aggregate([checks["python"]["status"], checks["blender"]["status"]])
    overall = aggregate([local_status, checks["git"]["status"], checks["codex"]["status"]])
    return {
        "status": overall.value,
        "localCompilerStatus": local_status.value,
        "cloudPublisherStatus": cloud_status.value,
        "checks": checks,
    }
