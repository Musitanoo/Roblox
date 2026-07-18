# Roblox Top 1 — Action Loop 0.4.1

| Champ | Valeur |
| --- | --- |
| ID | `SLICE-ACTION-004` |
| Classe | `CONTRACT` |
| Cycle de vie | `IN_REVIEW` |
| Version | 0.4.1 |
| Propriétaire / approbateur | Founder |
| Scope | Boucle d’action Fight, Repair, Rescue ; 1 à 2 joueurs ; sans persistance |
| Remplace | Aucun |
| Source | `Roblox_Top_1_Action_Loop_0.4.md`, fourni par le founder le 2026-07-15 |
| Dernière revue | 2026-07-17 |
| Revue suivante | Décision founder d’acceptation, résultat technique/humain, ou changement de scope |

> Note d’autorité : ce document enregistre intégralement la spécification candidate.
> Son cycle `IN_REVIEW` ne vaut ni acceptation, ni preuve joueur, ni autorisation
> de franchir un stage gate. Les verdicts non observés restent `UNKNOWN`.
> Les sources officielles utilisées ont été revalidées le 2026-07-15 ; elles
> devront l’être de nouveau avant acceptation si l’API ou la politique change.

## Intégration dans le corpus

| Relation | Source d'autorité |
| --- | --- |
| Vision couverte | [GDD 1.0.3](../Roblox_Top_1_Game_Design_Document_v1.0.md), sections 11 et 14 |
| Baseline technique | [Defense 0.2](DEFENSE_LOOP_0_2.md) puis [Build 0.3](BUILD_LOOP_0_3.md) |
| Autorisation | [Roadmap et ADR-0002](00-governance/ROADMAP_AND_STAGE_GATES.md) |
| Successeur conditionnel | [Progression 0.5.1](PROGRESSION_LOOP_0_5.md) |
| Risques et vocabulaire | [R-003/R-004/R-005/R-009](00-governance/RISK_REGISTER.md) et [glossaire](00-governance/GLOSSARY.md) |

Cette intégration rend le contrat découvrable. ADR-0002 rend sa décision
d'acceptation admissible, mais ne change pas son cycle `IN_REVIEW` et ne
transforme pas la preuve humaine G3 `UNKNOWN` en `PASS`.

## Journal de révision

- `0.4.1` — architecture alignée sur Script Sync, phases/action states séparés,
  scope séquencé en sous-gates, protocoles bornés et tests hostiles renforcés.
- `0.4.0` — spécification founder enregistrée sans preuve d’implémentation.

**Nom interne : Fight, Repair, Rescue**<br>
**Statut fonctionnel : spécification candidate complète ; implémentation non autorisée par ce seul enregistrement**<br>
**Dépendances : Defense Loop 0.2 et Build Loop 0.3 techniquement stables**<br>
**Challenge ajouté : Challenge 3 — Blackout**<br>
**Capacité cible : 1 à 2 joueurs**<br>
**Preuve joueur : `UNKNOWN` ; founder actuellement seul testeur disponible**<br>
**Plateformes : clavier/souris, tactile, manette**<br>
**DataStore : interdit**<br>
**Publication : interdite**

---

# 0. Vérité de validation

Cette tranche vise un niveau de conception et de vérification élevé, mais elle n’est considérée comme réussie qu’après playtests observables.

Verdicts autorisés :

- `PASS` : comportement réellement observé et critères critiques réussis ;
- `PARTIAL` : boucle jouable, mais un élément critique reste incomplet ;
- `FAIL` : boucle cassée, injuste ou non autoritaire ;
- `BLOCKED` : prérequis externe absent, scénario non exécutable sans extrapolation ;
- `UNKNOWN` : comportement non testé ou preuve insuffisante.

Aucun comportement non observé ne reçoit `PASS`.

## 0.1 Gate et séquence réversible

Cette spécification complète ne constitue pas une autorisation d’implémenter les
trois sous-tranches en une fois. ADR-0002 renonce au gate participant comme
condition de séquencement, mais la preuve produit reste `UNKNOWN`. Le founder
doit encore accepter le contrat et le scope technique avant implémentation.

Ordre obligatoire après acceptation du scope :

1. `0.4A — Repair the Blackout` : outil de réparation, PowerRelay, warning,
   blackout et backup ; aucun fusil, Hunter, Downed ou revive ;
2. `0.4B — Fight or Repair` : Pulse Rifle et Hunter ajoutés pour tester le choix
   combat/soutien ;
3. `0.4C — Rescue` : santé d’action, Downed, revive et contributions ; preuve
   coopérative nécessaire pour fermer son gate humain.

Chaque sous-tranche reçoit ses propres verdicts techniques et peut être arrêtée
ou corrigée avant la suivante. Le Challenge 3 complet et la Definition of Done
globale ne peuvent recevoir `PASS` qu’après intégration des trois.

---

# 1. Objectif unique

Prouver que le joueur reste activement indispensable pendant la défense sans rendre sa forteresse inutile.

Principe :

> **La forteresse gère la pression ordinaire. Le joueur résout les menaces prioritaires, entretient les défenses, répond aux crises et sauve ses alliés.**

Boucle d’action :

1. lire une menace ;
2. choisir entre tirer, réparer, restaurer le relais ou secourir ;
3. agir avec un retour immédiat ;
4. constater l’effet sur la défense ;
5. recevoir une contribution reconnue ;
6. reprendre une nouvelle décision.

---

# 2. Hypothèse testée

> Un fusil simple, un outil de réparation limité, une panne électrique télégraphiée, un ennemi anti-joueur et une réanimation coopérative suffisent-ils à créer des décisions actives intéressantes pendant la défense ?

La tranche doit prouver que :

- tirer ne remplace pas la construction ;
- les Tourelles ne permettent pas l’AFK ;
- réparer implique un coût d’opportunité ;
- la crise oblige à quitter une position sûre ;
- un joueur à terre crée un moment de coopération ;
- les contributions non offensives sont visibles ;
- le solo reste viable.

---

# 3. Périmètre

## Inclus

- mode Action uniquement pendant `DEFENDING` ;
- un fusil hitscan ;
- chargeur et rechargement ;
- feedback de tir local immédiat ;
- raycast et dégâts serveur ;
- un outil de réparation canalisé ;
- charge de réparation limitée par challenge ;
- réparation de structures ;
- un relais électrique permanent ;
- panne électrique annoncée ;
- Tourelles désactivées pendant la panne ;
- un nouvel ennemi : Hunter ;
- santé d’action personnalisée ;
- état Downed ;
- réanimation coopérative ;
- récupération solo ;
- contributions individuelles et collectives ;
- Challenge 3 — Blackout ;
- mobile, clavier/souris et manette ;
- latence simulée ;
- instrumentation de prototype.

## Exclus

- inventaire ;
- plusieurs armes ;
- raretés ;
- munitions persistantes ;
- loot ;
- crafting ;
- classes ;
- compétences ;
- progression ;
- DataStore ;
- friendly fire ;
- projectiles physiques de gameplay ;
- headshots ;
- critiques ;
- recul complexe ;
- soins consommables ;
- réparation hors challenge ;
- nouveaux pièges ;
- nouvelles constructions ;
- matchmaking ;
- quatre joueurs ;
- animation finale ;
- art final ;
- monétisation.

---

# 4. Résultat joueur recherché

Une défense doit pouvoir produire un souvenir comme :

> « Le relais a sauté, les Tourelles se sont arrêtées, j’ai couvert mon ami pendant qu’il réparait, puis un Hunter m’a mis à terre et il m’a relevé avant que la Brute atteigne le noyau. »

Cette histoire contient :

- une crise ;
- un choix ;
- une coordination ;
- un risque ;
- un sauvetage ;
- un climax.

---

# 5. Principes d’équilibre

## 5.1 La forteresse conserve la majorité de la puissance

Une base cohérente doit gérer la majorité des Rôdeurs.

Le joueur intervient surtout contre :

- Hunters ;
- Brutes ;
- structures endommagées ;
- blackout ;
- alliés Downed ;
- brèches.

## 5.2 Une seule action principale à la fois

Pendant le tir, le joueur ne peut pas :

- réparer ;
- restaurer le relais ;
- réanimer.

Pendant une canalisation, son fusil est indisponible et sa mobilité diminue.

## 5.3 Ressources bornées

- chargeur limité ;
- rechargement ;
- charge de réparation limitée ;
- canalisations interruptibles ;
- durée de crise limitée.

## 5.4 Aucun coût persistant

À la fin du challenge :

- munitions restaurées ;
- charge de réparation restaurée ;
- santé restaurée ;
- base restaurée ;
- aucune arme ou ressource perdue.

---

# 6. États du joueur

```lua
export type PlayerActionState =
    "INACTIVE"
    | "ACTIVE"
    | "RELOADING"
    | "REPAIRING"
    | "REVIVING"
    | "DOWNED"
    | "RECOVERING"
```

## INACTIVE

- aucune action de combat ou canal actif ;
- état utilisé hors de la phase globale `DEFENDING`.

## ACTIVE

- déplacement normal ;
- tir ;
- rechargement ;
- changement d’outil ;
- interaction.

## RELOADING

- tir bloqué ;
- déplacement permis ;
- changement d’outil annule.

## REPAIRING

- tir bloqué ;
- vitesse réduite ;
- canal serveur actif.

## REVIVING

- tir bloqué ;
- déplacement fortement limité ;
- canal serveur actif.

## État DOWNED

- aucun tir ;
- aucune réparation ;
- aucun blocage physique des ennemis ;
- balise visible ;
- récupération programmée.

## RECOVERING

- invulnérabilité courte ;
- actions temporairement limitées ;
- retour automatique à `ACTIVE`.

Le serveur possède l’état canonique.

La phase globale existante reste strictement l’une de `PREPARATION`, `STARTING`,
`DEFENDING`, `VICTORY`, `DEFEAT` ou `REVIEW`. `PlayerActionState` ne la remplace
pas : il vaut `INACTIVE` dans toutes les phases sauf `DEFENDING`. À toute sortie
de `DEFENDING`, le serveur annule reload, réparation, revive, timers et tâches
avant de répliquer `INACTIVE`.

---

# 7. Santé d’action

Ne pas dépendre de la mort Roblox normale pour cette tranche.

Le serveur maintient une santé d’action séparée :

```lua
export type ActionHealthState = {
    current: number,
    maximum: number,
    isDowned: boolean,
    invulnerableUntil: number,
}
```

Valeurs initiales :

```text
MaximumHealth = 100
HunterDamage = 22
BruteContactDamage = 35
ReviveHealth = 50
SoloRecoveryHealth = 40
RecoveryInvulnerability = 2.0 s
```

Règles :

- aucune régénération passive pendant `DEFENDING` ;
- les dégâts sont appliqués uniquement par le serveur ;
- un dommage létal déclenche `DOWNED` ;
- le personnage n’entre pas dans l’état Roblox `Dead` ;
- la défaite dépend uniquement du noyau.

Un reset, `CharacterRemoving`, respawn ou remplacement d’outil pendant
`DEFENDING` n’efface jamais santé, charge, cooldown, Downed ou contribution. Le
serveur annule les canaux puis restaure le personnage selon l’état canonique ;
aucun reset volontaire ne procure soin, munitions ou repositionnement meilleur
que la récupération normale.

La valeur peut être répliquée par attributs pour l’UI, sans accepter de modification client.

---

# 8. Pulse Rifle

## 8.1 Rôle

Arme polyvalente destinée aux menaces prioritaires.

## 8.2 Valeurs initiales

```text
Damage = 28
Range = 120 studs
MagazineSize = 18
FireRate = 5 shots/s
ReloadDuration = 1.35 s
ReserveAmmo = unlimited in prototype
Spread = 0
Headshots = disabled
FriendlyFire = disabled
```

## 8.3 Actions abstraites

```text
ACTION_FIRE
ACTION_RELOAD
ACTION_EQUIP_RIFLE
ACTION_EQUIP_REPAIR
ACTION_INTERACT
```

L’Input Action System ou une abstraction équivalente doit regrouper clavier, tactile et manette dans les mêmes actions de gameplay.

## 8.4 Bindings initiaux

### Clavier/souris

- tir : clic gauche ;
- recharger : R ;
- fusil : 1 ;
- réparation : 2 ;
- interaction : E.

### Tactile

- bouton Tir ;
- bouton Recharger ;
- sélecteur d’outil ;
- bouton contextuel Interagir ;
- assistance de visée légère.

### Manette

- tir : gâchette droite ;
- recharger : X ou action équivalente ;
- changement d’outil : boutons d’épaule ;
- interaction : A.

Le contexte Action est activé uniquement pendant `DEFENDING`.

---

# 9. Pipeline de tir

## 9.1 Prédiction client cosmétique

À la pression :

1. vérifier l’état local ;
2. vérifier le chargeur estimé ;
3. jouer flash, son, recul visuel et tracer ;
4. calculer une direction normalisée ;
5. générer `shotId` ;
6. envoyer l’intention ;
7. attendre la confirmation pour le hit marker de dégâts.

Le client ne crée jamais de dégâts.

## 9.2 Requête

```lua
export type FireRequest = {
    protocolVersion: 1,
    shotId: string,
    aimDirection: Vector3,
    clientSequence: number,
}
```

L’origine finale n’est pas fournie par le client. Le serveur utilise le muzzle autoritaire du personnage ou de l’outil.

Bornes d’entrée :

- table plate avec exactement les champs connus ;
- `shotId` UTF-8 non vide, maximum 64 octets ;
- `clientSequence` entier fini entre 0 et `2^31 - 1` ;
- chaque composante de `aimDirection` est finie ;
- magnitude avant normalisation entre `0.99` et `1.01` ;
- aucun tableau imbriqué, Instance, CFrame, origine, cible ou dégât client.

## 9.3 Validation serveur

Ordre obligatoire :

1. joueur valide ;
2. challenge `DEFENDING` ;
3. état `ACTIVE` ;
4. `shotId` inédit ;
5. séquence cohérente ;
6. cadence respectée ;
7. chargeur non vide ;
8. direction finie, non nulle et normalisée ;
9. muzzle autoritaire disponible ;
10. raycast serveur ;
11. cible ennemie vivante ;
12. dégâts issus de la configuration serveur ;
13. chargeur décrémenté ;
14. contribution enregistrée ;
15. résultat envoyé.

## 9.4 Raycast

Le serveur utilise `Workspace:Raycast()` avec paramètres filtrés.

Exclusions :

- personnage du tireur ;
- previews ;
- FX ;
- objets explicitement non queryables.

Le serveur ne fait jamais confiance :

- à une Instance de cible fournie par le client ;
- à une position d’impact client ;
- à une valeur de dégâts client.

## 9.5 Feedback

### Local immédiat

- flash ;
- son ;
- recul ;
- tracer provisoire.

### Confirmé

- hit marker ;
- mort ;
- dégâts ;
- contribution.

Un tir refusé conserve éventuellement le feedback cosmétique local, mais n’inflige aucun dégât.

---

# 10. Chargeur et rechargement

États :

```text
READY
COOLDOWN
RELOADING
EMPTY
```

Règles :

- rechargement manuel ou automatique à vide ;
- impossible pendant Repairing, Reviving ou Downed ;
- changement d’outil annule ;
- tir annule seulement si le rechargement n’a pas été validé comme terminé ;
- serveur source de vérité ;
- spam sans effet supplémentaire.

---

# 11. Outil de réparation

## 11.1 Rôle

Entretenir les défenses et restaurer le relais sans rendre la base immortelle.

## 11.2 Valeurs

```text
MaximumRepairCharge = 100
StructureRepairRate = 110 HP/s
ChargeDrainRate = 20/s
RepairRange = 13 studs
RepairTickFrequency = 5 Hz
MoveSpeedMultiplier = 0.55
RelayBaseRestoreDuration = 3.5 s
IntermissionChargeRestore = 25
```

À charge pleine, le joueur canalise environ cinq secondes.

## 11.3 Cibles

- Wall ;
- SlowTrap ;
- Turret ;
- PowerRelay.

Le noyau ne peut pas être réparé en 0.4.

## 11.4 Requête d’ouverture

```lua
export type BeginRepairRequest = {
    protocolVersion: 1,
    requestId: string,
    targetId: string,
}
```

Le client ne transmet aucune quantité de réparation.

`requestId` et `targetId` sont non vides et limités à 64 octets. Toute clé
inconnue, table imbriquée ou valeur d’un autre type est rejetée avant recherche
de cible.

## 11.5 Validation serveur

À l’ouverture et chaque tick :

- état compatible ;
- challenge actif ;
- cible valide ;
- cible endommagée ou relais offline ;
- distance ;
- ligne de vue ;
- charge disponible ;
- personnage non Downed ;
- aucune réanimation ;
- fréquence serveur.

## 11.6 Interruptions

- entrée relâchée ;
- cible détruite ou restaurée ;
- distance ;
- ligne de vue ;
- dégâts reçus ;
- joueur Downed ;
- changement d’outil ;
- fin du challenge ;
- charge vide.

## 11.7 Feedback

- faisceau ;
- progression ;
- son continu ;
- variation visuelle de la cible ;
- réparation confirmée ;
- charge restante ;
- raison d’arrêt.

---

# 12. PowerRelay

## 12.1 Rôle

Infrastructure permanente, non constructible, installée dans une zone exposée mais accessible.

## 12.2 États

```text
ONLINE
WARNING
OFFLINE
RESTORING
RECOVERED
```

## 12.3 Effet OFFLINE

- Tourelles désactivées ;
- SlowTraps continuent ;
- Murs inchangés ;
- fusil disponible ;
- HUD et monde signalent clairement la panne.

## 12.4 Restauration

- un ou deux joueurs peuvent contribuer ;
- progression centralisée serveur ;
- un joueur : environ 3,5 secondes ;
- deux joueurs : vitesse plafonnée à 1,75×, pas 2× ;
- consommation de charge individuelle ;
- interruption indépendante.

## 12.5 Anti-softlock

Si le relais n’est pas restauré après 22 secondes :

- système de secours ;
- retour ONLINE ;
- aucune contribution de restauration accordée ;
- message explicite ;
- challenge continué.

Cette limite évite une séquence morte ou impossible pour un nouveau joueur.

---

# 13. Hunter

## 13.1 Fonction

Menace anti-joueur lisible qui perturbe particulièrement les canalisations.

## 13.2 Valeurs

```text
MaximumHealth = 90
MoveSpeed = 9
PlayerTargetRange = 36 studs
PulseRange = 42 studs
LockDuration = 0.8 s
Damage = 22
AttackCooldown = 2.2 s
CoreDamage = 25
StructureDPS = 10
```

## 13.3 Mouvement

Le Hunter reste sur le système de route existant.

Il ne poursuit pas librement les joueurs à travers toute la base dans cette tranche.

## 13.4 Attaque

Pendant sa progression :

1. rechercher une cible valide dans 36 studs ;
2. appliquer un score ;
3. s’arrêter ;
4. afficher verrouillage et ligne de ciblage pendant 0,8 seconde ;
5. vérifier ligne de vue ;
6. tirer une impulsion serveur ;
7. reprendre sa route.

## 13.5 Priorité

```text
REVIVING = 3
REPAIRING = 2
ACTIVE = 1
DOWNED = 0
RECOVERING_INVULNERABLE = 0
```

En cas d’égalité, choisir le joueur le plus proche.

## 13.6 Lisibilité

- silhouette fine ;
- son avant verrouillage ;
- ligne visible ;
- icône sur la cible ;
- animation de tir ;
- aucune attaque instantanée ;
- aucune téléportation ;
- aucun stunlock.

Cette version produit une menace active sans ajouter un pathfinding dynamique vers les joueurs.

---

# 14. Downed

## 14.1 Déclenchement

Lors d’un dommage létal :

1. santé d’action fixée à 1 ;
2. état `DOWNED` ;
3. outils désactivés ;
4. collisions adaptées pour ne pas bloquer les ennemis ;
5. balise de secours ;
6. timer serveur.

## 14.2 Durées

```text
AutoRecoveryDelay = 7.0 s
ReviveChannelDuration = 2.75 s
ActiveReviveGraceMaximum = 2.75 s
```

## 14.3 Solo

Après 7 secondes :

- retour près du noyau ;
- 40 santé ;
- 2 secondes d’invulnérabilité ;
- charge de réparation réduite de 20, sans valeur négative ;
- aucune perte persistante.

## 14.4 Coopération

Un allié peut réanimer avant la récupération automatique.

À 7 secondes, si aucun canal valide n’est actif :

- téléportation près du noyau ;
- 40 santé ;
- aucun game over.

Si un canal valide est déjà actif à 7 secondes, le serveur accorde uniquement
le temps restant de ce canal, plafonné à 2,75 secondes. Toute interruption après
le délai déclenche immédiatement la récupération. Le mode coopératif ne peut
donc pas imposer au joueur Downed une pénalité automatique arbitrairement plus
longue que le solo.

## 14.5 Règles

Un joueur Downed :

- ne tire pas ;
- ne répare pas ;
- ne peut pas être ciblé par les Hunters ;
- ne bloque pas les routes ;
- n’entre pas dans la mort Roblox normale.

---

# 15. Réanimation

## 15.1 Interaction

Utiliser un ProximityPrompt à maintien ou une couche d’interaction équivalente compatible avec clavier, tactile et manette.

Valeurs :

```text
MaximumActivationDistance = 8 studs
HoldDuration = 2.75 s
RequiresLineOfSight = true
```

Intentions réseau :

```lua
export type BeginReviveRequest = {
    protocolVersion: 1,
    requestId: string,
    targetUserId: number,
}

export type EndChannelRequest = {
    protocolVersion: 1,
    requestId: string,
    channelId: string,
}
```

`requestId` et `channelId` sont limités à 64 octets. `targetUserId` est un
entier fini correspondant à un joueur connecté ; les UserIds négatifs ne sont
acceptés que dans le harness multi-client Studio. Le serveur émet `channelId` et
seul son propriétaire peut terminer ce canal.

## 15.2 Validation serveur continue

- cible toujours Downed ;
- réanimateur Active ;
- distance ;
- ligne de vue ;
- challenge actif ;
- pas d’autre canal incompatible.

## 15.3 Interruption

- entrée relâchée ;
- distance ;
- ligne de vue ;
- réanimateur touché ;
- réanimateur Downed ;
- cible récupérée ;
- fin du challenge.

## 15.4 Réussite

- cible à 50 santé ;
- invulnérabilité 2 secondes ;
- `RECOVERING` puis `ACTIVE` ;
- contribution de sauvetage ;
- signal audio-visuel d’équipe.

---

# 16. Challenge 3 — Blackout

## 16.1 Fiche

```text
Challenge 3 — Blackout

Durée estimée : 5 à 6 minutes
Routes : gauche et droite
Menaces : Rôdeurs, Brutes, Hunters
Crise : panne électrique annoncée
Effet : Tourelles temporairement hors ligne
Objectif : protéger le noyau et restaurer le relais
Récompense persistante : aucune
```

## 16.2 Vague 1 — Lire la menace

- 8 Rôdeurs ;
- 1 Hunter ;
- Hunter annoncé ;
- aucun blackout ;
- respiration : 10 secondes ;
- +25 charge de réparation.

Objectif : apprendre le fusil et la menace de ciblage.

## 16.3 Vague 2 — Blackout

- warning de surtension : 8 secondes ;
- relais OFFLINE ;
- 10 Rôdeurs ;
- 2 Hunters ;
- Tourelles désactivées ;
- restauration manuelle possible ;
- backup après 22 secondes ;
- respiration : 12 secondes ;
- +25 charge.

Objectif : choisir entre couvrir et réparer.

## 16.4 Vague 3 — Crise combinée

- 12 Rôdeurs ;
- 1 Brute ;
- 2 Hunters ;
- comportement Brute de 0.2 ;
- aucun second blackout ;
- climax.

## 16.5 Fin

Victoire :

- toutes les vagues générées ;
- aucun ennemi vivant ;
- noyau vivant.

Défaite :

- noyau à zéro.

Les joueurs Downed ne déclenchent pas la défaite.

---

# 17. Contributions

```lua
export type PlayerContribution = {
    playerUserId: number,
    enemyDamage: number,
    priorityEnemyDamage: number,
    repairHealthRestored: number,
    relayRepairProgress: number,
    revivesCompleted: number,
    timesDowned: number,
    huntersDefeated: number,
    blackoutResponseSeconds: number?,
}
```

## REVIEW

Présenter des axes séparés :

- Combat ;
- Engineering ;
- Rescue ;
- Crisis response.

Ne pas produire un score unique.

Titres descriptifs possibles :

- Defender ;
- Engineer ;
- Rescuer ;
- Crisis Responder.

Un joueur peut recevoir plusieurs titres.

---

# 18. HUD

## Permanent pendant la défense

- santé du noyau ;
- santé du joueur ;
- vague ;
- ennemis restants ;
- chargeur ;
- charge de réparation ;
- outil équipé ;
- état de l’allié.

## Crise

- warning ;
- icône du relais ;
- direction 3D ;
- état ;
- progression ;
- temps avant backup.

## HUD Downed

Pour la victime :

- timer ;
- état de l’allié ;
- récupération prévue.

Pour l’allié :

- icône ;
- distance ;
- interaction ;
- progression.

## Mobile

- tir à droite ;
- sélecteur d’outil accessible ;
- interaction contextuelle ;
- boutons éloignés du saut ;
- aucun hover requis ;
- test sur petit téléphone.

---

# 19. Architecture Luau

```text
data/src/shared/Game
├── Config
│   ├── WeaponConfig.luau
│   ├── RepairConfig.luau
│   ├── PlayerActionConfig.luau
│   ├── CrisisConfig.luau
│   ├── ChallengeConfig.luau
│   └── EnemyConfig.luau
├── ActionTypes.luau
├── WeaponMath.luau
├── RepairRules.luau
├── GameTypes.luau
└── StateConstants.luau

data/src/server/Game
├── GameServer.server.luau
└── Services
    ├── GameStateService.luau
    ├── ChallengeService.luau
    ├── GridEnemyService.luau
    ├── GridDefenseService.luau
    ├── CombatStatsService.luau
    ├── PlayerActionService.luau
    ├── WeaponService.luau
    ├── RepairService.luau
    ├── PlayerStateService.luau
    ├── CrisisService.luau
    └── ContributionService.luau

data/src/client
├── DefenseLoopClient.local.luau
└── GameClient
    ├── ActionInputController.luau
    ├── WeaponController.luau
    ├── RepairController.luau
    ├── ReviveController.luau
    ├── ActionHUDController.luau
    └── CrisisController.luau
```

Mappings Script Sync conservés :

```text
data/src/shared → ReplicatedStorage/Shared
data/src/server → ServerScriptService/Server
data/src/client → StarterPlayer/StarterPlayerScripts/Client
```

Les remotes sont créés et validés par `GameServer.server.luau` sous
`ReplicatedStorage/Game/Remotes`, comme dans Build 0.3 ; ils ne sont pas des
fichiers synchronisés. Les `InputContext`, `InputAction` et `InputBinding` vivent
dans `ReplicatedStorage/Inputs` et sont Studio-authoritative. Les templates
`Hunter`, `PulseRifle`, `RepairTool` et `PowerRelay` restent Studio-authoritative
sous `ServerStorage/GameTemplates`. Aucun même subtree n’est géré simultanément
par Script Sync et par une autre synchronisation.

Intégration obligatoire : `WeaponService` applique les dégâts via l’interface
autoritaire du `GridEnemyService`; `RepairService` répare via
`GridDefenseService`; aucun second registre de santé ennemi/défense n’est créé.
`GameTypes.EnemyType` est étendu explicitement avec `Hunter` et tous les switches
exhaustifs existants reçoivent un cas ou un refus fermé.

---

# 20. Responsabilités

## PlayerActionService

- états ;
- transitions ;
- outils ;
- verrouillages.

## WeaponService

- chargeur ;
- cadence ;
- reload ;
- muzzle ;
- raycast ;
- dégâts ;
- confirmations.

## RepairService

- charge ;
- canaux ;
- validations ;
- ticks ;
- restauration.

## PlayerStateService

- santé d’action ;
- Downed ;
- recovery ;
- invulnérabilité ;
- revive.

## CrisisService

- relais ;
- warning ;
- blackout ;
- backup ;
- progression.

## ContributionService

- statistiques ;
- événements clés ;
- rapport.

---

# 21. Sécurité client-serveur

Le client envoie des intentions.

Chaque handler applique dans cet ordre : type racine, nombre de champs, version
de protocole, longueurs et nombres finis, rate limit, cache d’idempotence, phase
et état, permission, validation spatiale, puis effet. Une table cyclique,
imbriquée ou contenant une Instance inattendue est rejetée avant toute recherche
dans le monde.

Requêtes complémentaires :

```lua
export type ReloadRequest = {
    protocolVersion: 1,
    requestId: string,
}
```

`RequestFire`, `RequestReload`, `BeginRepair`, `EndRepair`, `BeginRevive` et
`EndRevive` utilisent des RemoteEvents fiables. `ShotFX` peut utiliser un
UnreliableRemoteEvent uniquement pour les effets cosmétiques ; confirmation,
dégâts et état restent fiables et autoritaires.

Le serveur contrôle :

- état ;
- chargeur ;
- cadence ;
- rechargement ;
- origine du tir ;
- raycast ;
- dégâts ;
- réparation ;
- charge ;
- santé ;
- Downed ;
- revive ;
- relais ;
- blackout ;
- contribution ;
- résultat.

## Rate limits initiaux

```text
RequestFire = 8/s, burst 4
RequestReload = 2/s
BeginRepair = 3/s
EndRepair = 5/s
BeginRevive = 3/s
EndRevive = 5/s
```

Ce sont des token buckets par joueur et par action avec un burst égal à deux
secondes de débit, sauf `RequestFire` dont le burst reste 4. Un plafond global
de 24 intentions d’action par seconde et par joueur protège contre l’alternance
entre remotes. Les refus sont silencieux côté gameplay, métriques agrégées côté
serveur, et ne créent aucune tâche ni réponse volumineuse.

## Idempotence

- `shotId` unique ;
- `requestId` unique ;
- aucun double effet ;
- cache des 64 derniers identifiants par joueur et par famille ;
- le cache conserve le résultat complet pendant au plus 120 secondes afin
  qu’un duplicate reçoive exactement la même réponse sans réexécuter l’effet ;
- un même identifiant avec un payload différent est rejeté `REQUEST_CONFLICT` ;
- les caches et token buckets sont supprimés à `PlayerRemoving`.

`clientSequence` doit progresser strictement. Les duplicates connus sont servis
depuis le cache ; un recul, un saut supérieur à 32 ou un wrap non négocié force
un resync de l’arme sans appliquer de dégâts.

## Validation spatiale

La position répliquée ne suffit pas.

Le serveur recalcule :

- distance ;
- ligne de vue ;
- muzzle ;
- cible ;
- portée.

Le muzzle issu du personnage répliqué n’est pas considéré sûr par sa seule
provenance serveur : il doit rester dans l’arène autorisée, à distance bornée du
HumanoidRootPart observé et compatible avec les contrôles de déplacement du
challenge. Une téléportation, une origine hors zone ou un personnage absent
rejette tir/réparation/revive avant raycast.

---

# 22. Feedback

## Tir

- animation ;
- flash ;
- son ;
- tracer ;
- impact ;
- hit marker confirmé.

## Réparation

- faisceau ;
- progression ;
- son ;
- cible changeant visuellement ;
- charge.

## Hunter

- verrouillage ;
- ligne ;
- son ;
- impact lisible.

## Revive

- maintien ;
- progression ;
- signal final ;
- invulnérabilité visible.

Les timings de gameplay sont serveur ; les animations ne constituent jamais l’autorité.

---

# 23. Performance

Contraintes :

- 24 ennemis actifs maximum ;
- 2 joueurs maximum ;
- raycast uniquement au tir ;
- recherche Hunter toutes les 0,25 s maximum ;
- réparation à 5 Hz ;
- aucune recherche globale par frame ;
- UI événementielle ;
- FX réutilisés ;
- connexions nettoyées à la fin ;
- dix rematchs sans accumulation.

Les FX de tir peuvent utiliser une communication cosmétique non fiable si disponible, mais aucun état critique ne doit en dépendre.

---

# 24. Analytics de prototype

Dans Studio, ces événements sont des enregistrements structurés locaux capturés
par le harness ; `AnalyticsService` n’envoie ni funnel ni custom event depuis
Studio. Dans une expérience publiée ultérieure, l’émission se fait uniquement
côté serveur après validation autoritaire. Les IDs de requête, UserIds, positions
exactes et payloads bruts ne sont jamais placés dans les custom fields.

Le [catalogue Analytics 0.9.1](ANALYTICS_EVENT_CATALOG_0_9.md) propose de
regrouper ces signaux locaux sous `ActionMilestone` pour une future émission.
Il reste `DRAFT` et G6 fermé : les noms ci-dessous ne sont pas des événements
Roblox officiellement actifs.

```text
FIRST_SHOT
FIRST_CONFIRMED_HIT
FIRST_RELOAD
FIRST_REPAIR_STARTED
FIRST_REPAIR_COMPLETED
BLACKOUT_WARNING
BLACKOUT_STARTED
RELAY_REPAIR_STARTED
RELAY_RESTORED
RELAY_BACKUP_TRIGGERED
PLAYER_DOWNED
REVIVE_STARTED
REVIVE_COMPLETED
SOLO_RECOVERY
CHALLENGE_COMPLETED
```

Mesurer :

- temps avant premier tir ;
- précision ;
- temps en tir ;
- temps en réparation ;
- réponse au blackout ;
- restauration manuelle ou backup ;
- Downed ;
- revives ;
- distribution des contributions ;
- rematch.

---

# 25. Tests obligatoires

| ID | Test |
|---|---|
| T01 | Actions désactivées hors DEFENDING |
| T02 | Entrées clavier, tactile et manette |
| T03 | Feedback local sans dégâts locaux |
| T04 | Tir serveur inflige 28 dégâts |
| T05 | Direction invalide rejetée |
| T06 | Cadence trop rapide rejetée |
| T07 | shotId dupliqué sans double dégât |
| T08 | Chargeur vide bloque |
| T09 | Rechargement correct |
| T10 | Changement d’outil annule le reload |
| T11 | Friendly fire impossible |
| T12 | Réparation hors portée rejetée |
| T13 | Réparation sans LOS rejetée |
| T14 | Réparation restaure une structure |
| T15 | Charge diminue correctement |
| T16 | Charge vide arrête le canal |
| T17 | Dégâts reçus interrompent la réparation |
| T18 | Intermission restaure 25 charge |
| T19 | Blackout annoncé 8 secondes |
| T20 | Blackout désactive les Tourelles |
| T21 | SlowTraps restent actifs |
| T22 | Relais restauré par un joueur |
| T23 | Deux joueurs : vitesse plafonnée à 1,75× |
| T24 | Backup après 22 secondes |
| T25 | Hunter reste sur sa route |
| T26 | Hunter cible un joueur Active |
| T27 | Hunter priorise Repairing/Reviving |
| T28 | Hunter télégraphie 0,8 seconde |
| T29 | Hunter ignore Downed et invulnérable |
| T30 | Dégât létal déclenche Downed |
| T31 | Downed verrouille les actions |
| T32 | Downed ne bloque pas la route |
| T33 | Revive réussi en 2,75 secondes |
| T34 | Revive interrompu par distance |
| T35 | Revive interrompu par dégâts |
| T36 | Récupération automatique après 7 secondes, identique solo/coop hors canal actif |
| T37 | Coop failure recovery fonctionne |
| T38 | Invulnérabilité 2 secondes |
| T39 | Noyau seul condition de défaite |
| T40 | Contributions exactes |
| T41 | REVIEW sans score unique |
| T42 | Challenge 3 gagné |
| T43 | Challenge 3 perdu |
| T44 | Deux clients synchronisés |
| T45 | 150 ms sans double tir/réparation |
| T46 | Petit téléphone utilisable |
| T47 | Manette utilisable |
| T48 | Dix rematchs sans résidus |
| T49 | Output client/serveur propre |
| T50 | Performance acceptable avec 24 ennemis |
| T51 | Phase globale et PlayerActionState suivent la matrice définie |
| T52 | Sortie de DEFENDING annule tous canaux, reloads, timers et tâches |
| T53 | Payload racine, clés inconnues, tables imbriquées/cycliques et types invalides rejetés |
| T54 | NaN, infini, direction nulle ou non normalisée rejetés sans effet |
| T55 | Identifiants vides ou supérieurs à 64 octets rejetés avant lookup |
| T56 | Token buckets par remote et plafond global bornent le spam sans file interne infinie |
| T57 | Duplicate identique renvoie le résultat caché ; même ID/payload différent est conflictuel |
| T58 | Séquence reculée ou saut >32 resync sans dégât ni consommation |
| T59 | 0.4A fonctionne sans module, remote ou template de 0.4B/0.4C |
| T60 | InputContext Action s’active uniquement en DEFENDING sans casser les contrôles Roblox réservés |
| T61 | Reset/respawn/CharacterRemoving ne réinitialise ni santé, charge, cooldown, Downed ou contribution |
| T62 | Leave et remplacement de Character nettoient canaux, caches, tâches et connexions |
| T63 | Téléportation ou muzzle hors arène rejette tir/réparation/revive avant raycast |

---

# 26. Definition of Done

Action Loop 0.4.1 reçoit `PASS` uniquement si :

1. le fusil est réactif, mais les dégâts restent serveur ;
2. le joueur répare sans rendre les structures immortelles ;
3. la charge crée un arbitrage ;
4. le blackout est annoncé et récupérable ;
5. le Hunter est distinct, lisible et équitable ;
6. Downed et revive produisent une coopération utile ;
7. le solo reste viable ;
8. les contributions non offensives sont reconnues ;
9. les Tourelles restent utiles ;
10. le tir ne remplace pas la construction ;
11. T01 à T63 ont tous un verdict ;
12. T04, T05, T06, T07, T14, T20, T22, T24, T28, T30, T33, T36, T39, T44, T45, T46, T51, T52, T53, T54, T56, T57, T58, T59, T61, T62 et T63 sont `PASS` ;
13. aucun comportement non observé ne reçoit `PASS`.

---

# 27. Gate humain

Tester avec 6 à 12 joueurs, seuls puis par deux.

Observer :

- tirent-ils sur les Hunters ?
- comprennent-ils quand réparer ?
- voient-ils le warning ?
- trouvent-ils le relais ?
- couvrent-ils le réparateur ?
- voient-ils l’allié Downed ?
- tentent-ils le revive ?
- changent-ils de rôle ?
- l’action détourne-t-elle trop de la base ?

Seuils internes :

- 85 % tirent correctement en moins de 20 secondes ;
- 70 % réparent au moins une structure ;
- 80 % comprennent que les Tourelles sont offline ;
- 70 % trouvent le relais ;
- 60 % le restaurent manuellement ;
- 70 % remarquent un allié Downed ;
- 60 % réussissent un revive ;
- 50 % décrivent un choix entre combat et soutien ;
- 40 % relancent volontairement.

Ces seuils sont internes et non officiels. Rapporter systématiquement les
comptes `n/N`, la composition du panel et les abandons ; avec 6 à 12 personnes,
les pourcentages servent de direction de décision et non d’estimation
statistique généralisable. Tant que seul le founder teste, ils restent
inapplicables et le gate humain demeure `UNKNOWN`.

---

# 28. Risques

## Fusil dominant

Réduire dégâts/cadence avant d’augmenter artificiellement la santé de tous les ennemis.

## Réparation ennuyeuse

Améliorer feedback, ciblage et décision. Ne pas allonger le canal.

## Blackout injuste

Vérifier warning, accès, lisibilité et backup.

## Hunter frustrant

Conserver verrouillage, LOS, faible vie, cooldown et absence de stunlock.

## Revive impossible

Ajuster pression, fenêtre et placement, pas seulement réduire la difficulté globale.

---

# 29. Tranche suivante

Tranche recommandée :

> **Progression Loop 0.5.1 — trois difficultés, Indice de maîtrise temporaire, Recherche temporaire, cinq déblocages horizontaux et récompenses de première réussite, toujours sans DataStore.**

La persistance vient seulement après validation de :

> **Construire → défendre → agir → comprendre → modifier → retenter.**

---

# 30. Sources officielles

Sources Roblox Creator Hub, revalidées pour les affirmations utilisées le
2026-07-15. Leur existence confirme les capacités de plateforme, pas la qualité
joueur de cette slice.

- https://create.roblox.com/docs/input/input-action-system
- https://create.roblox.com/docs/projects/cross-platform
- https://create.roblox.com/docs/workspace/raycasting
- https://create.roblox.com/docs/scripting/events/remote
- https://create.roblox.com/docs/scripting/security/defensive-design
- https://create.roblox.com/docs/scripting/security/server-side-detection
- https://create.roblox.com/docs/ui/proximity-prompts
- https://create.roblox.com/docs/reference/engine/classes/ProximityPrompt/Triggered
- https://create.roblox.com/docs/studio/testing-modes
- https://create.roblox.com/docs/performance-optimization/design
- https://create.roblox.com/docs/performance-optimization/test-on-hardware
- https://create.roblox.com/docs/studio/mcp
