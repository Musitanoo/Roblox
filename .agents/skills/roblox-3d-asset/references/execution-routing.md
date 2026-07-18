# Execution routing

## Contents

1. Command discovery
2. Art-direction engine
3. Per-asset engine
4. Route selection
5. Safe publication

## Command discovery

From the repository root, verify the actual surfaces:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 help
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 --help
~~~

Use `help` as the canonical discovery command. Windows PowerShell 5.1 may
consume `-?` before a script launched with `-File` can observe it, so `-?` is
not a reliable wrapper contract. `--help` is the supported alias. Help must
exit successfully without executing a workflow command.

Use only commands shown by the checked-in version. Prefer the package-local Python environment and pinned Blender/Rokit versions.

## Art-direction engine

Typical evidence-first sequence:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 doctor
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 precanon-init -Brief <brief> -RequestId <id> -Output <dir>
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 precanon-preflight -Request <request.json> -Output <preflight.json>
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 precanon-browser-doctor -BrowserAdapter <codex_iab|codex_chrome> -Output <browser-doctor.json>
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 precanon-handoff -Request <request.json> -Preflight <preflight.json> -BrowserDoctor <browser-doctor.json> -Output <handoff.json>
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 precanon-operator -Request <request.json> -Output <operator-dir>
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 canons
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 validate-canons
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 validate
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 validate-luau
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 workbench -RenderMode full -Resume
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 verify-blender
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 transfer -Open
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 publish-transfer
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 stage-transfer
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 prepare-study
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 test
~~~

Validate Studio, simulator, and physical-device reports with their distinct commands. Never pass a simulator report to the physical-device validator.

Use the `precanon-*` commands before compiling a new visual canon when the
object still needs visual exploration. The handoff is a dry transport contract:
it never opens a browser, submits a prompt or consumes quota. Actual browser
submission requires current user authorization, a local Browser doctor bound
to the exact official adapter, and visible current-task exposure of
`mcp__node_repl__js`. Local installation health does not prove task exposure.
`codex_iab` is allowed only for attachment-free handoffs; any hash-bound upload
requires `codex_chrome`. Import the downloaded local file with
`precanon-import`, then record one of the four bounded decisions with
`precanon-review`.

If task Browser control is unavailable, use `precanon-operator` instead of
retrying setup. This supported route recomputes preflight, opens a local
loopback interface, composes one exact submission text, accepts one explicit
human-dropped result, performs the normal import and exposes the same review
decisions. `-DryRun` prepares and validates the operator session without
opening or serving the interface.

Use `transfer` when proving that a frozen territory grammar generalizes to the
independent `turret_fast_v1` challenge. Its normal success criterion is an
automated PASS with global `PARTIAL` while human selection is pending. Use
`-RequirePass` only after a real, hash-bound human review exists.

Use `canons` to compile the 18 object x territory visual contracts and
`validate-canons` to prove deterministic 18/48 coverage. Use
`validate-canons -RequireLockedCanons` or `build -RequireLockedCanons` only for
production authorization; those commands must remain blocked while the final
territory, complete visual boards, or human locks are missing.

Use `lock-canon` only after the founder selected the final territory. It is a
dry-run without `-Apply` and requires a complete hash-bound visual evidence
manifest plus the completed `human-review-completed.json` downloaded from the
packet gallery. A real apply rejects pending boards, pending mandatory checks,
contradictory decisions, digest drift and simulated reviewer identities.

Use `prepare-study` only after the three full-render matrices and Studio
evidence are current. It creates separate participant and expert ZIPs,
anonymized stimuli, twelve participant slots, four expert slots, a private
label map and an operator workspace. Never distribute `private/` or
`operator/`. Use `seal-study` only after the raw JSON sessions have been
returned; it validates complete matrices and binds their exact hash to the
private map before `score`.

Use `publish-transfer` to inspect the sanitized nine-candidate staging plan.
Use `publish-transfer -ConfirmPublish` only when the current user request
explicitly authorizes external staging mutation. The command never decides the
final territory and never prints raw Roblox identifiers.

Use `stage-transfer` for the read-only Studio plan and `stage-transfer -Apply`
for the explicitly authorized staging mutation. It requires one Edit-mode
Studio instance and applies a rollback-capable swap only after all nine
insertions pass source, bounds, MeshId, render, collision, hierarchy and
staging-identity checks.

## Per-asset engine

Discover its current help, then use the smallest applicable sequence:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 doctor --repo .
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 validate .\assets-3d\<asset-key>\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 compile .\assets-3d\<asset-key>\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 compile-states .\assets-3d\<asset-key>\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 verify-states .\assets-3d\<asset-key>\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 canon-packet .\assets-3d\<asset-key>\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 blender-mcp-doctor --repo .
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 blender-inspect .\assets-3d\<asset-key>\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 blender-workbench .\assets-3d\<asset-key>\asset.json --mode explore
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 publish .\assets-3d\<asset-key>\asset.json --dry-run
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 report .\assets-3d\<asset-key>\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 test
~~~

Use --confirm-publish only when publication is explicitly authorized in the current request.

The per-asset contract must reference the exact visual canon ID, territory,
path and SHA-256. Validation, Blender provenance, the build manifest and
publication preconditions must agree on that binding.

Use `canon-packet` after state compilation to render, compose and verify the
exact seventeen-board multimodal evidence package. Its normal automated success
is `REAL_RENDERED` with human review still `PENDING`; it never locks the canon
or sets production approval. Use `--force` only when the two raw Blender passes
must be intentionally rebuilt instead of reusing their hash-bound cache.

Use the Blender Visual Workbench only after a deterministic build exists. Start
with `blender-inspect`; create an `EXPLORE` session only for a measurable visual
problem. Preview does not save Candidate. Apply writes only Candidate and must
retain rollback. Translate an accepted change set to deterministic source, then
run `blender-verify-promotion` against the exact authoritative contract before
considering the change reproducible. The prepared promotion sandbox is the
expected source, not a substitute for it: verification must fail before source
transcription, then compare the authoritative path, revision, canon binding and
semantic source exactly, compile that authoritative source twice and reproduce
every candidate operation. This technical `PASS` still grants no Studio,
human-art or production approval.

## Route selection

- mechanical/modular/repeated: deterministic parametric Blender builder;
- human-owned source mesh: immutable source plus cleanup/reconstruction;
- organic/irregular exploration: generated reference, then controlled rebuild;
- rigged/deforming: asset-specific rig extension plus pose/deformation tests;
- temporary prototype: Studio procedural model, production approval forbidden.

Do not decimate a poor generated mesh and call it production cleanup.

## Safe publication

Before any external write:

1. Confirm the place and creator are staging-only without printing their values.
2. Confirm credentials by presence only.
3. Run publication dry-run and review the action.
4. Require current user authorization for the confirmed call.
5. Poll bounded operations and sanitize stored responses.
6. Preserve Package/asset identity across v2 when the update path is under test.
7. Prove the visual delta and wrapper preservation independently.
