# Objective Core

| Champ | Valeur |
| --- | --- |
| ID canonique | `objective_core` |
| Fonction | Objectif principal à défendre et ancre visuelle |
| Dimensions | 6 × 7 × 6 studs |
| Pivot | `bottom_center` |
| Lecture cible | 60 studs |
| États | `INTACT`, `DAMAGED`, `CRITICAL` |
| Statut | `CANDIDATE` — approbation `PENDING` |
| Source | [`../../art/canonical-visuals/salvaged-frontier/objective_core.json`](../../art/canonical-visuals/salvaged-frontier/objective_core.json) |

## Promesse d'une seconde

Un cœur lumineux, haut et protégé, explique immédiatement ce que la forteresse
défend. Sa cage, son exposition et sa posture communiquent l'intégrité à
distance sans dépendre de l'UI.

## Limite de vérité gameplay

Les trois références restent des candidats visuels liés à `PD-08`. Elles
n'annoncent ni points de vie exacts, ni multiplicateur de protection, ni
mécanique de réparation. Même `CRITICAL` reste un objectif présent et
défendable ; la défaite est un état terminal runtime-only séparé.

## Construction obligatoire

- `Pedestal` : base stable, large et non armée.
- `ProtectedCore` : cœur lumineux, ancre fixe de vie et d'attention.
- `ProtectiveCage` : structure qui montre physiquement le niveau de protection.
- `ServiceSpine` : colonne arrière de maintenance et accès joueur.

La face joueur et la colonne de service ne changent jamais de côté. Le cœur ne
devient ni une sphère flottante gratuite, ni une arme.

## Hiérarchie

1. masse primaire : monument protégé sur son piédestal ;
2. masse secondaire : cage et colonne de service ;
3. finition : attaches, bords réparés et signaux sémantiques limités.

La verticalité en fait un landmark ; le vide autour du cœur rend son niveau
d'exposition lisible.

## États d'intégrité

### `INTACT`

- cage fermée et régulière ;
- cœur protégé avec pulsation stable ;
- accès joueur lisible sans dominer le monument ;
- transition `DAMAGED` : 0,5 s.

### `DAMAGED`

- la cage s'ouvre sur une chaîne causale localisée ;
- le cœur augmente son exposition et son irrégularité ;
- posture, valeur et lumière signalent la perte de protection ;
- la chronologie de retour ou d'aggravation reste une intention visuelle à
  confirmer par le contrat gameplay.

### `CRITICAL`

- une partie approuvée de la cage se rompt ;
- le cœur est fortement exposé, mais reste sur le même anchor ;
- alarme lisible par cage, lumière, mouvement et audio, pas par rouge seul ;
- la silhouette reste celle d'un objectif allié, jamais d'une tourelle ;
- la reconstruction vers `INTACT` reste une transition visuelle candidate.

## Matériaux et sémantique

Slate et composite forment le monument calme. Le cuivre raconte les
interventions humaines. Le mint désigne l'accès allié. Warning et critical
restent localisés autour de la protection réellement compromise. Le cœur peut
être lumineux, mais son mesh et sa cage doivent rester lisibles lumière coupée.

## Invariants

- 6 × 7 × 6, footprint et pivot fixes ;
- piédestal, cœur, cage et spine toujours reconnaissables ;
- ouverture joueur et arrière technique ne s'inversent pas ;
- exposition progressive autour d'un cœur immobile ;
- aucune silhouette d'arme.

## Interdictions

Boîte plate, cœur flottant sans protection, baril ou viseur hostile, symétrie
radiale effaçant avant/arrière, health color-only, fissures uniformes,
symbolisme textuel inexpliqué, particules occultantes, bruit de ruine générique.

## Critères de verrouillage

Le paquet multimodal doit rendre incontestables le landmark, le côté service,
le degré d'exposition et les trois états dans les profils d'éclairage et aux
distances mobile déclarées.
