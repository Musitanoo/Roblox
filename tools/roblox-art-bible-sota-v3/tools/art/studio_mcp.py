from __future__ import annotations

import json
import os
import queue
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from tools.art.common import sanitized_subprocess_environment


class StudioMcpError(RuntimeError):
    pass


def discover_studio_mcp() -> Path:
    explicit = os.environ.get("ROBLOX_STUDIO_MCP_EXE")
    if explicit:
        path = Path(explicit)
        if path.is_file():
            return path.resolve()
        raise StudioMcpError("ROBLOX_STUDIO_MCP_EXE does not point to a file")
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise StudioMcpError("LOCALAPPDATA is unavailable")
    candidates = list(
        (Path(local) / "Roblox/Versions").glob("version-*/StudioMCP.exe")
    )
    if not candidates:
        raise StudioMcpError("Roblox Studio MCP executable was not found")
    return max(candidates, key=lambda path: path.stat().st_mtime).resolve()


class StudioMcpClient:
    def __init__(self, executable: Path | None = None) -> None:
        self.executable = executable or discover_studio_mcp()
        self.process = subprocess.Popen(
            [str(self.executable)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            env=sanitized_subprocess_environment(),
        )
        if self.process.stdin is None or self.process.stdout is None:
            raise StudioMcpError("Studio MCP stdio pipes are unavailable")
        self._messages: queue.Queue[dict[str, Any]] = queue.Queue()
        self._stderr: queue.Queue[str] = queue.Queue()
        self._next_id = 1
        threading.Thread(
            target=self._pump_stdout,
            daemon=True,
        ).start()
        if self.process.stderr is not None:
            threading.Thread(
                target=self._pump_stderr,
                daemon=True,
            ).start()
        initialize = self.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "roblox-art-direction-workflow",
                    "version": "3.5.0",
                },
            },
            timeout=15,
        )
        if "result" not in initialize:
            raise StudioMcpError("Studio MCP initialize did not return a result")
        self.notify("notifications/initialized", {})
        tools = self.request("tools/list", {}, timeout=15)
        self.tool_names = {
            item["name"]
            for item in tools.get("result", {}).get("tools", [])
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }

    def _pump_stdout(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            try:
                message = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(message, dict):
                self._messages.put(message)

    def _pump_stderr(self) -> None:
        assert self.process.stderr is not None
        for line in self.process.stderr:
            self._stderr.put(line.rstrip("\r\n"))

    def _send(self, value: dict[str, Any]) -> None:
        if self.process.poll() is not None:
            raise StudioMcpError("Studio MCP process exited unexpectedly")
        assert self.process.stdin is not None
        self.process.stdin.write(
            json.dumps(value, separators=(",", ":"), ensure_ascii=False) + "\n"
        )
        self.process.stdin.flush()

    def request(
        self,
        method: str,
        params: dict[str, Any],
        *,
        timeout: float = 30,
    ) -> dict[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        self._send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params,
            }
        )
        deadline = time.monotonic() + timeout
        deferred: list[dict[str, Any]] = []
        try:
            while time.monotonic() < deadline:
                try:
                    message = self._messages.get(timeout=0.2)
                except queue.Empty:
                    continue
                if message.get("id") == request_id:
                    if "error" in message:
                        raise StudioMcpError(
                            f"Studio MCP request {method} returned an error"
                        )
                    return message
                deferred.append(message)
        finally:
            for message in deferred:
                self._messages.put(message)
        raise StudioMcpError(f"Studio MCP request {method} timed out")

    def notify(self, method: str, params: dict[str, Any]) -> None:
        self._send(
            {
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
            }
        )

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any],
        *,
        timeout: float = 45,
    ) -> dict[str, Any]:
        if name not in self.tool_names:
            raise StudioMcpError(f"Studio MCP tool is unavailable: {name}")
        response = self.request(
            "tools/call",
            {"name": name, "arguments": arguments},
            timeout=timeout,
        )
        result = response.get("result")
        if not isinstance(result, dict):
            raise StudioMcpError(f"Studio MCP tool returned no result: {name}")
        if result.get("isError") is True:
            raise StudioMcpError(f"Studio MCP tool reported an error: {name}")
        return result

    @staticmethod
    def text_content(result: dict[str, Any]) -> str:
        content = result.get("content", [])
        if not isinstance(content, list):
            return ""
        return "\n".join(
            item["text"]
            for item in content
            if isinstance(item, dict)
            and item.get("type") == "text"
            and isinstance(item.get("text"), str)
        )

    @classmethod
    def json_content(cls, result: dict[str, Any]) -> Any:
        text = cls.text_content(result)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise StudioMcpError("Studio MCP tool did not return JSON text") from exc

    def select_only_studio(self) -> dict[str, Any]:
        studios: list[dict[str, Any]] = []
        for _attempt in range(5):
            payload = self.json_content(
                self.call_tool("list_roblox_studios", {}, timeout=15)
            )
            studios = (
                payload.get("studios", [])
                if isinstance(payload, dict)
                else []
            )
            if len(studios) == 1:
                break
            time.sleep(1)
        if len(studios) != 1:
            raise StudioMcpError(
                "exactly one Roblox Studio instance is required"
            )
        studio_id = studios[0].get("id")
        if not isinstance(studio_id, str):
            raise StudioMcpError("Studio instance has no selectable identifier")
        self.call_tool(
            "set_active_studio",
            {"studio_id": studio_id},
            timeout=15,
        )
        return {"count": 1, "name": studios[0].get("name")}

    def close(self) -> None:
        if self.process.poll() is not None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            self.process.kill()

    def __enter__(self) -> "StudioMcpClient":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
