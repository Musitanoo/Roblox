from __future__ import annotations

import unittest
from pathlib import Path


STUDIO = Path(__file__).resolve().parents[1] / "studio"


class StudioScriptTests(unittest.TestCase):
    def test_no_script_is_named_atomic(self) -> None:
        self.assertFalse(any("atomic" in path.name.lower() for path in STUDIO.glob("*.luau")))

    def test_mutating_operator_scripts_default_to_dry_run(self) -> None:
        for name in (
            "configure_wrapper.luau",
            "staged_swap_visual.luau",
            "create_benchmark_scenes.luau",
            "activate_benchmark_scene.luau",
        ):
            source = (STUDIO / name).read_text(encoding="utf-8")
            self.assertIn("local DRY_RUN = true", source, name)

    def test_staged_swap_retains_rollback(self) -> None:
        source = (STUDIO / "staged_swap_visual.luau").read_text(encoding="utf-8")
        self.assertIn('operation = "REINSERT_STAGED_SWAP"', source)
        self.assertNotIn("oldRoot:Destroy()", source)


if __name__ == "__main__":
    unittest.main()
