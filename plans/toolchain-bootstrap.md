# ExecPlan — Toolchain Roblox Top 1

## Outcome

Provide a reproducible Windows-first Luau toolchain for the validation prototype, governed by the repository `AGENTS.md` and compatible with native Roblox Studio Script Sync.

## Scope

- Integrate the founder-provided `AGENTS.md` and specialize it for this repository.
- Pin Rokit, StyLua, Selene, and Luau LSP.
- Add deterministic format, lint, and type-analysis commands.
- Document Script Sync and Roblox Studio MCP responsibilities.
- Validate every installed binary and checked-in configuration.

## Out of scope

- Rojo, Wally, TestEZ, Lune, CI, and Open Cloud execution.
- Gameplay implementation.
- GitHub remote creation or authentication.

## Milestones

1. Audit repository, Git, Studio, and current tool availability.
2. Install native prerequisites and Rokit.
3. Pin and install the selected Luau tools.
4. Add repository instructions, configuration, and command wrappers.
5. Run all static checks and verify Studio integration.

## Validation

- `rokit list` reports the exact pinned versions.
- StyLua, Selene, and Luau LSP each report the expected version.
- `scripts/check.ps1` exits with code 0.
- The active Studio exposes the three expected Script Sync root folders, each with an active direct mapping and no nested duplicate directory.
- Git diff contains only the intended bootstrap files and previous user-approved initialization.

## Recovery

- Tool versions are changed only in `rokit.toml`.
- Repository tooling is removable without modifying game data.
- Script Sync and Rojo must never own the same subtree.

## Decisions

- Native Script Sync remains the synchronization workflow for the prototype.
- Local source roots are `data/src/server`, `data/src/shared`, and `data/src/client`.
- PowerShell wrappers resolve Rokit-managed binaries directly on Windows when Rokit proxy links fail.

## Status

Complete. Rokit-managed tools are pinned and validated, all static checks pass, the official Studio MCP connection is active, and the three native Script Sync mappings resolve directly to `data/src/server`, `data/src/shared`, and `data/src/client`.
