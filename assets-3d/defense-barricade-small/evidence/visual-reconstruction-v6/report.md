# Defense Barricade Small — preuve de reconstruction v6

## Verdict

`PARTIAL`.

La reconstruction locale, la famille d’états, la déterminisme et la revue
visuelle interne sont `PASS`. La note interne est de 92/100. Ce résultat ne
constitue pas une approbation de production : le canon reste `CANDIDATE`,
l’approbation humaine est `PENDING` et les preuves Studio/mobile/cloud sont
absentes.

## Autorité exacte

- Contrat : révision 6.
- SHA-256 du contrat :
  `1a03c5151f91c205d8a5014e3fb2602ffe4c1995aa5b8949e0297752a0516415`.
- Canon : `vc_barricade__salvaged-frontier__v1`.
- SHA-256 du canon :
  `5e196aa1ab2bdaaa9c024d250ea76f82b134848b4dcd32b2741f7970c5c77e58`.
- Statut du canon : `CANDIDATE`, non éligible à la production.
- Compilateur :
  `e5d7b014533e47d7e3f4a0f0b6f30e1ed1019f3ca99b09c75ada1c696c6eff42`.

## Résultat v6 mesuré

| Propriété | Résultat |
| --- | ---: |
| Composants stables | 29 |
| Triangles | 1 468 |
| Cible | 1 500 |
| Maximum canonique | 2 000 |
| Matériaux | 6 |
| États | 3 |
| Dimensions | 8 × 4 × 2 studs |
| Pivot | `BASE_CENTER` |

La révision 6 atteint enfin la cible de triangles sans retirer les panneaux
séparés, le support de remplacement, la réparation cuivre, les articulations,
les boulons, les pieds en deux niveaux ou le module de service arrière.

## Lecture artistique

### Identité validée en interne

- cadre slate lourd et silhouette immédiatement défensive ;
- trois baies composites lisibles à distance mobile ;
- panneau gauche légèrement plus petit, réellement interprétable comme pièce
  de remplacement ;
- backing `BareMetal` exposé et réparation `SunCopper` à deux articulations ;
- socket arrière cuivre avec noyau mint, visible sans polluer la face gameplay ;
- densité de détail limitée aux pièces fonctionnelles.

La barricade exprime Salvaged Frontier par son histoire de réparation et ses
matériaux réemployés, tandis qu’Industrial Toy Defense maintient une
construction simple, massive et lisible.

### Famille d’états

Les états `intact`, `damaged` et `critical` conservent exactement :

- les 29 mêmes noms de composants ;
- 1 468 triangles ;
- les dimensions 8 × 4 × 2 ;
- le pivot et le grounding ;
- l’empreinte au sol.

`damaged` fait descendre le panneau gauche et rompt localement la ligne
supérieure. `critical` amplifie la même chaîne causale en une brèche dominante
de gauche vers le centre. Les différences ne reposent pas uniquement sur la
couleur : silhouette, posture, valeur de matériau et signal du socket changent
ensemble.

## Déterminisme

La preuve machine est
[determinism-report.json](../../build/state-determinism/determinism-report.json).

- trois GLB sémantiquement distincts ;
- géométrie, noms, triangles, dimensions et pivot invariants ;
- exports GLB et FBX A/B conformes ;
- 24/24 vues A/B strictement identiques ;
- 24/24 vues publiées strictement identiques à la référence A ;
- comparaison publiée globale : `PASS`.

Le vérificateur décode les PNG en RGBA8. L’identité exacte reste la voie
normale. Une micro-variation raster ne peut passer que si elle respecte
simultanément :

- au plus 0,001 % de pixels différents ;
- un delta maximal d’un niveau par canal ;
- une erreur absolue moyenne normalisée au plus égale à 10⁻⁶.

Le test de régression démontre qu’un delta de deux niveaux sur un seul pixel
échoue déjà. Sur cette preuve v6, aucune tolérance n’a été utilisée.

## Inspection Workbench

Session :
`defense-barricade-small-c27ba459b5f1`.

Le mode `OBSERVE` a retrouvé les 29 composants, 1 468 triangles, les six
matériaux, les bounds 8 × 4 × 2 et le pivot `BASE_CENTER`. La référence est
restée immuable. Le Workbench n’accorde aucune autorité de production.

## Correction de la preuve historique v5

L’affichage tronqué observé en v5 provenait de la surface d’inspection. Le
décodage PNG indépendant et une conversion JPEG à chemin unique ont confirmé
que le fichier était valide. Aucune corruption du PNG n’a été prouvée.

Le pipeline a malgré tout été durci avec :

- stabilisation de deux trames consécutives ;
- PNG RGBA8 et dithering explicitement contrôlés ;
- comparaison pixel décodée entre builds A/B ;
- comparaison des états publiés avec la référence déterministe ;
- sauvegardes Blender versionnées désactivées et absence vérifiée de
  `source.blend1` dans tous les builds courants.

## Tests du workflow

- `138 passed` dans la suite adversariale de la bible ;
- `47 passed` dans la suite `r3d` active ;
- `47 tests` dans le package portable, dont `46 passed` et un skip attendu
  parce que la configuration MCP appartient au dépôt hôte ;
- un `SKIP` attendu : la configuration MCP projet est installée par le dépôt
  hôte et ne doit pas être exigée du package isolé.

## Gates de production encore ouverts

- paquet multimodal complet et verrouillage humain du canon ;
- revue artistique humaine liée au digest v6 ;
- publication staging v1 puis mise à jour du même Package v2 ;
- intégration et playtest Studio avec wrapper, collisions et console ;
- matrice d’éclairage Studio ;
- mobile physique bas de gamme ;
- benchmark équilibré à 1, 30 et 100 exemplaires ;
- provenance Git propre et figée.

`productionApproved` reste donc `false`.
