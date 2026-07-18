---
name: roblox-3d-asset
description: Create, revise, audit, validate, publish, integrate, or benchmark production Roblox 3D assets with the repository's deterministic Blender compiler, art-direction workbench, Studio staging workflow, evidence contracts, and mobile/human gates. Use for Roblox props, MeshParts, Packages, modular kits, buildings, weapons, machines, stylized vegetation, hard-surface or organic meshes, pivots, UVs, materials, collisions, damage states, LOD, mobile readability, reimport, asset performance, or 3D QA. Do not use for terrain-only work, 2D UI, thumbnails, or unrelated gameplay scripting.
---

# Roblox 3D Asset

Operate the repository's evidence-first asset factory. Codex orchestrates, Blender compiles deterministic geometry, Roblox Studio stages and tests, and humans retain final art authority.

## Read the applicable contract

Always read:

- [evidence-and-gates.md](references/evidence-and-gates.md)
- [execution-routing.md](references/execution-routing.md)

Read only when applicable:

- [precanonical-web.md](references/precanonical-web.md) before using ChatGPT
  Web Images for visual exploration or correction.
- [studio-mobile-human.md](references/studio-mobile-human.md) before Studio work, performance claims, device validation, or art approval.
- [platform-facts.md](references/platform-facts.md) before publication, Package behavior, platform limits, or other time-sensitive claims.
- [BLENDER_MCP_WORKBENCH.md](../../../docs/BLENDER_MCP_WORKBENCH.md) before
  interactive Blender inspection, visual diagnosis, bounded experimentation,
  rollback, or source-promotion verification.

## Establish truth before action

1. Find the repository root and read every applicable AGENTS.md or override.
2. Inspect git status, target asset files, plans, the art lock, and existing evidence.
3. Determine the active Studio synchronization authority before editing scripts.
4. Discover the checked-in commands with --help; never invent a command or tool path.
5. State the developer-visible outcome and observable acceptance criteria.
6. Create or update an ExecPlan for production assets, publication, cross-cutting tooling, or uncertain integration.

During workflow development, edit and validate the active checked-in copy in
place. Do not repeatedly uninstall, reinstall or rebuild release archives.
Packaging and staged installation are explicit release checkpoints, except
when the task is specifically testing bootstrap, dependency or installation
behavior.

Keep separate:

~~~json
{
  "specificationStatus": "PASS",
  "implementationStatus": "UNKNOWN",
  "productionApproved": false
}
~~~

Never infer implementation success from a complete specification.

## Select one operating mode

- vertical_slice: prove a complete asset lifecycle when the factory or update path is not yet proven.
- create: produce a new asset against an accepted art direction.
- revise: change stable source while preserving names, pivots, wrapper contracts, and registry identity.
- family: derive related variants from one parametric source.
- prototype: explore quickly; forbid production approval.
- audit: inspect and report; do not mutate unless the user also requested changes.

Route the first unproven create/revise request through vertical_slice.

## Use the two checked-in engines

Treat these surfaces as complementary:

- scripts/art-direction.ps1: art-direction contracts, render matrix, candidate comparison, Blender determinism, Studio evidence, simulator evidence, and packaging.
- scripts/r3d.ps1: one asset's contract, compile, publication dry-run/confirmation, and final report.

If either required surface is absent, report BLOCKED; do not substitute remembered code. Never copy a second compiler into the skill.

## Execute the production sequence

1. Validate the art-direction library and confirm whether it is exploration or locked.
2. Create the asset contract, provenance, registry, and ExecPlan.
3. For the selected six-object corpus, compile the object-by-state
   precanonical campaign before any Web action. It must cover exactly the
   sixteen applicable states and require one distinct `gpt-image-2`
   generation per object-state. Use a standalone bounded request only for
   isolated exploration or historical evidence.
4. Run the precanonical Browser doctor for the exact selected adapter. Treat
   local installation health and current-task tool exposure as separate gates.
   A local `PASS` never proves that the task exposes `mcp__node_repl__js`.
5. When visual exploration is needed and explicitly authorized, use the
   sanitized ChatGPT Web handoff. Submit automatically only when the current
   task visibly exposes the required tool and backend. Otherwise use
   `precanon-campaign-operator` for the selected corpus: the human copies the
   exact bound text, confirms visible `gpt-image-2`, submits one generation,
   downloads one result and drops it into the loopback-only interface.
   Accepted reviews advance automatically; revisions stay on the same state.
   Use `precanon-operator` only for a standalone request. Preflight, hashing,
   import, provenance and review remain automated. Never infer quota, hidden
   geometry or authority.
6. Generate bounded silhouette candidates unless an immutable accepted reference exists.
7. Select the candidate through the applicable human gate. Web imagery may
   receive `HUMAN_SELECTED` only as input to canonicalization, never
   `CANONICAL`.
8. Compile a closed visual canon for the exact object x art direction. Cover identity, one-second read, every view, proportions, components, materials, semantic zones, every state and transition, invariants, allowed variation, and explicit prohibitions.
9. Bind the complete multimodal board packet and human approval before marking a canon LOCKED. Never silently edit a canon to match an output.
10. Create a pre-generation authority envelope containing the exact canon and compiler hashes. Candidate canons authorize exploration only; production requires LOCKED + COMPLETE + APPROVED.
11. Compile from recipes or accepted source with pinned Blender, seed, axis mapping, budgets, and the bound canon.
12. When visual diagnosis or correction is needed, open the Blender Visual
    Workbench against the exact compiled hash. Use `OBSERVE` before `EXPLORE`,
    express every mutation as a bounded change set, prove rollback, and
    promote only through the deterministic source. Never treat Candidate as
    production source.
13. Block on deterministic geometry, transform, UV, material, naming, dimension, pivot, component, state, and file-size failures.
14. Render the standardized matrix, including exact-pixel mobile landscape and portrait views.
15. Produce a canon compliance report for geometric, visual, functional, technical, perceptual, and human requirements.
16. Review silhouette, function, state cues, material hierarchy, repetition, lighting, and severe artifacts.
17. Stage only in the confirmed staging place; preserve the runtime wrapper and simple collision authority.
18. Run reimport/update proof, 1/30/100 repetition checks, console inspection, and applicable Studio analysis.
19. Keep simulator structure/visual evidence separate from physical-device metrics.
20. Prepare the final art-direction decision through the blinded study kit:
    anonymized labels, balanced timed participant tasks, separate expert review,
    private mapping, raw-session preservation and sealed hashes. Never expose
    territory identities to reviewers or automatically select the winner.
21. Require human approval where the contract demands it.
22. Generate a hash-bound final report and explicitly list every skipped, blocked, unknown, or failed proof.

When the task is to freeze or audit the art bible itself, run the independent
sixth-asset transfer command after the five-asset calibration matrix. Do not
add `turret_fast_v1` to the calibration compiler: its separation is what makes
the transfer evidence meaningful.

Do not publish unless the current request authorizes publication and the publisher's explicit confirmation flag is used. A dry run is not publication proof.

For the frozen transfer challenge, use `publish-transfer` before
`publish-transfer -ConfirmPublish`, then `stage-transfer` before
`stage-transfer -Apply`. Preserve the raw staging identity registry outside the
replaceable package under the host repository's gitignored
`assets-3d/registry/*.local.json`.

## Non-negotiable asset rules

- Gameplay readability outranks micro-detail.
- Silhouette and proportions outrank texture complexity.
- Never promote a first AI-generated mesh directly to production geometry.
- Never promote a Web-generated image directly into a visual canon.
- Never consume Web quota before the current precanonical preflight and local
  Browser doctor pass their own applicable checks.
- Never interpret an installed plugin, configured MCP server or healthy native
  host as proof that the current task exposes browser control.
- Never require Browser/Chrome plugin health for the explicit human operator
  route; it is task-browser-independent and loopback-only.
- Never retry, switch to imagegen/API, or invent a model name automatically.
- Never combine several gameplay states in one primary generation. Require one
  generation per object-state and derive every later state from the accepted
  previous state of the same object.
- Prefer parametric reconstruction for mechanical, architectural, modular, or repeated assets.
- Preserve stable component names and pivots after first integration.
- Use one UV set and one material slot per production mesh component.
- Keep each mesh below both its internal triangle budget and Roblox's current hard limit.
- Keep visual meshes non-collidable when wrapper Parts own gameplay collision.
- Reuse identical mesh/material combinations; do not export maps full of duplicate meshes.
- Encode gameplay states with redundant shape, value, color, motion, and audio cues where applicable.
- Treat the canonical visual definition as the production source of truth. Everything not explicitly variable is stable.
- Never run production generation without a preflight bound to the exact LOCKED canon hash.
- Never design states independently; derive them from one stable component structure and declared operations.
- Never store, print, transmit, or commit credentials.
- Never expose arbitrary Blender Python, a network listener, external asset
  download, canonical-source overwrite or Roblox publication through the
  normal Workbench MCP surface.
- Never invent Roblox identifiers, Package states, metrics, captures, reviewers, or approvals.

## Completion rule

Report PASS only when every applicable required proof passed. A valid simulator report, beautiful render, error-free console, local file, or complete textual CANDIDATE canon alone is insufficient for production approval.

Use the repository's final-report format and include:

- verdict;
- outcome;
- files changed;
- exact verification commands;
- Studio scenarios and observable evidence;
- risks and unknowns;
- highest-value next action only when one remains.
