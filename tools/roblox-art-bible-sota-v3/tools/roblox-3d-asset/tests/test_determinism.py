from __future__ import annotations

import binascii
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipeline.determinism import (
    canonical_png_content_sha256,
    compare_png_render,
    compare_published_state_build,
    sha256_file,
)


def _chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def _png_rgba(
    width: int,
    height: int,
    pixels: bytes,
    metadata: bytes,
) -> bytes:
    signature = b"\x89PNG\r\n\x1a\n"
    header = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    stride = width * 4
    scanlines = b"".join(
        b"\x00" + pixels[offset : offset + stride]
        for offset in range(0, len(pixels), stride)
    )
    return (
        signature
        + _chunk(b"IHDR", header)
        + _chunk(b"tEXt", metadata)
        + _chunk(b"IDAT", zlib.compress(scanlines))
        + _chunk(b"IEND", b"")
    )


def _png(pixel: bytes, metadata: bytes) -> bytes:
    return _png_rgba(1, 1, pixel, metadata)


def _state_fixture(root: Path, pixel: bytes) -> None:
    renders = root / "intact" / "renders"
    renders.mkdir(parents=True)
    state = root / "intact"
    (state / "provenance.json").write_text(
        json.dumps({"semanticSha256": "semantic-intact"}),
        encoding="utf-8",
    )
    (state / "geometry.json").write_text(
        json.dumps({"triangleCount": 12}),
        encoding="utf-8",
    )
    (state / "asset.glb").write_bytes(b"glb")
    (state / "asset-update.fbx").write_bytes(b"fbx")
    (state / "manifest.json").write_text(
        json.dumps(
            {
                "artifacts": {
                    "fbxUpdate": {
                        "sha256": sha256_file(state / "asset-update.fbx"),
                        "bytes": 3,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    (renders / "front.png").write_bytes(_png(pixel, b"fixture"))


class DeterminismTests(unittest.TestCase):
    def test_png_content_hash_ignores_metadata_but_not_pixels(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = root / "first.png"
            second = root / "second.png"
            changed = root / "changed.png"
            first.write_bytes(_png(b"\x10\x20\x30\xff", b"run=a"))
            second.write_bytes(_png(b"\x10\x20\x30\xff", b"run=b"))
            changed.write_bytes(_png(b"\x10\x20\x31\xff", b"run=b"))
            self.assertNotEqual(sha256_file(first), sha256_file(second))
            self.assertEqual(
                canonical_png_content_sha256(first),
                canonical_png_content_sha256(second),
            )
            self.assertNotEqual(
                canonical_png_content_sha256(first),
                canonical_png_content_sha256(changed),
            )

    def test_render_comparison_accepts_only_bounded_raster_variance(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            first = root / "first.png"
            micro = root / "micro.png"
            bounded_field = root / "bounded-field.png"
            excessive_field = root / "excessive-field.png"
            visible = root / "visible.png"
            pixel_count = 512 * 512
            baseline = bytearray(b"\x10\x20\x30\xff" * pixel_count)
            micro_pixels = bytearray(baseline)
            micro_pixels[(313 * 512 + 423) * 4 + 1] += 1
            bounded_field_pixels = bytearray(baseline)
            excessive_field_pixels = bytearray(baseline)
            for index in range(24):
                bounded_field_pixels[index * 4 + 1] += 1
                excessive_field_pixels[index * 4 + 1] += 1
            excessive_field_pixels[24 * 4 + 1] += 1
            visible_pixels = bytearray(baseline)
            visible_pixels[(313 * 512 + 423) * 4 + 1] += 2
            first.write_bytes(
                _png_rgba(512, 512, bytes(baseline), b"run=first")
            )
            micro.write_bytes(
                _png_rgba(512, 512, bytes(micro_pixels), b"run=micro")
            )
            bounded_field.write_bytes(
                _png_rgba(
                    512,
                    512,
                    bytes(bounded_field_pixels),
                    b"run=bounded-field",
                )
            )
            excessive_field.write_bytes(
                _png_rgba(
                    512,
                    512,
                    bytes(excessive_field_pixels),
                    b"run=excessive-field",
                )
            )
            visible.write_bytes(
                _png_rgba(512, 512, bytes(visible_pixels), b"run=visible")
            )

            bounded = compare_png_render(first, micro)
            self.assertTrue(bounded["passed"])
            self.assertEqual("BOUNDED_PIXEL_TOLERANCE", bounded["mode"])
            self.assertEqual(1, bounded["differentPixelCount"])
            self.assertEqual(1, bounded["maximumChannelDelta"])

            bounded_count = compare_png_render(first, bounded_field)
            self.assertTrue(bounded_count["passed"])
            self.assertEqual(24, bounded_count["differentPixelCount"])

            rejected_count = compare_png_render(first, excessive_field)
            self.assertFalse(rejected_count["passed"])
            self.assertEqual(25, rejected_count["differentPixelCount"])

            rejected = compare_png_render(first, visible)
            self.assertFalse(rejected["passed"])
            self.assertEqual("PIXEL_MISMATCH", rejected["mode"])
            self.assertEqual(2, rejected["maximumChannelDelta"])

    def test_published_state_must_match_deterministic_reference(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            published = root / "published"
            reference = root / "reference"
            _state_fixture(published, b"\x10\x20\x30\xff")
            _state_fixture(reference, b"\x10\x20\x30\xff")
            passing = compare_published_state_build(
                published,
                reference,
                ["intact"],
                ["front"],
            )
            self.assertEqual("PASS", passing["status"])

            (published / "intact" / "renders" / "front.png").write_bytes(
                _png(b"\x10\x20\x31\xff", b"corrupt")
            )
            failing = compare_published_state_build(
                published,
                reference,
                ["intact"],
                ["front"],
            )
            self.assertEqual("FAIL", failing["status"])
            self.assertFalse(
                failing["states"][0]["checks"]["renders"][0]["passed"]
            )


if __name__ == "__main__":
    unittest.main()
