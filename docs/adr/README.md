# Architecture Decision Records

| Champ | Valeur |
| --- | --- |
| ID | `ADR-INDEX` |
| Classe | `REFERENCE` |
| Cycle de vie | `ACTIVE` |
| Propriétaire | Équipe de développement |
| Dernière revue | 2026-07-18 |

Un ADR capture une décision matérielle, pas chaque choix de code. Il est requis
lorsqu'au moins deux options raisonnables affectent le canon, un contrat
partagé, les données, la sécurité, le workflow, une dépendance, la publication
ou la réversibilité.

## Convention

- Nom : `ADR-NNNN-slug.md`.
- Statuts : `PROPOSED`, `ACCEPTED`, `SUPERSEDED`, `REJECTED`.
- Un ADR accepté n'est pas réécrit pour faire disparaître une ancienne décision.
  Ajouter un addendum ou un nouvel ADR qui le remplace.
- Les conséquences et le déclencheur de réévaluation sont obligatoires.

## Registre

| ADR | Statut | Décision |
| --- | --- | --- |
| [ADR-0001](ADR-0001-documentation-system.md) | `ACCEPTED` | Taxonomie, autorité et création just-in-time du corpus documentaire. |
| [ADR-0002](ADR-0002-waive-g3-participant-gate.md) | `ACCEPTED` | Dérogation founder au gate participant G3 sans conversion de la preuve `UNKNOWN` en `PASS`. |

Utiliser [ADR_TEMPLATE.md](../templates/ADR_TEMPLATE.md) pour le prochain ADR.
