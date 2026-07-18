# Preuves mobile — simulateur et appareil physique

| Champ | Valeur |
| --- | --- |
| ID | `ART-MOBILE-001` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 2.0.0 |
| Simulateur courant | `PARTIAL` |
| Appareil physique courant | `BLOCKED` |
| Dernière revue | 2026-07-16 |

Les deux protocoles sont indépendants. Le Studio Device Simulator prouve le
viewport, l'orientation, la composition et certains chemins d'input. Seul un
appareil réel peut prouver frame time, mémoire, thermique, crash et throttling.

## A. Studio Device Simulator

Le rapport doit enregistrer les valeurs réellement lues, pas seulement le nom
d'un preset susceptible de changer :

```text
profileId
profileSource = builtin | custom
resolutionWidth
resolutionHeight
dpi
orientation
scalingMode
inputMode
studioVersion
placeVersion
candidateDigest
```

Viewports contractuels minimum :

- landscape : 640 × 360 ;
- portrait : 360 × 640.

Un profil custom versionné est préférable pour la reproductibilité. Si un
preset constructeur est utilisé, ses valeurs lues sont copiées dans le rapport.

```powershell
.\scripts\art-direction.ps1 validate-simulator `
  -Report evidence/mobile/studio-simulator/report.json
```

Le rapport actuel reste `PARTIAL` : les captures prouvent la composition des
conditions graybox/candidat 30/100, mais les snapshots LibMP valides ont
retourné une plage 0..0 et SceneAnalysisService était indisponible. Ces
diagnostics ne deviennent pas des mesures inventées.

## B. Appareil physique obligatoire

Statut : `BLOCKED`, aucun appareil baseline nommé n'a exécuté le protocole
courant.

Pour chaque device :

1. enregistrer fabricant, modèle, OS, mémoire, SoC/GPU si disponibles, qualité
   graphique, orientation, build et place version ;
2. cold launch puis 60 s de warm-up ;
3. cinq passages graybox et cinq candidat ;
4. ordre A/B équilibré, sans trois conditions identiques consécutives ;
5. même caméra, serveur, qualité et scénario ;
6. session soutenue d'au moins 15 minutes ;
7. frame time médian, p95, p99, MAD et maximum ;
8. FPS médian/minimum et stalls ;
9. mémoire médiane, p95, maximum et catégories disponibles ;
10. crash, température/état thermique initial-final et throttling observé ;
11. input/touch, lisibilité paysage et portrait ;
12. logs bruts, MicroProfiler et captures hashés.

```powershell
.\scripts\art-direction.ps1 validate-mobile `
  -Report evidence/mobile/<device>/performance-report.json `
  -RequirePass
```

Le validateur recalcule les seuils et l'ordre A/B. Un champ `pass: true` sans
données cohérentes est rejeté.

## C. Lisibilité par objet

- 60 studs : barricade, objective, enemy, turret ;
- 30 studs : floor, damage effect ;
- fonction, facing et intégrité sans couleur seule ;
- interaction alliée distincte de la menace ;
- VFX sans occlusion de la prochaine décision ;
- UI compatible text scaling et reduced motion.

Source officielle consultée le 2026-07-16 :
[Test on hardware](https://create.roblox.com/docs/performance-optimization/test-on-hardware)
et [Studio testing modes](https://create.roblox.com/docs/studio/testing-modes).
