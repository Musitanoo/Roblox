# Defense Loop 0.1

## Purpose

This graybox validates one hypothesis: configuring a few fixed defenses, deliberately starting a bounded challenge, understanding the result, and retrying is enjoyable and legible enough to justify deeper construction systems.

## Player loop

1. In `PREPARATION`, approach any green pad and choose `Vide`, `Mur`, or `Tourelle`.
2. Approach the yellow console and launch Challenge 1.
3. During `STARTING` and `DEFENDING`, building is locked.
4. Three waves of 4, 6, and 8 basic enemies follow the single dark lane.
5. The server resolves wall damage, turret damage, core damage, victory, and defeat.
6. `REVIEW` shows the core health, first destroyed structure, and number of enemies that reached the core.
7. `Modifier et retenter` restores the preparation snapshot and returns to `PREPARATION`.

Wave spawn intervals are 4.5, 4.0, and 3.5 seconds, with 10-second intermissions. The shortening intervals make pressure increase without adding a second enemy type.

## DataModel ownership

Native Script Sync remains authoritative for Luau:

```text
data/src/server/Game  -> ServerScriptService/Server/Game
data/src/shared/Game  -> ReplicatedStorage/Shared/Game
data/src/client/DefenseLoopClient.local.luau
                       -> StarterPlayer/StarterPlayerScripts/Client/DefenseLoopClient
```

Studio remains authoritative for `Workspace/Prototype` and `ServerStorage/GameTemplates`. Runtime state and the two RemoteEvents live under `ReplicatedStorage/Game`.

The closed 0.1 world baseline is recoverable from the ignored local file `studio/DefenseLoop-0.1-baseline.rbxl`. Its exact checksum and a versioned critical-instance manifest are recorded in `studio/README.md`; synchronized Luau remains authoritative on disk after recovery.

The existing `DefenseLoopClient` instance is a directly synchronized, enabled `LocalScript` with `RunContext=Legacy`. The `Client` root was resumed after a paused-sync conflict, the authoritative disk version was selected, and a temporary disk-only witness appeared automatically in Studio before being removed. Client source must therefore be edited only in `data/src/client/DefenseLoopClient.local.luau`; no manual Studio mirror is used.

## Security boundary

The client only opens UI and sends a pad name plus an allowed selection, or a challenge action. The server verifies player membership, payload type and length, request rate, game phase, pad membership, interaction distance, and action membership. The server owns all spawned models, health, damage, transitions, snapshots, and resets.

## Explicit exclusions

There is no DataStore, persistence, progression, free placement grid, farming map, inventory, crafting, adaptive horde, difficulty selection, trading, monetization, final art, external asset, or publication workflow in this slice.

## Manual acceptance scenarios

- Four turrets should provide a clear victory path.
- No defenses should provide a clear defeat path.
- Rapid duplicate console interactions must result in only one `STARTING` transition.
- Build requests outside `PREPARATION` must leave the defensive layout unchanged.
- Returning from `REVIEW` must clear enemies, restore core health and the initial pad snapshot, and allow another launch without restarting Studio.

## Observed validation

- A readability-only visual pass now distinguishes the dark lane from the floor, marks its direction toward the core, outlines build pads, and labels the horde entrance, core, and challenge console. The wall, turret, and basic zombie remain simple Parts but now have distinct silhouettes, highlights, health bars where relevant, and a short turret tracer; no combat value or state-machine behavior changed.
- Desktop play visibly showed the phase accent, core health bar, build-role labels, wall/turret silhouettes, zombie health, turret fire feedback, and the review result. Challenge 1 still completed in `VICTORY` with core 500/500 and clean Output.
- In iPhone 17 Pro landscape Device Emulator, the status panel, world labels, build menu, and all three role choices remained in bounds. Real OS-level taps opened the build menu and selected `Tourelle`; the server created `Pad01_Turret` with its muzzle and highlight, and Output remained clean. Studio was then reset to the default viewport.
- A real iPhone 17 Pro landscape Device Emulator tap opened the CoreGUI `Configurer` prompt, a second tap selected `Mur`, and the server created `Workspace.Prototype.Runtime.Defenses.Pad01_Wall` with `Pad01.DefenseType=Wall`. Output remained clean and Studio was reset to the default viewport.
- Four turrets produced `VICTORY` in 95.5 seconds with core 500/500.
- No defenses produced repeatable `DEFEAT` results in 84.7–84.9 seconds after 13 enemies reached the core.
- Ten consecutive final-configuration cycles returned to `PREPARATION` with no retained enemy and clean Output.
- A two-client `StudioTestService` probe received readiness from both clients and confirmed two remotes plus the shared preparation state.
- iPhone 17 Pro landscape simulation kept the status, three 100×70 build choices, review, and 324×58 retry button inside the safe logical viewport.
