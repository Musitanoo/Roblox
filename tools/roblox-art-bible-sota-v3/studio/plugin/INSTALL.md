# Studio plugin installation

Create a local plugin model with this hierarchy:

```text
ArtDirectionGoldenScene (Script using ArtDirectionGoldenScene.plugin.luau)
├── Generated (Folder)
│   ├── ArtDirectionConfig (ModuleScript)
│   ├── LightingProfiles (ModuleScript)
│   └── TerritoryStyles (ModuleScript)
└── Src (Folder)
    ├── GoldenSceneBuilder (ModuleScript)
    ├── GoldenSceneValidator (ModuleScript)
    ├── LightingProfileService (ModuleScript)
    └── AssetKitStager (ModuleScript)
```

Copy the corresponding `.luau` sources. The plugin uses `ChangeHistoryService` recordings, so build/staging actions are undoable.

Before applying a profile, configure `LightingStyle` and `PrioritizeLightingQuality` manually in Studio according to the profile preconditions. The service verifies them and fails explicitly on mismatch.

For client captures, place generated modules and `LightingProfileService` under `ReplicatedStorage.ArtDirectionTools`, then place `CaptureController.client.luau` in `StarterPlayerScripts` and set its `ResolutionId` attribute.
