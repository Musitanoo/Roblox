# Roblox Top 1 — Persistence Loop 0.6.1

| Champ | Valeur |
| --- | --- |
| ID | `SLICE-PERSISTENCE-006` |
| Classe | `CONTRACT` |
| Cycle de vie | `IN_REVIEW` |
| Version | 0.6.1 |
| Propriétaire / approbateur | Founder |
| Scope | Profils persistants versionnés, verrouillés et récupérables dans un univers de test isolé |
| Remplace | Aucun |
| Source | `Roblox_Top_1_Persistence_Loop_0.6.md`, fourni par le founder le 2026-07-15 |
| Dernière revue | 2026-07-17 |
| Revue suivante | Entrée G4 ou dérogation explicite, acceptation du schéma, threat model data, migration ou rollback |

> Note d’autorité : ce document enregistre intégralement la spécification candidate.
> Son cycle `IN_REVIEW` ne vaut ni acceptation, ni preuve joueur, ni autorisation
> de franchir un stage gate. Les verdicts non observés restent `UNKNOWN`.
> Les sources officielles utilisées ont été revalidées le 2026-07-15 ; elles
> devront l’être de nouveau avant acceptation si l’API ou la politique change.

## Intégration dans le corpus

| Relation | Source d'autorité |
| --- | --- |
| Vision couverte | [GDD 1.0.3](../Roblox_Top_1_Game_Design_Document_v1.0.md), sections 8 et 17 |
| Schémas producteurs | [Build 0.3](BUILD_LOOP_0_3.md) et [Progression 0.5.1](PROGRESSION_LOOP_0_5.md) acceptés dans le scope persistant |
| Autorisation | [Roadmap G4 et règle de dérogation](00-governance/ROADMAP_AND_STAGE_GATES.md) |
| Risque bloquant | [R-006 — corruption, perte ou duplication](00-governance/RISK_REGISTER.md) |
| Opérations/recovery | [Runbook Persistence 0.6.1](PERSISTENCE_OPERATIONS_RUNBOOK_0_6.md), également `IN_REVIEW` |
| Sources instables | [Registre Roblox officiel](references/ROBLOX_OFFICIAL_SOURCES.md) à revalider avant activation |

Cette intégration ne crée aucun DataStore, univers de test, clé, credential,
snapshot ou procédure opérateur. Tous ces éléments restent à autoriser et à
prouver séparément.

## Journal de révision

- `0.6.1` — callback UpdateAsync et métadonnées bornés, révisions distantes
  strictes, versioning horaire/30 jours explicité, recovery sans ancien lock,
  architecture serveur non répliquée et tests de panne renforcés.
- `0.6.0` — spécification founder enregistrée sans preuve d’implémentation.

**Nom interne : Versioned, Locked, Recoverable Profiles**<br>
**Statut fonctionnel : spécification candidate complète ; implémentation non autorisée par ce seul enregistrement**<br>
**Dépendances : Build Loop 0.3 et Progression Loop 0.5.1 techniquement stables, schémas acceptés**<br>
**Données persistées : base, progression, blueprints et records**<br>
**Environnement de test : univers Roblox privé distinct obligatoire**<br>
**DataStore de production : interdit pendant les tests Studio**<br>
**Publication publique : interdite**<br>
**Trading et achats : interdits**<br>
**Preuve technique et joueur : `UNKNOWN` ; aucun DataStore activé par ce document**

---

# 0. Vérité de validation

Une persistance n’est jamais « parfaite » par déclaration.

Elle reçoit `PASS` uniquement après vérification de :

- chargements réels ;
- sauvegardes réelles ;
- reconnexions ;
- deux serveurs concurrents ;
- erreurs injectées ;
- throttling ;
- fermeture serveur ;
- migrations ;
- données corrompues ;
- récupération d’une ancienne version ;
- absence de perte ou duplication observable.

Verdicts :

- `PASS` : preuve observable obtenue ;
- `PARTIAL` : données généralement sûres mais un scénario critique reste incomplet ;
- `FAIL` : risque d’écrasement, duplication, corruption ou chargement par défaut après erreur ;
- `BLOCKED` : environnement, autorisation ou prérequis externe empêche le scénario ;
- `UNKNOWN` : scénario non exécuté.

Aucun comportement non testé ne reçoit `PASS`.

## 0.1 Entrée, autorisation et ordre de preuve

Persistence 0.6.1 ne peut être implémentée qu’après ouverture de G4 ou dérogation
founder explicite, acceptation du schéma réellement produit par Build 0.3 et
Progression 0.5.1, threat model data et procédure de rollback. Ce contrat
`IN_REVIEW` ne satisfait pas automatiquement ces prérequis.

Ordre obligatoire lorsque l’entrée est autorisée :

1. fonctions pures : defaults, migration, validation, normalisation et taille ;
2. adapter mémoire : locks, révisions, queue et idempotence ;
3. fault injection : throttle, écriture ambiguë, lock perdu et shutdown ;
4. univers privé `Roblox Top 1 — Data Test` : vraies reconnexions, versions et
   deux serveurs ;
5. seulement après tous les tests critiques, décision séparée sur une alpha
   privée. Aucune publication publique n’est incluse.

---

# 1. Objectif unique

Transformer les données temporaires du prototype en profil persistant, versionné, verrouillé et récupérable.

La tranche doit garantir que le joueur retrouve :

- sa forteresse ;
- sa campagne ;
- ses difficultés débloquées ;
- ses Mastery Marks ;
- sa Recherche ;
- ses blueprints ;
- ses meilleurs records.

Elle doit aussi garantir qu’un problème de service ne remplace jamais silencieusement les vraies données par un profil vide.

---

# 2. Principes non négociables

## 2.1 Un profil autonome par joueur

Toutes les données liées sont sauvegardées dans un seul objet DataStore.

Avantages :

- chargement cohérent ;
- sauvegarde atomique ;
- restauration d’une version cohérente ;
- moins de requêtes ;
- pas de base sauvegardée sans la progression correspondante.

## 2.2 Un seul écrivain autoritaire

Seul `ProfilePersistenceService` peut écrire au DataStore.

Les autres systèmes utilisent :

```text
ProfileSession:Read()
ProfileSession:Mutate(reason, callback)
ProfileSession:MarkDirty(reason)
```

Aucun service de gameplay ne doit appeler directement `DataStoreService`.

## 2.3 UpdateAsync uniquement pour les profils

Les opérations de chargement, sauvegarde, refresh de lock et release utilisent `UpdateAsync()`.

`SetAsync()` et `GetAsync()` ne sont pas utilisés dans le chemin normal du profil.

## 2.4 Lock de session atomique

Le lock est acquis dans les métadonnées pendant le même `UpdateAsync()` qui charge les données.

Deux serveurs ne doivent jamais posséder simultanément le même profil en mémoire.

## 2.5 Aucun profil par défaut après erreur

Un profil par défaut est créé uniquement lorsque la valeur DataStore est réellement `nil` dans un `UpdateAsync()` réussi.

Il est interdit de créer un profil par défaut lorsque :

- la requête échoue ;
- le service est indisponible ;
- un lock actif existe ;
- les données sont invalides ;
- le schéma est trop récent ;
- la migration échoue.

## 2.6 Versionner les données, pas le nom du DataStore

Le nom du DataStore reste stable.

Les migrations utilisent `schemaVersion` dans l’objet.

## 2.7 Validation avant utilisation et avant sauvegarde

Toute donnée chargée est :

1. décodée ;
2. migrée ;
3. validée ;
4. normalisée ;
5. seulement ensuite exposée au gameplay.

## 2.8 Erreur critique = lecture bloquée

En cas de corruption critique ou schéma futur :

- ne pas écraser ;
- ne pas démarrer le gameplay ;
- journaliser ;
- fournir un code d’erreur ;
- conserver les versions DataStore pour récupération.

## 2.9 Aucune dépendance au client

Le client ne peut jamais :

- charger ;
- sauvegarder ;
- demander une ancienne version ;
- modifier un lock ;
- choisir une révision ;
- envoyer un profil complet.

## 2.10 La sauvegarde est observable

L’interface peut afficher :

```text
LOADING
SAVED
SAVING
SAVE_DELAYED
DATA_LOCKED
DATA_ERROR
READ_ONLY
```

Le joueur ne doit jamais être trompé sur l’état de ses données.

---

# 3. Environnement de test obligatoire

## 3.1 Univers séparé

Créer une expérience privée distincte :

```text
Roblox Top 1 — Data Test
```

Elle ne doit pas être une place de l’univers de production.

## 3.2 Studio API access

Activer `Enable Studio Access to API Services` uniquement dans cet univers de test.

Ne pas l’activer dans l’expérience destinée à devenir la production pendant la préproduction.

## 3.3 Comptes et clés de test

Préfixes :

```text
player/<UserId>
fixture/<FixtureId>
```

Les fixtures ne partagent jamais les clés des vrais joueurs de test.

## 3.4 Nettoyage

Après les essais destructifs :

- inspecter Data Stores Manager ;
- supprimer les clés de fixtures ;
- conserver seulement les profils nécessaires aux tests de reconnexion ;
- documenter toute restauration manuelle.

---

# 4. DataStore et clés

## Nom

```text
RobloxTop1_PlayerProfiles
```

Ne pas ajouter `_v1`, `_v2` ou une date au nom pour chaque migration.

## Clé

```lua
local key = `player/{userId}`
```

## Scope

Utiliser le scope global par défaut.

Organiser par préfixes plutôt que multiplier les scopes.

## UserIds

Chaque écriture retourne :

```lua
{ userId }
```

dans le champ UserIds de `UpdateAsync()`.

---

# 5. Schéma courant

```lua
export type ProfileDataV2 = {
    schemaVersion: 2,
    dataRevision: number,

    createdAt: number,
    updatedAt: number,
    lastSessionAt: number,

    base: {
        planSchemaVersion: number,
        planRevision: number,
        pieces: {[string]: BuildPieceData},
    },

    progression: {
        progressionSchemaVersion: 1,
        cleared: {[string]: boolean},
        masteryMarks: {[string]: {[string]: boolean}},
        bestRecords: {[string]: BestRecord},
        researchBalance: number,
        unlockedBlueprints: {[string]: boolean},
    },

    audit: {
        totalSessions: number,
        totalSuccessfulSaves: number,
        lastPlaceId: number,
        lastPlaceVersion: number,
        lastSaveReason: string,
    },
}
```

Sous-schémas acceptés à l’entrée de 0.6 :

```text
CURRENT_BUILD_PLAN_SCHEMA = 2
CURRENT_PROGRESSION_SCHEMA = 1
```

`BuildPieceData` du plan schema 2 conserve `pieceType` dans
`Wall | SlowTrap | Turret` et ajoute `variantId: string?`. `variantId` est `nil`
pour une pièce par défaut ou un BlueprintId whitelisté et réellement débloqué.
Les versions de sous-schémas sont migrées avant validation du profil racine.

## Données interdites

Ne pas sauvegarder :

- Instances ;
- CFrame ;
- Vector3 ;
- Color3 ;
- connexions ;
- fonctions ;
- userdata ;
- états runtime de vagues ;
- santé actuelle des structures ;
- munitions de challenge ;
- joueurs Downed ;
- analytics brutes ;
- lock dans la valeur.

Les positions de construction utilisent des coordonnées de grille numériques.

---

# 6. Métadonnées DataStore

Le lock et le minimum opérationnel restent dans les métadonnées. Les noms sont
volontairement compacts : Roblox limite chaque nom de clé à 50 caractères,
chaque valeur à 250 caractères et l’ensemble clé-valeur à 300 caractères.

```lua
export type ProfileMetadata = {
    lock: string?,
    lockUntil: number?,
    schema: number,
    revision: number,
    saveId: string,
    savedAt: number,
}
```

`lock` est limité à 80 caractères, `saveId` à 64, les nombres sont des entiers
finis et le sérialiseur refuse toute metadata estimée au-dessus de 240
caractères afin de conserver une marge sur la limite plateforme. JobId, PlaceId
et diagnostics détaillés restent dans les logs privés ou la section `audit` de
la valeur, pas dans la metadata.

## Règle critique

Chaque callback `UpdateAsync()` retourne toujours :

1. la valeur ;
2. les UserIds ;
3. les métadonnées complètes.

Omettre UserIds ou métadonnées pendant une écriture peut supprimer les
associations précédentes. Même une écriture sans changement fonctionnel retourne
les définitions complètes validées.

## Identifiant de lock

```text
<JobId>:<GUID>
```

Le GUID est généré une fois par session de profil.

---

# 7. Versions supportées

```text
CURRENT_PROFILE_SCHEMA = 2
MINIMUM_SUPPORTED_SCHEMA = 0
```

## V0 — prototype legacy

Forme possible :

```lua
{
    buildPlan = ...,
    cleared = ...,
    masteryMarks = ...,
    bestRecords = ...,
    researchBalance = ...,
    unlockedBlueprints = ...,
}
```

## V1

Forme :

```lua
{
    schemaVersion = 1,
    dataRevision = ...,
    base = ...,
    progression = ...,
}
```

Il manque certains timestamps et champs audit.

## V2 — courant

Schéma complet défini plus haut.

---

# 8. Pipeline de migration

```text
Decode
→ DetectSchema
→ Migrate one version at a time
→ Validate current schema
→ Normalize recoverable fields
→ Expose profile
```

## Modules

```text
ProfileMigrations
├── Migrate_0_to_1
└── Migrate_1_to_2

BuildPlanMigrations
└── Migrate_1_to_2

ProgressionMigrations
└── Validate_1
```

## Règles de migration

- fonctions pures ;
- déterministes ;
- non yield ;
- deep copy ;
- aucune écriture DataStore directe ;
- aucune dépendance à Workspace ;
- chaque étape incrémente exactement d’une version ;
- tests avec fixtures figées ;
- migration idempotente au schéma courant.

Ordre : profil racine, BuildPlan, progression, puis validation croisée. La
migration BuildPlan 1→2 ajoute seulement `variantId = nil` et conserve
PieceId/cellule/rotation ; toute autre transformation exige une nouvelle version
et un test de fixture dédié.

## V0 vers V1

- créer `base` ;
- créer `progression` ;
- conserver les IDs connus ;
- supprimer les champs runtime ;
- initialiser `dataRevision`.

## V1 vers V2

- ajouter `createdAt`, `updatedAt`, `lastSessionAt` ;
- ajouter `audit` ;
- garantir `planSchemaVersion` ;
- normaliser les records.

## Schéma futur

Si :

```text
stored.schemaVersion > CURRENT_PROFILE_SCHEMA
```

alors :

- code `FUTURE_SCHEMA` ;
- aucune migration descendante ;
- aucune sauvegarde ;
- session refusée ;
- récupération ou déploiement d’un serveur compatible requis.

---

# 9. Validation et normalisation

## 9.1 Validation racine

Vérifier :

- table ;
- schemaVersion entier ;
- dataRevision entier >= 0 ;
- timestamps finis et >= 0 ;
- sections `base`, `progression`, `audit`.

## 9.2 Base

Vérifier :

- maximum 64 pièces ;
- IDs string <= 64 caractères ;
- types de pièces whitelistés ;
- coordonnées entières dans la grille ;
- rotation 0–3 ;
- aucune cellule dupliquée ;
- aucune pièce sur zone interdite ;
- footprint valide ;
- budgets recalculés depuis les configs ;
- blueprints utilisés réellement débloqués.

## 9.3 Progression

Vérifier :

- challenge IDs connus ;
- difficulty IDs connus ;
- mastery IDs connus ;
- recherche entière >= 0 ;
- recherche <= limite de sécurité ;
- blueprints whitelistés ;
- best records avec nombres finis et bornés.

## 9.4 Audit

Les valeurs audit non critiques peuvent être normalisées.

## 9.5 Champs inconnus

- les champs inconnus à l’intérieur d’une section connue sont supprimés lors de la normalisation ;
- seuls les champs explicitement optionnels d’audit ou de record peuvent être
  normalisés avec une valeur neutre documentée ;
- un champ critique manquant dans `base`, `cleared`, `masteryMarks`, Recherche
  ou blueprints doit être produit par une migration reconnue, sinon le profil
  devient `CORRUPT_PROFILE` ;
- une structure racine incohérente provoque `CORRUPT_PROFILE`.

## 9.6 Aucune fausse checksum

Ne pas inventer une checksum non cryptographique présentée comme garantie de sécurité.

L’intégrité vient de :

- validation serveur ;
- session lock ;
- révisions ;
- versions DataStore ;
- writes atomiques ;
- récupération.

---

# 10. Profil par défaut

`ProfileDefaults.Create(userId, now)` retourne un nouvel objet profond.

Il ne partage aucune table entre joueurs.

Valeurs :

```text
schemaVersion = 2
dataRevision = 0
researchBalance = 0
unlockedBlueprints = {}
cleared = {}
masteryMarks = {}
bestRecords = {}
base.pieces = {}
audit.totalSessions = 0
audit.totalSuccessfulSaves = 0
```

Le profil par défaut est validé par les mêmes règles que les profils chargés.

---

# 11. États de session

```lua
export type ProfileSessionState =
    "LOADING"
    | "ACTIVE"
    | "SAVING"
    | "RELEASING"
    | "RELEASED"
    | "LOCK_LOST"
    | "LOAD_FAILED"
    | "CORRUPT"
    | "READ_ONLY"
```

## Transitions

```text
LOADING → ACTIVE
LOADING → LOAD_FAILED
LOADING → CORRUPT

ACTIVE → SAVING → ACTIVE
ACTIVE → RELEASING → RELEASED
ACTIVE → LOCK_LOST
ACTIVE → READ_ONLY

LOCK_LOST → RELEASING/RELEASED
READ_ONLY → RELEASING/RELEASED
```

Aucune mutation gameplay n’est acceptée hors `ACTIVE`.

---

# 12. Session locking

## Valeurs initiales

```text
LOCK_TTL_SECONDS = 180
LOCK_REFRESH_INTERVAL_SECONDS = 60
LOAD_LOCK_WAIT_LIMIT_SECONDS = 20
LOCK_SAFETY_MARGIN_SECONDS = 30
```

Les timestamps de lock utilisent `DateTime.now().UnixTimestamp` figé une fois
par opération. Ils servent uniquement à l’expiration opérationnelle, jamais à
calculer une récompense joueur.

## Acquisition

Le chargement utilise `UpdateAsync(key, transform)`.

Avant l’appel, le serveur fige `operationNow`, `ownLockId`, `saveId` et
`userIds = { userId }`. Le callback peut être réexécuté par Roblox : il est pur,
non-yield, sans log, analytics, génération aléatoire, mutation externe ou lecture
du temps. Defaults et migrations reçoivent les valeurs figées.

Dans le transform :

1. lire `currentValue` et `DataStoreKeyInfo` ;
2. extraire UserIds et metadata existants, ou tables vides pour une vraie clé
   absente ;
3. valider forme, tailles et nombres de metadata avant toute décision ;
4. détecter le lock, son propriétaire et son expiration ;
5. si un autre lock actif existe, marquer localement l’issue `LOCKED` et
   retourner `nil` pour annuler l’écriture ;
6. créer un default uniquement si `currentValue == nil`, sinon deep-copy,
   détecter le schéma, migrer puis valider ;
7. construire la metadata complète avec `lock = ownLockId` et
   `lockUntil = operationNow + LOCK_TTL_SECONDS` ;
8. retourner `value, { userId }, metadata`.

Après succès du `pcall`, le résultat n’est accepté que si une valeur et un
`DataStoreKeyInfo` sont retournés, que `keyInfo:GetMetadata().lock` vaut
`ownLockId` et que valeur/metadata concordent sur schema et révision. Un retour
`nil` après conflit est toujours `DATA_LOCKED`, jamais un profil chargeable.

## Lock actif

Un lock est actif si :

```text
metadata.lock existe
AND metadata.lock != ownLockId
AND metadata.lockUntil > operationNow
```

## Lock expiré

Un serveur peut reprendre uniquement un lock expiré.

La reprise est journalisée :

```text
LOCK_TAKEOVER_EXPIRED
```

## Pas de force load public

Aucun bouton joueur ne force le takeover d’un lock actif.

## Attente de lock

Si un autre serveur possède le lock :

- rester sur écran de chargement ;
- retry borné ;
- message `Data still active in another server` ;
- après 20 secondes : quitter proprement avec invitation à réessayer.

Ne jamais charger des valeurs par défaut.

## Refresh

Chaque heartbeat de lock confirmé :

- vérifie `metadata.lock == ownLockId` ;
- prolonge `metadata.lockUntil` ;
- préserve `schema`, `revision`, `saveId`, `savedAt` et UserIds.

Si aucun refresh n’est confirmé avant `lockUntil - LOCK_SAFETY_MARGIN_SECONDS`,
la session passe `READ_ONLY`, bloque les nouvelles mutations et tente une sortie
contrôlée. Elle ne continue jamais à écrire en supposant que le lock existe.

## Lock perdu

Si `metadata.lock` ne contient plus le `ownLockId` :

- état `LOCK_LOST` ;
- mutations bloquées ;
- aucune nouvelle sauvegarde aveugle ;
- message au joueur ;
- sortie contrôlée ;
- journal critique.

---

# 13. File d’opérations par clé

Chaque profil possède une file série.

## But

Empêcher :

- deux autosaves simultanés ;
- un autosave qui écrase une sauvegarde finale ;
- des retries dans le désordre ;
- un release concurrent avec un save.

## API de file d’opérations

```lua
ProfileWriteQueue:Enqueue(operation)
ProfileWriteQueue:GetLength()
ProfileWriteQueue:CancelPendingAutosaves()
ProfileWriteQueue:DrainUntil(deadline)
```

## Priorités

1. `FINAL_SAVE_AND_RELEASE` ;
2. `LOCK_REFRESH` lorsqu’il atteint la marge de sécurité ;
3. `CRITICAL_SAVE` ;
4. `AUTOSAVE` ;
5. `LOCK_REFRESH` normal.

Toute sauvegarde réussie rafraîchit également le lock. La file contient au plus
quatre opérations pending par profil ; au-delà, les autosaves/refreshes
redondants sont coalescés, jamais les releases. Aucune requête client ne peut
ajouter directement une opération à cette file.

## Coalescing

Plusieurs autosaves pending peuvent être regroupés vers la dernière révision.

Une sauvegarde finale supprime les autosaves obsolètes de la file et effectue
save + retrait du lock dans un seul `UpdateAsync` conditionné par `ownLockId`.

Aucune opération déjà active n’est interrompue.

---

# 14. Retry policy

## Wrapper

Toutes les requêtes passent dans :

```lua
DataStoreOperationRunner:Run(operationName, key, callback, policy)
```

## pcall

Chaque requête réseau est dans `pcall`.

## Backoff

Valeurs normales :

```text
Attempt 1 : immédiat
Attempt 2 : 1 s + jitter
Attempt 3 : 2 s + jitter
Attempt 4 : 4 s + jitter
Attempt 5 : 8 s + jitter
Maximum normal attempts : 5
```

Jitter :

```text
0 à 25 % du délai
```

## Erreurs retryables

Traiter comme retryables dans la limite :

- throttling ;
- internal server error ;
- timeout ;
- échec réseau ;
- état d’écriture ambigu.

Chaque tentative respecte aussi le deadline de l’opération et reconsulte le
budget applicable. La classification privilégie les codes/états structurés du
service ; un message inconnu n’est jamais transformé en succès.

## Erreurs non retryables

- profil invalide ;
- schéma futur ;
- lock perdu ;
- clé invalide ;
- erreur de programmation ;
- sérialisation impossible.

## Écriture ambiguë

Chaque sauvegarde utilise un `saveId`.

Si une requête échoue après une écriture potentielle :

- réessayer avec le même `saveId`, le même snapshot cible et la même révision ;
- dans le callback suivant, si `metadata.saveId == saveId` et que la révision
  distante égale la cible, retourner valeur/UserIds/metadata inchangés et
  classifier `ALREADY_COMMITTED` ;
- si le lock ou la révision ne correspondent pas, échouer fermé sans écraser ;
- ne jamais appliquer deux fois une mutation de progression ;
- si l’état reste ambigu après le budget d’essais, conserver dirty, passer
  `READ_ONLY`, ne pas annoncer `SAVED` et ne pas retirer le lock aveuglément.

---

# 15. Budgets et throttling

## Budget-aware

Avant les opérations non urgentes :

- consulter les budgets `StandardRead` et `StandardWrite`, tous deux consommés
  par `UpdateAsync()` ;
- différer si le budget est trop faible ;
- ne jamais lancer une tempête de retries.

`GetRequestBudgetForRequestType()` aide à planifier mais ne garantit pas le
succès : throughput par clé, limites expérience, queues et erreurs réseau restent
possibles. Le code ne modifie pas les limites serveur via
`SetRateLimitForRequestType()` dans cette slice.

## Autosaves

- répartis avec jitter ;
- uniquement un profil par tâche ;
- aucun save par placement de pièce ;
- aucun save par tir ou événement de combat.

## Final save

Le final save possède priorité, mais reste borné par la fermeture du serveur et les limites du service.

## Queue Roblox

Le système interne doit éviter de remplir les queues de requêtes Roblox.

---

# 16. Mutations en mémoire

## API de mutation

```lua
ProfileSession:Mutate(reason, callback)
```

## Règles de mutation

- serveur uniquement ;
- état `ACTIVE` ;
- `reason` appartient à un enum fermé ;
- callback non-yield et sans effet externe ;
- deep copy obligatoire vers une working copy ;
- validation complète de la working copy après callback ;
- commit atomique puis incrément unique de `dataRevision` ;
- `updatedAt` ;
- dirty flag ;
- raison enregistrée ;
- delta répliqué au client.

Si le callback lève une erreur, tente de yield, produit une donnée invalide ou
échoue à la validation, la working copy est jetée : aucune révision, dirty flag,
réplication, analytics ou récompense n’est appliquée. Les effets externes
éventuels ne se déclenchent qu’après commit mémoire réussi.

## Mutations critiques

Sont critiques :

- challenge clear ;
- Mastery Mark ;
- Recherche gagnée ;
- Recherche dépensée ;
- blueprint unlock.

Elles déclenchent un save différé prioritaire.

## Mutations base

Les placements modifient le profil en mémoire mais ne sauvegardent pas à chaque opération.

Déclencheurs de save :

- sortie du mode construction ;
- lancement d’un challenge ;
- 15 secondes après la dernière modification ;
- autosave.

## Transaction de blueprint

Le débit de Recherche et l’unlock se produisent dans une seule mutation mémoire.

Ils sont sauvegardés dans le même objet.

La mutation consomme le `requestId` idempotent défini par Progression 0.5.1. Un
duplicate renvoie le résultat précédent ; un ID conflictuel n’exécute ni débit
ni unlock.

---

# 17. Dirty tracking

```lua
export type DirtyState = {
    isDirty: boolean,
    firstDirtyAt: number?,
    lastDirtyAt: number?,
    reasons: {[string]: boolean},
    lastPersistedRevision: number,
    lastEnqueuedRevision: number,
}
```

Après une sauvegarde de révision N :

- si la session est toujours à N : clean ;
- si la session est > N : reste dirty.

Une requête lente ne doit pas marquer comme sauvegardées des mutations plus récentes.

---

# 18. Cadence de sauvegarde

## Autosave/lock heartbeat

```text
60 secondes + jitter de 0 à 10 secondes
```

Même un profil clean doit refresh son lock.

## Save différé de mutation critique

```text
5 secondes après la mutation
Minimum 15 secondes depuis la dernière écriture réussie
```

## Save de base

```text
15 secondes après la dernière modification
ou sortie du mode Build
ou Challenge STARTING
```

## Pas de spam

Toutes les raisons sont regroupées dans une seule sauvegarde de l’objet complet.

---

# 19. Algorithme de sauvegarde

1. capturer un deep copy de la révision cible ;
2. valider et normaliser ;
3. vérifier la taille ;
4. capturer `expectedRemoteRevision = lastPersistedRevision` ;
5. générer ou réutiliser `saveId` pour cette cible ;
6. attendre la file ;
7. appeler `UpdateAsync()` avec paramètres figés ;
8. vérifier `metadata.lock == ownLockId` ;
9. si saveId et révision cible correspondent, classifier déjà committed ;
10. sinon exiger que valeur et metadata distantes valent exactement
    `expectedRemoteRevision` ;
11. écrire snapshot, UserIds et metadata complète à la révision cible ;
12. vérifier le retour `DataStoreKeyInfo` ;
13. mettre à jour `lastPersistedRevision` seulement après confirmation ;
14. conserver dirty si la session contient une révision plus récente.

## Conflit de révision

Toute révision distante différente de `expectedRemoteRevision`, hors
`ALREADY_COMMITTED` exact, est un conflit — supérieure comme inférieure. Une
différence entre `value.dataRevision` et `metadata.revision` est également
critique.

- ne pas écraser ;
- état `READ_ONLY` ;
- journal `REVISION_CONFLICT` ;
- sortie contrôlée.

---

# 20. Chargement

## UX

Pendant `LOADING` :

- personnage placé dans une zone neutre ou contrôles bloqués ;
- aucune base créée ;
- aucune progression exposée ;
- UI de chargement.

## Succès

Après acquisition, migration et validation :

1. créer `ProfileSession` ;
2. incrémenter `audit.totalSessions` ;
3. mettre à jour `lastSessionAt` ;
4. exposer le snapshot ;
5. construire la base ;
6. activer le gameplay.

## Base active et propriété

Chaque joueur charge son profil autonome, mais un seul BuildPlan est rendu comme
forteresse active : celui du propriétaire serveur courant. Les profils invités
restent chargés pour leur progression personnelle ; leur `base` n’est ni rendue
ni modifiée.

Un transfert de propriétaire :

1. est interdit pendant `STARTING` ou `DEFENDING` ; le snapshot du challenge ne
   change jamais de propriétaire en cours d’assaut ;
2. sauvegarde/release le plan actif de l’ancien propriétaire selon son lifecycle ;
3. attend `PREPARATION`, annule sélection et ready states ;
4. injecte une deep copy validée du plan du nouveau propriétaire dans
   `BuildPlanStore` ;
5. incrémente/réplique la révision runtime sans la confondre avec
   `dataRevision` persistante.

Le serveur ne copie jamais la base de l’hôte dans le profil d’un invité. Si le
transfert ne peut être confirmé, la construction reste bloquée plutôt que de
rendre une base par défaut.

## Échec

Codes :

```text
DATASTORE_UNAVAILABLE
DATA_LOCKED
CORRUPT_PROFILE
FUTURE_SCHEMA
MIGRATION_FAILED
VALIDATION_FAILED
LOAD_TIMEOUT
```

Aucun échec ne crée un profil vide.

---

# 21. Sauvegarde au départ

## PlayerRemoving

1. marquer `RELEASING` ;
2. bloquer les mutations ;
3. annuler autosaves pending ;
4. exécuter `FINAL_SAVE_AND_RELEASE` ;
5. dans le même `UpdateAsync()`, vérifier le lock et la révision, écrire le
   snapshot final si dirty puis retourner metadata complète avec
   `lock = nil`, `lockUntil = nil` ;
6. passer `RELEASED` uniquement après confirmation ;
7. en cas d’échec ou d’ambiguïté, ne jamais effectuer un second unlock aveugle :
   journal critique, aucun faux `SAVED`, lock laissé expirer ;
8. supprimer la session mémoire à la fin du budget de fermeture.

## Double appel

PlayerRemoving et BindToClose peuvent cibler la même session.

Le lifecycle doit garantir une seule release.

---

# 22. BindToClose

## Démarrage

- `serverClosing = true` ;
- refuser les nouveaux profils ;
- bloquer les nouvelles mutations ;
- annuler les autosaves obsolètes.

## Sauvegardes

- lancer les releases en parallèle ;
- une file par clé reste série ;
- utiliser un deadline interne ;
- journaliser les succès et échecs ;
- ne pas appeler Studio production DataStores depuis une place non dédiée.

## Délai interne

```text
SHUTDOWN_DEADLINE_SECONDS = 25
```

C’est un budget interne de conception, pas une promesse de plateforme.

## Résultat

Les locks non libérés expirent naturellement selon le TTL, mais l’échec de release est toujours journalisé comme critique.

---

# 23. Réplication au client

Le client reçoit un snapshot filtré :

```lua
export type PublicProfileSnapshot = {
    revision: number,
    saveState: string,
    base: PublicBuildPlan,
    progression: PublicProgression,
}
```

Ne pas répliquer :

- lock et lockUntil ;
- saveId ;
- métadonnées internes ;
- erreurs brutes ;
- timestamps opérationnels ;
- audit interne complet.

Le client ne renvoie jamais un snapshot modifié.

---

# 24. Limites de taille

## Objectif interne

```text
Warning threshold = 128 KB JSON
Hard internal threshold = 256 KB JSON
```

Ces limites internes restent largement sous la limite maximale du service.

## Contrôle

Avant save :

```lua
HttpService:JSONEncode(profile)
```

Utilisé uniquement pour :

- estimation de taille ;
- détection de valeurs non sérialisables.

Le JSON n’est pas la valeur stockée ; le DataStore stocke la table.

## Dépassement

- warning à 128 KB ;
- save refusé à 256 KB ;
- état `READ_ONLY` ;
- aucune troncature silencieuse.

---

# 25. Versioning et récupération

## Versions natives

Utiliser les versions du DataStore par clé.

Garantie réelle à ne pas surinterpréter : la première écriture d’une clé dans
chaque heure UTC crée le backup versionné de cette heure ; les écritures
suivantes de la même heure écrasent cette version horaire. Les backups remplacés
expirent après 30 jours ; la version la plus récente n’expire pas. Le système ne
promet donc jamais un point de restauration par autosave.

Ne pas créer :

```text
player/123/backup1
player/123/backup2
```

à chaque save.

## Support Recovery Tool

Outil serveur/Studio uniquement :

```text
ProfileRecoveryTool
```

Fonctions :

- lister les versions récentes ;
- afficher date, schema et révision ;
- charger une version ;
- migrer et valider en mémoire ;
- comparer avec la version courante ;
- restaurer via `UpdateAsync()` ;
- créer une nouvelle version courante.

`ListVersionsAsync()` est paginé et borné par fenêtre de temps/page. La version
sélectionnée est chargée avec `GetVersionAsync()` et son
`DataStoreKeyInfo.Version` exact ; aucune approximation par index de page.

## Conditions

- joueur hors ligne ;
- aucun lock actif ;
- opérateur autorisé ;
- confirmation explicite ;
- raison de restauration ;
- logs.

Le recovery acquiert d’abord un lock opérateur conditionnel. Il restaure
uniquement la valeur migrée/validée ; il ne copie jamais `lock`, `lockUntil`,
`saveId` ni d’autres métadonnées opérationnelles d’une ancienne version. Il
réassocie `{ userId }`, génère nouvelle révision/saveId/metadata, écrit une
nouvelle latest version puis retire le lock opérateur après confirmation.

## Pas de RemoteEvent public

Le Recovery Tool n’est jamais exposé aux clients.

## Snapshot opérationnel

Avant toute publication modifiant la logique de stockage :

- créer le snapshot quotidien Data Stores Open Cloud ;
- documenter l’ID/date du snapshot ;
- publier ensuite seulement si migrations et rollback ont été testés.

Le snapshot est une opération privilégiée hors serveur de jeu, avec clé API à
scope minimal, restriction réseau et secret absent du dépôt. Son exécution
reste `UNKNOWN` tant que l’artefact/ID n’a pas été observé.

---

# 26. Corruption et quarantine

## Recoverable

Exemples :

- audit manquant ;
- record optionnel invalide ;
- champ inconnu ;
- blueprint ancien avec alias connu.

Action :

- normaliser ;
- signaler ;
- sauvegarder au prochain cycle avec raison `SANITIZED_LOAD`.

## Critical

Exemples :

- racine non-table ;
- schema absent sans forme legacy reconnue ;
- schéma futur ;
- pièces massivement invalides ;
- Recherche non numérique ;
- migration exception ;
- taille excessive ;
- conflit de révision.

Action :

- aucune écriture ;
- `CORRUPT` ou `READ_ONLY` ;
- gameplay bloqué ;
- récupération via version.

---

# 27. Adapter architecture

## Interfaces

```lua
export type StoredKeyInfo = {
    userIds: {number},
    metadata: ProfileMetadata,
    version: string?,
}

export type UpdateTransform = (
    currentValue: unknown,
    currentInfo: StoredKeyInfo?
) -> (unknown?, {number}?, ProfileMetadata?)

export type AdapterError = {
    code: string,
    retryable: boolean,
    ambiguousWrite: boolean,
}

export type AdapterResult = {
    ok: boolean,
    value: unknown?,
    keyInfo: StoredKeyInfo?,
    error: AdapterError?,
}

export type DataStoreAdapter = {
    UpdateAsync: (self, key: string, transform: UpdateTransform) -> AdapterResult,
    ListVersionsAsync: (
        self,
        key: string,
        minDateMs: number?,
        maxDateMs: number?,
        pageSize: number
    ) -> AdapterResult,
    GetVersionAsync: (self, key: string, version: string) -> AdapterResult,
}
```

L’adapter convertit les tuples/erreurs moteur vers ce résultat fermé ; aucune
chaîne d’erreur brute ne remonte au gameplay. `pageSize` est borné par config et
les pages sont parcourues sous deadline.

## Implémentations

### RobloxDataStoreAdapter

- vrai DataStoreService ;
- environnement Data Test uniquement pendant Studio.

### InMemoryDataStoreAdapter

- tests unitaires ;
- versions simulées ;
- métadonnées ;
- aucune requête réseau.

### FaultInjectingDataStoreAdapter

Peut simuler :

- échec avant write ;
- write réussi puis exception ambiguë ;
- throttling ;
- timeout ;
- lock concurrent ;
- lock expiré ;
- metadata perdue ;
- fermeture serveur.

Le gameplay ne connaît pas l’adapter concret.

---

# 28. Architecture Luau

```text
data/src/shared/Game
├── PublicProfileTypes.luau
├── BuildTypes.luau
├── ProgressionTypes.luau
└── GameTypes.luau

data/src/server/Game
├── GameServer.server.luau
├── Services
│   ├── ProfilePersistenceService.luau
│   ├── ProfileSessionService.luau
│   ├── ProfileMutationService.luau
│   ├── ProfileReplicationService.luau
│   ├── GridBuildService.luau
│   ├── ProgressionService.luau
│   └── PersistenceAnalyticsService.luau
└── Persistence
    ├── PersistenceConfig.luau
    ├── ProfileTypes.luau
    ├── ProfileDefaults.luau
    ├── ProfileValidator.luau
    ├── ProfileNormalizer.luau
    ├── ProfileMigrations.luau
    ├── BuildPlanMigrations.luau
    ├── RobloxDataStoreAdapter.luau
    ├── InMemoryDataStoreAdapter.luau
    ├── FaultInjectingDataStoreAdapter.luau
    ├── ProfileWriteQueue.luau
    ├── DataStoreOperationRunner.luau
    ├── SessionLock.luau
    └── ProfileRecoveryTool.luau

data/src/client
├── DefenseLoopClient.local.luau
└── GameClient
    ├── ProfileLoadingController.luau
    ├── SaveStatusController.luau
    └── ProfileSyncController.luau

tests/persistence/fixtures
├── profile-v0.luau
├── profile-v1.luau
├── profile-v2.luau
├── corrupt-root.luau
├── future-schema.luau
└── oversized-profile.luau
```

Mappings Script Sync inchangés : `data/src/shared` vers
`ReplicatedStorage/Shared`, `data/src/server` vers
`ServerScriptService/Server` et `data/src/client` vers
`StarterPlayer/StarterPlayerScripts/Client`. Les remotes filtrés sont créés par
le serveur sous `ReplicatedStorage/Game/Remotes`. Defaults, schéma complet,
migrations, adapters, locks et recovery restent exclusivement serveur ; seul le
type du snapshot public est répliqué.

Les fixtures sous `tests/` ne sont ni Script Sync ni publiées. Les tests purs et
l’adapter mémoire les consomment depuis le runner de dépôt ; les scénarios du
Data Test universe créent leurs données via des commandes serveur de harness
allowlistées, jamais via un RemoteEvent joueur.

---

# 29. Responsabilités

## ProfilePersistenceService

- DataStore ;
- load ;
- save ;
- release ;
- version recovery ;
- budget ;
- retries.

## ProfileSessionService

- lifecycle ;
- locks ;
- dirty state ;
- autosave ;
- shutdown.

## ProfileMutationService

- API de mutation ;
- validation ;
- revisions ;
- critical save scheduling.

## ProfileReplicationService

- snapshots filtrés ;
- deltas ;
- save states.

## PersistenceAnalyticsService

- métriques ;
- erreurs structurées ;
- jamais de données personnelles brutes dans les logs.

---

# 30. Observabilité

Le [catalogue Analytics 0.9.1](ANALYTICS_EVENT_CATALOG_0_9.md) classe les
événements `PROFILE_*` comme logs/métriques opérationnels privés par défaut.
Ils ne deviennent pas des custom events joueur sans finalité et autorisation G6
séparées.

Événements serveur :

```text
PROFILE_LOAD_STARTED
PROFILE_LOAD_SUCCEEDED
PROFILE_LOAD_FAILED
PROFILE_LOCK_WAIT
PROFILE_LOCK_ACQUIRED
PROFILE_LOCK_TAKEOVER_EXPIRED
PROFILE_LOCK_LOST
PROFILE_MIGRATED
PROFILE_SANITIZED
PROFILE_SAVE_STARTED
PROFILE_SAVE_SUCCEEDED
PROFILE_SAVE_RETRY
PROFILE_SAVE_FAILED
PROFILE_RELEASE_SUCCEEDED
PROFILE_RELEASE_FAILED
PROFILE_RECOVERY_STARTED
PROFILE_RECOVERY_SUCCEEDED
PROFILE_RECOVERY_FAILED
```

Champs :

- `profileCorrelationId` aléatoire par session dans les logs normaux ;
- UserId brut uniquement dans un audit privé à accès restreint lorsque recovery
  ou suppression l’exige ; aucun « hash » maison présenté comme anonymisation ;
- schema ;
- dataRevision ;
- attempt ;
- duration ;
- reason ;
- errorCode ;
- placeVersion.

Ne jamais journaliser le profil complet.

---

# 31. Sécurité

## Client

Aucun RemoteEvent pour :

- save ;
- rollback ;
- lock ;
- migration ;
- Research directe ;
- blueprint direct.

Les remotes gameplay existants déclenchent des mutations serveur.

## Serveur

- whitelist de toutes les IDs ;
- validation de toute mutation ;
- aucun callback UpdateAsync yield ;
- aucun secret dans ReplicatedStorage ;
- aucun recovery command client ;
- aucun default profile sur erreur.

## Duplication

Le lock de session empêche deux serveurs de charger le même profil.

Les transactions de Recherche sont atomiques dans le profil unique.

## Suppression et accès opérateur

Les UserIds sont réassociés à chaque écriture afin que les données joueur
restent identifiables par les outils de plateforme. Aucun endpoint joueur ne
supprime ou exporte un profil dans 0.6. Avant toute alpha publique, une procédure
séparée et revue doit couvrir demande d’accès/suppression, vérification
d’identité, joueur offline, absence de lock, sauvegardes/versioning plateforme,
audit et moindre privilège Open Cloud. Son absence bloque la publication mais
n’empêche pas les fixtures de l’univers Data Test.

---

# 32. Tests unitaires et intégration

## Couche 1 — fonctions pures

- defaults ;
- migrations ;
- validation ;
- normalisation ;
- budgets ;
- size estimation.

## Couche 2 — InMemory adapter

- load/save ;
- revisions ;
- locks ;
- queue ;
- idempotence.

## Couche 3 — Fault injection

- failures ;
- ambiguous writes ;
- throttling ;
- lock loss ;
- shutdown.

## Couche 4 — Data Test universe

- vraies versions ;
- vraie reconnexion ;
- deux serveurs ;
- BindToClose ;
- Data Stores Manager ;
- recovery.

---

# 33. Tests obligatoires

| ID | Test |
|---|---|
| T01 | Aucun DataStore appelé depuis un LocalScript |
| T02 | Seul ProfilePersistenceService accède au DataStore |
| T03 | Profil par défaut validé |
| T04 | Nouveau joueur créé uniquement après UpdateAsync réussi |
| T05 | Échec de load ne crée pas de profil vide |
| T06 | Clé player/UserId correcte |
| T07 | Un seul objet contient base + progression + blueprints |
| T08 | V0 migre vers V1 |
| T09 | V1 migre vers V2 |
| T10 | V2 reste idempotent |
| T11 | Migration ne modifie pas la fixture source |
| T12 | Migration failure bloque le gameplay |
| T13 | Future schema rejeté sans save |
| T14 | Corrupt root rejeté sans save |
| T15 | Champs optionnels invalides normalisés |
| T16 | Pièce inconnue sans alias rejetée ou quarantinée |
| T17 | Alias de pièce legacy migré |
| T18 | Budget base recalculé |
| T19 | Blueprint non débloqué dans le plan rejeté |
| T20 | Valeurs NaN/inf rejetées |
| T21 | Profil >256 KB refusé |
| T22 | Warning >128 KB |
| T23 | Lock acquis atomiquement au load |
| T24 | Deuxième serveur bloqué par lock actif |
| T25 | Deuxième serveur ne reçoit jamais profil par défaut |
| T26 | Lock expiré repris |
| T27 | Lock takeover journalisé |
| T28 | Lock refresh toutes les 60 s et READ_ONLY avant marge si non confirmé |
| T29 | Lock perdu détecté |
| T30 | Lock perdu bloque les mutations |
| T31 | PlayerRemoving sauvegarde puis unlock uniquement après confirmation |
| T32 | BindToClose sauvegarde puis unlock uniquement après confirmation |
| T33 | PlayerRemoving + BindToClose ne double-release pas |
| T34 | Lock reste si release échoue, puis expire |
| T35 | Queue série les opérations d’une clé |
| T36 | Profils différents peuvent sauvegarder en parallèle |
| T37 | Autosaves coalescés |
| T38 | Release prioritaire sur autosave pending |
| T39 | Retry backoff respecte la séquence |
| T40 | Jitter borné |
| T41 | Max attempts normal = 5 |
| T42 | Throttle retryable |
| T43 | Internal error retryable |
| T44 | Validation error non retryable |
| T45 | Ambiguous write détecté via metadata.saveId |
| T46 | Même saveId ne double-applique pas |
| T47 | Budget faible diffère autosave |
| T48 | Aucun save par placement individuel |
| T49 | Exit Build déclenche save différé |
| T50 | Challenge STARTING déclenche save base |
| T51 | First clear marque dirty critique |
| T52 | Blueprint unlock débit + unlock atomiques |
| T53 | Révision augmente à chaque mutation |
| T54 | Save révision N ne clean pas N+1 |
| T55 | Toute révision distante inattendue, supérieure ou inférieure, déclenche conflict |
| T56 | Conflict ou mismatch valeur/metadata n’écrase pas la valeur distante |
| T57 | Snapshot client exclut metadata |
| T58 | Client ne peut pas imposer une révision |
| T59 | Reconnexion retrouve la base |
| T60 | Reconnexion retrouve clears |
| T61 | Reconnexion retrouve marks |
| T62 | Reconnexion retrouve Research |
| T63 | Reconnexion retrouve blueprints |
| T64 | Reconnexion retrouve best records |
| T65 | Destruction runtime ne persiste pas |
| T66 | BuildPlan restauré depuis les données |
| T67 | Première écriture d’une heure UTC crée un backup listable ; writes suivants ne promettent pas un backup distinct |
| T68 | ListVersions récupère les versions |
| T69 | GetVersion charge une ancienne version |
| T70 | Recovery refuse un joueur online |
| T71 | Recovery refuse un lock actif |
| T72 | Recovery valide/migre avant restore |
| T73 | Recovery crée une nouvelle version courante |
| T74 | Studio utilise univers Data Test séparé |
| T75 | Production universe Studio API reste désactivée |
| T76 | Fixture keys séparées |
| T77 | Test cleanup documenté |
| T78 | Save status UI LOADING/SAVING/SAVED |
| T79 | SAVE_DELAYED visible après retries |
| T80 | DATA_ERROR visible sans faux succès |
| T81 | Deux clients ne peuvent pas muter un autre profil |
| T82 | Deux serveurs réels testent le lock |
| T83 | 150 ms de latence n’affecte pas l’intégrité |
| T84 | Fermeture avec deux profils sauvegarde en parallèle |
| T85 | Dix reconnexions sans perte |
| T86 | Cinquante mutations puis save cohérent |
| T87 | Output client/serveur propre |
| T88 | Aucun profil complet dans les logs |
| T89 | Snapshot Open Cloud exécuté et ID/date enregistrés avant changement de logique de stockage |
| T90 | Documentation de rollback complète |
| T91 | Metadata complète reste sous seuil interne 240 et limites par nom/valeur |
| T92 | Callback UpdateAsync répété produit exactement la même sortie sans effet externe |
| T93 | Retour nil pour lock actif ne produit jamais une session chargeable |
| T94 | Succès UpdateAsync sans KeyInfo/lock propre/revision concordante est refusé |
| T95 | File par profil reste <=4 et coalesce sans supprimer FINAL_SAVE_AND_RELEASE |
| T96 | Échec final save n’annonce pas SAVED et laisse le lock expirer |
| T97 | Mutation invalide jette la working copy sans révision, dirty, réplication ou analytics |
| T98 | BuildPlan 1→2 ajoute seulement variantId nil et conserve les budgets |
| T99 | variantId inconnu ou non débloqué bloque load/save sans écrasement |
| T100 | Progression schema 1 et profil schema 2 valident ensemble |
| T101 | Recovery ne copie jamais lock/saveId/metadata d’une ancienne version |
| T102 | Recovery réassocie UserIds, crée saveId/révision et une nouvelle latest version |
| T103 | ListVersions pagination, time bounds et page size respectent deadline |
| T104 | Budgets StandardRead et StandardWrite faibles diffèrent les opérations non urgentes |
| T105 | Adapters, defaults, migrations, locks et recovery absents de ReplicatedStorage |
| T106 | Fixtures tests non synchronisées et commandes Data Test allowlistées serveur |
| T107 | Logs normaux excluent UserId brut, profil complet, payload et metadata sensible |
| T108 | Procédure suppression/accès explicitement bloquante avant alpha publique |
| T109 | Seule la base du propriétaire actif est rendue et mutable |
| T110 | Profil invité ne reçoit jamais une copie de la base hôte |
| T111 | Départ propriétaire en challenge conserve le snapshot puis transfère seulement en PREPARATION |
| T112 | Échec de transfert bloque Build sans charger de base par défaut |

---

# 34. Definition of Done

Persistence Loop 0.6.1 reçoit `PASS` uniquement si :

1. la base, la progression, les blueprints et records survivent à une reconnexion ;
2. aucun échec de load ne crée de données par défaut ;
3. deux serveurs ne peuvent pas charger le même profil ;
4. les migrations sont déterministes et testées ;
5. les données invalides ne sont jamais écrasées ;
6. les writes sont sérialisés et idempotents ;
7. les retries sont bornés et observables ;
8. PlayerRemoving et BindToClose libèrent le lock uniquement après final write confirmé ; un échec le laisse expirer sans faux succès ;
9. la perte de lock bloque les mutations ;
10. une ancienne version peut être restaurée ;
11. Studio utilise un univers de test séparé ;
12. les 112 tests possèdent un verdict ;
13. T04, T05, T09, T13, T14, T23, T24, T25, T29, T31, T32, T33, T35, T45, T46, T52, T54, T55, T56, T59, T63, T67, T72, T73, T74, T75, T82, T84, T91, T92, T93, T94, T95, T96, T97, T98, T99, T100, T101, T102, T104, T105, T109, T110, T111 et T112 sont `PASS` ;
14. aucun comportement non observé ne reçoit `PASS`.

---

# 35. Gate humain

La persistance est surtout technique, mais tester avec 5 à 10 joueurs :

- comprennent-ils l’icône de sauvegarde ?
- attendent-ils une sauvegarde avant de quitter ?
- le message de lock est-il clair ?
- le message d’erreur n’accuse-t-il pas le joueur ?
- retrouvent-ils exactement leur base ?
- remarquent-ils une perte ou duplication ?
- comprennent-ils qu’une sauvegarde est retardée ?

Seuils internes :

- 100 % retrouvent leur profil après reconnexion normale ;
- 100 % ne peuvent pas ouvrir une deuxième session concurrente ;
- 0 perte observable sur dix reconnexions ;
- 0 duplication de Recherche ou blueprint ;
- 80 % comprennent les états SAVING/SAVED ;
- 80 % comprennent le message DATA_LOCKED.

Rapporter les comptes `n/N`, appareils, délais observés et chaque reconnexion.
Les objectifs à 100 % sont des invariants de sécurité du scénario testé, pas une
estimation statistique de fiabilité globale. Tant que seul le founder teste,
l’UX indépendante reste `UNKNOWN`; les tests techniques déterministes et deux
serveurs restent néanmoins obligatoires.

---

# 36. Risques et garde-fous

## Lock trop court

Risque :

- takeover pendant une panne temporaire.

Garde-fou :

- TTL 180 s ;
- refresh 60 s ;
- takeover uniquement après expiry.

## Lock trop long

Risque :

- joueur bloqué après crash.

Garde-fou :

- attente claire ;
- expiry bornée ;
- aucun force-load public.

## Autosave trop fréquent

Risque :

- throttling.

Garde-fou :

- dirty tracking ;
- coalescing ;
- jitter ;
- budget-aware.

## Autosave trop rare

Risque :

- progression récente perdue au crash.

Garde-fou :

- save critique différé ;
- save à la sortie du Build ;
- save au Challenge STARTING ;
- heartbeat.

## Migration destructive

Risque :

- données perdues.

Garde-fou :

- fonctions pures ;
- fixtures ;
- versions natives ;
- snapshot avant déploiement ;
- aucune écriture si migration échoue.

## Profil gigantesque

Risque :

- limites et coûts.

Garde-fou :

- coordonnées de grille compactes ;
- pas d’Instances ;
- seuils internes ;
- un objet cohérent.

## Default-on-error

Risque maximal :

- écrasement irréversible.

Garde-fou :

- règle absolue : default uniquement après UpdateAsync réussi avec valeur nil.

---

# 37. Tranche suivante

Après `PASS` de la persistance :

> **Expedition Loop 0.7 — une mission d’extraction de ressource ciblée, persistée et directement utile à un challenge.**

Le trading reste interdit jusqu’à :

- économie stable ;
- transactions atomiques ;
- anti-duplication ;
- journaux ;
- recovery ;
- tests de sécurité dédiés.

---

# 38. Sources officielles Roblox

Sources Roblox Creator Hub revalidées le 2026-07-15. Les limites et APIs sont
des dépendances instables : revalidation obligatoire avant implémentation,
snapshot, migration, alpha ou publication.

- [Data stores](https://create.roblox.com/docs/cloud-services/data-stores)

- [Implement player data and purchasing systems](https://create.roblox.com/docs/cloud-services/data-stores/player-data-purchasing)

- [Best practices for data stores](https://create.roblox.com/docs/cloud-services/data-stores/best-practices)

- [Data store versioning, listing, and caching](https://create.roblox.com/docs/cloud-services/data-stores/versioning-listing-and-caching)

- [Data store error codes and limits](https://create.roblox.com/docs/cloud-services/data-stores/error-codes-and-limits)

- [DataStoreService](https://create.roblox.com/docs/reference/engine/classes/DataStoreService)

- [DataStoreService:GetRequestBudgetForRequestType](https://create.roblox.com/docs/reference/engine/classes/DataStoreService/GetRequestBudgetForRequestType)

- [DataModel:BindToClose](https://create.roblox.com/docs/reference/engine/classes/DataModel/BindToClose)

- [Data Stores Manager](https://create.roblox.com/docs/cloud-services/data-stores/data-stores-manager)

- [Open Cloud data stores](https://create.roblox.com/docs/cloud/guides/data-stores)

- [Access control and confidentiality](https://create.roblox.com/docs/scripting/security/access-control)

- [Studio MCP](https://create.roblox.com/docs/studio/mcp)
