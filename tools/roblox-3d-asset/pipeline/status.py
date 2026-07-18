from __future__ import annotations

from enum import Enum


class Status(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"
    SKIPPED = "SKIPPED"


EXIT_CODES = {
    Status.PASS: 0,
    Status.FAIL: 2,
    Status.PARTIAL: 3,
    Status.BLOCKED: 4,
    Status.UNKNOWN: 5,
    Status.SKIPPED: 6,
}


def exit_code(status: str | Status) -> int:
    return EXIT_CODES[Status(status)]


def aggregate(statuses: list[str | Status]) -> Status:
    normalized = [Status(value) for value in statuses]
    if not normalized:
        return Status.UNKNOWN
    for candidate in (Status.FAIL, Status.BLOCKED, Status.PARTIAL, Status.UNKNOWN, Status.SKIPPED):
        if candidate in normalized:
            return candidate
    return Status.PASS
