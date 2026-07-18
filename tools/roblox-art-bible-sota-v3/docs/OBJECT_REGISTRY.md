# Registre canonique des objets Salvaged Frontier

| Champ | Valeur |
| --- | --- |
| ID | `ART-OBJECT-REG-001` |
| Classe | `REFERENCE` |
| Cycle de vie | `ACTIVE` |
| Source | `../art/canonical-visuals/salvaged-frontier/*.json` |
| Dernière revue | 2026-07-16 |

## Portée

Les six objets ferment les fonctions nécessaires à la calibration et au test
de transfert de la DA. Ils ne prétendent pas lister tous les futurs objets du
jeu. Chaque JSON canonique reste l'autorité complète ; les fiches humaines
ci-dessous en sont une projection lisible.

## Matrice exacte

| ID | Nom | Fonction | Dimensions W×H×D | Pivot | Lecture | États | Variantes |
| --- | --- | --- | --- | --- | ---: | --- | ---: |
| `barricade` | Defense Barricade Small | Bloquer temporairement un chemin | 8×4×2 | `bottom_center` | 60 studs | I/D/C | 3 |
| `objective_core` | Objective Core | Objectif principal et ancre visuelle | 6×7×6 | `bottom_center` | 60 studs | I/D/C | 3 |
| `enemy_standard` | Violet Frontier Rôdeur | Zombie marcheur standard | 2.5×5.5×2.5 | `feet_center` | 60 studs | I/D/C | 3 |
| `floor_module` | Fortress Floor Module | Cellule répétable de sol | 4×0.5×4 | `bottom_center` | 30 studs | I/D | 2 |
| `damage_effect` | Directional Damage Effect | Expliquer direction, cause et gravité | 4×4×4 | `impact_center` | 30 studs | D/C | 2 |
| `turret_fast_v1` | Fast Defense Turret | Défense rapide orientée | 4.8×5.4×5.2 | `bottom_center` | 60 studs | I/D/C | 3 |

`I/D/C` signifie `INTACT`, `DAMAGED`, `CRITICAL`. Total : 16 variantes.

## Lecture fonctionnelle commune

Chaque objet doit répondre en une seconde :

1. Qu'est-ce que c'est ?
2. Où est son avant ou son vecteur causal ?
3. Est-il allié, hostile ou neutre ?
4. Peut-on interagir avec lui, et depuis quel côté ?
5. Quel est son niveau d'intégrité ?
6. Que va-t-il probablement faire ensuite ?

La lecture ne dépend jamais uniquement d'un hue, d'un texte, d'un son ou d'un
micro-détail.

## Fiches

- [Defense Barricade Small](objects/BARRICADE.md)
- [Objective Core](objects/OBJECTIVE_CORE.md)
- [Violet Frontier Rôdeur](objects/ENEMY_STANDARD.md)
- [Fortress Floor Module](objects/FLOOR_MODULE.md)
- [Directional Damage Effect](objects/DAMAGE_EFFECT.md)
- [Fast Defense Turret](objects/TURRET_FAST_V1.md)

## Statut de verrouillage

Les six définitions sont `CANDIDATE`, leurs paquets visuels sont `SPECIFIED` et
leurs approbations humaines sont `PENDING`. La complétude descriptive ne doit
pas être confondue avec un verrou multimodal ou une approbation de production.
