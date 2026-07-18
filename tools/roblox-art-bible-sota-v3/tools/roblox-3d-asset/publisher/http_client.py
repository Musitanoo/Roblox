from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any


API_ROOT = "https://apis.roblox.com/assets/v1"


class ApiError(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


def _decode_json(payload: bytes) -> dict[str, Any]:
    if not payload:
        return {}
    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, dict):
        raise ApiError("Open Cloud returned a non-object JSON response")
    return value


def _request(
    method: str,
    url: str,
    api_key: str,
    *,
    body: bytes | None = None,
    content_type: str | None = None,
    attempts: int = 4,
) -> dict[str, Any]:
    headers = {"x-api-key": api_key, "Accept": "application/json"}
    if content_type:
        headers["Content-Type"] = content_type
    for attempt in range(attempts):
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                return _decode_json(response.read())
        except urllib.error.HTTPError as error:
            response = error.read(4096).decode("utf-8", errors="replace")
            retryable = error.code == 429 or 500 <= error.code < 600
            if retryable and attempt + 1 < attempts:
                time.sleep(min(15.0, (2**attempt) + random.random()))
                continue
            raise ApiError(
                f"Open Cloud HTTP {error.code}: {response}", status_code=error.code, retryable=retryable
            ) from error
        except urllib.error.URLError as error:
            if attempt + 1 < attempts:
                time.sleep(min(15.0, (2**attempt) + random.random()))
                continue
            raise ApiError(f"Open Cloud network error: {error.reason}", retryable=True) from error
    raise ApiError("Open Cloud request exhausted retries", retryable=True)


def multipart_body(request_value: dict[str, Any], file_path: Path, media_type: str) -> tuple[bytes, str]:
    boundary = "r3d-" + uuid.uuid4().hex
    request_json = json.dumps(request_value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    file_payload = file_path.read_bytes()
    chunks = [
        f"--{boundary}\r\n".encode(),
        b'Content-Disposition: form-data; name="request"\r\n',
        b"Content-Type: application/json\r\n\r\n",
        request_json,
        b"\r\n",
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="fileContent"; filename="{file_path.name}"\r\n'.encode(),
        f"Content-Type: {media_type}\r\n\r\n".encode(),
        file_payload,
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ]
    return b"".join(chunks), f"multipart/form-data; boundary={boundary}"


def mutate_asset(
    method: str,
    path: str,
    api_key: str,
    request_value: dict[str, Any],
    file_path: Path,
    media_type: str,
) -> dict[str, Any]:
    body, content_type = multipart_body(request_value, file_path, media_type)
    return _request(method, API_ROOT + path, api_key, body=body, content_type=content_type)


def get_json(path: str, api_key: str) -> dict[str, Any]:
    return _request("GET", API_ROOT + path, api_key)


def poll_operation(operation_path: str, api_key: str, *, attempts: int = 30) -> dict[str, Any]:
    normalized = operation_path.removeprefix("operations/")
    for attempt in range(attempts):
        operation = get_json(f"/operations/{normalized}", api_key)
        if operation.get("done"):
            if operation.get("error"):
                raise ApiError(f"Open Cloud operation failed: {json.dumps(operation['error'], ensure_ascii=False)}")
            return operation
        if attempt + 1 < attempts:
            time.sleep(min(10.0, 1.0 + attempt * 0.5))
    raise ApiError("Open Cloud operation did not finish within the bounded polling window", retryable=True)
