# Studio, mobile, and human gates

## Contents

1. Studio authority
2. Golden scene
3. A/B benchmark
4. Simulator boundary
5. Physical device
6. Human art gate

## Studio authority

Before mutation:

1. List connected Studio instances.
2. Confirm the active staging instance.
3. Confirm Edit, Client, or Server DataModel availability.
4. Determine whether Script Sync owns the target.
5. Change synchronized code on disk, not through MCP.
6. Use MCP for inspection, execution, staging, playtest, console, and captures.

Never expose creator, place, Package, or credential values in logs or reports unless the report contract explicitly permits a sanitized form.

## Golden scene

Test the accepted asset under standardized cameras, scale references, semantic backgrounds, and every required lighting profile. Bind captures to the current source and report hashes. A screenshot proves appearance only; pair it with hierarchy and validator evidence.

When the task concerns a visual canon, classify each capture into the required
board family and bind its exact path and SHA-256. A canon cannot be `LOCKED`
until every required board is present and the human decision references the
complete evidence-package digest.

Use simple invisible hitboxes for gameplay collision by default. Keep the visual root replaceable without changing wrapper scripts, attributes, tags, attachments, or collision.

## A/B benchmark

Use equal layouts and camera paths for:

- graybox 30 versus candidate 30;
- graybox 100 versus candidate 100.

Record asset instances, BaseParts, MeshParts, unique mesh/material combinations, singleton combinations, transparency, decals, and shadows. Alternate runtime A/B order when measuring timing. Separate warm-up from samples and spikes from steady state.

## Simulator boundary

Studio Device Simulator can prove:

- exact requested resolution/orientation readback;
- safe-area and layout behavior;
- structural scene setup;
- visual readability in the simulated frame.

It cannot prove physical-device thermals, memory pressure, sustained FPS, load time, or input latency. Store simulator evidence in a distinct schema and reset simulation to default after testing.

LibMP or SceneAnalysis failures remain BLOCKED or UNKNOWN; never replace missing frames with invented statistics.

## Physical device

For release-relevant performance, require the checked-in protocol:

- target low-end hardware profile;
- cold launch and declared cache state;
- warm-up duration;
- balanced randomized or alternating A/B passes;
- same graphics, camera, server state, and duration;
- raw samples plus median, p95/p99 where applicable, dispersion, crashes, and thermal state;
- sustained session duration required by the schema.

Physical-device absence blocks only that gate, not deterministic local compilation.

## Human art gate

Keep candidate labels blinded and randomize order. Use separate reviewers for function/silhouette and art-direction coherence when practical. Preserve raw submissions.

For the installed art-direction study, use the generated P01-P12 participant
slots and R01-R04 expert slots. Share only the participant or expert ZIP.
Require the five-second exposure flow, one assigned ID per person, one device
class per participant and no backtracking. Store returned JSON files unchanged,
then seal them through the checked-in command before unblinding.

Require human authority for the selected direction, P0/P1 assets, hero characters, anatomy, expressive faces, complex rigging, and material disagreements. Do not average reviewer disagreement into a fictitious objective perfection score.
