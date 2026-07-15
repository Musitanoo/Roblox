# Defense Loop 0.2 — ExecPlan

## Status and outcome

Implementation is complete in the synchronized source roots and the active
Studio graybox. The technical acceptance suite is observed; the separate human
gate with unbriefed players remains outside this implementation run.

The previous minimal two-route graybox milestone remains recoverable in Git and
in the local Studio recovery snapshot. The founder's current 0.2 specification
supersedes its four-pad/four-service/90–150-second constraints.

Deliver the smallest authoritative implementation that proves:

> architectural weakness → factual autopsy → modification → voluntary rematch

The product contract is `docs/DEFENSE_LOOP_0_2.md`. No commit or publication is
authorized for this execution.

## Baseline audit — 2026-07-15

- Repository: `C:\Project\Roblox`, branch `agent/defense-loop-0.2`.
- Worktree was clean before this plan update.
- One intended Studio instance was selected in Edit mode.
- Native Script Sync maps the three authoritative disk roots documented in
  `AGENTS.md`; no nested duplicate mapping was found.
- Present: 0.1 state machine, server-validated four-pad placement, snapshot and
  reset, BasicZombie, Wall, Turret, and the readability-only Lane02/Spawn02/
  Brute milestone.
- Missing: the exact 96 × 72 hierarchy, eight pads, build budget, SlowTrap,
  two-route runtime choice, Challenge 2, three required services, current-run
  autopsy, new remotes, and 0.2 client UI.
- Incompatible: the old four-pad world, single-lane `EnemyService`, combat-owned
  `BuildService`, 500-health core config, old waves, and monolithic 0.1 UI.
- Overwrite audit: no uncommitted user file was identified. Studio migration
  replaces only project-owned prototype geometry/templates. The ignored 0.1 and
  0.2 graybox place files plus tracked manifests provide recovery.

## Implementation decisions

1. Preserve the existing repository mappings instead of inventing the literal
   top-level paths from the product diagram. Shared config therefore remains at
   `ReplicatedStorage/Shared/Game`, while `ReplicatedStorage/Game` holds mutable
   replicated state and remotes.
2. Migrate the world atomically to the exact two-lane/eight-pad hierarchy. Do
   not retain compatibility aliases for the old `Lane`, `Lane02`, `EnemySpawn`,
   or `Pad01`–`Pad04` names.
3. Keep exactly seven focused server modules. Split combat ownership out of the
   old `BuildService`; do not add a framework or general service container.
4. Use closed identifiers: routes `Left`/`Right`, enemies `Roamer`/`Brute`, and
   defenses `Empty`/`Wall`/`SlowTrap`/`Turret`.
5. Keep route selection deterministic enough to test: injectable seeded random
   selection for the 75/25 Roamer rule and alternating Brute tie resolution.
6. Record only bounded current-run counters. Freeze one report at result, clear
   it on the next run/return, and never persist it.
7. Preserve the 0.1 client entrypoint for Script Sync and compose three local
   controller ModuleScripts beneath `data/src/client/GameClient`.

## Intended source delta

Shared:

- update `GameTypes.luau`, `ChallengeConfig.luau`, `DefenseConfig.luau`, and
  `EnemyConfig.luau`;
- add `RouteConfig.luau` and `StateConstants.luau`.

Server:

- update `GameServer.server.luau`, `GameStateService.luau`, `BuildService.luau`,
  `ChallengeService.luau`, and `EnemyService.luau`;
- add `RouteService.luau`, `DefenseService.luau`, and
  `CombatStatsService.luau`.

Client:

- update `DefenseLoopClient.local.luau`;
- add `GameClient/BuildController.luau`, `HUDController.luau`, and
  `ReviewController.luau`.

Studio-owned delta:

- migrate `Workspace/Prototype` to `EnemySpawns`, `Lanes`, eight `BuildPads`,
  three `ReviewMarkers`, and empty `Runtime/Enemies` and `Runtime/Defenses`;
- add/tune primitive `SlowTrap`, `Roamer`, and `Brute` templates under
  `ServerStorage/GameTemplates` without external assets.

## Service responsibilities and boundaries

- `GameStateService`: legal transitions, core health, state replication.
- `BuildService`: pad registry, budget, build validation, prepared snapshot, and
  restoration. It never trusts cost from the client.
- `RouteService`: fixed node graph, route costs, wall-health BarrierScore,
  Roamer/Brute choices, and review marker presentation.
- `EnemyService`: bounded spawn records, movement, wall attacks, core arrival,
  slows, deaths, and route progress.
- `DefenseService`: template lifecycle, defense health, turret target/damage,
  SlowTrap effects, wall destruction, and cleanup.
- `CombatStatsService`: bounded counters, unique FirstBreach, frozen report,
  and replicated report attributes.
- `ChallengeService`: remote validation, run token, snapshot, countdown, wave
  schedule, Brute warning, win/defeat, review, reset, and rematch.

Dependencies are wired explicitly in `GameServer`. Cycles use narrow callbacks
registered after construction. All client-triggered paths fail closed and are
rate-limited.

## Milestones

1. Contract and recovery: update this plan/product contract; verify clean
   baseline, active Studio, mappings, and recovery artifacts.
2. World migration: create exact two-lane hierarchy and templates; inspect
   overview, lane convergence, pad ownership, marker hiding, and template
   readability before gameplay integration.
3. Shared/server core: implement configs, types, seven services, four remotes,
   build budget, routes, combat, wave lifecycle, report, and restoration.
4. Client: implement touch-first preparation, defending HUD, Brute warning,
   four-card review, return, modification, and rematch.
5. Static validation: format, format check, Selene/Luau analysis, diff check, and
   source audit for DataStore/publication/client-owned authority.
6. Runtime validation: execute and record T01–T18 with server/client Output,
   observable state, screenshots, two clients, latency, and Device Emulator.
7. Handoff: inspect the complete unstaged diff, record every unproven behavior,
   and deliver a truthful global verdict without commit or publication.

## Verification commands

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\format.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\format.ps1 -Check
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
git diff --check
git status --short
```

Runtime checks use the selected Studio place, Client/Server inspection, Server &
Clients with two clients, approximately 150 ms simulated latency, and a real
touch sequence in a small-screen Device Emulator. Screenshots prove only visual
state; server attributes/instances and Output prove the corresponding logic.

## Recovery and stop conditions

- Disk remains authoritative for synchronized scripts; Studio remains
  authoritative for unsynchronized geometry/templates.
- If Script Sync is not observed after a source edit, stop before assigning a
  runtime verdict.
- If world migration fails, return to Edit mode and use the local graybox
  snapshot only for recovery, then re-establish Script Sync from disk.
- Run tokens cancel delayed wave/review work before cleanup. Runtime folders and
  connections must be empty/bounded after every cycle.
- Stop rather than expanding scope if fixed routes cannot express the mechanic,
  if a general pathfinding framework appears necessary, or if review facts do
  not explain an observable event.

## Evidence ledger

- 2026-07-15: audit completed; the clean 0.1 plus readability-only 0.2 milestone
  is recoverable and synchronized.
- 2026-07-15: new founder specification reconciled. The old four-pad/four-service
  contract is explicitly superseded; no user-authored uncommitted change is at
  risk.
- 2026-07-15: Studio world migrated to the exact two-lane/eight-pad hierarchy.
  Left and right routes, separate spawns, convergence, review markers, runtime
  folders, and all five primitive templates were inspected in the intended
  Studio instance. No external asset was introduced.
- 2026-07-15: Script Sync exposed all seven server services, four remotes, shared
  configs/types, and three client controller modules in the active Edit
  DataModel. A later grep in Studio observed the final unique-slow counter fix.
- 2026-07-15: budget refusal, two-route use, seeded 75/25 route bias, Brute lane
  choice/wall destruction, unique FirstBreach, turret damage, locked building,
  rejected double start, victory, defeat, snapshot restoration, and rematch were
  observed through authoritative runtime attributes and instances.
- 2026-07-15: an actual iPhone 7 landscape touch sequence returned from REVIEW,
  selected `SlowTrap` on a physical pad, and launched the rematch. All essential
  preparation, build, defending, and four-card review controls remained within
  the measured 667 × 375 viewport.
- 2026-07-15: a server with two clients showed the same defeat report on both
  clients. A separate 150 ms incoming-replication-lag run kept client/server on
  the same phase and wave while two start requests produced one challenge.
- 2026-07-15: a controlled runtime overlap placed two SlowTraps over one live
  Roamer. The observed multiplier was `0.55` before and after refresh, never a
  multiplicative `0.3025`. The counter now records each enemy only once.
- 2026-07-15: initial complete challenges measured 72.6–90.3 seconds. Wave 2
  and 3 pacing was tuned without changing counts or enemy rules. A first
  confirmation measured 236.7 seconds; the final measured victory was 241.2
  seconds, inside the 240–300-second target.
- 2026-07-15: a temporary Studio-only hook exercised the real state, challenge,
  enemy, report, cleanup, and restoration services for ten consecutive cycles
  after one warm-up. Every sample returned `PREPARATION`, core `1000`, zero
  enemies, and zero defenses; Runtime retained only its two folders. Memory tags
  did not grow (`LuaHeap` 680.94→677.63 MB, `Instances` 35.08→35.06 MB,
  `Signals` 13.47→13.45 MB). The hook was removed before final verification.
- 2026-07-15: the final synchronized configuration also produced a no-defense
  defeat in 155.9 seconds: core `0`, 19 enemies reached it, traffic 11 Left / 8
  Right, and no runtime enemy remained in REVIEW. Returning cleared the report
  and restored `PREPARATION`, core `1000`, budget `0`, and both runtime folders
  empty. Runtime Output contained only `Defense Loop 0.2 server ready`.
- 2026-07-15: founder decision recorded because an unbriefed human panel is not
  currently available. The slice keeps `PASS TECHNIQUE` and receives
  `PASS PROVISOIRE / GO CONDITIONNEL` for narrow, reversible 0.3 work. Human
  comprehension remains `UNKNOWN`, a synthetic causal gate supplies the interim
  evidence, and the first available real-player traffic must reopen the human
  gate before any `PASS PRODUIT` claim.
