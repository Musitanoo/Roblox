from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from copy import deepcopy
from pathlib import Path
from typing import Any

from mcp.bounded_operations import source_bindings, validate_change_set
from mcp.evidence_writer import append_event, utc_now, write_json
from mcp.scene_inspector import (
    evaluate_invariants,
    file_sha256,
    run_bridge,
    scene_diff,
)
from mcp.security_policy import (
    FORBIDDEN_TOOL_NAMES,
    REQUIRED_BLENDER_VERSION,
    RepositoryOperationLock,
    WorkbenchError,
    canonical_sha256,
    ensure_asset_contract,
    ensure_session_id,
    ensure_within,
    random_session_id,
    random_token_sha256,
    sanitized_blender_environment,
)
from pipeline.contract import validate_contract
from pipeline.doctor import find_blender


SESSION_SCHEMA = "https://roblox-top1.local/schemas/blender-workbench-session.schema.json"


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise WorkbenchError(f"cannot read JSON {path}: {error}") from error
    if not isinstance(value, dict):
        raise WorkbenchError(f"JSON root must be an object: {path}")
    return value


def _make_read_only(path: Path) -> None:
    path.chmod(stat.S_IREAD)


def _make_writable(path: Path) -> None:
    path.chmod(stat.S_IREAD | stat.S_IWRITE)


def _json_pointer_get(document: Any, pointer: str) -> Any:
    value = document
    for token in pointer.lstrip("/").split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def _json_pointer_set(document: Any, pointer: str, replacement: Any) -> None:
    tokens = [
        token.replace("~1", "/").replace("~0", "~")
        for token in pointer.lstrip("/").split("/")
    ]
    parent = document
    for token in tokens[:-1]:
        parent = parent[int(token)] if isinstance(parent, list) else parent[token]
    final = tokens[-1]
    if isinstance(parent, list):
        parent[int(final)] = replacement
    else:
        parent[final] = replacement


def _compare_promoted_contract(
    *,
    session: dict[str, Any],
    expected: dict[str, Any],
    authoritative: dict[str, Any],
    authoritative_path: Path,
) -> dict[str, Any]:
    bound_path = Path(session["contract"]["path"]).resolve()
    expected_revision = session["contract"]["revision"] + 1
    expected_canon_hash = session["visualCanon"]["sha256"]
    checks = {
        "authoritativePath": {
            "passed": authoritative_path.resolve() == bound_path,
            "expected": str(bound_path),
            "actual": str(authoritative_path.resolve()),
        },
        "revision": {
            "passed": authoritative.get("revision") == expected_revision,
            "expected": expected_revision,
            "actual": authoritative.get("revision"),
        },
        "visualCanonBinding": {
            "passed": authoritative.get("visualCanon", {}).get("sha256")
            == expected_canon_hash,
            "expected": expected_canon_hash,
            "actual": authoritative.get("visualCanon", {}).get("sha256"),
        },
        "semanticSource": {
            "passed": canonical_sha256(authoritative) == canonical_sha256(expected),
            "expectedCanonicalSha256": canonical_sha256(expected),
            "actualCanonicalSha256": canonical_sha256(authoritative),
        },
    }
    return {
        "passed": all(item["passed"] for item in checks.values()),
        "checks": checks,
    }


class WorkbenchManager:
    def __init__(self, repo: Path) -> None:
        self.repo = repo.resolve()
        self.assets_root = self.repo / "assets-3d"
        self.tool_root = self.repo / "tools" / "roblox-3d-asset"

    def doctor(self) -> dict[str, Any]:
        blender = find_blender()
        blender_check: dict[str, Any]
        if blender is None:
            blender_check = {"status": "BLOCKED", "reason": "Blender not found"}
        else:
            completed = subprocess.run(
                [str(blender), "--version"],
                check=False,
                capture_output=True,
                text=True,
                env=sanitized_blender_environment(),
                timeout=30,
            )
            first_line = (completed.stdout or completed.stderr).splitlines()[0]
            version_ok = first_line.startswith(REQUIRED_BLENDER_VERSION)
            blender_check = {
                "status": "PASS" if completed.returncode == 0 and version_ok else "FAIL",
                "path": str(blender),
                "version": first_line,
                "requiredVersion": REQUIRED_BLENDER_VERSION,
                "executableSha256": file_sha256(blender),
            }
        from mcp.server_adapter import TOOL_DEFINITIONS

        tool_names = {tool["name"] for tool in TOOL_DEFINITIONS}
        forbidden_present = sorted(tool_names & FORBIDDEN_TOOL_NAMES)
        config_path = self.repo / ".codex" / "config.toml"
        config_text = config_path.read_text(encoding="utf-8") if config_path.is_file() else ""
        config_ok = (
            "[mcp_servers.blender_visual_workbench]" in config_text
            and "r3d-mcp.ps1" in config_text
            and "transport" not in config_text.lower()
        )
        checks = {
            "blender": blender_check,
            "transport": {
                "status": "PASS" if config_ok else "FAIL",
                "type": "STDIO",
                "tcpListener": False,
                "projectConfig": str(config_path),
            },
            "toolSurface": {
                "status": "PASS" if not forbidden_present else "FAIL",
                "toolCount": len(tool_names),
                "forbiddenToolsPresent": forbidden_present,
                "arbitraryPython": False,
            },
            "environment": {
                "status": "PASS",
                "telemetryDisabled": True,
                "robloxSecretsForwarded": False,
                "externalProvidersEnabled": False,
            },
            "bridge": {
                "status": "PASS"
                if (self.tool_root / "blender" / "workbench_bridge.py").is_file()
                else "FAIL",
                "sha256": file_sha256(self.tool_root / "blender" / "workbench_bridge.py")
                if (self.tool_root / "blender" / "workbench_bridge.py").is_file()
                else None,
            },
        }
        status = "PASS" if all(item["status"] == "PASS" for item in checks.values()) else "FAIL"
        return {
            "status": status,
            "capability": "CAP-BLENDER-MCP-001",
            "checks": checks,
            "productionApproved": False,
        }

    def _session_path(self, value: Path | str) -> Path:
        path = Path(value).resolve()
        path = ensure_within(path, self.assets_root, "session")
        if path.is_dir():
            path = path / "session.json"
        if path.name != "session.json" or not path.is_file():
            raise WorkbenchError("session must reference an existing session.json")
        if "workbench" not in path.parts:
            raise WorkbenchError("session.json is outside an asset workbench directory")
        return path

    def _load_session(
        self,
        value: Path | str,
        *,
        require_open: bool = True,
        allow_contract_drift: bool = False,
    ) -> tuple[Path, dict[str, Any]]:
        path = self._session_path(value)
        session = _read_json(path)
        if require_open and session.get("lifecycle") != "OPEN":
            raise WorkbenchError("workbench session is not open")
        bindings = (
            ("asset contract", session["contract"]["path"], session["contract"]["sha256"]),
            ("visual canon", session["visualCanon"]["path"], session["visualCanon"]["sha256"]),
            ("generator", session["generator"]["path"], session["generator"]["sha256"]),
            ("reference build", session["reference"]["path"], session["reference"]["sha256"]),
            ("Blender bridge", session["implementation"]["bridge"]["path"], session["implementation"]["bridge"]["sha256"]),
            ("session manager", session["implementation"]["sessionManager"]["path"], session["implementation"]["sessionManager"]["sha256"]),
            ("MCP adapter", session["implementation"]["serverAdapter"]["path"], session["implementation"]["serverAdapter"]["sha256"]),
        )
        for label, bound_path, expected_hash in bindings:
            if allow_contract_drift and label == "asset contract":
                continue
            current_path = Path(bound_path)
            if not current_path.is_file() or file_sha256(current_path) != expected_hash:
                raise WorkbenchError(f"{label} hash drifted since the session opened")
        snapshot_value = session["contract"].get("snapshotPath")
        if snapshot_value is not None:
            snapshot_path = ensure_within(
                Path(snapshot_value), path.parent / "Reference", "contract snapshot"
            )
            if (
                not snapshot_path.is_file()
                or file_sha256(snapshot_path) != session["contract"]["sha256"]
            ):
                raise WorkbenchError("immutable contract snapshot is missing or drifted")
        return path, session

    def _bindings(self, contract_path: Path) -> dict[str, Any]:
        validation = validate_contract(contract_path)
        if validation["status"] != "PASS":
            raise WorkbenchError("asset contract validation failed: " + "; ".join(validation["errors"]))
        contract = _read_json(contract_path)
        canon_path = Path(validation["visualCanon"]["path"])
        build_root = contract_path.parent / "build"
        manifest_path = build_root / "manifest.json"
        provenance_path = build_root / "provenance.json"
        blend_path = build_root / "source.blend"
        for required in (manifest_path, provenance_path, blend_path):
            if not required.is_file():
                raise WorkbenchError(f"compiled build prerequisite is missing: {required}")
        manifest = _read_json(manifest_path)
        provenance = _read_json(provenance_path)
        contract_hash = file_sha256(contract_path)
        canon_hash = file_sha256(canon_path)
        blend_hash = file_sha256(blend_path)
        declared_blend_hash = manifest.get("artifacts", {}).get("blend", {}).get("sha256")
        if manifest.get("status") != "PASS":
            raise WorkbenchError("reference build manifest is not PASS")
        if provenance.get("contractSha256") != contract_hash:
            raise WorkbenchError("reference build was compiled from a different asset contract")
        if provenance.get("visualCanon", {}).get("sha256") != canon_hash:
            raise WorkbenchError("reference build was compiled from a different visual canon")
        compiler_hash = file_sha256(self.tool_root / "blender" / "compile_asset.py")
        if provenance.get("generatorSha256") != compiler_hash:
            raise WorkbenchError("reference build was compiled by a different generator version")
        if declared_blend_hash != blend_hash:
            raise WorkbenchError("reference source.blend hash differs from its build manifest")
        return {
            "contractData": contract,
            "contractValidation": validation,
            "contractPath": contract_path,
            "contractSha256": contract_hash,
            "canonPath": canon_path,
            "canonSha256": canon_hash,
            "buildBlendPath": blend_path,
            "buildBlendSha256": blend_hash,
            "buildManifestPath": manifest_path,
            "buildManifestSha256": file_sha256(manifest_path),
            "buildSemanticSha256": provenance.get("semanticSha256"),
            "compilerSha256": compiler_hash,
        }

    def begin_session(
        self,
        contract_value: Path | str,
        *,
        mode: str,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        contract_path = ensure_asset_contract(Path(contract_value), self.repo)
        normalized_mode = mode.upper()
        if normalized_mode not in {"OBSERVE", "EXPLORE"}:
            raise WorkbenchError("mode must be OBSERVE or EXPLORE")
        bindings = self._bindings(contract_path)
        contract = bindings["contractData"]
        identifier = ensure_session_id(session_id) if session_id else random_session_id(contract["assetKey"])
        session_root = contract_path.parent / "workbench" / identifier
        if session_root.exists():
            raise WorkbenchError(f"workbench session already exists: {identifier}")
        reference_path = session_root / "Reference" / "source.blend"
        contract_snapshot_path = session_root / "Reference" / "asset.json"
        candidate_path = session_root / "Candidate" / "source.blend"
        reference_path.parent.mkdir(parents=True, exist_ok=False)
        (session_root / "Review").mkdir(parents=True)
        (session_root / "Evidence" / "before").mkdir(parents=True)
        shutil.copy2(bindings["buildBlendPath"], reference_path)
        shutil.copy2(contract_path, contract_snapshot_path)
        _make_read_only(reference_path)
        _make_read_only(contract_snapshot_path)
        if normalized_mode == "EXPLORE":
            candidate_path.parent.mkdir(parents=True)
            shutil.copy2(reference_path, candidate_path)
            _make_writable(candidate_path)

        baseline = run_bridge(
            repo=self.repo,
            session_root=session_root,
            blend_path=reference_path,
            contract_path=contract_path,
            action="inspect",
            capture_root=session_root / "Evidence" / "before",
        )["sceneManifest"]
        if file_sha256(reference_path) != bindings["buildBlendSha256"]:
            raise WorkbenchError("OBSERVE changed the immutable reference build")
        write_json(session_root / "base-scene-manifest.json", baseline)
        write_json(session_root / "scene-inspection.json", baseline)
        diagnosis = {
            "schemaVersion": "1.0.0",
            "status": "DRAFT",
            "classification": None,
            "observation": None,
            "probableCause": None,
            "canonConflict": False,
            "decision": "REVISION_REQUIRED",
        }
        write_json(session_root / "diagnosis.json", diagnosis)
        session = {
            "$schema": SESSION_SCHEMA,
            "schemaVersion": "1.0.0",
            "sessionId": identifier,
            "assetKey": contract["assetKey"],
            "mode": normalized_mode,
            "lifecycle": "OPEN",
            "createdAt": utc_now(),
            "sessionTokenSha256": random_token_sha256(),
            "contract": {
                "path": str(contract_path),
                "snapshotPath": str(contract_snapshot_path),
                "sha256": bindings["contractSha256"],
                "revision": contract["revision"],
            },
            "visualCanon": {
                "path": str(bindings["canonPath"]),
                "canonId": contract["visualCanon"]["canonId"],
                "sha256": bindings["canonSha256"],
                "status": bindings["contractValidation"]["visualCanon"]["status"],
            },
            "generator": {
                "path": str(self.tool_root / "blender" / "compile_asset.py"),
                "sha256": bindings["compilerSha256"],
            },
            "implementation": {
                "bridge": {
                    "path": str(self.tool_root / "blender" / "workbench_bridge.py"),
                    "sha256": file_sha256(self.tool_root / "blender" / "workbench_bridge.py"),
                },
                "sessionManager": {
                    "path": str(self.tool_root / "mcp" / "session_manager.py"),
                    "sha256": file_sha256(self.tool_root / "mcp" / "session_manager.py"),
                },
                "serverAdapter": {
                    "path": str(self.tool_root / "mcp" / "server_adapter.py"),
                    "sha256": file_sha256(self.tool_root / "mcp" / "server_adapter.py"),
                },
            },
            "reference": {
                "path": str(reference_path),
                "sha256": bindings["buildBlendSha256"],
                "semanticSha256": baseline["semanticSha256"],
                "readOnly": True,
            },
            "candidate": {
                "path": str(candidate_path) if normalized_mode == "EXPLORE" else None,
                "semanticSha256": baseline["semanticSha256"] if normalized_mode == "EXPLORE" else None,
            },
            "baseline": {
                "manifest": str(session_root / "base-scene-manifest.json"),
                "buildManifestSha256": bindings["buildManifestSha256"],
                "compilerSemanticSha256": bindings["buildSemanticSha256"],
            },
            "rollbackStack": [],
            "operationCount": 0,
            "decision": "REVISION_REQUIRED",
            "productionApproved": False,
        }
        write_json(session_root / "session.json", session)
        append_event(
            session_root / "Evidence" / "operations.jsonl",
            {"event": "SESSION_OPENED", "mode": normalized_mode, "at": utc_now()},
        )
        return {
            "status": "PASS",
            "session": str(session_root / "session.json"),
            "sessionId": identifier,
            "mode": normalized_mode,
            "referenceSemanticSha256": baseline["semanticSha256"],
            "captures": sorted(str(path) for path in (session_root / "Evidence" / "before" / "renders").glob("*.png")),
            "productionApproved": False,
        }

    def inspect_session(self, session_value: Path | str) -> dict[str, Any]:
        session_path, session = self._load_session(session_value)
        session_root = session_path.parent
        reference_path = Path(session["reference"]["path"])
        before_hash = file_sha256(reference_path)
        response = run_bridge(
            repo=self.repo,
            session_root=session_root,
            blend_path=reference_path,
            contract_path=Path(session["contract"]["path"]),
            action="inspect",
        )
        after_hash = file_sha256(reference_path)
        if before_hash != after_hash or after_hash != session["reference"]["sha256"]:
            raise WorkbenchError("read-only inspection changed the reference build")
        write_json(session_root / "scene-inspection.json", response["sceneManifest"])
        return {
            "status": "PASS",
            "sessionId": session["sessionId"],
            "sceneManifest": response["sceneManifest"],
            "referenceImmutability": "PASS",
        }

    def create_change_set(
        self, session_value: Path | str, draft: dict[str, Any]
    ) -> dict[str, Any]:
        session_path, session = self._load_session(session_value)
        if session["mode"] != "EXPLORE":
            raise WorkbenchError("OBSERVE sessions cannot create change sets")
        session_root = session_path.parent
        contract = _read_json(Path(session["contract"]["path"]))
        required_text = ("observation", "probableCause", "intent", "rollbackMethod")
        for name in required_text:
            if not isinstance(draft.get(name), str) or not draft[name].strip():
                raise WorkbenchError(f"change set draft requires {name}")
        operations = draft.get("operations")
        targets = list(dict.fromkeys(item.get("target") for item in operations or []))
        change_set = {
            "$schema": "https://roblox-top1.local/schemas/blender-change-set.schema.json",
            "schemaVersion": "1.0.0",
            "changeSetId": draft.get("changeSetId"),
            "sessionId": session["sessionId"],
            "assetKey": session["assetKey"],
            "baseBuildSha256": session["reference"]["sha256"],
            "assetContractSha256": session["contract"]["sha256"],
            "visualCanonId": session["visualCanon"]["canonId"],
            "visualCanonSha256": session["visualCanon"]["sha256"],
            "intent": draft["intent"],
            "observation": draft["observation"],
            "probableCause": draft["probableCause"],
            "targets": targets,
            "operations": operations,
            "preservedInvariants": draft.get("preservedInvariants"),
            "requiredViews": draft.get("requiredViews"),
            "expectedEffects": draft.get("expectedEffects", []),
            "maximumTriangleDelta": draft.get("maximumTriangleDelta", 0),
            "rollbackMethod": draft["rollbackMethod"],
            "productionAuthorized": False,
        }
        validate_change_set(change_set, session, contract)
        bindings = source_bindings(change_set, contract)
        write_json(session_root / "change-set.json", change_set)
        write_json(
            session_root / "source-patch.json",
            {
                "schemaVersion": "1.0.0",
                "changeSetId": change_set["changeSetId"],
                "bindings": bindings,
                "authoritativeSourceModified": False,
                "productionAuthorized": False,
            },
        )
        write_json(
            session_root / "diagnosis.json",
            {
                "schemaVersion": "1.0.0",
                "status": "PASS",
                "classification": draft.get("classification", "PROPORTION"),
                "observation": draft["observation"],
                "probableCause": draft["probableCause"],
                "canonConflict": False,
                "decision": "REVISION_REQUIRED",
            },
        )
        append_event(
            session_root / "Evidence" / "operations.jsonl",
            {"event": "CHANGE_SET_CREATED", "changeSetId": change_set["changeSetId"], "at": utc_now()},
        )
        return {
            "status": "PASS",
            "changeSet": str(session_root / "change-set.json"),
            "sourcePatch": str(session_root / "source-patch.json"),
            "sourcePromotable": all(item["sourcePromotable"] for item in bindings),
            "productionApproved": False,
        }

    def _load_change_set(self, value: Path | str) -> tuple[Path, dict[str, Any], Path, dict[str, Any], dict[str, Any]]:
        path = ensure_within(Path(value), self.assets_root, "change set")
        if path.name != "change-set.json" or not path.is_file():
            raise WorkbenchError("change set must reference an existing change-set.json")
        session_path, session = self._load_session(path.parent / "session.json")
        contract = _read_json(Path(session["contract"]["path"]))
        change_set = _read_json(path)
        validate_change_set(change_set, session, contract)
        return path, change_set, session_path, session, contract

    def _current_manifest(self, session_path: Path, session: dict[str, Any]) -> dict[str, Any]:
        response = run_bridge(
            repo=self.repo,
            session_root=session_path.parent,
            blend_path=Path(session["candidate"]["path"]),
            contract_path=Path(session["contract"]["path"]),
            action="inspect",
        )
        return response["sceneManifest"]

    def _invariant_report(
        self,
        *,
        session_path: Path,
        session: dict[str, Any],
        contract: dict[str, Any],
        change_set: dict[str, Any],
        candidate: dict[str, Any],
    ) -> dict[str, Any]:
        reference = _read_json(Path(session["baseline"]["manifest"]))
        return evaluate_invariants(
            reference=reference,
            candidate=candidate,
            contract=contract,
            requested=change_set["preservedInvariants"],
            maximum_triangle_delta=change_set["maximumTriangleDelta"],
            reference_hash_before=session["reference"]["sha256"],
            reference_hash_after=file_sha256(Path(session["reference"]["path"])),
            contract_hash_before=session["contract"]["sha256"],
            contract_hash_after=file_sha256(Path(session["contract"]["path"])),
            canon_hash_before=session["visualCanon"]["sha256"],
            canon_hash_after=file_sha256(Path(session["visualCanon"]["path"])),
        )

    def preview_change(self, change_set_value: Path | str) -> dict[str, Any]:
        _, change_set, session_path, session, contract = self._load_change_set(change_set_value)
        if session["mode"] != "EXPLORE":
            raise WorkbenchError("OBSERVE sessions cannot preview mutations")
        session_root = session_path.parent
        response = run_bridge(
            repo=self.repo,
            session_root=session_root,
            blend_path=Path(session["candidate"]["path"]),
            contract_path=Path(session["contract"]["path"]),
            action="preview",
            operations=change_set["operations"],
            capture_root=session_root / "Evidence" / "after-preview",
        )
        manifest = response["sceneManifest"]
        report = self._invariant_report(
            session_path=session_path,
            session=session,
            contract=contract,
            change_set=change_set,
            candidate=manifest,
        )
        diff = scene_diff(_read_json(Path(session["baseline"]["manifest"])), manifest)
        write_json(session_root / "contract-comparison.json", report)
        write_json(session_root / "geometry-diff.json", diff)
        write_json(session_root / "invariant-report.json", report)
        write_json(session_root / "preview-scene-manifest.json", manifest)
        append_event(
            session_root / "Evidence" / "operations.jsonl",
            {"event": "CHANGE_PREVIEWED", "status": report["status"], "at": utc_now()},
        )
        return {
            "status": report["status"],
            "sessionId": session["sessionId"],
            "candidateSemanticSha256": manifest["semanticSha256"],
            "invariantReport": str(session_root / "invariant-report.json"),
            "geometryDiff": str(session_root / "geometry-diff.json"),
            "captures": response["captures"],
            "candidateSaved": False,
            "productionApproved": False,
        }

    def apply_change(self, change_set_value: Path | str) -> dict[str, Any]:
        _, change_set, session_path, session, contract = self._load_change_set(change_set_value)
        if session["mode"] != "EXPLORE":
            raise WorkbenchError("OBSERVE sessions cannot apply mutations")
        session_root = session_path.parent
        candidate_path = Path(session["candidate"]["path"])
        before_manifest = self._current_manifest(session_path, session)
        sequence = session["operationCount"] + 1
        backup_path = session_root / "Evidence" / "rollback" / f"{sequence:04d}" / "candidate.blend"
        backup_path.parent.mkdir(parents=True, exist_ok=False)
        shutil.copy2(candidate_path, backup_path)
        try:
            response = run_bridge(
                repo=self.repo,
                session_root=session_root,
                blend_path=candidate_path,
                contract_path=Path(session["contract"]["path"]),
                action="mutate",
                operations=change_set["operations"],
                capture_root=session_root / "Evidence" / "after",
            )
            manifest = response["sceneManifest"]
            report = self._invariant_report(
                session_path=session_path,
                session=session,
                contract=contract,
                change_set=change_set,
                candidate=manifest,
            )
            if report["status"] != "PASS":
                raise WorkbenchError("candidate violated a preserved invariant")
        except Exception:
            shutil.copy2(backup_path, candidate_path)
            _make_writable(candidate_path)
            append_event(
                session_root / "Evidence" / "operations.jsonl",
                {"event": "CHANGE_AUTO_ROLLED_BACK", "sequence": sequence, "at": utc_now()},
            )
            raise
        diff = scene_diff(_read_json(Path(session["baseline"]["manifest"])), manifest)
        write_json(session_root / "candidate-scene-manifest.json", manifest)
        write_json(session_root / "geometry-diff.json", diff)
        write_json(session_root / "material-diff.json", {
            "schemaVersion": "1.0.0",
            "before": diff["materialsBefore"],
            "after": diff["materialsAfter"],
            "status": "PASS",
        })
        write_json(session_root / "invariant-report.json", report)
        session["operationCount"] = sequence
        session["candidate"]["semanticSha256"] = manifest["semanticSha256"]
        session["rollbackStack"].append(
            {
                "sequence": sequence,
                "backupPath": str(backup_path),
                "beforeSemanticSha256": before_manifest["semanticSha256"],
                "afterSemanticSha256": manifest["semanticSha256"],
                "changeSetId": change_set["changeSetId"],
            }
        )
        session["decision"] = "EXPLORATION_ACCEPTED"
        write_json(session_path, session)
        append_event(
            session_root / "Evidence" / "operations.jsonl",
            {"event": "CHANGE_APPLIED", "sequence": sequence, "semanticSha256": manifest["semanticSha256"], "at": utc_now()},
        )
        return {
            "status": "PASS",
            "sessionId": session["sessionId"],
            "candidateSemanticSha256": manifest["semanticSha256"],
            "rollbackDepth": len(session["rollbackStack"]),
            "referenceImmutability": "PASS",
            "productionApproved": False,
        }

    def revert_last_change(self, session_value: Path | str) -> dict[str, Any]:
        session_path, session = self._load_session(session_value)
        if session["mode"] != "EXPLORE" or not session["rollbackStack"]:
            raise WorkbenchError("there is no applied candidate change to revert")
        entry = session["rollbackStack"].pop()
        candidate_path = Path(session["candidate"]["path"])
        shutil.copy2(Path(entry["backupPath"]), candidate_path)
        _make_writable(candidate_path)
        manifest = self._current_manifest(session_path, session)
        if manifest["semanticSha256"] != entry["beforeSemanticSha256"]:
            raise WorkbenchError("rollback did not restore the expected semantic scene hash")
        if file_sha256(Path(session["reference"]["path"])) != session["reference"]["sha256"]:
            raise WorkbenchError("rollback detected reference build drift")
        session["candidate"]["semanticSha256"] = manifest["semanticSha256"]
        session["decision"] = "REVISION_REQUIRED"
        write_json(session_path, session)
        append_event(
            session_path.parent / "Evidence" / "operations.jsonl",
            {"event": "CHANGE_REVERTED", "sequence": entry["sequence"], "semanticSha256": manifest["semanticSha256"], "at": utc_now()},
        )
        return {
            "status": "PASS",
            "sessionId": session["sessionId"],
            "semanticSha256": manifest["semanticSha256"],
            "rollbackDepth": len(session["rollbackStack"]),
            "referenceImmutability": "PASS",
        }

    def reset_candidate(self, session_value: Path | str) -> dict[str, Any]:
        session_path, session = self._load_session(session_value)
        if session["mode"] != "EXPLORE":
            raise WorkbenchError("OBSERVE sessions have no candidate to reset")
        candidate_path = Path(session["candidate"]["path"])
        shutil.copy2(Path(session["reference"]["path"]), candidate_path)
        _make_writable(candidate_path)
        manifest = self._current_manifest(session_path, session)
        if manifest["semanticSha256"] != session["reference"]["semanticSha256"]:
            raise WorkbenchError("candidate reset differs from the reference semantic hash")
        session["rollbackStack"] = []
        session["candidate"]["semanticSha256"] = manifest["semanticSha256"]
        session["decision"] = "REVISION_REQUIRED"
        write_json(session_path, session)
        append_event(
            session_path.parent / "Evidence" / "operations.jsonl",
            {"event": "CANDIDATE_RESET", "at": utc_now()},
        )
        return {
            "status": "PASS",
            "sessionId": session["sessionId"],
            "semanticSha256": manifest["semanticSha256"],
            "referenceImmutability": "PASS",
        }

    def compare_candidate(self, session_value: Path | str) -> dict[str, Any]:
        session_path, session = self._load_session(session_value)
        if session["mode"] != "EXPLORE":
            raise WorkbenchError("OBSERVE sessions have no candidate to compare")
        candidate = self._current_manifest(session_path, session)
        reference = _read_json(Path(session["baseline"]["manifest"]))
        diff = scene_diff(reference, candidate)
        write_json(session_path.parent / "geometry-diff.json", diff)
        return {
            "status": "PASS",
            "sessionId": session["sessionId"],
            "changedComponentCount": len(diff["changedComponents"]),
            "triangleDelta": diff["triangleDelta"],
            "geometryDiff": str(session_path.parent / "geometry-diff.json"),
        }

    def prepare_promotion_sandbox(self, change_set_value: Path | str) -> dict[str, Any]:
        _, change_set, session_path, session, contract = self._load_change_set(change_set_value)
        if session["decision"] != "EXPLORATION_ACCEPTED":
            raise WorkbenchError("candidate change must be applied and accepted before promotion preparation")
        bindings = source_bindings(change_set, contract)
        if not all(item["sourcePromotable"] for item in bindings):
            raise WorkbenchError("change set contains an operation without deterministic source binding")
        sandbox = session_path.parent / "PromotionSandbox"
        sandbox.mkdir(parents=True, exist_ok=True)
        promoted = deepcopy(contract)
        for binding in bindings:
            current = _json_pointer_get(promoted, binding["jsonPointer"])
            if current != binding["before"]:
                raise WorkbenchError(
                    f"source pointer is stale: {binding['jsonPointer']} expected={binding['before']} actual={current}"
                )
            _json_pointer_set(promoted, binding["jsonPointer"], binding["after"])
        promoted["revision"] = contract["revision"] + 1
        promoted["visualCanon"]["path"] = session["visualCanon"]["path"]
        contract_path = sandbox / "asset.json"
        write_json(contract_path, promoted)
        validation = validate_contract(contract_path)
        if validation["status"] != "PASS":
            raise WorkbenchError("promotion sandbox contract is invalid: " + "; ".join(validation["errors"]))
        report = {
            "schemaVersion": "1.0.0",
            "status": "PASS",
            "changeSetId": change_set["changeSetId"],
            "sandboxContract": str(contract_path),
            "bindings": bindings,
            "authoritativeSourceModified": False,
            "productionApproved": False,
        }
        write_json(sandbox / "source-promotion-preparation.json", report)
        session["decision"] = "READY_FOR_SOURCE_PROMOTION"
        session["promotionSandbox"] = str(contract_path)
        write_json(session_path, session)
        append_event(
            session_path.parent / "Evidence" / "operations.jsonl",
            {"event": "PROMOTION_SANDBOX_PREPARED", "at": utc_now()},
        )
        return report

    def _compile(self, contract_path: Path, output: Path, session_root: Path) -> dict[str, Any]:
        output = ensure_within(output, session_root, "promotion build")
        if output.exists():
            shutil.rmtree(output)
        output.mkdir(parents=True)
        blender = find_blender()
        if blender is None:
            raise WorkbenchError("Blender not found")
        command = [
            str(blender),
            "--background",
            "--factory-startup",
            "--python",
            str(self.tool_root / "blender" / "compile_asset.py"),
            "--",
            str(contract_path),
            str(output),
        ]
        with RepositoryOperationLock(self.repo):
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                env=sanitized_blender_environment(),
                timeout=600,
            )
        (output / "workbench-compile.log").write_text(
            (completed.stdout or "") + (completed.stderr or ""), encoding="utf-8"
        )
        result_path = output / "compile-result.json"
        if completed.returncode != 0 or not result_path.is_file():
            raise WorkbenchError(f"promotion compilation failed: {output / 'workbench-compile.log'}")
        result = _read_json(result_path)
        if result.get("status") != "PASS":
            raise WorkbenchError("promotion compilation did not pass")
        return result

    def verify_promotion(
        self,
        session_value: Path | str,
        authoritative_contract_value: Path | str,
    ) -> dict[str, Any]:
        session_path, session = self._load_session(
            session_value, allow_contract_drift=True
        )
        if session.get("decision") != "READY_FOR_SOURCE_PROMOTION":
            raise WorkbenchError("promotion sandbox has not been prepared")
        authoritative_contract = ensure_asset_contract(
            Path(authoritative_contract_value), self.repo
        )
        snapshot_value = session["contract"].get("snapshotPath")
        if not snapshot_value:
            raise WorkbenchError(
                "workbench session predates immutable contract snapshots; "
                "open a new session before verifying source promotion"
            )
        baseline_contract_path = ensure_within(
            Path(snapshot_value), session_path.parent / "Reference", "contract snapshot"
        )
        if file_sha256(baseline_contract_path) != session["contract"]["sha256"]:
            raise WorkbenchError("immutable contract snapshot hash differs from the session")
        baseline_contract = _read_json(baseline_contract_path)
        change_set = _read_json(session_path.parent / "change-set.json")
        validate_change_set(change_set, session, baseline_contract)
        sandbox_contract = ensure_within(
            Path(session["promotionSandbox"]),
            session_path.parent / "PromotionSandbox",
            "promotion sandbox contract",
        )
        expected_promoted = _read_json(sandbox_contract)
        bindings = source_bindings(change_set, baseline_contract)
        for binding in bindings:
            if (
                _json_pointer_get(expected_promoted, binding["jsonPointer"])
                != binding["after"]
            ):
                raise WorkbenchError(f"promoted source does not contain {binding['jsonPointer']}={binding['after']}")
        authoritative_validation = validate_contract(authoritative_contract)
        if authoritative_validation["status"] != "PASS":
            raise WorkbenchError(
                "authoritative promoted contract is invalid: "
                + "; ".join(authoritative_validation["errors"])
            )
        authoritative_data = _read_json(authoritative_contract)
        source_equivalence = _compare_promoted_contract(
            session=session,
            expected=expected_promoted,
            authoritative=authoritative_data,
            authoritative_path=authoritative_contract,
        )
        session_root = session_path.parent
        report_path = session_root / "promotion-report.json"
        if not source_equivalence["passed"]:
            report = {
                "$schema": "https://roblox-top1.local/schemas/blender-promotion-report.schema.json",
                "schemaVersion": "1.0.0",
                "status": "FAIL",
                "sessionId": session["sessionId"],
                "changeSetId": change_set["changeSetId"],
                "sandboxContract": str(sandbox_contract),
                "authoritativeContract": str(authoritative_contract),
                "authoritativeContractSha256": file_sha256(authoritative_contract),
                "authoritativeSourceModified": file_sha256(authoritative_contract)
                != session["contract"]["sha256"],
                "sourceEquivalence": source_equivalence,
                "semanticDeterminism": {
                    "passed": False,
                    "status": "SKIPPED",
                    "reason": "authoritative source does not exactly reproduce the prepared promotion",
                    "buildA": None,
                    "buildB": None,
                },
                "binaryDeterminism": {
                    "passed": False,
                    "status": "SKIPPED",
                    "reason": "source equivalence failed",
                    "artifacts": {},
                },
                "candidateReproduction": {
                    "passed": False,
                    "status": "SKIPPED",
                    "reason": "source equivalence failed",
                    "checks": [],
                },
                "productionApproved": False,
            }
            write_json(report_path, report)
            append_event(
                session_root / "Evidence" / "operations.jsonl",
                {
                    "event": "PROMOTION_VERIFIED",
                    "status": "FAIL",
                    "reason": "SOURCE_EQUIVALENCE",
                    "at": utc_now(),
                },
            )
            return report
        build_a = session_root / "PromotionVerification" / "build-a"
        build_b = session_root / "PromotionVerification" / "build-b"
        self._compile(authoritative_contract, build_a, session_root)
        self._compile(authoritative_contract, build_b, session_root)
        provenance_a = _read_json(build_a / "provenance.json")
        provenance_b = _read_json(build_b / "provenance.json")
        deterministic = provenance_a["semanticSha256"] == provenance_b["semanticSha256"]
        manifest_a = _read_json(build_a / "manifest.json")
        manifest_b = _read_json(build_b / "manifest.json")
        binary_checks = {
            name: {
                "buildA": manifest_a["artifacts"][name]["sha256"],
                "buildB": manifest_b["artifacts"][name]["sha256"],
                "passed": manifest_a["artifacts"][name]["sha256"]
                == manifest_b["artifacts"][name]["sha256"],
            }
            for name in ("glb", "fbxUpdate")
        }
        binary_deterministic = all(item["passed"] for item in binary_checks.values())
        candidate_manifest = self._current_manifest(session_path, session)
        compiled_manifest = run_bridge(
            repo=self.repo,
            session_root=session_root,
            blend_path=build_a / "source.blend",
            contract_path=authoritative_contract,
            action="inspect",
        )["sceneManifest"]
        candidate_objects = {item["name"]: item for item in candidate_manifest["objects"]}
        compiled_objects = {item["name"]: item for item in compiled_manifest["objects"]}
        reproduction_checks: list[dict[str, Any]] = []
        for operation in change_set["operations"]:
            if operation["type"] == "SET_COMPONENT_DIMENSION":
                axis = {"designX": 0, "designY": 1, "designZ": 2}[operation["axis"]]
                candidate_value = candidate_objects[operation["target"]]["designDimensions"][axis]
                compiled_value = compiled_objects[operation["target"]]["designDimensions"][axis]
            elif operation["type"] == "MOVE_COMPONENT":
                axis = {"designX": 0, "designY": 1, "designZ": 2}[operation["axis"]]
                candidate_value = candidate_objects[operation["target"]]["designLocation"][axis]
                compiled_value = compiled_objects[operation["target"]]["designLocation"][axis]
            elif operation["type"] == "SET_MATERIAL_ROLE":
                candidate_value = candidate_objects[operation["target"]]["materials"][0]
                compiled_value = compiled_objects[operation["target"]]["materials"][0]
            elif operation["type"] == "SET_MATERIAL_VALUE":
                candidate_materials = {item["name"]: item for item in candidate_manifest["materials"]}
                compiled_materials = {item["name"]: item for item in compiled_manifest["materials"]}
                candidate_value = candidate_materials[operation["target"]][operation["property"]]
                compiled_value = compiled_materials[operation["target"]][operation["property"]]
            elif operation["type"] == "ROTATE_COMPONENT":
                candidate_value = candidate_objects[operation["target"]]["boundsDesign"]
                compiled_value = compiled_objects[operation["target"]]["boundsDesign"]
            else:
                candidate_value = operation["after"]
                compiled_value = operation["after"]
            reproduction_checks.append(
                {
                    "operationType": operation["type"],
                    "target": operation["target"],
                    "candidate": candidate_value,
                    "compiled": compiled_value,
                    "passed": candidate_value == compiled_value,
                }
            )
        reproduced = all(item["passed"] for item in reproduction_checks)
        status = (
            "PASS"
            if source_equivalence["passed"]
            and deterministic
            and binary_deterministic
            and reproduced
            else "FAIL"
        )
        report = {
            "$schema": "https://roblox-top1.local/schemas/blender-promotion-report.schema.json",
            "schemaVersion": "1.0.0",
            "status": status,
            "sessionId": session["sessionId"],
            "changeSetId": change_set["changeSetId"],
            "sandboxContract": str(sandbox_contract),
            "authoritativeContract": str(authoritative_contract),
            "authoritativeContractSha256": file_sha256(authoritative_contract),
            "authoritativeSourceModified": True,
            "sourceEquivalence": source_equivalence,
            "semanticDeterminism": {
                "passed": deterministic,
                "buildA": provenance_a["semanticSha256"],
                "buildB": provenance_b["semanticSha256"],
            },
            "binaryDeterminism": {
                "passed": binary_deterministic,
                "artifacts": binary_checks,
            },
            "candidateReproduction": {
                "passed": reproduced,
                "checks": reproduction_checks,
            },
            "productionApproved": False,
        }
        write_json(report_path, report)
        if status == "PASS":
            session["decision"] = "SOURCE_PROMOTION_VERIFIED"
            session["verifiedPromotion"] = {
                "report": str(report_path),
                "reportSha256": file_sha256(report_path),
                "authoritativeContractSha256": file_sha256(authoritative_contract),
            }
            write_json(session_path, session)
        append_event(
            session_root / "Evidence" / "operations.jsonl",
            {"event": "PROMOTION_VERIFIED", "status": status, "at": utc_now()},
        )
        return report

    def close_session(self, session_value: Path | str) -> dict[str, Any]:
        unchecked_path = self._session_path(session_value)
        unchecked_session = _read_json(unchecked_path)
        promotion_verified = (
            unchecked_session.get("decision") == "SOURCE_PROMOTION_VERIFIED"
        )
        session_path, session = self._load_session(
            session_value, allow_contract_drift=promotion_verified
        )
        if promotion_verified:
            verification = session.get("verifiedPromotion") or {}
            report_path = Path(verification.get("report", ""))
            current_contract = Path(session["contract"]["path"])
            if (
                not report_path.is_file()
                or file_sha256(report_path) != verification.get("reportSha256")
                or not current_contract.is_file()
                or file_sha256(current_contract)
                != verification.get("authoritativeContractSha256")
            ):
                raise WorkbenchError(
                    "verified promotion evidence or authoritative source drifted before close"
                )
        session["lifecycle"] = "CLOSED"
        session["closedAt"] = utc_now()
        write_json(session_path, session)
        append_event(
            session_path.parent / "Evidence" / "operations.jsonl",
            {"event": "SESSION_CLOSED", "at": utc_now()},
        )
        return {
            "status": "PASS",
            "sessionId": session["sessionId"],
            "lifecycle": "CLOSED",
            "evidencePreserved": True,
            "productionApproved": False,
        }
