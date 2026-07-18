from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import r3d


class CompileStatesTests(unittest.TestCase):
    def test_failed_state_renders_as_explicit_unavailable_evidence(self) -> None:
        contract = {
            "displayName": "Test Barricade",
            "revision": 7,
            "states": {
                "variants": [
                    {"id": "intact", "description": "Ready"},
                    {"id": "damaged", "description": "Damaged"},
                ]
            },
            "renders": {"views": ["front"]},
        }
        page = r3d._state_review_html(
            contract,
            [
                {"stateId": "intact", "status": "PASS"},
                {
                    "status": "FAIL",
                    "errors": ["render stability failed"],
                },
            ],
            production_eligible=False,
        )

        self.assertIn("Rendu indisponible", page)
        self.assertIn("render stability failed", page)
        self.assertIn("./damaged/compile-result.json", page)
        self.assertNotIn("./damaged/renders/front.png", page)
        self.assertIn("status-fail", page)

    def test_blender_crash_cannot_reuse_stale_compile_result(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            contract = root / "asset.json"
            contract.write_text("{}", encoding="utf-8")
            output = root / "build"
            output.mkdir()
            stale = output / "compile-result.json"
            stale.write_text(
                json.dumps({"status": "PASS", "stateId": "old"}),
                encoding="utf-8",
            )
            completed = SimpleNamespace(
                returncode=2,
                stdout="",
                stderr="Blender crashed",
            )

            with patch.dict(
                os.environ,
                {"ROBLOX_OPEN_CLOUD_API_KEY": "must-not-reach-blender"},
                clear=False,
            ):
                with patch.object(
                    r3d.subprocess,
                    "run",
                    return_value=completed,
                ) as run_blender:
                    result = r3d._run_blender_compile(
                        contract,
                        output,
                        "damaged",
                        Path("blender.exe"),
                    )

        self.assertEqual("FAIL", result["status"])
        self.assertEqual("damaged", result["stateId"])
        self.assertEqual(str(output), result["output"])
        self.assertIn("did not produce", result["reason"])
        environment = run_blender.call_args.kwargs["env"]
        self.assertNotIn("ROBLOX_OPEN_CLOUD_API_KEY", environment)
        self.assertEqual("0", environment["PYTHONHASHSEED"])
        self.assertEqual("true", environment["DISABLE_TELEMETRY"])
        self.assertGreater(run_blender.call_args.kwargs["timeout"], 0)

    def test_failed_blender_result_is_normalized_with_state_identity(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            contract = root / "asset.json"
            contract.write_text("{}", encoding="utf-8")
            output = root / "build"

            def run_blender(*_args: object, **_kwargs: object) -> SimpleNamespace:
                (output / "compile-result.json").write_text(
                    json.dumps(
                        {
                            "status": "FAIL",
                            "errors": ["render did not stabilize"],
                        }
                    ),
                    encoding="utf-8",
                )
                return SimpleNamespace(returncode=2, stdout="", stderr="")

            with patch.object(r3d.subprocess, "run", side_effect=run_blender):
                result = r3d._run_blender_compile(
                    contract,
                    output,
                    "critical",
                    Path("blender.exe"),
                )

        self.assertEqual("FAIL", result["status"])
        self.assertEqual("critical", result["stateId"])
        self.assertEqual(str(output), result["output"])
        self.assertEqual(2, result["commandExitCode"])


if __name__ == "__main__":
    unittest.main()
