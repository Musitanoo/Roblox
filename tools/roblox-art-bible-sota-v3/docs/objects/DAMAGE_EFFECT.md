# Directional Damage Effect

| Champ | Valeur |
| --- | --- |
| ID canonique | `damage_effect` |
| Fonction | Communiquer direction, gravité et cause d'un impact |
| Enveloppe | 4 × 4 × 4 studs |
| Pivot | `impact_center` |
| Lecture cible | 30 studs |
| États | `DAMAGED`, `CRITICAL` |
| Statut | `CANDIDATE` — approbation `PENDING` |
| Source | [`../../art/canonical-visuals/salvaged-frontier/damage_effect.json`](../../art/canonical-visuals/salvaged-frontier/damage_effect.json) |

## Promesse d'une seconde

Un wedge, un arc et quelques fragments lourds pointent vers la source du coup,
se terminent au point d'impact exact et distinguent une conséquence sérieuse
d'une conséquence critique sans masquer la cible.

## Composants temporels

- `ImpactFlash` : fixe le contact exact, très bref.
- `DirectionalWedge` : porte le vecteur source → impact et la gravité.
- `MajorFragments` : deux ou trois formes maximum, accordées au matériau
  frappé.
- `ResidualTrail` : conserve brièvement la causalité après la forme primaire.

Ce n'est pas un objet physique persistant. Aucun composant ne devient
collidable, queryable ou lootable.

## Limite de vérité gameplay

Les deux références sont `VISUAL_ONLY` et liées à `PD-08`. Le VFX rapporte un
résultat de dégâts déjà décidé par le serveur ; il ne calcule ni dégâts,
stagger, destruction ou collision et ne persiste pas comme débris gameplay.

## États d'intégrité représentés

### `DAMAGED`

- wedge directionnel compact ;
- arc bent cuivre-or contrôlé ;
- deux fragments majeurs maximum lorsque la lecture le permet ;
- disparition rapide pour rendre la prochaine décision visible ;
- une aggravation immédiate peut déclencher `CRITICAL`.

### `CRITICAL`

- wedge plus cassé, angle et amplitude plus sévères ;
- jusqu'à trois fragments majeurs, jamais une pluie ;
- signal critique par forme, timing, fragmentation, lumière et audio ;
- résidu fin et contenu, sans brouillard.

Il n'existe pas d'asset `INTACT` : l'absence d'événement est l'absence du VFX.

## Timing contractuel

- hit flash : maximum 0,12 s ;
- forme primaire : environ 0,35 s ;
- résidu : maximum 1,2 s ;
- l'effet reste entièrement dans l'enveloppe et n'occulte pas la cible.

## Invariants

- pivot au contact et bounds 4 × 4 × 4 ;
- direction alignée sur la vraie source du hit ;
- direction et gravité lisibles sans couleur ;
- deux ou trois fragments majeurs maximum ;
- aucune géométrie gameplay persistante.

## Interdictions

Explosion sphérique uniforme, flash blanc plein écran, fog de particules,
fragments nombreux ou persistants, direction inventée, gravité hue-only,
débris collidables, VFX photoréaliste sans rapport avec le matériau.

## Critères de verrouillage

La preuve doit inclure impacts de plusieurs directions, deux gravités, fonds
clairs/sombres, vues mobile, overdraw contrôlé et vérification que la cible
redevient lisible avant la décision suivante.
