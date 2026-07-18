# Fast Defense Turret

| Champ | Valeur |
| --- | --- |
| ID canonique | `turret_fast_v1` |
| Fonction | Tourelle joueur à tir rapide |
| Dimensions | 4.8 × 5.4 × 5.2 studs |
| Pivot | `bottom_center` |
| Lecture cible | 60 studs |
| États | `INTACT`, `DAMAGED`, `CRITICAL` |
| Statut | `CANDIDATE` — approbation `PENDING` |
| Source | [`../../art/canonical-visuals/salvaged-frontier/turret_fast_v1.json`](../../art/canonical-visuals/salvaged-frontier/turret_fast_v1.json) |

## Rôle de transfert

La tourelle est le sixième asset, volontairement distinct des cinq assets de
calibration. Elle vérifie que la constitution peut produire une machine de
gameplay nouvelle sans inventer palette, matériau, famille d'angles, bevel,
caméra ou langage de damage.

Les preuves de transfert antérieures restent historiques. Elles ne valident
pas le hash du candidat actuel ; une nouvelle preuve technique et humaine sera
nécessaire après verrouillage.

## Promesse d'une seconde

Une machine plantée, à deux canons, vise vers l'avant, expose un socket
d'interaction à l'arrière sûr et perd visuellement sa confiance de tir quand
son intégrité diminue. L'apparence ne prouve ni tracking, ni cadence, ni dégâts.

## Limite de vérité gameplay

Les trois références restent des candidats visuels liés à `PD-07`. `INTACT`
signifie visuellement prêt ; `DAMAGED` signifie confiance réduite ;
`CRITICAL` signifie posture de désactivation prévue. Aucun de ces états ne
prouve qu'un système de ciblage, de tir ou de réparation est implémenté.

## Construction obligatoire

- `Foundation` : footprint stable et axe de rotation.
- `WeaponBody` : masse supérieure orientable.
- `TwinBarrels` : identité intacte non négociable.
- `ServiceMass` : volume arrière d'alimentation/refroidissement.
- `InteractionSocket` : accès allié, opposé au firing face.

## États d'intégrité

### `INTACT`

- deux canons parallèles et lisibles ;
- weapon body centré, foundation stable ;
- socket arrière mint borné ;
- posture centrée et signaux visuels de readiness ;
- transition `DAMAGED` : 0,35 s.

### `DAMAGED`

- un canon s'abaisse à son pivot réel ;
- le guard ou support associé s'ouvre ;
- le socket passe en signal warning sans migrer à l'avant ;
- aucun changement exact de cadence, ciblage ou dégâts n'est déduit ;
- retour `INTACT` : 1,3 s ; aggravation `CRITICAL` : 0,45 s.

### `CRITICAL`

- un canon et son muzzle approuvés sont retirés ;
- la masse supérieure s'incline autour de l'axe stable ;
- le socket s'ouvre et expose la chaîne de réparation ;
- posture visuellement désactivée et readiness éteinte ;
- fumée fine et sparks rares, non occultants ;
- retour réparé `INTACT` : 2 s.

## Matériaux et DA

Le châssis slate standard porte l'essentiel de la masse. Le composite secondaire
calme le service body. Une adaptation cuivre explique refroidissement,
alimentation ou réparation. Le mint reste strictement sur le socket allié.
Warning et critical suivent le côté mécaniquement défaillant.

## Invariants

- dimensions, pivot, foundation et axe de rotation fixes ;
- deux canons en `INTACT` ;
- forward aim et rear service mass toujours lisibles ;
- socket arrière jamais confondu avec un muzzle ;
- damage suit la chaîne canon → guard → support → posture → socket.

## Interdictions

Variante intacte à un canon, missile/laser/heavy cannon, socket sur la firing
face, canons aiguilles, fils fins, plaques flottantes, damage emissive-only,
nouvelle palette ou nouvelle famille constructive.

## Critères de verrouillage

La preuve finale doit sélectionner Salvaged Frontier, être liée au
`evidencePackageSha256` courant, atteindre les seuils humains prévus et être
complétée par les preuves Studio/mobile requises. Les anciennes publications
v3.7 ne satisfont pas ce verrou.
