from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from tools.art.common import ROOT
from tools.art.bind_studio_captures import PROFILES


TERRITORIES = (
    "industrial-toy-defense",
    "salvaged-frontier",
    "clean-tactical-diorama",
)
CAPTURES = ROOT / "evidence/studio/captures"
OUTPUT = ROOT / "evidence/studio/studio-contact-sheet.jpg"


def main() -> int:
    font = ImageFont.load_default()
    cells: list[tuple[str, Image.Image]] = []
    for territory_id in TERRITORIES:
        for profile_id in PROFILES:
            path = CAPTURES / f"{territory_id}__{profile_id}.jpg"
            with Image.open(path) as source:
                cells.append((f"{territory_id} | {profile_id}", source.convert("RGB").copy()))
    width = max(image.width for _, image in cells)
    height = max(image.height for _, image in cells)
    label_height = 24
    sheet = Image.new("RGB", (width * len(PROFILES), (height + label_height) * len(TERRITORIES)), "#11151b")
    draw = ImageDraw.Draw(sheet)
    for index, (label, image) in enumerate(cells):
        column = index % len(PROFILES)
        row = index // len(PROFILES)
        x = column * width
        y = row * (height + label_height)
        sheet.paste(image, (x, y))
        draw.rectangle((x, y + height, x + width, y + height + label_height), fill="#11151b")
        draw.text((x + 6, y + height + 6), label, fill="#f4f7fb", font=font)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(OUTPUT, format="JPEG", quality=92, optimize=True)
    print(f"[PASS] Studio contact sheet: {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
