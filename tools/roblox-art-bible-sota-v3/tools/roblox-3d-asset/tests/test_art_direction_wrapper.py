from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _project_root() -> Path:
    for candidate in (ROOT, *ROOT.parents):
        if (
            (candidate / "AGENTS.md").is_file()
            and (candidate / "scripts/art-direction.ps1").is_file()
        ):
            return candidate
    raise RuntimeError("host repository root was not found")


class ArtDirectionWrapperTests(unittest.TestCase):
    def test_help_command_and_long_alias_are_observable(self) -> None:
        powershell = shutil.which("powershell")
        if powershell is None:
            self.skipTest("PowerShell is unavailable")
        project = _project_root()
        wrapper = project / "scripts/art-direction.ps1"
        for help_argument in ("help", "--help"):
            with self.subTest(help_argument=help_argument):
                completed = subprocess.run(
                    [
                        powershell,
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(wrapper),
                        help_argument,
                    ],
                    cwd=project,
                    check=False,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                output = (completed.stdout + completed.stderr).strip()
                self.assertEqual(0, completed.returncode, output)
                self.assertIn("art-direction workflow", output)
                self.assertIn("doctor", output)
                self.assertIn("validate-canons", output)
                self.assertIn("never executes a workflow command", output)

    def test_non_help_argument_is_forwarded_to_installed_workflow(self) -> None:
        powershell = shutil.which("powershell")
        if powershell is None:
            self.skipTest("PowerShell is unavailable")
        project = _project_root()
        wrapper = project / "scripts/art-direction.ps1"
        probe = "__wrapper_forwarding_probe__"
        completed = subprocess.run(
            [
                powershell,
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(wrapper),
                probe,
            ],
            cwd=project,
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        output = (completed.stdout + completed.stderr).strip()
        self.assertNotEqual(0, completed.returncode)
        self.assertIn(probe, output)
        self.assertNotIn("Roblox art-direction workflow\n\nUsage:", output)


if __name__ == "__main__":
    unittest.main()
