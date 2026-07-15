# Defense Loop 0.2

## Product question

Defense Loop 0.2 must answer one question: after a second route and one wall-breaking Brute expose a real weakness, can the player understand the short autopsy, modify the four-pad layout, and observe a better rematch?

This is still one voluntary challenge and one graybox arena. It does not validate adaptive hordes, progression, persistence, free placement, or content scale.

## Player-visible loop

1. In `PREPARATION`, configure the same four pads as `Empty`, `Wall`, or `Turret`.
2. Start the single available challenge voluntarily.
3. Standard zombies pressure the primary route while a clearly telegraphed Brute pressures the secondary route and attacks nearby walls.
4. Finish in victory or defeat for a readable spatial reason.
5. In `REVIEW`, see a compact autopsy naming the most damaging route and the Brute's structural impact.
6. Return to `PREPARATION`, modify at least one pad, and rematch immediately.
7. Observe whether the changed layout improves the relevant metric.

## Fixed content budget

- Two routes: the existing primary lane plus one new secondary lane.
- Two enemy types: `BasicZombie` and `Brute`.
- Three waves in the existing 90–150 second target.
- Four existing BuildPads; no extra pad and no free grid.
- One challenge only; no difficulty selector.
- One compact autopsy panel; no history, analytics backend, reward, or recommendation engine.

All health, damage, movement, spawn composition, and timing values remain centralized in shared configuration modules.

## Architectural weakness to test

The two routes must create a genuine coverage tradeoff. A layout concentrated on the primary route leaves the secondary route materially weaker. The Brute must make that weakness visible by prioritizing and damaging a nearby wall; it must never teleport, receive hidden buffs, or select a route adaptively.

The graybox must make both routes, their spawn origins, and their relationship to the four pads visible before the challenge starts. The intended weak route must be reproducible from configuration, not chosen from player telemetry.

## Elementary autopsy

The server records bounded counters for the current challenge only:

- enemies reaching the core per route;
- core damage attributed per route;
- wall damage caused by the Brute;
- first structure destroyed, including its cause when known.

`REVIEW` displays only:

- victory or defeat and remaining core health;
- the route that caused the most core damage, or `Aucune` if neither did;
- the Brute's wall damage and first destroyed structure;
- `Modifier et retenter`.

Tie-breaking must be deterministic and documented. No persistent history is stored. The client renders replicated server results and never computes the diagnosis.

## Server authority and limits

- Extend the existing four services; do not add a fifth service.
- Reuse `RequestBuild` and `RequestStartChallenge`; no new client remote is required.
- The server selects enemy type and route from immutable wave configuration.
- Spawn requests remain bounded by `maxActiveEnemies` and the challenge run token.
- Enemy type and route identifiers are validated against shared closed sets.
- Brute damage, wall targeting, counters, results, snapshot restoration, and phase transitions remain server-owned.
- Runtime counters are cleared on every start and every return to preparation.

## Explicit exclusions

Do not add DataStore, progression, rewards, multiple difficulties, adaptive route selection, adaptive horde logic, free placement, new defenses, player weapons, repair, farming maps, inventory, crafting, trading, monetization, final art, commercial audio, external assets, or publication.

## Acceptance contract

The slice is `PASS` only when all applicable checks are observed:

1. Both routes are visible and used by server-spawned enemies.
2. `BasicZombie` and `Brute` are visually distinguishable before contact.
3. The Brute attacks a nearby wall and deals configured server-owned damage.
4. Standard zombies retain the 0.1 movement, wall interaction, and core behavior.
5. Enemy type and route are selected only by server wave configuration.
6. Invalid enemy types, route identifiers, duplicate starts, and builds during `DEFENDING` fail closed.
7. Concentrating defenses on the primary route produces the expected secondary-route weakness.
8. Review attributes match observed route/core/wall events.
9. The autopsy names the materially weak route for the baseline weak layout.
10. Returning to preparation clears both enemy types and all current-run counters.
11. The exact defensive snapshot is restored before modification.
12. After a relevant pad change, rematch improves at least one declared metric: remaining core health, secondary-route core damage, secondary-route arrivals, or Brute wall damage.
13. The autopsy updates to reflect the rematch rather than retaining stale values.
14. Victory and defeat remain reachable for understandable configurations.
15. Ten alternating baseline/rematch cycles complete without retained runtime instances or new Output warnings/errors.
16. Solo and Server & Clients with two clients observe the same authoritative state and review.
17. With 200 ms simulated incoming replication lag, no duplicate challenge or stale review is produced.
18. A real touch sequence in iPhone landscape opens the build menu, changes a defense after review, launches the rematch, and keeps the autopsy controls in bounds.
19. The complete 0.1 regression checklist still passes.
20. No publication or persistence API access occurs.

No check may be promoted to `PASS` from source inspection alone.

## Stop conditions

Stop and reassess instead of expanding scope if either route cannot be understood in graybox, the Brute requires a new pathfinding framework, the autopsy cannot be derived from bounded server events, or the modified layout has no observable causal effect after tuning within the fixed content budget.

## Graybox milestone evidence

The first 0.2 milestone is complete without gameplay changes:

- `Lane02` uses exactly four direct navigation Parts on the left flank, with blue-black asphalt, cyan borders, and cyan forward arrows.
- `EnemySpawn02` is an orange Neon 7×0.5×7 Part at `(-18, 0.25, 27)` labeled `ROUTE 2 / ENTRÉE BRUTE`.
- The primitive `Brute` is 12.1×11.2×5.73 studs versus 4.85×6.45×3 for `BasicZombie`, with a wide armored silhouette, oversized shoulders/fists, red eyes, and no Script.
- Observed overview and close-up Studio views kept route 1 identifiable by yellow arrows/red entrance, route 2 by cyan/orange, and the Brute by silhouette plus `BRUTE • BRISE-MURS`.
- A temporary Workspace clone used for close-up inspection was deleted before delivery.
- A 0.1 smoke start remained in `PREPARATION` with core 500, two remotes, zero runtime enemies, the complete client UI, and zero server/client runtime warning or error.

No 0.2 enemy spawning, movement, damage, wave, counter, autopsy, or client behavior exists yet.
