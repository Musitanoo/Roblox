# Compilateur Blender de direction artistique

Le script est exécuté exclusivement par Blender :

```bash
blender --background --factory-startup --python-exit-code 19 \
  --python tools/blender/build_art_direction.py -- \
  --root <repo> \
  --territory industrial-toy-defense \
  --render-mode smoke
```

Modes :

- `build-only` : 15 variantes et exports, sans matrice de rendus;
- `smoke` : 108 captures bornées par territoire;
- `full` : 421 captures de couverture contractuelle par territoire.

Le compilateur :

1. charge et hash les contrats canoniques;
2. sonde le moteur disponible;
3. construit les cinq assets et trois états;
4. normalise les bounds et pivots;
5. contrôle triangles, volume, non-manifold, matériaux, UV et FOV vertical;
6. exporte chaque variante séparément;
7. rend les jobs prescrits;
8. écrit `build-report.json` avec hashes.

Après le processus Blender :

```bash
python -m tools.art.validate_build_report build/<territory>/build-report.json --require-complete
```

Blender est une prévalidation. Roblox Studio demeure le renderer canonique.

## Compilateur de transfert indépendant

Ne pas ajouter `turret_fast_v1` au compilateur de calibration. Exécuter sa
preuve isolée avec :

```powershell
.\scripts\art-direction.ps1 transfer -Open
```

`tools/blender/build_transfer_asset.py` importe les primitives, matériaux,
caméras, validations, exports et la canonicalisation GLB éprouvés ci-dessus,
mais garde le sixième asset hors du set de calibration. Cette séparation est
une propriété obligatoire de la preuve de transfert.
