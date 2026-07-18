# Sources techniques primaires

| Champ | Valeur |
| --- | --- |
| ID | `ART-SOURCES-001` |
| Classe | `REFERENCE` |
| Cycle de vie | `ACTIVE` |
| Dernière vérification | 2026-07-16 |

Les sources externes définissent les capacités et limites de plateforme. Elles
ne prouvent jamais que ce projet respecte ses propres contrats : cette preuve
vient des rapports et artefacts courants.

## Roblox Creator Hub

| Sujet | Source primaire | Décision locale |
| --- | --- | --- |
| Géométrie | [General specifications](https://create.roblox.com/docs/art/modeling/specifications) | Watertight, volume non nul, pas de n-gons ; limite plateforme 20k triangles, budgets internes inférieurs |
| Blender | [Blender setup](https://create.roblox.com/docs/art/blender) | Repère Z-up Blender, preset export Roblox et validation de réimport |
| Export | [Export requirements](https://create.roblox.com/docs/art/modeling/export-requirements) | Transforms appliquées et contrôle axes/scale |
| Textures et UV | [Texture specifications](https://create.roblox.com/docs/art/modeling/texture-specifications) | Un material/UV set par composant, UV 0–1, normal OpenGL |
| PBR | [SurfaceAppearance](https://create.roblox.com/docs/art/modeling/surface-appearance) | Albedo, normal, roughness, metalness ; test sous plusieurs lumières |
| Camera | [Camera](https://create.roblox.com/docs/reference/engine/classes/Camera) | `FieldOfViewMode = Vertical`, FOV et viewport lus |
| Lighting | [Lighting](https://create.roblox.com/docs/reference/engine/classes/Lighting) | Préconditions protégées, propriétés mutables relues |
| Captures | [CaptureService](https://create.roblox.com/docs/reference/engine/classes/CaptureService) | Orchestration client et sauvegarde utilisateur explicite |
| Testing modes | [Studio testing modes](https://create.roblox.com/docs/studio/testing-modes) | Profil custom, résolution, DPI, orientation et input enregistrés |
| Hardware | [Test on hardware](https://create.roblox.com/docs/performance-optimization/test-on-hardware) | Simulateur distinct du téléphone physique ; session soutenue |
| Performance | [Improve performance](https://create.roblox.com/docs/performance-optimization/improve) | Instancing, collision simple, RenderFidelity, transparence bornée |
| MicroProfiler | [MicroProfiler](https://create.roblox.com/docs/performance-optimization/microprofiler) | Traces brutes conservées, pas seulement une moyenne FPS |
| Particules | [Particle emitters](https://create.roblox.com/docs/effects/particle-emitters) | Overdraw et plafond mobile considérés ; cible interne stricte |
| MeshPart | [MeshPart](https://create.roblox.com/docs/reference/engine/classes/MeshPart) | `RenderFidelity.Automatic` par défaut et readback Studio |
| Assets API | [Assets API](https://create.roblox.com/docs/cloud/guides/usage-assets) | Staging, formats et taille contrôlés ; mutation explicitement confirmée |
| Accessibilité | [Accessibility](https://create.roblox.com/docs/production/publishing/accessibility) | Pas de couleur/son seul, text scaling et reduced motion |

## Blender

| Sujet | Source primaire | Décision locale |
| --- | --- | --- |
| CLI et exit code | [Command line arguments](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html) | `--background --factory-startup --python-exit-code 19` |
| Rendu CLI | [Command line rendering](https://docs.blender.org/manual/en/latest/advanced/command_line/render.html) | Ordre d'arguments déterministe et testable |

Le moteur de rendu n'est pas supposé par numéro de version. Le compilateur
sonde l'enum disponible et enregistre celui utilisé.

## Schémas et accessibilité perceptuelle

| Sujet | Source primaire | Décision locale |
| --- | --- | --- |
| JSON Schema 2020-12 | [Release notes](https://json-schema.org/draft/2020-12/release-notes) | Schemas fermés, `$defs`, validation des schemas |
| Contraste non textuel | [WCAG 2.2 — Non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html) | 3:1 comme garde-fou, pas preuve suffisante en 3D |
| Couleur non unique | [WCAG 2.2 — Use of color](https://www.w3.org/WAI/WCAG22/Understanding/use-of-color.html) | État critique redondant par forme/mouvement/audio |
| Simulation CVD | [Machado et al. 2009](https://www.inf.ufrgs.br/~oliveira/pubs_files/CVD_Simulation/Machado_Oliveira_Fernandes_CVD_Vis2009_final.pdf) | Vues simulées et revue humaine |

## Mise à jour

Toute évolution externe qui affecte un contrat déclenche :

1. revalidation de la source et de la date ;
2. modification versionnée du contrat local ;
3. régénération des sorties dépendantes ;
4. validateurs et tests adversariaux ;
5. invalidation visible des preuves incompatibles.
