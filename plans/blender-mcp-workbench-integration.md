# ExecPlan — Blender Visual Workbench MCP

## Status

```json
{
  "planVersion": "1.0.0",
  "specificationStatus": "PASS",
  "implementationStatus": "PASS_LOCAL_VERTICAL_SLICE",
  "verticalSliceStatus": "PASS",
  "studioStatus": "UNKNOWN",
  "productionApproved": false
}
```

## Observable outcome

Extend the existing `r3d` pipeline with a local MCP workbench that can inspect
an exact Blender build, create a reversible candidate, apply only declared
high-level operations, emit hash-bound evidence, prove rollback, and verify
that an accepted experiment was reproduced from deterministic source.

The workbench passes its local vertical slice when it proves all of the
following on `defense_barricade_small`:

1. the exact contract, canon, generator, Blender executable and reference
   `.blend` are hash-bound before inspection;
2. `OBSERVE` cannot create or mutate a candidate;
3. `EXPLORE` writes only below one ignored session directory and never saves
   over the reference build;
4. two declared feet can be changed through bounded operations without an
   arbitrary-Python tool;
5. before/after scene manifests, invariant reports and normalized captures are
   produced with the same cameras;
6. rollback restores the candidate semantic hash and leaves the reference
   binary hash unchanged;
7. a structured change set maps each operation to a deterministic source
   parameter;
8. two recompilations of a promoted sandbox source are semantically identical
   and reproduce the candidate within declared tolerance.

Studio and physical-device acceptance remain separate. Local MCP success must
not be relabelled as production approval.

## Authority and safety decisions

- The locked visual canon defines the object; the asset contract and generator
  remain production source.
- The workbench is diagnostic and experimental only.
- No third-party BlenderMCP package or add-on is installed in the normal path.
- The MCP transport is project-scoped STDIO, so it opens no TCP listener.
- Blender is spawned from one verified absolute path with a sanitized
  environment and one repository lock.
- The Blender bridge exposes an enum dispatcher only. It has no arbitrary code,
  add-on installation, download, publication, canon-edit or contract-edit tool.
- Reference builds are copied read-only and hash-checked before and after every
  operation.
- Production promotion is a verification action after a source edit; it is not
  a direct MCP mutation of authoritative source.

## Milestones

### M0 — Contract and governance

- Add the `IN_REVIEW` workbench contract, gate definitions and corpus routing.
- Add closed schemas for sessions, scenes, change sets, invariants and
  promotion reports.

### M1 — Bounded Blender bridge

- Inspect component hierarchy, transforms, bounds, pivots, mesh statistics,
  materials and modifiers.
- Render a repeatable review matrix from an immutable reference or candidate.
- Apply only allow-listed operations with declared before/after values.

### M2 — Transactional session manager

- Bind all inputs and create `Reference`, `Candidate`, `Review` and `Evidence`.
- Enforce path confinement, single-operation locking, reference immutability,
  rollback and append-only operation logs.
- Produce geometry, material and invariant diffs.

### M3 — MCP and CLI surfaces

- Add an MCP STDIO adapter with read-only annotations and write-tool approval
  routing.
- Extend `r3d.py` with doctor, inspect, workbench, preview, apply, revert,
  compare, reset and promotion-verification commands.
- Add the project-scoped Codex MCP configuration using an absolute local
  launcher and a strict tool allow-list.

### M4 — Adversarial verification

- Prove OBSERVE immutability, stale-hash rejection, undeclared-target rejection,
  out-of-root rejection, operation-bound rejection and forbidden-tool absence.
- Prove MCP initialize/list/call behavior over STDIO.

### M5 — Barricade vertical slice

- Compile the current barricade and capture the baseline.
- Explore a bounded two-foot width change without modifying authoritative
  source.
- Compare, rollback, reapply and export a change set.
- Apply the generated source patch only to a session-contained sandbox contract,
  compile twice and verify reproduction.
- Preserve `productionApproved=false`; Studio verification remains `UNKNOWN`
  until executed against the selected staging place.

## Exact files

- `docs/BLENDER_MCP_WORKBENCH.md`
- `docs/ROBLOX_3D_ASSET_WORKFLOW.md`
- `docs/TOOLING.md`
- `docs/README.md`
- `docs/00-governance/DOCUMENT_REGISTER.md`
- `docs/00-governance/ROADMAP_AND_STAGE_GATES.md`
- `plans/blender-mcp-workbench-integration.md`
- `.codex/config.toml`
- `.gitignore`
- `scripts/r3d-mcp.ps1`
- `tools/roblox-3d-asset/r3d.py`
- `tools/roblox-3d-asset/mcp/*.py`
- `tools/roblox-3d-asset/blender/workbench_bridge.py`
- `tools/roblox-3d-asset/schemas/blender-*.schema.json`
- `tools/roblox-3d-asset/tests/test_workbench_*.py`

The release-bundle mirror under
`tools/roblox-art-bible-sota-v3/tools/roblox-3d-asset/` is synchronized only
after the active in-place implementation passes targeted tests. No ZIP,
uninstall or staged reinstallation is part of this run.

## Verification commands

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 blender-mcp-doctor --repo .
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 test
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 blender-inspect .\assets-3d\defense-barricade-small\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 blender-workbench .\assets-3d\defense-barricade-small\asset.json --mode explore
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
```

## Recovery

- All sessions live under `assets-3d/<asset>/workbench/` and are ignored by
  Git by default.
- A failed operation restores its pre-operation candidate backup before
  returning `FAIL`.
- Reset copies the immutable reference back to Candidate and proves the
  semantic hash.
- The project MCP config can be disabled without deleting any evidence or
  changing the compiler.
- No Cloud, Roblox publication or Studio mutation is performed by workbench
  commands.

## Progress

- [x] Accept the bounded architecture and reject raw arbitrary Blender Python.
- [x] Inspect the active compiler, build evidence, governance and Codex MCP
  configuration surface.
- [x] Add contracts, schemas and governance routing.
- [x] Implement the bounded Blender bridge and session manager.
- [x] Implement MCP and `r3d` command surfaces.
- [x] Add adversarial and protocol tests.
- [x] Execute the barricade local vertical slice.
- [ ] Execute staging Studio and mobile gates when applicable.

## Results — 2026-07-17

- Blender 5.2.0 LTS, bridge, `stdio`, secret isolation and 12-tool allow-list:
  `PASS`.
- Per-asset Python suite: 30 tests `PASS`; package adversarial suite: 130 tests
  `PASS`.
- Draft 2020-12 validation of five schemas against the actual session:
  `PASS`.
- MCP `initialize` and `tools/list` through `scripts/r3d-mcp.ps1`: `PASS`.
- Candidate change: two declared feet, `designX 1.6 → 1.8`, two components
  changed, triangle delta 0, all requested invariants `PASS`.
- Rollback: candidate returned to semantic hash
  `91d6d8e6bde8162efb792dd6f56eeb6dae5eab5193f0fcaa21ba0f5fa9047633`;
  reference immutability `PASS`.
- Promotion sandbox: both reconstructed builds produced semantic hash
  `7a13df22ee1e9a8f8f1109fa22ee363a855ff3a5fd68c9fc4b810d900cb45acb`
  and reproduced both target values: `PASS`. Their GLB hashes are both
  `c7afad5222f3956d73611e45feb4a89e46712aea1c11c8a874f78ca533123055`
  and their normalized FBX hashes are both
  `2612c02821acd398d91f5143c856d782ac0f1cf1b023b70928c53af89851f21a`.
- The first strengthened A/B check exposed one path-dependent FBX byte. The
  compiler now normalizes only its embedded source path and records its own
  SHA-256 in provenance; the final rerun passed instead of suppressing the
  failed check.
- Authoritative `asset.json` was intentionally unchanged. Studio, mobile and
  human art approval remain `UNKNOWN`; `productionApproved=false`.
