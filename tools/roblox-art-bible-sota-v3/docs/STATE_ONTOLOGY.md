# Ontologie des états visuels et gameplay

| Champ | Valeur |
| --- | --- |
| ID | `ART-STATE-001` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 1.1.0 |
| Scope | Vocabulaire de DA ; implémentation runtime non déclarée |
| Dernière revue | 2026-07-18 |

## Principe

Un objet ne possède pas « un état » unique. Il compose plusieurs axes
orthogonaux. Cette séparation empêche qu'une réparation, un tir, une
affiliation ou un focus UI soit transformé par erreur en variante de mesh.

```text
VisualState =
  IntegrityState
  + OperationalState
  + ActionState
  + InteractionState
  + AffiliationState
  + LifecycleState
  + TransientEvent*
```

Le présent document ferme le vocabulaire artistique. Il ne prétend pas que ces
enums sont déjà implémentés dans le gameplay.

## Axes normatifs

### `IntegrityState`

Décrit l'intégrité visible durable et peut autoriser une variante d'asset.

- `INTACT` : structure complète, fonction lisible, aucune rupture majeure.
- `DAMAGED` : perte partielle ou exposition causale ; fonction encore
  reconnaissable.
- `CRITICAL` : rupture visuelle sévère ; silhouette et posture changent sans
  déplacer les anchors gameplay. La capacité réelle n'est jamais déduite de
  cette apparence.

Applicabilité exacte :

| Objet | `INTACT` | `DAMAGED` | `CRITICAL` | Raison d'absence |
| --- | ---: | ---: | ---: | --- |
| `barricade` | oui | oui | oui | — |
| `objective_core` | oui | oui | oui | — |
| `enemy_standard` | oui | oui | oui | — |
| `floor_module` | oui | oui | non | Le module endommagé reste un sol honnête ; pas de faux état critique. |
| `damage_effect` | non | oui | oui | L'absence de VFX signifie « aucun événement », pas un asset `INTACT`. |
| `turret_fast_v1` | oui | oui | oui | — |

`IntegrityState` est le seul axe qui structure les 16 variantes exportées
Salvaged Frontier actuellement définies.

L'applicabilité exacte, les overlays, les transients, l'état terminal et la
vérité gameplay de chaque état sont définis par objet dans :

```text
art/canonical-visuals/object-product-contracts.json
```

### `OperationalState`

Décrit la capacité fonctionnelle, sans imposer une nouvelle géométrie :

- `READY`
- `ACTIVE`
- `DEGRADED`
- `DISABLED`

La correspondance avec l'intégrité n'est pas bijective. Une tourelle
`DAMAGED` peut rester `ACTIVE` ou devenir `DEGRADED`. Une barricade
`CRITICAL` peut encore bloquer selon le gameplay autoritaire. Tant que le
contrat gameplay applicable n'est pas accepté, les prompts et canons doivent
décrire uniquement l'apparence et conserver la promesse de collision déclarée.

### `ActionState`

Décrit une action courte ou une animation :

- commun : `IDLE`, `REPAIRING`
- tourelle : `TRACKING`, `FIRING`, `RELOADING`
- ennemi : `MOVING`, `ATTACKING`, `STAGGERED`, `DYING`
- objectif : `PULSING`, `ALARMING`
- VFX : `IMPACTING`, `RESIDUAL`, `FADING`

Un `ActionState` ne modifie jamais silencieusement les dimensions, le pivot ou
la collision.

### `InteractionState`

Décrit l'affordance joueur/UI :

- `AVAILABLE`
- `FOCUSED`
- `SELECTED`
- `BLOCKED`
- `UNAVAILABLE`

Il s'exprime par forme, contraste, mouvement ou UI ; jamais par couleur seule.

### `AffiliationState`

- `PLAYER`
- `ALLY`
- `HOSTILE`
- `NEUTRAL`

L'affiliation contrôle les rôles sémantiques autorisés. Le mint d'interaction
alliée ne doit pas migrer sur l'ennemi hostile.

### `LifecycleState`

- `PREVIEW`
- `PLACED`
- `ACTIVE`
- `DISABLED`
- `DESTROYED`
- `REMOVED`

Ce cycle décrit l'existence gameplay. `DESTROYED` n'est pas automatiquement
une quatrième variante d'intégrité ; il peut être une transition vers retrait,
débris bornés ou remplacement selon le contrat gameplay.

### `TransientEvent`

Événement non stocké comme état visuel durable :

- `HIT`
- `BREAK`
- `REPAIR_STARTED`
- `REPAIR_COMPLETED`
- `FIRE`
- `MUZZLE_FLASH`
- `SELECTION_CHANGED`

Un événement déclenche un VFX, un son, une animation ou une transition, puis
expire.

## Composition correcte

```text
turret_fast_v1
IntegrityState   = DAMAGED
OperationalState = DEGRADED
ActionState      = FIRING
InteractionState = AVAILABLE
AffiliationState = PLAYER
LifecycleState   = ACTIVE
TransientEvent   = MUZZLE_FLASH
```

Cette composition ne crée qu'une variante géométrique `damaged`. Les autres
axes sont rendus par animation, lumière, VFX, audio ou UI.

## Transitions et invariants

- Toute transition d'intégrité nomme les composants affectés et sa durée.
- `repair` est une action ou une transition vers un niveau d'intégrité
  supérieur, jamais un `IntegrityState`.
- `critical` peut être un état d'intégrité ou un rôle de couleur/VFX ; le
  contexte doit être explicite.
- Les transitions conservent dimensions, pivot, anchors, footprint et promesse
  de collision, sauf contrat gameplay versionné.
- Une référence primaire ne compose jamais automatiquement un overlay
  opérationnel, un transient ou un état terminal.
- Un prompt ne peut pas annoncer une capacité, une collision, une persistance
  ou un apprentissage adaptatif que son bloc `gameplayTruth` ne permet pas.
- Les signaux de gravité utilisent au moins deux canaux parmi silhouette,
  posture, valeur, couleur, lumière, mouvement, VFX et audio.
- Un état non applicable n'est ni généré, ni staged, ni compté comme preuve.
