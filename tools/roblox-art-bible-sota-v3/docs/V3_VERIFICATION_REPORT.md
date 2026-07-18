# Rapport de vérification v3.9 — snapshot enregistré

> **Autorité temporelle : `RECORDED`.** Ce rapport décrit l'environnement et
> les artefacts observés lors de la vérification v3.9. Il ne définit pas le
> statut courant. Lire [`../STATUS.json`](../STATUS.json) et
> [STATUS_CONTRACT.md](STATUS_CONTRACT.md). Les comptes fixes ci-dessous sont
> historiques et peuvent différer des validateurs actuels.

Date : 2026-07-16.

Environnement observé : Windows PowerShell 5.1, Python package-local, Blender
5.2.0, StyLua 2.5.2, Selene 0.31.0 et Luau LSP 1.68.1.

## Verdict par couche

| Couche | Verdict | Preuve actuelle |
|---|---|---|
| Constitution créative | `PASS` | Décision fondateur + constitution machine + bible humaine |
| Précanonique local | `PASS` | Contrats fermés, compilateur déterministe, préflight zéro consommation, handoff et revue |
| Exécution ChatGPT Web | `NOT_REQUESTED` | Aucun clic, aucune image et aucun quota consommé pendant l'intégration |
| Validation statique | `PASS` | 57 schémas, 59 instances, 106 tests adversariaux et code généré |
| Canons candidats | `PASS` | 18 canons, 48 états, drift nul |
| Canons production sélectionnés | `BLOCKED` | Six paquets de 17 planches et approbations manquants |
| Blender Salvaged Frontier | `PASS` | 421/421 rendus, 13 exports, 2 stress scenes |
| Conformité technique/composants | `PASS` | Cinq assets vérifiés contre leurs canons |
| Conformité visuelle/humaine | `BLOCKED` | Planches hash-bound et locks humains absents |
| Vertical slice barricade v2 | `PASS` technique | Canon Salvaged Frontier, compilation GLB/FBX et huit rendus |
| Sixième asset | `PARTIAL` | Automatisation courante `PASS 100/100`, humain `PENDING` |
| Studio sélectionné | `UNKNOWN` | Preuves v3.7 archivées, restaging courant non exécuté |
| Mobile physique | `BLOCKED` | Aucun appareil low-tier nommé |
| Étude aveugle | `INCOMPLETE` | Conservée comme recherche, non utilisée pour la sélection |
| Production | `false` | Gates externes et humains ouverts |

## Sélection et constitution

La décision figée est :

> Salvaged Frontier définit l'identité du monde ; Industrial Toy Defense
> impose la discipline de lecture.

Le contrat interdit la fusion visuelle 50/50. Salvaged Frontier contrôle le
sens, la mémoire, les matériaux, l'asymétrie et la tonalité. Industrial Toy
Defense ne fournit que les contraintes de masse, de hiérarchie, de joints, de
modularité, d'accent et de lecture instantanée.

La constitution couvre vingt-et-un scopes, notamment :

- monde, architecture, biomes et forteresse ;
- buildables, objectifs, ennemis, avatars et états ;
- formes, réparations, matériaux, usure et palette ;
- animation, VFX, éclairage, caméra, UI et audio visuel ;
- répétition, cosmétique, génération procédurale et gouvernance.

## Preuve Blender sélectionnée

La matrice complète Salvaged Frontier courante produit :

- 421 rendus sur 421 attendus ;
- 13 exports GLB applicables ;
- 13 vues hero de review ;
- deux scènes de répétition à 30 exemplaires ;
- des hashes d'entrée courants pour territoire, matériaux et générateur ;
- un rapport de build `PASS` ;
- un readback sémantique indépendant des composants ;
- cinq rapports de conformité dont géométrie, budgets et composants passent.

Les rapports restent globalement `BLOCKED` parce que leurs contrôles visuels,
perceptuels et humains exigent les paquets canoniques multimodaux. Ce blocage
est intentionnel.

## Corrections esthétiques vérifiées

L'inspection des rendus a conduit à deux corrections exécutables :

- la poutre centrale de la barricade est redevenue slate structurel afin que le
  cuivre décrive une réparation locale au lieu d'envahir l'identité ;
- le mint a été retiré de l'ennemi et remplacé par des signaux hostiles
  raspberry/warning/critical concentrés vers l'avant.

Le vertical slice `Defense Barricade Small` a ensuite été migré en révision 2 :

- canon `vc_barricade__salvaged-frontier__v1` ;
- châssis slate ;
- panneaux composite récupérés ;
- unique renfort cuivre diagonal ;
- interaction mint locale ;
- noms de pièces historiques conservés ;
- compilation GLB et FBX `PASS`.

## Sixième asset

`turret_fast_v1` a été régénéré avec les contrats courants :

- neuf builds ;
- neuf GLB ;
- 108 rendus ;
- déterminisme `PASS` dans les trois territoires ;
- maximum 1 148 triangles Industrial Toy Defense ;
- maximum 1 156 triangles Salvaged Frontier ;
- maximum 920 triangles Clean Tactical Diorama ;
- score automatisé `100/100` ;
- territoire d'approbation explicitement `salvaged-frontier` ;
- review humaine encore `PENDING`.

Le seul blocage du rapport portable est l'approbation humaine liée au digest
exact du paquet de preuve.

## Tests

Résultats courants :

- `91 passed` pour la suite adversariale Python ;
- `18 tests OK` pour le moteur per-asset r3d ;
- StyLua : `PASS` ;
- Selene : `0 errors`, `0 warnings`, `0 parse errors` ;
- Luau LSP : `PASS` sur les modules applicables ;
- `verify_static.py` : toutes les étapes applicables `PASS` ;
- syntaxe shell POSIX : `SKIPPED` sur cet environnement Windows ;
- résolution Plugin/CaptureController : `SKIPPED` sans sourcemap Studio
  installé.

## Limites d'autorité

Les preuves de comparaison, publication Cloud et intégration Studio v3.7 sont
préservées dans les archives. Elles ne valident pas la constitution sélectionnée
car leurs hashes précèdent les nouvelles règles.

Le prochain `PASS` de production exige encore :

1. les dix-sept familles de planches pour chacun des six canons sélectionnés ;
2. leur approbation humaine liée par hash ;
3. l'approbation exacte de `turret_fast_v1` ;
4. le restaging Studio courant ;
5. le test mobile physique ;
6. l'index de preuves complet ;
7. la création de `art/art-lock.json`.
