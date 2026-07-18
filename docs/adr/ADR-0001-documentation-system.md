# ADR-0001 — Système documentaire hiérarchisé et just-in-time

| Champ | Valeur |
| --- | --- |
| ID | `ADR-0001` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 1.0.0 |
| Propriétaire / approbateur | Founder |
| Scope | Gouvernance documentaire du dépôt |
| Source | État du corpus avant migration documentaire 1.0 |
| Remplace | Aucun |
| Date de décision | 2026-07-15 |
| Dernière revue | 2026-07-17 |
| Revue suivante | Nouvelle classe, ambiguïté récurrente ou coût de maintenance excessif |

## Contexte

Le projet possède un GDD riche, une constitution d'exécution (`AGENTS.md`), des
contrats de slices, des ExecPlans et des rapports de preuve. Il ne possède pas de
porte d'entrée ou de registre. Une proposition de corpus global identifie de
nombreux domaines pertinents, mais créer immédiatement des dizaines de fichiers
dupliquerait les contrats et contredirait la stratégie validation-first.

## Décision

1. Séparer classe d'autorité, cycle de vie et verdict de preuve.
2. Utiliser les classes `CANON`, `CONTRACT`, `HYPOTHESIS`, `CONFIG`, `PLAN`,
   `EVIDENCE` et `REFERENCE`.
3. Conserver `AGENTS.md` comme constitution d'exécution et le GDD comme autorité
   de conception, sous l'autorité de la demande explicite du founder.
4. Extraire une constitution produit courte ; ne pas rendre immuable l'ensemble
   des hypothèses du GDD.
5. Indexer et préserver les contrats et preuves existants au lieu de les
   réécrire ou renommer.
6. Créer les documents spécialisés uniquement lorsqu'un gate, risque, contrat
   partagé ou choix matériel le déclenche.
7. Utiliser des modèles à noyau court avec sections conditionnelles.

## Alternatives

### Un GDD monolithique

Rejeté : mélange vision, comportement, tuning et preuve avec des rythmes de
changement incompatibles.

### Créer immédiatement le corpus complet

Rejeté : coût d'entretien élevé, faux sentiment de maturité et risque de sources
concurrentes avant que les systèmes soient applicables.

### Laisser chaque feature choisir librement son format

Rejeté : navigation, verdicts, décisions et preuves deviennent incohérents.

## Conséquences

- Le registre et le portail doivent être mis à jour dans le même changement
  qu'un nouveau document autoritaire.
- Les futurs domaines — persistance, économie, social, LiveOps, conformité — ont
  un déclencheur clair sans recevoir une spécification prématurée.
- Une petite discipline de métadonnées et de liens est ajoutée à chaque
  changement documentaire.
- Les anciens documents restent lisibles même s'ils ne possèdent pas encore le
  nouveau bandeau de métadonnées ; le registre fournit leur classification.

## Réversibilité et réévaluation

La taxonomie peut être étendue par un nouvel ADR. Réévaluer si deux classes sont
régulièrement confondues, si le registre devient coûteux à maintenir ou si
l'équipe grandit au point de nécessiter des propriétaires et workflows plus
granulaires.
