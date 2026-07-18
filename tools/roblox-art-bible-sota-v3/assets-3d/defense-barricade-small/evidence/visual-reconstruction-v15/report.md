# Defense Barricade Small — preuve de reconstruction v15

## Verdict

`PARTIAL`.

La reconstruction locale, les trois états, l’enveloppe dimensionnelle, le
Workbench `OBSERVE` et le déterminisme A/B sont `PASS`. La revue visuelle
interne honnête atteint 89/100 : la barricade est cohérente, lisible et
techniquement admissible, mais elle n’est pas encore déclarée artistiquement
parfaite. Le canon est toujours `CANDIDATE`, la décision humaine reste
`PENDING` et les preuves Studio, mobile physique et Roblox Cloud manquent.

## Autorité exacte

- Contrat : révision 15.
- SHA-256 du contrat :
  `4007359aad9898b758666d3dbdcd06f9c4f4c33362642edc71b2509858009fb9`.
- Référence précanonique sélectionnée :
  `precanonical/results/defense-barricade-web-001-result-001/raw/generated-001.png`.
- SHA-256 de la référence :
  `219ebd23eff48a3c32413c4ca80660ba725b4689bf523b61b6eaa79ac17865bd`.
- Canon : `vc_barricade__salvaged-frontier__v1`.
- SHA-256 du canon :
  `5e196aa1ab2bdaaa9c024d250ea76f82b134848b4dcd32b2741f7970c5c77e58`.
- Statut du canon : `CANDIDATE`, non éligible à la production.
- Compilateur :
  `34642e84af8b3d15bb12e3d365f5157aa911ab484b59bacf92eed426e64e2460`.

## Résultat mesuré

| Propriété | Résultat |
| --- | ---: |
| Composants stables | 42 |
| Triangles | 1 496 |
| Cible | 1 500 |
| Maximum canonique | 2 000 |
| Matériaux utilisés | 8 |
| États | 3 |
| Dimensions | 8 × 4 × 2 studs |
| Tolérance contractuelle | 0,25 % |
| Pivot | `BASE_CENTER` |

La révision 15 utilise les quatre triangles encore disponibles sous la cible.
Elle conserve les trois panneaux, le cadre segmenté, les deux pieds à trois
niveaux, les attaches, les renforts arrière, la réparation cuivre et le socket
de service arrière.

## Revue visuelle interne

| Dimension | Score |
| --- | ---: |
| Silhouette | 23/25 |
| Proportions | 18/20 |
| Direction artistique | 17/20 |
| Lisibilité gameplay | 19/20 |
| Originalité | 12/15 |
| **Total** | **89/100** |

### Forces prouvées

- La fonction de barricade est comprise immédiatement en face, en
  trois-quarts et à distance mobile.
- Le châssis sombre, les trois masses composites et les pieds étagés
  construisent une hiérarchie primaire claire.
- Le panneau gauche de remplacement, la grande diagonale cuivre et le socket
  arrière protégé racontent une réparation localisée conforme à Salvaged
  Frontier.
- L’état `damaged` casse une seule épaule et fait pivoter le panneau gauche.
- L’état `critical` élargit la même chaîne de rupture vers le centre et ouvre
  mécaniquement le socket : son capot cuivre se déporte et révèle le noyau
  rouge.
- Aucun état important ne dépend uniquement de la couleur.

### Écarts encore visibles face à la référence

- Les surfaces sont volontairement calmes et compatibles avec le canon, mais
  elles restent plus uniformes que la référence précanonique. Le traitement
  final Roblox `SurfaceAppearance` et l’abrasion directionnelle autorisée
  restent à prouver dans Studio.
- Les pieds et attaches sont désormais construits et crédibles, mais leur
  finition n’atteint pas encore la richesse de contact et de matière perçue
  dans le concept.
- L’originalité repose surtout sur la réparation cuivre et le module arrière ;
  elle n’a pas encore été confirmée par une revue experte indépendante.
- Le rendu Blender prouve la composition et les matériaux déclarés, pas le
  résultat exact du pipeline d’import Roblox.

Ces écarts interdisent de convertir 89/100 en 90 artificiellement. Ils doivent
être résolus ou explicitement acceptés par la revue humaine du paquet complet.

## États et invariants

Les états `intact`, `damaged` et `critical` conservent :

- les 42 mêmes noms de composants ;
- 1 496 triangles ;
- les dimensions exactes 8 × 4 × 2 ;
- le pivot et le grounding ;
- l’empreinte au sol ;
- le même socket gameplay arrière.

Le premier A/B de la révision 13 a correctement échoué lorsqu’un panneau
critique dépassait la profondeur de 0,018 stud. La source a ensuite été
corrigée et la tolérance contractuelle resserrée de 1 % à 0,25 %, conforme aux
±0,005 stud du canon.

## Déterminisme

Preuve :
[determinism-report.json](../../build/state-determinism/determinism-report.json).

- invariants : 3/3 `PASS` ;
- états sémantiquement distincts : `PASS` ;
- GLB distincts entre états : `PASS` ;
- exports GLB, FBX, géométrie et sémantique A/B : `PASS` ;
- 24/24 rendus A/B strictement identiques ;
- zéro pixel différent ;
- delta maximal par canal : zéro ;
- comparaison des états publiés : `PASS`.

Aucune tolérance raster n’a été consommée sur cette preuve.

## Inspection Workbench

Session : `defense-barricade-small-012c50f1fcc4`.

Le mode `OBSERVE` a retrouvé :

- 42 composants ;
- 1 496 triangles ;
- huit matériaux utilisés ;
- les bounds exacts 8 × 4 × 2 ;
- le pivot `BASE_CENTER` ;
- le grounding à zéro ;
- une référence restée immuable.

Cette inspection prouve le build intact de la révision 15. Elle ne constitue
pas une approbation artistique et n’autorise aucune publication.

## Gates de production encore ouverts

- paquet multimodal complet révision 15 et revue de ses 17 planches ;
- verrouillage humain du canon lié au digest exact ;
- décision artistique humaine liée à la preuve v15 ;
- import et réimport dans le place staging ;
- préservation du wrapper, des collisions, tags, attributs et sockets ;
- matrice d’éclairage Studio ;
- tests de répétition 1, 30 et 100 ;
- simulateur mobile séparé du mobile physique ;
- benchmark bas de gamme sur appareil réel ;
- publication staging v1 puis mise à jour v2 du même asset ou Package ;
- provenance Git propre et figée.

`productionApproved` reste donc `false`.
