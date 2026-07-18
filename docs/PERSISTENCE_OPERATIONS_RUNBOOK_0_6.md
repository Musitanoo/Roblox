# Persistence Loop 0.6.1 — Runbook d'opérations et de récupération

| Champ | Valeur |
| --- | --- |
| ID | `OPS-PERSIST-006` |
| Classe | `CONTRACT` opérationnel |
| Cycle de vie | `IN_REVIEW` |
| Version | 0.6.1 |
| Propriétaire / approbateur | Founder/Engineering |
| Scope | Tests DataStore isolés, diagnostic et récupération d'un profil 0.6.1 |
| Dépend de | [Persistence Loop 0.6.1](PERSISTENCE_LOOP_0_6.md) accepté ou dérogé |
| Source | `tmp/docs/PERSISTENCE_OPERATIONS_RUNBOOK_0.6.md`, corrigé le 2026-07-15 |
| Dernière revue | 2026-07-15 |
| Revue suivante | Acceptation 0.6.1, changement d'API DataStore, schéma, incident ou restauration réelle |

> Ce runbook n'active aucun DataStore. Tant que G4 et Persistence 0.6.1 restent
> fermés/`IN_REVIEW`, toutes les opérations réelles sont interdites sauf
> dérogation explicite dans un univers de test isolé. Une lecture de ce document
> ne constitue pas une autorisation opérateur.

## 1. Invariants de sécurité

- Ne jamais activer Studio API Services sur l'univers destiné à la production.
- Ne jamais charger un profil par défaut après une erreur, corruption ou lock.
- Ne jamais restaurer un joueur online ou une clé portant un lock actif.
- Ne jamais copier `lock`, `lockUntil`, `saveId` ou les métadonnées
  opérationnelles d'une ancienne version.
- Ne jamais exposer une opération de recovery par RemoteEvent/RemoteFunction.
- Ne jamais écrire sans migration, validation, UserIds, nouvelle révision,
  nouveau `saveId` et vérification post-écriture.
- Une écriture ambiguë, un lock perdu ou une confirmation absente laisse la
  session `READ_ONLY`/dirty ; aucun faux `SAVED` n'est affiché.

## 2. Autorisation et fiche d'opération

Avant un test réel, consigner dans un artefact privé :

```text
operationId:
operator:
reason:
approvedBy:
universeAlias: Data Test
gameIdSuffix:
placeVersion:
dataStoreName:
scope:
fixturePrefixOrProfileCorrelationId:
expectedSchema: 2
expectedRevision:
snapshotIdAndDate:
startedAtUtc:
rollbackPoint:
```

Ne pas consigner de cookie, clé API, profil complet, metadata sensible ou UserId
brut dans un artefact partagé. Le GameId et les clés complètes restent dans le
canal opérateur privé ; le rapport utilise des suffixes/corrélations opaques.

Arrêter avant toute lecture/écriture si : univers non confirmé, expérience non
privée, production Studio API possiblement active, opérateur non autorisé,
snapshot requis absent, schéma inattendu ou logs/output indisponibles.

## 3. Ordre de preuve

1. Fonctions pures : defaults, migrations, validation, taille et metadata.
2. Adapter mémoire : révisions, locks, queue, UserIds et idempotence.
3. Fault injection : throttle, écriture ambiguë, lock perdu et shutdown.
4. Univers Data Test privé : reconnexion et deux serveurs réels.
5. Recovery sur fixture dédiée.
6. Décision séparée avant toute alpha.

Un niveau échoué bloque les suivants. Un test simulé ne reçoit jamais le verdict
d'un test DataStore réel.

## 4. Scénarios Data Test obligatoires

### 4.1 Reconnexion — T59–T64, T85

1. Charger une fixture nouvelle ou explicitement autorisée.
2. Modifier base, clear, mark, Research, blueprint et record de façon valide.
3. Attendre la confirmation `SAVED` de la révision attendue.
4. Quitter normalement, rejoindre un autre serveur et comparer chaque champ.
5. Répéter dix fois avec révisions monotones et aucune duplication.

### 4.2 Concurrence et lock — T23–T34, T82

1. Le serveur A acquiert le lock et confirme sa propre metadata.
2. Le serveur B tente la même clé ; le callback retourne `nil` et B ne devient
   jamais chargeable.
3. A sauvegarde puis libère uniquement après confirmation de la dernière valeur,
   des UserIds, de la révision et de son lock.
4. B ne peut charger qu'après release confirmée ou expiration réelle.
5. Tester séparément lock perdu et refresh non confirmé : session `READ_ONLY`,
   mutations bloquées, aucun unlock étranger.

### 4.3 Écriture ambiguë — T45–T46, T94, T96

L'adapter écrit puis simule une erreur après commit. Le retry conserve le même
`saveId`, la même working copy et la même révision attendue. Le résultat est
`ALREADY_COMMITTED` uniquement si valeur, metadata, UserIds, lock et révision
correspondent exactement. Sinon : conflit, dirty conservé, aucun `SAVED`.

### 4.4 Migration et corruption — T08–T20, T98–T100

Pour chaque fixture : deep copy, migration pure, validation, invariants, source
inchangée, sérialisation, sauvegarde contrôlée puis reload. Une racine critique
invalide, un futur schéma ou un variant non débloqué bloque sans écrire. Les
normalisations ne concernent que les champs explicitement non critiques.

### 4.5 Shutdown — T31–T34, T84, T96

Tester `PlayerRemoving`, double appel avec `BindToClose`, deux profils en
parallèle et échec de final save. L'unlock n'est écrit qu'avec la dernière valeur
confirmée ; sinon le lock reste et expire naturellement.

## 5. Recovery d'une version — T67–T73, T101–T103

### 5.1 Préconditions

- joueur offline et absence de session active confirmée ;
- opérateur et approbateur autorisés ;
- snapshot/rollback disponible lorsque requis ;
- clé exacte, raison, fenêtre UTC et deadline bornées ;
- aucune mutation client ou gameplay pendant l'opération.

### 5.2 Inspection

1. Paginer `ListVersionsAsync()` dans une fenêtre/une taille bornées.
2. Enregistrer les versions candidates sans supposer un backup par autosave :
   seule la première écriture d'une heure UTC crée le backup de cette heure.
3. Charger la version choisie avec son `DataStoreKeyInfo.Version` exact via
   `GetVersionAsync()`.
4. Migrer et valider une copie en mémoire ; comparer un résumé borné à la latest.
5. Préserver/réassocier `{ userId }` attendu, jamais les anciennes métadonnées
   opérationnelles.

### 5.3 Écriture de restauration

1. Acquérir par `UpdateAsync()` un lock opérateur conditionnel sur la latest ;
   refuser tout lock actif ou révision qui change pendant l'opération.
2. Générer une nouvelle révision monotone, un nouveau `saveId`, `savedAt` et une
   metadata complète sous le seuil interne de 240 caractères.
3. Écrire la valeur restaurée migrée/validée avec les UserIds complets.
4. Relire/vérifier valeur, `DataStoreKeyInfo`, UserIds, schéma, révision,
   `saveId` et lock opérateur.
5. Libérer le lock opérateur uniquement après confirmation ; cette libération
   crée la latest version utilisable.
6. Recharger avec le chemin normal, puis produire le rapport de preuve.

Une erreur après écriture est ambiguë : vérifier le `saveId` avant toute nouvelle
tentative. Une confirmation absente laisse le lock expirer ; ne jamais annoncer
une restauration réussie.

## 6. Snapshot et changement de schéma — T89–T90

Avant une modification de logique de stockage : migrations et recovery `PASS`,
fixtures représentatives non personnelles, snapshot Data Stores Open Cloud du
jour, ID/date observés, clé API à scope minimal hors dépôt, canari privé et plan
de rollback sans downgrade destructif. Le snapshot quotidien ne remplace pas les
versions par clé ni les tests de restauration.

## 7. Nettoyage

- arrêter les playtests et confirmer zéro session/lock fixture actif ;
- supprimer uniquement les clés fixtures explicitement listées ;
- vérifier Data Stores Manager et les budgets ;
- conserver les preuves nécessaires à l'audit, sans profil complet ;
- révoquer/faire expirer les credentials temporaires selon la procédure ;
- noter chaque check `PASS`, `FAIL`, `PARTIAL`, `BLOCKED` ou `UNKNOWN`.

## 8. Preuve minimale d'une exécution

```text
operationId:
scenario/tests:
environment:
schema before/after:
revision before/after:
version source/new latest:
saveId confirmation:
UserIds preserved: PASS/FAIL/UNKNOWN
lock acquisition/release:
snapshot evidence:
expected:
observed:
logs/artifacts:
cleanup:
verdict:
remaining risks:
```

Le runbook complet reçoit un verdict opérationnel seulement quand les scénarios
applicables de T01–T112 sont exécutés. Son existence ne réduit pas le risque
R-006 et ne remplace pas la Definition of Done de Persistence 0.6.1.
