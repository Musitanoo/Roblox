from __future__ import annotations

import argparse
import html
import json
import secrets
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from random import Random
from typing import Any

from PIL import Image

from tools.art.common import (
    ROOT,
    canonical_json_bytes,
    load_json,
    rel,
    sha256_bytes,
    sha256_file,
    validate_with_schema,
    write_json,
)

LABELS = ("A", "B", "C")
TERRITORIES = (
    "industrial-toy-defense",
    "salvaged-frontier",
    "clean-tactical-diorama",
)
STUDY_ID = "art-direction-vertical-slice-v1"
TARGET_PARTICIPANTS = 12
TARGET_EXPERTS = 4
EXPOSURE_MS = 5000

TASKS: tuple[dict[str, Any], ...] = (
    {
        "taskId": "silhouette_barricade_60",
        "assetId": "barricade",
        "stateId": "intact",
        "camera": "far",
        "pass": "silhouette",
        "prompt": "Quel objet cette silhouette représente-t-elle ?",
        "options": ["barricade", "objective_core", "enemy_standard"],
        "answer": "barricade",
    },
    {
        "taskId": "silhouette_objective_60",
        "assetId": "objective_core",
        "stateId": "intact",
        "camera": "far",
        "pass": "silhouette",
        "prompt": "Quel objet cette silhouette représente-t-elle ?",
        "options": ["barricade", "objective_core", "enemy_standard"],
        "answer": "objective_core",
    },
    {
        "taskId": "silhouette_enemy_60",
        "assetId": "enemy_standard",
        "stateId": "intact",
        "camera": "far",
        "pass": "silhouette",
        "prompt": "Quel objet cette silhouette représente-t-elle ?",
        "options": ["barricade", "objective_core", "enemy_standard"],
        "answer": "enemy_standard",
    },
    {
        "taskId": "function_buildable_30",
        "assetId": "barricade",
        "stateId": "intact",
        "camera": "mid",
        "pass": "beauty",
        "prompt": "Quelle fonction de gameplay cet objet communique-t-il ?",
        "options": ["buildable_defense", "defendable_objective", "hostile_threat"],
        "answer": "buildable_defense",
    },
    {
        "taskId": "function_objective_30",
        "assetId": "objective_core",
        "stateId": "intact",
        "camera": "mid",
        "pass": "beauty",
        "prompt": "Quelle fonction de gameplay cet objet communique-t-il ?",
        "options": ["buildable_defense", "defendable_objective", "hostile_threat"],
        "answer": "defendable_objective",
    },
    {
        "taskId": "function_threat_30",
        "assetId": "enemy_standard",
        "stateId": "intact",
        "camera": "mid",
        "pass": "beauty",
        "prompt": "Quelle fonction de gameplay cet objet communique-t-il ?",
        "options": ["buildable_defense", "defendable_objective", "hostile_threat"],
        "answer": "hostile_threat",
    },
    {
        "taskId": "state_intact",
        "assetId": "objective_core",
        "stateId": "intact",
        "camera": "mid",
        "pass": "beauty",
        "prompt": "Quel est l’état actuel de l’objet ?",
        "options": ["intact", "damaged", "critical"],
        "answer": "intact",
    },
    {
        "taskId": "state_damaged",
        "assetId": "objective_core",
        "stateId": "damaged",
        "camera": "mid",
        "pass": "beauty",
        "prompt": "Quel est l’état actuel de l’objet ?",
        "options": ["intact", "damaged", "critical"],
        "answer": "damaged",
    },
    {
        "taskId": "state_critical",
        "assetId": "objective_core",
        "stateId": "critical",
        "camera": "mid",
        "pass": "beauty",
        "prompt": "Quel est l’état actuel de l’objet ?",
        "options": ["intact", "damaged", "critical"],
        "answer": "critical",
    },
    {
        "taskId": "impact_direction",
        "assetId": "damage_effect",
        "stateId": "critical",
        "camera": "near",
        "pass": "beauty",
        "prompt": "De quelle direction provient l’impact ?",
        "options": ["left", "right", "front", "back"],
        "answer": "left",
    },
)

OPTION_LABELS = {
    "barricade": "Barricade défensive",
    "objective_core": "Objectif à défendre",
    "enemy_standard": "Ennemi standard",
    "buildable_defense": "Défense constructible",
    "defendable_objective": "Objectif à protéger",
    "hostile_threat": "Menace hostile",
    "intact": "Intact",
    "damaged": "Endommagé",
    "critical": "Critique",
    "left": "Gauche",
    "right": "Droite",
    "front": "Avant",
    "back": "Arrière",
}

DIMENSION_LABELS = {
    "functionalReadability": "Lecture fonctionnelle",
    "silhouetteHierarchy": "Silhouette et hiérarchie des formes",
    "roleStateDifferentiation": "Différenciation des rôles et états",
    "identityDistinctiveness": "Identité distinctive",
    "mobileClutterControl": "Contrôle du bruit visuel mobile",
    "materialLightingRobustness": "Robustesse des matériaux et éclairages",
    "productionScalability": "Capacité de production",
    "modularityReuse": "Modularité et réutilisation",
    "technicalFitness": "Adéquation technique",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _under_root(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise RuntimeError("The study output must stay under the installed workflow root.") from exc
    return resolved


def _image_source(evidence_root: Path, territory: str, task: dict[str, Any]) -> Path:
    name = (
        f"{territory}__{task['assetId']}__{task['stateId']}__{task['camera']}__"
        f"Lighting_Gameplay_Default__world_neutral_light__mobile_landscape_hard__"
        f"{task['pass']}.png"
    )
    path = evidence_root / "build" / territory / "renders" / "full" / name
    if not path.is_file():
        raise RuntimeError(
            f"Missing full-render stimulus: {path}. Run art-direction build "
            "-RenderMode full before preparing the study."
        )
    return path


def _reencode_image(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        image.convert("RGB").save(destination, format="PNG", optimize=True)


def _copy_expert_image(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise RuntimeError(f"Missing expert-review evidence: {source}")
    _reencode_image(source, destination)


def _public_package_id(
    stimuli: list[dict[str, Any]],
    expert_images: list[dict[str, Any]],
    protocol: dict[str, Any],
    rubric: dict[str, Any],
) -> str:
    contract = {
        "studyId": STUDY_ID,
        "labels": LABELS,
        "exposureMs": EXPOSURE_MS,
        "stimuli": stimuli,
        "expertImages": expert_images,
        "tasks": TASKS,
        "generatorSha256": sha256_file(Path(__file__)),
        "protocolSha256": sha256_bytes(canonical_json_bytes(protocol)),
        "rubricSha256": sha256_bytes(canonical_json_bytes(rubric)),
    }
    return sha256_bytes(canonical_json_bytes(contract))


def _participant_assignments(public_package_id: str, stimuli: list[dict[str, Any]]) -> dict[str, Any]:
    assignments: dict[str, Any] = {}
    task_lookup = {(item["blindLabel"], item["taskId"]): item for item in stimuli}
    for index in range(TARGET_PARTICIPANTS):
        participant_id = f"P{index + 1:02d}"
        rng = Random(f"{public_package_id}:{participant_id}")
        trials = []
        pairs = [(label, task) for label in LABELS for task in TASKS]
        for _ in range(200):
            rng.shuffle(pairs)
            if all(
                not (
                    offset >= 2
                    and pairs[offset][0] == pairs[offset - 1][0] == pairs[offset - 2][0]
                )
                for offset in range(len(pairs))
            ):
                break
        for label, task in pairs:
            options = list(task["options"])
            rng.shuffle(options)
            item = task_lookup[(label, task["taskId"])]
            trials.append(
                {
                    "blindLabel": label,
                    "taskId": task["taskId"],
                    "prompt": task["prompt"],
                    "image": item["path"],
                    "options": [
                        {"id": option, "label": OPTION_LABELS[option]} for option in options
                    ],
                }
            )
        assignments[participant_id] = {"trials": trials}
    return assignments


def _expert_assignments(public_package_id: str) -> dict[str, Any]:
    assignments: dict[str, Any] = {}
    roles = ("function_silhouette", "art_direction_coherence")
    for index in range(TARGET_EXPERTS):
        reviewer_id = f"R{index + 1:02d}"
        labels = list(LABELS)
        Random(f"{public_package_id}:{reviewer_id}").shuffle(labels)
        assignments[reviewer_id] = {
            "reviewerRole": roles[index % len(roles)],
            "labelOrder": labels,
        }
    return assignments


def _participant_html(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Étude visuelle — participants</title>
<style>
:root{{color-scheme:dark;--bg:#071019;--panel:#111d29;--line:#294055;--text:#eef7fc;--muted:#99adbd;--cyan:#54dbea}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top,#13283a,#071019 62%);color:var(--text);font:16px/1.45 Segoe UI,sans-serif}}
main{{width:min(920px,100%);margin:auto;padding:24px}}section{{background:#101c28;border:1px solid var(--line);border-radius:18px;padding:clamp(18px,4vw,36px)}}
h1,h2{{margin-top:0}}label{{display:grid;gap:7px;margin:14px 0}}select,input,textarea,button{{font:inherit}}select,input,textarea{{width:100%;padding:12px;border:1px solid var(--line);border-radius:10px;background:#0a1520;color:var(--text)}}
button{{padding:12px 18px;border:1px solid #3b647b;border-radius:11px;background:#153549;color:var(--text);cursor:pointer}}button.primary{{background:#12677a}}button:disabled{{opacity:.45;cursor:not-allowed}}
.hidden{{display:none!important}}.muted{{color:var(--muted)}}#stimulus{{display:block;width:100%;aspect-ratio:16/9;object-fit:contain;background:#02070b;border-radius:13px;border:1px solid var(--line)}}
.meta{{display:flex;justify-content:space-between;gap:12px;margin:10px 0;color:var(--muted)}}.answers{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}}
.answer.selected{{outline:3px solid var(--cyan)}}.confidence{{display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center;margin:18px 0}}
.warning{{padding:12px;border-left:4px solid #e3a52c;background:#302510}}progress{{width:100%;height:12px}}
</style></head><body><main>
<section id="start"><h1>Étude visuelle aveugle</h1>
<p>Vous évaluerez trois candidats anonymes. Aucun nom de direction artistique n’est communiqué. Chaque stimulus apparaît pendant cinq secondes, puis disparaît avant la réponse.</p>
<p class="warning">Effectuez la session en plein écran, sans capture ni retour arrière, sur le même appareil du début à la fin.</p>
<label>Identifiant attribué<select id="participantId"><option value="">Choisir…</option>{''.join(f'<option>{html.escape(pid)}</option>' for pid in payload["assignments"])}</select></label>
<label>Classe d’appareil<select id="deviceClass"><option value="mobile">Mobile</option><option value="tablet">Tablette</option><option value="desktop">Ordinateur</option></select></label>
<button class="primary" id="begin">Commencer</button></section>
<section id="trial" class="hidden"><progress id="progress" max="30"></progress><div class="meta"><span id="candidate"></span><span id="counter"></span></div>
<h2 id="prompt"></h2><img id="stimulus" alt="Stimulus visuel"><p id="countdown" class="muted"></p>
<div id="answerPanel" class="hidden"><div class="answers" id="answers"></div>
<div class="confidence"><label>Confiance : <input id="confidence" type="range" min="0" max="1" step="0.1" value="0.5"></label><strong id="confidenceValue">0,5</strong></div>
<button class="primary" id="next" disabled>Valider la réponse</button></div></section>
<section id="exit" class="hidden"><h2>Trois dernières questions</h2>
<label>Candidat le plus mémorable<select id="memorable"><option>A</option><option>B</option><option>C</option></select></label>
<label>Candidat le plus facile à comprendre<select id="easiest"><option>A</option><option>B</option><option>C</option></select></label>
<label>Quel signal visuel a surtout guidé vos réponses ?<textarea id="cue" rows="4" minlength="3"></textarea></label>
<button class="primary" id="download">Terminer et enregistrer la session</button></section>
</main><script>
const STUDY={data}; let assignment,participantId,deviceClass,startedAt,index=0,responses=[],selected=null,answerShownAt=0;
const $=id=>document.getElementById(id); const iso=()=>new Date().toISOString();
function show(id){{for(const section of document.querySelectorAll('main>section'))section.classList.add('hidden');$(id).classList.remove('hidden')}}
$('begin').onclick=()=>{{participantId=$('participantId').value;if(!participantId)return alert('Choisissez votre identifiant.');deviceClass=$('deviceClass').value;assignment=STUDY.assignments[participantId];startedAt=iso();show('trial');renderTrial()}};
function renderTrial(){{selected=null;$('next').disabled=true;$('answerPanel').classList.add('hidden');$('stimulus').classList.remove('hidden');
const t=assignment.trials[index];$('progress').value=index;$('counter').textContent=`${{index+1}} / ${{assignment.trials.length}}`;$('candidate').textContent=`Candidat ${{t.blindLabel}}`;
$('prompt').textContent=t.prompt;$('stimulus').src=t.image;$('countdown').textContent='Observation : 5,0 s';let left=STUDY.exposureMs;
const timer=setInterval(()=>{{left-=100;$('countdown').textContent=`Observation : ${{Math.max(left,0)/1000}} s`.replace('.',',');if(left<=0){{clearInterval(timer);$('stimulus').classList.add('hidden');$('countdown').textContent='Stimulus masqué : répondez sans revenir en arrière.';showAnswers(t)}}}},100)}}
function showAnswers(t){{const box=$('answers');box.innerHTML='';for(const option of t.options){{const b=document.createElement('button');b.className='answer';b.textContent=option.label;b.onclick=()=>{{selected=option.id;for(const x of box.children)x.classList.remove('selected');b.classList.add('selected');$('next').disabled=false}};box.appendChild(b)}}$('answerPanel').classList.remove('hidden');answerShownAt=performance.now()}}
$('confidence').oninput=()=>$('confidenceValue').textContent=Number($('confidence').value).toFixed(1).replace('.',',');
$('next').onclick=()=>{{const t=assignment.trials[index];responses.push({{trialIndex:index,blindLabel:t.blindLabel,taskId:t.taskId,answer:selected,confidence:Number($('confidence').value),exposureMs:STUDY.exposureMs,responseTimeMs:Math.max(50,Math.round(performance.now()-answerShownAt))}});index++;if(index>=assignment.trials.length)show('exit');else renderTrial()}};
$('download').onclick=()=>{{if($('cue').value.trim().length<3)return alert('Décrivez brièvement le signal visuel décisif.');const session={{$schema:'https://roblox-top1.local/schemas/participant-session.schema.json',schemaVersion:'1.0.0',studyId:STUDY.studyId,publicPackageId:STUDY.publicPackageId,participantId,deviceClass,startedAt,completedAt:iso(),responses,exitAnswers:{{mostMemorable:$('memorable').value,easiestToUnderstand:$('easiest').value,decisiveCue:$('cue').value.trim()}}}};download(session,`participant-${{participantId}}.json`);$('download').disabled=true;$('download').textContent='Session enregistrée'}};
function download(value,name){{const blob=new Blob([JSON.stringify(value,null,2)+'\\n'],{{type:'application/json'}}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}}
</script></body></html>"""


def _expert_html(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    options = "".join(f"<option>{html.escape(rid)}</option>" for rid in payload["assignments"])
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Étude visuelle — experts</title><style>
:root{{color-scheme:dark;--bg:#071019;--panel:#111d29;--line:#294055;--text:#eef7fc;--muted:#99adbd;--cyan:#54dbea}}
*{{box-sizing:border-box}}body{{margin:0;background:#071019;color:var(--text);font:15px/1.45 Segoe UI,sans-serif}}main{{width:min(1250px,100%);margin:auto;padding:24px}}
section{{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:24px;margin-bottom:18px}}select,input,textarea,button{{font:inherit}}select,input,textarea{{padding:10px;border:1px solid var(--line);border-radius:9px;background:#08131d;color:var(--text)}}
button{{padding:12px 18px;border:1px solid #3b647b;border-radius:11px;background:#12677a;color:white;cursor:pointer}}.hidden{{display:none!important}}.muted{{color:var(--muted)}}
.gallery{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:10px}}.gallery img{{width:100%;aspect-ratio:16/9;object-fit:contain;background:#02070b;border-radius:10px}}
.rating{{display:grid;grid-template-columns:minmax(260px,1fr) 110px 180px;gap:12px;align-items:center;padding:12px 0;border-bottom:1px solid var(--line)}}label{{display:grid;gap:6px;margin:12px 0}}
@media(max-width:700px){{.rating{{grid-template-columns:1fr}}}}</style></head><body><main>
<section id="start"><h1>Revue experte aveugle</h1><p>Évaluez uniquement les candidats A, B et C. Ne cherchez pas à identifier leur provenance.</p>
<label>Identifiant attribué<select id="reviewerId"><option value="">Choisir…</option>{options}</select></label><button id="begin">Commencer</button></section>
<div id="review" class="hidden"><section><h1 id="title"></h1><p id="role" class="muted"></p><div class="gallery" id="gallery"></div></section>
<section><h2>Notation</h2><div id="ratings"></div><label>Observations sur ce candidat<textarea id="notes" rows="5"></textarea></label><button id="next">Valider ce candidat</button></section></div>
<section id="done" class="hidden"><h2>Revue terminée</h2><button id="download">Enregistrer la session experte</button></section>
</main><script>
const STUDY={data};const $=id=>document.getElementById(id);let reviewerId,assignment,index=0,startedAt,ratings=[],notes={{A:'',B:'',C:''}};
const iso=()=>new Date().toISOString();function showStart(id){{$('start').classList.add('hidden');$('review').classList.add('hidden');$('done').classList.add('hidden');$(id).classList.remove('hidden')}}
$('begin').onclick=()=>{{reviewerId=$('reviewerId').value;if(!reviewerId)return alert('Choisissez votre identifiant.');assignment=STUDY.assignments[reviewerId];startedAt=iso();showStart('review');render()}};
function render(){{const label=assignment.labelOrder[index];$('title').textContent=`Candidat ${{label}}`;$('role').textContent=assignment.reviewerRole==='function_silhouette'?'Focalisation principale : fonction, silhouette et états.':'Focalisation principale : cohérence, identité et capacité de production.';
const gallery=$('gallery');gallery.innerHTML='';for(const item of STUDY.expertImages.filter(x=>x.blindLabel===label)){{const img=document.createElement('img');img.src=item.path;img.alt=`Candidat ${{label}} — vue ${{item.kind}}`;gallery.appendChild(img)}}
const box=$('ratings');box.innerHTML='';for(const dim of STUDY.dimensions){{const row=document.createElement('div');row.className='rating';row.innerHTML=`<div><strong>${{dim.label}}</strong><div class="muted">${{dim.question}}</div></div><select data-score="${{dim.id}}"><option>1</option><option>2</option><option>3</option><option selected>4</option><option>5</option></select><label>Confiance <input data-confidence="${{dim.id}}" type="range" min="0" max="1" step="0.1" value="0.7"></label>`;box.appendChild(row)}}$('notes').value=notes[label]}}
$('next').onclick=()=>{{const label=assignment.labelOrder[index];for(const dim of STUDY.dimensions){{ratings.push({{blindLabel:label,dimensionId:dim.id,score:Number(document.querySelector(`[data-score="${{dim.id}}"]`).value),confidence:Number(document.querySelector(`[data-confidence="${{dim.id}}"]`).value)}})}}notes[label]=$('notes').value.trim();index++;if(index>=assignment.labelOrder.length)showStart('done');else render()}};
$('download').onclick=()=>{{const session={{$schema:'https://roblox-top1.local/schemas/expert-session.schema.json',schemaVersion:'1.0.0',studyId:STUDY.studyId,publicPackageId:STUDY.publicPackageId,reviewerId,reviewerRole:assignment.reviewerRole,startedAt,completedAt:iso(),ratings,candidateNotes:notes}};const blob=new Blob([JSON.stringify(session,null,2)+'\\n'],{{type:'application/json'}}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`expert-${{reviewerId}}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);$('download').disabled=true;$('download').textContent='Session enregistrée'}};
</script></body></html>"""


def _zip_tree(source: Path, output: Path) -> None:
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())


def _gate_evidence(output: Path, label: str, territory: str, evidence_root: Path) -> dict[str, Any]:
    visual_report = evidence_root / "evidence/blender/visual-quality-report.json"
    blender_report = evidence_root / "evidence/blender/blender-verification-report.json"
    studio_report = evidence_root / f"evidence/studio/{territory}/studio-report.json"
    provenance = evidence_root / "art/references/provenance.json"
    cvd_report = evidence_root / "evidence/blender/cvd-report.json"
    physical_report = evidence_root / "evidence/mobile/physical/performance-report.json"

    visual = load_json(visual_report)
    blender = load_json(blender_report)
    studio = load_json(studio_report)
    provenance_value = load_json(provenance)
    territory_visual = next(item for item in visual["territories"] if item["territoryId"] == territory)
    territory_blender = next(item for item in blender["territories"] if item["territoryId"] == territory)

    evaluations = {
        "not_color_only": (
            visual["status"] == "PASS"
            and all(item["pass"] for item in territory_visual["stateComparisons"]),
            "State silhouette differences pass the current visual-quality thresholds.",
            [visual_report],
        ),
        "grayscale_and_cvd": (
            cvd_report.is_file() and load_json(cvd_report).get("status") == "PASS",
            "No executed grayscale/CVD evidence report exists yet."
            if not cvd_report.is_file()
            else "Executed grayscale/CVD report status was evaluated.",
            [cvd_report] if cvd_report.is_file() else [evidence_root / "art/palettes/semantic-palette.json"],
        ),
        "materials_four_lights": (
            studio["status"] == "PASS"
            and len(studio["lightingChecks"]) == 4
            and all(item["ok"] and item["evidenceFresh"] for item in studio["lightingChecks"].values()),
            "Studio report contains four fresh passing lighting profiles.",
            [studio_report],
        ),
        "group_30_visual": (
            studio["status"] == "PASS"
            and all(
                item["pass"]
                for key, item in studio["reuseChecks"].items()
                if key.endswith("_30")
            ),
            "Studio 30-copy reuse groups were evaluated.",
            [studio_report],
        ),
        "provenance_complete": (
            provenance_value["humanApproval"]["status"] == "APPROVED",
            "Reference provenance is structurally complete but human approval is still pending.",
            [provenance],
        ),
        "deterministic_rules": (
            blender["status"] == "PASS" and territory_blender["status"] == "PASS",
            "Two-run Blender determinism report passes for this candidate.",
            [blender_report],
        ),
        "roblox_technical_budgets": (
            blender["status"] == "PASS"
            and territory_blender["status"] == "PASS"
            and studio["status"] == "PASS",
            "Blender budgets and Studio import checks pass.",
            [blender_report, studio_report],
        ),
        "studio_golden_scene": (
            studio["status"] == "PASS",
            "Hash-bound Studio Golden Scene report status.",
            [studio_report],
        ),
        "real_device_mobile": (
            physical_report.is_file() and load_json(physical_report).get("status") == "PASS",
            "No schema-valid physical low-tier device report exists yet."
            if not physical_report.is_file()
            else "Physical-device report status was evaluated.",
            [physical_report] if physical_report.is_file() else [],
        ),
    }

    result: dict[str, Any] = {}
    for gate_id, (passed, reason, sources) in evaluations.items():
        bound_sources = []
        for source_index, source in enumerate(sources, start=1):
            if not source.is_file():
                continue
            suffix = source.suffix.lower() or ".bin"
            bound_path = (
                output
                / "operator/source-evidence"
                / f"{label}__{gate_id}__S{source_index:02d}{suffix}"
            )
            bound_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, bound_path)
            bound_sources.append({"path": rel(bound_path), "sha256": sha256_file(bound_path)})
        wrapper = {
            "schemaVersion": "1.0.0",
            "studyId": STUDY_ID,
            "blindLabel": label,
            "gateId": gate_id,
            "pass": bool(passed),
            "reason": reason,
            "sources": bound_sources,
        }
        wrapper_path = output / "operator/technical-evidence" / f"{label}__{gate_id}.json"
        write_json(wrapper_path, wrapper)
        result[gate_id] = {
            "pass": bool(passed),
            "evidencePath": rel(wrapper_path),
            "sha256": sha256_file(wrapper_path),
        }
    return result


def _privacy_scan(public_root: Path) -> list[str]:
    issues: list[str] = []
    forbidden = tuple(value.lower() for value in TERRITORIES)
    for path in public_root.rglob("*"):
        relative = path.relative_to(public_root).as_posix().lower()
        if any(value in relative for value in forbidden):
            issues.append(relative)
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".zip"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        for value in forbidden:
            if value in text:
                issues.append(f"{relative}:{value}")
    return sorted(set(issues))


def prepare(output: Path, evidence_root: Path) -> dict[str, Any]:
    output = _under_root(output)
    evidence_root = evidence_root.resolve()
    if output.exists():
        shutil.rmtree(output)
    public_root = output / "public"
    participant_root = public_root / "participant"
    expert_root = public_root / "expert"
    for path in (
        participant_root / "stimuli",
        expert_root / "images",
        output / "operator/technical-evidence",
        output / "private",
        output / "sessions/participants",
        output / "sessions/experts",
    ):
        path.mkdir(parents=True, exist_ok=True)

    territories = list(TERRITORIES)
    secrets.SystemRandom().shuffle(territories)
    mapping = dict(zip(LABELS, territories, strict=True))
    salt_id = secrets.token_hex(16)
    generated_at = _utc_now()

    stimuli: list[dict[str, Any]] = []
    answer_key: dict[str, str] = {}
    for label in LABELS:
        territory = mapping[label]
        for task_index, task in enumerate(TASKS, start=1):
            source = _image_source(evidence_root, territory, task)
            relative = Path("stimuli") / label / f"T{task_index:02d}.png"
            destination = participant_root / relative
            _reencode_image(source, destination)
            with Image.open(destination) as encoded:
                width, height = encoded.size
            stimuli.append(
                {
                    "blindLabel": label,
                    "taskId": task["taskId"],
                    "path": relative.as_posix(),
                    "sha256": sha256_file(destination),
                    "width": width,
                    "height": height,
                }
            )
            answer_key[task["taskId"]] = task["answer"]

    rubric = load_json(ROOT / "art/qa/visual-rubric.json")
    protocol = load_json(ROOT / "art/qa/task-protocol.json")

    expert_images: list[dict[str, Any]] = []
    for label in LABELS:
        territory = mapping[label]
        index = 1
        for lighting in (
            "Lighting_Gameplay_Default",
            "Lighting_HighContrast",
            "Lighting_Adverse_Night",
            "Lighting_Neutral_QA",
        ):
            source = evidence_root / f"evidence/studio/captures/{territory}__{lighting}.jpg"
            relative = Path("images") / label / f"E{index:02d}.png"
            _copy_expert_image(source, expert_root / relative)
            expert_images.append(
                {
                    "blindLabel": label,
                    "kind": f"studio_{index:02d}",
                    "path": relative.as_posix(),
                    "sha256": sha256_file(expert_root / relative),
                }
            )
            index += 1
        quality_root = evidence_root / f"evidence/blender/visual-quality-artifacts/{territory}"
        for source in sorted(quality_root.glob("*.png")):
            relative = Path("images") / label / f"E{index:02d}.png"
            _copy_expert_image(source, expert_root / relative)
            expert_images.append(
                {
                    "blindLabel": label,
                    "kind": f"silhouette_state_{index:02d}",
                    "path": relative.as_posix(),
                    "sha256": sha256_file(expert_root / relative),
                }
            )
            index += 1
        transfer_root = evidence_root / f"evidence/transfer/turret-fast-v1/{territory}"
        transfer_sources = [
            transfer_root / "hero/intact.png",
            transfer_root / "hero/damaged.png",
            transfer_root / "hero/critical.png",
            transfer_root / "far-mobile/intact.png",
            transfer_root / "far-mobile/damaged.png",
            transfer_root / "far-mobile/critical.png",
            transfer_root / "orientation/front_silhouette.png",
            transfer_root / "orientation/back_silhouette.png",
            transfer_root / "portrait-mobile/intact.png",
            transfer_root / "portrait-mobile/damaged.png",
            transfer_root / "portrait-mobile/critical.png",
        ]
        for source in transfer_sources:
            relative = Path("images") / label / f"E{index:02d}.png"
            _copy_expert_image(source, expert_root / relative)
            expert_images.append(
                {
                    "blindLabel": label,
                    "kind": f"transfer_{index:02d}",
                    "path": relative.as_posix(),
                    "sha256": sha256_file(expert_root / relative),
                }
            )
            index += 1

    public_package_id = _public_package_id(stimuli, expert_images, protocol, rubric)
    participant_assignments = _participant_assignments(public_package_id, stimuli)
    dimensions = [
        {
            "id": dim_id,
            "label": DIMENSION_LABELS.get(dim_id, dim_id),
            "question": value["question"],
        }
        for dim_id, value in rubric["dimensions"].items()
    ]
    participant_payload = {
        "studyId": STUDY_ID,
        "publicPackageId": public_package_id,
        "exposureMs": EXPOSURE_MS,
        "assignments": participant_assignments,
    }
    expert_payload = {
        "studyId": STUDY_ID,
        "publicPackageId": public_package_id,
        "assignments": _expert_assignments(public_package_id),
        "dimensions": dimensions,
        "expertImages": expert_images,
    }
    (participant_root / "index.html").write_text(
        _participant_html(participant_payload), encoding="utf-8", newline="\n"
    )
    (expert_root / "index.html").write_text(
        _expert_html(expert_payload), encoding="utf-8", newline="\n"
    )

    public_manifest = {
        "schemaVersion": "1.0.0",
        "studyId": STUDY_ID,
        "publicPackageId": public_package_id,
        "generatedAt": generated_at,
        "candidateLabels": list(LABELS),
        "exposureMs": EXPOSURE_MS,
        "participantSlots": list(participant_assignments),
        "expertSlots": list(expert_payload["assignments"]),
        "stimuli": stimuli,
        "expertImages": expert_images,
        "protocolSha256": sha256_file(ROOT / "art/qa/task-protocol.json"),
        "rubricSha256": sha256_file(ROOT / "art/qa/visual-rubric.json"),
    }
    write_json(public_root / "study-public-manifest.json", public_manifest)
    write_json(
        participant_root / "participant-manifest.json",
        {
            "schemaVersion": "1.0.0",
            "studyId": STUDY_ID,
            "publicPackageId": public_package_id,
            "exposureMs": EXPOSURE_MS,
            "stimuli": stimuli,
        },
    )
    write_json(
        expert_root / "expert-manifest.json",
        {
            "schemaVersion": "1.0.0",
            "studyId": STUDY_ID,
            "publicPackageId": public_package_id,
            "dimensions": dimensions,
            "images": expert_images,
        },
    )
    write_json(output / "operator/answer-key.json", {"studyId": STUDY_ID, "answers": answer_key})
    technical_by_label = {
        label: _gate_evidence(output, label, mapping[label], evidence_root) for label in LABELS
    }
    write_json(
        output / "operator/reviewer-submissions.draft.json",
        {
            "$schema": "https://roblox-top1.local/schemas/reviewer-submissions.schema.json",
            "schemaVersion": "2.0.0",
            "studyId": STUDY_ID,
            "status": "DRAFT",
            "sealedAt": None,
            "participants": [],
            "expertReviews": [],
            "technicalEvidenceByBlindLabel": technical_by_label,
        },
    )
    write_json(
        output / "private/blind-map.json",
        {
            "$schema": "https://roblox-top1.local/schemas/blind-map.schema.json",
            "schemaVersion": "2.0.0",
            "studyId": STUDY_ID,
            "generatedAt": generated_at,
            "mapping": mapping,
            "sealedSubmissionsSha256": "0" * 64,
            "saltId": salt_id,
        },
    )
    shutil.copy2(
        ROOT / "art/decision/selection-decision.template.json",
        output / "operator/selection-decision.template.json",
    )
    operator_readme = """# Opération de l’étude aveugle

1. Ne partagez jamais `private/` ni `operator/`.
2. Distribuez `participant-kit.zip` aux participants P01–P12.
3. Distribuez `expert-kit.zip` aux experts R01–R04.
4. Placez les fichiers téléchargés dans `sessions/participants/` et
   `sessions/experts/`.
5. Exécutez `art-direction seal-study -StudyRoot <ce dossier>`.
6. Exécutez ensuite `art-direction score` avec les fichiers scellés.

La collecte humaine peut commencer. La sélection finale reste inéligible tant
que les preuves CVD, la provenance approuvée et le mobile physique ne passent
pas leurs gates techniques.
"""
    (output / "operator/README.md").write_text(operator_readme, encoding="utf-8", newline="\n")
    public_readme = """# Kit anonyme

Ce dossier ne révèle aucune direction artistique réelle.

- `participant/index.html` : tâche chronométrée pour P01–P12.
- `expert/index.html` : grille experte pour R01–R04.

Utiliser un identifiant une seule fois et renvoyer uniquement le fichier JSON
téléchargé à la fin. Ne pas rechercher l’identité des candidats.
"""
    (public_root / "README.md").write_text(public_readme, encoding="utf-8", newline="\n")

    participant_zip_root = output / "_participant_zip"
    expert_zip_root = output / "_expert_zip"
    shutil.copytree(participant_root, participant_zip_root / "participant")
    shutil.copy2(public_root / "README.md", participant_zip_root / "README.md")
    shutil.copytree(expert_root, expert_zip_root / "expert")
    shutil.copy2(public_root / "README.md", expert_zip_root / "README.md")
    _zip_tree(participant_zip_root, output / "participant-kit.zip")
    _zip_tree(expert_zip_root, output / "expert-kit.zip")
    shutil.rmtree(participant_zip_root)
    shutil.rmtree(expert_zip_root)

    privacy_issues = _privacy_scan(public_root)
    for archive_path in (output / "participant-kit.zip", output / "expert-kit.zip"):
        with zipfile.ZipFile(archive_path) as archive:
            for name in archive.namelist():
                lower = name.lower()
                if any(value in lower for value in TERRITORIES):
                    privacy_issues.append(f"{archive_path.name}:{name}")
                if Path(name).suffix.lower() in {".png", ".jpg", ".jpeg"}:
                    continue
                text = archive.read(name).decode("utf-8", errors="ignore").lower()
                for value in TERRITORIES:
                    if value in text:
                        privacy_issues.append(f"{archive_path.name}:{name}:{value}")
    if privacy_issues:
        raise RuntimeError(f"Public blind-package privacy leak: {sorted(set(privacy_issues))}")

    external_blockers = []
    flat_gates = [
        (label, gate_id, gate)
        for label, gates in technical_by_label.items()
        for gate_id, gate in gates.items()
    ]
    for gate_id in ("grayscale_and_cvd", "provenance_complete", "real_device_mobile"):
        if not all(gate["pass"] for _, observed, gate in flat_gates if observed == gate_id):
            external_blockers.append(gate_id)

    artifacts = []
    for kind, path in (
        ("participant_kit", output / "participant-kit.zip"),
        ("expert_kit", output / "expert-kit.zip"),
        ("public_manifest", public_root / "study-public-manifest.json"),
        ("participant_interface", participant_root / "index.html"),
        ("expert_interface", expert_root / "index.html"),
        ("answer_key", output / "operator/answer-key.json"),
        ("draft_submissions", output / "operator/reviewer-submissions.draft.json"),
        ("private_blind_map", output / "private/blind-map.json"),
    ):
        artifacts.append({"kind": kind, "path": rel(path), "sha256": sha256_file(path)})
    manifest = {
        "$schema": "https://roblox-top1.local/schemas/blind-study-manifest.schema.json",
        "schemaVersion": "1.0.0",
        "studyId": STUDY_ID,
        "status": "READY_FOR_HUMAN_COLLECTION",
        "generatedAt": generated_at,
        "publicPackageId": public_package_id,
        "privacyCheck": {"status": "PASS", "forbiddenIdentifiersFound": []},
        "targets": {
            "minimumParticipants": rubric["reviewPolicy"]["minimumTaskParticipants"],
            "targetParticipants": TARGET_PARTICIPANTS,
            "minimumExperts": rubric["reviewPolicy"]["minimumExpertReviewers"],
            "targetExperts": TARGET_EXPERTS,
            "trialsPerParticipant": len(TASKS) * len(LABELS),
            "ratingsPerExpert": len(dimensions) * len(LABELS),
        },
        "artifacts": artifacts,
        "externalBlockers": external_blockers,
    }
    write_json(output / "study-manifest.json", manifest)
    errors = validate_with_schema(manifest, ROOT / "schemas/blind-study-manifest.schema.json")
    if errors:
        raise RuntimeError("; ".join(errors))
    return manifest


def _refresh_technical_evidence(study_root: Path, evidence_root: Path) -> dict[str, Any]:
    blind_map = load_json(study_root / "private/blind-map.json")
    mapping = blind_map["mapping"]
    technical_by_label = {
        label: _gate_evidence(study_root, label, mapping[label], evidence_root)
        for label in LABELS
    }
    draft_path = study_root / "operator/reviewer-submissions.draft.json"
    draft = load_json(draft_path)
    draft["technicalEvidenceByBlindLabel"] = technical_by_label
    write_json(draft_path, draft)

    manifest_path = study_root / "study-manifest.json"
    manifest = load_json(manifest_path)
    manifest["externalBlockers"] = sorted(
        {
            gate_id
            for gates in technical_by_label.values()
            for gate_id, gate in gates.items()
            if not gate["pass"]
        }
    )
    manifest["artifacts"] = [
        {
            **artifact,
            "sha256": sha256_file(draft_path),
        }
        if artifact["kind"] == "draft_submissions"
        else artifact
        for artifact in manifest["artifacts"]
    ]
    write_json(manifest_path, manifest)
    return manifest


def seal(study_root: Path, evidence_root: Path) -> Path:
    study_root = _under_root(study_root)
    evidence_root = evidence_root.resolve()
    manifest = _refresh_technical_evidence(study_root, evidence_root)
    public = load_json(study_root / "public/study-public-manifest.json")
    answers = load_json(study_root / "operator/answer-key.json")["answers"]
    draft = load_json(study_root / "operator/reviewer-submissions.draft.json")
    participant_files = sorted((study_root / "sessions/participants").glob("*.json"))
    expert_files = sorted((study_root / "sessions/experts").glob("*.json"))
    rubric = load_json(ROOT / "art/qa/visual-rubric.json")

    issues: list[str] = []
    for artifact in manifest["artifacts"]:
        artifact_path = ROOT / artifact["path"]
        if not artifact_path.is_file():
            issues.append(f"Missing study artifact: {artifact['path']}")
        elif sha256_file(artifact_path) != artifact["sha256"]:
            issues.append(f"Study artifact hash mismatch: {artifact['path']}")
    for item in public["stimuli"]:
        path = study_root / "public/participant" / item["path"]
        if not path.is_file() or sha256_file(path) != item["sha256"]:
            issues.append(f"Participant stimulus mismatch: {item['blindLabel']}/{item['taskId']}")
    for item in public["expertImages"]:
        path = study_root / "public/expert" / item["path"]
        if not path.is_file() or sha256_file(path) != item["sha256"]:
            issues.append(f"Expert image mismatch: {item['blindLabel']}/{item['kind']}")
    expected_package_id = _public_package_id(
        public["stimuli"], public["expertImages"], load_json(ROOT / "art/qa/task-protocol.json"), rubric
    )
    if expected_package_id != manifest["publicPackageId"]:
        issues.append("Public package digest no longer matches its visual and protocol inputs")
    privacy_issues = _privacy_scan(study_root / "public")
    if privacy_issues:
        issues.append(f"Public candidate identity leak: {privacy_issues}")

    participants = []
    for path in participant_files:
        value = load_json(path)
        issues += [f"{path.name}: {item}" for item in validate_with_schema(value, ROOT / "schemas/participant-session.schema.json")]
        if value.get("publicPackageId") != manifest["publicPackageId"]:
            issues.append(f"{path.name}: publicPackageId mismatch")
        expected = {(label, task["taskId"]) for label in LABELS for task in TASKS}
        observed = {(item["blindLabel"], item["taskId"]) for item in value.get("responses", [])}
        if observed != expected:
            issues.append(f"{path.name}: incomplete or duplicate trial matrix")
        participants.append(
            {
                "participantId": value.get("participantId"),
                "deviceClass": value.get("deviceClass"),
                "responses": [
                    {
                        "blindLabel": item["blindLabel"],
                        "taskId": item["taskId"],
                        "correct": item["answer"] == answers[item["taskId"]],
                        "confidence": item["confidence"],
                        "responseTimeMs": item["responseTimeMs"],
                    }
                    for item in value.get("responses", [])
                ],
            }
        )
    experts = []
    for path in expert_files:
        value = load_json(path)
        issues += [f"{path.name}: {item}" for item in validate_with_schema(value, ROOT / "schemas/expert-session.schema.json")]
        if value.get("publicPackageId") != manifest["publicPackageId"]:
            issues.append(f"{path.name}: publicPackageId mismatch")
        experts.append({"reviewerId": value.get("reviewerId"), "ratings": value.get("ratings", [])})

    participant_ids = [item["participantId"] for item in participants]
    reviewer_ids = [item["reviewerId"] for item in experts]
    if len(participant_ids) != len(set(participant_ids)):
        issues.append("Duplicate participant IDs")
    if len(reviewer_ids) != len(set(reviewer_ids)):
        issues.append("Duplicate expert reviewer IDs")
    if len(participants) < rubric["reviewPolicy"]["minimumTaskParticipants"]:
        issues.append(
            f"Need at least {rubric['reviewPolicy']['minimumTaskParticipants']} participant sessions"
        )
    if len(experts) < rubric["reviewPolicy"]["minimumExpertReviewers"]:
        issues.append(f"Need at least {rubric['reviewPolicy']['minimumExpertReviewers']} expert sessions")
    if public["publicPackageId"] != manifest["publicPackageId"]:
        issues.append("Public manifest no longer matches the study manifest")
    if issues:
        raise RuntimeError("\n".join(issues))

    sealed = {
        "$schema": "https://roblox-top1.local/schemas/reviewer-submissions.schema.json",
        "schemaVersion": "2.0.0",
        "studyId": STUDY_ID,
        "status": "SEALED",
        "sealedAt": _utc_now(),
        "participants": participants,
        "expertReviews": experts,
        "technicalEvidenceByBlindLabel": draft["technicalEvidenceByBlindLabel"],
    }
    output = study_root / "operator/reviewer-submissions.sealed.json"
    write_json(output, sealed)
    errors = validate_with_schema(sealed, ROOT / "schemas/reviewer-submissions.schema.json")
    if errors:
        output.unlink(missing_ok=True)
        raise RuntimeError("; ".join(errors))

    blind_map_path = study_root / "private/blind-map.json"
    blind_map = load_json(blind_map_path)
    blind_map["sealedSubmissionsSha256"] = sha256_file(output)
    write_json(blind_map_path, blind_map)
    errors = validate_with_schema(blind_map, ROOT / "schemas/blind-map.schema.json")
    if errors:
        raise RuntimeError("; ".join(errors))

    raw_index = {
        "schemaVersion": "1.0.0",
        "studyId": STUDY_ID,
        "sealedAt": sealed["sealedAt"],
        "participantSessions": [
            {"path": rel(path), "sha256": sha256_file(path)} for path in participant_files
        ],
        "expertSessions": [
            {"path": rel(path), "sha256": sha256_file(path)} for path in expert_files
        ],
    }
    raw_index_path = study_root / "operator/raw-session-index.json"
    write_json(raw_index_path, raw_index)
    manifest["status"] = "SEALED"
    updated_artifacts = []
    for artifact in manifest["artifacts"]:
        path = ROOT / artifact["path"]
        if artifact["kind"] == "private_blind_map":
            artifact = {**artifact, "sha256": sha256_file(blind_map_path)}
        updated_artifacts.append(artifact)
    updated_artifacts.extend(
        [
            {"kind": "sealed_submissions", "path": rel(output), "sha256": sha256_file(output)},
            {
                "kind": "raw_session_index",
                "path": rel(raw_index_path),
                "sha256": sha256_file(raw_index_path),
            },
        ]
    )
    manifest["artifacts"] = updated_artifacts
    write_json(study_root / "study-manifest.json", manifest)
    errors = validate_with_schema(
        manifest, ROOT / "schemas/blind-study-manifest.schema.json"
    )
    if errors:
        raise RuntimeError("; ".join(errors))
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare or seal the blinded art-direction study.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare_parser = subparsers.add_parser("prepare")
    prepare_parser.add_argument(
        "--output", type=Path, default=ROOT / "evidence/human/art-direction-study-v1"
    )
    prepare_parser.add_argument("--evidence-root", type=Path, default=ROOT)
    seal_parser = subparsers.add_parser("seal")
    seal_parser.add_argument(
        "--study-root", type=Path, default=ROOT / "evidence/human/art-direction-study-v1"
    )
    seal_parser.add_argument("--evidence-root", type=Path, default=ROOT)
    args = parser.parse_args()
    if args.command == "prepare":
        manifest = prepare(args.output, args.evidence_root)
        print(
            f"[PASS] Blind study ready for human collection: {args.output.resolve()} | "
            f"public package {manifest['publicPackageId']} | "
            f"external gates still blocked: {', '.join(manifest['externalBlockers']) or 'none'}"
        )
        return 0
    output = seal(args.study_root, args.evidence_root)
    print(f"[PASS] Human submissions sealed: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
