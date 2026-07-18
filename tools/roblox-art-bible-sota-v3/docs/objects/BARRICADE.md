# Defense Barricade Small

| Champ | Valeur |
| --- | --- |
| ID canonique | `barricade` |
| Fonction | Structure défensive temporaire de blocage de chemin |
| Dimensions | 8 × 4 × 2 studs |
| Pivot | `bottom_center` |
| Lecture cible | 60 studs |
| États | `INTACT`, `DAMAGED`, `CRITICAL` |
| Statut | `CANDIDATE` — approbation `PENDING` |
| Source | [`../../art/canonical-visuals/salvaged-frontier/barricade.json`](../../art/canonical-visuals/salvaged-frontier/barricade.json) |

## Promesse d'une seconde

Une masse large, basse et ancrée promet visuellement le blocage de la lane. Le
joueur comprend le côté menace, la faiblesse structurelle et le côté sûr sans
que l'image prétende prouver la collision ou la mécanique de réparation.

## Limite de vérité gameplay

Les trois références restent des candidats visuels liés à `PD-07`. La collision
simple autoritaire conserve le même footprint dans `INTACT`, `DAMAGED` et
`CRITICAL`. Aucun état primaire n'autorise un passage joueur, une pénalité de
statistique ou une réparation implémentée. Un éventuel état `DESTROYED` est
runtime-only tant qu'un contrat accepté ne le définit pas.

## Construction obligatoire

- `FoundationFeet` : deux appuis lisibles, stables et compatibles avec le sol.
- `StructuralFrame` : cadre principal et chemin de charge persistant.
- `BlockingPanels` : trois baies de blocage ; jamais deux ou quatre.
- `ServiceModule` : affordance visuelle de service/statut protégée dans le
  quadrant supérieur droit de l'arrière sûr.

L'avant est le côté menace. L'arrière porte le service joueur. Une seule
adaptation causale domine : panneau remplacé, renfort diagonal ou raccord
réparé. Le châssis standard reste 75–85 % de la lecture.

## Matériaux et sémantique

- cadre : métal peint slate profond ;
- panneaux : composite récupéré bone-sand ;
- usure structurelle : métal nu limité aux arêtes réellement sollicitées ;
- adaptation/repair : cuivre brûlé borné ;
- interaction alliée : mint, uniquement au module de service ;
- danger : warning/critical, localisé sur la chaîne de défaillance.

Trois familles de matériaux visibles maximum. Ni rouille uniforme, ni bois
universel, ni décoration sans cause.

## États d'intégrité

### `INTACT`

- cadre, pieds et trois baies complets ;
- panneaux alignés et rythme stable ;
- module arrière visuellement prêt et signal allié borné ;
- silhouette frontale pleine, arrière techniquement lisible ;
- transition vers `DAMAGED` : 0,35 s.

### `DAMAGED`

- un panneau pivote ou se déforme autour de son ancrage réel ;
- le cadre expose une contrainte locale sans déplacer le footprint ;
- le module de service change de signal sans devenir une alarme color-only ;
- la faiblesse se lit par ouverture structurelle, angle, valeur et posture sans
  devenir un passage ;
- retour `INTACT` : 1,2 s ; aggravation `CRITICAL` : 0,45 s.

### `CRITICAL`

- une baie s'ouvre sévèrement selon le chemin de charge déclaré, sans ouverture
  de taille joueur ;
- un élément du cadre révèle la rupture, sans fragments bloquants libres ;
- le module arrière s'ouvre pour rendre la réparation urgente ;
- le wrapper de blocage reste inchangé et aucun vide ne promet la traversée ;
- retour réparé `INTACT` : 1,8 s.

## Invariants

- dimensions, pivot, footprint et orientation restent fixes ;
- rythme à trois baies et deux appuis toujours reconnaissable ;
- interaction toujours à l'arrière sûr ;
- anchors, IDs de composants et points d'effet stables ;
- aucun état ne déplace silencieusement la collision.

## Interdictions

Quatrième baie, point d'interaction côté ennemi, pics ou fils fins, armure
flottante, fissures aléatoires, damage color-only, microtexte, logos, fragments
persistants, silhouette de tas de ferraille.

## Critères de verrouillage

Les 17 planches doivent prouver vues, composants, proportions, matériaux,
zones, trois états, comparaison, mobile near/mid/far, quatre éclairages,
répétition 1/30/100 et annotations requises/interdites. Le rapport doit être lié
au hash du canon et signé humainement avant `LOCKED`.
