from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Any

from tools.art.common import ROOT, load_json, validate_with_schema
from tools.art.evidence_validation import metric_order_issues, verify_artifacts


def _pct(candidate: float, baseline: float) -> float:
    if baseline <= 0:
        raise ValueError("baseline must be positive")
    return (candidate / baseline - 1.0) * 100.0


def _close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=0.0, abs_tol=0.01)


def validate_report(path: Path, *, require_pass: bool = False) -> dict[str, Any]:
    report = load_json(path)
    issues = validate_with_schema(report, ROOT / "schemas/performance-report.schema.json")
    if issues:
        return {"status": "INVALID", "issues": issues}

    issues.extend(verify_artifacts(report["artifacts"], required_prefix="evidence/mobile/"))
    issues.extend(metric_order_issues("graybox", report["graybox"]))
    issues.extend(metric_order_issues("candidate", report["candidate"]))

    sequence = report["protocol"]["sequence"]
    if sequence.count("A") != sequence.count("B"):
        issues.append("protocol.sequence must contain equal graybox/candidate pass counts")
    if any(sequence[index] == sequence[index + 1] == sequence[index + 2] for index in range(len(sequence) - 2)):
        issues.append("protocol.sequence may not contain three identical conditions in a row")

    if report["status"] != "BLOCKED":
        graybox = report["graybox"]
        candidate = report["candidate"]
        regressions = report["regressions"]
        expected = {
            "frameTimeMedianPct": _pct(candidate["frameTimeMs"]["median"], graybox["frameTimeMs"]["median"]),
            "frameTimeP95Pct": _pct(candidate["frameTimeMs"]["p95"], graybox["frameTimeMs"]["p95"]),
            "memoryP95Mb": candidate["memoryMb"]["p95"] - graybox["memoryMb"]["p95"],
            "minimumFpsDelta": candidate["fps"]["minimum"] - graybox["fps"]["minimum"],
        }
        for key, expected_value in expected.items():
            if not _close(regressions[key], expected_value):
                issues.append(
                    f"regressions.{key} mismatch: expected {expected_value:.4f}, "
                    f"observed {regressions[key]:.4f}"
                )

        threshold = regressions["thresholds"]
        computed_pass = (
            expected["frameTimeMedianPct"] <= threshold["maxFrameTimeMedianPct"]
            and expected["frameTimeP95Pct"] <= threshold["maxFrameTimeP95Pct"]
            and expected["memoryP95Mb"] <= threshold["maxMemoryP95Mb"]
            and candidate["fps"]["minimum"] >= threshold["minimumCandidateFps"]
            and candidate["crashes"] <= threshold["crashesAllowed"]
            and (
                threshold["thermalThrottleAllowed"]
                or not candidate["thermal"]["throttleObserved"]
            )
        )
        if regressions["pass"] != computed_pass:
            issues.append("regressions.pass does not match the measured thresholds")

    if report["status"] == "PASS":
        serialized = str(report)
        if "UNEXECUTED" in serialized or report["device"]["deviceIdHash"] == "0" * 64:
            issues.append("PASS report contains template markers")
        kinds = {artifact["kind"] for artifact in report["artifacts"]}
        required = {"raw_metrics", "device_log", "landscape_screenshot", "portrait_screenshot"}
        missing = required - kinds
        if missing:
            issues.append(f"PASS mobile report lacks artifact kinds: {sorted(missing)}")
        if not ({"microprofiler_dump", "microprofiler_screenshot"} & kinds):
            issues.append("PASS mobile report lacks MicroProfiler evidence")
    if require_pass and report["status"] != "PASS":
        issues.append(f"Performance report status is {report['status']}; PASS required")

    return {
        "status": "PASS" if not issues else "FAIL",
        "reportedStatus": report["status"],
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate real-device Roblox mobile evidence.")
    parser.add_argument("report", type=Path)
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args()
    result = validate_report(args.report, require_pass=args.require_pass)
    if result["status"] == "PASS":
        print(f"[PASS] Performance report validated ({result['reportedStatus']}): {args.report}")
        return 0
    for issue in result["issues"]:
        print(f"[FAIL] {issue}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
