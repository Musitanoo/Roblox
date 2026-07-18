# Build Loop 0.3 — ExecPlan

## Outcome

Replace the eight-pad preparation interface with a data-first, server-authorized
16 × 12 build grid while retaining the validated Defense Loop 0.2 challenge.
The result must support mouse, touch, and gamepad intent; green/red/amber preview;
atomic place/move/rotate/delete; undo/redo/clear; Structure and Power budgets;
revisioned synchronization; deterministic route preview; snapshot restoration;
one owner; and one read-only observer.

## Baseline audit — 2026-07-15

- Repository: `C:\Project\Roblox`, branch `agent/defense-loop-0.2`.
- The complete 0.2 implementation is currently an uncommitted founder-owned
  worktree and must be preserved.
- Static checks pass with zero formatting, lint, parse, or Luau analysis errors.
- The intended Studio place is `Place de pasdideepfffff : 07142026_1`, place ID
  `81801089784379`, in Edit mode with all three Script Sync roots present.
- A fresh 0.2 smoke test observed `PREPARATION`, core 1000, seven services, eight
  pads, empty runtime folders, complete client UI, and Output containing only
  `Defense Loop 0.2 server ready`.
- Incompatible components are deliberately limited to pad-owned `BuildService`,
  pad-owned records in `DefenseService`, fixed-lane cost/path queries in
  `RouteService` and `EnemyService`, pad snapshots in `ChallengeService`, and the
  pad menu in the client.

## Architecture and migration

Shared pure modules:

- `BuildGridConfig` and `PieceConfig` hold immutable tuning.
- `BuildTypes` defines closed operations, reasons, plan, request, and result.
- `GridMath` owns rotated-surface coordinate conversion and footprints.
- `BuildRules` owns mathematical validation, occupancy, and budget calculation.
- `RouteSolver` owns deterministic four-neighbor Manhattan A*.

Server build modules:

- `BuildPlanStore` owns the canonical schema-v1 plan and deep copies.
- `BuildHistory` owns at most 20 reversible snapshot operations.
- `BuildValidator` validates requests in the mandated cheap-to-expensive order.
- `BuildRenderer` rebuilds tagged runtime Instances from plan data using
  `PivotTo()` and standardized template pivots.
- `BuildService` owns owner transfer, rate limiting, idempotence, revisions,
  operations, synchronization, snapshots, and renderer coordination.

Direct integrations:

- `DefenseService` indexes rendered pieces by PieceId and owns runtime health.
- `RouteService` queries the canonical plan and pure solver for route cost/path.
- `EnemyService` follows solver world points and attacks blocking pieces.
- `ChallengeService` snapshots/restores BuildPlan data and gates owner launch.
- The client composes build camera, preview, UI, and input controllers beneath
  the existing Script Sync LocalScript entrypoint.

Studio migration:

- add one `Prototype/BuildSurface` Part centered on the arena;
- remove `Prototype/BuildPads` after the grid path is synchronized;
- move Wall, SlowTrap, and Turret under `GameTemplates/BuildPieces`;
- give each build template a ground-level `BuildPivot` PrimaryPart;
- keep lanes, spawns, core, console, review markers, and enemy templates intact.

## Milestones

1. Add this plan/spec and pure shared modules with deterministic checks.
2. Add canonical plan, history, validation, renderer, protocol, and owner rules.
3. Adapt combat paths and challenge snapshot without changing Challenge 2 content.
4. Replace pad UI with camera, preview, palette, edits, and cross-platform actions.
5. Migrate Studio graybox and verify Script Sync.
6. Execute T01–T32, abuse cases, two clients, latency, mobile, gamepad when
   available, ten cycles, Output, and accessible performance tools.
7. Review the complete diff, record evidence and unknowns, and report the verdict
   without commit or publication.

## Verification and recovery

Use the checked-in format/check scripts and `git diff --check`. Runtime proof must
inspect both server and client DataModels. Disk remains authoritative for synced
scripts; Studio remains authoritative for geometry and templates. The existing
0.2 local recovery snapshot and manifest remain untouched. If the grid migration
cannot preserve Challenge 2, return Studio to Edit, stop at a recoverable source
state, and report `PARTIAL` rather than expanding scope.

## Progress

- 2026-07-15: audit complete; migration boundaries and acceptance strategy fixed.
- 2026-07-15: grille mathématique, plan versionné, validation serveur, historique,
  rendu, routes déterministes, combat adapté et contrôleur client livrés.
- 2026-07-15: migration Studio effectuée sans publication; BuildPads archivés,
  BuildSurface et trois prototypes primitifs installés; Script Sync vérifié.
- 2026-07-15: le Device Emulator a révélé un chevauchement mobile puis l'absence
  de pan tactile; les deux défauts ont été corrigés. Tap, rotation, confirmation,
  pan et zoom tactiles ont ensuite été observés.
- 2026-07-15: le playtest combat a révélé que les modèles rendus étaient nommés
  `PieceId_Type`; `GridDefenseService` indexe désormais l'attribut PieceId et la
  destruction runtime ne modifie plus le plan canonique.
- 2026-07-15: tous les tests critiques spécifiés sont PASS. T25, T27 et T31 sont
  PARTIAL; T32 est UNKNOWN. Verdict global conservé à PARTIAL.
- 2026-07-15: T25, T27, T31 et T32 fermés en playtest. Restauration complète,
  requête hostile observateur, contrôleur virtuel officiel et dix cycles avec
  ennemi runtime sont PASS. T01–T32 sont PASS; verdict technique global PASS.

## Decisions

- Conserver les services 0.2 existants et câbler des modules `Grid*` évite
  d'écraser le travail utilisateur non commité; leur suppression est reportée à
  une tâche de nettoyage bornée.
- Ajouter deux boutons tactiles Zoom+/Zoom- complète le pinch et rend le zoom
  observable et accessible sur petit écran.
- Le gate humain reste UNKNOWN; le résultat technique ne vaut que comme
  PASS PROVISOIRE / GO CONDITIONNEL.
- `StartPrompt.GamepadKeyCode` passe de ButtonX à ButtonSelect afin de supprimer
  le conflit entre lancement du challenge et rotation manette pendant la
  préparation.
