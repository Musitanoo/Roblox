# Integration with the existing r3d pipeline

This package owns **art-direction contracts and evidence**, not final asset publishing.

After selection:

```text
art/art-lock.json
      ↓
production asset brief references selected territory + lock hash
      ↓
existing asset.json contract
      ↓
scripts/r3d.ps1 validate / compile / report / publish
      ↓
Golden Scene revalidation
```

The wrapper detects `scripts/r3d.ps1` at the repository root and can call its doctor. Do not copy publishing credentials or Open Cloud logic into this package.
