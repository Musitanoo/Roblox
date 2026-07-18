# Art locks

## Creative-direction lock

The founder creative decision is already recorded:

- `art/decision/founder-direction-decision.json`;
- `art/selected/salvaged-frontier-constitution.json`;
- `art/art-direction.json` status `CANDIDATE_SELECTED`;
- `productionApproved=false`.

This lock freezes what the selected direction means and how Industrial Toy
Defense may constrain it. It does not authorize production assets.

## Production art lock v1.0

`tools/art/lock_direction.py` is the only supported way to produce `art/art-lock.json`.

Required inputs:

- either the founder strategic decision
  `art/decision/founder-direction-decision.json`, or a sealed blind-study
  `selection-decision.json`;
- scoring report and private blind map only when the blind-study decision route
  is used;
- complete evidence index with every required hard gate PASS;
- Blender build report for all five assets/states;
- Studio Golden Scene report;
- physical mobile performance report;
- six visual canons for the selected territory, each `LOCKED`, each carrying
  all seventeen required board families with verified file hashes and an
  explicit human approval bound to the candidate hash;
- sixth-asset transfer report with `automatedStatus=PASS`;
- `art/transfer/turret-fast-v1-review.json` signed `APPROVED`, bound to the
  report's exact `evidencePackageSha256`, and naming the selected territory.

The lock stores hashes for the selected constitution, all canonical JSON files,
the six selected visual canons and their approval overlays. `art/art-lock.json`
is the production authority; the creative selection document remains immutable
and is not rewritten during lock creation. Any later change invalidates the
lock until deliberately versioned and re-signed. A generated model cannot be
used to silently rewrite its canon; a changed decision creates a reviewed canon
revision first.
