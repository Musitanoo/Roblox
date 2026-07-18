# Contrat technique Roblox — Salvaged Frontier

| Champ | Valeur |
| --- | --- |
| ID | `ART-ROBLOX-TECH-001` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 1.0.0 |
| Scope | Meshes, matériaux, collision, VFX, instancing, import et mobile |
| Dernière revue | 2026-07-16 |

## Principe

Les limites de plateforme sont des plafonds, pas des cibles. Les budgets
internes ci-dessous sont plus stricts afin de préserver la lecture mobile, la
répétition et la capacité serveur/client. Une dérogation exige une mesure
Studio et appareil physique, un owner et un rollback.

## Budgets par variante

| Objet | Triangles internes max | Texture class | Répétition critique |
| --- | ---: | --- | --- |
| `barricade` | 2 000 | `medium` | 30 / 100 |
| `objective_core` | 4 500 | `medium` | landmark unique + stress |
| `enemy_standard` | 5 000 | `medium` | horde 30 / 100 |
| `floor_module` | 800 | `small` | grille 30 / 100 |
| `damage_effect` | 300 équivalent géométrique | `small` | événements concurrents bornés |
| `turret_fast_v1` | 3 500 | `medium` | défenses 30 / 100 |

La limite Roblox de 20 000 triangles par mesh importé reste un plafond externe ;
elle ne remplace jamais ces budgets internes.

## Géométrie

- géométrie destinée à la production fermée, sans trou, face arrière exposée,
  volume nul ou intersection inexpliquée ;
- quads privilégiés au travail ; aucun n-gon dans la sortie ;
- transforms appliquées/frozen avant export ;
- dimensions et pivot vérifiés après construction et après import ;
- formes primaires et secondaires conservées avant tout détail tertiaire ;
- aucune géométrie invisible décorative sous les assets ;
- un élément mobile, cassable ou remplaçable possède un composant et un anchor
  nommés.

## UV, matériaux et PBR

- un material slot maximum par composant mesh de production ;
- un UV set maximum, contenu dans 0–1 ;
- normal map tangent-space OpenGL ;
- textures internes au plus à 1024 px pour ce corpus ;
- maps de production : albedo, roughness, metalness, normal ;
- emissive seulement si la capacité cible et le gate visuel l'autorisent ;
- aucune ombre, lumière de scène ou saleté globale baked dans l'albedo ;
- les matériaux restent lisibles dans quatre profils d'éclairage, pas seulement
  dans le hero light.

La palette commune de rôles et la palette de territoire sont deux couches :
la première définit la sémantique cross-territory ; la seconde donne les
valeurs Salvaged Frontier utilisées pour la reconstruction. Elles ne doivent
pas être fusionnées ou comparées comme deux versions concurrentes.

## Collision

- collision gameplay séparée de la géométrie visuelle complexe ;
- `Box` privilégié pour les volumes simples, puis primitive/hull minimale selon
  le besoin mesuré ;
- `PreciseConvexDecomposition` interdit par défaut sur les objets répétés ;
- la collision ne change pas avec un état visuel sans contrat gameplay ;
- floor et barricade doivent rester honnêtes : aucun relief ou fragment ne
  promet une collision inexistante ;
- les VFX et fragments décoratifs sont non collidables et non queryables.

## Répétition et instancing

- les répétitions utilisent le même `MeshContent` et la même combinaison de
  texture/matériau lorsque l'apparence est identique ;
- aucune duplication d'asset ID pour fabriquer artificiellement de la variété ;
- les variations autorisées utilisent transform, tint borné, phase ou
  accessoires explicitement contractuels ;
- les scènes 1/30/100 vérifient draw pressure, transparence, mémoire et
  lisibilité collective ;
- `RenderFidelity.Automatic` est la valeur par défaut des MeshParts staged,
  sauf mesure justifiant une exception.

## Transparence et VFX

- éviter les couches transparentes superposées et les particules plein écran ;
- le Damage Effect utilise quelques formes fortes et disparaît rapidement ;
- taux d'émission mobile contractuel inférieur ou égal au plafond Roblox de
  100 particules/s par émetteur, avec une cible interne normalement bien plus
  basse ;
- chaque effet possède un budget de durée, d'emitters, de fragments et de
  surface écran ;
- aucune gravité, affiliation ou interaction ne dépend exclusivement d'une
  couleur ;
- les modes reduced motion remplacent tremblement, flash et répétition rapide
  par des signaux plus stables.

## Import et staging

Chaque instance staged porte :

```text
ArtTerritory
ArtAssetId
ArtState
ArtSourceSha256
```

L'import refuse source hash absente, dimensions hors tolérance, pivot faux,
MeshId vide, classe non supportée ou état non applicable. La publication Cloud
reste staging-only, dry-run par défaut et séparée de l'intégration Studio.

## Mobile et accessibilité

- conception au viewport mobile, pas simple réduction desktop ;
- signal doublé par forme/valeur/mouvement/texte ou audio selon le cas ;
- aucune information indispensable par couleur seule ou son seul ;
- prise en compte de `PreferredTextSize` et reduced motion dans les surfaces UI
  associées ;
- les performances physiques exigent un appareil baseline nommé, une session
  soutenue et des mesures frame/mémoire/thermique.

Le Device Simulator prouve viewport et composition, jamais la thermique ni le
throttling d'un téléphone réel.

## Sources officielles

Consultées le 2026-07-16 :

- [General specifications](https://create.roblox.com/docs/art/modeling/specifications)
- [Texture specifications](https://create.roblox.com/docs/art/modeling/texture-specifications)
- [SurfaceAppearance / PBR](https://create.roblox.com/docs/art/modeling/surface-appearance)
- [Improve performance](https://create.roblox.com/docs/performance-optimization/improve)
- [Particle emitters](https://create.roblox.com/docs/effects/particle-emitters)
- [Test on hardware](https://create.roblox.com/docs/performance-optimization/test-on-hardware)
- [Accessibility](https://create.roblox.com/docs/production/publishing/accessibility)

Les sources officielles définissent la plateforme. Les budgets chiffrés par
objet restent des décisions internes issues des contrats machine du paquet.
