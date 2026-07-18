# Roblox Top 1 — Art Direction and 3D Asset Workflow v3

This package is the production-oriented, evidence-first art-direction and 3D
asset workflow for Roblox Top 1. It combines:

- a closed art-direction library;
- a hash-bound precanonical ChatGPT Web visualization layer with strict quota,
  provenance and human-authority boundaries;
- 18 closed canonical visual definitions covering every object x territory
  pair and all 48 applicable states;
- a deterministic Blender compiler and render matrix;
- a bounded, transactional Blender Visual Workbench MCP for inspection,
  reversible experiments and deterministic source-reproduction proof;
- a per-asset r3d compiler and guarded staging publisher;
- Roblox Studio staging, Golden Scene, reimport, repetition, and capture tools;
- distinct simulator, physical-device, and human approval gates;
- a discoverable roblox-3d-asset Codex skill;
- a hash-verified, staged installer.

## Current truth

~~~text
specification            PASS
static verification      PASS
precanonical workflow    PASS (local contracts, preflight, handoff, intake and review)
Blender execution        PASS
Blender evidence         BUILD_PLUS_CANON_PACKET (barricade r6 REAL_RENDERED 17/17)
Blender Workbench MCP    PASS_LOCAL_VERTICAL_SLICE
Roblox Studio evidence   UNKNOWN for selected v1 constitution
Studio simulator report  PARTIAL
physical mobile evidence BLOCKED
human selection          PASS (founder strategic authority)
blind study              INCOMPLETE / not used as decision proof
sixth-asset transfer     PARTIAL (current automation PASS, human approval pending)
transfer Cloud staging   UNKNOWN for selected constitution
transfer Studio staging  UNKNOWN for selected constitution
visual canon contracts   PASS (18 canons / 48 states, deterministic)
visual canon lock        SELECTED_PARTIAL (one packet complete; six human locks pending)
final territory          salvaged-frontier
production approved      false
~~~

The founder has frozen the creative direction:

> Salvaged Frontier defines the world identity; Industrial Toy Defense imposes
> the readability discipline.

Read `docs/SALVAGED_FRONTIER_ART_BIBLE.md` and the strict
`art/selected/salvaged-frontier-constitution.json`.

The complete human documentation map starts at `docs/README.md`. It routes to
the current status contract, state ontology, six-object registry, individual
object sheets, Roblox/Blender contracts, visual metrics, evidence and
governance without duplicating machine authority.

The workflow implementation remains usable for preproduction. Production
approval remains false because the optimized selected grammar still requires
six complete canon board locks, refreshed Studio evidence, a named low-tier
physical mobile run, and final human approvals.

## Historical v3.7 evidence baseline

The following evidence proved the pre-selection three-territory pipeline. It is
retained as engineering history, not claimed as current visual approval for the
optimized selected constitution:

- 39 applicable territory/asset/state variants built and exported.
- 1,263 full-matrix renders plus six repetition stress renders.
- Two-run Blender semantic and GLB determinism for every variant.
- Three Studio Golden Scenes validated in the confirmed staging place.
- Twelve hash-bound Studio captures across four lighting profiles.
- Import v1 and reimport v2 passed while preserving Roblox-owned properties.
- A/B benchmark scenes for graybox/candidate at 30 and 100 repetitions.
- Exact Studio Device Simulator readbacks at 640×360 and 360×640.
- Independent `turret_fast_v1` transfer compiler: 9 builds, 9 deterministic
  GLBs, 108 renders, 51 portable territory artifacts, 3 review artifacts, and
  automated score 100/100 across all three territories.
- Nine immutable transfer candidates published to the allowlisted staging
  creator, remotely reread, and preserved in a resumable local-only registry.
- Transactional Studio integration of all nine candidates with canonical GLB
  bounds, non-empty MeshIds, 59 canonical material-role bindings, separate
  hitboxes, six 30/100 reuse groups, Client/Server playtest, zero new relevant
  console errors, and return to Edit.
- Three transfer-specific Studio viewport captures, one per territory, bound
  to the portable report by path, byte count and SHA-256.
- Eighteen canon-compliance reports pass canon binding, geometry, technical
  budgets, and per-state semantic component readback. Visual boards and human
  authority remain separate open gates.
- The current automated test counts are emitted by `verify_static.py`; they are
  not frozen in this document because every new closed contract adds regression
  cases.
- 60 JSON Schemas and 59 canonical manifest instances.
- StyLua, Selene, and Luau LSP verification on the applicable Studio sources.

Studio screen capture proved all four isolated benchmark views for the v3.7
candidate set. LibMP still
produced valid snapshots with a zero-frame range and SceneAnalysisService was
disabled in the active runtime. Those two capabilities remain blocked and are
never converted into fabricated performance metrics.

## One-command developer workflow

~~~powershell
.\scripts\art-direction.ps1 bootstrap
.\scripts\art-direction.ps1 doctor
.\scripts\art-direction.ps1 precanon-preflight -Request <request.json> -Output <preflight.json>
.\scripts\art-direction.ps1 precanon-browser-doctor -BrowserAdapter codex_iab -Output <browser-doctor.json>
.\scripts\art-direction.ps1 precanon-handoff -Request <request.json> -Preflight <preflight.json> -BrowserDoctor <browser-doctor.json> -Output <handoff.json>
.\scripts\art-direction.ps1 precanon-operator -Request <request.json> -Output <operator-dir>
.\scripts\art-direction.ps1 precanon-campaign-init -Output <campaign-dir>
.\scripts\art-direction.ps1 precanon-campaign-operator -Campaign <campaign.json> -Output <operator-runtime>
.\scripts\art-direction.ps1 canons
.\scripts\art-direction.ps1 validate-canons
.\scripts\art-direction.ps1 workbench -RenderMode full -Resume
.\scripts\art-direction.ps1 simulate-workflow -Resume
.\scripts\art-direction.ps1 transfer -Open
.\scripts\art-direction.ps1 publish-transfer
.\scripts\art-direction.ps1 stage-transfer
.\scripts\art-direction.ps1 prepare-study -Open
~~~

The workbench generates Studio configuration, validates contracts, resumes
hash-current Blender builds, produces the full review matrix, builds the Studio
import queue, verifies A/B determinism, builds the review gallery, and runs both
test suites.

The per-asset command below renders two raw Blender runs, verifies their raster
determinism, composes the exact seventeen canonical board families twice and
writes a hash-bound review gallery:

~~~powershell
.\scripts\r3d.ps1 canon-packet `
  .\assets-3d\defense-barricade-small\asset.json
~~~

Its `PASS` is automated evidence only. The generated human review remains
`PENDING`, and the command never locks a canon or approves production.
The gallery stores review progress locally, requires 17 board decisions and
seven mandatory gates, then downloads a digest-bound
`human-review-completed.json`. The production lock imports and validates that
file instead of trusting free-form command-line approval text.

`simulate-workflow` exercises the complete twelve-stage workflow without human,
browser, Studio, device, secret, network, or cloud mutation. Synthetic evidence
is confined to `build/simulations/complete-workflow/`; it may prove the
simulation mechanics, but can never approve production. A successful run must
therefore report `simulationStatus=PASS`, `realProductionStatus=BLOCKED`, and
`productionApproved=false`.

The precanonical branch is documented in
`docs/PRECANONICAL_WEB_WORKFLOW.md`. It compiles a gameplay brief into a
stage-bounded request, verifies hashes and budget without consuming quota, and
verifies the app-managed local Browser runtime, then produces a sanitized
task-scoped handoff. The browser remains transport only.
`codex_chrome` is the default and the only attachment-capable adapter;
`codex_iab` is an explicitly selected fallback for attachment-free handoffs,
with preflight blocking any incompatible request. Local runtime health never
proves that the current Codex task exposes `mcp__node_repl__js`; handoffs remain
`AWAITING_TASK_BROWSER_CAPABILITY` until that task-scoped capability is
observed.
When the six selected objects and all their states are being defined,
`precanon-campaign-init` and `precanon-campaign-operator` are the official
semi-automatic path. The campaign contains exactly sixteen object-state tasks,
requires one visibly confirmed `gpt-image-2` generation per task, binds every
later state to the accepted previous state of the same object, and advances
immediately after review. `precanon-operator` remains the compatible
single-request route for historical or isolated evidence. Both routes are
loopback-only and handle exact prompt copying, human result drop, immutable
import and review without API usage or hidden browser control.
Downloaded images are imported with conservative provenance and can be marked
`HUMAN_SELECTED` only as input to canonicalization; they can never be marked
canonical or production-approved directly.

`canons` deterministically compiles the 18 object x territory contracts.
`validate-canons -RequireLockedCanons` is the production preflight and is
expected to remain blocked until all six Salvaged Frontier canons bind their
complete multimodal boards and their human approvals are hash-bound. The
territory choice itself is already frozen by founder authority. Read
`docs/CANONICAL_VISUAL_DEFINITIONS.md`.

`transfer` is the one-command sixth-asset gate. It builds `turret_fast_v1`
twice per territory for deterministic comparison, executes one 36-render full
pass per territory, packages portable evidence, measures readability, and
opens the comparison gallery. It exits successfully when automated evidence
passes while preserving `PARTIAL` until a selected territory and a hash-bound
human approval exist. Add `-RequirePass` only when validating a genuinely
signed final transfer decision.

`publish-transfer` and `stage-transfer` are safe dry-runs by default. The
external staging write requires `-ConfirmPublish`; the transactional Studio
write requires `-Apply`. Neither command selects a final territory or prints
raw Roblox identifiers.

`prepare-study` crée deux ZIP distribuables sans identité de territoire,
douze affectations participantes équilibrées, quatre affectations expertes,
une carte aléatoire privée, les preuves techniques liées par hash et l’espace
de scellement. Après placement des sessions JSON dans leurs dossiers,
`seal-study` valide les matrices complètes et lie le dataset scellé à la carte
privée. Lire `docs/BLIND_STUDY_PROTOCOL.md`. Aucune commande ne sélectionne
automatiquement un territoire.

For one asset:

~~~powershell
.\scripts\r3d.ps1 doctor --repo .
.\scripts\r3d.ps1 validate .\assets-3d\defense-barricade-small\asset.json
.\scripts\r3d.ps1 compile .\assets-3d\defense-barricade-small\asset.json
.\scripts\r3d.ps1 compile-states .\assets-3d\defense-barricade-small\asset.json
.\scripts\r3d.ps1 verify-states .\assets-3d\defense-barricade-small\asset.json
.\scripts\r3d.ps1 blender-inspect .\assets-3d\defense-barricade-small\asset.json --repo .
.\scripts\r3d.ps1 publish .\assets-3d\defense-barricade-small\asset.json --dry-run
~~~

`compile-states` materializes one topology-preserving build per canonical state
and creates an ergonomic comparison board. `verify-states` recompiles every
state twice, validates state invariants and distinctness, and refuses the
published board if any GLB, geometry report, semantic hash or rendered pixel
differs from the deterministic references. FBX integrity is bound to each
state manifest because FBX retains normalized source-path length across
different output roots.

`r3d report` also validates every path declared by `review.json`. A review
cannot retain `PARTIAL` or `PASS` when its asset identity, revision or evidence
files are missing, stale or outside the asset root. A declared visual `PASS`
additionally requires both automated and human review to be `PASS`.

Cloud mutation requires the separate --confirm-publish flag and a staging
creator present in the local allowlist. Secrets are never included in reports.

## Evidence validators

~~~powershell
.\scripts\art-direction.ps1 validate-studio -Report <studio-report> -RequirePass
.\scripts\art-direction.ps1 validate-simulator -Report <simulator-report>
.\scripts\art-direction.ps1 validate-mobile -Report <physical-device-report> -RequirePass
~~~

Simulator evidence cannot be passed to the physical-device validator.

## Package and installation

~~~powershell
.\scripts\art-direction.ps1 package -Output ..\roblox-art-bible-sota-v3.zip
.\scripts\install-workflow.ps1 -TargetRepo C:\Project\Roblox
~~~

The installer automatically reuses the source `.venv` Python when available.
From a clean extraction, pass `-PythonPath` or set `ART_PYTHON` when no real
Python 3 interpreter is discoverable from PATH.

The installer verifies every source SHA-256, copies to a staging directory,
bootstraps and tests that staged copy, then activates it. Existing workflow,
skill, wrapper, per-asset pipeline, or reference asset contract paths require
-Replace and are moved to timestamped backups. The installed reference
contract resolves its canon from the installed workflow package, so
`scripts/r3d.ps1` and the art-direction wrapper consume the same visual source
of truth.

## Interpretation

Blender is preflight evidence; Studio is the renderer of record. Studio
simulation is not physical hardware. Automated visual review is not the final
art decision. Start with `docs/README.md` and `docs/STATUS_CONTRACT.md` before
changing a gate. Verification and visual-audit documents are recorded
snapshots, not current-status authority.
