from __future__ import annotations

from pathlib import Path

from tools.art.blind_study import (
    LABELS,
    TASKS,
    _participant_assignments,
    _privacy_scan,
)


def test_participant_assignments_are_complete_and_balanced() -> None:
    stimuli = [
        {
            "blindLabel": label,
            "taskId": task["taskId"],
            "path": f"stimuli/{label}/{index:02d}.png",
            "sha256": "0" * 64,
        }
        for label in LABELS
        for index, task in enumerate(TASKS, start=1)
    ]
    assignments = _participant_assignments("1" * 64, stimuli)
    expected = {(label, task["taskId"]) for label in LABELS for task in TASKS}
    assert len(assignments) == 12
    for assignment in assignments.values():
        observed = {(trial["blindLabel"], trial["taskId"]) for trial in assignment["trials"]}
        assert observed == expected
        assert len(assignment["trials"]) == 30


def test_public_privacy_scan_detects_candidate_identity(tmp_path: Path) -> None:
    clean = tmp_path / "clean"
    clean.mkdir()
    (clean / "index.html").write_text("Candidats A, B et C", encoding="utf-8")
    assert _privacy_scan(clean) == []

    leaked = tmp_path / "leaked"
    leaked.mkdir()
    (leaked / "index.html").write_text("industrial-toy-defense", encoding="utf-8")
    assert _privacy_scan(leaked)
