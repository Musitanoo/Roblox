# Roblox Studio Golden Scene

| Champ | Valeur |
| --- | --- |
| ID | `ART-STUDIO-GOLDEN-001` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 2.0.0 |
| Statut sélectionné courant | `UNKNOWN` |
| Dernière revue | 2026-07-16 |

## Frontière de preuve

Les Golden Scenes v3.7 ont prouvé le pipeline pré-sélection. Elles sont
historiques. Aucun `PASS` Studio n'est revendiqué pour la constitution
Salvaged Frontier optimisée tant qu'un staging frais n'est pas exécuté et lié
aux hashes courants.

## Arborescence de staging

```text
ServerStorage/
└── ArtDirectionAssetKit/
    └── salvaged-frontier/
        └── <assetId>/
            └── <state applicable>
```

Chaque état est un `Model` ou `MeshPart` avec :

```text
ArtTerritory
ArtAssetId
ArtState
ArtSourceSha256
```

## Matrice exacte sélectionnée

| Asset | États attendus |
| --- | --- |
| `barricade` | `intact`, `damaged`, `critical` |
| `objective_core` | `intact`, `damaged`, `critical` |
| `enemy_standard` | `intact`, `damaged`, `critical` |
| `floor_module` | `intact`, `damaged` |
| `damage_effect` | `damaged`, `critical` |
| `turret_fast_v1` | `intact`, `damaged`, `critical` |

Le builder refuse `floor_module/critical` et `damage_effect/intact`. Les cinq
assets de calibration représentent 13 variantes. La tourelle de transfert en
ajoute 3, pour 16 variantes Salvaged Frontier.

## Builder

`GoldenSceneBuilder.luau` crée :

- vues isolées par état ;
- fonds clair et sombre ;
- grille métrique et avatar R15 ;
- groupes de répétition 1/30/100 selon applicabilité ;
- cluster gameplay ;
- caméras à FOV vertical ;
- quatre profils Lighting ;
- proxies de collision visuellement distincts lors des diagnostics.

Les placeholders sont autorisés seulement en exploration et invalident la
preuve.

## Validator

`GoldenSceneValidator.luau` vérifie :

- territoire, asset et état dans la matrice ;
- bounds, pivot et orientation ;
- `ArtSourceSha256` présent et cohérent ;
- absence de placeholders et source manquante ;
- MeshId/TextureID/SurfaceAppearance non vides lorsque requis ;
- collision séparée et propriétés gameplay conservées ;
- profil Lighting appliqué puis relu ;
- caméra, viewport et FOV ;
- exactement 30 ou 100 clones dans le groupe déclaré ;
- même signature mesh/material pour les répétitions identiques ;
- aucune nouvelle erreur pertinente Client ou Server.

Le rapport est validé indépendamment :

```powershell
.\scripts\art-direction.ps1 validate-studio `
  -Report evidence/studio/salvaged-frontier/studio-report.json `
  -RequirePass
```

## Captures

Chaque capture lie :

- version de constitution ;
- asset, état et vue ;
- profil Lighting ;
- viewport, orientation et FOV ;
- hash source et hash image ;
- Studio instance et scénario, sans exposer d'identifiant sensible portable.

`CaptureService` respecte le flux utilisateur Roblox. Le système ne prétend pas
écrire arbitrairement un fichier local.

## Scénario d'acceptation

1. confirmer l'unique instance staging active ;
2. importer les 16 variantes courantes ;
3. construire et valider la Golden Scene ;
4. lancer Play Client/Server ;
5. exercer lecture, collision, states, interactions et répétition ;
6. inspecter consoles client/serveur ;
7. capturer les quatre éclairages et viewports mobile ;
8. revenir en Edit ;
9. lier rapport et captures aux hashes courants.

Une capture seule ou une console propre seule ne prouve pas le scénario.
