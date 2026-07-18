# Tooling — Roblox Top 1

| Champ | Valeur |
| --- | --- |
| ID | `ENG-TOOLING-001` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 1.1.0 |
| Propriétaire / approbateur | Engineering / Founder |
| Scope | Toolchain locale, checks, Script Sync et intégrations Studio/MCP |
| Source | `rokit.toml`, scripts du dépôt et workflow Studio actif |
| Remplace | Version 1.0.0 de ce guide |
| Dernière revue | 2026-07-17 |
| Revue suivante | Version, commande, mapping Script Sync ou intégration modifiée |

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

1. Install the current Git for Windows release and open a new terminal. Confirm
   that the executable is discoverable before continuing:

   ```powershell
   git --version
   where.exe git
   ```

   If the installer completed but `git` is not found, close and reopen the
   terminal so its `PATH` is refreshed. Do not document a successful Git setup
   until `git --version` succeeds in the actual development shell.
2. Install the current Microsoft Visual C++ x64 Redistributable.
3. Install Rokit 1.2.0 from its official GitHub release and run `rokit self-install`.
4. From the repository root, run:

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

# Validate only the durable Markdown corpus and document register
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-docs.ps1

# Validate the ignored local Studio 0.1 recovery snapshot against its tracked manifest
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-studio-baseline.ps1

# Validate the ignored local Studio 0.2 graybox snapshot against its tracked manifest
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check-studio-graybox.ps1
```

The default check first validates the durable Markdown corpus, then targets
`data/src` and `tests` when present and validates every tracked Studio manifest
as JSON. The dedicated Studio snapshot checks are intentionally separate because
a fresh clone does not contain the ignored local `.rbxl` recovery files.

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

## Blender Visual Workbench MCP

The project-scoped `.codex/config.toml` declares a local STDIO server named
`blender_visual_workbench`. It launches `scripts/r3d-mcp.ps1`, forwards no
Roblox credentials, exposes a strict tool allow-list, and prompts for every
tool that writes session evidence or a Candidate copy. Restart Codex after a
configuration change, then use `/mcp` to confirm exposure in the new task.

This workbench complements the deterministic compiler. It does not replace
`asset.json`, a locked visual canon, `compile_asset.py`, Studio, or human art
approval. Its normal path has no arbitrary Python, TCP listener, download,
publication, or canonical-source editing tool.

```powershell
# Environment, transport and allow-list
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 blender-mcp-doctor --repo .

# Immutable review
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 blender-inspect .\assets-3d\<asset>\asset.json

# Transactional candidate
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 blender-workbench .\assets-3d\<asset>\asset.json --mode explore
```

The complete authority model, operation bounds, evidence layout and promotion
sequence are defined in
[BLENDER_MCP_WORKBENCH.md](BLENDER_MCP_WORKBENCH.md).
