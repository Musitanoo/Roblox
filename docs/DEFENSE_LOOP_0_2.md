# Defense Loop 0.2 — Two-Lane Failure-to-Learning Slice

## Product outcome

Defense Loop 0.2 must prove one causal loop:

> weakness observed → cause understood → base modified → voluntary rematch

The player has two fixed attack lanes and eight fixed BuildPads. An eight-point
budget forces a coverage tradeoff. Roamers generally seek the cheaper lane,
while the announced Brute seeks fortifications and destroys walls quickly.
Review presents server-authored facts, never a prescribed solution.

Victory is useful, but it is not the primary proof. The slice succeeds when a
player can identify the first breach, explain why the core suffered, change the
layout, and start another attempt.

## Fixed scope

- One graybox arena, approximately 96 × 72 studs.
- Two fixed routes converging near the core.
- Eight fixed BuildPads: `Left01`–`Left03`, `Right01`–`Right03`,
  `CoreLeft`, and `CoreRight`.
- Four build choices: `Empty`, `Wall`, `SlowTrap`, and `Turret`.
- One eight-point server-owned construction budget.
- Two enemy types: `Roamer` and `Brute`.
- One challenge, `Challenge2_FirstBreach`, with three waves.
- One current-run factual autopsy and immediate rematch.
- One to two players; no persistent data and no publication.

Explicit exclusions: DataStore, progression, materials, crafting, expeditions,
trading, monetization, player weapons, active repair, free placement, adaptive
persistent hordes, final art, public assets, and unrelated refactoring.

## Authoritative tuning

All values live in shared immutable configuration modules.

| Element | Values |
| --- | --- |
| Core | `MaxHealth = 1000` |
| Wall | `MaxHealth = 700`, `Cost = 1`, blocking |
| SlowTrap | `MaxHealth = 250`, `Cost = 1`, `SlowMultiplier = 0.55`, `EffectDuration = 1.25`, non-blocking |
| Turret | `MaxHealth = 350`, `Cost = 2`, `Range = 28`, `Damage = 18`, `Cooldown = 0.35` |
| Roamer | `MaxHealth = 100`, `MoveSpeed = 8`, `CoreDamage = 40`, `StructureDPS = 20` |
| Brute | `MaxHealth = 450`, `MoveSpeed = 4.5`, `CoreDamage = 120`, `StructureDPS = 85` |
| Runtime cap | `MaxActiveEnemies = 24` |

The initial target challenge duration is four to five minutes. Timing must be
measured in Studio and reported honestly; it is tuning evidence, not a reason
to add content.

## World contract

```text
Workspace/Prototype
├── BaseFloor
├── ObjectiveCore
├── PlayerSpawn
├── ChallengeConsole
├── EnemySpawns
│   ├── LeftSpawn
│   └── RightSpawn
├── Lanes
│   ├── LeftLane/Node01..Node05
│   └── RightLane/Node01..Node05
├── BuildPads
│   ├── Left01..Left03
│   ├── Right01..Right03
│   ├── CoreLeft
│   └── CoreRight
├── ReviewMarkers
│   ├── LeftLaneMarker
│   ├── RightLaneMarker
│   └── FirstBreachMarker
└── Runtime
    ├── Enemies
    └── Defenses
```

The routes start separately and converge only near the core. Lateral pads affect
their named lane; the two core pads form the last line. Every navigation route
is an ordered five-node graph. No global pathfinding or per-frame route
recalculation is permitted.

## Build and route rules

Costs are `Empty = 0`, `Wall = 1`, `SlowTrap = 1`, and `Turret = 2`. The server
validates state, player permission, pad identity, requested closed-set type,
distance, budget, rate, occupancy, and concurrent processing. The client never
sends a cost.

Route cost is base travel cost plus 40 per blocking Wall and 15 per SlowTrap.
Turrets do not change route cost.

- A Roamer chooses the cheapest lane 75% of the time and the other lane 25% of
  the time. Its route is immutable after spawn.
- A Brute chooses the lane with the highest sum of live blocking-wall health.
  Ties alternate deterministically.
- In wave 3, if both lanes contain Walls, assign one Brute to each. Otherwise,
  assign the first to the most fortified lane and the second to the other lane.
- A Brute is announced six seconds before spawn and attacks the first blocking
  Wall it reaches.

## Challenge 2 — Première Brèche

- Wave 1: six Roamers, three per lane, 0.9-second spawn interval, then eight
  seconds of breathing room.
- Wave 2: eight Roamers and one announced Brute, then ten seconds of breathing
  room.
- Wave 3: ten Roamers and two Brutes under the assignment rule above.
- No boss and no persistent reward.

`STARTING` captures the prepared layout, resets statistics and health, locks
construction, and counts down three seconds. `DEFENDING` owns waves, routes,
damage, and results. `REVIEW` locks construction, shows at most four cards, and
activates bounded 3D markers. Returning to `PREPARATION` removes enemies,
restores the captured layout at full health, hides markers, and waits for an
explicit modification or rematch.

## Combat and autopsy

Roamers and Brutes attack the next blocking Wall, otherwise the core. They do
not intentionally target Turrets or SlowTraps in this slice. Turrets select the
living in-range enemy furthest along its route. SlowTrap effects refresh but do
not multiply. The first enemy-caused Wall destruction is recorded once.

The server freezes these current-run fields:

`Result`, `ChallengeId`, `ChallengeDuration`, `CoreHealthRemaining`,
`LeftLaneEnemyCount`, `RightLaneEnemyCount`, `LeftLaneCoreHits`,
`RightLaneCoreHits`, `FirstBreachTime`, `FirstBreachLane`,
`FirstBreachPadId`, `FirstBreachEnemyType`, `TotalWallDamageAbsorbed`,
`TotalTurretDamage`, `TotalEnemiesSlowed`, and `EnemiesReachedCore`.

Review displays four cards maximum: result/core health, lane traffic, first
breach, and aggregate defense contribution. Lane markers visualize traffic and
the first-breach pad is marked red. These are facts, not strategy instructions.

## Source architecture

The repository's established Script Sync mapping remains authoritative:

- shared contracts/config: `ReplicatedStorage/Shared/Game`;
- runtime remotes/state: `ReplicatedStorage/Game`;
- server systems: `ServerScriptService/Server/Game`;
- client entrypoint/controllers: `StarterPlayerScripts/Client`.

Use exactly the required seven server modules:

`GameStateService`, `BuildService`, `ChallengeService`, `RouteService`,
`EnemyService`, `DefenseService`, and `CombatStatsService`.

Remotes are `RequestBuild`, `RequestStartChallenge`,
`RequestReturnToPreparation`, and `StateChanged`. The server owns state, budget,
construction, routes, spawns, damage, health, first breach, outcome, and report.

## Acceptance matrix

| ID | Required observation |
| --- | --- |
| T01 | Clean startup in `PREPARATION`. |
| T02 | A fifth Turret is rejected by the eight-point budget. |
| T03 | Both lanes are used when neither contains a Wall. |
| T04 | Roamers use a fortified lane less often over a meaningful sample. |
| T05 | The Brute selects the walled lane and destroys a Wall. |
| T06 | `FirstBreach` is unique and matches lane, pad, time, and enemy type. |
| T07 | SlowTrap slows and refreshes without multiplicative stacking. |
| T08 | Turret targeting, server damage, and accumulated damage agree. |
| T09 | A build request during `DEFENDING` is rejected. |
| T10 | A duplicate start request cannot create a second challenge. |
| T11 | Victory transitions to `REVIEW`. |
| T12 | Defeat transitions to `REVIEW`. |
| T13 | The captured layout and full health are restored. |
| T14 | The player modifies the layout and starts a rematch. |
| T15 | Ten cycles leave no runtime residue, error, warning, or obvious growth. |
| T16 | A server and two clients share authoritative state and report. |
| T17 | About 150 ms simulated latency produces no duplicate operation. |
| T18 | Essential controls work through real touch on a small emulated screen. |

Every row receives `PASS`, `FAIL`, `PARTIAL`, or `UNKNOWN`; source inspection
alone cannot prove runtime behavior. Technical `PASS` additionally requires no
DataStore use, no publication, server authority, a bounded diff, and applicable
static checks passing.

## Human gate

After technical validation, test five to ten unbriefed players. Provisional
thresholds are 70% correctly naming the weakness, 50% modifying the base without
prompting, and 40% voluntarily rematching.

## Decision record — provisional pass without a human gate

Founder decision, 2026-07-15: an unbriefed human panel is not currently
available. Defense Loop 0.2 therefore receives `PASS TECHNIQUE` and
`PASS PROVISOIRE / GO CONDITIONNEL` for the next reversible slice. Human
comprehension remains explicitly `UNKNOWN`; this decision must never be reported
as a measured `PASS PRODUIT`.

The temporary replacement is a synthetic causal gate:

- compare deterministic baseline and modified layouts over repeatable seeds;
- require the rematch to improve at least two declared measures: core health by
  at least 150, first breach by at least 15 seconds, at least three fewer core
  arrivals, or a measurable reduction of damage on the weak lane;
- verify that the six-second Brute warning, route choice, unique FirstBreach,
  factual review, mobile controls, reset, and rematch stay exact;
- use independent zero-context visual reviews as supporting evidence only, never
  as a claim that human understanding was measured.

Defense Loop 0.3 may proceed provisionally only while its work remains narrow,
reversible, and free of persistence, progression, economy, monetization, or
content expansion. The first available real-player traffic must reopen the human
gate and measure understand → modify → rematch before any broader product claim.
