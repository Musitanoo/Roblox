from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from mcp.security_policy import WorkbenchError
from mcp.session_manager import WorkbenchManager


def _schema(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


PATH = {"type": "string", "minLength": 1}
TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "get_blender_environment",
        "description": "Verify the exact Blender workbench environment and bounded tool surface.",
        "inputSchema": _schema({}),
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True},
    },
    {
        "name": "begin_workbench_session",
        "description": "Bind an immutable compiled build and open an OBSERVE or EXPLORE evidence session.",
        "inputSchema": _schema(
            {
                "contract": PATH,
                "mode": {"type": "string", "enum": ["OBSERVE", "EXPLORE"]},
                "sessionId": {"type": "string"},
            },
            ["contract", "mode"],
        ),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False},
    },
    {
        "name": "get_scene_manifest",
        "description": "Inspect the immutable reference scene and prove that its hash did not change.",
        "inputSchema": _schema({"session": PATH}, ["session"]),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True},
    },
    {
        "name": "create_change_set",
        "description": "Validate and persist a measurable bounded change set for an EXPLORE session.",
        "inputSchema": _schema(
            {"session": PATH, "draft": {"type": "object"}}, ["session", "draft"]
        ),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False},
    },
    {
        "name": "preview_change_set",
        "description": "Apply a change set in memory, render evidence, and leave the candidate file unchanged.",
        "inputSchema": _schema({"changeSet": PATH}, ["changeSet"]),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True},
    },
    {
        "name": "apply_change_set",
        "description": "Apply allow-listed operations only to the Candidate copy with automatic rollback on failure.",
        "inputSchema": _schema({"changeSet": PATH}, ["changeSet"]),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False},
    },
    {
        "name": "revert_last_change",
        "description": "Restore the previous Candidate semantic state and verify reference immutability.",
        "inputSchema": _schema({"session": PATH}, ["session"]),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False},
    },
    {
        "name": "reset_candidate",
        "description": "Reset Candidate from immutable Reference and prove semantic equality.",
        "inputSchema": _schema({"session": PATH}, ["session"]),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True},
    },
    {
        "name": "compare_candidate_to_reference",
        "description": "Write a structured geometry and material diff between Candidate and Reference.",
        "inputSchema": _schema({"session": PATH}, ["session"]),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True},
    },
    {
        "name": "prepare_promotion_sandbox",
        "description": "Translate source-bound operations into a session-contained contract without changing authoritative source.",
        "inputSchema": _schema({"changeSet": PATH}, ["changeSet"]),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True},
    },
    {
        "name": "verify_promotion",
        "description": "Prove that the authoritative contract exactly reproduces the prepared source promotion, compile it twice, and compare it with Candidate.",
        "inputSchema": _schema(
            {"session": PATH, "contract": PATH}, ["session", "contract"]
        ),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": True},
    },
    {
        "name": "close_workbench_session",
        "description": "Close a workbench session without deleting its evidence.",
        "inputSchema": _schema({"session": PATH}, ["session"]),
        "annotations": {"readOnlyHint": False, "destructiveHint": False, "idempotentHint": False},
    },
]


class WorkbenchMcpServer:
    def __init__(self, repo: Path) -> None:
        self.manager = WorkbenchManager(repo)

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name == "get_blender_environment":
            return self.manager.doctor()
        if name == "begin_workbench_session":
            return self.manager.begin_session(
                arguments["contract"],
                mode=arguments["mode"],
                session_id=arguments.get("sessionId"),
            )
        if name == "get_scene_manifest":
            return self.manager.inspect_session(arguments["session"])
        if name == "create_change_set":
            return self.manager.create_change_set(arguments["session"], arguments["draft"])
        if name == "preview_change_set":
            return self.manager.preview_change(arguments["changeSet"])
        if name == "apply_change_set":
            return self.manager.apply_change(arguments["changeSet"])
        if name == "revert_last_change":
            return self.manager.revert_last_change(arguments["session"])
        if name == "reset_candidate":
            return self.manager.reset_candidate(arguments["session"])
        if name == "compare_candidate_to_reference":
            return self.manager.compare_candidate(arguments["session"])
        if name == "prepare_promotion_sandbox":
            return self.manager.prepare_promotion_sandbox(arguments["changeSet"])
        if name == "verify_promotion":
            return self.manager.verify_promotion(
                arguments["session"], arguments["contract"]
            )
        if name == "close_workbench_session":
            return self.manager.close_session(arguments["session"])
        raise WorkbenchError(f"unknown or forbidden workbench tool: {name}")

    def handle(self, message: dict[str, Any]) -> dict[str, Any] | None:
        method = message.get("method")
        request_id = message.get("id")
        if request_id is None:
            return None
        if method == "initialize":
            requested = message.get("params", {}).get("protocolVersion", "2025-06-18")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": requested,
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "blender-visual-workbench", "version": "1.0.0"},
                    "instructions": (
                        "Diagnostic workbench only. Reference and canonical sources are immutable; "
                        "all production approval remains external."
                    ),
                },
            }
        if method == "ping":
            return {"jsonrpc": "2.0", "id": request_id, "result": {}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOL_DEFINITIONS}}
        if method == "tools/call":
            params = message.get("params", {})
            try:
                result = self.call_tool(params.get("name", ""), params.get("arguments", {}))
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True),
                            }
                        ],
                        "structuredContent": result,
                        "isError": result.get("status") in {"FAIL", "BLOCKED"},
                    },
                }
            except Exception as error:
                failure = {"status": "FAIL", "error": str(error), "productionApproved": False}
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(failure, ensure_ascii=False)}],
                        "structuredContent": failure,
                        "isError": True,
                    },
                }
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"method not found: {method}"},
        }

    def serve(self) -> int:
        for raw_line in sys.stdin:
            if not raw_line.strip():
                continue
            try:
                message = json.loads(raw_line)
                response = self.handle(message)
            except (json.JSONDecodeError, TypeError) as error:
                response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": str(error)},
                }
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
                sys.stdout.flush()
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    args = parser.parse_args()
    return WorkbenchMcpServer(Path(args.repo)).serve()


if __name__ == "__main__":
    raise SystemExit(main())
