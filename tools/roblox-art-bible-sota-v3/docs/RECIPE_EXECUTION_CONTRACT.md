# Recipe execution contract

Every field in an asset recipe belongs to exactly one closed category.

## Executable inputs

- `assetId`: selects the calibrated asset function.
- `bevelRatioTarget`: controls deterministic bevel width.
- `stateBreakStrategy`: selects a closed territory/asset strategy profile and
  named geometry targets.

An unknown strategy fails static validation. A strategy that matches no built
geometry raises a Blender runtime error.

## Validation and perceptual targets

- `primaryPrimitives` and `secondaryPrimitives` describe required semantic
  masses for visual review.
- `asymmetryTarget` is measured during territory review, not used as an opaque
  mesh deformation coefficient.
- `moduleCountTarget` constrains the semantic module count.
- `detailBandTargets` define projected-area review targets and must sum to one.

These fields are intentionally not described as procedural geometry commands.
They are closed, schema-validated targets consumed by visual and human review.
No field may exist outside these two categories.

## State bounds

The first applicable state is the reference state. It is normalized exactly to
the calibration dimensions. Later states reuse its per-axis scale and may only
receive a uniform fit to remain inside the reference envelope. This prevents a
broken state from being independently stretched back into the intact shape.
