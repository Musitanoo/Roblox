# Roblox Top 1 — Codex Instructions

## Mission

Build and validate a Roblox live-service experience with the long-term ambition of reaching world-leading 30-day average CCU.

The current strategy is validation-first. Optimize for learning speed, playable proof, retention evidence, social value, technical correctness, and safe iteration — not code volume or premature scale.

Canonical design principle:

> One verb. Infinite situations. Persistent identity. Better with friends.

A technically correct feature that does not improve a testable player outcome is not automatically valuable.

## Communication and truth

- Communicate with the founder in French unless explicitly asked otherwise.
- Keep code, identifiers, commands, and technical filenames in their conventional language.
- Be direct and distinguish facts, assumptions, hypotheses, recommendations, and measured results.
- Never claim completion without observable evidence.
- Use these verdicts:
  - `PASS`: all applicable acceptance checks succeeded.
  - `FAIL`: a required behavior or check failed.
  - `PARTIAL`: useful work exists, but acceptance is incomplete.
  - `BLOCKED`: an external prerequisite prevents completion.
  - `UNKNOWN`: the result was not or could not be verified.
- Never convert a skipped check into a `PASS`. Report it as skipped and explain why it was not applicable or could not run.

## Before changing anything

1. Read this file completely.
2. Inspect the repository root, `git status`, and relevant directories.
3. Read the closest applicable `AGENTS.md` or `AGENTS.override.md`.
4. Read only the specifications needed for the task.
5. Inspect existing implementation and test patterns.
6. Confirm the active Studio synchronization workflow.
7. State the intended outcome and observable acceptance criteria before implementation.

Never assume a tool, command, package, path, architecture, Studio instance, or synchronization mapping exists. Verify it first.

## Product authority

Resolve decisions in this order:

1. The user's current explicit request.
2. `Roblox_Top_1_Game_Design_Document_v1.0.md`, accepted specifications, and decision records.
3. Current executable behavior and tests.
4. Existing implementation patterns.
5. Your own assumptions.

When sources conflict, state the conflict, choose the safest reversible interpretation, and record material decisions. Do not silently expand product scope. The GDD is design authority, not proof that an untested hypothesis works.

## Current development posture

Unless explicitly told otherwise:

- Build the smallest playable experiment that can validate or invalidate the hypothesis.
- Prefer a narrow vertical slice over broad infrastructure.
- Keep the core action understandable quickly.
- Prefer a few interacting systems over large amounts of isolated content.
- Avoid implementing a full economy, trading, guilds, battle pass, multi-place architecture, or large content pipeline before the relevant player behavior is validated.
- Preserve reversible changes and clean stopping points.
- Do not add a framework, service layer, abstraction, dependency, or pipeline for hypothetical future scale.

## Repository layout

The current repository uses:

- `data/src/server/`: authoritative server systems synchronized to `ServerScriptService/Server`.
- `data/src/client/`: input, camera, UI, presentation, and cosmetic prediction synchronized to `StarterPlayer/StarterPlayerScripts/Client`.
- `data/src/shared/`: shared types, protocol definitions, immutable configuration, and pure utilities synchronized to `ReplicatedStorage/Shared`.
- `tests/`: unit and integration tests when introduced.
- `docs/`: architecture decisions, test plans, protocols, budgets, and tooling documentation.
- `scripts/`: deterministic repository tooling.
- `plans/`: self-contained ExecPlans for complex work.
- `rokit.toml`: pinned development toolchain.

Do not move `data/src` to a root-level `src` directory unless an accepted migration explicitly changes Script Sync mappings and all affected commands.

## Current toolchain and commands

Pinned versions are authoritative in `rokit.toml`:

- Rokit 1.2.0;
- StyLua 2.5.2;
- Selene 0.31.0;
- Luau LSP 1.68.1.

Use the checked-in commands rather than remembered raw invocations:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\format.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\format.ps1 -Check
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

`scripts/check.ps1` is the default static verification command. It validates configuration, formatting, lint, and type analysis for source roots that exist. A no-source result is a reported `SKIP`, not evidence that gameplay code passed.

Do not install Rojo, Wally, Pesde, TestEZ, Lune, CI workflows, or production dependencies until the task creates a concrete need and the user accepts the scope. Do not mix package managers.

## Source of truth and Studio sync

The current prototype workflow is native Roblox Studio Script Sync plus local files. Rojo is not configured.

Mappings:

```text
ServerScriptService/Server
→ data/src/server

ReplicatedStorage/Shared
→ data/src/shared

StarterPlayer/StarterPlayerScripts/Client
→ data/src/client
```

Windows Script Sync setup: invoke `Script Sync → Sync to...` on each of the three Folder instances and select the common parent `C:\Project\Roblox\data\src`. Selecting a child directory directly creates an invalid nested path such as `data/src/server/Server`; verify that no such duplicate directory exists.

Authority rules:

- Locally synchronized scripts are authoritative on disk during Codex work.
- Studio is authoritative for unsynced world geometry, terrain, lighting, manual instance composition, and assets unless documented otherwise.
- Never let Rojo and Script Sync manage the same subtree simultaneously.
- Never edit the same script through both local files and Studio MCP during one task.
- Prefer local-file edits for scripts present on disk.
- Use Studio MCP primarily for exploration, execution, playtesting, console inspection, screenshots, and interaction testing.
- Before editing through MCP, confirm the target is not locally managed.
- Before completion, verify the expected local version reached the intended active Studio session.
- If Script Sync cannot be verified, runtime synchronization remains `UNKNOWN` even when local checks pass.

## Implementation workflow

Before implementation:

- State the player-visible or developer-visible outcome.
- Define observable acceptance criteria.
- Inspect related code, tests, security boundaries, persistence, networking, and performance risks.
- Create or update an ExecPlan for complex work.

During implementation:

- Make the smallest coherent change.
- Preserve existing behavior unless the specification changes it.
- Avoid unrelated cleanup and speculative abstractions.
- Prefer simple, explicit Luau.
- Keep modules focused and dependencies directional.
- Update tests and documentation when behavior, commands, architecture, or data formats change.
- Keep the repository in a recoverable state after each meaningful milestone.

After implementation:

- Review the full diff for accidental changes.
- Run the relevant automated checks.
- Perform an appropriate Studio playtest for runtime-facing changes.
- Inspect client and server console output.
- Capture evidence supporting the final verdict.
- Report every check that was skipped, failed, or could not be observed.

## Luau standards

- Use `.luau` for new Luau files.
- Follow Script Sync naming: `.server.luau` for server Scripts, `.client.luau` for client Scripts, `.local.luau` for LocalScripts, and `.luau` for ModuleScripts.
- Start new production scripts and modules with `--!strict` unless a documented constraint prevents it.
- Define explicit exported types for public module interfaces.
- Prefer typed structures over loosely shaped tables.
- Avoid `any`; isolate and justify unavoidable unsafe casts.
- Do not suppress type or lint errors without a documented reason.
- Prefer guard clauses and early returns.
- Avoid hidden global state and cyclic module dependencies.
- Keep configuration separate from mutable runtime state.
- Use `task.*` APIs instead of deprecated scheduling APIs.
- Clean up connections, instances, tasks, and resources deterministically.
- Make randomness injectable or seedable when logic needs deterministic tests.
- Comments explain intent, invariants, tradeoffs, or Roblox-specific constraints — not obvious syntax.
- Run StyLua; do not hand-format around the formatter.

## Client/server architecture

The server is authoritative for:

- progression, inventory, currency, purchases, rewards, and mastery;
- damage, combat results, building validity, crafting, and upgrades;
- enemy spawning, wave state, ownership transfer, and persistent data;
- permissions, anti-abuse decisions, challenge results, and reward eligibility.

The client may own:

- input collection;
- camera, UI, presentation, audio, and visual effects;
- temporary cosmetic prediction that can be reconciled with server truth.

Shared replicated code may contain types, protocol schemas, pure deterministic logic, and safe immutable configuration. Never replicate secrets, privileged state, hidden anti-abuse logic, or authoritative mutable state.

Dependencies must flow toward shared pure contracts; shared code must not depend on server-only or client-only modules.

## Networking and security

Treat every client request as hostile.

For each RemoteEvent, RemoteFunction, prompt, touch-triggered action, or client-initiated request:

- validate type and structure;
- validate numeric bounds, finite numbers, enum membership, and string lengths;
- validate permissions, progression, ownership, and current server state;
- validate spatial distance and timing when relevant;
- enforce server-side rate limits and bounded queues;
- calculate prices, rewards, damage, and outcomes on the server;
- reject malformed, stale, replayed, duplicated, or impossible requests safely;
- perform cheap validation before expensive work;
- avoid returning privileged reasons or data that improve an attacker's knowledge.

Never trust client-provided prices, rewards, damage, timestamps, positions, inventory, instances, ownership, or target eligibility without server verification.

Threat-model every new client-triggerable feature:

- What if arbitrary values, NaN, infinities, huge tables, or unexpected Instances are sent?
- What if it is called 1,000 times per second?
- What if calls are replayed, duplicated, delayed, or reordered?
- What if the client controls local position, network ownership, or physics?
- Can it damage another player's experience, data, economy, or server budget?

Prefer secure-by-design rules over after-the-fact exploit detection. Security checks must fail closed without crashing the server.

## Persistent data

- Never access DataStoreService from client code.
- Never test against production data when an isolated test universe, mock, or namespace can be used.
- Do not enable Studio API access for a live production universe merely to pass a local test.
- Handle persistence failures explicitly and preserve player progress when writes fail.
- Design writes for retries, duplicate requests, shutdown, and multi-server concurrency.
- Prefer transactional update patterns when concurrent writes are possible.
- Version persisted schemas and document forward and rollback migrations.
- Make rewards and migrations idempotent where duplicate execution is possible.
- Never delete or rewrite player data without an explicit reviewed migration and rollback plan.
- Avoid logging secrets, authentication material, or unnecessary personal data.

## Gameplay integrity

- Separate pure game rules from engine side effects where practical.
- Use explicit state machines for non-trivial wave, match, trade, crafting, or session flows.
- Prevent double-spend, double-claim, duplicate completion, and repeated rewards.
- Keep progression tuning in validated configuration instead of scattered literals.
- Preserve a fair free progression path.
- Do not introduce deceptive scarcity, opaque paid randomness, punitive streak loss, pay-to-win, or other dark patterns.
- Failure must remain understandable, recoverable, and useful, consistent with the GDD.

## Performance

Design for the weakest supported mobile target, not the developer PC.

- Measure meaningful performance work; do not optimize by intuition alone.
- Avoid per-frame work when events or lower-frequency updates suffice.
- Bound loops, tables, queues, listeners, raycasts, pathfinding requests, spawned tasks, NPCs, projectiles, traps, physics objects, and retained telemetry.
- Minimize replicated state and remote traffic.
- Treat pathfinding, humanoids, network ownership, physics, destruction, and mass NPC updates as explicit budget risks.
- Prefer aggregation, pooling, spatial partitioning, and fixed work budgets only when evidence justifies them.
- Use MicroProfiler and runtime measurements for performance-sensitive changes.
- When feasible, include before/after evidence for optimizations.

## Dependencies and tooling

- Do not add a production dependency without concrete benefit, maintenance review, license check, and an accepted ownership plan.
- Reuse existing dependencies before adding overlapping ones.
- Pin tool and dependency versions using the repository's chosen system.
- Do not mix package managers for the same domain without an accepted migration decision.
- Never edit generated or vendored code unless explicitly required.
- Never commit credentials, Roblox cookies, API keys, secrets, local authentication state, or production identifiers.
- Discover actual commands before running or documenting them.
- Prefer checked-in scripts over remembered commands.
- If a required command is absent or broken, report the exact failure and use `BLOCKED`, `PARTIAL`, or `UNKNOWN`; never invent a passing result.

## Roblox Studio MCP verification

When Studio MCP is available:

1. List connected Studio instances.
2. Select and confirm the intended active instance before modifying anything.
3. Confirm Edit, Client, or Server DataModel availability.
4. Inspect the relevant DataModel subtree and scripts.
5. Confirm whether local synchronization manages the target.
6. Change locally managed code through the repository.
7. Verify synchronization before playtesting.
8. Start the appropriate play mode.
9. Exercise the acceptance scenario with navigation and input tools when useful.
10. Inspect both client and server console output.
11. Inspect relevant runtime instances or state.
12. Capture a screenshot for visual, UI, or world changes.
13. Stop the playtest and report evidence.

A screenshot alone does not prove correct logic. An error-free console alone does not prove correct gameplay. A local file alone does not prove Script Sync delivered it to Studio.

## Testing strategy

Use the smallest test level that proves the behavior, then add higher-level evidence when risk requires it.

Use unit tests for deterministic rules such as damage, costs, loot, waves, targeting, serialization, migrations, state transitions, and validation.

Use integration tests for boundaries such as remotes, inventory, rewards, building placement, wave lifecycle, persistence adapters, trading, and replication.

Use Studio playtests for controls, camera, UI, server/client interaction, physics, navigation, NPC behavior, world interaction, device usability, and complete gameplay loops.

Every bug fix should add a regression test when practical. Prefer proof that fails before the fix and passes after it. Do not add TestEZ before tests exist merely to satisfy a tooling checklist.

## Definition of done

A task is `PASS` only when all applicable conditions are satisfied:

- the requested behavior exists;
- observable acceptance criteria pass;
- relevant format, lint, type, build, and test checks pass;
- runtime-facing changes pass an appropriate Studio playtest;
- client and server consoles show no new relevant errors or warnings;
- security, persistence, and performance risks are addressed;
- documentation is updated when behavior, commands, architecture, or data formats change;
- the diff contains no unrelated modifications;
- remaining risks and unknowns are explicit.

Compilation, type-checking, or a plausible screenshot alone is insufficient proof for a gameplay feature. If no runtime-facing behavior changed, a Studio playtest may be non-applicable, but that decision must be stated.

## Review priorities

Review in this order:

1. player data loss or corruption;
2. exploitable client trust, economy, rewards, trades, damage, or ownership;
3. crashes, hangs, infinite loops, and unrecoverable state;
4. duplicate rewards, double-spend, and non-idempotent flows;
5. broken core gameplay or progression;
6. severe server, client, network, physics, or memory regressions;
7. incorrect persistence or migrations;
8. missing tests for high-risk logic;
9. unnecessary complexity and maintainability;
10. style.

Report findings with exact paths, affected behavior, severity, reasoning or reproduction, and the smallest safe remediation.

## Git safety

- Inspect `git status` before editing.
- Never overwrite or discard user changes.
- Keep the diff scoped to the task.
- Do not amend, rebase, force-push, reset, clean, delete branches, or perform destructive Git operations without explicit permission.
- Do not commit generated artifacts unless intentionally tracked.
- Use a dedicated branch or worktree for parallel or risky work when available.
- Do not create a commit without a configured and confirmed Git identity.
- Do not add or alter a remote without an explicit repository URL and authorization.
- Before reporting completion, inspect the full staged and unstaged diff and list changed files.

## ExecPlans

Create an ExecPlan in `plans/` before implementation for cross-cutting systems, persistent schema changes, economy/trading/inventory/monetization changes, security-sensitive protocols, major refactors, multi-place or deployment changes, significant tooling migrations, major unknowns, or work too large to remain understandable from a small diff.

An ExecPlan must be self-contained and kept current. It defines the observable outcome, milestones, exact files and commands, validation evidence, decisions, recovery strategy, and remaining risks. Update status and decisions while working; do not let the plan become historical fiction.

Small localized fixes do not require an ExecPlan.

## Final report

At the end of a coding task, report:

1. `Verdict`: PASS, FAIL, PARTIAL, BLOCKED, or UNKNOWN.
2. `Outcome`: what changed for the player or developer.
3. `Files changed`: repository-relative paths.
4. `Verification`: exact commands and Studio scenarios executed, with results.
5. `Evidence`: concise logs, observations, or screenshots.
6. `Risks / unknowns`: anything not proven.
7. `Next action`: the single highest-value next step, only when genuinely needed.

Do not hide failures behind a positive summary. No proof means no `PASS`.
