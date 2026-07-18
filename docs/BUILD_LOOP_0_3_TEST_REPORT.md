# Build Loop 0.3 — Rapport de validation

| Champ | Valeur |
| --- | --- |
| ID | `EVIDENCE-BUILD-003` |
| Classe | `EVIDENCE` |
| Cycle de vie | `RECORDED` |
| Propriétaire | Engineering |
| Scope | Exécution historique T01–T32 du build et de la place observés le 2026-07-15 |
| Contrat testé | [BUILD_LOOP_0_3.md](BUILD_LOOP_0_3.md) v0.3.0 |
| Source | Playtests Studio, sorties client/serveur et scénarios consignés ci-dessous |
| Date de preuve | 2026-07-15 |
| Place vérifiée | `Place de pasdideepfffff : 07142026_1` (`81801089784379`) |
| Environnement | Roblox Studio local ; solo, Device Emulator et Server & Clients ; version Studio exacte non enregistrée |
| Révision testée | Commit/build exact non enregistré ; preuve bornée à la place et aux observations ci-dessous |
| Artefacts | Matrice T01–T32 et observations de ce rapport ; logs bruts non versionnés |
| Dernière revue | 2026-07-17 |
| Revue suivante | Addendum après toute modification runtime ou nouvelle exécution |
| Verdict global | `PASS TECHNIQUE` |

> Addendum documentaire du 2026-07-17 : le libellé global historique `PASS` est
> normalisé en `PASS TECHNIQUE`. Aucune observation ni ligne T01–T32 n'a été
> réécrite, et ce rapport ne couvre pas les modifications ultérieures du
> worktree.

## Résultat livré

La construction par huit BuildPads est remplacée par une grille mathématique
16 × 12 de cellules de quatre studs. Le serveur possède le plan versionné, les
budgets Structure/Énergie, l'occupation, les mutations, l'historique, le rendu,
les routes et les snapshots. Le client fournit caméra, fantôme, prévisualisation
des routes et commandes souris, tactiles et manette.

La place Studio contient un seul `BuildSurface`, aucun Part par cellule, et des
prototypes primitifs lisibles pour Wall, SlowTrap et Turret. Les anciens
BuildPads ont été conservés dans `ServerStorage/LegacyDefenseLoop02` comme
solution de retour arrière et ne sont plus actifs dans `Workspace/Prototype`.

## Matrice T01–T32

| ID | Verdict | Preuve observable |
|---|---|---|
| T01 | PASS | PREPARATION active la construction; DEFENDING la verrouille et refuse les mutations. |
| T02 | PASS | Cellules (1,1), (8,6) et (16,12) converties monde→cellule sans dérive. |
| T03 | PASS | Cinq points de part et d'autre du centre de (8,6) restent stables dans la même cellule. |
| T04 | PASS | Wall 1×2 validé en R0/R90; placement tactile observé avec attribut serveur `Rotation=1`. |
| T05 | PASS | Wall R90 en (16,12) refusé `OUTSIDE_GRID`. |
| T06 | PASS | Placement en cellule réservée refusé `FORBIDDEN_CELL`. |
| T07 | PASS | Superposition avec une pièce du plan refusée `OCCUPIED`. |
| T08 | PASS | Part serveur temporaire sur (12,10) : refus `WORLD_OVERLAP`, puis sonde supprimée. |
| T09 | PASS | 12 Walls = Structure 24; le treizième est refusé `STRUCTURE_LIMIT`. |
| T10 | PASS | Quatre Turrets = Énergie 8; la cinquième est refusée `POWER_LIMIT`. |
| T11 | PASS | Sous 500 ms entrant, `EN ATTENTE SERVEUR` apparaît, puis le modèle serveur arrive et Structure passe 0→2. |
| T12 | PASS | Deux requêtes du même `requestId` n'avancent la révision qu'une fois. |
| T13 | PASS | Une révision de base obsolète est refusée et le plan canonique est renvoyé. |
| T14 | PASS | Move : révision +1, même PieceId, même nombre de pièces, nouvelle cellule. |
| T15 | PASS | Rotate : révision +1, même PieceId, footprint et attribut rotation mis à jour. |
| T16 | PASS | Delete retire la pièce et restitue exactement Structure/Énergie. |
| T17 | PASS | Undo puis Redo restaurent plan, révision et budgets dans les deux sens. |
| T18 | PASS | Clear All vide le plan; Undo restaure les six pièces et leurs budgets. |
| T19 | PASS | Le preview et le coût de route changent lorsqu'un Wall est ajouté. |
| T20 | PASS | `GridRouteService` et `RouteSolver` renvoient les mêmes chemins/coûts déterministes pour le plan. |
| T21 | PASS | Sur 1 000 choix seedés avec la gauche fortifiée : 740 Rôdeurs choisissent la droite. |
| T22 | PASS | Avec la gauche fortifiée, le Brute choisit la gauche. |
| T23 | PASS | Mutation en DEFENDING refusée `WRONG_STATE`, sans changement de révision. |
| T24 | PASS | Destruction runtime d'un Wall : runtime vide, mais plan/révision/budget intacts. |
| T25 | PASS | Wall `P00001` détruit au runtime puis restauré à 700/700 PV en REVIEW et après REVIEW→PREPARATION; révision 1, Structure 2, noyau 1000, zéro ennemi et marqueur masqué. |
| T26 | PASS | Le premier joueur, propriétaire `UserId=-1`, place une pièce; révision et budget avancent. |
| T27 | PASS | En Server & Clients, l'observateur `UserId=-2` a forgé un PLACE contre l'owner `-1`; le serveur est resté à révision 0, zéro défense et Structure 0. |
| T28 | PASS | Deux clients voient Structure 0→2 et le même modèle après le placement du propriétaire. |
| T29 | PASS | Avec `IncomingReplicationLag=0.15`, deux DELETE identiques produisent exactement révision 1→2 et un seul retrait. |
| T30 | PASS | iPhone 17 Pro 874×402, viewport 749×361 : tap, rotation, confirmation, pan tactile et zoom tactile observés; boutons 44 px. |
| T31 | PASS | Émulateur de contrôleur Studio : D-pad déplace le ghost de X=-30 à -22, X tourne 0→90°, A place `P00001` en (3,1) R90, B masque le ghost et A après annulation ne change pas la révision 1. |
| T32 | PASS | Dix cycles avec un ennemi runtime chacun : DEFENDING→DEFEAT→REVIEW→PREPARATION, ennemi 1→0, noyau 0→1000; Runtime 2, Prototype 125, Replica 6, une UI et un ghost restent constants. |

## Preuves complémentaires

- Multi-client : serveur avec deux joueurs (`-1`, `-2`), propriétaire unique,
  observateur synchronisé.
- Latence : réglage client lu à `0.15`; suppression dupliquée acceptée une seule
  fois (`REV 2 DEF 0`).
- Mobile : le pan tactile a déplacé la caméra de
  `(54.331,72.100,43.714)` à `(43.840,72.100,52.164)`; Zoom+ l'a rapprochée
  d'une magnitude `99.202` à `88.308`.
- Combat : après correction de l'indexation par attribut PieceId, un Wall a été
  détruit par le Brute, FirstBreach a été enregistré une seule fois et le plan
  n'a pas muté.
- Restauration : le Wall `P00001`, supprimé du dossier runtime avant le départ,
  réapparaît avec le même identifiant et 700/700 PV en REVIEW puis en
  PREPARATION; le plan reste à la révision 1 et le budget à Structure 2.
- Sécurité deux clients : le client observateur a imprimé
  `T27_OBSERVER_SENT -2 -1 0`; le serveur a confirmé
  `T27_SERVER 2 -1 0 0 0`, soit deux joueurs, owner -1, révision 0, zéro
  défense et Structure 0 après la requête forgée.
- Manette : l'Émulateur de contrôleur officiel a été utilisé directement. Le
  conflit entre `ButtonX` et `StartPrompt` a été retiré en affectant le prompt
  physique à `ButtonSelect`; X reste réservé à la rotation pendant la
  construction.
- Endurance : chacun des dix cycles accélérés a réellement créé un Rôdeur,
  enregistré `EnemiesReachedCore=1`, produit DEFEAT/REVIEW, puis nettoyé le
  runtime et restauré PREPARATION. La configuration accélérée n'a servi qu'au
  playtest et les valeurs Challenge 2 normales ont ensuite été resynchronisées.
- Output des playtests solo finaux : uniquement `Build Loop 0.3 server ready`;
  aucun nouvel avertissement ou erreur.
- Vérifications locales : `format.ps1 -Check`, `check.ps1` et
  `git diff --check` terminent avec code 0; Selene rapporte 0 erreur et 0 warning;
  Luau LSP rapporte PASS.

## Écarts connus

- Les anciens modules 0.2 restent sur disque pour préserver le diff utilisateur;
  le serveur utilise les modules `Grid*`. Cette dette doit être nettoyée dans une
  tâche bornée après stabilisation, sans double gestion au runtime.
- `ContextActionService` est utilisé pour la manette au lieu du nouvel Input
  Action System; le parcours exigé par T31 est néanmoins observé de bout en bout.
- Un essai de stress non retenu dans les verdicts a volontairement injecté 24
  ennemis presque simultanés : la limite active a refusé un spawn et la phase a
  pu rester DEFENDING. Le Challenge 2 normal n'utilise pas ce rythme, mais la
  gestion future d'un refus de spawn devra terminer ou reporter proprement la
  vague avant toute augmentation de densité.
- Le geste pinch existe dans le code, mais le zoom mobile prouvé utilise aussi
  deux boutons tactiles explicites afin de rester accessible et testable.
- Aucun DataStore, progression, économie, nouvelle menace ou publication n'a été
  ajouté.

## Gate

T01 à T32 sont désormais `PASS`, y compris tous les tests critiques exigés par
la spécification. Le verdict technique global de Build Loop 0.3 est
`PASS TECHNIQUE`.

Le gate humain demeure séparément `UNKNOWN`. Ce PASS technique ne devient pas
une preuve de compréhension, de confort ou de rematch volontaire mesurés auprès
de joueurs non briefés; l'autorisation produit reste un
`PASS PROVISOIRE / GO CONDITIONNEL` jusqu'à G3.
