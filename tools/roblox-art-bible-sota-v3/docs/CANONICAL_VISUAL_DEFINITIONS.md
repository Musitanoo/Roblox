# Canonical Visual Definitions

## Outcome

No production 3D generation may decide what an object is.

The workflow first explores, compares and selects a solution. It then compiles
that solution into a closed, multimodal, versioned visual canon. Blender and
other generators become reconstructors of that canon.

Current implementation truth:

```text
objects                         6
art-direction territories       3
object x territory canons      18
required state definitions     48
selected territory             salvaged-frontier
current selected canon status  CANDIDATE
multimodal packet              0/6 current candidates fully bound
human lock                     PENDING
production canon gate          BLOCKED
```

Human-readable routing:

- `docs/OBJECT_REGISTRY.md` summarizes the exact selected six-object matrix;
- `docs/objects/` describes each selected object and applicable state;
- `docs/STATE_ONTOLOGY.md` separates integrity variants from runtime,
  interaction and transient state axes.

This is intentional. The founder selected Salvaged Frontier as the creative
identity. Earlier evidence packets remain historical evidence, but a candidate
revision changes the canon hash and therefore invalidates those packets for a
new lock. Every current candidate still needs a fresh complete packet and an
explicit human lock. Creative selection is never relabelled as production
approval.

## Precanonical input

Before a new canon is compiled, the optional precanonical workflow may turn a
functional brief into bounded visual proposals. Its prompt, constraints,
views, states, constitution and budget are hash-bound.

An imported Web image may be:

```text
REJECTED
REVISION_REQUIRED
PRECANONICAL_CANDIDATE
HUMAN_SELECTED
```

It may never be `CANONICAL`. `HUMAN_SELECTED` authorizes rationalization into
the contracts below; it does not replace them. Read
`docs/PRECANONICAL_WEB_WORKFLOW.md`.

## Authority chain

Every canon is compiled from exact hashes of:

- the accepted GDD product-art projection;
- the accepted retention and innovation doctrine;
- the object-product contracts;
- `art/art-direction.json`;
- the calibration kit;
- the shape language;
- the material rules;
- the selected territory grammar;
- the authored visual-canon source;
- the canon compiler.

Authority hash drift blocks canon regeneration.

## Source and generated contracts

Authored source:

```text
art/canonical-visuals/source.json
art/canonical-visuals/object-product-contracts.json
```

Generated source-of-truth contracts:

```text
art/canonical-visuals/<territory>/<asset>.json
art/canonical-visuals/catalog.json
```

The source separates:

- invariant object identity and gameplay meaning;
- falsifiable product and retention intent;
- primary visual states from runtime overlays, transients and terminal states;
- explicit gameplay truth and claim boundaries for every generated state;
- object-class-specific GPT Image 2 prompt discipline;
- all applicable states and transitions;
- territory-specific visual expression.

The compiler deterministically produces one complete canon for every
`asset x territory` pair and verifies the exact 18/48 coverage.

## What each canon contains

Each closed canon defines:

- identity, world role, affiliation, manufacture context and emotional intent;
- one-second function, orientation, interaction, danger and player relation;
- dimensions, pivot, tolerance and exact proportion rules;
- front, back, left, right, top, bottom, three-quarter and game-camera reads;
- landmarks, negative spaces and distance readability;
- primary, secondary and tertiary form hierarchy;
- stable semantic components and plausible assembly rules;
- territory shape, edge, detail, asymmetry, palette, material and wear grammar;
- material intent and semantic zones;
- every primary state, transition, component operation and gameplay-truth
  boundary;
- operational overlays, transient events and terminal runtime-only states;
- the retention hypothesis, intended player behavior, metric, failure
  condition, guardrails and current evidence status;
- invariant properties;
- bounded allowed variation;
- explicit forbidden outcomes;
- required visual boards;
- obligations, constraints, tolerances, prohibitions, identity locks and final
  output self-checks for generation;
- human approval and provenance.

## State contract

States derive from one component structure. They are not separately invented
assets.

The sixteen GPT Image 2 tasks are primary structural reference states only.
`REPAIRING`, `FIRING`, `SELECTED`, `HOSTILE`, `DISABLED`, transient events and
terminal `DESTROYED` or `DEFEATED` outcomes belong to separate runtime axes.
They are explicitly catalogued per object but excluded from primary generation
unless a later accepted contract authorizes a distinct reference.

Every generated state carries a `gameplayTruth` block that states:

```text
status
contractRef
trigger
capabilityEffect
collisionEffect
visualClaim
claimBoundary
```

A visual candidate may communicate posture, exposure or apparent severity. It
may not prove passability, collision, firing, tracking, damage, repair,
persistence or adaptive horde behavior that lacks an accepted gameplay
contract.

Allowed component operations are:

```text
PRESERVE
MOVE
ROTATE
EXPOSE
OPEN
BREAK
REMOVE
RECOLOR
EMIT
DEFORM
```

Every state carries redundant cues:

```text
shape
silhouette
value
color
light
motion
vfx
audio
```

Color is never the sole information channel.

## Required multimodal packet

A canon cannot be locked until all seventeen board families are hash-bound:

```text
orthographic
perspective
black_silhouette
component_breakdown
proportions
materials
semantic_zones
all_states
state_comparison
mobile_near
mobile_mid
mobile_far
lighting_matrix
repetition_1
repetition_30
repetition_100
required_and_forbidden_annotations
```

If a component or state is absent from every board, the canon is incomplete.

## Status lifecycle

```text
DRAFT -> CANDIDATE -> ACCEPTED -> LOCKED
                                  |
                                  +-> REVISED
```

- `DRAFT`: incomplete; generation forbidden.
- `CANDIDATE`: complete textual contract; exploration allowed.
- `ACCEPTED`: human-selected solution; final evidence may still be assembled.
- `LOCKED`: visual packet complete and human approval bound to its digest.
- `REVISED`: approved new version with an explicit reason.

The lock is stored as a separate overlay under:

```text
art/canonical-visuals/locks/<territory>/<asset>.json
```

This preserves the evaluated candidate and prevents a result from silently
rewriting its own requirements.

## Generation authority

Before Blender runs, `prepare_canon_generation.py` creates a
`generation-authority` envelope containing:

- mode: `EXPLORATION` or `PRODUCTION`;
- scope: `calibration` or `transfer`;
- territory;
- catalog hash;
- compiler path and hash;
- canon IDs, paths, statuses and hashes.

Exploration accepts `CANDIDATE`. Production accepts only:

```text
LOCKED + visual packet COMPLETE + human approval APPROVED
```

The canonical wrapper fails before Blender when that condition is not met.

After Blender, `build_canon_compliance.py` binds the exact build report hash to
the exact canon hash and reports geometric, visual, functional, technical,
perceptual and human compliance separately.

Functional compliance is not inferred from triangle counts. Blender runs
`tools/blender/inspect_component_evidence.py` against the saved `.blend` and
records every semantic object name, material role and detail band. The
versioned adapter `art/calibration/component-evidence-map.json` maps those
implementation names to stable canonical component IDs. Both the readback
report and adapter SHA-256 are embedded in the compliance report. The adapter
may explain how a component is found; it may not redefine the component.

## Commands

```powershell
.\scripts\art-direction.ps1 canons
.\scripts\art-direction.ps1 validate-canons

# Expected to fail until selection and human lock.
.\scripts\art-direction.ps1 validate-canons -RequireLockedCanons

# Candidate-bound exploration.
.\scripts\art-direction.ps1 build -RenderMode full -Resume

# Locked production preflight.
.\scripts\art-direction.ps1 build -RenderMode full -RequireLockedCanons

# Per-asset REAL_RENDERED 17-board packet. Add --force to rebuild both raw runs.
.\scripts\r3d.ps1 canon-packet `
  .\assets-3d\defense-barricade-small\asset.json
```

The packet command writes a hash-bound `evidence-manifest.json`, a pending
`human-review.json` and an ergonomic `index.html`. Its cache is reusable only
when the contract, canon, source blend, build manifest, renderer and every raw
PNG still match. Automated success never changes `productionApproved`.

Lock dry-run:

```powershell
.\scripts\art-direction.ps1 lock-canon `
  -Asset <asset> `
  -Territory <selected-territory> `
  -CanonEvidence <visual-evidence-manifest.json> `
  -HumanReview <human-review-completed.json>
```

Add `-Apply` only after the founder has selected the territory and the evidence
manifest contains every required board with current hashes. The interactive
gallery produces the review file only after all seventeen boards, all seven
mandatory gates, reviewer identity, decision and justification are complete.
The lock command imports and hashes that file; command-line text alone cannot
apply a real production lock.

## Per-asset r3d binding

An r3d `asset.json` now includes:

```json
{
  "visualCanon": {
    "canonId": "vc_barricade__industrial-toy-defense__v1",
    "assetId": "barricade",
    "territoryId": "industrial-toy-defense",
    "path": "art/canonical-visuals/industrial-toy-defense/barricade.json",
    "sha256": "<sha256>",
    "minimumStatus": "CANDIDATE",
    "productionStatus": "LOCKED"
  }
}
```

The contract validator checks identity, hash, status and dimensions. Blender
records the canon ID/hash in provenance and the build manifest. Publication
rejects stale canon-bound build evidence.

## Failure routing

When output differs from the canon, classify the cause before changing
anything:

1. canon incomplete or contradictory;
2. generator failed a correct canon;
3. technical constraints make the canon infeasible;
4. territory grammar was translated incorrectly;
5. object fails in real gameplay context.

If the canon must change, create a reviewed revision. Never edit requirements
silently to make an existing model appear compliant.
