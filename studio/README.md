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
