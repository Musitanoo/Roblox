# Defense Loop 0.2 — ExecPlan

## Status

Preparation only. No Defense Loop 0.2 gameplay implementation has begun.

## Outcome

Extend the validated 0.1 loop with exactly one secondary route, one wall-breaking Brute, one reproducible architectural weakness, and one elementary server-authored autopsy. A player must be able to read the weakness, change the existing four-pad configuration, rematch, and observe an improvement in a declared metric.

The product contract is `docs/DEFENSE_LOOP_0_2.md`. Its 20 checks are authoritative for this slice.

## Baseline prerequisites

- Defense Loop 0.1 source, tooling documentation, and acceptance evidence are committed before implementation starts.
- The active Studio place is saved to the local ignored recovery path documented in `studio/README.md`.
- Studio is in Edit mode, the intended instance is selected, and Script Sync delivers the three authoritative disk roots.
- Repository static checks pass and the 0.1 Output baseline contains no new warning or error.
- No nested `server/Server`, `shared/Shared`, or `client/Client` synchronization directory exists.

If any prerequisite fails, 0.2 implementation does not start.

## DataModel delta

Keep existing instance names and add only:

```text
Workspace/Prototype
├── EnemySpawn02
└── Lane02
    ├── Node01
    ├── Node02
    ├── Node03
    └── Node04

ServerStorage/GameTemplates
└── Brute
```

`EnemySpawn` and `Lane` remain the primary route to avoid an unnecessary world migration. The four existing BuildPads remain unchanged in count and interaction model.

## Source delta

Expected edits, kept within the current architecture:

- `data/src/shared/Game/GameTypes.luau`: closed `EnemyType` and `RouteId` types plus validators.
- `data/src/shared/Game/Config/ChallengeConfig.luau`: typed wave entries containing enemy type and route.
- `data/src/shared/Game/Config/EnemyConfig.luau`: separate immutable BasicZombie and Brute tuning.
- `data/src/server/Game/Services/EnemyService.luau`: two route definitions, typed spawn, per-type movement and wall damage, bounded event callbacks.
- `data/src/server/Game/Services/ChallengeService.luau`: config-driven spawns and current-run autopsy counters.
- `data/src/server/Game/Services/GameStateService.luau`: replicated, resettable autopsy result attributes.
- `data/src/client/DefenseLoopClient.local.luau`: compact autopsy presentation and route labels only.
- Studio-authoritative graybox and `Brute` primitive template.

`BuildService`, `GameServer`, and `DefenseConfig` should remain unchanged unless implementation evidence shows a concrete 0.2 requirement. No new service, RemoteEvent, framework, package, or persistence adapter is planned.

## Proposed immutable identifiers

- Enemy types: `BasicZombie`, `Brute`.
- Routes: `Primary`, `Secondary`.

These identifiers are server-selected from configuration. They are never accepted as authoritative client inputs.

## Autopsy contract

Maintain a single current-run record inside `ChallengeService` with bounded numeric counters:

- arrivals and core damage indexed by the two fixed route identifiers;
- Brute wall damage;
- first destroyed structure and cause.

At finish, select the weak route by highest core damage, then highest arrivals, then stable route order (`Primary`, `Secondary`). If both routes caused zero core damage, report `None`. Replicate only the final compact fields needed by the client. Clear them before every challenge and on return to preparation.

## Security and failure analysis

- Keep run-token cancellation around every spawn loop, intermission, finish, and delayed review transition.
- Reject unknown config identifiers during service construction rather than degrading to an arbitrary template or route.
- Keep `maxActiveEnemies` as a hard server cap across both enemy types.
- Clamp all damage to non-negative configured values; never accept damage, type, route, counters, or diagnosis from the client.
- Destroy both enemy types on finish/reset and clear their records before restoring the snapshot.
- Ensure duplicated, delayed, and reordered client requests cannot start a second run or return stale review data.
- Avoid per-frame scans beyond the bounded active-enemy and four-defense sets already present in 0.1.

## Milestones

1. Reconfirm baseline commit, Studio recovery file, Script Sync, and 0.1 smoke test.
2. Graybox `Lane02`/`EnemySpawn02` and primitive `Brute`; prove route readability before code expansion.
3. Extend shared types/config and make `EnemyService.spawn(enemyType, routeId)` fail closed.
4. Add config-driven mixed waves and prove both routes plus Brute wall damage.
5. Add bounded autopsy counters and server-replicated review fields.
6. Complete baseline weakness → review → modification → improved rematch on desktop.
7. Execute abuse, reset, ten-cycle, two-client, latency, and real-touch mobile tests.
8. Re-run the complete 0.1 regression matrix, audit the diff, and record final evidence.

Each milestone must leave a playable, recoverable state. Do not begin a later milestone while an earlier runtime invariant is failing.

## Verification commands

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\format.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\format.ps1 -Check
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
git diff --check
git status --short
```

Runtime verification uses the connected Studio instance, real prompts/UI input when relevant, server and client state inspection, Output review, Server & Clients with two clients, 200 ms simulated incoming replication lag, and iPhone landscape Device Emulator touch input. No place publication occurs.

## Evidence ledger

- 2026-07-15: 0.1 source and acceptance evidence audited; repository checks passed with StyLua, Selene (0 errors, 0 warnings, 0 parse errors), and Luau LSP.
- 2026-07-15: one intended Studio instance identified in Edit mode; Output contained only `Defense Loop 0.1 server ready`.
- 2026-07-15: 0.2 scope reduced to one added route, one added enemy type, one diagnosis, and one observable rematch improvement; no gameplay implementation started.
- 2026-07-15: ignored local Studio snapshot captured and verified against the tracked manifest: identity, byte length, SHA-256, and critical inventory all passed.
- 2026-07-15: current baseline smoke start observed server `PREPARATION`, core 500, two remotes, zero runtime enemies/defenses, and the client `DefenseLoopUI` with status, build, and review panels. Output remained limited to the normal ready message and Studio returned to Edit mode.

## Recovery strategy

- Git provides the authoritative 0.1 code and documentation checkpoint.
- The ignored local Studio snapshot provides emergency recovery for unsynchronized world geometry and templates; it must never replace the disk-authoritative Script Sync roots during normal work.
- Before world edits, verify the snapshot path and checksum recorded in `studio/README.md`.
- If a Studio edit fails, stop play, reopen the recovery snapshot only if necessary, restore Script Sync from disk, and rerun the 0.1 smoke test before resuming.
- Never publish as a recovery mechanism.

## Remaining unknowns for implementation

- Final Brute tuning and exact wave composition require measured desktop playtests; the 90–150 second challenge target and content budget are fixed, but numbers are not guessed in this preparation phase.
- Exact secondary-lane geometry must be grayboxed and inspected against turret range before implementation locks the causal baseline/rematch layouts.
- The 0.2 slice cannot be declared `PASS` until every applicable acceptance check is observed.
