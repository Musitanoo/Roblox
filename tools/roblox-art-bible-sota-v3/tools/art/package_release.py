from __future__ import annotations

import argparse
import zipfile
from pathlib import Path

from tools.art.build_package_manifest import build_value, included_files
from tools.art.common import ROOT, sha256_file, write_json

ARCHIVE_ROOT = "roblox-art-bible-sota-v3"
FIXED_ZIP_TIMESTAMP = (2026, 7, 15, 0, 0, 0)


def _write_member(archive: zipfile.ZipFile, relative: str, data: bytes) -> None:
    info = zipfile.ZipInfo(f"{ARCHIVE_ROOT}/{relative}", date_time=FIXED_ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, data, compresslevel=9)


def package(output: Path) -> dict[str, object]:
    manifest = build_value()
    manifest_path = ROOT / "PACKAGE_MANIFEST.json"
    write_json(manifest_path, manifest)
    files = included_files()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w") as archive:
        for path in files:
            _write_member(archive, path.relative_to(ROOT).as_posix(), path.read_bytes())
        _write_member(archive, "PACKAGE_MANIFEST.json", manifest_path.read_bytes())

    expected_names = {f"{ARCHIVE_ROOT}/{path.relative_to(ROOT).as_posix()}" for path in files}
    expected_names.add(f"{ARCHIVE_ROOT}/PACKAGE_MANIFEST.json")
    with zipfile.ZipFile(output, "r") as archive:
        observed_names = set(archive.namelist())
        if observed_names != expected_names:
            raise RuntimeError(
                f"Archive member mismatch: missing={sorted(expected_names - observed_names)}, "
                f"extra={sorted(observed_names - expected_names)}"
            )
        for path in files:
            relative = path.relative_to(ROOT).as_posix()
            if archive.read(f"{ARCHIVE_ROOT}/{relative}") != path.read_bytes():
                raise RuntimeError(f"Archive byte mismatch for {relative}")
    return {
        "output": str(output),
        "bytes": output.stat().st_size,
        "sha256": sha256_file(output),
        "fileCount": len(expected_names),
        "treeSha256": manifest["treeSha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a deterministic, self-verified release ZIP.")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT.parent / "roblox-art-bible-sota-v3.zip",
    )
    args = parser.parse_args()
    report = package(args.output)
    print(
        f"[PASS] Release archive: {report['output']} | {report['bytes']} bytes | "
        f"SHA-256 {report['sha256']} | {report['fileCount']} members"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
