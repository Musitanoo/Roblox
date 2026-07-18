# Salvaged Frontier Documentation Hardening — ExecPlan

## Outcome

Transformer le corpus artistique existant en une documentation cohérente,
navigable et exploitable sans interprétation implicite. Le résultat doit :

- figer `salvaged-frontier` comme constitution créative sélectionnée ;
- décrire précisément les six objets canoniques et tous leurs états applicables ;
- séparer les états d'intégrité, d'exploitation, d'action, d'interaction,
  d'affiliation et les événements transitoires ;
- fermer les contrats Blender, export, Roblox Studio, mobile, performance,
  accessibilité, preuve et gouvernance ;
- supprimer les contradictions entre preuves historiques et statut courant ;
- conserver `productionApproved=false` tant que les preuves Studio, appareil
  physique et approbations humaines requises ne sont pas acquises.

Ce plan n'autorise aucune modification gameplay, aucune publication Cloud,
aucune mutation Studio et aucun verrouillage artificiel des canons.

## Baseline audit — 2026-07-16

- Le dépôt est déjà modifié et contient de nombreux fichiers non suivis ou
  modifiés appartenant au travail de l'utilisateur ; ils doivent être préservés.
- La source de vérité machine est `tools/roblox-art-bible-sota-v3/STATUS.json`
  et les contrats JSON sous `art/`.
- La constitution créative Salvaged Frontier est sélectionnée et verrouillée
  par autorité founder, mais les six canons d'objet restent `CANDIDATE` avec
  approbation `PENDING`.
- Le catalogue couvre 18 canons et 48 variantes applicables. Pour le territoire
  sélectionné, les cinq assets de calibration couvrent 13 variantes et la
  tourelle de transfert en couvre 3, soit 16 variantes.
- Les documents Markdown contiennent des contradictions de temporalité :
  certaines preuves v3.7 Studio/Cloud sont racontées comme actuelles alors
  qu'elles précèdent la constitution sélectionnée.
- Les pages existantes ne définissent pas une ontologie d'états orthogonale et
  ne fournissent pas un registre humain compact des six objets.
- Le contrat d'axes ne couvre pas les matrices, orientations, normales,
  tangentes et le risque de double conversion.
- Le protocole mobile nomme un preset Studio comme s'il était une identité
  durable alors que la preuve doit enregistrer les valeurs réellement lues.

## Authority

1. Demande explicite du founder.
2. `AGENTS.md` et GDD acceptés.
3. Constitution sélectionnée et contrats JSON sous
   `tools/roblox-art-bible-sota-v3/art/`.
4. `STATUS.json` pour le statut courant.
5. Markdown comme projection humaine, jamais comme moyen de surclasser une
   preuve absente.

En cas de conflit, les JSON et preuves horodatées restent autoritaires pour les
valeurs et statuts exécutables. Le Markdown doit être corrigé.

## Acceptance criteria

1. Un index unique permet de trouver la bible, le statut, l'ontologie, les six
   objets, les contrats techniques et les preuves.
2. La DA définit thèse, principes, ratios, palette, matériaux, architecture,
   biomes, buildables, objectifs, ennemis, avatars, VFX, UI, caméra, répétition,
   génération et interdictions, sans confondre identité créative et production.
3. Chaque objet documente fonction, lecture instantanée, dimensions, pivot,
   composants, vues, matériaux, zones sémantiques, états applicables,
   transitions, invariants, variations et interdictions.
4. La matrice exacte est explicite : barricade 3, objective core 3, enemy 3,
   floor 2, damage effect 2, turret 3. Aucun produit cartésien artificiel.
5. `repair`, `firing`, `selected`, `hostile` et `critical` ne sont plus
   mélangés dans un enum unique.
6. Le contrat Blender/Roblox couvre points, directions, orientations,
   transformées, normales, tangentes, unités, pivots et validation de réimport.
7. Les budgets mesh, texture, collision, transparence, particules, instancing,
   mobile et accessibilité sont explicites et sourcés.
8. Les preuves historiques sont marquées comme telles et ne peuvent plus
   modifier le statut courant.
9. Les index du dépôt et le registre documentaire routent vers le paquet sans
   dupliquer ses centaines de fichiers.
10. Les liens Markdown, l'UTF-8, les JSON, les validateurs statiques,
    `scripts/check.ps1` et `git diff --check` passent, ou toute limite est
    reportée avec son verdict exact.

## Intended files

- Ajouter dans `tools/roblox-art-bible-sota-v3/docs/` :
  - `README.md`
  - `STATUS_CONTRACT.md`
  - `STATE_ONTOLOGY.md`
  - `OBJECT_REGISTRY.md`
  - six fiches sous `objects/`
  - `ROBLOX_TECHNICAL_ART_CONTRACT.md`
  - `VISUAL_METRICS_CONTRACT.md`
  - `GOVERNANCE_AND_RISK.md`
- Corriger les pages existantes d'axes, Blender, Golden Scene, mobile,
  transfert, remédiation, bible et sources.
- Synchroniser le README du paquet, `docs/ROBLOX_3D_ASSET_WORKFLOW.md`,
  `docs/README.md`, `docs/00-governance/DOCUMENT_REGISTER.md` et le plan
  principal de direction artistique.

## Milestones

1. Auditer les sources machine, les statuts, les 18 canons et les 48 variantes.
2. Créer la navigation, le contrat de statut et l'ontologie des états.
3. Documenter les six objets et leurs 16 variantes Salvaged Frontier.
4. Fermer les contrats Blender, Roblox, mobile, performance et accessibilité.
5. Corriger les contradictions historiques et synchroniser les index.
6. Exécuter les validateurs, auditer le diff et enregistrer les preuves.

## Verification

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
.\scripts\art-direction.ps1 verify-static
.\scripts\art-direction.ps1 validate-canons
git diff --check
git status --short
```

Ajouter un audit déterministe des fichiers Markdown : UTF-8, liens relatifs,
titres, présence dans le registre et absence de statuts contradictoires.

Un playtest Studio est non applicable aux seules modifications documentaires.
Les preuves Studio sélectionnées restent `UNKNOWN`; elles ne deviennent pas
`PASS` par cette réécriture.

## Recovery

- Ne pas supprimer les preuves historiques : les archiver ou les marquer
  explicitement comme snapshots.
- Ne pas modifier les contrats JSON pour les faire correspondre au texte.
- Ne pas produire de nouveaux assets ni publier.
- Si une valeur exacte n'est pas prouvée, la router vers sa source machine et
  l'étiqueter `UNKNOWN`, `PENDING` ou `BLOCKED`.

## Progress

- 2026-07-16 : audit initial terminé ; contradictions, matrice d'états et
  frontières d'autorité identifiées.
- 2026-07-16 : ExecPlan créé ; aucune mutation runtime, Studio ou Cloud
  autorisée.
- 2026-07-16 : portail, contrat de statut, ontologie, registre et six fiches
  objet ajoutés ; bible et définitions canoniques reliées.
- 2026-07-16 : contrats axes/Blender/Roblox/mobile/métriques/gouvernance
  fermés ; preuves v3.7 marquées historiques.
- 2026-07-16 : workflow racine 1.6.0, registre et paquet 3.13.0 synchronisés.
- 2026-07-16 : `scripts/check.ps1`, validation stricte, 18 canons/48 états,
  116 tests, r3d, syntaxe PowerShell, UTF-8/liens/H1, manifest et
  `git diff --check` passent. Le check shell est `SKIPPED` car Bash n'est pas
  disponible dans l'environnement Windows.
