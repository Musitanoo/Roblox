from __future__ import annotations

import hashlib
import json
import math
import os
import re
import secrets
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, Mapping


REQUIRED_BLENDER_VERSION = "Blender 5.2.0"
SESSION_ID = re.compile(r"^[a-z0-9][a-z0-9-]{7,79}$")
CHANGE_SET_ID = re.compile(r"^[a-z0-9][a-z0-9-]{7,79}$")
ALLOWED_SESSION_MODES = {"OBSERVE", "EXPLORE"}
ALLOWED_OPERATION_TYPES = {
    "SET_COMPONENT_DIMENSION",
    "SET_BEVEL_WIDTH",
    "MOVE_COMPONENT",
    "ROTATE_COMPONENT",
    "SET_COMPONENT_VISIBILITY",
    "SET_MATERIAL_ROLE",
    "SET_MATERIAL_VALUE",
}
FORBIDDEN_TOOL_NAMES = {
    "execute_arbitrary_python",
    "delete_arbitrary_file",
    "install_addon",
    "download_external_asset",
    "replace_canonical_source",
    "overwrite_asset_contract",
    "publish_to_roblox",
    "modify_locked_canon",
}
ALLOWED_INVARIANTS = {
    "overallWidth",
    "overallHeight",
    "overallDepth",
    "grounding",
    "interactionSocketPosition",
    "componentNames",
    "materialAssignments",
    "triangleBudget",
    "collisionContractUnchanged",
    "referenceImmutability",
    "visualCanonBinding",
}
ALLOWED_VIEWS = {
    "front",
    "rear",
    "left",
    "right",
    "top",
    "perspective",
    "mobile_distance",
    "silhouette",
}
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


class WorkbenchError(RuntimeError):
    """Fail-closed workbench contract error."""


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def random_session_id(asset_key: str) -> str:
    return f"{asset_key.replace('_', '-')}-{secrets.token_hex(6)}"


def random_token_sha256() -> str:
    return hashlib.sha256(secrets.token_bytes(32)).hexdigest()


def finite_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def ensure_within(path: Path, root: Path, label: str) -> Path:
    resolved = path.resolve()
    resolved_root = root.resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as error:
        raise WorkbenchError(f"{label} escapes its allowed root: {resolved}") from error
    return resolved


def ensure_asset_contract(path: Path, repo: Path) -> Path:
    resolved = ensure_within(path, repo / "assets-3d", "asset contract")
    if resolved.name != "asset.json" or not resolved.is_file():
        raise WorkbenchError("asset contract must be an existing assets-3d/**/asset.json")
    return resolved


def ensure_session_id(value: str) -> str:
    if not SESSION_ID.fullmatch(value):
        raise WorkbenchError("sessionId must match ^[a-z0-9][a-z0-9-]{7,79}$")
    return value


def ensure_change_set_id(value: str) -> str:
    if not CHANGE_SET_ID.fullmatch(value):
        raise WorkbenchError("changeSetId must match ^[a-z0-9][a-z0-9-]{7,79}$")
    return value


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


def sanitized_blender_environment() -> dict[str, str]:
    return sanitized_subprocess_environment(deterministic=True)


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


class RepositoryOperationLock(AbstractContextManager["RepositoryOperationLock"]):
    def __init__(self, repo: Path) -> None:
        self.path = repo.resolve() / ".codex" / "blender-workbench.lock"
        self.acquired = False

    def __enter__(self) -> "RepositoryOperationLock":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            try:
                existing = json.loads(self.path.read_text(encoding="utf-8"))
                pid = int(existing.get("pid", 0))
            except (OSError, ValueError, json.JSONDecodeError):
                pid = 0
            if _pid_alive(pid):
                raise WorkbenchError(
                    f"another Blender workbench operation owns the repository lock (pid={pid})"
                )
            self.path.unlink(missing_ok=True)
        flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
        descriptor = os.open(self.path, flags)
        try:
            os.write(
                descriptor,
                json.dumps({"pid": os.getpid()}, sort_keys=True).encode("utf-8"),
            )
        finally:
            os.close(descriptor)
        self.acquired = True
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.acquired:
            self.path.unlink(missing_ok=True)
            self.acquired = False
