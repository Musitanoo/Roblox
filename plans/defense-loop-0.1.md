# Defense Loop 0.1 — ExecPlan

## Outcome

Deliver the smallest faithful graybox loop in the private, open Studio place: a player configures four fixed pads as Empty, Wall, or Turret; deliberately starts Challenge 1; observes three bounded waves attack a core; receives a readable victory or defeat review; returns to the preserved preparation layout; and can retry without restarting Studio.

No publishing, persistence, progression, farming world, adaptive horde, free grid, monetization, or unaudited asset is in scope.

## Observable acceptance

The requested 16-item Definition of Done is authoritative. `PASS` requires observed evidence for every applicable item, including ten consecutive cycles, solo, two-client server mode, clean client/server Output, and mobile emulator usability. A skipped or unavailable runtime check remains `UNKNOWN` and prevents an overall `PASS`.

Security checks must also demonstrate that duplicate starts and build requests outside `PREPARATION` fail closed, malformed payloads do not crash the server, and all combat/build outcomes are calculated by the server.

## Current state and overwrite audit

- Git is clean on `agent/bootstrap-roblox-toolchain`.
- Studio instance `Expérience sans titre` is active and private publication is not touched.
- A blank playtest starts and stops with no Output errors.
- Workspace contains only Terrain, Camera, Baseplate, and SpawnLocation.
- `Baseplate` and `SpawnLocation` will be reused under `Workspace.Prototype`; no authored content is being replaced.
- Output confirms native Script Sync roots are ready for `Server`, `Shared`, and `Client`.

## Architecture decisions

1. Preserve the accepted Script Sync mappings instead of rewiring the repository:
   - `data/src/server/Game` → `ServerScriptService/Server/Game`;
   - `data/src/shared/Game` → `ReplicatedStorage/Shared/Game`;
   - `data/src/client/DefenseLoopClient.local.luau` → `StarterPlayerScripts/Client/DefenseLoopClient` through native Script Sync.
2. Create runtime remotes at `ReplicatedStorage/Game/Remotes`. Shared immutable configuration remains below the synchronized `ReplicatedStorage/Shared/Game` root.
3. Keep unsynchronized geometry and templates authoritative in Studio: `Workspace/Prototype` and `ServerStorage/GameTemplates`.
4. Use fixed lane nodes and server-driven anchored enemy movement instead of PathfindingService. This makes one-lane behavior deterministic and bounded for the experiment.
5. Use ProximityPrompts for pad and console interaction so the same interaction primitive supports mouse, touch, and gamepad. The custom UI only presents the three build choices, status, and review action.
6. Every client request is type-, state-, distance-, membership-, permission-, and rate-validated. The first request changes state synchronously so duplicate challenge starts cannot race.
7. Snapshot the pad configuration at `STARTING`; restore it on return from `REVIEW`. No DataStore is accessed.
8. Keep `DefenseLoopClient.local.luau` bound to the existing enabled `LocalScript` with `RunContext=Legacy`. Local disk source is authoritative; a temporary witness change must propagate automatically before runtime verification.

## Planned files

- `data/src/shared/Game/GameTypes.luau`
- `data/src/shared/Game/Config/ChallengeConfig.luau`
- `data/src/shared/Game/Config/DefenseConfig.luau`
- `data/src/shared/Game/Config/EnemyConfig.luau`
- `data/src/server/Game/GameServer.server.luau`
- `data/src/server/Game/Services/GameStateService.luau`
- `data/src/server/Game/Services/BuildService.luau`
- `data/src/server/Game/Services/EnemyService.luau`
- `data/src/server/Game/Services/ChallengeService.luau`
- `data/src/client/DefenseLoopClient.local.luau`
- `docs/DEFENSE_LOOP_0_1.md`
- this ExecPlan

## Studio instances

- `Workspace/Prototype`: BaseFloor, ObjectiveCore, PlayerSpawn, ChallengeConsole, EnemySpawn, Lane/Node01..Node04, BuildPads/Pad01..Pad04, Runtime/Enemies, Runtime/Defenses.
- `ServerStorage/GameTemplates`: BasicZombie, Wall, Turret.
- `ReplicatedStorage/Game/Remotes`: RequestBuild, RequestStartChallenge (created idempotently by the server).

## Milestones

1. Create this plan and record baseline evidence.
2. Build and inspect the exact graybox and primitive templates in Edit mode.
3. Add strict shared configuration/contracts, four focused server modules, one server entry point, and one client entry point.
4. Run repository format/check commands and verify local scripts reached the intended Studio paths.
5. Playtest victory, defeat, duplicate start, forbidden build, reset/rematch, repeated cycles, solo, two-client server mode, client/server Output, mobile viewport, and simulated latency where Studio tooling permits observable control.
6. Review all diffs, update this plan with evidence and residual risks, and report a truthful verdict.

## Exact repository verification

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\format.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\format.ps1 -Check
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
git status --short
git diff --check
git diff --stat
```

Runtime verification uses the connected Studio instance: inspect synchronized paths, start/stop play, exercise UI/remotes, inspect server and client state plus Output, and capture a gameplay screenshot. No place publication occurs.

## Recovery strategy

All repository edits are additive and scoped to the files listed above. Studio changes are contained under `Workspace.Prototype` and `ServerStorage.GameTemplates`, except for moving the default Baseplate and SpawnLocation into Prototype. If a milestone fails, stop play mode, leave the last coherent files on disk, preserve diagnostic Output, and report the incomplete check rather than deleting or hiding evidence.

## Progress and evidence

- 2026-07-15: baseline repository, active Studio instance, blank DataModel, Script Sync readiness, blank play start/stop, and Output inspected.
- 2026-07-15: exact graybox and three primitive templates created in Studio; screenshot and hierarchy inspection confirm one lane, four pads, colored objective/spawn/console, and no external assets.
- 2026-07-15: shared configuration/contracts, four server services, server entry point, and client UI implemented. Final repository checks pass: StyLua, Selene (0 errors, 0 warnings, 0 parse errors), and Luau LSP.
- 2026-07-15: Script Sync delivery observed for every server/shared file. The client `LocalScript` initially required a manual mirror because its synchronized root was paused; this was corrected later in the same session.
- 2026-07-15: real character navigation, prompts, and GUI clicks created four server-owned turrets. Four-turret Challenge 1 completed in `VICTORY` after 95.5 seconds with core 500/500 and zero enemies reaching it.
- 2026-07-15: no-defense Challenge 1 completed in `DEFEAT`; core reached 0/500 after 13 enemies. A wall dropped from 360 to 270 while the core remained 500, was destroyed, appeared as `Pad01 (Mur)` in review, and restored to 360 on return.
- 2026-07-15: duplicate start and build-during-`DEFENDING` requests were rejected. A burst containing one valid build, 999 rapid replacements, an oversized pad name, and a table payload resulted in exactly one wall and no server error.
- 2026-07-15: ten consecutive cycles on the final 4.5/4.0/3.5-second pacing completed in one Studio session. Every cycle reached review in 84.7–84.9 seconds with the expected no-defense defeat and returned to `PREPARATION`; final enemies = 0, core = 500, and Output contained only `Defense Loop 0.1 server ready`.
- 2026-07-15: `StudioTestService` multiplayer probe returned `pass=true`, `playerCount=2`, `clientReadyCount=2`, `gameReady=true`, `phase=PREPARATION`, and `remoteCount=2`. All three temporary probe instances and child Studio processes were removed.
- 2026-07-15: with `IncomingReplicationLag=0.2`, server placement round-trip was observed in 0.451 seconds and duplicate start still produced one `STARTING` transition. The setting was restored to 0.
- 2026-07-15: iPhone 17 Pro landscape simulation (874×402; logical safe viewport 750×303) found an inset/overlap defect. After correction, status, build menu, all three 100×70 choices, 360×280 review, and 324×58 retry button were entirely in bounds; status is hidden during review. Studio was reset to the default viewport.

- 2026-07-15: the paused `Client` Script Sync root was resumed and the authoritative disk version was selected. A temporary disk-only witness propagated automatically to the single `DefenseLoopClient` instance and disappeared automatically after removal; the instance remained an enabled `LocalScript` with `RunContext=Legacy`.
- 2026-07-15: in iPhone 17 Pro landscape Device Emulator, a real OS-level tap on the CoreGUI `Configurer` prompt opened the build menu and a second tap on `Mur` produced the server-owned `Pad01_Wall` model plus `Pad01.DefenseType=Wall`. Client/server Output contained no error or warning, play mode stopped, and the simulator returned to `default`.
- 2026-07-15: a scoped readability pass added lane borders and direction markers, stronger objective/spawn/console labeling, build-pad outlines, distinct primitive silhouettes for the three templates, health bars, turret tracers, and clearer responsive UI hierarchy. No gameplay numbers or systems changed. Desktop play observed a complete victory with visible zombie damage and turret fire; a real iPhone 17 Pro landscape tap opened the role menu and selected a server-owned turret with every relevant UI bound inside the viewport. Output stayed clean and the simulator was reset to `default`.
- 2026-07-15: the Studio-authoritative 0.1 world was captured locally as ignored `studio/DefenseLoop-0.1-baseline.rbxl` (106896 bytes, SHA-256 `FCD493534B212B801B48A7A2920957626A34D6410615F891C4A5E0DD51AA94C5`). A tracked manifest records critical hierarchy, dimensions, template counts, and Script Sync roots without treating the place binary as source code.

## Remaining risks

- Graybox geometry and templates remain Studio-authoritative. A local ignored place snapshot and tracked manifest now provide recovery and drift evidence, but the binary snapshot is machine-local and must be backed up separately if workstation loss is in scope.
