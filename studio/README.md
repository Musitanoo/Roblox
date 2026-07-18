# Local Studio recovery snapshots

Roblox Studio place files in this directory are intentionally ignored by Git. They contain Studio-authoritative world geometry, lighting, templates, and manual instance composition; they are recovery artifacts, not the source of truth for synchronized Luau.

## Defense Loop 0.1 baseline

- Local file: `studio/DefenseLoop-0.1-baseline.rbxl`
- Versioned inventory: `studio/DefenseLoop-0.1-baseline.manifest.json`
- Source Studio window: `Place de pasdideepfffff : 07142026_1 - Roblox Studio`
- MCP instance: `Expérience sans titre` (`7f5fb084-b3e7-4e9d-9e20-04bd7519705e`)
- Expected mode at capture: Edit
- Publication: forbidden and not required
- Script authority after opening: reconnect the existing Script Sync roots to `data/src/server`, `data/src/shared`, and `data/src/client`, choosing the disk version for synchronized source conflicts.

After the snapshot is created, record its byte length, SHA-256, capture time, and a compact Studio inventory below. Recalculate the checksum only when intentionally replacing the baseline.

### Recorded artifact

- Captured UTC: `2026-07-15T07:47:48.2551455Z`
- Length: `106896` bytes
- SHA-256: `FCD493534B212B801B48A7A2920957626A34D6410615F891C4A5E0DD51AA94C5`
- Format: binary Roblox place (`.rbxl`)

The checksum proves the ignored local file has not changed. The tracked manifest proves the expected critical hierarchy and graybox dimensions without making the binary place file a competing source of truth.

### Required inventory

- `Workspace.Prototype` with one primary lane, four BuildPads, objective, console, spawns, and readability visuals. The server creates the runtime folders when play starts.
- `ServerStorage.GameTemplates` with `BasicZombie`, `Wall`, and `Turret`.
- synchronized `Server`, `Shared`, and `Client` roots present, with exactly one enabled Legacy `DefenseLoopClient` LocalScript.

Do not commit `.rbxl`, `.rbxlx`, lock, autosave, or backup files. Do not use a snapshot as evidence that current disk source reached Studio; verify Script Sync separately.

## Defense Loop 0.2 graybox milestone

- Local file: `studio/DefenseLoop-0.2-graybox.rbxl`
- Versioned inventory: `studio/DefenseLoop-0.2-graybox.manifest.json`
- Captured UTC: `2026-07-15T10:01:10.8349299Z`
- Length: `108498` bytes
- SHA-256: `90A4BA9BD5748650B1D5BA4A1CB3A222DA696EAC28BB24BC44D133823FDB4B9B`
- Added Studio-authoritative instances only: `Workspace.Prototype.Lane02`, `Workspace.Prototype.EnemySpawn02`, and `ServerStorage.GameTemplates.Brute`.
- No Defense Loop 0.2 gameplay source is included in this milestone.

Validate it with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-studio-graybox.ps1
```

## Defense Loop 0.2 full graybox recovery

- Local file: `studio/DefenseLoop-0.2-full.rbxl`
- Versioned inventory: `studio/DefenseLoop-0.2-full.manifest.json`
- Captured UTC: `2026-07-15T11:13:43.2964558Z`
- Length: `111499` bytes
- SHA-256: `4586DE0D61F4C75D3B63C67A8C0ACD96ED691F2847CB7CFB90315345F625B4BD`
- Intended Studio instance: `Expérience sans titre`
  (`7f5fb084-b3e7-4e9d-9e20-04bd7519705e`), Edit mode.
- Publication: not performed.

This recovery copy contains the exact two-lane/eight-pad graybox, review markers,
runtime folders, and five primitive templates used by the 0.2 playtests. It does
not replace the synchronized Luau on disk. After opening it, reconnect the three
native Script Sync roots and choose the local disk source for synchronized code.
