# Build Loop 0.3 — Rapport de validation

Date : 2026-07-15  
Place vérifiée : `Place de pasdideepfffff : 07142026_1` (`81801089784379`)  
Verdict global : `PARTIAL`

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
| T25 | PARTIAL | Le démarrage rerend le Wall détruit à 700 PV; le retour complet REVIEW→PREPARATION n'a pas été rejoué après la dernière correction client. |
| T26 | PASS | Le premier joueur, propriétaire `UserId=-1`, place une pièce; révision et budget avancent. |
| T27 | PARTIAL | L'observateur est en mode lecture seule et ses contrôles ne mutent pas le plan; une requête hostile forgée depuis ce client n'a pas été observée. |
| T28 | PASS | Deux clients voient Structure 0→2 et le même modèle après le placement du propriétaire. |
| T29 | PASS | Avec `IncomingReplicationLag=0.15`, deux DELETE identiques produisent exactement révision 1→2 et un seul retrait. |
| T30 | PASS | iPhone 17 Pro 874×402, viewport 749×361 : tap, rotation, confirmation, pan tactile et zoom tactile observés; boutons 44 px. |
| T31 | PARTIAL | Bindings A/X/Y et flèches présents; aucune session avec contrôleur virtuel n'a validé déplacer/annuler de bout en bout. |
| T32 | UNKNOWN | Dix cycles complets consécutifs avec mesure des connexions n'ont pas été exécutés. |

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
  Action System.
- Le geste pinch existe dans le code, mais le zoom mobile prouvé utilise aussi
  deux boutons tactiles explicites afin de rester accessible et testable.
- Aucun DataStore, progression, économie, nouvelle menace ou publication n'a été
  ajouté.

## Gate

Tous les tests critiques exigés par la spécification sont `PASS`, dont T04, T07,
T10, T12, T13, T14, T17, T20, T23, T24, T28, T29 et T30. Le verdict global reste
cependant `PARTIAL` tant que T25, T27, T31 et T32 ne sont pas fermés.

Le gate humain demeure `UNKNOWN`. Le projet conserve donc le
`PASS PROVISOIRE / GO CONDITIONNEL` technique; il ne devient pas une preuve de
compréhension humaine mesurée.
