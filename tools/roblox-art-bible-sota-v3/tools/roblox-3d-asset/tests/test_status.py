from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.status import Status, aggregate, exit_code


class StatusTests(unittest.TestCase):
    def test_only_pass_returns_zero(self) -> None:
        self.assertEqual(0, exit_code(Status.PASS))
        for status in Status:
            if status is not Status.PASS:
                self.assertNotEqual(0, exit_code(status))

    def test_skipped_never_becomes_pass(self) -> None:
        self.assertEqual(Status.SKIPPED, aggregate([Status.PASS, Status.SKIPPED]))

    def test_fail_has_priority(self) -> None:
        self.assertEqual(Status.FAIL, aggregate([Status.UNKNOWN, Status.FAIL, Status.BLOCKED]))


if __name__ == "__main__":
    unittest.main()
