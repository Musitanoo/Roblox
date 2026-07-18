from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, sanitized_subprocess_environment, write_json

CHECK_TIMEOUT_SECONDS = 1800


def _tail(value: str, limit: int = 8000) -> str:
    return value[-limit:]


def _run(check_id: str, command: list[str], *, required: bool = True) -> dict[str, Any]:
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
            env=sanitized_subprocess_environment(),
            timeout=CHECK_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        stdout = (
            error.stdout.decode(errors="replace")
            if isinstance(error.stdout, bytes)
            else (error.stdout or "")
        )
        stderr = (
            error.stderr.decode(errors="replace")
            if isinstance(error.stderr, bytes)
            else (error.stderr or "")
        )
        completed = subprocess.CompletedProcess(
            command,
            124,
            stdout,
            stderr + f"\nCheck timed out after {CHECK_TIMEOUT_SECONDS} seconds.",
        )
    duration_ms = int(round((time.perf_counter() - start) * 1000))
    return {
        "id": check_id,
        "required": required,
        "command": command,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "exitCode": completed.returncode,
        "durationMs": duration_ms,
        "stdoutTail": _tail(completed.stdout),
        "stderrTail": _tail(completed.stderr),
    }


def _skipped(check_id: str, command: list[str]) -> dict[str, Any]:
    return {
        "id": check_id,
        "required": False,
        "command": command,
        "status": "SKIPPED",
        "exitCode": None,
        "durationMs": 0,
        "stdoutTail": "",
        "stderrTail": "Tool unavailable in packaging environment.",
    }


def _find_tool(name: str) -> str | None:
    observed = shutil.which(name)
    if observed:
        return observed
    profile = os.environ.get("USERPROFILE")
    if profile:
        candidate = Path(profile) / ".rokit/bin" / (f"{name}.exe" if os.name == "nt" else name)
        if candidate.is_file():
            return str(candidate)
    return None


def _find_blender() -> str | None:
    explicit = os.environ.get("ART_BLENDER")
    if explicit and Path(explicit).is_file():
        return explicit
    observed = shutil.which("blender")
    if observed:
        return observed
    if os.name == "nt":
        for variable in ("ProgramFiles", "ProgramFiles(x86)"):
            base = os.environ.get(variable)
            if not base:
                continue
            candidates = sorted((Path(base) / "Blender Foundation").glob("Blender */blender.exe"), reverse=True)
            if candidates:
                return str(candidates[0])
    mac = Path("/Applications/Blender.app/Contents/MacOS/Blender")
    return str(mac) if mac.is_file() else None


def verify() -> dict[str, Any]:
    python = sys.executable
    checks = [
        _run("pinned_python_dependencies", [python, "-m", "tools.art.check_dependencies"]),
        _run("generated_luau_drift", [python, "-m", "tools.art.generate_luau", "--check"]),
        _run(
            "schema_semantic_validation",
            [python, "-m", "tools.art.validate_library", "--report", "evidence/static-validation-report.json"],
        ),
        _run(
            "transfer_evidence_integrity",
            [
                python,
                "-m",
                "tools.art.validate_transfer_report",
                "evidence/transfer/turret-fast-v1/report.json",
            ],
        ),
        _run("python_compileall", [python, "-m", "compileall", "-q", "tools", "tests"]),
        _run("pytest_adversarial", [python, "-m", "pytest", "--override-ini=addopts=", "-q"]),
        _run("r3d_unit_tests", [python, "tools/roblox-3d-asset/r3d.py", "test"]),
    ]
    bash = shutil.which("bash")
    checks.append(
        _run("shell_syntax", [bash, "-n", "scripts/art-direction.sh"])
        if bash
        else _skipped("shell_syntax", ["bash", "-n", "scripts/art-direction.sh"])
    )
    powershell = shutil.which("powershell") or shutil.which("pwsh")
    if powershell:
        for check_id, script in (
            ("installer_powershell_syntax", "scripts/install-workflow.ps1"),
            ("runner_powershell_syntax", "scripts/art-direction.ps1"),
        ):
            checks.append(
                _run(
                    check_id,
                    [
                        powershell,
                        "-NoProfile",
                        "-Command",
                        "$errors=$null; [System.Management.Automation.Language.Parser]::ParseFile("
                        f"'{script}',[ref]$null,[ref]$errors) | Out-Null; "
                        "if ($errors.Count -gt 0) { $errors | ForEach-Object { Write-Error $_ }; exit 1 }",
                    ],
                )
            )
    checks.append(
        _run(
            "powershell_luau_validation",
            [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "scripts/art-direction.ps1", "validate-luau"],
        )
        if powershell
        else _skipped("powershell_luau_validation", ["powershell", "scripts/art-direction.ps1", "validate-luau"])
    )
    pytest_output = next(check["stdoutTail"] for check in checks if check["id"] == "pytest_adversarial")
    match = re.search(r"(\d+) passed", pytest_output)
    pytest_passed = int(match.group(1)) if match else 0
    blender = _find_blender()
    toolchain = {
        "pythonVersion": platform.python_version(),
        "platform": platform.platform(),
        "bashAvailable": bash is not None,
        "powershellAvailable": powershell is not None,
        "blenderAvailable": blender is not None,
        "luauAnalyzeAvailable": _find_tool("luau-lsp") is not None,
        "seleneAvailable": _find_tool("selene") is not None,
        "styluaAvailable": _find_tool("stylua") is not None,
        "rojoAvailable": shutil.which("rojo") is not None,
    }
    limitations = []
    for label, available in [
        ("Blender runtime", toolchain["blenderAvailable"]),
        ("PowerShell parser/runtime", toolchain["powershellAvailable"]),
        ("Luau LSP", toolchain["luauAnalyzeAvailable"]),
        ("Selene", toolchain["seleneAvailable"]),
        ("StyLua", toolchain["styluaAvailable"]),
        ("Rojo", toolchain["rojoAvailable"]),
    ]:
        if not available:
            limitations.append(f"{label} was not available in the packaging environment.")
    status = "PASS" if all(check["status"] == "PASS" for check in checks if check["required"]) else "FAIL"
    return {
        "$schema": "https://roblox-top1.local/schemas/static-verification-report.schema.json",
        "schemaVersion": "1.0.0",
        "status": status,
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "toolchain": toolchain,
        "checks": checks,
        "pytestPassed": pytest_passed,
        "limitations": limitations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run and persist the complete static verification suite.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "evidence/static-verification-report.json",
    )
    args = parser.parse_args()
    report = verify()
    write_json(args.output, report)
    for check in report["checks"]:
        print(f"[{check['status']}] {check['id']} ({check['durationMs']} ms)")
    print(f"[{report['status']}] static verification; pytest passed={report['pytestPassed']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
