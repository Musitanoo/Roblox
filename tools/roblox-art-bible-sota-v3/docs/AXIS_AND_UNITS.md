# Contrat d'axes, unités et transformations

| Champ | Valeur |
| --- | --- |
| ID | `ART-AXIS-001` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 2.0.0 |
| Dernière revue | 2026-07-16 |

## Repères sémantiques

| Espace | X | Y | Z | Up |
| --- | --- | --- | --- | --- |
| Design / Roblox | largeur | hauteur | profondeur | +Y |
| Blender | largeur | profondeur | hauteur | +Z |

Une unité Blender vaut un stud dans les scènes de calibration. Les dimensions
sont toujours nommées :

```json
{"width": 8.0, "height": 4.0, "depth": 2.0}
```

Les tableaux anonymes de dimensions sont interdits.

## Conversion sémantique

Pour un point ou une direction, du repère design/Roblox vers Blender :

```text
[xB]   [1 0 0] [xR]
[yB] = [0 0 1] [yR]
[zB]   [0 1 0] [zR]
```

Soit `vB = M vR`, avec :

```text
M = [[1,0,0],[0,0,1],[0,1,0]]
M^-1 = M^T = M
det(M) = -1
```

Pour une orientation :

```text
RB = M RR M^-1
```

Pour une transformée homogène :

```text
TB = H TR H^-1
```

où `H` étend `M` en matrice 4×4.

Pour une normale :

```text
nB = normalize((M^-1)^T nR)
```

Comme `M` est orthogonale, cela revient ici à `normalize(M nR)`. Un tangent
xyz suit la même conversion ; sa composante de handedness doit être inversée
si la réflexion est appliquée manuellement, car `det(M) = -1`.

## Exporteur et double conversion

Les formules ci-dessus définissent le sens du contrat et les validateurs. Elles
ne doivent pas être appliquées une deuxième fois si l'exporteur FBX/GLB effectue
déjà la conversion d'axes.

Pour le FBX Blender vers Roblox, le preset de référence suit la documentation
Roblox :

```text
Forward = Z Forward
Up = Y Up
Apply Scalings = FBX Unit Scale
```

Après export/import, vérifier systématiquement :

- dimensions W/H/D ;
- pivot et grounding ;
- facing avant/arrière ;
- winding et absence de faces inversées ;
- normales et tangentes ;
- orientation des composants mobiles ;
- correspondance des anchors et sockets.

Le « front » est le frame sémantique déclaré par le canon de l'objet. Aucun
signe global +Z/-Z n'est inventé dans cette page : son maintien est prouvé par
les vues front/back et le readback Studio.

## Pivots

- `bottom_center` : `minZ = 0` en Blender et centre XY à l'origine.
- `feet_center` : même règle, appliquée au plan des pieds.
- `impact_center` : centre des bounds à l'origine.

Tolérance : celle déclarée par le canon, actuellement 0,005 stud pour les six
objets sélectionnés.

Les transforms sont appliquées avant export. Aucun scale négatif, shear caché,
rotation non appliquée ou parent transform non documenté.

## Validation minimale

1. mesure après construction Blender ;
2. mesure dans l'export canonique ;
3. mesure après import Roblox ;
4. comparaison par dimension nommée ;
5. capture front/back et test d'un composant orienté ;
6. échec fermé en cas d'inversion, double conversion ou tolérance dépassée.

Sources officielles, consultées le 2026-07-16 :

- [Blender setup](https://create.roblox.com/docs/art/blender)
- [Export requirements](https://create.roblox.com/docs/art/modeling/export-requirements)
