from __future__ import annotations

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

from pipeline.doctor import _git, _git_candidates, find_git
from pipeline.status import Status


class DoctorTests(unittest.TestCase):
    def test_windows_candidates_include_standard_program_files_git(self) -> None:
        with (
            patch("pipeline.doctor.shutil.which", return_value=None),
            patch.dict(os.environ, {}, clear=True),
        ):
            candidates = {
                os.path.normcase(str(candidate))
                for candidate in _git_candidates(windows=True)
            }
        self.assertIn(
            os.path.normcase(r"C:\Program Files\Git\cmd\git.exe"),
            candidates,
        )

    def test_find_git_requires_an_executable_version_probe(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            candidate = Path(folder) / "git.exe"
            candidate.write_bytes(b"test")
            with patch(
                "pipeline.doctor._run",
                return_value=(0, "git version 2.51.0"),
            ) as run:
                discovered = find_git([candidate])
        self.assertEqual(candidate.resolve(), discovered)
        run.assert_called_once_with([str(candidate), "--version"])

    def test_find_git_rejects_unusable_file(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            candidate = Path(folder) / "git.exe"
            candidate.write_bytes(b"test")
            with patch(
                "pipeline.doctor._run",
                return_value=(1, "cannot execute"),
            ):
                self.assertIsNone(find_git([candidate]))

    def test_git_check_uses_discovered_absolute_executable(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            executable = (repo / "Git" / "cmd" / "git.exe").resolve()
            executable.parent.mkdir(parents=True)
            executable.write_bytes(b"test")
            status = SimpleNamespace(stdout="", returncode=0)
            with (
                patch(
                    "pipeline.doctor.find_git",
                    return_value=executable,
                ),
                patch(
                    "pipeline.doctor._run",
                    side_effect=[
                        (0, str(repo.resolve())),
                        (0, "0123456789abcdef"),
                    ],
                ),
                patch(
                    "pipeline.doctor.subprocess.run",
                    return_value=status,
                ) as run,
            ):
                result = _git(repo)
        self.assertEqual(Status.PASS.value, result["status"])
        self.assertEqual(str(executable), result["executable"])
        self.assertEqual(str(executable), run.call_args.args[0][0])


if __name__ == "__main__":
    unittest.main()
