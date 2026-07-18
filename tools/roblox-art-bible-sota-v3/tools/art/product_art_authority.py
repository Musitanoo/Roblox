from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from tools.art.common import (
    PROJECT_ROOT,
    ROOT,
    canonical_json_bytes,
    load_json,
    sha256_bytes,
    validate_with_schema,
)

AUTHORITY_PATH = ROOT / "art/authority/product-art-authority-v1.json"
AUTHORITY_SCHEMA = ROOT / "schemas/product-art-authority.schema.json"
HEADING = re.compile(r"^(#{1,6})\s+.+?\s*$")


def extract_markdown_sections(
    markdown: str,
    headings: list[str],
) -> list[dict[str, str]]:
    lines = markdown.replace("\r\n", "\n").replace("\r", "\n").splitlines()
    positions: dict[str, list[int]] = {heading: [] for heading in headings}
    for index, line in enumerate(lines):
        if line in positions:
            positions[line].append(index)

    sections: list[dict[str, str]] = []
    for heading in headings:
        matches = positions[heading]
        if len(matches) != 1:
            raise ValueError(
                f"selected GDD heading must exist exactly once: {heading!r}; "
                f"observed={len(matches)}"
            )
        start = matches[0]
        level = len(heading) - len(heading.lstrip("#"))
        end = len(lines)
        for index in range(start + 1, len(lines)):
            match = HEADING.match(lines[index])
            if match and len(match.group(1)) <= level:
                end = index
                break
        sections.append(
            {
                "heading": heading,
                "markdown": "\n".join(lines[start:end]).strip(),
            }
        )
    return sections


def projection_sha256(markdown: str, headings: list[str]) -> str:
    return sha256_bytes(
        canonical_json_bytes(extract_markdown_sections(markdown, headings))
    )


def validate_product_art_authority(
    authority_path: Path = AUTHORITY_PATH,
) -> list[str]:
    issues: list[str] = []
    try:
        authority = load_json(authority_path)
    except (OSError, ValueError) as error:
        return [f"product art authority is unreadable: {error}"]
    issues.extend(validate_with_schema(authority, AUTHORITY_SCHEMA))
    if issues:
        return issues

    projection: dict[str, Any] = authority["sourceProjection"]
    gdd_path = PROJECT_ROOT / projection["gddPath"]
    if not gdd_path.is_file():
        return [f"product art GDD source is missing: {gdd_path}"]
    markdown = gdd_path.read_text(encoding="utf-8")
    title = markdown.splitlines()[0] if markdown else ""
    expected_title_suffix = f"v{projection['gddDocumentVersion']}"
    if not title.endswith(expected_title_suffix):
        issues.append(
            "product art GDD version drift: "
            f"expected title suffix {expected_title_suffix!r}, observed {title!r}"
        )
    try:
        observed = projection_sha256(
            markdown,
            projection["sectionHeadings"],
        )
    except ValueError as error:
        issues.append(str(error))
    else:
        if observed != projection["contentSha256"]:
            issues.append(
                "product art GDD projection drift: "
                f"expected={projection['contentSha256']} observed={observed}"
            )
    return issues
