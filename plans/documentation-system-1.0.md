# Documentation System 1.0 — ExecPlan

## Outcome

Create a coherent, validation-first documentation system for Roblox Top 1.
The result must make the repository navigable from one entry point, distinguish
canon from accepted contracts, hypotheses, configuration, execution plans, and
evidence, classify every current document, define stage gates and risk
ownership, and provide lightweight templates that scale only when a concrete
risk or decision requires them.

No gameplay, synchronized Luau, Studio geometry, toolchain dependency, release,
or publication changes are authorized by this plan.

## Baseline audit — 2026-07-15

- Repository: `C:\Project\Roblox`, branch
  `agent/github-collaboration`.
- Worktree is clean before documentation work.
- `AGENTS.md` is the execution constitution and already defines the
  validation-first posture, truth verdicts, product authority, security,
  persistence, performance, testing, and completion rules.
- `Roblox_Top_1_Game_Design_Document_v1.0.md` is the design authority, but it
  combines durable principles with unvalidated product hypotheses and contains
  non-portable citation markers.
- Active product contracts and evidence already exist for Defense Loop 0.1,
  Defense Loop 0.2, and Build Loop 0.3. Build Loop 0.3 remains globally
  `PARTIAL`; its human gate is `UNKNOWN`.
- `docs/` has no front door, document register, lifecycle standard, concise
  product constitution, shared glossary, stage-gate map, risk register, ADR
  convention, or reusable specification/evidence templates.
- Native Studio Script Sync remains the confirmed workflow documented in
  `AGENTS.md` and `docs/TOOLING.md`. This task does not need a runtime
  synchronization check because it changes no runtime-facing file.

## Acceptance criteria

1. One documentation entry point identifies the current product and technical
   status, authoritative documents, active slice, known unknowns, and reading
   routes.
2. Every tracked document under the repository root, `docs/`, `plans/`, and
   `studio/` is classified in a register with owner role, authority class,
   lifecycle status, and review trigger.
3. The authority order is consistent with `AGENTS.md`; executable behavior and
   tests describe current reality but never silently supersede an accepted
   product contract.
4. A concise constitution extracts only durable product principles and labels
   all unmeasured outcomes as hypotheses.
5. Governance distinguishes `CANON`, `CONTRACT`, `HYPOTHESIS`, `CONFIG`,
   `PLAN`, `EVIDENCE`, and `REFERENCE`; lifecycle and truth verdict are
   separate dimensions.
6. Stage gates prevent premature persistence, economy, trading, monetization,
   broad LiveOps, or scale work.
7. The risk register prioritizes product comprehension, mobile construction,
   server authority, persistence, pathfinding/NPC budgets, scope, social value,
   and evidence quality.
8. Templates have a small mandatory core and conditional risk sections rather
   than forcing irrelevant boilerplate.
9. Material documentation-system decisions are recorded in an ADR.
10. All relative Markdown links resolve, source citations are human-readable,
    UTF-8 is valid, whitespace checks pass, and the final diff contains no
    runtime file.

## Intended files

- Update `README.md` and the GDD citation/status preamble where necessary.
- Add `docs/README.md` as the documentation front door.
- Add governance documents under `docs/00-governance/`.
- Add an official-source register under `docs/references/`.
- Add ADR conventions and the initial documentation-system ADR under
  `docs/adr/`.
- Add specification, ADR, evidence, and experiment templates under
  `docs/templates/`.
- Keep all existing slice contracts, evidence reports, plans, and Studio
  recovery documentation in place; do not rename them during this migration.

## Milestones

1. Freeze the documentation taxonomy, authority order, naming rules, and
   just-in-time creation triggers.
2. Create the front door, register, constitution, glossary, stage gates, and risk
   register.
3. Create ADR and document templates plus the official Roblox reference
   catalog.
4. Replace non-portable GDD citation markers with durable references without
   changing its product design.
5. Validate links, UTF-8, repository checks, diff scope, and documentation
   consistency; record the evidence here.

## Verification

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
git diff --check
git status --short
```

Run a deterministic local Markdown-link and UTF-8 audit over all tracked
`.md` files. Review the complete diff and confirm that no file under
`data/src`, `tests`, `scripts`, `tools`, or `studio` changed.

Studio playtesting is not applicable because the task changes documentation
only. Runtime synchronization therefore remains unchanged, not newly proven.

## Recovery

All intended changes are additive or small documentation edits. If the new
taxonomy conflicts with an existing accepted contract, preserve the contract,
record the conflict, and change the taxonomy. Do not rename or delete existing
evidence during this migration.

## Progress

- 2026-07-15: baseline audit complete; scope, acceptance criteria, and recovery
  boundaries fixed.
- 2026-07-15: documentation portal, product constitution, lifecycle/authority
  standard, exhaustive register, glossary, stage gates, risk register, ADR
  system, official-source catalog, and adaptive templates created.
- 2026-07-15: all non-portable GDD citation markers replaced with named primary
  sources; the GDD now distinguishes accepted design authority from measured
  player evidence.
- 2026-07-15: a separately-created untracked 3D asset workflow appeared during
  the task. It was preserved without modification and classified `IN_REVIEW` in
  the register because its specification self-reports `PASS` while its
  implementation remains `UNKNOWN` and production approval is false.
- 2026-07-15: repository static checks pass with 0 errors, 0 warnings, and 0
  parse errors. `git diff --check` passes. A strict audit confirms 30 Markdown
  files are valid UTF-8, every relative link resolves, and every Markdown file
  is registered. No internal conversation citation marker or tracking URL
  remains.

## Decisions

- Treat the proposed large corpus as a maturity map with creation triggers, not
  as permission to create dozens of empty specifications.
- Preserve `AGENTS.md` as execution authority instead of duplicating its full
  operational rules in product documentation.
- Preserve current slice documents as accepted contracts/evidence and index
  them rather than rewriting their history.

## Status

Complete. All acceptance criteria applicable to this documentation-only task
passed. Studio playtesting was not applicable; runtime synchronization and
player-facing behavior were not changed or re-claimed.
