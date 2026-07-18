from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.security_policy import FORBIDDEN_TOOL_NAMES
from mcp.server_adapter import TOOL_DEFINITIONS, WorkbenchMcpServer


REPO = ROOT.parents[1]


class WorkbenchMcpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.server = WorkbenchMcpServer(REPO)

    def test_forbidden_tools_are_not_exposed(self) -> None:
        names = {item["name"] for item in TOOL_DEFINITIONS}
        self.assertFalse(names & FORBIDDEN_TOOL_NAMES)
        self.assertNotIn("execute_python", names)

    def test_initialize_declares_tools_capability_and_authority_limit(self) -> None:
        response = self.server.handle(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-06-18"},
            }
        )
        self.assertEqual("2025-06-18", response["result"]["protocolVersion"])
        self.assertIn("immutable", response["result"]["instructions"])
        self.assertIn("tools", response["result"]["capabilities"])

    def test_tools_list_is_closed_and_schema_backed(self) -> None:
        response = self.server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = response["result"]["tools"]
        self.assertEqual(12, len(tools))
        self.assertTrue(all(tool["inputSchema"]["additionalProperties"] is False for tool in tools))
        verify = next(tool for tool in tools if tool["name"] == "verify_promotion")
        self.assertEqual(
            {"session", "contract"}, set(verify["inputSchema"]["required"])
        )

    def test_unknown_tool_fails_closed_without_traceback(self) -> None:
        response = self.server.handle(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "execute_arbitrary_python", "arguments": {}},
            }
        )
        self.assertTrue(response["result"]["isError"])
        payload = json.loads(response["result"]["content"][0]["text"])
        self.assertEqual("FAIL", payload["status"])
        self.assertNotIn("traceback", payload)

    def test_project_config_uses_stdio_launcher_and_write_approvals(self) -> None:
        config_path = REPO / ".codex" / "config.toml"
        if not config_path.is_file():
            self.skipTest("project MCP config is installed by the host repository")
        config = config_path.read_text(encoding="utf-8")
        self.assertIn("r3d-mcp.ps1", config)
        self.assertIn('default_tools_approval_mode = "writes"', config)
        self.assertNotIn("http://", config)
        self.assertNotIn("ROBLOX_OPEN_CLOUD_API_KEY", config)


if __name__ == "__main__":
    unittest.main()
