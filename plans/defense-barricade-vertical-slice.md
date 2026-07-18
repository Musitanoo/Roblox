# ExecPlan — Defense Barricade Small, vertical slice de production

## Outcome

Prouver qu’un objet Roblox défini par le GDD et la constitution Salvaged
Frontier peut être exploré visuellement, verrouillé par un canon, reconstruit
en famille d’états déterministe dans Blender, inspecté sans mutation de sa
source, publié exclusivement en staging, intégré dans Studio et benchmarké
avant toute approbation de production.

L’asset vertical slice est `defense_barricade_small`.

## Autorité

L’ordre d’autorité est :

1. GDD et documents produit acceptés ;
2. canon visuel verrouillé ;
3. contrat `asset.json` ;
4. recette paramétrique ;
5. build Blender ;
6. Workbench d’inspection ;
7. Studio staging ;
8. preuves humaines et mobiles.

Une image générée, une scène Workbench modifiée ou un rapport automatique ne
peut pas réviser silencieusement le canon.

## Résultat observable

### Développeur

- une commande valide le canon et le contrat avant Blender ;
- la famille `intact`, `damaged`, `critical` est compilée séparément ;
- une planche HTML compare tous les états et toutes les vues ;
- deux builds A/B prouvent le déterminisme ;
- les sorties publiées sont comparées aux références A/B ;
- le Workbench inspecte une copie immuable du build exact ;
- le rapport final refuse la production si un gate externe manque.

### Joueur et testeur

- la barricade mesure 8 × 4 × 2 studs ;
- elle reste une barricade identifiable dans tous ses états ;
- ses pieds, son empreinte et son pivot restent stables ;
- `damaged` et `critical` sont lisibles par la forme, pas seulement la couleur ;
- la collision gameplay reste séparée du mesh visuel.

## Contrat révision 6

- Canon : `vc_barricade__salvaged-frontier__v1`.
- Statut du canon : `CANDIDATE`.
- États : `intact`, `damaged`, `critical`.
- Dimensions : 8 × 4 × 2 studs.
- Pivot : `BASE_CENTER`.
- Triangles : cible 1 500, maximum canonique 2 000.
- Résultat de cette révision historique : 1 468 triangles par état.
- Composants de cette révision historique : 29, stables dans tous les états.
- Matériaux actifs : six rôles contrôlés, dont backing `BareMetal`, réparation
  `SunCopper` et socket `InteractionMint`.

## Révision 7 — diagnostic et hypothèse

La révision 6 est techniquement propre et lisible, mais la comparaison directe
avec la référence précanonique sélectionnée montre encore un écart de qualité
artistique incompatible avec un verrou final :

- le cadre ne porte pas assez fortement la silhouette ;
- les pieds sont larges, mais restent trop plats et trop légers visuellement ;
- les panneaux paraissent plus proches d'une grille fonctionnelle que d'une
  défense frontalière robuste ;
- le renfort cuivre et le socket racontent la réparation, mais manquent encore
  de présence dans la lecture proche ;
- les matériaux sont cohérents, mais le châssis absorbe trop de lumière et
  réduit la lecture des volumes secondaires.

Hypothèse v7 : renforcer uniquement les proportions porteuses, la profondeur
des plans, les biseaux et la hiérarchie de valeur doit rapprocher le build de
la référence sans ajouter de bruit tertiaire ni dépasser les budgets.

Invariants obligatoires :

- dimensions globales exactes `8 × 4 × 2` ;
- pivot et grounding inchangés ;
- 42 composants et noms stables ;
- trois baies et deux pieds ;
- états `intact`, `damaged`, `critical` issus de la même structure ;
- interaction menthe uniquement sur la face arrière ;
- réparation cuivre causale unique ;
- maximum canonique de 2 000 triangles ;
- collision gameplay et wrapper inchangés.

La révision 15 remplace les preuves locales antérieures après inspection
Workbench, compilation déterministe, validation des états, inspection des
rendus et reconstruction du paquet canonique 17/17. Elle ne remplace pas le
canon `CANDIDATE` par une autorité humaine inexistante.

## Gates d’acceptation

### Canon et contrat

- [x] le contrat référence le canon exact par SHA-256 ;
- [x] le validateur refuse un maximum local supérieur au maximum canonique ;
- [x] la couverture des états correspond exactement au canon ;
- [x] les opérations d’état sont bornées aux transformations et matériaux ;
- [ ] le canon est `LOCKED + COMPLETE + APPROVED`.

### Blender

- [x] compilation headless avec `--factory-startup` ;
- [x] dimensions et pivot conformes ;
- [x] géométrie, UV, matériaux et budgets validés ;
- [x] GLB et FBX produits ;
- [x] 29 noms de composants stables ;
- [x] trois états compilés ;
- [x] GLB et hashes sémantiques distincts ;
- [x] composants, dimensions, pivot et triangles invariants ;
- [x] deux compilations A/B identiques pour les sorties applicables ;
- [x] 24 rendus publiés identiques aux références A/B ;
- [x] intégrité des FBX publiée vérifiée contre chaque manifeste.

Le `.blend` n’est pas comparé bit à bit, car il enregistre son chemin de sortie.
Le FBX est bit-identique uniquement à chemin canonique équivalent ; entre
répertoires de longueurs différentes, son intégrité est prouvée par le
manifeste, tandis que la géométrie, le GLB, les rendus et le hash sémantique
prouvent le contenu.

### Visuel

- [x] silhouette large et stable ;
- [x] trois panneaux et réparation cuivre lisibles ;
- [x] continuité causale des trois états ;
- [x] état critique lisible par une brèche de silhouette ;
- [x] état endommagé distinct à distance mobile sans approcher la brèche critique ;
- [x] traitement matériel Salvaged Frontier contrôlé par rôles sémantiques ;
- [x] motif fonctionnel signature du panneau remplacé et de sa réparation ;
- [ ] revue visuelle interne à au moins 90/100 ;
- [x] paquet canonique `REAL_RENDERED` de 17/17 planches ;
- [x] deux passes Blender brutes et deux compositions déterministes ;
- [x] manifeste de preuve lié aux hashes v15 et validé sans dérive ;
- [ ] revue humaine à au moins 90/100 ;
- [ ] canon visuel humainement verrouillé.

La revue interne courante est 89/100 avec
`automationReviewStatus=PASS`. Ce statut signifie que les preuves techniques
et perceptuelles déclarées sont courantes ; il ne transforme pas 89 en 90.
Le statut global reste `PARTIAL`, car le floor visuel et
`humanReviewStatus=PASS` ne sont pas encore atteints.

### Workbench

- [x] Blender 5.2 et instance exacte identifiés ;
- [x] session `OBSERVE` en lecture seule ;
- [x] référence immuable ;
- [x] inspection de 42 composants et 1 496 triangles ;
- [x] captures standardisées ;
- [x] aucune exécution Python arbitraire dans la surface normale ;
- [x] promotion v9 reproduite depuis la source autoritative, après échec avant transcription ;
- [x] révision v15 reconstruite depuis la recette déterministe et réinspectée ;
- [x] session finale `defense-barricade-small-012c50f1fcc4` liée aux hashes v15.

### Publication et Studio

- [x] publisher `dry-run` sans réseau ;
- [x] cible non staging refusée ;
- [x] allowlist créateur obligatoire ;
- [x] mutation impossible sans confirmation explicite ;
- [ ] création v1 réelle dans le créateur staging ;
- [ ] mise à jour v2 sur le même Package ID ;
- [ ] readback du Package et de sa révision ;
- [ ] intégration du wrapper Studio ;
- [ ] collisions et propriétés vérifiées ;
- [ ] scènes 1/30/100 ;
- [ ] consoles client et serveur sans erreur pertinente.

### Performance et humain

- [ ] benchmark Studio réel ;
- [ ] preuve mobile physique low-tier ;
- [ ] étude ou revue indépendante ;
- [ ] approbation humaine finale.

## Commandes

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 doctor --repo .
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 validate .\assets-3d\defense-barricade-small\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 compile .\assets-3d\defense-barricade-small\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 compile-states .\assets-3d\defense-barricade-small\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 verify-states .\assets-3d\defense-barricade-small\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 canon-packet .\assets-3d\defense-barricade-small\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 blender-inspect .\assets-3d\defense-barricade-small\asset.json --repo .
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 publish .\assets-3d\defense-barricade-small\asset.json --dry-run
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 report .\assets-3d\defense-barricade-small\asset.json
```

La mutation Cloud exige séparément `--confirm-publish` et n’est jamais
déduite d’une demande de diagnostic ou de simulation.

## Preuves courantes

- Revue :
  `assets-3d/defense-barricade-small/review.json`.
- Planche des états :
  `assets-3d/defense-barricade-small/build/states/state-review.html`.
- Déterminisme :
  `assets-3d/defense-barricade-small/build/state-determinism/determinism-report.json`.
- Reconstruction v15 :
  `assets-3d/defense-barricade-small/evidence/visual-reconstruction-v15/report.md`.
- Workbench final :
  `assets-3d/defense-barricade-small/workbench/defense-barricade-small-012c50f1fcc4/session.json`.
- Promotion autoritative prouvée :
  `assets-3d/defense-barricade-small/workbench/defense-barricade-small-52ad124a9c26/promotion-report.json`.
- Paquet canonique réel :
  `tools/roblox-art-bible-sota-v3/evidence/canonical-visuals/salvaged-frontier/defense_barricade_small-r15/evidence-manifest.json`.
- Digest du paquet canonique :
  `b94a6f2e92470c066b635f342f5a6aae92f9d0f3f3c5023b1ebea0e13c4424a4`.
- Rapport final :
  `assets-3d/defense-barricade-small/qa/final-report.json`.

## Recovery

- aucun fichier utilisateur n’est supprimé par l’installation ;
- les builds restent régénérables ;
- la référence Workbench reste en lecture seule ;
- les corrections restent dans `Candidate` jusqu’à leur promotion ;
- le Package actif reste disponible jusqu’à validation du remplacement staged ;
- aucune publication de production n’existe dans ce plan.

## Progress

- [x] exploration et intégration du canon Salvaged Frontier ;
- [x] reconstruction révision 15 ;
- [x] génération des trois états ;
- [x] déterminisme A/B ;
- [x] synchronisation des rendus publiés avec les références ;
- [x] inspection Workbench finale ;
- [x] revue artistique interne v15 enregistrée honnêtement à 89/100 ;
- [x] paquet de preuve v15 ;
- [x] paquet canonique réel des 17 familles de planches, lié aux hashes v15 ;
- [ ] correction ou acceptation humaine des écarts qui maintiennent le score sous 90 ;
- [ ] verrouillage humain ;
- [ ] publication staging et réimport ;
- [ ] intégration et benchmark Studio ;
- [ ] preuve mobile physique ;
- [ ] approbation production.

## Current status

`PARTIAL`.

La fabrique locale produit une famille d’états techniquement valide,
déterministe et sous la cible de triangles. Le paquet canonique réel est
complet et déterministe, mais la revue interne reste à 89/100 et sa décision
humaine reste `PENDING`. Le verrou humain, la publication staging, Studio, le
benchmark et le mobile physique restent non prouvés. `productionApproved` doit
rester `false`.
