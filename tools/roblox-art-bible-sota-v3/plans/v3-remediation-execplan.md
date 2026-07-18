# ExecPlan — Executable Art Direction System v3

## Objective

Transform the audited v2 assurance package into a Windows-first v3 whose local
static and Blender claims are proven by executable evidence. The v3 remains an
exploration and assurance layer for the existing `r3d` pipeline; it does not
publish assets or select an art direction without Studio, device, and human
evidence.

## Observable acceptance criteria

- The package is isolated under `tmp/roblox-art-bible-sota-v3` and does not
  mutate v2 or the repository's installed `art/` and `tools/` trees.
- `scripts/art-direction.ps1 doctor`, `validate`, and `test` work in Windows
  PowerShell 5.1 from a clean package-local Python environment.
- Every applicable asset/state pair for all three territories builds in Blender
  without exceeding its triangle budget.
- Non-applicable asset/state combinations are absent from build and render
  contracts and rejected when supplied.
- Every machine-readable recipe field is either consumed by the compiler or
  explicitly classified as a validation target rather than executable input.
- Build reports include canonical semantic hashes and a repeated build produces
  the same canonical report and exported GLB hashes.
- Static validation cannot report the Blender layer as PASS; only a successful
  integration run may do so.
- Studio, mobile, human-selection, sixth-asset transfer, and production-lock
  statuses remain `UNKNOWN` or `PENDING` until their evidence exists.
- A fresh package manifest matches every shipped file byte-for-byte.

## Milestones

### M1 — Preserve and baseline

- Copy v2 to a new v3 directory.
- Record the v2 audit findings and v3 acceptance criteria.
- Preserve all external user changes.

### M2 — Windows and dependency bootstrap

- Remove reliance on PowerShell 7-only automatic platform variables.
- Add package-local virtual-environment bootstrap and dependency verification.
- Pin exact Python dependency versions in the runtime lock contract.
- Make `doctor` distinguish missing Python dependencies from missing Blender.

### M3 — Contract correction

- Add per-asset state applicability to the calibration kit.
- Derive build and render expectations from that applicability matrix.
- Add semantic validation for recipe/compiler compatibility and state coverage.
- Require explicit human provenance approval before art lock.

### M4 — Executable recipes and geometry budgets

- Consume declared primitive, module-count, asymmetry, bevel, and state-strategy
  inputs in deterministic compiler decisions or reclassify them as validation
  targets.
- Replace generic state damage with territory/asset strategy dispatch.
- Preserve intact reference scale when constructing damaged states.
- Tune deterministic geometry to remain within each strict budget.

### M5 — Runtime integration and determinism

- Add a Blender preflight/integration command.
- Build all applicable variants for all territories.
- Run two isolated builds and compare canonical reports and GLB SHA-256 hashes.
- Fail on any missing output, budget violation, or nondeterministic artifact.

### M6 — Honest release metadata

- Update README, status model, changelog, assurance model, and remediation map.
- Regenerate Luau configuration and verify no drift.
- Regenerate and verify the deterministic package manifest.

### M7 — Verification and handoff

- Execute static syntax, JSON schema, semantic, adversarial, Windows runner,
  Blender build, and determinism checks.
- Inspect the final v3 diff relative to v2.
- Report Studio, device, perceptual, and human gates as unexecuted.

## Recovery strategy

The v2 directory remains immutable. Delete only the isolated v3 directory to
revert this work. Blender and Python diagnostics write to package-local ignored
build/evidence directories or explicitly named temporary directories.

## Decision log

- 2026-07-15: v2 is the baseline because its contracts and evidence model are
  stronger than a rewrite, but its static PASS does not prove runtime fitness.
- 2026-07-15: v3 will not install itself into the main repository or contact
  Roblox services.
- 2026-07-15: no final territory will be chosen by automation alone.

## Current status

- M1: complete; v2 preserved and v3 isolated.
- M2: complete; PowerShell 5.1 doctor and local dependency bootstrap pass.
- M3: complete; applicability, recipe classification and human provenance gate pass static validation.
- M4: complete; all 39 variants pass the original strict triangle budgets.
- M5: complete for build-only determinism; 39 GLB SHA-256 values match across A/B runs.
- M6: complete; v3 truth metadata and documentation are current.
- M7: complete for local static and Blender smoke scope. Studio, device,
  perceptual study and human decision remain external gates.
