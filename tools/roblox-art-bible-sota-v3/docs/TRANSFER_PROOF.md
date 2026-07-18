# Preuve de transfert — `turret_fast_v1`

| Champ | Valeur |
| --- | --- |
| ID | `ART-TRANSFER-001` |
| Classe | `EVIDENCE` + protocole |
| Cycle de vie | `ACTIVE` |
| Version sélectionnée | Constitution Salvaged Frontier courante |
| Dernière revue | 2026-07-16 |

## But

`turret_fast_v1` est le sixième asset, précédemment non utilisé pour calibrer
les cinq recettes. Il teste la capacité du système à créer une défense rapide
sans ajouter palette, matériau, angle, bevel, caméra, lighting ou langage de
damage.

## Exécution

```powershell
.\scripts\art-direction.ps1 transfer -Open
```

La commande valide le contrat, construit deux fois par territoire, compare les
rapports et GLB, exécute la matrice de rendu, mesure silhouettes/framing,
package les artefacts et écrit :

```text
evidence/transfer/turret-fast-v1/report.json
```

## Preuve courante sélectionnée

```text
automatedStatus   PASS
automatedScore    100/100
overallStatus     PARTIAL
humanReview       PENDING
territories       3/3 PASS
determinism       3/3 PASS
full renders      108
portable assets   51 territory + 3 review
triangle maxima   1148 / 1156 / 920
triangle budget   3500
selected territory salvaged-frontier
```

Le `PARTIAL` est intentionnel. L'automatisation prouve le transfert technique.
Elle n'approuve pas la tourelle pour la production.

## Cloud et Studio

Statut courant pour la constitution sélectionnée :

```text
Cloud staging   UNKNOWN
Studio staging  UNKNOWN
```

Les `PASS` 9/9 Cloud, intégration Studio, groupes 30/100, playtest et captures
appartiennent à la baseline v3.7 archivée, antérieure au verrou Salvaged
Frontier optimisé. Ils prouvent que le pipeline a fonctionné à cette date, pas
que la version sélectionnée actuelle a été staged.

Les dry-runs restent disponibles :

```powershell
.\scripts\art-direction.ps1 publish-transfer
.\scripts\art-direction.ps1 stage-transfer
```

Toute mutation externe exige respectivement `-ConfirmPublish` ou `-Apply` et
une autorisation explicite. Cette documentation n'autorise aucune publication.

## Revue humaine finale

Le reviewer doit compléter
`art/transfer/turret-fast-v1-review.json` contre l'exact
`evidencePackageSha256`, sélectionner le même territoire que la constitution,
noter chaque dimension au moins 16/20 et atteindre 90/100.

```powershell
.\scripts\art-direction.ps1 validate-transfer -RequirePass
```

Modifier le digest pour forcer un résultat est interdit. Toute mutation du
canon ou de la preuve exige une reconstruction puis une nouvelle revue.
