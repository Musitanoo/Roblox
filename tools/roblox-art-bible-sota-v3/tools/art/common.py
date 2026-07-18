from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_BASE = "https://roblox-top1.local/schemas/"
SAFE_SUBPROCESS_ENVIRONMENT_KEYS = {
    "APPDATA",
    "COMSPEC",
    "HOMEDRIVE",
    "HOMEPATH",
    "LOCALAPPDATA",
    "NUMBER_OF_PROCESSORS",
    "OS",
    "PATH",
    "PATHEXT",
    "PROGRAMDATA",
    "PROGRAMFILES",
    "PROGRAMFILES(X86)",
    "SYSTEMDRIVE",
    "SYSTEMROOT",
    "TEMP",
    "TMP",
    "USERDOMAIN",
    "USERNAME",
    "USERPROFILE",
    "WINDIR",
}
SENSITIVE_ENVIRONMENT_NAMES = {
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_SESSION_TOKEN",
    "AZURE_CLIENT_SECRET",
    "GH_TOKEN",
    "GITHUB_TOKEN",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "HF_TOKEN",
    "HUGGINGFACE_HUB_TOKEN",
    "NPM_TOKEN",
    "OPENAI_API_KEY",
    "ROBLOX_3D_ALLOWED_CREATOR_IDS",
    "ROBLOX_OPEN_CLOUD_API_KEY",
    "ROBLOX_SECURITY",
    "ROBLOX_STAGING_CREATOR_ID",
}
SENSITIVE_ENVIRONMENT_SUFFIXES = (
    "_API_KEY",
    "_COOKIE",
    "_CREDENTIAL",
    "_CREDENTIALS",
    "_PASSWORD",
    "_PRIVATE_KEY",
    "_SECRET",
    "_TOKEN",
)


def _discover_project_root() -> Path:
    explicit = os.environ.get("ROBLOX_PROJECT_ROOT")
    if explicit:
        candidate = Path(explicit).resolve()
        if (
            (candidate / "scripts/r3d.ps1").is_file()
            and (candidate / "assets-3d/registry").is_dir()
        ):
            return candidate
        raise RuntimeError(
            "ROBLOX_PROJECT_ROOT does not point to a compatible repository"
        )
    for candidate in (ROOT, *ROOT.parents):
        if (
            (candidate / ".git").exists()
            and (candidate / "scripts/r3d.ps1").is_file()
            and (candidate / "assets-3d/registry").is_dir()
        ):
            return candidate
    return ROOT


PROJECT_ROOT = _discover_project_root()


class ArtSystemError(RuntimeError):
    """Raised when an executable art-direction contract is violated."""


def _sensitive_environment_name(name: str) -> bool:
    normalized = name.upper()
    return (
        normalized in SENSITIVE_ENVIRONMENT_NAMES
        or normalized.endswith(SENSITIVE_ENVIRONMENT_SUFFIXES)
    )


def sanitized_subprocess_environment(
    configured: Mapping[str, Any] | None = None,
    *,
    deterministic: bool = False,
) -> dict[str, str]:
    environment = {
        key: value
        for key, value in os.environ.items()
        if key.upper() in SAFE_SUBPROCESS_ENVIRONMENT_KEYS
    }
    for key, value in (configured or {}).items():
        name = str(key)
        if not _sensitive_environment_name(name):
            environment[name] = str(value)
    if deterministic:
        environment["PYTHONHASHSEED"] = "0"
    environment["DISABLE_TELEMETRY"] = "true"
    return environment


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ArtSystemError(f"Missing required file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArtSystemError(f"Invalid JSON in {path}: {exc}") from exc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_with_schema(instance: Any, schema_path: Path) -> list[str]:
    schema = load_json(schema_path)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(instance), key=lambda error: list(error.absolute_path))
    messages: list[str] = []
    for error in errors:
        pointer = "/" + "/".join(str(part) for part in error.absolute_path)
        messages.append(f"{pointer or '/'}: {error.message}")
    return messages


def require(condition: bool, message: str, issues: list[str]) -> None:
    if not condition:
        issues.append(message)


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return str(path)
