from __future__ import annotations

import argparse
import html
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.contract import validate_contract  # noqa: E402
from pipeline.determinism import (  # noqa: E402
    compare_published_state_build,
    compare_state_builds,
    sha256_file,
)
from pipeline.doctor import find_blender, run_doctor  # noqa: E402
from pipeline.state_variants import available_state_ids  # noqa: E402
from pipeline.status import Status, aggregate, exit_code  # noqa: E402
from mcp.security_policy import sanitized_blender_environment  # noqa: E402

BLENDER_TIMEOUT_SECONDS = 1200


def emit(result: dict) -> int:
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code(result.get("status", Status.UNKNOWN.value))


def command_doctor(args: argparse.Namespace) -> int:
    return emit(run_doctor(Path(args.repo).resolve()))


def command_validate(args: argparse.Namespace) -> int:
    return emit(validate_contract(Path(args.contract).resolve()))


def _run_blender_compile(
    contract: Path,
    output: Path,
    state_id: str,
    blender: Path,
) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    result_path = output / "compile-result.json"
    # Never reuse a prior result when Blender crashes before writing evidence.
    result_path.unlink(missing_ok=True)
    command = [
        str(blender),
        "--background",
        "--factory-startup",
        "--python",
        str(ROOT / "blender" / "compile_asset.py"),
        "--",
        str(contract),
        str(output),
        state_id,
    ]
    # Blender's FBX exporter derives internal IDs from Python hash(). The
    # sanitized environment fixes that seed without exposing host credentials.
    blender_environment = sanitized_blender_environment()
    log = output / "blender.log"
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            env=blender_environment,
            timeout=BLENDER_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        stdout = (
            error.stdout.decode(errors="replace")
            if isinstance(error.stdout, bytes)
            else (error.stdout or "")
        )
        stderr = (
            error.stderr.decode(errors="replace")
            if isinstance(error.stderr, bytes)
            else (error.stderr or "")
        )
        log.write_text(stdout + stderr, encoding="utf-8")
        return {
            "status": Status.FAIL.value,
            "stateId": state_id,
            "output": str(output),
            "commandExitCode": 124,
            "log": str(log),
            "reason": f"Blender timed out after {BLENDER_TIMEOUT_SECONDS} seconds",
        }
    log.write_text((completed.stdout or "") + (completed.stderr or ""), encoding="utf-8")
    if result_path.is_file():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result.setdefault("stateId", state_id)
        result.setdefault("output", str(output))
        result["commandExitCode"] = completed.returncode
        result["log"] = str(log)
        if completed.returncode != 0 and result.get("status") == Status.PASS.value:
            result["status"] = Status.FAIL.value
            result.setdefault("errors", []).append("Blender returned a non-zero exit code")
        return result
    return {
        "status": Status.FAIL.value,
        "stateId": state_id,
        "output": str(output),
        "commandExitCode": completed.returncode,
        "log": str(log),
        "reason": "Blender did not produce compile-result.json",
    }


def command_compile(args: argparse.Namespace) -> int:
    contract = Path(args.contract).resolve()
    validation = validate_contract(contract)
    if validation["status"] != Status.PASS.value:
        return emit(validation)
    contract_data = json.loads(contract.read_text(encoding="utf-8"))
    state_id = args.state or contract_data["states"]["default"]
    if state_id not in available_state_ids(contract_data):
        return emit(
            {
                "status": Status.FAIL.value,
                "reason": f"unknown state {state_id!r}",
                "availableStates": available_state_ids(contract_data),
            }
        )
    blender = find_blender()
    if not blender:
        return emit({"status": Status.BLOCKED.value, "reason": "Blender not found"})
    if args.output:
        output = Path(args.output).resolve()
    elif state_id == contract_data["states"]["default"]:
        output = contract.parent / "build"
    else:
        output = contract.parent / "build" / "states" / state_id
    return emit(_run_blender_compile(contract, output, state_id, blender))


def _state_review_html(
    contract_data: dict,
    results: list[dict],
    production_eligible: bool,
) -> str:
    variants = {
        variant["id"]: variant
        for variant in contract_data["states"]["variants"]
    }
    declared_state_ids = list(variants)
    state_ids = [
        (
            str(result["stateId"])
            if isinstance(result.get("stateId"), str)
            and result["stateId"] in variants
            else (
                declared_state_ids[index]
                if index < len(declared_state_ids)
                else f"unknown-{index + 1}"
            )
        )
        for index, result in enumerate(results)
    ]
    views = contract_data["renders"]["views"]
    headers = "".join(
        (
            "<th scope=\"col\">"
            f"<strong>{html.escape(state_id.upper())}</strong>"
            f"<span class=\"status status-{html.escape(str(result.get('status', 'UNKNOWN')).lower())}\">"
            f"{html.escape(str(result.get('status', 'UNKNOWN')))}</span>"
            f"<small>{html.escape(variants.get(state_id, {}).get('description', 'État non lié au contrat'))}</small>"
            "</th>"
        )
        for state_id, result in zip(state_ids, results, strict=True)
    )
    rows = []
    for view in views:
        cells = []
        for state_id, result in zip(state_ids, results, strict=True):
            if result.get("status") == Status.PASS.value:
                cells.append(
                    "<td>"
                    f"<a href=\"./{html.escape(state_id)}/renders/"
                    f"{html.escape(view)}.png\">"
                    f"<img src=\"./{html.escape(state_id)}/renders/"
                    f"{html.escape(view)}.png\" "
                    f"alt=\"{html.escape(state_id)} — {html.escape(view)}\">"
                    "</a>"
                    "</td>"
                )
                continue
            errors = result.get("errors")
            reason = (
                str(errors[0])
                if isinstance(errors, list) and errors
                else str(result.get("reason", "Compilation failed"))
            )
            cells.append(
                "<td class=\"unavailable\">"
                "<strong>Rendu indisponible</strong>"
                f"<small>{html.escape(reason)}</small>"
                "</td>"
            )
        rows.append(
            f"<tr id=\"view-{html.escape(view)}\">"
            f"<th scope=\"row\">{html.escape(view)}</th>{''.join(cells)}</tr>"
        )
    link_sections = []
    for state_id, result in zip(state_ids, results, strict=True):
        if result.get("status") == Status.PASS.value:
            section = (
                "<section class=\"artifact-links\">"
                f"<strong>{html.escape(state_id.upper())}</strong>"
                f"<a href=\"./{html.escape(state_id)}/manifest.json\">Manifest</a>"
                f"<a href=\"./{html.escape(state_id)}/asset.glb\">GLB</a>"
                f"<a href=\"./{html.escape(state_id)}/asset-update.fbx\">FBX</a>"
                "</section>"
            )
        else:
            section = (
                "<section class=\"artifact-links artifact-links-failed\">"
                f"<strong>{html.escape(state_id.upper())}</strong>"
                f"<a href=\"./{html.escape(state_id)}/compile-result.json\">"
                "Rapport d'échec</a>"
                f"<a href=\"./{html.escape(state_id)}/blender.log\">Log Blender</a>"
                "</section>"
            )
        link_sections.append(section)
    links = "".join(link_sections)
    production_label = "ELIGIBLE" if production_eligible else "NON ELIGIBLE"
    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Revue des états — {html.escape(contract_data['displayName'])}</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, system-ui, sans-serif; }}
    body {{ margin: 0; background: #111516; color: #edf3ef; }}
    header {{ position: sticky; top: 0; z-index: 3; padding: 1rem 1.25rem;
      background: rgba(17,21,22,.96); border-bottom: 1px solid #354044; }}
    h1 {{ margin: 0 0 .35rem; font-size: clamp(1.1rem, 2vw, 1.6rem); }}
    header p {{ margin: .25rem 0; color: #aebbb5; }}
    .gate {{ color: #ffca64; font-weight: 750; }}
    main {{ padding: 1rem; overflow-x: auto; }}
    table {{ width: 100%; min-width: 980px; border-collapse: separate;
      border-spacing: .65rem; table-layout: fixed; }}
    th, td {{ vertical-align: top; }}
    thead th {{ position: sticky; top: 94px; z-index: 2; padding: .8rem;
      background: #1a2123; border: 1px solid #354044; border-radius: .7rem; }}
    thead small {{ display: block; margin-top: .45rem; color: #aebbb5;
      font-weight: 450; line-height: 1.35; }}
    tbody th {{ position: sticky; left: 0; z-index: 1; width: 8rem;
      padding: .65rem; background: #151b1d; border-radius: .55rem;
      color: #9fdcc8; text-transform: uppercase; letter-spacing: .05em; }}
    td {{ padding: .4rem; background: #171d1f; border-radius: .7rem; }}
    img {{ display: block; width: 100%; height: auto; border-radius: .45rem;
      background: #0b0d0e; }}
    .status {{ float: right; padding: .18rem .45rem; border-radius: 999px;
      background: #214a3d; color: #aef4d8; font-size: .72rem; }}
    .status-fail, .status-blocked {{ background: #5a2525; color: #ffd2d2; }}
    .status-unknown, .status-partial {{ background: #594614; color: #ffe39b; }}
    .unavailable {{ min-height: 8rem; border: 1px dashed #854b4b;
      background: #25191a; color: #ffd2d2; }}
    .unavailable strong, .unavailable small {{ display: block; padding: .55rem; }}
    .unavailable small {{ color: #d6a8a8; overflow-wrap: anywhere; }}
    footer {{ display: flex; flex-wrap: wrap; gap: .8rem;
      padding: 1rem 1.25rem 2rem; color: #9aa7a1; }}
    .artifact-links {{ display: flex; align-items: center; gap: .65rem;
      padding: .65rem .8rem; background: #171d1f; border-radius: .6rem; }}
    .artifact-links-failed {{ border: 1px solid #713c3c; }}
    a {{ color: #70dec0; }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(contract_data['displayName'])} · revue comparative</h1>
    <p>Révision {contract_data['revision']} · états {", ".join(state_ids)}</p>
    <p class="gate">Canon production : {production_label}. Cette page est une preuve
      de comparaison, jamais une approbation humaine automatique.</p>
  </header>
  <main>
    <table>
      <thead><tr><th scope="col">Vue</th>{headers}</tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
  </main>
  <footer>{links}</footer>
</body>
</html>
"""


def command_compile_states(args: argparse.Namespace) -> int:
    contract = Path(args.contract).resolve()
    validation = validate_contract(contract)
    if validation["status"] != Status.PASS.value:
        return emit(validation)
    blender = find_blender()
    if not blender:
        return emit({"status": Status.BLOCKED.value, "reason": "Blender not found"})
    contract_data = json.loads(contract.read_text(encoding="utf-8"))
    state_ids = available_state_ids(contract_data)
    output = (
        Path(args.output).resolve()
        if args.output
        else contract.parent / "build" / "states"
    )
    results = [
        _run_blender_compile(contract, output / state_id, state_id, blender)
        for state_id in state_ids
    ]
    status = aggregate([result["status"] for result in results]).value
    report = {
        "schemaVersion": "1.0.0",
        "assetKey": contract_data["assetKey"],
        "revision": contract_data["revision"],
        "contractSha256": sha256_file(contract),
        "status": status,
        "defaultState": contract_data["states"]["default"],
        "stateCoverage": state_ids,
        "visualCanon": validation["visualCanon"],
        "results": results,
    }
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "states-manifest.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    review_path = output / "state-review.html"
    review_path.write_text(
        _state_review_html(
            contract_data,
            results,
            bool(validation["visualCanon"]["productionEligible"]),
        ),
        encoding="utf-8",
    )
    report["manifest"] = str(report_path)
    report["review"] = str(review_path)
    return emit(report)


def command_verify_states(args: argparse.Namespace) -> int:
    contract = Path(args.contract).resolve()
    validation = validate_contract(contract)
    if validation["status"] != Status.PASS.value:
        return emit(validation)
    blender = find_blender()
    if not blender:
        return emit({"status": Status.BLOCKED.value, "reason": "Blender not found"})
    contract_data = json.loads(contract.read_text(encoding="utf-8"))
    state_ids = available_state_ids(contract_data)
    output = (
        Path(args.output).resolve()
        if args.output
        else contract.parent / "build" / "state-determinism"
    )
    run_a = output / "run-a"
    run_b = output / "run-b"
    compile_results = {"runA": [], "runB": []}
    for state_id in state_ids:
        compile_results["runA"].append(
            _run_blender_compile(
                contract,
                run_a / state_id,
                state_id,
                blender,
            )
        )
        compile_results["runB"].append(
            _run_blender_compile(
                contract,
                run_b / state_id,
                state_id,
                blender,
            )
        )
    compile_status = aggregate(
        [
            result["status"]
            for run_results in compile_results.values()
            for result in run_results
        ]
    )
    if compile_status is not Status.PASS:
        report = {
            "schemaVersion": "1.0.0",
            "status": compile_status.value,
            "stateCoverage": state_ids,
            "compileResults": compile_results,
            "reason": "at least one deterministic state build did not pass",
        }
    else:
        report = compare_state_builds(
            run_a,
            run_b,
            state_ids,
            contract_data["renders"]["views"],
        )
        published_comparison = compare_published_state_build(
            contract.parent / "build" / "states",
            run_a,
            state_ids,
            contract_data["renders"]["views"],
        )
        report["publishedComparison"] = published_comparison
        if published_comparison["status"] != Status.PASS.value:
            report["status"] = Status.FAIL.value
        report["assetKey"] = contract_data["assetKey"]
        report["revision"] = contract_data["revision"]
        report["contractSha256"] = sha256_file(contract)
        report["visualCanon"] = validation["visualCanon"]
        report["compileResults"] = compile_results
    output.mkdir(parents=True, exist_ok=True)
    report_path = output / "determinism-report.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report["report"] = str(report_path)
    return emit(report)


def command_canon_packet(args: argparse.Namespace) -> int:
    from pipeline.canon_packet import CanonPacketError, build_canon_packet

    try:
        result = build_canon_packet(
            Path(args.contract).resolve(),
            Path(args.output).resolve() if args.output else None,
            force=args.force,
        )
    except CanonPacketError as error:
        result = {
            "status": Status.FAIL.value,
            "reason": str(error),
            "productionApproved": False,
        }
    if args.open and result.get("status") == Status.PASS.value:
        gallery = result.get("gallery")
        if isinstance(gallery, str) and Path(gallery).is_file():
            os.startfile(gallery)  # type: ignore[attr-defined]
    return emit(result)


def command_test(_: argparse.Namespace) -> int:
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"],
        check=False,
    )
    return completed.returncode


def command_publish(args: argparse.Namespace) -> int:
    from publisher.publish import publish

    return emit(
        publish(
            Path(args.contract).resolve(),
            dry_run=args.dry_run,
            confirm_publish=args.confirm_publish,
        )
    )


def command_report(args: argparse.Namespace) -> int:
    from pipeline.report import build_report

    return emit(build_report(Path(args.contract).resolve(), Path(args.output).resolve() if args.output else None))


def _workbench_manager(repo: str = "."):
    from mcp.session_manager import WorkbenchManager

    return WorkbenchManager(Path(repo).resolve())


def _session_argument(value: str, contract: str | None = None) -> Path:
    candidate = Path(value)
    if candidate.exists() or contract is None:
        return candidate.resolve()
    contract_path = Path(contract).resolve()
    return contract_path.parent / "workbench" / value / "session.json"


def command_blender_mcp_doctor(args: argparse.Namespace) -> int:
    return emit(_workbench_manager(args.repo).doctor())


def command_blender_inspect(args: argparse.Namespace) -> int:
    manager = _workbench_manager(args.repo)
    opened = manager.begin_session(
        Path(args.contract).resolve(), mode="OBSERVE", session_id=args.session_id
    )
    inspected = manager.inspect_session(opened["session"])
    inspected["session"] = opened["session"]
    inspected["captures"] = opened["captures"]
    inspected["productionApproved"] = False
    return emit(inspected)


def command_blender_workbench(args: argparse.Namespace) -> int:
    return emit(
        _workbench_manager(args.repo).begin_session(
            Path(args.contract).resolve(),
            mode=args.mode.upper(),
            session_id=args.session_id,
        )
    )


def command_blender_create_change(args: argparse.Namespace) -> int:
    draft = json.loads(Path(args.input).resolve().read_text(encoding="utf-8"))
    return emit(
        _workbench_manager(args.repo).create_change_set(
            _session_argument(args.session), draft
        )
    )


def command_blender_preview_change(args: argparse.Namespace) -> int:
    return emit(
        _workbench_manager(args.repo).preview_change(Path(args.change_set).resolve())
    )


def command_blender_apply_change(args: argparse.Namespace) -> int:
    return emit(
        _workbench_manager(args.repo).apply_change(Path(args.change_set).resolve())
    )


def command_blender_revert(args: argparse.Namespace) -> int:
    return emit(
        _workbench_manager(args.repo).revert_last_change(
            _session_argument(args.session)
        )
    )


def command_blender_reset(args: argparse.Namespace) -> int:
    return emit(
        _workbench_manager(args.repo).reset_candidate(
            _session_argument(args.session)
        )
    )


def command_blender_compare(args: argparse.Namespace) -> int:
    return emit(
        _workbench_manager(args.repo).compare_candidate(
            _session_argument(args.session)
        )
    )


def command_blender_prepare_promotion(args: argparse.Namespace) -> int:
    return emit(
        _workbench_manager(args.repo).prepare_promotion_sandbox(
            Path(args.change_set).resolve()
        )
    )


def command_blender_verify_promotion(args: argparse.Namespace) -> int:
    return emit(
        _workbench_manager(args.repo).verify_promotion(
            _session_argument(args.session, args.contract),
            Path(args.contract).resolve(),
        )
    )


def command_blender_close(args: argparse.Namespace) -> int:
    return emit(
        _workbench_manager(args.repo).close_session(
            _session_argument(args.session)
        )
    )


def command_blender_mcp_server(args: argparse.Namespace) -> int:
    from mcp.server_adapter import WorkbenchMcpServer

    return WorkbenchMcpServer(Path(args.repo).resolve()).serve()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Roblox 3D asset vertical-slice pipeline")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor")
    doctor.add_argument("--repo", default=".")
    doctor.set_defaults(handler=command_doctor)

    validate = subparsers.add_parser("validate")
    validate.add_argument("contract")
    validate.set_defaults(handler=command_validate)

    compile_parser = subparsers.add_parser("compile")
    compile_parser.add_argument("contract")
    compile_parser.add_argument("--output")
    compile_parser.add_argument("--state")
    compile_parser.set_defaults(handler=command_compile)

    compile_states = subparsers.add_parser("compile-states")
    compile_states.add_argument("contract")
    compile_states.add_argument("--output")
    compile_states.set_defaults(handler=command_compile_states)

    verify_states = subparsers.add_parser("verify-states")
    verify_states.add_argument("contract")
    verify_states.add_argument("--output")
    verify_states.set_defaults(handler=command_verify_states)

    canon_packet = subparsers.add_parser(
        "canon-packet",
        help="Render, compose and verify the 17-board visual-canon packet.",
    )
    canon_packet.add_argument("contract")
    canon_packet.add_argument("--output")
    canon_packet.add_argument("--open", action="store_true")
    canon_packet.add_argument(
        "--force",
        action="store_true",
        help="Rebuild both Blender raw-render runs even when their hash-bound cache is current.",
    )
    canon_packet.set_defaults(handler=command_canon_packet)

    publish_parser = subparsers.add_parser("publish")
    publish_parser.add_argument("contract")
    mode = publish_parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--confirm-publish", action="store_true")
    publish_parser.set_defaults(handler=command_publish)

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("contract")
    report_parser.add_argument("--output")
    report_parser.set_defaults(handler=command_report)

    tests = subparsers.add_parser("test")
    tests.set_defaults(handler=command_test)

    workbench_doctor = subparsers.add_parser("blender-mcp-doctor")
    workbench_doctor.add_argument("--repo", default=".")
    workbench_doctor.set_defaults(handler=command_blender_mcp_doctor)

    inspect_parser = subparsers.add_parser("blender-inspect")
    inspect_parser.add_argument("contract")
    inspect_parser.add_argument("--repo", default=".")
    inspect_parser.add_argument("--session-id")
    inspect_parser.set_defaults(handler=command_blender_inspect)

    workbench = subparsers.add_parser("blender-workbench")
    workbench.add_argument("contract")
    workbench.add_argument("--mode", choices=("observe", "explore"), default="explore")
    workbench.add_argument("--repo", default=".")
    workbench.add_argument("--session-id")
    workbench.set_defaults(handler=command_blender_workbench)

    create_change = subparsers.add_parser("blender-create-change")
    create_change.add_argument("session")
    create_change.add_argument("--input", required=True)
    create_change.add_argument("--repo", default=".")
    create_change.set_defaults(handler=command_blender_create_change)

    preview_change = subparsers.add_parser("blender-preview-change")
    preview_change.add_argument("change_set")
    preview_change.add_argument("--repo", default=".")
    preview_change.set_defaults(handler=command_blender_preview_change)

    apply_change = subparsers.add_parser("blender-apply-change")
    apply_change.add_argument("change_set")
    apply_change.add_argument("--repo", default=".")
    apply_change.set_defaults(handler=command_blender_apply_change)

    revert_change = subparsers.add_parser("blender-revert")
    revert_change.add_argument("session")
    revert_change.add_argument("--repo", default=".")
    revert_change.set_defaults(handler=command_blender_revert)

    reset_candidate = subparsers.add_parser("blender-reset")
    reset_candidate.add_argument("session")
    reset_candidate.add_argument("--repo", default=".")
    reset_candidate.set_defaults(handler=command_blender_reset)

    compare_candidate = subparsers.add_parser("blender-compare")
    compare_candidate.add_argument("session")
    compare_candidate.add_argument("--repo", default=".")
    compare_candidate.set_defaults(handler=command_blender_compare)

    prepare_promotion = subparsers.add_parser("blender-prepare-promotion-sandbox")
    prepare_promotion.add_argument("change_set")
    prepare_promotion.add_argument("--repo", default=".")
    prepare_promotion.set_defaults(handler=command_blender_prepare_promotion)

    verify_promotion = subparsers.add_parser("blender-verify-promotion")
    verify_promotion.add_argument("contract")
    verify_promotion.add_argument("--session", required=True)
    verify_promotion.add_argument("--repo", default=".")
    verify_promotion.set_defaults(handler=command_blender_verify_promotion)

    close_workbench = subparsers.add_parser("blender-close-workbench")
    close_workbench.add_argument("session")
    close_workbench.add_argument("--repo", default=".")
    close_workbench.set_defaults(handler=command_blender_close)

    mcp_server = subparsers.add_parser("blender-mcp-server")
    mcp_server.add_argument("--repo", default=".")
    mcp_server.set_defaults(handler=command_blender_mcp_server)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except Exception as error:
        from mcp.security_policy import WorkbenchError

        if isinstance(error, WorkbenchError):
            return emit(
                {
                    "status": Status.FAIL.value,
                    "error": str(error),
                    "productionApproved": False,
                }
            )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
