# Evidence and gates

## Contents

1. Status contract
2. Evidence hierarchy
3. Deterministic gates
4. Perceptual gates
5. Approval boundary

## Status contract

Use exactly:

- PASS: every applicable required proof exists and passes.
- FAIL: an executed mandatory behavior or gate failed.
- PARTIAL: useful result exists, but a secondary proof or approval is missing.
- BLOCKED: an external prerequisite prevented execution.
- UNKNOWN: the result was not measured or could not be observed.

Precedence is FAIL, BLOCKED, UNKNOWN, PARTIAL, PASS. A skipped check is never a pass.

## Evidence hierarchy

Prefer:

- schema-validated machine reports;
- immutable hashes;
- deterministic A/B manifests;
- sanitized cloud operation evidence;
- Studio hierarchy snapshots;
- before/after captures bound by hash;
- raw benchmark runs with hardware profile and order;
- a frozen Git commit.

Treat prose claims, prompts, one screenshot, one FPS values, and self-scores as weak evidence.

Classify each claim:

- deterministic: schema, dimensions, topology, UVs, transforms, names, hashes;
- external: auth, moderation, ownership, cloud operations, MCP availability;
- experimental: timing, FPS, memory, loading, network, thermals;
- perceptual: silhouette, style, finish, readability;
- human authority: accepted references and final art approval.

Precanonical Web evidence is perceptual exploration evidence. A prompt hash,
download hash and human selection prove provenance and a decision; they do not
prove hidden geometry, canon completeness, production implementation or
Roblox behavior.

## Deterministic gates

Applicable failures block promotion:

- precanonical request, selected constitution, prompt, views, states and budget
  are hash-bound before any Web submission;
- no automatic imagegen/API fallback, silent retry or duplicate successful
  prompt submission is enabled;
- schema and required files valid;
- stable unique component names;
- transforms applied;
- no loose, non-manifold, degenerate, zero-area, inverted, or unexpected geometry;
- exactly one UV set and one material slot per production component;
- UVs in 0–1 and declared textures present;
- triangles, dimensions, pivot, components, texture memory, and export bytes within budget;
- semantic determinism across repeated builds;
- source, recipe, tool, and evidence hashes current.
- exact visual canon ID, status, path and SHA-256 bound before generation;
- production generation uses a canon that is `LOCKED`, has a `COMPLETE`
  multimodal packet, and carries hash-bound human approval;
- every required state derives from the same stable components, anchors and
  declared component operations;
- no silent canon mutation or retroactive requirement change.

Warnings require a recorded disposition. They cannot erase a deterministic failure.

## Perceptual gates

Check:

- one-second function recognition;
- mobile near/mid/far silhouette;
- front/back and interaction-zone readability;
- state differences without color-only dependence;
- primary/secondary/tertiary shape hierarchy;
- accepted-reference coherence;
- no logos, accidental text, floating fragments, paper-thin accidents, generation artifacts, or uncontrolled noise;
- 1/30/100 repetition behavior under multiple lighting profiles.
- orthographic, perspective, component, proportion, material, semantic-zone,
  all-state, mobile, lighting, repetition, and required/forbidden boards bound
  to the current canon.

Perceptual review supports a decision; it does not mathematically prove beauty.

## Approval boundary

productionApproved may be true only when implementation is PASS, the art direction is locked, mandatory human review passed, source is frozen, publication/update identity is proven when applicable, Studio integration passed, and required real-device evidence exists.

For the sixth-asset transfer gate, distinguish:

- automated transfer PASS: three territory builds, A/B deterministic exports,
  grammar closure, visual metrics, mobile framing, and portable evidence pass;
- final transfer PASS: the selected territory matches a signed human review
  bound to the exact evidence package digest.

The first is necessary but cannot be relabelled as the second.
