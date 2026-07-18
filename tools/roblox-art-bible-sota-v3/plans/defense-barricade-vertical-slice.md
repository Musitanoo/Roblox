# ExecPlan - Defense Barricade vertical slice

## But

Prouver sur `defense-barricade-small` la chaine par asset: brief ferme,
validation, compilation Blender, exports reproductibles, rendu, publication
staging guardee, reimport Studio et rapport honnete.

## Source de verite

- `assets-3d/defense-barricade-small/asset.json`;
- `assets-3d/defense-barricade-small/review.json`;
- `tools/roblox-3d-asset/`;
- `scripts/r3d.ps1`;
- build genere sous `assets-3d/defense-barricade-small/build/`.

Le manifest utilise uniquement des chemins relatifs au depot. Aucun ID Roblox,
cookie, cle ou creator ID n'est versionne.

## Acceptation

- contrat asset PASS;
- Blender compile sans intervention manuelle;
- mesh ferme, dimensions/pivot/normales/UV et budgets PASS;
- GLB et FBX presents avec hashes;
- rendu de revue present;
- rapport consolide ne transforme aucun gate absent en PASS;
- publication dry-run ne fait aucun appel reseau;
- publication confirmee refuse une cible non staging, un creator hors allowlist
  ou des credentials absents;
- update/reimport conserve l'identite et les proprietes Roblox observees;
- tests unitaires de statut, contrat, publication et scripts Studio PASS.

## Commandes

~~~powershell
.\scripts\r3d.ps1 validate .\assets-3d\defense-barricade-small\asset.json
.\scripts\r3d.ps1 compile .\assets-3d\defense-barricade-small\asset.json
.\scripts\r3d.ps1 compile-states .\assets-3d\defense-barricade-small\asset.json
.\scripts\r3d.ps1 verify-states .\assets-3d\defense-barricade-small\asset.json
.\scripts\r3d.ps1 canon-packet .\assets-3d\defense-barricade-small\asset.json
.\scripts\r3d.ps1 blender-inspect .\assets-3d\defense-barricade-small\asset.json --repo .
.\scripts\r3d.ps1 publish .\assets-3d\defense-barricade-small\asset.json --dry-run
.\scripts\r3d.ps1 report .\assets-3d\defense-barricade-small\asset.json
~~~

## Resultats observes

| Gate | Etat | Preuve |
|---|---|---|
| Contrat | PASS | brief ferme accepte |
| Compilation | PASS | Blender 5.2 LTS |
| Geometrie | PASS | revision 6, 29 composants, 1 468 triangles, dimensions 8 x 4 x 2 |
| Etats | PASS | intact, damaged et critical topology-preserving, distincts et deterministes |
| Exports | PASS | GLB, FBX, manifest portable et 24/24 rendus A/B exacts |
| Tests r3d | PASS | 52/52 dans le dépôt hôte ; 51 PASS + 1 skip hôte attendu dans le package |
| Dry-run publication | PARTIAL attendu | aucune mutation reseau |
| Revue visuelle interne | PASS local | 92/100 ; approbation humaine encore PENDING |
| Paquet canonique | PASS automatise | `REAL_RENDERED` 17/17 ; deux passes Blender et deux compositions deterministes |
| Canon visuel | BLOCKED production | CANDIDATE ; lock humain lie au digest encore absent |
| Studio kit/reimport revision 6 | UNKNOWN | les preuves v3.7 sont historiques |
| Cloud package create/update specifique | UNKNOWN | registre local volontairement sans IDs |
| Mobile physique | BLOCKED | appareil absent |
| Selection humaine | PENDING | lock lie au paquet canonique v6 absent |

## Decision

Le vertical slice prouve l'architecture locale, la famille d'etats v6, le
paquet canonique reel de 17 familles lie aux hashes v6 et la securite de
publication. Il ne revendique ni lock artistique, ni create/update Cloud, ni
preuve Studio/mobile pour cette revision. Le prochain gate d'autorite est la
revue humaine liee au digest du paquet. Toute mutation ulterieure doit rester
staging, utiliser la configuration locale non versionnee et conserver
uniquement des receipts rediges.
