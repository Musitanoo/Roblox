# Tooling — Roblox Top 1

## Supported workflow

The prototype uses local Luau files, native Roblox Studio Script Sync, Git, and the official Roblox Studio MCP server. Rojo is intentionally not installed because Script Sync already owns the three code subtrees.

## Pinned tools

| Tool | Version | Purpose |
|---|---:|---|
| Rokit | 1.2.0 | Toolchain manager |
| StyLua | 2.5.2 | Deterministic Luau formatting |
| Selene | 0.31.0 | Roblox-aware linting |
| Luau LSP | 1.68.1 | Static analysis and editor language features |

The repository manifest is `rokit.toml`. Update versions deliberately, review release notes, reinstall, and run the full verification before committing a tool upgrade.

## First-time Windows setup

1. Install the current Microsoft Visual C++ x64 Redistributable.
2. Install Rokit 1.2.0 from its official GitHub release and run `rokit self-install`.
3. From the repository root, run:

   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
   powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
   ```

Rokit issue `rojo-rbx/rokit#112` can prevent proxy executables from resolving some tools on Windows. The checked-in PowerShell scripts deterministically resolve the exact Rokit-managed binaries from `rokit.toml`, so repository commands remain functional without abandoning version pinning.

## Commands

```powershell
# Install or restore the pinned toolchain
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1

# Format Luau sources
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\format.ps1

# Verify formatting only
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\format.ps1 -Check

# Validate configuration, format, lint, and type analysis
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1

# Validate the ignored local Studio 0.1 recovery snapshot against its tracked manifest
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-studio-baseline.ps1

# Validate the ignored local Studio 0.2 graybox snapshot against its tracked manifest
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-studio-graybox.ps1
```

The default checks target `data/src` and `tests` when present and validate every tracked Studio manifest as JSON. The dedicated Studio snapshot checks are intentionally separate because a fresh clone does not contain the ignored local `.rbxl` recovery files.

## Script Sync mappings

Configure these roots in Roblox Studio Explorer with **Script Sync → Sync to...**:

| Studio folder | Local directory |
|---|---|
| `ServerScriptService/Server` | `data/src/server` |
| `ReplicatedStorage/Shared` | `data/src/shared` |
| `StarterPlayer/StarterPlayerScripts/Client` | `data/src/client` |

On Windows, select the common parent directory `C:\Project\Roblox\data\src` for each of the three Folder instances. Script Sync then binds the instance names `Server`, `Shared`, and `Client` to the existing case-insensitive directories `server`, `shared`, and `client`. Do not select an individual child directory such as `data/src/server`: Studio would create the unwanted nested path `data/src/server/Server`.

After configuration, confirm that each Folder shows the Script Sync icon in Explorer and that the local tree contains no nested `server/Server`, `shared/Shared`, or `client/Client` directory.

If a synchronized root is paused, use **Script Sync → Reprendre la synchronisation**. When Studio reports a disk/instance conflict during Codex work, select **Version disque** because locally synchronized scripts are authoritative. For `DefenseLoopClient.local.luau`, verify that Studio retains exactly one enabled `LocalScript` named `DefenseLoopClient` with `RunContext=Legacy`; do not replace it with a client-context `Script`.

Prove a repaired binding with a harmless temporary comment added on disk: it must appear automatically in Studio and disappear automatically after removal. Never keep the witness or repair the source by manually pasting it into Studio.

Do not configure Rojo over any of these roots. Studio remains authoritative for unsynced geometry, terrain, lighting, assets, and manual instance composition.

## Luau LSP editor integration

The repository recommends `JohnnyMorganz.luau-lsp` and `JohnnyMorganz.stylua` through `.vscode/extensions.json`. Install the Luau Language Server Companion plugin in Roblox Studio so the editor can receive the live DataModel structure while Script Sync is in use.

The CLI analysis uses Roblox platform definitions and the strict repository `.luaurc`. Sourcemap generation is disabled because this project does not use Rojo.

Roblox global types are pinned from the Luau LSP `1.68.1` tag at `tools/luau-lsp/globalTypes.d.luau` (SHA-256 `A0027362F872D231C1C4BBEA6B2D5D561B0A4EA7E82458EA8A5F862CEF8938AA`). Update this file together with Luau LSP, never independently.

## Roblox Studio MCP

Enable Studio as an MCP server in **Assistant → … → Manage MCP Servers**. Codex should use MCP for inspection, execution, console review, screenshots, and playtests. Locally synchronized scripts must be edited on disk, not through MCP.
