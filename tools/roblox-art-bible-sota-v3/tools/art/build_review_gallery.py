from __future__ import annotations

import argparse
import html
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from tools.art.common import ROOT, load_json, sha256_file
from tools.art.validate_build_report import validate_report


TERRITORIES = (
    "industrial-toy-defense",
    "salvaged-frontier",
    "clean-tactical-diorama",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _contact_sheet(
    territory_id: str,
    cards: list[dict[str, Any]],
    output_path: Path,
) -> dict[str, Any]:
    thumb_width, thumb_height = 320, 240
    label_height = 34
    columns = 4
    rows = (len(cards) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * thumb_width, rows * (thumb_height + label_height)), "#111821")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default(size=16)
    for index, card in enumerate(cards):
        image = Image.open(card["absolutePath"]).convert("RGB")
        image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        x = (index % columns) * thumb_width
        y = (index // columns) * (thumb_height + label_height)
        offset = ((thumb_width - image.width) // 2, (thumb_height - image.height) // 2)
        sheet.paste(image, (x + offset[0], y + offset[1]))
        label = f"{card['assetId']}  /  {card['stateId']}"
        draw.text((x + 10, y + thumb_height + 8), label, fill="#E8F1F7", font=font)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, optimize=True)
    return {
        "territoryId": territory_id,
        "path": output_path.relative_to(output_path.parents[2]).as_posix(),
        "sha256": sha256_file(output_path),
        "resolution": {"width": sheet.width, "height": sheet.height},
    }


def _html_document(cards: list[dict[str, Any]], generated_at: str) -> str:
    territories = sorted({card["territoryId"] for card in cards})
    assets = sorted({card["assetId"] for card in cards})
    states = ("intact", "damaged", "critical")

    def options(values: tuple[str, ...] | list[str]) -> str:
        return "".join(f'<option value="{html.escape(value)}">{html.escape(value)}</option>' for value in values)

    card_markup = []
    for card in cards:
        label = f"{card['territoryId']} · {card['assetId']} · {card['stateId']}"
        card_markup.append(
            f"""
            <article class="card" tabindex="0"
                data-territory="{html.escape(card['territoryId'])}"
                data-asset="{html.escape(card['assetId'])}"
                data-state="{html.escape(card['stateId'])}">
              <button class="image-button" type="button" aria-label="Agrandir {html.escape(label)}">
                <img loading="lazy" src="{html.escape(card['webPath'])}" alt="{html.escape(label)}">
              </button>
              <div class="meta">
                <div><strong>{html.escape(card['assetId'])}</strong><span class="state {html.escape(card['stateId'])}">{html.escape(card['stateId'])}</span></div>
                <small>{html.escape(card['territoryId'])}</small>
                <small>{card['triangles']:,} / {card['triangleBudget']:,} triangles · {card['meshObjectCount']} meshes</small>
              </div>
            </article>
            """
        )

    return f"""<!doctype html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Roblox Art Bible v3 · Review Gallery</title>
  <style>
    :root {{ color-scheme: dark; --bg:#0b1118; --panel:#121b25; --line:#263646; --text:#e8f1f7; --muted:#91a4b5; --cyan:#42d7e5; }}
    * {{ box-sizing:border-box }} body {{ margin:0; font:15px/1.45 Inter,Segoe UI,sans-serif; background:linear-gradient(145deg,#081018,#101925); color:var(--text) }}
    header {{ position:sticky; top:0; z-index:3; padding:18px clamp(18px,4vw,52px); background:#0b1118e8; border-bottom:1px solid var(--line); backdrop-filter:blur(12px) }}
    h1 {{ margin:0 0 4px; font-size:clamp(20px,3vw,32px); letter-spacing:-.03em }} .sub {{ color:var(--muted) }}
    .toolbar {{ display:flex; flex-wrap:wrap; gap:10px; margin-top:14px }} select,button {{ border:1px solid var(--line); border-radius:9px; background:#162230; color:var(--text); padding:9px 12px }}
    main {{ padding:24px clamp(18px,4vw,52px) 60px }} .count {{ margin-bottom:14px; color:var(--muted) }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(285px,1fr)); gap:16px }}
    .card {{ overflow:hidden; border:1px solid var(--line); border-radius:14px; background:var(--panel); box-shadow:0 12px 34px #0005; transition:.18s transform,.18s border-color }}
    .card:hover,.card:focus-within {{ transform:translateY(-3px); border-color:#3f5d75 }} .card[hidden] {{ display:none }}
    .image-button {{ display:block; width:100%; padding:0; border:0; border-radius:0; cursor:zoom-in; background:#080d13 }}
    img {{ display:block; width:100%; aspect-ratio:4/3; object-fit:cover }} .meta {{ display:grid; gap:3px; padding:13px 14px 15px }}
    .meta div {{ display:flex; justify-content:space-between; gap:8px }} small {{ color:var(--muted) }}
    .state {{ padding:2px 8px; border-radius:999px; font-size:11px; text-transform:uppercase; letter-spacing:.08em; background:#263646 }}
    .state.damaged {{ background:#5b4a18 }} .state.critical {{ background:#632a33 }}
    dialog {{ width:min(94vw,1200px); border:1px solid var(--line); border-radius:14px; padding:0; background:#070c11; color:var(--text) }}
    dialog::backdrop {{ background:#000c }} dialog img {{ width:100%; height:auto; max-height:84vh; object-fit:contain }} dialog button {{ position:absolute; right:10px; top:10px; cursor:pointer }}
  </style>
</head>
<body>
  <header><h1>Review Gallery · Art Bible v3</h1><div class="sub">39 variantes applicables · rendu Blender de prévalidation · Studio reste canonique · {html.escape(generated_at)}</div>
    <div class="toolbar">
      <select id="territory" aria-label="Territoire"><option value="">Tous les territoires</option>{options(territories)}</select>
      <select id="asset" aria-label="Asset"><option value="">Tous les assets</option>{options(assets)}</select>
      <select id="state" aria-label="État"><option value="">Tous les états</option>{options(list(states))}</select>
      <button id="reset" type="button">Réinitialiser</button>
    </div>
  </header>
  <main><div class="count" id="count"></div><section class="grid">{''.join(card_markup)}</section></main>
  <dialog id="viewer"><button type="button" aria-label="Fermer">Fermer</button><img alt="Vue agrandie"></dialog>
  <script>
    const cards=[...document.querySelectorAll('.card')], filters=['territory','asset','state'];
    const apply=()=>{{let shown=0; for(const card of cards){{const visible=filters.every(k=>!document.getElementById(k).value||card.dataset[k]===document.getElementById(k).value); card.hidden=!visible; shown+=visible?1:0}} document.getElementById('count').textContent=`${{shown}} variante${{shown>1?'s':''}} affichée${{shown>1?'s':''}}`;}};
    filters.forEach(k=>document.getElementById(k).addEventListener('change',apply)); document.getElementById('reset').onclick=()=>{{filters.forEach(k=>document.getElementById(k).value='');apply()}};
    const dialog=document.getElementById('viewer'), large=dialog.querySelector('img'); document.querySelectorAll('.image-button').forEach(button=>button.onclick=()=>{{large.src=button.querySelector('img').src;large.alt=button.querySelector('img').alt;dialog.showModal()}}); dialog.querySelector('button').onclick=()=>dialog.close(); dialog.onclick=e=>{{if(e.target===dialog)dialog.close()}}; apply();
  </script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local review gallery from current, hash-validated Blender reports.")
    parser.add_argument("--output", type=Path, default=ROOT / "build/review")
    parser.add_argument("--build-root", type=Path, default=ROOT / "build")
    parser.add_argument("--territory", choices=TERRITORIES, action="append")
    args = parser.parse_args()
    territories = tuple(args.territory or TERRITORIES)
    output = args.output.resolve()
    build_root = args.build_root.resolve()
    output.mkdir(parents=True, exist_ok=True)

    cards: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    for territory_id in territories:
        report_path = build_root / territory_id / "build-report.json"
        issues = validate_report(report_path)
        if issues:
            raise RuntimeError(f"{territory_id}: stale or invalid build report: {'; '.join(issues[:5])}")
        report = load_json(report_path)
        if not report["reviewRequested"] or not report["reviewEvidence"]:
            raise RuntimeError(f"{territory_id}: review renders are missing; rebuild with -ReviewRenders")
        reports.append({"territoryId": territory_id, "reportSha256": sha256_file(report_path), "inputHashes": report["inputHashes"]})
        asset_reports = {(item["assetId"], item["stateId"]): item for item in report["assets"]}
        for evidence in report["reviewEvidence"]:
            asset_report = asset_reports[(evidence["assetId"], evidence["stateId"])]
            absolute = report_path.parent / evidence["path"]
            cards.append(
                {
                    "territoryId": territory_id,
                    "assetId": evidence["assetId"],
                    "stateId": evidence["stateId"],
                    "triangles": asset_report["triangles"],
                    "triangleBudget": asset_report["triangleBudget"],
                    "meshObjectCount": asset_report["meshObjectCount"],
                    "sourceSha256": evidence["sha256"],
                    "absolutePath": absolute,
                    "webPath": Path(os.path.relpath(absolute, output)).as_posix(),
                }
            )

    cards.sort(key=lambda item: (TERRITORIES.index(item["territoryId"]), item["assetId"], item["stateId"]))
    generated_at = _utc_now()
    contact_sheets = []
    for territory_id in territories:
        territory_cards = [card for card in cards if card["territoryId"] == territory_id]
        contact_sheets.append(_contact_sheet(territory_id, territory_cards, output / "contact-sheets" / f"{territory_id}.png"))

    manifest = {
        "schemaVersion": "1.0.0",
        "status": "REQUIRES_HUMAN_REVIEW",
        "generatedAt": generated_at,
        "rendererTruth": "BLENDER_PREFLIGHT_ONLY_STUDIO_IS_CANONICAL",
        "variantCount": len(cards),
        "reports": reports,
        "contactSheets": contact_sheets,
        "cards": [{key: value for key, value in card.items() if key not in {"absolutePath", "webPath"}} for card in cards],
    }
    manifest_path = output / "review-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    index_path = output / "index.html"
    index_path.write_text(_html_document(cards, generated_at), encoding="utf-8")
    print(json.dumps({"status": "PASS", "gallery": str(index_path), "manifest": str(manifest_path), "variants": len(cards)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
