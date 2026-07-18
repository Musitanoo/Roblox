# Contrat du compilateur Blender déterministe

| Champ | Valeur |
| --- | --- |
| ID | `ART-BLENDER-001` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 2.1.0 |
| Dernière revue | 2026-07-17 |

## Autorité

Le compilateur consomme territoire, constitution, canon d'objet, kit de
calibration, caméra, render matrix, lighting et palettes. Il reconstruit un
objet déjà défini ; il ne choisit ni sa fonction, ni ses composants, ni ses
états.

`build-only`, `smoke` et `full` partagent la même géométrie. Le mode de rendu
change le volume de preuve, jamais l'asset.

## Préconditions

- Blender et version enregistrés dans le rapport ;
- factory startup pour éliminer l'état utilisateur ;
- seed déterministe ;
- hashes de toutes les entrées vérifiés ;
- canon `CANDIDATE` minimum pour exploration ;
- canon `LOCKED + COMPLETE + APPROVED` pour production ;
- dimensions, budgets, composants et états lus depuis les contrats, jamais
  recopiés dans le code.

## Géométrie obligatoire

- bounds exacts dans la tolérance ;
- pivot exact et grounding ;
- géométrie de production watertight, sans trou ni backface exposée ;
- volume non nul ;
- aucun n-gon dans la sortie ;
- normales cohérentes et tangentes valides ;
- transforms appliquées, scale positif, aucun shear ;
- composants sémantiques nommés et présents ;
- pas d'intersection ou de support flottant inexpliqué ;
- budgets triangles par variante respectés.

Une exception de surface ouverte exige un contrat d'objet explicite,
un test Roblox et une waiver. « Effet visuel » n'autorise pas silencieusement
une géométrie invalide.

## Matériaux et UV

- un material slot maximum par mesh component ;
- un UV layer maximum ;
- UV dans 0–1 ;
- normal map OpenGL tangent-space ;
- textures dans la classe déclarée ;
- rôles de matériaux canoniques, sans matériau ad hoc ;
- couleur sémantique bornée par les surfaces maximales de la constitution.

## États

Tous les états applicables dérivent de la même structure et des mêmes IDs de
composants. Seules les opérations autorisées sont utilisées :

```text
PRESERVE MOVE ROTATE EXPOSE OPEN BREAK REMOVE RECOLOR EMIT DEFORM
```

Un état absent de la matrice d'applicabilité est un échec d'entrée, pas une
variante à générer.

## Export

- un GLB canonique par asset/état ;
- exclusion des caméras, lumières, floors de calibration et helpers ;
- nommage stable `<assetId>__<state>.glb` ;
- axes/export conformes à [AXIS_AND_UNITS.md](AXIS_AND_UNITS.md) ;
- manifest SHA-256 ;
- SHA-256 du générateur exact dans la provenance ;
- ordre de sérialisation et canonicalisation déterministes ;
- rapport contenant Blender, moteur de rendu, seed, inputs, outputs, skipped
  checks et erreurs.

Le FBX est permis pour les probes explicitement contractuels. Il ne remplace
pas le GLB canonique sans décision versionnée.

Le chemin du `.blend` source embarqué par l'exporteur FBX est normalisé avant
hashing. Deux builds A/B doivent produire le même hash sémantique et les mêmes
octets GLB/FBX applicables ; une différence de dossier de sortie n'est pas un
champ volatil autorisé.

## Workbench visuel

L'inspection et les corrections interactives suivent
[BLENDER_MCP_WORKBENCH.md](BLENDER_MCP_WORKBENCH.md). `Reference` reste
immuable, `Candidate` reste réversible et aucun changement n'entre en
production avant reproduction depuis la source déterministe.

## Caméra et rendu

- `FieldOfViewMode = Vertical` côté Roblox ;
- FOV vertical réel lu et enregistré ;
- framing normalisé landscape/portrait ;
- vues orthographiques, perspective, silhouette, composants, états, mobile,
  quatre éclairages et répétition selon le paquet de 17 boards ;
- aucun crop ou post-traitement qui modifie la preuve ;
- toute capture lie viewport, canon, build, territoire, état et SHA-256.

## Post-build bloquant

Le run échoue si :

- un composant primaire/secondaire manque ;
- bounds, pivot, triangles, UV, matériaux, watertightness ou volume échouent ;
- un état requis manque ou un état non applicable existe ;
- deux builds déterministes divergent sans champ autorisé ;
- la preuve ne correspond pas au hash courant ;
- un check requis est sauté.

Un exit code zéro sans manifest et rapport cohérents ne vaut pas `PASS`.

## Limite de la preuve

Le `PASS` Blender prouve la reconstruction et les contrôles hors Studio. Il ne
prouve ni collision runtime, ni import réel, ni lisibilité physique mobile, ni
approbation artistique humaine.
