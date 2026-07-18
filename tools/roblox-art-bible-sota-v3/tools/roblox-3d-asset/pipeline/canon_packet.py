from __future__ import annotations

"""Build a deterministic, human-reviewable 17-board visual-canon packet."""

import hashlib
import html
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from PIL import Image, ImageDraw, ImageFont, ImageOps

from pipeline.contract import resolve_visual_canon_path, validate_contract
from pipeline.determinism import compare_png_render
from pipeline.doctor import find_blender
from pipeline.io_utils import read_json, sha256_file, write_json
from pipeline.review import review_binding_issues
from mcp.security_policy import sanitized_blender_environment

BOARD_IDS = (
    "orthographic",
    "perspective",
    "black_silhouette",
    "component_breakdown",
    "proportions",
    "materials",
    "semantic_zones",
    "all_states",
    "state_comparison",
    "mobile_near",
    "mobile_mid",
    "mobile_far",
    "lighting_matrix",
    "repetition_1",
    "repetition_30",
    "repetition_100",
    "required_and_forbidden_annotations",
)
RAW_VIEW_IDS = (
    "mobile_near",
    "mobile_mid",
    "mobile_far",
    "lighting_neutral_qa",
    "lighting_gameplay_default",
    "lighting_high_contrast",
    "lighting_adverse_night",
    "repetition_1",
    "repetition_30",
    "repetition_100",
)
PACKAGE_DIGEST_FIELDS = (
    "$schema",
    "schemaVersion",
    "assetKey",
    "revision",
    "assetId",
    "territoryId",
    "canonId",
    "baseCandidateSha256",
    "evidenceClass",
    "generation",
    "authority",
    "boards",
    "humanReviewStatus",
    "productionApproved",
)

WIDTH = 1920
HEIGHT = 1080
BLENDER_TIMEOUT_SECONDS = 1800
BACKGROUND = "#091014"
SURFACE = "#111c22"
SURFACE_ALT = "#17262d"
LINE = "#29414a"
TEXT = "#edf7f3"
MUTED = "#9db2ad"
MINT = "#66e0bb"
COPPER = "#d8893a"
GOLD = "#efc15a"
CRITICAL = "#e34b5f"


class CanonPacketError(RuntimeError):
    """Raised when the visual-canon evidence contract cannot be proven."""


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _package_digest(manifest: dict[str, Any]) -> str:
    payload = {field: manifest.get(field) for field in PACKAGE_DIGEST_FIELDS}
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _repo_root(contract: Path) -> Path:
    for candidate in contract.parents:
        if (
            (candidate / "scripts/r3d.ps1").is_file()
            and (candidate / "tools/roblox-3d-asset/r3d.py").is_file()
        ):
            return candidate
    raise CanonPacketError("repository root could not be discovered")


def _bounded(path: Path, root: Path, label: str) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as error:
        raise CanonPacketError(f"{label} must remain under {root}") from error
    return resolved


def _relative(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _require_file(path: Path, label: str) -> Path:
    if not path.is_file():
        raise CanonPacketError(f"{label} is missing: {path}")
    return path


def _require_json(path: Path, label: str) -> dict[str, Any]:
    _require_file(path, label)
    try:
        value = read_json(path)
    except (OSError, ValueError) as error:
        raise CanonPacketError(f"{label} is invalid: {error}") from error
    return value


def _reset_output(
    output: Path,
    evidence_root: Path,
    *,
    preserve_raw: bool,
) -> None:
    _bounded(output, evidence_root, "canon packet output")
    if output == evidence_root.resolve():
        raise CanonPacketError("canon packet output may not replace evidence root")
    output.mkdir(parents=True, exist_ok=True)
    directories = ["composition-a", "composition-b", "boards"]
    if not preserve_raw:
        directories = ["raw-a", "raw-b", *directories]
    for directory in directories:
        target = output / directory
        if target.exists():
            _bounded(target, output, directory)
            shutil.rmtree(target)
    for name in (
        "raw-render-report.json",
        "composition-determinism-report.json",
        "evidence-manifest.json",
        "human-review.json",
        "index.html",
        "canon-packet.log",
    ):
        (output / name).unlink(missing_ok=True)


def _run_raw_render(
    blender: Path,
    tool_root: Path,
    contract: Path,
    source_blend: Path,
    output: Path,
) -> dict[str, Any]:
    script = tool_root / "blender/render_canon_packet.py"
    _require_file(script, "canon packet Blender renderer")
    output.mkdir(parents=True, exist_ok=True)
    command = [
        str(blender),
        "--background",
        "--factory-startup",
        "--python",
        str(script),
        "--",
        str(contract),
        str(source_blend),
        str(output),
    ]
    environment = sanitized_blender_environment()
    log_path = output / "blender.log"
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            env=environment,
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
        log_path.write_text(stdout + stderr, encoding="utf-8", newline="\n")
        raise CanonPacketError(
            f"raw Blender render timed out after {BLENDER_TIMEOUT_SECONDS} seconds"
        ) from error
    log_path.write_text(
        (completed.stdout or "") + (completed.stderr or ""),
        encoding="utf-8",
        newline="\n",
    )
    manifest_path = output / "raw-manifest.json"
    if not manifest_path.is_file():
        raise CanonPacketError(
            f"Blender did not produce raw-manifest.json; exit={completed.returncode}"
        )
    manifest = read_json(manifest_path)
    if completed.returncode != 0 or manifest.get("status") != "PASS":
        raise CanonPacketError(
            f"raw Blender render failed; exit={completed.returncode}; "
            f"reason={manifest.get('error')}"
        )
    observed = {item.get("viewId") for item in manifest.get("renders", [])}
    if observed != set(RAW_VIEW_IDS):
        raise CanonPacketError(
            f"raw Blender view coverage drift: {sorted(observed)}"
        )
    return manifest


def _load_cached_raw(
    output: Path,
    *,
    asset_key: str,
    revision: int,
    contract_sha: str,
    canon_id: str,
    canon_sha: str,
    source_sha: str,
    build_manifest_sha: str,
    renderer_sha: str,
) -> dict[str, Any] | None:
    manifest_path = output / "raw-manifest.json"
    if not manifest_path.is_file():
        return None
    try:
        manifest = read_json(manifest_path)
    except (OSError, ValueError):
        return None
    expected = {
        "status": "PASS",
        "evidenceClass": "REAL_RENDERED",
        "assetKey": asset_key,
        "revision": revision,
        "contractSha256": contract_sha,
        "canonId": canon_id,
        "canonSha256": canon_sha,
        "sourceBlendSha256": source_sha,
        "buildManifestSha256": build_manifest_sha,
        "rendererScriptSha256": renderer_sha,
    }
    if any(manifest.get(key) != value for key, value in expected.items()):
        return None
    renders = {item.get("viewId"): item for item in manifest.get("renders", [])}
    if set(renders) != set(RAW_VIEW_IDS):
        return None
    for view_id, item in renders.items():
        path = output / str(item.get("path", ""))
        if (
            not path.is_file()
            or path.stat().st_size != item.get("bytes")
            or sha256_file(path) != item.get("sha256")
        ):
            return None
    return manifest


def _compare_raw_runs(
    first_root: Path,
    second_root: Path,
    first: dict[str, Any],
    second: dict[str, Any],
) -> dict[str, Any]:
    invariant_fields = (
        "assetKey",
        "revision",
        "contractSha256",
        "canonId",
        "canonSha256",
        "sourceBlendSha256",
        "buildManifestSha256",
        "rendererScriptSha256",
    )
    invariant_checks = {
        field: first.get(field) == second.get(field)
        for field in invariant_fields
    }
    first_views = {item["viewId"]: item for item in first["renders"]}
    second_views = {item["viewId"]: item for item in second["renders"]}
    comparisons = []
    for view_id in RAW_VIEW_IDS:
        comparison = compare_png_render(
            first_root / first_views[view_id]["path"],
            second_root / second_views[view_id]["path"],
        )
        comparison["viewId"] = view_id
        comparison["runAFileSha256"] = first_views[view_id]["sha256"]
        comparison["runBFileSha256"] = second_views[view_id]["sha256"]
        comparisons.append(comparison)
    passed = all(invariant_checks.values()) and all(
        comparison["passed"] for comparison in comparisons
    )
    return {
        "schemaVersion": "1.0.0",
        "status": "PASS" if passed else "FAIL",
        "evidenceClass": "REAL_RENDERED",
        "assetKey": first["assetKey"],
        "revision": first["revision"],
        "contractSha256": first["contractSha256"],
        "canonId": first["canonId"],
        "canonSha256": first["canonSha256"],
        "sourceBlendSha256": first["sourceBlendSha256"],
        "runAManifestSha256": sha256_file(first_root / "raw-manifest.json"),
        "runBManifestSha256": sha256_file(second_root / "raw-manifest.json"),
        "invariants": invariant_checks,
        "renders": comparisons,
        "productionApproved": False,
    }


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _text_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    maximum_width: int,
    maximum_lines: int,
) -> list[str]:
    words = str(text).replace("\n", " ").split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= maximum_width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
        if len(lines) >= maximum_lines:
            break
    if current and len(lines) < maximum_lines:
        lines.append(current)
    consumed = " ".join(lines)
    source = " ".join(words)
    if consumed != source and lines:
        while (
            draw.textlength(lines[-1] + "...", font=font) > maximum_width
            and lines[-1]
        ):
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1].rstrip() + "..."
    return lines


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.ImageFont,
    fill: str,
    width: int,
    maximum_lines: int,
    spacing: int = 8,
) -> int:
    lines = _text_lines(draw, text, font, width, maximum_lines)
    x, y = xy
    line_height = font.getbbox("Ag")[3] - font.getbbox("Ag")[1]
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height + spacing
    return y


def _canvas(
    title: str,
    subtitle: str,
    board_index: int,
    contract: dict[str, Any],
    canon_sha: str,
    contract_sha: str,
) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, WIDTH, 126), fill="#0d181d")
    draw.rectangle((0, 124, WIDTH, 126), fill=MINT)
    draw.text((54, 28), title, font=_font(44), fill=TEXT)
    draw.text((56, 82), subtitle, font=_font(21), fill=MUTED)
    badge = "CANDIDATE | HUMAN LOCK PENDING"
    badge_font = _font(20)
    badge_width = int(draw.textlength(badge, font=badge_font)) + 34
    draw.rounded_rectangle(
        (WIDTH - badge_width - 54, 34, WIDTH - 54, 78),
        radius=22,
        fill="#26371f",
        outline=GOLD,
        width=2,
    )
    draw.text(
        (WIDTH - badge_width - 37, 45),
        badge,
        font=badge_font,
        fill=GOLD,
    )
    footer = (
        f"{board_index:02d}/17 | {contract['displayName']} | r{contract['revision']} | "
        f"CANON {canon_sha[:12]} | CONTRACT {contract_sha[:12]} | "
        "productionApproved=false"
    )
    draw.rectangle((0, HEIGHT - 52, WIDTH, HEIGHT), fill="#0d181d")
    draw.text((54, HEIGHT - 37), footer, font=_font(17), fill=MUTED)
    return image, draw


def _panel(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    fill: str = SURFACE,
    outline: str = LINE,
) -> None:
    draw.rounded_rectangle(box, radius=20, fill=fill, outline=outline, width=2)


def _paste_contained(
    canvas: Image.Image,
    source_path: Path,
    box: tuple[int, int, int, int],
    *,
    background: str = "#0a0e10",
    border: bool = True,
) -> None:
    x0, y0, x1, y1 = box
    if border:
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle(
            box,
            radius=18,
            fill=background,
            outline=LINE,
            width=2,
        )
    inset = 8
    available = (x1 - x0 - inset * 2, y1 - y0 - inset * 2)
    with Image.open(source_path) as source:
        rgba = source.convert("RGBA")
        fitted = ImageOps.contain(rgba, available, Image.Resampling.LANCZOS)
    px = x0 + (x1 - x0 - fitted.width) // 2
    py = y0 + (y1 - y0 - fitted.height) // 2
    canvas.paste(fitted, (px, py), fitted)


def _caption(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    note: str | None = None,
) -> None:
    x0, y0, _x1, y1 = box
    draw.rounded_rectangle(
        (x0 + 14, y1 - (70 if note else 43), x0 + 260, y1 - 14),
        radius=12,
        fill="#0b151acc",
    )
    draw.text((x0 + 27, y1 - (60 if note else 36)), label, font=_font(21), fill=TEXT)
    if note:
        draw.text((x0 + 27, y1 - 34), note, font=_font(15), fill=MUTED)


def _image_grid(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    items: list[tuple[str, Path]],
    columns: int,
    area: tuple[int, int, int, int] = (48, 154, 1872, 1002),
) -> None:
    x0, y0, x1, y1 = area
    rows = (len(items) + columns - 1) // columns
    gap = 18
    cell_width = (x1 - x0 - gap * (columns - 1)) // columns
    cell_height = (y1 - y0 - gap * (rows - 1)) // rows
    for index, (label, path) in enumerate(items):
        column = index % columns
        row = index // columns
        box = (
            x0 + column * (cell_width + gap),
            y0 + row * (cell_height + gap),
            x0 + column * (cell_width + gap) + cell_width,
            y0 + row * (cell_height + gap) + cell_height,
        )
        _paste_contained(canvas, path, box)
        _caption(draw, box, label)


def _bullets(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    values: list[str],
    *,
    accent: str = MINT,
    maximum_items: int = 6,
) -> None:
    _panel(draw, box)
    x0, y0, x1, _y1 = box
    draw.text((x0 + 24, y0 + 22), title, font=_font(26), fill=accent)
    y = y0 + 66
    font = _font(19)
    for value in values[:maximum_items]:
        draw.ellipse((x0 + 25, y + 8, x0 + 33, y + 16), fill=accent)
        y = _draw_wrapped(
            draw,
            (x0 + 48, y),
            value,
            font,
            TEXT,
            x1 - x0 - 76,
            3,
            4,
        ) + 9


def _state_paths(asset_root: Path, state_id: str) -> dict[str, Path]:
    root = asset_root / "build/states" / state_id / "renders"
    return {
        view: _require_file(root / f"{view}.png", f"{state_id}/{view} render")
        for view in (
            "front",
            "rear",
            "left",
            "right",
            "top",
            "perspective",
            "mobile_distance",
            "silhouette",
        )
    }


def _hex_color(value: str) -> tuple[int, int, int]:
    clean = value.lstrip("#")
    return tuple(int(clean[index : index + 2], 16) for index in (0, 2, 4))


def _build_boards(
    output: Path,
    contract: dict[str, Any],
    canon: dict[str, Any],
    contract_sha: str,
    canon_sha: str,
    asset_root: Path,
    raw_root: Path,
) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    states = {
        state_id: _state_paths(asset_root, state_id)
        for state_id in ("intact", "damaged", "critical")
    }
    raw = {
        view_id: _require_file(raw_root / f"{view_id}.png", view_id)
        for view_id in RAW_VIEW_IDS
    }
    part_count = len(contract["geometry"]["parts"])
    paths: dict[str, Path] = {}

    def save(
        board_id: str,
        title: str,
        subtitle: str,
        renderer: Callable[[Image.Image, ImageDraw.ImageDraw], None],
    ) -> None:
        index = BOARD_IDS.index(board_id) + 1
        canvas, draw = _canvas(
            title,
            subtitle,
            index,
            contract,
            canon_sha,
            contract_sha,
        )
        renderer(canvas, draw)
        path = output / f"{index:02d}-{board_id}.png"
        canvas.save(path, format="PNG", compress_level=9, optimize=False)
        paths[board_id] = path

    save(
        "orthographic",
        "Orthographic board",
        "Volumes, orientation and footprint without perspective distortion.",
        lambda canvas, draw: _image_grid(
            canvas,
            draw,
            [
                ("ENEMY FACE", states["intact"]["front"]),
                ("SAFE REAR", states["intact"]["rear"]),
                ("LEFT", states["intact"]["left"]),
                ("RIGHT", states["intact"]["right"]),
                ("TOP", states["intact"]["top"]),
            ],
            3,
        ),
    )

    def perspective_board(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
        main = (48, 154, 1320, 1002)
        _paste_contained(canvas, states["intact"]["perspective"], main)
        _caption(draw, main, "CANONICAL THREE-QUARTER", "INTACT STATE")
        _bullets(
            draw,
            (1340, 154, 1872, 566),
            "One-second read",
            [
                canon["instantRead"]["oneSecondPromise"],
                canon["instantRead"]["orientationCue"],
                canon["instantRead"]["interactionCue"],
            ],
            maximum_items=3,
        )
        _bullets(
            draw,
            (1340, 584, 1872, 1002),
            "Recognition landmarks",
            canon["silhouette"]["recognitionLandmarks"],
            accent=COPPER,
            maximum_items=4,
        )

    save(
        "perspective",
        "Canonical perspective",
        "Salvaged Frontier identity, function and orientation in one read.",
        perspective_board,
    )

    save(
        "black_silhouette",
        "Black silhouettes by state",
        "Damage progression must remain readable without material or color.",
        lambda canvas, draw: _image_grid(
            canvas,
            draw,
            [
                ("INTACT", states["intact"]["silhouette"]),
                ("DAMAGED", states["damaged"]["silhouette"]),
                ("CRITICAL", states["critical"]["silhouette"]),
            ],
            3,
        ),
    )

    def components_board(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
        image_box = (48, 154, 1015, 1002)
        _paste_contained(canvas, states["intact"]["perspective"], image_box)
        _caption(draw, image_box, "REAL ASSEMBLY", f"{part_count} STABLE PARTS")
        components = canon["construction"]["components"]
        positions = [
            (1035, 154, 1444, 566),
            (1463, 154, 1872, 566),
            (1035, 584, 1444, 1002),
            (1463, 584, 1872, 1002),
        ]
        for component, box, number in zip(components, positions, range(1, 5), strict=True):
            _panel(draw, box)
            x0, y0, x1, _y1 = box
            draw.ellipse((x0 + 22, y0 + 22, x0 + 66, y0 + 66), fill=COPPER)
            draw.text((x0 + 36, y0 + 31), str(number), font=_font(20), fill="#091014")
            draw.text(
                (x0 + 80, y0 + 25),
                component["id"],
                font=_font(24),
                fill=TEXT,
            )
            y = _draw_wrapped(
                draw,
                (x0 + 24, y0 + 88),
                component["function"],
                _font(18),
                MUTED,
                x1 - x0 - 48,
                4,
                5,
            )
            _draw_wrapped(
                draw,
                (x0 + 24, y + 12),
                component["readingRole"],
                _font(17),
                MINT,
                x1 - x0 - 48,
                4,
                5,
            )

    save(
        "component_breakdown",
        "Functional component breakdown",
        "Every visible mass belongs to a named, causal component.",
        components_board,
    )

    def proportions_board(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
        image_box = (48, 154, 1280, 1002)
        _paste_contained(canvas, states["intact"]["front"], image_box)
        _caption(draw, image_box, "FRONT | ROBLOX SCALE")
        x0, y0, x1, y1 = image_box
        draw.line((x0 + 80, y1 - 64, x1 - 80, y1 - 64), fill=MINT, width=4)
        draw.line((x0 + 80, y1 - 80, x0 + 80, y1 - 48), fill=MINT, width=4)
        draw.line((x1 - 80, y1 - 80, x1 - 80, y1 - 48), fill=MINT, width=4)
        draw.text(
            ((x0 + x1) // 2 - 90, y1 - 105),
            f"{contract['dimensionsStuds']['width']:.1f} studs",
            font=_font(24),
            fill=MINT,
        )
        pivot = contract["pivot"]
        pivot_label = pivot.get("mode") if isinstance(pivot, dict) else str(pivot)
        _bullets(
            draw,
            (1300, 154, 1872, 494),
            "Locked dimensions",
            [
                f"Width: {contract['dimensionsStuds']['width']:.1f} studs",
                f"Height: {contract['dimensionsStuds']['height']:.1f} studs",
                f"Depth: {contract['dimensionsStuds']['depth']:.1f} studs",
                f"Pivot : {pivot_label}",
            ],
            maximum_items=4,
        )
        _bullets(
            draw,
            (1300, 512, 1872, 1002),
            "Proportion rules",
            canon["dimensions"]["proportionRules"],
            accent=GOLD,
            maximum_items=5,
        )

    save(
        "proportions",
        "Proportions and dimensions",
        "Exact gameplay scale, tolerances and mass relationships.",
        proportions_board,
    )

    def materials_board(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
        image_box = (48, 154, 1120, 1002)
        _paste_contained(canvas, states["intact"]["perspective"], image_box)
        _caption(draw, image_box, "APPLIED MATERIALS")
        x0 = 1140
        draw.text((x0, 168), "Production palette", font=_font(28), fill=TEXT)
        y = 220
        for material in contract["materials"][:6]:
            color = _hex_color(material["color"])
            draw.rounded_rectangle((x0, y, x0 + 84, y + 64), radius=12, fill=color)
            draw.text((x0 + 106, y + 4), material["name"], font=_font(21), fill=TEXT)
            draw.text(
                (x0 + 106, y + 35),
                f"R {material['roughness']:.2f} | M {material['metallic']:.2f}",
                font=_font(16),
                fill=MUTED,
            )
            y += 88
        _draw_wrapped(
            draw,
            (x0, y + 8),
            canon["artDirection"]["materialLanguage"],
            _font(18),
            MINT,
            700,
            5,
            6,
        )
        _draw_wrapped(
            draw,
            (x0, y + 132),
            canon["artDirection"]["wearLogic"],
            _font(18),
            COPPER,
            700,
            5,
            6,
        )

    save(
        "materials",
        "Materials and value hierarchy",
        "Calm broad surfaces, causal boundaries and bounded semantic accents.",
        materials_board,
    )

    def zones_board(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
        front_box = (48, 154, 930, 568)
        rear_box = (48, 588, 930, 1002)
        _paste_contained(canvas, states["intact"]["front"], front_box)
        _caption(draw, front_box, "ENEMY FACE")
        _paste_contained(canvas, states["intact"]["rear"], rear_box)
        _caption(draw, rear_box, "SAFE REAR")
        colors = [MINT, "#b6c7c2", COPPER, CRITICAL]
        boxes = [
            (950, 154, 1400, 568),
            (1420, 154, 1872, 568),
            (950, 588, 1400, 1002),
            (1420, 588, 1872, 1002),
        ]
        for zone, color, box in zip(
            canon["semanticZones"],
            colors,
            boxes,
            strict=True,
        ):
            _panel(draw, box)
            x0, y0, x1, _y1 = box
            draw.rectangle((x0, y0, x0 + 10, box[3]), fill=color)
            draw.text((x0 + 30, y0 + 24), zone["id"], font=_font(24), fill=color)
            y = _draw_wrapped(
                draw,
                (x0 + 30, y0 + 72),
                zone["purpose"],
                _font(18),
                TEXT,
                x1 - x0 - 58,
                5,
                5,
            )
            _draw_wrapped(
                draw,
                (x0 + 30, y + 10),
                zone["shapeRule"],
                _font(17),
                MUTED,
                x1 - x0 - 58,
                4,
                5,
            )

    save(
        "semantic_zones",
        "Semantic zones",
        "Structure, blocking, interaction and vulnerability never compete.",
        zones_board,
    )

    save(
        "all_states",
        "All canonical states",
        "Three distinct outputs, one structure, one identity and stable anchors.",
        lambda canvas, draw: _image_grid(
            canvas,
            draw,
            [
                ("INTACT | READY", states["intact"]["perspective"]),
                ("DAMAGED | WARNING", states["damaged"]["perspective"]),
                ("CRITICAL | IMMINENT FAILURE", states["critical"]["perspective"]),
            ],
            3,
        ),
    )

    def state_comparison(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
        _image_grid(
            canvas,
            draw,
            [
                ("INTACT | FRONT", states["intact"]["front"]),
                ("DAMAGED | FRONT", states["damaged"]["front"]),
                ("CRITICAL | FRONT", states["critical"]["front"]),
                ("INTACT | SILHOUETTE", states["intact"]["silhouette"]),
                ("DAMAGED | SILHOUETTE", states["damaged"]["silhouette"]),
                ("CRITICAL | SILHOUETTE", states["critical"]["silhouette"]),
            ],
            3,
        )

    save(
        "state_comparison",
        "Causal state comparison",
        "Shape, silhouette, value and breakage confirm state without color-only cues.",
        state_comparison,
    )

    def mobile_board(
        board_id: str,
        label: str,
        scale: str,
        note: str,
    ) -> None:
        def renderer(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
            image_box = (48, 154, 1872, 928)
            _paste_contained(canvas, raw[board_id], image_box)
            _caption(draw, image_box, label, scale)
            draw.rounded_rectangle(
                (48, 946, 1872, 1002),
                radius=14,
                fill=SURFACE_ALT,
                outline=LINE,
                width=2,
            )
            draw.text((72, 961), note, font=_font(19), fill=MUTED)

        save(
            board_id,
            f"Mobile read | {label.lower()}",
            "Canonical 16:9 framing; perceptual evidence, not physical-device measurement.",
            renderer,
        )

    mobile_board(
        "mobile_near",
        "NEAR",
        "Ortho 8.5",
        "Construction, feet and material hierarchy must remain immediately readable.",
    )
    mobile_board(
        "mobile_mid",
        "MID",
        "Ortho 14.0",
        "Blocking function, three-bay rhythm and orientation must read in one second.",
    )
    mobile_board(
        "mobile_far",
        "FAR",
        "Ortho 22.0",
        "Dark frame, light panels and feet must preserve an unambiguous silhouette.",
    )

    save(
        "lighting_matrix",
        "Lighting matrix",
        "Same camera, four real profiles: QA, gameplay, contrast and adverse night.",
        lambda canvas, draw: _image_grid(
            canvas,
            draw,
            [
                ("NEUTRAL QA", raw["lighting_neutral_qa"]),
                ("GAMEPLAY DEFAULT", raw["lighting_gameplay_default"]),
                ("HIGH CONTRAST", raw["lighting_high_contrast"]),
                ("ADVERSE NIGHT", raw["lighting_adverse_night"]),
            ],
            2,
        ),
    )

    def repetition_board(board_id: str, count: int) -> None:
        def renderer(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
            image_box = (48, 154, 1495, 1002)
            _paste_contained(canvas, raw[board_id], image_box)
            _caption(draw, image_box, f"{count} INSTANCE{'S' if count > 1 else ''}")
            _bullets(
                draw,
                (1515, 154, 1872, 1002),
                "Reuse evidence",
                [
                    f"{count} rendered models",
                    f"{part_count * count} scene objects",
                    f"{part_count} unique mesh data blocks",
                    "Linked mesh data",
                    "Same palette and identity",
                    "Separate Roblox benchmark required",
                ],
                accent=MINT,
                maximum_items=6,
            )

        save(
            board_id,
            f"Repetition x{count}",
            "Real visual density with reuse of the same geometry data.",
            renderer,
        )

    repetition_board("repetition_1", 1)
    repetition_board("repetition_30", 30)
    repetition_board("repetition_100", 100)

    def annotations_board(canvas: Image.Image, draw: ImageDraw.ImageDraw) -> None:
        image_box = (48, 154, 930, 1002)
        _paste_contained(canvas, states["intact"]["perspective"], image_box)
        _caption(draw, image_box, "REFERENCE TO REVIEW")
        _bullets(
            draw,
            (950, 154, 1400, 1002),
            "Required",
            canon["invariants"]
            + canon["silhouette"]["recognitionLandmarks"],
            accent=MINT,
            maximum_items=8,
        )
        _bullets(
            draw,
            (1420, 154, 1872, 1002),
            "Forbidden",
            canon["forbidden"],
            accent=CRITICAL,
            maximum_items=9,
        )

    save(
        "required_and_forbidden_annotations",
        "Required and forbidden",
        "Everything not explicitly variable remains stable.",
        annotations_board,
    )

    if set(paths) != set(BOARD_IDS):
        raise CanonPacketError("board compositor did not produce exact coverage")
    return paths


def _compare_compositions(
    first: dict[str, Path],
    second: dict[str, Path],
) -> dict[str, Any]:
    comparisons = []
    for board_id in BOARD_IDS:
        first_sha = sha256_file(first[board_id])
        second_sha = sha256_file(second[board_id])
        comparisons.append(
            {
                "boardId": board_id,
                "runASha256": first_sha,
                "runBSha256": second_sha,
                "exact": first_sha == second_sha,
            }
        )
    passed = all(item["exact"] for item in comparisons)
    return {
        "schemaVersion": "1.0.0",
        "status": "PASS" if passed else "FAIL",
        "boardCount": len(comparisons),
        "comparisons": comparisons,
        "productionApproved": False,
    }


def _binding(
    role: str,
    root_name: str,
    path: Path,
    root: Path,
) -> dict[str, Any]:
    _require_file(path, role)
    return {
        "role": role,
        "root": root_name,
        "path": _relative(path, root),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
    }


def _write_gallery(
    output: Path,
    contract: dict[str, Any],
    canon: dict[str, Any],
    package_sha: str,
    board_paths: dict[str, Path],
    review_template: dict[str, Any],
) -> None:
    cards = []
    for index, board_id in enumerate(BOARD_IDS, start=1):
        path = board_paths[board_id]
        cards.append(
            f"<article class=\"card\" data-board=\"{html.escape(board_id)}\">"
            f"<a href=\"boards/{html.escape(path.name)}\" target=\"_blank\">"
            f"<img src=\"boards/{html.escape(path.name)}\" "
            f"alt=\"{html.escape(board_id)}\"></a>"
            "<div class=\"card-head\">"
            f"<strong>{index:02d}. {html.escape(board_id)}</strong>"
            f"<span class=\"badge\" id=\"badge-{html.escape(board_id)}\">PENDING</span>"
            "</div>"
            "<div class=\"card-review\">"
            f"<div class=\"choice\" data-choice-board=\"{html.escape(board_id)}\">"
            "<button type=\"button\" data-value=\"PASS\">Conforme</button>"
            "<button type=\"button\" data-value=\"FAIL\">À corriger</button>"
            "</div>"
            f"<textarea data-comment-board=\"{html.escape(board_id)}\" "
            "maxlength=\"2000\" placeholder=\"Commentaire précis si nécessaire\"></textarea>"
            "</div>"
            "</article>"
        )
    check_labels = {
        "oneSecondFunctionRead": "Fonction comprise en une seconde",
        "stateReadWithoutColorOnly": "États lisibles sans dépendre de la couleur",
        "mobileNearMidFar": "Lecture mobile proche, moyenne et lointaine",
        "lightingRobustness": "Robustesse sous les quatre éclairages",
        "repetitionOneThirtyHundred": "Densité maîtrisée à 1, 30 et 100 exemplaires",
        "requiredAndForbiddenCompliance": "Exigences et interdictions respectées",
        "artDirectionQuality": "Qualité Salvaged Frontier au niveau production",
    }
    checks = []
    for check_id in review_template["mandatoryChecks"]:
        checks.append(
            f"<div class=\"check-row\" data-check=\"{html.escape(check_id)}\">"
            f"<span>{html.escape(check_labels[check_id])}</span>"
            f"<div class=\"choice\" data-choice-check=\"{html.escape(check_id)}\">"
            "<button type=\"button\" data-value=\"PASS\">PASS</button>"
            "<button type=\"button\" data-value=\"FAIL\">FAIL</button>"
            "</div></div>"
        )
    review_json = json.dumps(review_template, ensure_ascii=False).replace(
        "</", "<\\/"
    )
    page = """<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Canon visuel — __DISPLAY_NAME__</title>
  <style>
    :root { color-scheme: dark; font: 16px/1.45 Inter,Segoe UI,sans-serif;
      --bg:#091014;--surface:#111c22;--line:#29414a;--text:#edf7f3;
      --muted:#9db2ad;--mint:#66e0bb;--gold:#efc15a;--red:#ff6478; }
    * { box-sizing:border-box }
    body { margin:0;background:var(--bg);color:var(--text) }
    header { position:sticky;top:0;z-index:3;padding:18px 30px;background:#0d181df2;
      border-bottom:2px solid var(--mint);backdrop-filter:blur(12px) }
    h1 { margin:0 0 4px;font-size:clamp(22px,3vw,36px) }
    h2 { margin:0 0 8px;font-size:clamp(22px,3vw,32px) }
    p { margin:4px 0;color:var(--muted) }
    .gate { color:var(--gold);font-weight:750 }
    .actions { display:flex;gap:10px;flex-wrap:wrap;margin-top:12px;align-items:center }
    a.button,.primary { color:#07110e;background:var(--mint);padding:9px 13px;
      border:0;border-radius:9px;text-decoration:none;font-weight:750;cursor:pointer }
    a.secondary { color:var(--text);background:#20323a }
    .progress { margin-left:auto;color:var(--mint);font-weight:750 }
    main { display:grid;grid-template-columns:repeat(auto-fit,minmax(360px,1fr));
      gap:18px;padding:24px }
    .card { border:1px solid var(--line);border-radius:15px;overflow:hidden;background:var(--surface) }
    .card.pass { border-color:var(--mint) }
    .card.fail { border-color:var(--red) }
    .card img { display:block;width:100%;aspect-ratio:16/9;object-fit:cover;background:#05090b }
    .card-head { display:flex;justify-content:space-between;gap:12px;padding:13px 15px 8px }
    .badge { color:var(--gold);font-size:12px;text-transform:uppercase;letter-spacing:.05em }
    .card.pass .badge { color:var(--mint) }
    .card.fail .badge { color:var(--red) }
    .card-review { padding:4px 15px 15px }
    .choice { display:flex;gap:8px;flex-wrap:wrap }
    .choice button { padding:7px 10px;border:1px solid var(--line);border-radius:8px;
      color:var(--text);background:#0c151a;cursor:pointer }
    .choice button.selected-pass { border-color:var(--mint);background:#14352d;color:var(--mint) }
    .choice button.selected-fail { border-color:var(--red);background:#371921;color:#ff9baa }
    textarea,input,select { width:100%;margin-top:9px;padding:10px 11px;border:1px solid var(--line);
      border-radius:9px;color:var(--text);background:#091216;font:inherit }
    textarea { min-height:72px;resize:vertical }
    .review { margin:10px 24px 32px;padding:24px;border:1px solid var(--line);
      border-radius:16px;background:var(--surface);scroll-margin-top:190px }
    .review-grid { display:grid;grid-template-columns:minmax(320px,1fr) minmax(320px,1fr);
      gap:22px;margin-top:18px }
    .check-row { display:flex;justify-content:space-between;align-items:center;
      gap:15px;padding:12px 0;border-bottom:1px solid var(--line) }
    label { display:block;margin:12px 0 4px;color:var(--muted) }
    .hint { min-height:24px;margin:12px 0;color:var(--gold) }
    .primary:disabled { opacity:.45;cursor:not-allowed }
    .danger { border:1px solid var(--red);color:#ff9baa;background:transparent;
      padding:8px 12px;border-radius:9px;cursor:pointer }
    code { color:var(--mint);word-break:break-all }
    @media (max-width:820px) {
      header { position:static;padding:16px }
      main { grid-template-columns:1fr;padding:14px }
      .review { margin:8px 14px 24px;padding:17px }
      .review-grid { grid-template-columns:1fr }
      .progress { width:100%;margin-left:0 }
    }
  </style>
</head>
<body>
  <header>
    <h1>__DISPLAY_NAME__ · paquet canonique r__REVISION__</h1>
    <p>__THESIS__</p>
    <p class="gate">CANDIDATE · revue humaine obligatoire · productionApproved=false</p>
    <p>Digest : <code>__PACKAGE_SHA__</code></p>
    <div class="actions">
      <a class="button" href="#review">Commencer la revue</a>
      <a class="button" href="evidence-manifest.json">Manifest de preuve</a>
      <a class="button secondary" href="human-review.json">Gabarit JSON</a>
      <a class="button" href="raw-render-report.json">Déterminisme Blender</a>
      <span class="progress" id="progress">0/17 planches · 0/7 gates</span>
    </div>
  </header>
  <main>__CARDS__</main>
  <section class="review" id="review">
    <h2>Décision humaine liée au digest</h2>
    <p>Examine chaque planche en taille réelle, statue sur les sept gates, puis
      télécharge le fichier de revue. Aucun choix n’est prérempli.</p>
    <div class="review-grid">
      <div>
        <h3>Gates obligatoires</h3>
        __CHECKS__
      </div>
      <div>
        <h3>Autorité et décision</h3>
        <label for="reviewer">Nom de l’autorité humaine</label>
        <input id="reviewer" maxlength="200" autocomplete="name"
          placeholder="Ex. Nelson — Founder / Art Director">
        <label for="decision">Décision</label>
        <select id="decision">
          <option value="">Choisir après la revue</option>
          <option value="LOCK">LOCK — verrouiller ce canon</option>
          <option value="REVISION_REQUIRED">REVISION_REQUIRED — corriger</option>
          <option value="REJECT">REJECT — rejeter cette proposition</option>
        </select>
        <label for="decisionRecord">Justification vérifiable</label>
        <textarea id="decisionRecord" maxlength="4000"
          placeholder="Pourquoi cette décision est-elle correcte au regard du GDD, de la DA, des états, du mobile et des interdictions ?"></textarea>
        <p class="hint" id="hint">Les 17 planches et les 7 gates doivent être examinés.</p>
        <div class="actions">
          <button class="primary" id="download" type="button" disabled>
            Télécharger human-review-completed.json
          </button>
          <button class="danger" id="reset" type="button">Réinitialiser la revue locale</button>
        </div>
      </div>
    </div>
  </section>
  <script>
    const TEMPLATE = __REVIEW_JSON__;
    const storageKey = `visual-canon-review:${TEMPLATE.evidencePackageSha256}`;
    let state = structuredClone(TEMPLATE);
    try {
      const saved = JSON.parse(localStorage.getItem(storageKey) || "null");
      if (saved && saved.evidencePackageSha256 === TEMPLATE.evidencePackageSha256) {
        state = saved;
      }
    } catch (_) {}

    const boardIds = Object.keys(TEMPLATE.boards);
    const checkIds = Object.keys(TEMPLATE.mandatoryChecks);
    const byId = id => document.getElementById(id);
    const choiceButtons = (selector, value) =>
      [...document.querySelectorAll(`${selector} button`)].forEach(button => {
        button.classList.toggle("selected-pass", button.dataset.value === value && value === "PASS");
        button.classList.toggle("selected-fail", button.dataset.value === value && value === "FAIL");
      });

    function persist() {
      state.reviewer = byId("reviewer").value.trim() || null;
      state.decision = byId("decision").value || null;
      state.decisionRecord = byId("decisionRecord").value.trim() || null;
      localStorage.setItem(storageKey, JSON.stringify(state));
    }

    function render() {
      boardIds.forEach(id => {
        const status = state.boards[id].status;
        const card = document.querySelector(`[data-board="${id}"]`);
        card.classList.toggle("pass", status === "PASS");
        card.classList.toggle("fail", status === "FAIL");
        byId(`badge-${id}`).textContent = status;
        choiceButtons(`[data-choice-board="${id}"]`, status);
        document.querySelector(`[data-comment-board="${id}"]`).value =
          state.boards[id].comment || "";
      });
      checkIds.forEach(id => {
        choiceButtons(`[data-choice-check="${id}"]`, state.mandatoryChecks[id]);
      });
      byId("reviewer").value = state.reviewer || "";
      byId("decision").value = state.decision || "";
      byId("decisionRecord").value = state.decisionRecord || "";

      const boardValues = boardIds.map(id => state.boards[id].status);
      const checkValues = checkIds.map(id => state.mandatoryChecks[id]);
      const boardsDone = boardValues.filter(value => value !== "PENDING").length;
      const checksDone = checkValues.filter(value => value !== "PENDING").length;
      byId("progress").textContent = `${boardsDone}/17 planches · ${checksDone}/7 gates`;

      const allDone = boardsDone === boardIds.length && checksDone === checkIds.length;
      const failed = boardValues.includes("FAIL") || checkValues.includes("FAIL");
      const identityReady = (state.reviewer || "").length >= 2;
      const recordReady = (state.decisionRecord || "").length >= 3;
      const decision = state.decision;
      const coherentDecision =
        (decision === "LOCK" && !failed) ||
        ((decision === "REVISION_REQUIRED" || decision === "REJECT") && failed);
      const ready = allDone && identityReady && recordReady && coherentDecision;
      byId("download").disabled = !ready;
      if (!allDone) {
        byId("hint").textContent = "Les 17 planches et les 7 gates doivent être examinés.";
      } else if (!identityReady || !recordReady || !decision) {
        byId("hint").textContent = "Renseigne l’autorité, la décision et sa justification.";
      } else if (!coherentDecision) {
        byId("hint").textContent = failed
          ? "LOCK est interdit tant qu’un élément est en échec."
          : "Une révision ou un rejet exige au moins un échec explicite.";
      } else {
        byId("hint").textContent = "Revue cohérente et prête à être téléchargée.";
      }
    }

    document.querySelectorAll("[data-choice-board]").forEach(group => {
      group.querySelectorAll("button").forEach(button => {
        button.onclick = () => {
          state.boards[group.dataset.choiceBoard].status = button.dataset.value;
          persist();
          render();
        };
      });
    });
    document.querySelectorAll("[data-comment-board]").forEach(field => {
      field.oninput = () => {
        state.boards[field.dataset.commentBoard].comment = field.value.trim() || null;
        persist();
      };
    });
    document.querySelectorAll("[data-choice-check]").forEach(group => {
      group.querySelectorAll("button").forEach(button => {
        button.onclick = () => {
          state.mandatoryChecks[group.dataset.choiceCheck] = button.dataset.value;
          persist();
          render();
        };
      });
    });
    ["reviewer", "decision", "decisionRecord"].forEach(id => {
      byId(id).oninput = () => { persist(); render(); };
      byId(id).onchange = () => { persist(); render(); };
    });
    byId("download").onclick = () => {
      persist();
      const completed = structuredClone(state);
      completed.reviewedAt = new Date().toISOString();
      completed.status = {
        LOCK: "APPROVED",
        REVISION_REQUIRED: "REVISION_REQUIRED",
        REJECT: "REJECTED"
      }[completed.decision];
      const blob = new Blob([JSON.stringify(completed, null, 2) + "\\n"],
        {type:"application/json"});
      const anchor = document.createElement("a");
      anchor.href = URL.createObjectURL(blob);
      anchor.download = "human-review-completed.json";
      anchor.click();
      setTimeout(() => URL.revokeObjectURL(anchor.href), 1000);
      byId("hint").textContent = "Revue téléchargée. Valide-la avec lock-canon en dry-run.";
    };
    byId("reset").onclick = () => {
      if (!confirm("Effacer uniquement la progression locale de cette revue ?")) return;
      localStorage.removeItem(storageKey);
      state = structuredClone(TEMPLATE);
      render();
    };
    render();
  </script>
</body>
</html>
"""
    page = (
        page.replace("__DISPLAY_NAME__", html.escape(contract["displayName"]))
        .replace("__REVISION__", str(contract["revision"]))
        .replace(
            "__THESIS__",
            html.escape(canon["identity"]["territoryVisualThesis"]),
        )
        .replace("__PACKAGE_SHA__", package_sha)
        .replace("__CARDS__", "".join(cards))
        .replace("__CHECKS__", "".join(checks))
        .replace("__REVIEW_JSON__", review_json)
    )
    (output / "index.html").write_text(page, encoding="utf-8", newline="\n")


def build_canon_packet(
    contract_path: Path,
    output_path: Path | None = None,
    *,
    force: bool = False,
) -> dict[str, Any]:
    contract_path = contract_path.resolve()
    validation = validate_contract(contract_path)
    if validation["status"] != "PASS":
        return {
            "status": "FAIL",
            "reason": "asset contract validation failed",
            "validation": validation,
            "productionApproved": False,
        }
    blender = find_blender()
    if blender is None:
        return {
            "status": "BLOCKED",
            "reason": "Blender was not found",
            "productionApproved": False,
        }

    repo = _repo_root(contract_path)
    tool_root = repo / "tools/roblox-3d-asset"
    package_root = _require_file(
        repo / "tools/roblox-art-bible-sota-v3/STATUS.json",
        "art-direction package",
    ).parent
    evidence_root = package_root / "evidence/canonical-visuals"
    contract = read_json(contract_path)
    canon_path = resolve_visual_canon_path(
        contract_path,
        contract["visualCanon"]["path"],
    )
    canon = _require_json(canon_path, "visual canon")
    contract_sha = sha256_file(contract_path)
    canon_sha = sha256_file(canon_path)
    required_boards = [
        board["id"] for board in canon["visualPacket"]["boards"]
    ]
    if required_boards != list(BOARD_IDS):
        return {
            "status": "FAIL",
            "reason": "visual canon board order or coverage drift",
            "expected": list(BOARD_IDS),
            "observed": required_boards,
            "productionApproved": False,
        }

    asset_root = contract_path.parent
    main_manifest_path = asset_root / "build/manifest.json"
    states_manifest_path = asset_root / "build/states/states-manifest.json"
    determinism_path = asset_root / "build/state-determinism/determinism-report.json"
    review_path = asset_root / "review.json"
    main = _require_json(main_manifest_path, "main build manifest")
    states = _require_json(states_manifest_path, "states manifest")
    determinism = _require_json(determinism_path, "state determinism report")
    review = _require_json(review_path, "visual review")
    failures = []
    if main.get("status") != "PASS":
        failures.append("main build manifest is not PASS")
    if states.get("status") != "PASS":
        failures.append("states manifest is not PASS")
    if determinism.get("status") != "PASS":
        failures.append("state determinism report is not PASS")
    if review.get("automationReviewStatus") != "PASS":
        failures.append("automated visual review is not PASS")
    failures.extend(
        f"visual review authority: {issue}"
        for issue in review_binding_issues(
            review,
            asset_root=asset_root,
            contract=contract,
            contract_sha256=contract_sha,
        )
    )
    if states.get("contractSha256") != contract_sha:
        failures.append("states manifest contract hash drift")
    if determinism.get("contractSha256") != contract_sha:
        failures.append("determinism report contract hash drift")
    if main.get("visualCanon", {}).get("sha256") != canon_sha:
        failures.append("main build visual canon hash drift")
    if failures:
        return {
            "status": "FAIL",
            "reason": "precanonical packet authority is stale",
            "errors": failures,
            "productionApproved": False,
        }

    default_output = (
        evidence_root
        / contract["visualCanon"]["territoryId"]
        / f"{contract['assetKey']}-r{contract['revision']}"
    )
    output = _bounded(
        output_path.resolve() if output_path else default_output.resolve(),
        evidence_root,
        "canon packet output",
    )
    raw_a = output / "raw-a"
    raw_b = output / "raw-b"
    source_blend = asset_root / "build/source.blend"
    renderer_path = tool_root / "blender/render_canon_packet.py"
    cache_arguments = {
        "asset_key": contract["assetKey"],
        "revision": contract["revision"],
        "contract_sha": contract_sha,
        "canon_id": canon["canonId"],
        "canon_sha": canon_sha,
        "source_sha": sha256_file(source_blend),
        "build_manifest_sha": sha256_file(main_manifest_path),
        "renderer_sha": sha256_file(renderer_path),
    }
    run_a = None if force else _load_cached_raw(raw_a, **cache_arguments)
    run_b = None if force else _load_cached_raw(raw_b, **cache_arguments)
    reused_raw = run_a is not None and run_b is not None
    _reset_output(output, evidence_root, preserve_raw=reused_raw)
    if not reused_raw:
        run_a = _run_raw_render(
            blender,
            tool_root,
            contract_path,
            source_blend,
            raw_a,
        )
        run_b = _run_raw_render(
            blender,
            tool_root,
            contract_path,
            source_blend,
            raw_b,
        )
    assert run_a is not None and run_b is not None
    raw_report = _compare_raw_runs(raw_a, raw_b, run_a, run_b)
    write_json(output / "raw-render-report.json", raw_report)
    if raw_report["status"] != "PASS":
        return {
            "status": "FAIL",
            "reason": "raw Blender packet rendering is not deterministic",
            "report": str(output / "raw-render-report.json"),
            "productionApproved": False,
        }

    composition_a = _build_boards(
        output / "composition-a",
        contract,
        canon,
        contract_sha,
        canon_sha,
        asset_root,
        raw_a,
    )
    composition_b = _build_boards(
        output / "composition-b",
        contract,
        canon,
        contract_sha,
        canon_sha,
        asset_root,
        raw_a,
    )
    composition_report = _compare_compositions(composition_a, composition_b)
    write_json(output / "composition-determinism-report.json", composition_report)
    if composition_report["status"] != "PASS":
        return {
            "status": "FAIL",
            "reason": "board composition is not deterministic",
            "report": str(output / "composition-determinism-report.json"),
            "productionApproved": False,
        }

    boards_root = output / "boards"
    boards_root.mkdir()
    board_paths: dict[str, Path] = {}
    for board_id in BOARD_IDS:
        destination = boards_root / composition_a[board_id].name
        shutil.copyfile(composition_a[board_id], destination)
        board_paths[board_id] = destination

    raw_report_path = output / "raw-render-report.json"
    authority = {
        "bindings": [
            _binding("contract", "PROJECT_ROOT", contract_path, repo),
            _binding("canon", "PACKAGE_ROOT", canon_path, package_root),
            _binding(
                "asset_generator",
                "PROJECT_ROOT",
                tool_root / "blender/compile_asset.py",
                repo,
            ),
            _binding(
                "canon_packet_generator",
                "PROJECT_ROOT",
                tool_root / "pipeline/canon_packet.py",
                repo,
            ),
            _binding(
                "main_build_manifest",
                "PROJECT_ROOT",
                main_manifest_path,
                repo,
            ),
            _binding(
                "states_manifest",
                "PROJECT_ROOT",
                states_manifest_path,
                repo,
            ),
            _binding(
                "determinism_report",
                "PROJECT_ROOT",
                determinism_path,
                repo,
            ),
            _binding(
                "visual_review",
                "PROJECT_ROOT",
                review_path,
                repo,
            ),
            _binding(
                "raw_render_manifest",
                "PACKAGE_ROOT",
                raw_report_path,
                package_root,
            ),
        ]
    }
    board_bindings = {}
    for board_id in BOARD_IDS:
        path = board_paths[board_id]
        with Image.open(path) as image:
            dimensions = image.size
        board_bindings[board_id] = [
            {
                "path": _relative(path, package_root),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "mediaType": "image/png",
                "width": dimensions[0],
                "height": dimensions[1],
            }
        ]
    manifest = {
        "$schema": "https://roblox-top1.local/schemas/visual-canon-evidence.schema.json",
        "schemaVersion": "1.0.0",
        "assetKey": contract["assetKey"],
        "revision": contract["revision"],
        "assetId": canon["assetId"],
        "territoryId": canon["territoryId"],
        "canonId": canon["canonId"],
        "baseCandidateSha256": canon_sha,
        "evidenceClass": "REAL_RENDERED",
        "generatedAt": _utc_now(),
        "generation": {
            "tool": "r3d canon-packet",
            "toolVersion": "1.0.0",
            "deterministicComposition": True,
            "rawRenderStatus": "PASS",
        },
        "authority": authority,
        "boards": board_bindings,
        "humanReviewStatus": "PENDING",
        "productionApproved": False,
    }
    manifest["evidencePackageSha256"] = _package_digest(manifest)
    manifest_path = output / "evidence-manifest.json"
    write_json(manifest_path, manifest)
    review_template = {
        "$schema": "https://roblox-top1.local/schemas/visual-canon-human-review.schema.json",
        "schemaVersion": "1.0.0",
        "status": "PENDING",
        "assetKey": contract["assetKey"],
        "assetId": canon["assetId"],
        "territoryId": canon["territoryId"],
        "revision": contract["revision"],
        "canonId": canon["canonId"],
        "evidenceManifest": _relative(manifest_path, package_root),
        "evidenceManifestSha256": sha256_file(manifest_path),
        "evidencePackageSha256": manifest["evidencePackageSha256"],
        "reviewer": None,
        "reviewedAt": None,
        "decision": None,
        "decisionRecord": None,
        "allowedDecisions": ["LOCK", "REVISION_REQUIRED", "REJECT"],
        "boards": {
            board_id: {
                "status": "PENDING",
                "comment": None,
            }
            for board_id in BOARD_IDS
        },
        "mandatoryChecks": {
            "oneSecondFunctionRead": "PENDING",
            "stateReadWithoutColorOnly": "PENDING",
            "mobileNearMidFar": "PENDING",
            "lightingRobustness": "PENDING",
            "repetitionOneThirtyHundred": "PENDING",
            "requiredAndForbiddenCompliance": "PENDING",
            "artDirectionQuality": "PENDING",
        },
        "productionApproved": False,
    }
    write_json(output / "human-review.json", review_template)
    _write_gallery(
        output,
        contract,
        canon,
        manifest["evidencePackageSha256"],
        board_paths,
        review_template,
    )
    return {
        "status": "PASS",
        "assetKey": contract["assetKey"],
        "revision": contract["revision"],
        "canonId": canon["canonId"],
        "evidenceClass": "REAL_RENDERED",
        "boardCount": len(board_paths),
        "rawRenderDeterminism": raw_report["status"],
        "compositionDeterminism": composition_report["status"],
        "rawRenderCache": "REUSED" if reused_raw else "REBUILT",
        "evidencePackageSha256": manifest["evidencePackageSha256"],
        "evidenceManifest": str(manifest_path),
        "gallery": str(output / "index.html"),
        "humanReview": {
            "status": "PENDING",
            "path": str(output / "human-review.json"),
        },
        "lockEligibleAfterHumanApproval": True,
        "productionApproved": False,
    }
