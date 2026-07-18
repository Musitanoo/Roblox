# Build Loop 0.3 — Grid Build, Predict, Edit, Retest

| Champ | Valeur |
| --- | --- |
| ID | `SLICE-BUILD-003` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 0.3.0 |
| Propriétaire / approbateur | Product/Engineering / Founder |
| Scope | Construction autoritaire sur grille, édition et retest ; sans persistance ni publication |
| Source | Spécification founder Build Loop 0.3 et baseline Defense Loop 0.2 |
| Remplace | Construction par BuildPads de Defense Loop 0.2 |
| Dernière revue | 2026-07-17 |
| Revue suivante | Modification runtime, nouvelle exécution T01–T32, résultat G3 ou changement de scope |

## Decision and scope

Build Loop 0.3 replaces all BuildPad-dependent construction with a mathematical
16 × 12 ground grid using four-stud cells. Defense Loop 0.2 remains the combat
baseline: two approaches, Roamers, Brutes, three waves, factual review, reset,
and voluntary rematch.

The slice is authorized under the recorded `PASS PROVISOIRE / GO CONDITIONNEL`.
It remains reversible and introduces no DataStore, progression, economy,
crafting, expedition, monetization, new enemy, player weapon, active repair,
vertical building, or publication.

## Player contract

The intended loop is:

> select → preview → place → test → understand → edit → retry

Construction is available only in `PREPARATION`. The owner can place, move,
rotate, delete, undo, redo, and clear the plan. An observer sees the canonical
plan and budgets but cannot mutate it or start the challenge.

## Grid and pieces

- 16 columns, 12 rows, four studs per cell, 64 × 48 studs total.
- Grid coordinates derive from the rotated `BuildSurface` CFrame.
- Cells are mathematical; there is no server Part per cell.
- Wall: 1 × 2, rotatable, Structure 2, Power 0, 700 health.
- SlowTrap: 1 × 1, Structure 1, Power 1, 250 health.
- Turret: 1 × 1, rotatable, Structure 3, Power 2, 350 health.
- Structure limit 24; Power limit 8.

## Authority and protocol

The server owns the owner, plan, revision, footprints, occupancy, budgets,
spatial overlap, history, routes, snapshots, combat, and result. The client sends
only an operation intention with a request ID and base revision. It never sends
an authoritative CFrame, footprint, cost, path, damage, validation, or result.

Every accepted mutation increments the plan revision. The server retains the 64
most recent request results per player, limits construction to 10 requests per
second, and returns cached results for duplicate request IDs. A stale revision
returns `STALE_REVISION` and triggers a full plan resynchronization.

## Required proof

Tests T01–T32 from the founder specification each receive `PASS`, `FAIL`,
`PARTIAL`, `BLOCKED`, or `UNKNOWN`. `BLOCKED` means an external prerequisite
prevented observation; it is never converted into `PASS`. No unobserved behavior
receives `PASS`. A technical pass requires the critical tests identified in the
founder specification, clean static checks, clean client/server Output, an empty
runtime after reset, and no publication or persistence access.

The human comfort gate remains `UNKNOWN` while an unbriefed panel is unavailable.
Synthetic causal evidence may support a provisional continuation but cannot be
reported as measured human comprehension.

Le relevé d'exécution courant est conservé dans
`docs/BUILD_LOOP_0_3_TEST_REPORT.md`. La dernière exécution qui y est enregistrée
porte T01–T32 à `PASS` et un verdict global `PASS TECHNIQUE`. Ce verdict reste
lié au build et aux scénarios observés dans ce rapport : il ne certifie pas
automatiquement un worktree modifié. Le gate humain reste `UNKNOWN` et aucun
`PASS PRODUIT` n'est revendiqué.
