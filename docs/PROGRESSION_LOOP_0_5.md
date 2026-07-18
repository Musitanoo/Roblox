# Roblox Top 1 — Progression Loop 0.5.1

| Champ | Valeur |
| --- | --- |
| ID | `SLICE-PROGRESSION-005` |
| Classe | `CONTRACT` |
| Cycle de vie | `IN_REVIEW` |
| Version | 0.5.1 |
| Propriétaire / approbateur | Founder |
| Scope | Progression de prototype en mémoire serveur ; sans DataStore ni monétisation |
| Remplace | Aucun |
| Source | `Roblox_Top_1_Progression_Loop_0.5.md`, fourni par le founder le 2026-07-15 |
| Dernière revue | 2026-07-17 |
| Revue suivante | Entrée G4 ou dérogation explicite, résultat Action 0.4.1, ou changement de progression |

> Note d’autorité : ce document enregistre intégralement la spécification candidate.
> Son cycle `IN_REVIEW` ne vaut ni acceptation, ni preuve joueur, ni autorisation
> de franchir un stage gate. Les verdicts non observés restent `UNKNOWN`.
> Les sources officielles utilisées ont été revalidées le 2026-07-15 ; elles
> devront l’être de nouveau avant acceptation si l’API ou la politique change.

## Intégration dans le corpus

| Relation | Source d'autorité |
| --- | --- |
| Vision couverte | [GDD 1.0.3](../Roblox_Top_1_Game_Design_Document_v1.0.md), section 17 |
| Baseline technique | [Build 0.3](BUILD_LOOP_0_3.md) et [Action 0.4.1](ACTION_LOOP_0_4.md) dans le scope utilisé |
| Autorisation | [Roadmap G4 et règle de dérogation](00-governance/ROADMAP_AND_STAGE_GATES.md) |
| Schéma consommateur | [Persistence 0.6.1](PERSISTENCE_LOOP_0_6.md) après acceptation du schéma |
| Risques et vocabulaire | [R-004/R-007/R-008/R-015/R-016](00-governance/RISK_REGISTER.md) et [glossaire](00-governance/GLOSSARY.md) |

Cette intégration ne transforme ni la progression mémoire en données
persistantes, ni le contrat `IN_REVIEW` en autorisation G4.

## Journal de révision

- `0.5.1` — progression isolée du profil persistant, transactions de fin de
  challenge idempotentes, protocoles bornés, architecture Script Sync réelle et
  sous-gates de validation ajoutés.
- `0.5.0` — spécification founder enregistrée sans preuve d’implémentation.

**Nom interne : Mastery, Research, Sidegrades**<br>
**Statut fonctionnel : spécification candidate complète ; implémentation non autorisée par ce seul enregistrement**<br>
**Dépendances : Defense Loop 0.2, Build Loop 0.3 et Action Loop 0.4.1 techniquement stables dans le scope utilisé**<br>
**Capacité cible : 1 à 2 joueurs**<br>
**Preuve joueur : `UNKNOWN` ; founder actuellement seul testeur disponible**<br>
**Progression : mémoire serveur uniquement**<br>
**DataStore : interdit**<br>
**Publication : interdite**<br>
**Monétisation : interdite**

---

# 0. Vérité de validation

Cette tranche ne cherche pas encore à construire l’économie finale ou la progression sur plusieurs jours.

Elle doit seulement prouver que la progression :

- clarifie le prochain objectif ;
- récompense la maîtrise ;
- encourage la variété ;
- débloque de nouvelles stratégies ;
- donne envie de tenter une nouvelle difficulté ;
- n’incite pas à répéter mécaniquement la même mission.

La rétention réelle reste `UNKNOWN` avant des cohortes et playtests réels.

Verdicts :

- `PASS` : observé et vérifié ;
- `PARTIAL` : jouable avec défaut important ;
- `FAIL` : boucle exploitative, confuse ou cassée ;
- `BLOCKED` : prérequis externe absent, scénario non exécutable sans extrapolation ;
- `UNKNOWN` : non testé.

Aucun comportement non observé ne reçoit `PASS`.

## 0.1 Entrée et séquence réversible

L’implémentation exige soit l’ouverture de G4, soit une dérogation founder
explicite. Action 0.4.1 doit au minimum être techniquement stable dans le scope des
challenges utilisés. La présence de ce contrat `IN_REVIEW` ne satisfait aucune
de ces conditions.

Ordre d’implémentation si le gate autorise la slice :

1. `0.5A — Next Clear` : CH01→CH02→CH03 Recruit, first clears et prochain
   objectif, sans dépense de Recherche ;
2. `0.5B — Prove Mastery` : objectifs, records et gates Veteran/Onslaught ;
3. `0.5C — Choose a Sidegrade` : Recherche, cinq blueprints, Research Lab,
   ready check et règles de groupe.

Chaque sous-tranche conserve un état mémoire réinitialisé à la fermeture du
serveur. Elle peut être supprimée ou corrigée sans migration persistante. La
Definition of Done globale exige l’intégration des trois.

---

# 1. Objectif unique

Ajouter une progression temporaire et transparente reliant :

> **Challenge réussi → maîtrise prouvée → recherche obtenue → nouvelle possibilité défensive → nouveau challenge.**

La progression ne doit pas devenir :

> **Répéter la même mission → remplir une barre → augmenter les statistiques → répéter.**

---

# 2. Hypothèse testée

> Trois challenges, trois difficultés, des objectifs de maîtrise explicites et cinq blueprints horizontaux suffisent-ils à créer une anticipation sincère sans produire de grind ?

La tranche doit prouver que :

- le joueur comprend ce qu’il doit faire ensuite ;
- la difficulté ajoute surtout de la complexité ;
- le joueur distingue Maîtrise et Recherche ;
- les first clears ont de la valeur ;
- les blueprints changent la stratégie ;
- les répétitions identiques ont un rendement nul ;
- les amis ne permettent pas de sauter les prérequis personnels.

---

# 3. Principes non négociables

## 3.1 La maîtrise ouvre, la recherche débloque

- la **Maîtrise** est non dépensable ;
- la **Recherche** est dépensable ;
- aucun troisième système de points n’est ajouté.

## 3.2 First clear avant répétition

La majorité de la progression vient :

- des premières réussites ;
- de nouveaux objectifs de maîtrise ;
- de nouvelles difficultés ;
- de nouvelles stratégies.

## 3.3 Aucun rendement infini

Rejouer exactement le même challenge :

- ne redonne pas sa récompense de first clear ;
- ne redonne pas un objectif déjà acquis ;
- peut seulement améliorer un record visible ;
- reste utile pour le plaisir, l’apprentissage et le rematch.

## 3.4 Horizontal avant vertical

Les cinq déblocages sont des variantes avec avantages et coûts.

Aucun blueprint n’est universellement meilleur.

## 3.5 Difficulté par problèmes

Les difficultés supérieures augmentent surtout :

- simultanéité ;
- composition ;
- recouvrement de vagues ;
- pression multi-axe ;
- temps de réaction ;
- gestion de ressources.

Les multiplicateurs statistiques restent faibles.

Les configurations sont appliquées une seule fois à la définition de référence,
jamais sur une vague déjà modifiée. Les comptes utilisent
`math.floor(base * multiplier + 0.5)` en conservant `0` à `0` ; santé, vitesse,
warnings et charges sont bornés par leurs configs avant création runtime. Le
preview et le serveur consomment la même fonction pure de résolution afin
d’éviter un écart UI/gameplay.

## 3.6 Transparence

Avant de lancer, le joueur voit :

- menaces ;
- difficulté ;
- objectifs ;
- récompense de first clear ;
- récompenses déjà obtenues ;
- raison d’un verrou.

## 3.7 Progression du prototype explicitement temporaire

L’UI affiche :

> **Progression de prototype — réinitialisée lorsque le serveur ferme.**

Aucune promesse de sauvegarde n’est faite.

---

# 4. Boucle de progression

1. ouvrir la Campaign Board ;
2. voir le prochain challenge ;
3. consulter la difficulté et les objectifs ;
4. préparer la base ;
5. confirmer le groupe ;
6. réussir ou échouer ;
7. voir les objectifs validés ;
8. obtenir la Recherche de first clear ;
9. débloquer un blueprint ;
10. modifier la forteresse ;
11. tenter le prochain challenge ou améliorer sa maîtrise.

---

# 5. Contenu de campagne

La campagne de prototype contient trois challenges.

## CH01 — First Stand

Objectif d’apprentissage :

- deux routes ;
- construction ;
- Tourelles ;
- Rôdeurs ;
- aucune crise.

## CH02 — First Breach

Objectif d’apprentissage :

- Brutes ;
- Murs ;
- première brèche ;
- autopsie.

## CH03 — Blackout

Objectif d’apprentissage :

- fusil ;
- réparation ;
- Hunters ;
- relais ;
- Downed et revive.

Chaque challenge conserve ses systèmes déjà validés.

---

# 6. Difficultés

```lua
export type DifficultyId = "RECRUIT" | "VETERAN" | "ONSLAUGHT"
```

## 6.1 Recruit

But : apprendre et réussir tôt.

```text
EnemyCountMultiplier = 0.85
EnemyHealthMultiplier = 0.95
EnemySpeedMultiplier = 0.95
WarningDurationMultiplier = 1.25
WaveOverlapSeconds = 0
IntermissionRepairCharge = 30
ThreatPreview = FULL
ExtraSpecialBudget = 0
```

Règles :

- menaces entièrement annoncées ;
- spéciaux introduits séparément ;
- aucune superposition de vagues ;
- aucune mécanique supprimée.

## 6.2 Veteran

But : version de référence.

```text
EnemyCountMultiplier = 1.00
EnemyHealthMultiplier = 1.00
EnemySpeedMultiplier = 1.00
WarningDurationMultiplier = 1.00
WaveOverlapSeconds = 0
IntermissionRepairCharge = 25
ThreatPreview = FULL
ExtraSpecialBudget = 0
```

## 6.3 Onslaught

But : maîtrise avancée par complexité.

```text
EnemyCountMultiplier = 1.15
EnemyHealthMultiplier = 1.05
EnemySpeedMultiplier = 1.05
WarningDurationMultiplier = 0.80
WaveOverlapSeconds = 4
IntermissionRepairCharge = 15
ThreatPreview = PARTIAL_TIMING
ExtraSpecialBudget = 1
```

Règles :

- tous les types d’ennemis restent annoncés ;
- le timing exact de certains spawns est masqué ;
- une vague peut commencer quatre secondes avant la fin complète de la précédente ;
- au maximum un ennemi spécial supplémentaire par challenge ;
- aucune augmentation statistique supérieure aux valeurs configurées ;
- aucun contre caché.

---

# 7. Modificateurs par challenge et difficulté

Le `DifficultyConfig` ajuste un challenge data-driven.

## CH01

### CH01 — Recruit

- 85 % des Rôdeurs ;
- avertissements longs ;
- aucun overlap.

### CH01 — Veteran

- calendrier de référence ;
- deux axes simultanés.

### CH01 — Onslaught

- 15 % de Rôdeurs supplémentaires ;
- quatre secondes d’overlap entre vagues 2 et 3 ;
- pression plus équilibrée entre les axes.

## CH02

### CH02 — Recruit

- un seul Brute dans le challenge ;
- avertissement Brute +25 % ;
- aucun Brute simultané.

### CH02 — Veteran

- Challenge 2 de référence.

### CH02 — Onslaught

- un Brute supplémentaire au budget spécial ;
- overlap de la dernière vague ;
- Rôdeurs légèrement plus rapides ;
- règle de fortification inchangée et annoncée.

## CH03

### CH03 — Recruit

- un Hunter maximum simultané ;
- blackout backup après 26 secondes ;
- warning +25 % ;
- charge intermission 30.

### CH03 — Veteran

- Challenge 3 de référence ;
- backup après 22 secondes.

### CH03 — Onslaught

- un Hunter supplémentaire dans la dernière vague ;
- overlap de la vague 2 vers 3 ;
- warning blackout réduit à 80 % ;
- backup toujours disponible après 22 secondes ;
- charge intermission 15.

---

# 8. Matrice de progression

```text
                    RECRUIT     VETERAN     ONSLAUGHT
CH01 First Stand       ●            ○            ○
CH02 First Breach      🔒           ○            ○
CH03 Blackout          🔒           ○            ○
```

## 8.1 État initial

Débloqué :

- CH01 Recruit.

Tout le reste est verrouillé.

## 8.2 Progression Recruit

- clear CH01 Recruit → CH02 Recruit ;
- clear CH02 Recruit → CH03 Recruit.

## 8.3 Déblocage Veteran

Conditions cumulatives :

- CH01, CH02 et CH03 Recruit terminés ;
- au moins 6 Mastery Marks au total.

Alors :

- les trois versions Veteran sont débloquées.

## 8.4 Déblocage Onslaught

Conditions cumulatives :

- CH01, CH02 et CH03 Veteran terminés ;
- au moins 15 Mastery Marks au total.

Alors :

- les trois versions Onslaught sont débloquées.

## 8.5 Aucun bypass de difficulté

Un challenge verrouillé ne peut pas être lancé par un appel client.

---

# 9. ProgressionSessionData

```lua
export type ChallengeDifficultyKey = string

export type BestRecord = {
    coreHealthRemaining: number,
    completionSeconds: number,
    timesDowned: number,
    relayRestoreSeconds: number?,
    enemiesReachedCore: number,
    defenseDamageRatio: number,
}

export type ProgressionSessionData = {
    progressionSchemaVersion: 1,
    revision: number,
    cleared: {[ChallengeDifficultyKey]: boolean},
    masteryMarks: {[ChallengeDifficultyKey]: {[string]: boolean}},
    bestRecords: {[ChallengeDifficultyKey]: BestRecord},
    researchBalance: number,
    unlockedBlueprints: {[string]: boolean},
}
```

Valeurs initiales :

```text
progressionSchemaVersion = 1
revision = 0
researchBalance = 0
```

Les données de progression :

- sont créées côté serveur au join ;
- ne sont jamais placées dans `leaderstats` ;
- sont répliquées sous forme de snapshot filtré ;
- sont détruites au leave ou à la fermeture du serveur ;
- n’utilisent aucune API de persistance.

Ce type n’est pas un profil joueur autonome et ne contient pas le BuildPlan.
Persistence 0.6.1 l’embarque plus tard sous `ProfileData.progression` après
validation explicite du schéma ; elle ne sérialise jamais directement une table
runtime de `ProgressionSessionData`.

`ChallengeDifficultyKey` est produit uniquement par une fonction pure à partir
de deux IDs whitelistés : `challengeId .. "|" .. difficultyId`. Aucun texte
client libre ne devient une clé.

---

# 10. Maîtrise

## 10.1 Définition

Une Mastery Mark représente un objectif explicite réussi.

Elle est :

- non dépensable ;
- binaire ;
- unique par challenge, difficulté et objectif ;
- accordée uniquement après une victoire ;
- évaluée côté serveur.

## 10.2 Total

```text
Maximum = 27 Mastery Marks
```

Calcul :

- 3 challenges ;
- 3 difficultés ;
- 3 objectifs par cellule.

## 10.3 CH01 — objectifs

### `CORE_GUARDIAN`

```text
CoreHealthRemaining >= 80 %
```

### `CLEAN_LINES`

```text
EnemiesReachedCore <= 2
```

### `FORTRESS_FIRST`

```text
DefenseDamageRatio >= 0.65
```

`DefenseDamageRatio` correspond aux dégâts infligés par Tourelles et systèmes défensifs divisés par les dégâts totaux infligés aux ennemis.

## 10.4 CH02 — objectifs

### `BRUTE_CONTROL`

```text
Every Brute defeated before reaching the core
```

### `LATE_BREACH`

```text
At least 2 Walls present at STARTING
AND
FirstBreachTime >= 120 s OR no breach
```

### `CORE_STANDING`

```text
CoreHealthRemaining >= 65 %
```

## 10.5 CH03 — objectifs

### `FAST_RECOVERY`

```text
Relay manually restored
AND
RelayRestoreSeconds <= 12
```

### `STAY_STANDING`

```text
No player became DOWNED
```

### `CRISIS_RESISTANT`

```text
CoreHealthRemaining >= 60 %
```

## 10.6 Attribution

Après victoire :

1. obtenir le rapport serveur ;
2. évaluer chaque objectif ;
3. comparer au profil ;
4. ajouter uniquement les nouvelles marks ;
5. incrémenter la révision ;
6. déclencher les gates ;
7. envoyer un delta.

Après défaite :

- afficher la progression partielle ;
- n’accorder aucune mark ;
- indiquer les objectifs proches sans les valider.

---

# 11. Recherche

## 11.1 Définition

La Recherche est une ressource temporaire servant exclusivement à débloquer des blueprints de prototype.

## 11.2 Sources

Chaque première victoire d’une cellule Challenge × Difficulty accorde :

```text
FirstClearResearch = 1
```

Maximum théorique :

```text
9 Research
```

## 11.3 Anti-grind

Une cellule déjà clear :

- n’accorde plus de Recherche ;
- même après reconnexion dans le même serveur ;
- même après rematch ;
- même avec une meilleure performance.

## 11.4 Pas d’aléatoire

La Recherche n’est jamais :

- un drop ;
- une probabilité ;
- une roulette ;
- achetable ;
- multipliée par un produit.

## 11.5 Dépenses

Chaque blueprint coûte :

```text
1 Research
```

La transaction est :

- serveur ;
- atomique ;
- idempotente ;
- journalisée localement ;
- non remboursable dans l’UI normale.

Un reset de test existe seulement dans un harness Studio serveur, jamais dans un RemoteEvent de joueur.

---

# 12. Blueprints horizontaux

Les blueprints ajoutent des variantes à la palette de Build Loop 0.3.

Les pièces par défaut restent disponibles.

## BP01 — Reinforced Wall

```text
BlueprintId = BP01_REINFORCED_WALL
Family = Wall
Footprint = 1x2
StructureCost = 3
PowerCost = 0
MaximumHealth = 1100
NavigationCost = 120
```

Avantage :

- résistance élevée.

Coûts :

- budget plus important ;
- attire davantage les Brutes ;
- réduit la quantité de défenses disponibles.

## BP02 — Lightweight Wall

```text
BlueprintId = BP02_LIGHTWEIGHT_WALL
Family = Wall
Footprint = 1x2
StructureCost = 1
PowerCost = 0
MaximumHealth = 380
NavigationCost = 55
```

Avantage :

- canalisation bon marché ;
- couverture large.

Coûts :

- très fragile ;
- faible retard contre Brute.

## BP03 — Precision Turret

```text
BlueprintId = BP03_PRECISION_TURRET
Family = Turret
Footprint = 1x1
StructureCost = 3
PowerCost = 2
MaximumHealth = 350
Range = 38
Damage = 42
Cooldown = 0.85
TargetRule = SPECIAL_THEN_CORE_DISTANCE
NavigationCost = 55
```

Avantage :

- menaces spéciales ;
- grande portée.

Coûts :

- faible cadence ;
- moins efficace contre les essaims.

## BP04 — Suppression Turret

```text
BlueprintId = BP04_SUPPRESSION_TURRET
Family = Turret
Footprint = 1x1
StructureCost = 3
PowerCost = 3
MaximumHealth = 350
Range = 23
Damage = 11
Cooldown = 0.18
TargetRule = CORE_DISTANCE
NavigationCost = 55
```

Avantage :

- Rôdeurs et pression de masse.

Coûts :

- portée courte ;
- énergie élevée ;
- faible impact par tir.

## BP05 — Cryo Trap

```text
BlueprintId = BP05_CRYO_TRAP
Family = SlowTrap
Footprint = 1x1
StructureCost = 2
PowerCost = 2
MaximumHealth = 250
SlowMultiplier = 0.35
EffectDuration = 1.50
NavigationCost = 35
```

Avantage :

- contrôle puissant.

Coûts :

- plus cher ;
- réduit la place disponible pour les dégâts.

## 12.1 Règle de sidegrade

Aucun blueprint ne peut avoir simultanément :

- meilleur coût ;
- meilleure santé ;
- meilleur effet ;
- aucune faiblesse.

## 12.2 Intégration

Après unlock :

- la variante apparaît dans la famille correspondante ;
- la carte affiche les différences ;
- le plan Build passe explicitement du schéma 1 au schéma 2 ;
- `pieceType` reste la famille fermée `Wall`, `SlowTrap` ou `Turret` ;
- `variantId: string?` stocke le BlueprintId exact, `nil` signifiant la pièce
  par défaut ;
- la validation serveur utilise sa configuration ;
- l’autopsie distingue les variantes.

Migration mémoire BuildPlan 1→2 : deep copy, conservation des PieceIds,
positions et rotations, ajout de `variantId = nil`, incrément unique de
`schemaVersion`, puis revalidation complète des footprints et budgets. Aucun
variantId client n’est accepté si le blueprint n’est pas débloqué dans les
données personnelles du propriétaire.

---

# 13. Campaign Board

## 13.1 Accès

Disponible uniquement pendant `PREPARATION` et `REVIEW`.

Ouverture :

- console dans la base ;
- bouton HUD secondaire.

## 13.2 Structure

Afficher une matrice :

- lignes : challenges ;
- colonnes : difficultés.

Chaque cellule affiche :

- verrou ;
- clear ;
- Mastery Marks `0/3` à `3/3` ;
- first-clear Research disponible ou obtenue ;
- meilleur core health ;
- bouton sélectionner.

## 13.3 Détails

Le panneau latéral affiche :

- description ;
- menaces ;
- différences de difficulté ;
- objectifs de maîtrise ;
- récompense ;
- raison du verrou ;
- composition du groupe.

## 13.4 Hiérarchie visuelle

Priorité :

1. prochain challenge recommandé ;
2. difficulté ;
3. objectifs ;
4. récompenses ;
5. records.

Ne pas afficher tous les détails simultanément sur petit écran.

---

# 14. Research Lab

## 14.1 Accès

Uniquement pendant `PREPARATION` et `REVIEW`.

## 14.2 Cartes

Chaque blueprint montre :

- silhouette ;
- famille ;
- valeurs principales ;
- avantage ;
- coût ;
- faiblesse ;
- statut.

## 14.3 Comparaison

Afficher la variante à côté de la pièce par défaut ou d’une variante comparable.

Exemple :

```text
Reinforced Wall
+400 HP
+1 Structure Cost
Higher Brute attraction
```

## 14.4 Unlock

Le bouton est désactivé si :

- déjà débloqué ;
- Recherche insuffisante ;
- mauvais état ;
- requête pending.

---

# 15. Ready Check

## 15.1 Solo

Le propriétaire sélectionne et confirme.

Le challenge démarre après les validations serveur.

## 15.2 Deux joueurs

1. propriétaire sélectionne ;
2. l’autre joueur reçoit la fiche ;
3. il confirme `READY` ;
4. toute modification de challenge ou difficulté annule les ready states ;
5. démarrage seulement si tous les participants sont ready.

## 15.3 Timeout

Pas de démarrage automatique.

Après 20 secondes :

- rappel visuel ;
- le propriétaire peut annuler ;
- aucune pression punitive.

## 15.4 Déconnexion

Si un joueur non propriétaire quitte :

- ready check recalculé.

Si le propriétaire quitte avant STARTING :

- transfert de propriété existant ;
- sélection annulée ;
- nouveau propriétaire doit confirmer.

---

# 16. Participation et progression en groupe

## 16.1 Participants

Le serveur prend un snapshot des joueurs présents à `STARTING`.

## 16.2 Éligibilité

Un joueur reçoit progression seulement s’il :

- est présent dans le snapshot ;
- reste jusqu’à `VICTORY` ou `DEFEAT` ;
- n’est pas marqué comme test client invalide.

Aucun seuil de dégâts n’est imposé au prototype afin de ne pas pénaliser le soutien.

## 16.3 Challenge verrouillé chez un invité

Un invité peut aider l’hôte dans une cellule qu’il n’a pas encore débloquée.

Il reçoit :

- rapport de contribution ;
- expérience de jeu ;
- aucun first clear ;
- aucune Recherche ;
- aucune Mastery Mark ;
- message clair : `Assisted Preview — prerequisites required`.

S’il avait déjà la cellule débloquée, il reçoit sa progression personnelle normalement.

Cette règle permet l’aide sans saut de campagne.

---

# 17. Calcul du résultat

Le résultat de challenge contient :

```lua
export type ProgressionResult = {
    completionId: string,
    challengeId: string,
    difficultyId: DifficultyId,
    victory: boolean,
    wasFirstClear: boolean,
    researchEarned: number,
    newlyEarnedMasteryIds: {string},
    totalMastery: number,
    newlyUnlockedChallenges: {string},
    newlyUnlockedDifficulties: {DifficultyId},
    updatedBestRecord: boolean,
    progressionRevision: number,
    assistedPreview: boolean,
}
```

## Ordre serveur

1. générer une fois `completionId` côté serveur au passage vers le résultat ;
2. figer le rapport de combat et le snapshot des participants ;
3. déterminer la victoire ;
4. vérifier éligibilité et cell unlock personnelle ;
5. calculer first clear, Recherche et Mastery sur une copie ;
6. comparer le best record selon la règle déterministe ;
7. calculer les gates ;
8. valider la copie complète ;
9. committer une seule mutation et une seule révision ;
10. mettre en cache le résultat par `completionId` ;
11. répliquer le même résultat ;
12. émettre les analytics seulement après commit.

Aucune récompense n’est enregistrée avant la fin autoritaire.

Un `completionId` déjà traité renvoie le résultat immuable mis en cache et ne
réévalue aucune récompense. Un même ID associé à un autre challenge, une autre
difficulté ou un autre rapport est un `COMPLETION_CONFLICT` critique.

## Comparaison du meilleur record

Comparer lexicographiquement, dans cet ordre :

1. `coreHealthRemaining` le plus élevé ;
2. `enemiesReachedCore` le plus faible ;
3. `completionSeconds` le plus faible ;
4. `timesDowned` le plus faible ;
5. `relayRestoreSeconds` le plus faible lorsque les deux valeurs existent ;
6. `defenseDamageRatio` le plus élevé.

Une égalité complète ne remplace pas le record et n’incrémente pas la révision.

---

# 18. Écran de progression post-challenge

Après l’autopsie de combat :

## Page 1 — Résultat

- victoire/défaite ;
- core health ;
- contribution.

## Page 2 — Mastery

- trois objectifs ;
- réussi/échoué ;
- nouveaux marks ;
- meilleure progression.

## Page 3 — Progression

- Recherche gagnée ;
- nouvelle cellule débloquée ;
- difficulté débloquée ;
- blueprint disponible.

## Actions

- modifier la base ;
- ouvrir Research Lab ;
- rematch ;
- prochain challenge recommandé.

L’écran doit pouvoir être ignoré rapidement après la première lecture.

---

# 19. Architecture Luau

```text
data/src/shared/Game
├── Config
│   ├── CampaignConfig.luau
│   ├── DifficultyConfig.luau
│   ├── MasteryConfig.luau
│   ├── BlueprintConfig.luau
│   ├── ChallengeConfig.luau
│   └── PieceConfig.luau
├── ProgressionTypes.luau
├── ProgressionRules.luau
├── MasteryRules.luau
├── DifficultyRules.luau
└── GameTypes.luau

data/src/server/Game
├── GameServer.server.luau
└── Services
    ├── ChallengeService.luau
    ├── GridBuildService.luau
    ├── SessionProgressionService.luau
    ├── ProgressionService.luau
    ├── BlueprintService.luau
    ├── ReadyService.luau
    └── GameAnalyticsService.luau

data/src/client
├── DefenseLoopClient.local.luau
└── GameClient
    ├── CampaignBoardController.luau
    ├── ResearchLabController.luau
    ├── ProgressionResultController.luau
    ├── ReadyCheckController.luau
    └── ProgressionHUDController.luau
```

Mappings Script Sync inchangés : `data/src/shared` vers
`ReplicatedStorage/Shared`, `data/src/server` vers
`ServerScriptService/Server` et `data/src/client` vers
`StarterPlayer/StarterPlayerScripts/Client`. Les remotes restent créés par
`GameServer.server.luau` sous `ReplicatedStorage/Game/Remotes` et ne sont pas
gérés comme fichiers synchronisés.

`BlueprintService` ne possède pas un second BuildPlan : il fournit au
`GridBuildService` la whitelist personnelle et la configuration effective des
variants. Budgets, footprints, rendu et routes restent calculés par la chaîne
Build 0.3 migrée au schema 2.

---

# 20. Responsabilités

## SessionProgressionService

- `ProgressionSessionData` mémoire ;
- snapshots ;
- révisions ;
- destruction au leave ;
- aucun DataStore.

## ProgressionService

- matrice ;
- unlocks ;
- first clears ;
- Mastery ;
- best records ;
- résultats.

## BlueprintService

- Recherche ;
- unlocks ;
- validation ;
- intégration Build Loop.

## ReadyService

- sélection ;
- ready states ;
- participants ;
- invalidation.

## GameAnalyticsService

- adapter d’événements ;
- logs structurés en Studio ;
- AnalyticsService dans une future version publiée ;
- aucune décision de gameplay.

---

# 21. Protocoles réseau

## Sélection

```lua
export type SelectMissionRequest = {
    protocolVersion: 1,
    requestId: string,
    challengeId: string,
    difficultyId: DifficultyId,
    progressionRevision: number,
}
```

## Unlock blueprint

```lua
export type UnlockBlueprintRequest = {
    protocolVersion: 1,
    requestId: string,
    blueprintId: string,
    progressionRevision: number,
}
```

## Ready et synchronisation

```lua
export type ReadyRequest = {
    protocolVersion: 1,
    requestId: string,
    selectionRevision: number,
    ready: boolean,
}

export type ProgressionSyncRequest = {
    protocolVersion: 1,
    requestId: string,
    knownProgressionRevision: number,
}
```

Chaque résultat contient `requestId`, `success`, un code fermé, la révision
canonique et uniquement le snapshot/delta filtré nécessaire. Les IDs de requête
sont non vides et limités à 64 octets ; IDs de challenge, difficulté et
blueprint viennent de whitelists fermées et sont limités à 32 octets ; les
révisions sont des entiers finis positifs ou nuls.

## Validation serveur

Pour chaque requête :

- joueur valide ;
- table plate, version et clés exactes ;
- types, longueurs et nombres finis ;
- rate limit puis cache d’idempotence ;
- révision ;
- état ;
- permission ;
- ID connu ;
- gates ;
- solde ;
- opération atomique ;
- révision incrémentée.

Seul le propriétaire sélectionne une mission. Chaque joueur ne peut modifier
que son propre ready state et ses propres blueprints. `RequestProgressionSync`
ne peut demander le profil d’un autre joueur. Une table imbriquée, cyclique,
surdimensionnée ou contenant une Instance est rejetée avant lookup.

## Idempotence

Le serveur garde les 64 derniers request IDs et résultats complets par joueur et
par famille pendant au plus 120 secondes. Un duplicate identique reçoit le même
résultat sans nouvelle mutation ; un ID réutilisé avec un autre payload reçoit
`REQUEST_CONFLICT`. Les caches sont détruits au leave.

Rate limits initiaux par joueur : sync `1/2 s`, sélection `2/s`, ready `4/s`,
unlock `2/s`, avec plafond global `8/s`. Les token buckets sont bornés à deux
secondes de burst et ne créent aucune file de requêtes gameplay.

---

# 22. Sécurité

Le client ne contrôle jamais :

- Maîtrise ;
- Recherche ;
- first clear ;
- difficulté débloquée ;
- objective completion ;
- blueprint unlock ;
- récompense ;
- meilleur record.

Le serveur évalue les objectifs avec :

- CombatStatsService ;
- ContributionService ;
- CrisisService ;
- BuildPlan snapshot ;
- ChallengeService.

Les événements analytics sont émis seulement après une opération serveur réussie.

---

# 23. Analytics de prototype

Le [catalogue Analytics 0.9.1](ANALYTICS_EVENT_CATALOG_0_9.md) est la taxonomie
candidate transversale. Il reste `DRAFT` et ne remplace pas les assertions
locales de cette slice ; aucune émission Roblox officielle n'est autorisée avant
G6 et une décision d'activation versionnée.

## 23.1 Limitation Studio

Les événements Roblox Analytics réels ne sont pas envoyés depuis Studio.

Dans Studio :

- `GameAnalyticsService` écrit des événements structurés ;
- un test recorder les collecte ;
- les assertions peuvent les inspecter.

Dans une future bêta publiée :

- appels `AnalyticsService` côté serveur ;
- jamais côté client.

## 23.2 Funnel progression

```text
PROGRESSION_BOARD_OPENED
MISSION_SELECTED
READY_CONFIRMED
CHALLENGE_STARTED
CHALLENGE_COMPLETED
MASTERY_VIEWED
RESEARCH_EARNED
BLUEPRINT_VIEWED
BLUEPRINT_UNLOCKED
BLUEPRINT_USED
NEXT_CHALLENGE_STARTED
```

## 23.3 Custom events

Limiter les noms et utiliser les custom fields :

```text
ChallengeAttempt
ChallengeResult
MasteryEarned
BlueprintAction
DifficultyAction
```

Custom fields proposées :

- Challenge ;
- Difficulty ;
- PartySize.

## 23.4 Mesures

- taux de sélection par difficulté ;
- taux de victoire ;
- attempts avant clear ;
- first clear vers blueprint unlock ;
- blueprint unlock vers utilisation ;
- variété de blueprints ;
- taux de rematch ;
- progression vers Veteran ;
- progression vers Onslaught ;
- abandon de ready check ;
- assisted previews.

---

# 24. Performance et portée

## Contraintes

- trois challenges ;
- trois difficultés ;
- cinq blueprints ;
- profils mémoire légers ;
- aucune boucle par frame ;
- règles de progression pures ;
- UI construite une fois puis mise à jour par delta ;
- pas de duplication des configurations ;
- pas de DataStore.

## Configs

Les valeurs de difficulté et récompense sont centralisées pour permettre ensuite une migration vers Experience Configs ou experiments sans réécrire le gameplay.

---

# 25. Tests obligatoires

| ID | Test |
|---|---|
| T01 | ProgressionSessionData créé avec valeurs initiales |
| T02 | Aucun DataStore ou API de persistance appelé |
| T03 | Progression reset après nouveau serveur |
| T04 | CH01 Recruit seul débloqué au départ |
| T05 | Clear CH01 Recruit débloque CH02 Recruit |
| T06 | Clear CH02 Recruit débloque CH03 Recruit |
| T07 | Veteran reste verrouillé avant les trois Recruit |
| T08 | Veteran reste verrouillé sous 6 marks |
| T09 | Veteran se débloque avec conditions cumulatives |
| T10 | Onslaught reste verrouillé avant les trois Veteran |
| T11 | Onslaught reste verrouillé sous 15 marks |
| T12 | Onslaught se débloque avec conditions cumulatives |
| T13 | Sélection verrouillée rejetée côté serveur |
| T14 | Recruit applique sa configuration |
| T15 | Veteran applique sa configuration |
| T16 | Onslaught applique sa configuration |
| T17 | Multiplicateurs statistiques restent bornés |
| T18 | Threat preview correcte par difficulté |
| T19 | First clear accorde 1 Research |
| T20 | Repeat clear n’accorde pas de Research |
| T21 | Défaite n’accorde pas de Research |
| T22 | Mastery évaluée seulement après victoire |
| T23 | CH01 objectifs évalués correctement |
| T24 | CH02 objectifs évalués correctement |
| T25 | CH03 objectifs évalués correctement |
| T26 | Mark déjà acquise non dupliquée |
| T27 | Nouvelle mark ajoutée lors d’un meilleur run |
| T28 | Best record remplacé seulement si meilleur selon règle |
| T29 | Unlock ReinforcedWall coûte 1 |
| T30 | Unlock LightweightWall coûte 1 |
| T31 | Unlock PrecisionTurret coûte 1 |
| T32 | Unlock SuppressionTurret coûte 1 |
| T33 | Unlock CryoTrap coûte 1 |
| T34 | Solde insuffisant rejeté |
| T35 | Blueprint invalide rejeté |
| T36 | Requête dupliquée sans double dépense |
| T37 | Révision obsolète déclenche resync |
| T38 | Variantes apparaissent après unlock |
| T39 | Variantes invisibles avant unlock |
| T40 | ReinforcedWall applique coûts et stats exacts |
| T41 | LightweightWall applique coûts et stats exacts |
| T42 | PrecisionTurret applique règle de cible |
| T43 | SuppressionTurret applique cadence et énergie |
| T44 | CryoTrap applique son ralentissement |
| T45 | Budgets Build recalculés côté serveur |
| T46 | Pièce par défaut reste disponible |
| T47 | Campaign Board affiche états exacts |
| T48 | Raisons de verrou lisibles |
| T49 | Solo ready immédiat |
| T50 | Deux joueurs doivent confirmer |
| T51 | Changement de sélection annule ready |
| T52 | Déconnexion recalcule ready |
| T53 | Invité éligible reçoit sa progression |
| T54 | Invité verrouillé reçoit Assisted Preview sans progression |
| T55 | ProgressionResult identique serveur/client |
| T56 | Événements Studio enregistrés localement |
| T57 | Analytics émis après succès, jamais avant |
| T58 | Aucun reward aléatoire |
| T59 | Aucun gain infini par répétition |
| T60 | UI petit téléphone utilisable |
| T61 | UI manette utilisable |
| T62 | Deux clients synchronisés à 150 ms |
| T63 | Dix completions sans duplication ou fuite |
| T64 | Output client et serveur propre |
| T65 | Performance stable du système de progression |
| T66 | Payloads réseau malformés, surdimensionnés, cycliques ou avec révision non finie rejetés |
| T67 | Rate limits et plafond global bornent le spam sans file infinie |
| T68 | completionId dupliqué renvoie le résultat caché sans double reward |
| T69 | completionId réutilisé avec un autre rapport produit COMPLETION_CONFLICT |
| T70 | Comparaison BestRecord déterministe ; égalité complète sans nouvelle révision |
| T71 | BuildPlan schema 1 migre vers 2 sans changer pièces, positions, rotations ou budgets |
| T72 | variantId inconnu ou non débloqué rejeté côté serveur |
| T73 | Preview et runtime utilisent la même résolution pure difficulté/arrondi |
| T74 | 0.5A fonctionne sans Research Lab, dépense ou variante |
| T75 | Leave et fermeture détruisent données, caches et ready states sans DataStore |

---

# 26. Definition of Done

Progression Loop 0.5.1 reçoit `PASS` uniquement si :

1. la prochaine action est toujours visible ;
2. Maîtrise et Recherche sont comprises comme deux systèmes distincts ;
3. la répétition identique ne produit pas de gain infini ;
4. les difficultés ajoutent surtout de la complexité ;
5. les cinq blueprints sont de vraies sidegrades ;
6. le serveur attribue toutes les récompenses ;
7. le groupe ne permet pas de contourner les prérequis ;
8. le prototype affiche clairement l’absence de persistance ;
9. les 75 tests possèdent un verdict ;
10. T02, T04, T09, T12, T13, T19, T20, T22, T26, T36, T40, T42, T45, T50, T54, T59, T60, T62, T66, T67, T68, T69, T70, T71, T72, T73 et T74 sont `PASS` ;
11. aucun comportement non observé ne reçoit `PASS`.

---

# 27. Gate humain

Tester avec 8 à 16 personnes.

## Observer

- comprennent-elles le prochain challenge ?
- distinguent-elles Maîtrise et Recherche ?
- voient-elles pourquoi une difficulté est verrouillée ?
- choisissent-elles un blueprint pour son usage ?
- utilisent-elles réellement le blueprint ?
- rejouent-elles pour une mark manquante ?
- essaient-elles une difficulté supérieure ?
- perçoivent-elles les difficultés comme plus intéressantes ou seulement plus longues ?

## Seuils internes

- 85 % identifient le prochain objectif ;
- 75 % expliquent Maîtrise vs Recherche ;
- 70 % comprennent un verrou sans aide ;
- 70 % choisissent un blueprint selon son tradeoff ;
- 60 % utilisent leur blueprint au challenge suivant ;
- 60 % tentent une nouvelle difficulté après unlock ;
- 50 % rejouent pour une mark spécifique ;
- 40 % commencent un challenge supplémentaire après une récompense ;
- moins de 20 % décrivent la progression comme du grind.

Ces seuils sont internes, pas des benchmarks officiels. Rapporter les comptes
`n/N`, la composition du panel, l’ordre des challenges et les abandons ; avec 8
à 16 personnes, ces pourcentages guident une décision locale sans permettre une
généralisation statistique. Tant que seul le founder teste, le gate humain reste
`UNKNOWN`.

---

# 28. Risques et corrections

## Confusion entre Maîtrise et Recherche

Correction :

- icônes distinctes ;
- verbes distincts : `Prouver` et `Débloquer` ;
- aucun troisième score.

## Grind

Correction :

- first-clear ;
- marks uniques ;
- meilleur record ;
- aucun gain répétitif.

## Difficulté artificielle

Correction :

- comparer durée, frustration et diversité ;
- réduire les multiplicateurs avant de réduire la complexité ;
- préserver télégraphie et backup.

## Sidegrades faussement horizontales

Correction :

- analyser taux de sélection et de victoire ;
- chercher une variante dominante ;
- renforcer les coûts, pas seulement nerfer le plaisir.

## Trop d’UI

Correction :

- contexte ;
- progressive disclosure ;
- matrice compacte ;
- détails sur sélection.

## Aide entre amis frustrante

Correction :

- Assisted Preview clairement annoncé ;
- aucune fausse promesse de récompense ;
- future récompense de soutien reportée à l’économie persistante.

## Reset du serveur

Correction :

- bannière prototype ;
- aucun mot `sauvegardé` ;
- commande Studio de test clairement séparée.

---

# 29. Tranche suivante

La tranche suivante recommandée est :

> **Persistence Loop 0.6.1 — sauvegarde versionnée de la base, de la progression et des blueprints avec migration, session locking, retries, backups et environnement de test séparé.**

L’expédition viendra après la persistance :

> **Expedition Loop 0.7 — une mission de ressources ciblée reliée à un challenge précis.**

---

# 30. Sources officielles

Sources Roblox Creator Hub revalidées pour les affirmations utilisées le
2026-07-15. Elles décrivent des capacités et pratiques de plateforme, pas une
preuve de compréhension, de plaisir ou de rétention pour cette progression.

- [Roblox Discovery](https://create.roblox.com/docs/discovery)

- [Analytics overview](https://create.roblox.com/docs/production/analytics)

- [Get started with analytics](https://create.roblox.com/docs/production/analytics/get-started)

- [Funnel events](https://create.roblox.com/docs/production/analytics/funnel-events)

- [Custom events](https://create.roblox.com/docs/production/analytics/custom-events)

- [Custom fields](https://create.roblox.com/docs/production/analytics/custom-fields)

- [AnalyticsService](https://create.roblox.com/docs/reference/engine/classes/AnalyticsService)

- [Core loops](https://create.roblox.com/docs/production/game-design/core-loops)

- [Onboarding](https://create.roblox.com/docs/production/game-design/onboarding)

- [Quest design](https://create.roblox.com/docs/production/game-design/introduction-to-quest-design)

- [UI/UX design](https://create.roblox.com/docs/production/game-design/ui-ux-design)

- [Client-server boundary](https://create.roblox.com/docs/scripting/security/client-server-boundary)

- [Server authority](https://create.roblox.com/docs/projects/server-authority)

- [Studio testing modes](https://create.roblox.com/docs/studio/testing-modes)

- [Studio MCP](https://create.roblox.com/docs/studio/mcp)
