# Fortress Floor Module

| Champ | Valeur |
| --- | --- |
| ID canonique | `floor_module` |
| Fonction | Cellule répétable de sol de forteresse |
| Dimensions | 4 × 0.5 × 4 studs |
| Pivot | `bottom_center` |
| Lecture cible | 30 studs |
| États | `INTACT`, `DAMAGED` |
| Statut | `CANDIDATE` — approbation `PENDING` |
| Source | [`../../art/canonical-visuals/salvaged-frontier/floor_module.json`](../../art/canonical-visuals/salvaged-frontier/floor_module.json) |

## Promesse d'une seconde

Une cellule carrée promet visuellement un sol sûr, modulaire et alignable. Le
joueur comprend les connexions de voisinage et repère une défaillance locale
sans que la référence visuelle prétende modifier la collision.

## Limite de vérité gameplay

Les références restent liées à `PD-06`. `DAMAGED` est explicitement
`VISUAL_ONLY` : aucune pénalité de mouvement, placement, support ou collision
n'est autorisée. Le plan de collision et les anchors restent identiques.

## Construction obligatoire

- `StructuralSlab` : volume porteur et surface traversable.
- `CentralInset` : identité top-view et zone de réparation.
- `EdgeKeys` : clés d'alignement compatibles avec les quatre voisins.

La répétition est une propriété centrale. Les instances réutilisent les mêmes
combinaisons mesh/matériau ; elles ne génèrent pas un mesh unique par tuile.

## États d'intégrité

### `INTACT`

- slab plan, inset stable, quatre edge keys compatibles ;
- surface de marche honnête et sans micro-relief gênant ;
- rythme répétable visible à proximité sans bruit à distance ;
- transition `DAMAGED` : 0,25 s.

### `DAMAGED`

- une défaillance locale affecte le `CentralInset` ou expose un `EdgeKey` ;
- le dommage suit une cause unique, pas un réseau de fissures aléatoires ;
- la surface conserve la même promesse visuelle de marche et le même plan de
  collision déclaré ;
- retour `INTACT` : 0,9 s.

`CRITICAL` est non applicable. Si le gameplay introduit un sol non traversable,
il faudra versionner le contrat gameplay et le canon au lieu d'inventer une
variante implicite.

## Matériaux et répétition

Le slate porte la structure, le composite calme l'inset et le métal nu reste
localisé aux contacts. Le cuivre peut marquer une réparation réelle, jamais
chaque tuile. Les variations de surface ne doivent ni casser l'instancing, ni
produire un damier de matériaux uniques.

## Invariants

- 4 × 0.5 × 4 et pivot fixes ;
- plan de collision stable ;
- edge keys exactement compatibles ;
- inset et périmètre reconnaissables en top-view ;
- aucune variation qui modifie les anchors de placement.

## Interdictions

Réseaux de cracks aléatoires, relief gênant, flèches ou textes peints, faux
boutons, damage color-only, bords incompatibles, ombres ou saleté baked dans
l'albedo, variations uniques détruisant la réutilisation.

## Critères de verrouillage

Le paquet doit prouver 1, 30 et 100 répétitions, les raccords sur quatre côtés,
la lisibilité du dommage local et l'honnêteté collision/visuel en Studio.
