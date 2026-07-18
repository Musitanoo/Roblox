# Violet Frontier Rôdeur

| Champ | Valeur |
| --- | --- |
| ID canonique | `enemy_standard` |
| Rôle GDD | rôdeur — zombie marcheur standard de la horde |
| Fonction | pression de route de référence, lisible et honnête |
| Dimensions | 2.5 × 5.5 × 2.5 studs |
| Pivot | `feet_center` |
| Lecture cible | 60 studs |
| États | `INTACT`, `DAMAGED`, `CRITICAL` |
| Statut | `CANDIDATE` — nouvelle preuve visuelle requise |
| Source | [`../../art/canonical-visuals/salvaged-frontier/enemy_standard.json`](../../art/canonical-visuals/salvaged-frontier/enemy_standard.json) |

## Décision

L'ennemi standard est un **zombie violet stylisé**, jamais un robot, un golem
blindé ou une brute miniature.

Cette décision répond à quatre autorités :

1. le GDD nomme explicitement le rôle standard `rôdeur` et demande des zombies
   mémorables, commercialement distinctifs, expressifs, non gore et fortement
   lisibles ;
2. la doctrine de rétention exige une menace comprise avant de pouvoir produire
   une décision, une cause observable et un rematch volontaire ;
3. Salvaged Frontier impose une histoire matérielle et biologique du monde,
   sans transférer le cuivre d'auteur du joueur sur la horde ;
4. Industrial Toy Defense n'apporte que la discipline de masse, de contraste et
   de lecture mobile.

La couleur violette est une identité de faction constante, pas une promesse
mesurée de rétention et pas un remplacement de la silhouette.

## Promesse d'une seconde

Le joueur voit immédiatement :

- une tête zombie inclinée avec cavité faciale et mâchoire graphique ;
- un corps violet voûté en poire ;
- une main ouverte qui cherche la cible et un avant-bras plus bas ;
- deux jambes fléchies de rôdeur ;
- une excroissance violette oblique, de la couronne à l'épaule opposée.

Même en niveaux de gris et sans émission, l'objet doit se lire comme un zombie
standard orienté vers la forteresse.

## Hiérarchie canonique

### Formes primaires — 72 %

- `HunchedBody` : corps biologique voûté qui porte l'identité et la posture ;
- `ZombieHead` : tête inclinée visible, cavité faciale sombre et mâchoire large ;
- `ShamblingArms` : deux arcs de bras épais, inégaux, aux mains ouvertes ;
- `StaggerLegs` : deux jambes fléchies et séparées.

### Formes secondaires — 23 %

- `FrontierBloom` : une seule excroissance biologique durcie, oblique, intégrée
  entre couronne et épaule ;
- rythme épaule haute / épaule basse ;
- plans calmes des mains, du visage et des pieds.

### Détails tertiaires — 5 % maximum

- deux puits oculaires raspberry inégaux ;
- un à trois grands plans sur l'excroissance ;
- une à trois compressions ou marques non gore, larges et causales.

## Proportions qui séparent les rôles

- le torso voûté occupe environ 42 % de la hauteur ;
- la tête occupe 16 à 20 % de la hauteur et mène le profil ;
- les mains restent ouvertes, moyennes et plus petites que la tête ;
- les épaules restent plus étroites que celles d'une future brute ;
- les jambes occupent environ un tiers de la hauteur ;
- l'excroissance ne dépasse ni les bounds ni la lecture principale.

Ces règles empêchent le rôdeur de voler la promesse du GDD réservée à la brute,
qui attaque les murs.

## Palette hostile

| Rôle | Plage | Usage |
| --- | --- | --- |
| Biologie profonde | `#30283F` | ombres, masse dominante |
| Biologie violette | `#654A78` | peau et plans lisibles |
| Menace raspberry | `#A84876` | yeux et intérieur de mâchoire uniquement |
| Warning | `#F2C94C` | fracture `DAMAGED`, très locale |
| Critical | `#E64A4A` | fracture ou œil `CRITICAL`, très local |
| Fibre sèche | clair désaturé | intérieur non gore de la même fracture |

Le violet reste mat et désaturé. Il n'est ni néon, ni emissif sur toute la
surface, ni dépendant d'un éclairage favorable. Le cuivre, le mint, les panneaux
sable et le châssis slate des constructions alliées sont interdits.

## Traduction Salvaged Frontier

La horde partage le monde, pas l'acte de construction du joueur. Le rôdeur
exprime une mutation hostile violette, fixe et stable, jamais une adaptation
apprise, une réparation fière ou une armure de récupération.

Cette mutation ne constitue aucune preuve de horde adaptative. `H-HORDE-001`
reste différée et interdite comme promesse visuelle ou marketing.

L'excroissance est le repère commercial et la chaîne causale des dégâts :

```text
INTACT
excroissance continue
    ↓
DAMAGED
épaule abaissée + première fracture sèche + bras qui traîne
    ↓
CRITICAL
    même fracture élargie + même bras abaissé + même genou qui cède
```

Une nouvelle fracture arbitraire, une pièce détachée ou une anatomie différente
constitue un échec de continuité.

## États d'intégrité

### `INTACT`

- tête inclinée et visage zombie lisible ;
- hunch stable ;
- une main avance, l'autre reste plus basse ;
- deux jambes fléchies portent entièrement le corps ;
- excroissance violette intacte ;
- rasp régulier, pas mécanique.

### `DAMAGED`

- l'épaule du côté de l'excroissance descend ;
- le même bras reste attaché et commence à traîner ;
- le torso tourne de 8 à 12 degrés sans changer le footprint ;
- une seule fracture sèche ouvre l'excroissance ;
- un œil s'interrompt ;
- la couleur confirme, mais la posture suffit.

### `CRITICAL`

- le même genou cède et abaisse le corps ;
- le même bras traîne dans une posture affaiblie, sans déduire sa capacité
  d'attaque exacte ;
- la même fracture s'élargit ;
- la tête et l'autre main préservent encore le facing ;
- l'émission devient rare avec de longs intervalles sombres ;
- aucun membre ne se détache.

## Limite de vérité gameplay

Les trois références restent des candidats visuels liés à `PD-03`. Elles ne
définissent ni vitesse, ni dégâts, ni fréquence d'attaque, ni hitbox. L'état
`CRITICAL` reste hostile et n'est pas l'état terminal `DEFEATED`, lequel reste
runtime-only.

## Interdictions

- robot, mech, golem blindé, combinaison motorisée ou machine sans visage ;
- visor, sensor slit, chest core, service box ou articulation mécanique ;
- poings géants, épaules de brute ou pose héroïque ;
- avatar Roblox simplement recoloré ;
- cuivre, mint, panneaux sable, réparations alliées ou armure mécanique ;
- violet néon global ou état communiqué uniquement par couleur ;
- gore, sang, organes, dents réalistes ou membres détachés ;
- cornes, ailes, armes, cristaux aléatoires ou fumée permanente ;
- changement de corps entre vues ou entre états.

## Critères de verrouillage

La nouvelle planche précanonique ne peut être retenue que si :

- quatre vues montrent exactement la même anatomie ;
- le rôdeur est identifié comme zombie standard en une seconde ;
- aucun évaluateur ne le confond avec la brute, un robot ou un buildable ;
- la silhouette reste lisible à 60 studs et dans une horde de 30/100 ;
- le violet reste identifiable sous trois éclairages et en transformations CVD ;
- chaque état est reconnu par posture et silhouette avant la couleur ;
- la chaîne de fracture et les composants restent continus ;
- le fondateur accepte explicitement la planche avant tout verrouillage.
