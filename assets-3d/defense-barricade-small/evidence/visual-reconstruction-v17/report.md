# Defense Barricade Small — revue de reconstruction v17

## Verdict

`PARTIAL`

La reconstruction v17 atteint le seuil visuel interne de `90/100` et conserve
une chaîne technique entièrement déterministe. Elle n'est pas approuvée pour la
production : le canon reste `CANDIDATE`, la revue humaine liée au hash manque,
et les preuves Roblox Studio, mobile physique et benchmark ne sont pas encore
présentes.

## Changement évalué

La révision 17 ajoute un bevel déterministe de `0,06` stud aux trois panneaux
reclaimed. Le changement ne cherche pas à ajouter du bruit ou des greebles. Il
sépare la grande face calme de chaque panneau de son épaisseur et crée un
highlight stable dans les vues frontale et trois-quarts.

Le changement a été exploré dans la session Workbench
`defense-barricade-small-panel-edge-v16d`, puis transcrit dans la recette
autoritative. La promotion vérifiée prouve :

- trois composants modifiés exactement ;
- `+192` triangles, soit `1 688` triangles par état ;
- dimensions, pivot, grounding, noms, matériaux et socket préservés ;
- fingerprints exacts des positions de sommets, faces et UV entre le candidat
  et la recompilation autoritative ;
- GLB et FBX identiques entre deux builds autoritatifs indépendants.

## Score interne

| Axe | Score |
| --- | ---: |
| Silhouette | 23/25 |
| Proportions | 18/20 |
| Direction artistique | 18/20 |
| Lisibilité gameplay | 19/20 |
| Originalité | 12/15 |
| **Total** | **90/100** |

Le point gagné en direction artistique correspond à une différence observable :
les panneaux ne lisent plus comme trois plaques plates simplement découpées.
Leur épaisseur et leur fabrication sont maintenant visibles sans texture
bruyante, sans nouvelle famille de matériau et sans modifier la silhouette.

## Preuves techniques

- Contrat v17 :
  `98d3e0f01af7c14c8be8c4d2b3ebccd4f167dfa586f435d8662924699dc28876`.
- Canon :
  `5e196aa1ab2bdaaa9c024d250ea76f82b134848b4dcd32b2741f7970c5c77e58`.
- Référence précanonique :
  `219ebd23eff48a3c32413c4ca80660ba725b4689bf523b61b6eaa79ac17865bd`.
- Compilateur :
  `4d9dd176eb8aec26ace12e70a9ea4cf0fe1adccf2976677f40bc976cf3eeb67e`.
- Déterminisme des états :
  `build/state-determinism/determinism-report.json`, statut `PASS`.
- Promotion Workbench :
  `workbench/defense-barricade-small-panel-edge-v16d/promotion-report.json`,
  statut `PASS`.

Les 24 comparaisons de rendus A/B sont exactes : zéro pixel différent et delta
de canal maximal égal à zéro. Les trois GLB et les trois hashes sémantiques sont
distincts entre états, tout en conservant 42 composants, 1 688 triangles,
8 × 4 × 2 studs et le pivot `BASE_CENTER`.

## Limites non masquées

- Le résultat est solide pour un prop Roblox stylisé, mais l'abrasion
  directionnelle et la réponse `SurfaceAppearance` finale restent à prouver
  dans Studio.
- Le socket critique ouvert est lisible depuis la face de service, mais sa
  qualité sous la matrice d'éclairage Roblox n'est pas encore mesurée.
- Le score d'originalité reste interne et doit être confirmé par une revue
  experte indépendante.
- Aucun test sur appareil mobile physique ni benchmark 1/30/100 n'est encore
  lié au hash v17.
- `90/100` est un seuil interne atteint, pas une déclaration de perfection ni
  une approbation humaine.

## Décision

La v17 est `READY_FOR_HUMAN_CANON_REVIEW` sur le plan visuel interne. Elle reste
`productionApproved=false` tant que le canon, Studio, mobile, benchmark et
l'approbation humaine ne sont pas tous prouvés.
