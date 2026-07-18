# Defense Barricade Small — preuve de reconstruction v5

## Verdict

`PARTIAL`.

La reconstruction déterministe et la famille d’états sont techniquement
`PASS`. La qualité artistique reste `REVISION_REQUIRED` avec une note de
87/100. Ce paquet ne constitue ni un verrouillage du canon ni une approbation
de production.

## Autorité exacte

- Contrat : révision 5.
- SHA-256 du contrat :
  `b4284bf1075e1509d3d78b5965e107020b97af11ac970d2a475414dd22bcd17d`.
- Canon : `vc_barricade__salvaged-frontier__v1`.
- SHA-256 du canon :
  `5e196aa1ab2bdaaa9c024d250ea76f82b134848b4dcd32b2741f7970c5c77e58`.
- Statut du canon : `CANDIDATE`, non éligible à la production.

## Évolution mesurée

| Preuve | Baseline révision 3 | Reconstruction révision 5 |
| --- | ---: | ---: |
| Composants | 11 | 29 |
| Triangles | 1 188 | 1 916 |
| États explicites | 1 | 3 |
| Dimensions | 8 × 4 × 2 | 8 × 4 × 2 |
| Pivot | `BASE_CENTER` | `BASE_CENTER` |

La hausse de triangles est justifiée par la séparation des panneaux, supports,
articulations, boulons, rails d’état et module de service. Elle respecte le
maximum canonique de 2 000, mais dépasse la cible de 1 500.

## Famille d’états

Les états `intact`, `damaged` et `critical` partagent :

- les mêmes 29 composants ;
- les mêmes noms ;
- 1 916 triangles ;
- les mêmes dimensions ;
- le même pivot ;
- la même empreinte au sol.

Les différences d’état sont portées uniquement par des transformations et
matériaux déclarés. Les GLB et hashes sémantiques sont distincts. Les sorties
publiées, les rapports géométriques et les 24 rendus correspondent aux builds
déterministes A/B.

La planche de comparaison est
`build/states/state-review.html`. La preuve machine est
`build/state-determinism/determinism-report.json`.

## Lecture visuelle

### Points validés

- masse large, stable et immédiatement compatible avec une barricade ;
- trois panneaux composites lisibles ;
- cadre sombre et pieds lourds adaptés à la lecture mobile ;
- réparation cuivre identifiable et fonctionnelle ;
- état critique clairement distinct par une brèche de gauche vers le centre ;
- socket arrière conservant la hiérarchie du front gameplay.

### Révision encore nécessaire

- les matériaux restent trop propres et uniformes pour la promesse finale
  Salvaged Frontier ;
- l’état `damaged` est encore trop discret à la distance mobile ;
- la construction reste relativement générique et nécessite un motif
  fonctionnel signature supplémentaire ;
- la marge entre 1 916 triangles et le maximum de 2 000 est trop faible ;
- aucune capture Roblox sous les éclairages réels ni preuve mobile physique
  n’existe pour cette révision.

## Anomalie d’inspection et durcissement du workflow

Pendant la revue v5, la surface d’inspection d’image a affiché
`damaged/perspective.png` comme une ancienne trame tronquée. Un décodage PNG
indépendant et une conversion JPEG à chemin unique ont ensuite montré que le
fichier publié était valide : aucune corruption du PNG n’a été prouvée.
L’incident est donc classé comme anomalie de cache ou d’affichage de l’outil
d’inspection, et non comme corruption du build.

Le workflow a néanmoins été durci. `verify-states` compare désormais chaque
GLB, rapport géométrique, hash sémantique et rendu publié aux références
déterministes. Le compilateur refuse aussi une trame non stabilisée.
L’intégrité du FBX est vérifiée contre son manifeste ; son identité binaire
entre répertoires de longueurs différentes n’est pas exigée, car le format
encode la longueur du chemin source normalisé.

## Gates de production encore ouverts

- verrouillage humain du canon ;
- revue visuelle finale à au moins 90/100 ;
- publication staging v1 et v2 ;
- confirmation et intégration du Package dans Studio ;
- benchmark Roblox et mobile ;
- provenance Git propre.

`productionApproved` reste donc `false`.
