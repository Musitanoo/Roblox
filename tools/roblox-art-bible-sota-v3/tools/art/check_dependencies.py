from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from tools.art.common import ROOT


def expected_versions() -> dict[str, str]:
    requirements = ROOT / "requirements-dev.txt"
    result: dict[str, str] = {}
    for raw_line in requirements.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "==" not in line:
            raise ValueError(f"Unpinned dependency in {requirements.name}: {line}")
        name, expected = line.split("==", 1)
        result[name] = expected
    return result


def check() -> list[str]:
    issues: list[str] = []
    for package, expected in expected_versions().items():
        try:
            observed = version(package)
        except PackageNotFoundError:
            issues.append(f"{package} is not installed (expected {expected})")
            continue
        if observed != expected:
            issues.append(f"{package}=={observed} is installed (expected {expected})")
    return issues


def main() -> int:
    issues = check()
    if issues:
        for issue in issues:
            print(f"[FAIL] {issue}")
        print("Run scripts/art-direction.ps1 bootstrap (Windows) or scripts/art-direction.sh bootstrap.")
        return 1
    print(f"[PASS] {len(expected_versions())} pinned Python dependencies match.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
