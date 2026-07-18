# Build Loop 0.3 — Critical Gameplay Fixes

## Lot 1 outcome

Close four validated regressions without changing route selection or Brute
policy:

1. only the current build owner can start a challenge or return from review;
2. build requests are rate-limited before parsing, cache lookup, or replies, and
   malformed request tables have a bounded shallow shape;
3. selecting and moving a piece works again, build actions pass through outside
   the owner's preparation phase, and route previews are not recomputed when the
   relevant placement state did not change;
4. a refused enemy spawn cannot leave the game indefinitely in `DEFENDING`.

## Authority and compatibility

- `AGENTS.md` and the user's current correction request are authoritative.
- `docs/BUILD_LOOP_0_3.md` keeps the observer read-only.
- Existing request IDs, operations, result reasons, plan revisions, owner
  transfer, and valid owner controls remain compatible.
- Cached request results remain idempotent while the caller is inside the
  ingress quota. Excess traffic is intentionally rate-limited before cache
  replay and receives at most one small notification per player per window.
- Lot 1 does not change route-cost, live-routing, Roamer, or Brute behavior.
  Lot 2 below explicitly supersedes that boundary for the audited combat fixes.

## Patch contract

### Security boundaries

- Attacker-controlled sources:
  `RequestStartChallenge`, `RequestReturnToPreparation`, and `BuildRequest`.
- Enforcement:
  `ChallengeService` checks the owner through `GridBuildService`; build request
  ingress consumes quota before any request parsing, cache lookup, or result.
- Bounded request shape:
  four known top-level fields and only the scalar fields applicable to the
  selected operation.
- Legitimate control:
  the current owner can still start near the console, return from `REVIEW`, and
  replay a request ID within quota to receive the cached result.

### Runtime recovery

If wave execution returns while its token and phase are still current, the
challenge transitions through `DEFEAT`, clears active enemies, produces a
review report, and reaches `REVIEW` after the configured outcome delay.
Cancellation caused by a newer run token is not converted into a defeat.

## Files

- `data/src/server/Game/Build/BuildRequestPolicy.luau`
- `data/src/server/Game/Services/GridBuildService.luau`
- `data/src/server/Game/Services/ChallengeService.luau`
- `data/src/client/DefenseLoopClient.local.luau`
- `data/src/client/GameClient/HUDController.luau`
- `data/src/client/GameClient/ReviewController.luau`
- `data/src/client/GameClient/GridBuildController.luau`
- `tests/gameplay/BuildRequestPolicy.spec.luau`

## Verification

Repository checks:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\format.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
& 'C:\Program Files\Git\cmd\git.exe' diff --check
```

Studio scenarios required before a runtime `PASS`:

1. Start a two-client server. Confirm client 1 is `BuildOwnerUserId`.
2. Client 2 fires both challenge remotes directly. Phase must not change and
   both action buttons must remain non-actionable.
3. Client 1 starts from inside the console radius, reaches `REVIEW`, then
   returns to `PREPARATION`. The authoritative store, rendered PieceIds,
   replicated revision/budgets, combat projection, and both client plans must
   match the captured snapshot.
4. Send ten valid build requests inside one rate window, replay one cached
   request inside quota, then exceed the quota with cached and malformed
   requests. Only the first over-limit request may receive a small
   `RATE_LIMITED` result; plan and revision must remain stable. After a newer
   commit, replay an older cached result and verify that no client rewinds to
   its older plan revision. Restart the client controller in the same player
   session and verify that its GUID-scoped request IDs cannot collide with the
   prior controller instance.
5. Select an existing piece, choose Move, move the ghost, and confirm with
   mouse, touch, and gamepad. The PieceId remains stable and revision increases
   once.
6. During `DEFENDING`, as an observer, and after leaving `PREPARATION`, verify
   Return, R, Escape, Delete, DPad, triggers, Z/Y, and gamepad build inputs are
   not consumed by the build controller.
7. Force `EnemyService.spawn` to return false during a wave. The phase must
   leave `DEFENDING`, active enemies must clear, and `REVIEW` must become
   reachable after the configured outcome delay.
8. Inspect both client and server consoles for new errors or warnings.

## Progress

- [x] Finding paths revalidated in the current dirty worktree.
- [x] Implementation complete.
- [x] Pure request-policy regression test added.
- [x] Formatting, lint, and type analysis pass.
- [ ] Studio runtime scenarios pass.

## Lot 2 — Live combat routing

### Lot 2 outcome

- Keep the canonical BuildPlan unchanged while exposing a server-only live
  combat projection containing only defenses whose runtime record and model
  remain alive.
- Compute future enemy paths from that live projection. Existing enemies keep
  the path captured at spawn.
- Resolve a blocking wall by the first live Wall PieceId in the remaining cell
  sequence of that enemy's path, within a cell-count and world-distance bound.
- Record the first breach against the attacker's immutable route rather than an
  anchor-derived wall side.

### Exact lane policies

- A defense belongs to `Left` when its canonical anchor `cellX` is at or left
  of half the configured grid width; otherwise it belongs to `Right`.
- Roamer lane cost is exactly configured base travel cost plus 40 per live Wall
  plus 15 per live SlowTrap. Turrets never enter this cost.
- A Roamer selects the cheaper lane for the configured 75 percent branch and
  the other lane otherwise. Equal costs split on the supplied random roll.
- A Brute selects the lane with the greater sum of current live Wall health.
  The tie cursor alternates only when wall health is equal.
- Wave 3 returns fixed `Left, Right` when both lanes contain at least one live
  Wall and leaves the tie cursor unchanged. Otherwise, the first Brute uses the
  live-health rule and the second receives the other lane.
- Grid A* uses a per-cell base traversal cost plus the Wall/SlowTrap surcharge
  to choose geometry inside the already selected lane. A Turret cell adds no
  surcharge. This internal geometry cost is not the Roamer lane-selection
  cost.

### Exact turret priority

Among living in-range enemies, choose highest normalized distance travelled
along the immutable spawn path. Equal progress chooses higher core damage, then
the lower stable spawn serial. No client value participates in the score.

### Additional files

- `data/src/server/Game/CombatRoutingPolicy.luau`
- `data/src/server/Game/Services/GridRouteService.luau`
- `data/src/server/Game/Services/GridDefenseService.luau`
- `data/src/server/Game/Services/GridEnemyService.luau`
- `data/src/shared/Game/RouteSolver.luau`
- `data/src/shared/Game/Config/RouteConfig.luau`
- `data/src/shared/Game/Config/PieceConfig.luau`
- `tests/gameplay/CombatRoutingPolicy.spec.luau`
- `tests/gameplay/RouteSolver.spec.luau`

### Coexistence cleanup

The active server entrypoint loads only `GridBuildService`,
`GridDefenseService`, `GridEnemyService`, and `GridRouteService`. Repository-wide
reference checks found no runtime, test, Studio manifest, or active snapshot
consumer for their superseded 0.2 names. Script Sync maps the containing
directories rather than requiring those filenames. Remove the inert
`Services/BuildService.luau`, `DefenseService.luau`, `EnemyService.luau`, and
`RouteService.luau` modules, plus the unused pad client
`GameClient/BuildController.luau`.

`GameTypes.luau` and `StateConstants.luau` also become consumer-free after that
removal and duplicate locally typed Grid contracts. Candidate 0.4–0.6 documents
remain `IN_REVIEW`, so their future filenames do not authorize retaining dead
production modules. The historical 0.1/0.2 plans keep their original filenames
as history.

Removed files:

- `data/src/client/GameClient/BuildController.luau`
- `data/src/server/Game/Services/BuildService.luau`
- `data/src/server/Game/Services/DefenseService.luau`
- `data/src/server/Game/Services/EnemyService.luau`
- `data/src/server/Game/Services/RouteService.luau`
- `data/src/shared/Game/GameTypes.luau`
- `data/src/shared/Game/StateConstants.luau`

### Build authority cohesion

`GridBuildService.restore` must replace the authoritative store before rendering
or notifying combat, refresh replicated budget/revision attributes, and send a
full `SYNC` result to clients. This prevents the renderer, combat projection,
server plan, and client plan from diverging if restoration ever receives a plan
other than the current store clone.

Preview and authoritative overlap-box dimensions both derive from
`BuildGridConfig.cellSize`; no independent four-stud literal remains in build
geometry. Grid bounds, schema version, and the configured surface name follow
the same rule. `PieceConfig.maxHealth` is the single health authority for build
pieces; obsolete pad-era budgets, cooldowns, and duplicate route/blocking flags
are removed from active configuration. Ghost validation and path-preview
rebuilding run only when the plan or preview intent changes, rather than on
every rendered frame. The server-owned runtime defense and enemy folders are
cleared authoritatively on initialization/reset so saved or externally inserted
residue cannot become a phantom client plan.

Additional cohesion files:

- `data/src/server/Game/Build/BuildHistory.luau`
- `data/src/server/Game/Build/BuildPlanStore.luau`
- `data/src/server/Game/Build/BuildRenderer.luau`
- `data/src/server/Game/GameServer.server.luau`
- `data/src/server/Game/Services/CombatStatsService.luau`
- `data/src/shared/Game/BuildTypes.luau`
- `data/src/shared/Game/Config/DefenseConfig.luau`

### Additional Studio scenarios

9. Spawn two enemies on a route containing an on-path Wall and a physically
   closer off-path Wall. Both must attack the on-path Wall; the off-path Wall
   health must remain unchanged.
10. Destroy that Wall. The existing enemies must continue on their captured
    path. A later enemy path and route costs must not include the destroyed
    Wall.
11. Place only Turrets on one lane. Roamer route cost must remain unchanged.
    Add one Wall and one SlowTrap and observe increments of 40 and 15.
12. Damage unequal Wall sets before spawning a Brute. It must choose the lane
    with greater current Wall-health sum. Repeated exact ties must alternate.
13. In wave 3, verify one Brute per lane when both lanes have a live Wall; when
    only one lane has Walls, the first Brute uses it and the second uses the
    other lane.
14. Put two enemies in one Turret's range: the farther-along enemy must be
    targeted even when Euclidean core distance would select the other. Verify
    core-damage and spawn-serial tie-breaks.
15. Inspect server/client consoles and MicroProfiler for new errors, warnings,
    path recomputation spikes, or unbounded per-frame work.

### Lot 2 progress

- [x] Live-combat authority and pure policy designed.
- [x] Runtime implementation complete.
- [x] Pure combat-routing and route-solver regression tests added.
- [x] Superseded 0.2 runtime modules removed after zero-consumer verification.
- [x] Restore authority and grid-size derivation made single-source.
- [x] Formatting, lint, and type analysis pass.
- [ ] Studio scenarios 9–15 pass.

## Recovery

All changes are local and file-scoped. Revert only the files listed above if
the patch must be abandoned; do not reset the dirty worktree or overwrite the
founder's pre-existing `GridBuildController` edits.
