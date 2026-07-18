from __future__ import annotations

import hashlib
import json
import struct
import zlib
from pathlib import Path
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
RENDER_PIXEL_TOLERANCE = {
    "maximumDifferentPixelCount": 24,
    "maximumDifferentPixelRatio": 0.0001,
    "maximumChannelDelta": 1,
    "maximumNormalizedMeanAbsoluteError": 0.000001,
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json_sha256(path: Path) -> str:
    value = json.loads(path.read_text(encoding="utf-8"))
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _paeth_predictor(left: int, above: int, upper_left: int) -> int:
    estimate = left + above - upper_left
    left_distance = abs(estimate - left)
    above_distance = abs(estimate - above)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= above_distance and left_distance <= upper_left_distance:
        return left
    if above_distance <= upper_left_distance:
        return above
    return upper_left


def _decode_png_rgba8(path: Path) -> tuple[int, int, bytes]:
    payload = path.read_bytes()
    if not payload.startswith(PNG_SIGNATURE):
        raise ValueError(f"not a PNG file: {path}")
    cursor = len(PNG_SIGNATURE)
    critical: dict[bytes, list[bytes]] = {
        b"IHDR": [],
        b"PLTE": [],
        b"tRNS": [],
        b"IDAT": [],
    }
    while cursor < len(payload):
        if cursor + 12 > len(payload):
            raise ValueError(f"truncated PNG chunk: {path}")
        length = struct.unpack(">I", payload[cursor : cursor + 4])[0]
        chunk_type = payload[cursor + 4 : cursor + 8]
        data_start = cursor + 8
        data_end = data_start + length
        if data_end + 4 > len(payload):
            raise ValueError(f"truncated PNG data: {path}")
        if chunk_type in critical:
            critical[chunk_type].append(payload[data_start:data_end])
        cursor = data_end + 4
        if chunk_type == b"IEND":
            break
    if len(critical[b"IHDR"]) != 1 or not critical[b"IDAT"]:
        raise ValueError(f"PNG is missing IHDR or IDAT: {path}")
    width, height, bit_depth, color_type, compression, filtering, interlace = (
        struct.unpack(">IIBBBBB", critical[b"IHDR"][0])
    )
    if (
        bit_depth != 8
        or color_type != 6
        or compression != 0
        or filtering != 0
        or interlace != 0
    ):
        raise ValueError(
            "render PNG must be non-interlaced RGBA8: "
            f"{path}; bitDepth={bit_depth}; colorType={color_type}; "
            f"compression={compression}; filter={filtering}; interlace={interlace}"
        )
    decoded_scanlines = zlib.decompress(b"".join(critical[b"IDAT"]))
    bytes_per_pixel = 4
    row_bytes = width * bytes_per_pixel
    expected_bytes = height * (row_bytes + 1)
    if len(decoded_scanlines) != expected_bytes:
        raise ValueError(
            f"unexpected PNG scanline size: {path}; "
            f"expected={expected_bytes}; observed={len(decoded_scanlines)}"
        )
    pixels = bytearray(height * row_bytes)
    source_offset = 0
    for row_index in range(height):
        filter_type = decoded_scanlines[source_offset]
        source_offset += 1
        row = decoded_scanlines[source_offset : source_offset + row_bytes]
        source_offset += row_bytes
        destination_offset = row_index * row_bytes
        previous_offset = destination_offset - row_bytes
        for column, encoded in enumerate(row):
            left = (
                pixels[destination_offset + column - bytes_per_pixel]
                if column >= bytes_per_pixel
                else 0
            )
            above = (
                pixels[previous_offset + column]
                if row_index > 0
                else 0
            )
            upper_left = (
                pixels[previous_offset + column - bytes_per_pixel]
                if row_index > 0 and column >= bytes_per_pixel
                else 0
            )
            if filter_type == 0:
                value = encoded
            elif filter_type == 1:
                value = encoded + left
            elif filter_type == 2:
                value = encoded + above
            elif filter_type == 3:
                value = encoded + ((left + above) // 2)
            elif filter_type == 4:
                value = encoded + _paeth_predictor(left, above, upper_left)
            else:
                raise ValueError(
                    f"unsupported PNG filter {filter_type}: {path}"
                )
            pixels[destination_offset + column] = value & 0xFF
    return width, height, bytes(pixels)


def canonical_png_content_sha256(path: Path) -> str:
    width, height, pixels = _decode_png_rgba8(path)
    return _canonical_rgba8_sha256(width, height, pixels)


def _canonical_rgba8_sha256(width: int, height: int, pixels: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(b"ROBLOX_TOP1_PNG_RGBA8_V2\0")
    digest.update(struct.pack(">II", width, height))
    digest.update(pixels)
    return digest.hexdigest()


def compare_png_render(
    first: Path,
    second: Path,
    tolerance: dict[str, float | int] | None = None,
) -> dict[str, Any]:
    thresholds = tolerance or RENDER_PIXEL_TOLERANCE
    first_width, first_height, first_pixels = _decode_png_rgba8(first)
    second_width, second_height, second_pixels = _decode_png_rgba8(second)
    first_hash = _canonical_rgba8_sha256(
        first_width, first_height, first_pixels
    )
    second_hash = _canonical_rgba8_sha256(
        second_width, second_height, second_pixels
    )
    dimensions_match = (
        first_width == second_width and first_height == second_height
    )
    if not dimensions_match:
        return {
            "passed": False,
            "mode": "DIMENSION_MISMATCH",
            "first": first_hash,
            "second": second_hash,
            "dimensions": {
                "first": [first_width, first_height],
                "second": [second_width, second_height],
                "passed": False,
            },
            "tolerance": thresholds,
        }
    if first_hash == second_hash:
        return {
            "passed": True,
            "mode": "EXACT",
            "first": first_hash,
            "second": second_hash,
            "dimensions": {
                "first": [first_width, first_height],
                "second": [second_width, second_height],
                "passed": True,
            },
            "differentPixelCount": 0,
            "differentPixelRatio": 0.0,
            "maximumChannelDelta": 0,
            "normalizedMeanAbsoluteError": 0.0,
            "tolerance": thresholds,
        }
    different_pixels = 0
    maximum_channel_delta = 0
    absolute_error = 0
    for offset in range(0, len(first_pixels), 4):
        pixel_differs = False
        for channel in range(4):
            delta = abs(
                first_pixels[offset + channel] - second_pixels[offset + channel]
            )
            absolute_error += delta
            maximum_channel_delta = max(maximum_channel_delta, delta)
            pixel_differs = pixel_differs or delta != 0
        if pixel_differs:
            different_pixels += 1
    pixel_count = first_width * first_height
    different_pixel_ratio = different_pixels / pixel_count
    normalized_mean_absolute_error = (
        absolute_error / (len(first_pixels) * 255)
    )
    passed = (
        different_pixels
        <= int(thresholds.get("maximumDifferentPixelCount", pixel_count))
        and
        different_pixel_ratio
        <= float(thresholds["maximumDifferentPixelRatio"])
        and maximum_channel_delta
        <= int(thresholds["maximumChannelDelta"])
        and normalized_mean_absolute_error
        <= float(thresholds["maximumNormalizedMeanAbsoluteError"])
    )
    return {
        "passed": passed,
        "mode": "BOUNDED_PIXEL_TOLERANCE" if passed else "PIXEL_MISMATCH",
        "first": first_hash,
        "second": second_hash,
        "dimensions": {
            "first": [first_width, first_height],
            "second": [second_width, second_height],
            "passed": True,
        },
        "differentPixelCount": different_pixels,
        "differentPixelRatio": different_pixel_ratio,
        "maximumChannelDelta": maximum_channel_delta,
        "normalizedMeanAbsoluteError": normalized_mean_absolute_error,
        "tolerance": thresholds,
    }


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _state_fingerprints(
    state: Path,
) -> dict[str, Any]:
    provenance = _read_json(state / "provenance.json")
    manifest = _read_json(state / "manifest.json")
    fbx_path = state / "asset-update.fbx"
    return {
        "semantic": provenance["semanticSha256"],
        "glb": sha256_file(state / "asset.glb"),
        "fbx": sha256_file(fbx_path),
        "fbxBytes": fbx_path.stat().st_size,
        "fbxManifest": manifest["artifacts"]["fbxUpdate"],
        "geometry": canonical_json_sha256(state / "geometry.json"),
    }


def compare_published_state_build(
    published: Path,
    reference: Path,
    state_ids: list[str],
    views: list[str],
) -> dict[str, Any]:
    state_reports: list[dict[str, Any]] = []
    for state_id in state_ids:
        try:
            actual = _state_fingerprints(published / state_id)
            expected = _state_fingerprints(reference / state_id)
            render_checks = []
            for view in views:
                comparison = compare_png_render(
                    published / state_id / "renders" / f"{view}.png",
                    reference / state_id / "renders" / f"{view}.png",
                )
                comparison["view"] = view
                comparison["published"] = comparison.pop("first")
                comparison["reference"] = comparison.pop("second")
                render_checks.append(comparison)
            checks = {
                "semantic": actual["semantic"] == expected["semantic"],
                "glb": actual["glb"] == expected["glb"],
                "fbxArtifactIntegrity": {
                    "published": (
                        actual["fbx"]
                        == actual["fbxManifest"]["sha256"]
                        and actual["fbxBytes"]
                        == actual["fbxManifest"]["bytes"]
                    ),
                    "reference": (
                        expected["fbx"]
                        == expected["fbxManifest"]["sha256"]
                        and expected["fbxBytes"]
                        == expected["fbxManifest"]["bytes"]
                    ),
                },
                "fbxCrossPathBinaryDeterminism": {
                    "required": False,
                    "reason": (
                        "FBX embeds normalized source-path length; raw binary "
                        "identity is authoritative only at canonical paths"
                    ),
                },
                "geometry": actual["geometry"] == expected["geometry"],
                "renders": render_checks,
            }
            checks["fbxArtifactIntegrity"]["passed"] = (
                checks["fbxArtifactIntegrity"]["published"]
                and checks["fbxArtifactIntegrity"]["reference"]
            )
            passed = (
                checks["semantic"]
                and checks["glb"]
                and checks["fbxArtifactIntegrity"]["passed"]
                and checks["geometry"]
                and all(item["passed"] for item in render_checks)
            )
            state_reports.append(
                {
                    "stateId": state_id,
                    "status": "PASS" if passed else "FAIL",
                    "checks": checks,
                }
            )
        except (KeyError, OSError, ValueError, zlib.error) as error:
            state_reports.append(
                {
                    "stateId": state_id,
                    "status": "FAIL",
                    "reason": str(error),
                }
            )
    passed = (
        len(state_reports) == len(state_ids)
        and all(item["status"] == "PASS" for item in state_reports)
    )
    return {
        "schemaVersion": "1.1.0",
        "status": "PASS" if passed else "FAIL",
        "publishedRoot": str(published),
        "referenceRoot": str(reference),
        "stateCoverage": state_ids,
        "states": state_reports,
    }


def compare_state_builds(
    run_a: Path,
    run_b: Path,
    state_ids: list[str],
    views: list[str],
) -> dict[str, Any]:
    state_reports: list[dict[str, Any]] = []
    semantic_hashes: list[str] = []
    glb_hashes: list[str] = []
    invariant_signatures: list[dict[str, Any]] = []
    for state_id in state_ids:
        state_a = run_a / state_id
        state_b = run_b / state_id
        provenance_a = _read_json(state_a / "provenance.json")
        provenance_b = _read_json(state_b / "provenance.json")
        geometry_a = _read_json(state_a / "geometry.json")
        geometry_b = _read_json(state_b / "geometry.json")
        semantic_a = provenance_a["semanticSha256"]
        semantic_b = provenance_b["semanticSha256"]
        glb_a = sha256_file(state_a / "asset.glb")
        glb_b = sha256_file(state_b / "asset.glb")
        fbx_a = sha256_file(state_a / "asset-update.fbx")
        fbx_b = sha256_file(state_b / "asset-update.fbx")
        geometry_hash_a = canonical_json_sha256(state_a / "geometry.json")
        geometry_hash_b = canonical_json_sha256(state_b / "geometry.json")
        render_checks = []
        for view in views:
            comparison = compare_png_render(
                state_a / "renders" / f"{view}.png",
                state_b / "renders" / f"{view}.png",
            )
            comparison["view"] = view
            comparison["runA"] = comparison.pop("first")
            comparison["runB"] = comparison.pop("second")
            render_checks.append(comparison)
        checks = {
            "semantic": {
                "runA": semantic_a,
                "runB": semantic_b,
                "passed": semantic_a == semantic_b,
            },
            "glb": {"runA": glb_a, "runB": glb_b, "passed": glb_a == glb_b},
            "fbx": {"runA": fbx_a, "runB": fbx_b, "passed": fbx_a == fbx_b},
            "geometry": {
                "runA": geometry_hash_a,
                "runB": geometry_hash_b,
                "passed": geometry_hash_a == geometry_hash_b,
            },
            "renders": render_checks,
        }
        passed = all(
            [
                checks["semantic"]["passed"],
                checks["glb"]["passed"],
                checks["fbx"]["passed"],
                checks["geometry"]["passed"],
                all(item["passed"] for item in render_checks),
            ]
        )
        state_reports.append(
            {
                "stateId": state_id,
                "status": "PASS" if passed else "FAIL",
                "checks": checks,
            }
        )
        semantic_hashes.append(semantic_a)
        glb_hashes.append(glb_a)
        invariant_signatures.append(
            {
                "stateId": state_id,
                "componentNames": [
                    item["name"] for item in geometry_a["objects"]
                ],
                "triangleCount": geometry_a["triangleCount"],
                "dimensionsStuds": geometry_a["dimensionsStuds"],
                "pivot": geometry_a["pivot"],
            }
        )

    reference = invariant_signatures[0]
    invariant_checks = []
    for signature in invariant_signatures:
        checks = {
            "componentNames": (
                signature["componentNames"] == reference["componentNames"]
            ),
            "triangleCount": (
                signature["triangleCount"] == reference["triangleCount"]
            ),
            "dimensionsStuds": (
                signature["dimensionsStuds"] == reference["dimensionsStuds"]
            ),
            "pivot": signature["pivot"] == reference["pivot"],
        }
        invariant_checks.append(
            {
                "stateId": signature["stateId"],
                "passed": all(checks.values()),
                "checks": checks,
            }
        )

    distinctness = {
        "semanticHashesUnique": len(set(semantic_hashes)) == len(state_ids),
        "glbHashesUnique": len(set(glb_hashes)) == len(state_ids),
    }
    passed = (
        all(item["status"] == "PASS" for item in state_reports)
        and all(item["passed"] for item in invariant_checks)
        and all(distinctness.values())
    )
    return {
        "schemaVersion": "1.1.0",
        "status": "PASS" if passed else "FAIL",
        "stateCoverage": state_ids,
        "states": state_reports,
        "stateInvariants": invariant_checks,
        "stateDistinctness": distinctness,
        "blendBinaryDeterminism": {
            "required": False,
            "reason": (
                "source.blend records its output path; semantic, geometry, "
                "Roblox export and decoded render content are authoritative"
            ),
        },
    }
