from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, load_json, sha256_file, validate_with_schema, write_json

LABELS = ["A", "B", "C"]


def _fail(message: str, code: int = 1) -> int:
    print(f"[FAIL] {message}")
    return code


def _task_contract(protocol: dict[str, Any]) -> tuple[set[str], dict[str, str]]:
    task_ids: set[str] = set()
    group_by_task: dict[str, str] = {}
    for group_id, group in protocol["taskGroups"].items():
        for task in group["tasks"]:
            task_ids.add(task["taskId"])
            group_by_task[task["taskId"]] = group_id
    return task_ids, group_by_task


def score(submissions_path: Path, blind_map_path: Path) -> dict[str, Any]:
    submissions = load_json(submissions_path)
    blind_map = load_json(blind_map_path)
    rubric = load_json(ROOT / "art/qa/visual-rubric.json")
    protocol = load_json(ROOT / "art/qa/task-protocol.json")

    errors = validate_with_schema(submissions, ROOT / "schemas/reviewer-submissions.schema.json")
    errors += validate_with_schema(blind_map, ROOT / "schemas/blind-map.schema.json")
    if errors:
        return {"status": "BLOCKED", "issues": errors}
    if submissions["status"] != "SEALED":
        return {"status": "BLOCKED", "issues": ["Submissions must be SEALED before unblinding."]}
    if submissions["studyId"] != blind_map["studyId"] or submissions["studyId"] != protocol["studyId"]:
        return {"status": "BLOCKED", "issues": ["Study IDs do not match."]}
    if sha256_file(submissions_path) != blind_map["sealedSubmissionsSha256"]:
        return {"status": "BLOCKED", "issues": ["Blind map does not match the sealed submissions SHA-256."]}
    if set(blind_map["mapping"].values()) != {"industrial-toy-defense", "salvaged-frontier", "clean-tactical-diorama"}:
        return {"status": "BLOCKED", "issues": ["Blind map must be a bijection over all three territories."]}

    task_ids, group_by_task = _task_contract(protocol)
    expected_responses = {(label, task_id) for label in LABELS for task_id in task_ids}
    issues: list[str] = []

    participant_ids = [participant["participantId"] for participant in submissions["participants"]]
    if len(participant_ids) != len(set(participant_ids)):
        issues.append("participantId values must be unique")
    reviewer_ids = [reviewer["reviewerId"] for reviewer in submissions["expertReviews"]]
    if len(reviewer_ids) != len(set(reviewer_ids)):
        issues.append("reviewerId values must be unique")
    for participant in submissions["participants"]:
        observed = {(r["blindLabel"], r["taskId"]) for r in participant["responses"]}
        if observed != expected_responses:
            missing = sorted(expected_responses - observed)
            extra = sorted(observed - expected_responses)
            issues.append(f"{participant['participantId']}: response matrix mismatch; missing={missing}, extra={extra}")

    dimension_ids = set(rubric["dimensions"])
    expected_ratings = {(label, dim) for label in LABELS for dim in dimension_ids}
    for reviewer in submissions["expertReviews"]:
        observed = {(r["blindLabel"], r["dimensionId"]) for r in reviewer["ratings"]}
        if observed != expected_ratings:
            missing = sorted(expected_ratings - observed)
            extra = sorted(observed - expected_ratings)
            issues.append(f"{reviewer['reviewerId']}: rating matrix mismatch; missing={missing}, extra={extra}")

    technical_ids = {gate_id for gate_id, gate in rubric["hardGates"].items() if gate["kind"] == "technical_boolean"}
    for label in LABELS:
        evidence_by_id = submissions["technicalEvidenceByBlindLabel"][label]
        observed = set(evidence_by_id)
        if observed != technical_ids:
            issues.append(f"{label}: technical evidence IDs must equal {sorted(technical_ids)}; observed {sorted(observed)}")
            continue
        for gate_id, evidence in evidence_by_id.items():
            evidence_path = (ROOT / evidence["evidencePath"]).resolve()
            try:
                evidence_path.relative_to(ROOT.resolve())
            except ValueError:
                issues.append(f"{label}/{gate_id}: evidencePath escapes the repository root")
                continue
            if not evidence_path.is_file():
                issues.append(f"{label}/{gate_id}: evidence file does not exist: {evidence['evidencePath']}")
                continue
            actual_hash = sha256_file(evidence_path)
            if actual_hash != evidence["sha256"]:
                issues.append(f"{label}/{gate_id}: evidence SHA-256 mismatch")
    if issues:
        return {"status": "BLOCKED", "issues": issues}

    correct_by_label_group: dict[tuple[str, str], list[bool]] = defaultdict(list)
    confidence_by_label: dict[str, list[float]] = defaultdict(list)
    for participant in submissions["participants"]:
        for response in participant["responses"]:
            group = group_by_task[response["taskId"]]
            correct_by_label_group[(response["blindLabel"], group)].append(response["correct"])
            confidence_by_label[response["blindLabel"]].append(response["confidence"])

    ratings_by_label_dim: dict[tuple[str, str], list[float]] = defaultdict(list)
    rating_confidence_by_label: dict[str, list[float]] = defaultdict(list)
    for reviewer in submissions["expertReviews"]:
        for rating in reviewer["ratings"]:
            ratings_by_label_dim[(rating["blindLabel"], rating["dimensionId"])].append(rating["score"])
            rating_confidence_by_label[rating["blindLabel"]].append(rating["confidence"])

    candidates: list[dict[str, Any]] = []
    for label in LABELS:
        hard_gates: dict[str, dict[str, Any]] = {}
        for gate_id, gate in rubric["hardGates"].items():
            if gate["kind"] == "task_rate":
                values = correct_by_label_group[(label, gate["taskGroupId"])]
                rate = sum(values) / len(values)
                participant_count = len(submissions["participants"])
                passed = participant_count >= gate["minimumParticipants"] and rate >= gate["minimumCorrectRate"]
                hard_gates[gate_id] = {"pass": passed, "correctRate": rate, "participants": participant_count}
            else:
                evidence = submissions["technicalEvidenceByBlindLabel"][label][gate_id]
                hard_gates[gate_id] = {"pass": evidence["pass"], "evidencePath": evidence["evidencePath"], "sha256": evidence["sha256"]}

        dimension_results: dict[str, dict[str, Any]] = {}
        weighted = 0.0
        floors_pass = True
        disagreement_pass = True
        for dim_id, dim in rubric["dimensions"].items():
            scores = ratings_by_label_dim[(label, dim_id)]
            mean = statistics.fmean(scores)
            spread = max(scores) - min(scores)
            floor_pass = mean >= dim["floor"]
            floors_pass &= floor_pass
            disagreement_pass &= spread <= rubric["reviewPolicy"]["maximumPostReconciliationDisagreement"]
            weighted += (mean / rubric["scale"]["max"]) * dim["weight"]
            dimension_results[dim_id] = {"mean": mean, "min": min(scores), "max": max(scores), "spread": spread, "floor": dim["floor"], "pass": floor_pass}

        all_confidence = confidence_by_label[label] + rating_confidence_by_label[label]
        median_confidence = statistics.median(all_confidence)
        all_hard = all(result["pass"] for result in hard_gates.values())
        score_pass = weighted >= rubric["weightedScoreMinimum"]
        confidence_pass = median_confidence >= rubric["reviewPolicy"]["minimumMedianConfidence"]
        eligible = all_hard and score_pass and floors_pass and disagreement_pass and confidence_pass
        candidates.append({
            "blindLabel": label,
            "territoryId": blind_map["mapping"][label],
            "eligible": eligible,
            "weightedScore": round(weighted, 4),
            "scorePass": score_pass,
            "dimensionFloorsPass": floors_pass,
            "reviewerDisagreementPass": disagreement_pass,
            "medianConfidence": round(median_confidence, 4),
            "confidencePass": confidence_pass,
            "hardGates": hard_gates,
            "dimensions": dimension_results,
        })

    ranking = sorted(
        ({"blindLabel": c["blindLabel"], "territoryId": c["territoryId"], "eligible": c["eligible"], "weightedScore": c["weightedScore"]} for c in candidates),
        key=lambda item: (item["eligible"], item["weightedScore"]), reverse=True,
    )
    return {
        "status": "COMPLETE",
        "studyId": submissions["studyId"],
        "selectionAuthority": "HUMAN_ONLY",
        "automaticSelection": None,
        "candidates": candidates,
        "ranking": ranking,
        "issues": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score sealed blind-study evidence without selecting a territory.")
    parser.add_argument("submissions", type=Path)
    parser.add_argument("blind_map", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/human/scoring-report.json")
    parser.add_argument("--require-eligible", action="store_true")
    args = parser.parse_args()
    report = score(args.submissions, args.blind_map)
    write_json(args.output, report)
    if report["status"] == "BLOCKED":
        for issue in report["issues"]:
            print(f"[BLOCKED] {issue}")
        return 2
    print(f"[PASS] Scoring complete. No automatic selection was made. Report: {args.output}")
    if args.require_eligible and not any(c["eligible"] for c in report["candidates"]):
        print("[FAIL] No candidate is eligible.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
