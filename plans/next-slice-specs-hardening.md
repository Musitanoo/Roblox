# Next Slice Specifications 0.4–0.6 — ExecPlan

## Outcome

Transformer les trois spécifications candidates Action 0.4, Progression 0.5 et
Persistence 0.6 en contrats d'implémentation cohérents, bornés et vérifiables,
sans autoriser leur implémentation ni modifier le runtime. Les documents doivent
respecter l'architecture Script Sync réelle, expliciter leurs gates, fermer les
ambiguïtés de protocole et rendre la persistance récupérable sans promesse
supérieure aux garanties Roblox observables.

Ce plan autorise uniquement des changements Markdown dans les trois contrats,
leur navigation, leur registre et ce plan. Il n'autorise aucun DataStore, aucune
publication, aucun RemoteEvent, aucun gameplay et aucune modification Studio.

## Inputs

- `docs/ACTION_LOOP_0_4.md`.
- `docs/PROGRESSION_LOOP_0_5.md`.
- `docs/PERSISTENCE_LOOP_0_6.md`.
- Constitution produit, GDD, roadmap, registre des risques et standard
  documentaire acceptés.
- Contrats/code exécutables Defense 0.2 et Build 0.3.
- Documentation Roblox Creator Hub actuelle sur Input Action System, frontière
  client-serveur, AnalyticsService, DataStoreService, métadonnées, limites et
  versioning.

## Acceptance criteria

1. Les trois contrats portent une révision patch et un journal de révision.
2. Les dépendances et gates distinguent enregistrement, acceptation,
   autorisation d'implémentation, preuve technique et preuve joueur.
3. Action 0.4 séquence ses hypothèses afin qu'un défaut puisse être attribué à
   une tranche réversible ; ses états s'intègrent aux phases existantes.
4. Tous les protocoles client déclenchables bornent forme, longueur, nombres,
   fréquence, cache d'idempotence et réponse dupliquée.
5. Progression 0.5 définit les transactions et résultats de façon atomique,
   déterministe et compatible avec Build 0.3 puis Persistence 0.6.
6. Persistence 0.6 définit précisément le callback `UpdateAsync`, la limite de
   métadonnées, les écritures ambiguës, les conflits de révision, les versions
   horaires/30 jours et une récupération qui ne restaure jamais un ancien lock.
7. Les arbres d'architecture utilisent exclusivement les mappings réels
   `data/src/shared`, `data/src/server` et `data/src/client`.
8. Les tests obligatoires couvrent les nouvelles invariants critiques et la
   Definition of Done les référence sans transformer un skipped en `PASS`.
9. Les sources officielles utilisées sont revalidées et datées ; aucune
   recommandation Roblox n'est présentée comme preuve joueur.
10. UTF-8, titres uniques, liens relatifs, registre documentaire,
    `git diff --check` et `scripts/check.ps1` passent.

## Intended files

- Modifier `docs/ACTION_LOOP_0_4.md`.
- Modifier `docs/PROGRESSION_LOOP_0_5.md`.
- Modifier `docs/PERSISTENCE_LOOP_0_6.md`.
- Modifier `docs/00-governance/DOCUMENT_REGISTER.md` et `docs/README.md` si la
  navigation ou les versions l'exigent.
- Modifier ce plan avec les décisions, preuves et le statut final.

## Milestones

1. Auditer les contrats contre le code, les gates et les sources officielles.
2. Corriger Action 0.4 et son protocole d'action.
3. Corriger Progression 0.5 et son contrat transactionnel.
4. Corriger Persistence 0.6, migrations, locks, retries et recovery.
5. Effectuer une revue croisée et toutes les vérifications documentaires.

## Verification

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
git diff --check
git status --short
```

Ajouter un audit déterministe des liens relatifs, de l'UTF-8, des titres et du
registre. Studio n'est pas applicable parce que ce plan ne change aucun fichier
runtime.

## Recovery

Les trois fichiers sources fournis par le founder restent disponibles dans le
dossier Downloads et servent de référence de contenu. En cas de conflit,
préserver le contrat accepté le plus étroit, marquer l'écart et ne jamais
élargir un gate silencieusement. Aucun changement utilisateur hors de la liste
de fichiers prévue ne doit être modifié ou supprimé.

## Progress

- 2026-07-15 : audit initial du dépôt, des trois contrats et des APIs Roblox
  officielles effectué ; chemins d'architecture fictifs, états ambigus,
  protocoles insuffisamment bornés et garanties de versioning à préciser.
- 2026-07-15 : Action 0.4.1, Progression 0.5.1 et Persistence 0.6.1 durcis ;
  sous-gates, protocoles, transactions, migrations, locks, retries et recovery
  alignés sur l'architecture et les garanties observables.
- 2026-07-15 : revue croisée terminée ; 63, 75 et 112 tests continus et uniques,
  blocs Markdown équilibrés, titres uniques et liens relatifs valides.

## Decisions

- Conserver les trois contrats en `IN_REVIEW` : le perfectionnement
  documentaire n'est pas une acceptation produit ni une dérogation de gate.
- Réviser les documents en 0.4.1, 0.5.1 et 0.6.1 sans renommer leur identité de
  slice.
- Préserver le scope fonctionnel proposé, mais le séquencer en sous-gates pour
  réduire l'incertitude et permettre un arrêt réversible.

## Status

Complete. Ce statut clôt le travail documentaire de ce plan ; les trois
contrats restent `IN_REVIEW`, leur implémentation n'est pas autorisée et leur
preuve joueur reste `UNKNOWN`.
