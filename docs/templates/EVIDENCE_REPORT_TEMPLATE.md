# [Système] — Rapport de validation [version]

| Champ | Valeur |
| --- | --- |
| ID | `DOMAIN-EVIDENCE-NNN` |
| Classe | `EVIDENCE` |
| Cycle de vie | `RECORDED` |
| Propriétaire | Rôle responsable de la preuve |
| Scope | Build, place, version et comportement couverts |
| Contrat testé | Lien + version/commit |
| Source | Exécution, logs et artefacts bruts |
| Date de preuve | YYYY-MM-DD |
| Dernière revue | YYYY-MM-DD |
| Revue suivante | Addendum après nouvelle exécution ou invalidation |
| Environnement | Studio/place/mode/appareil/clients/latence |
| Verdict global | `UNKNOWN` |

## Résultat livré

Comportement réellement présent, sans extrapoler au plaisir ou à la rétention.

## Matrice d'acceptation

| ID | Verdict | Observation | Artefact |
| --- | --- | --- | --- |
| T01 | `UNKNOWN` | Non exécuté | — |

Verdicts admis : `PASS`, `FAIL`, `PARTIAL`, `BLOCKED` ou `UNKNOWN`. Un prérequis
externe absent reçoit `BLOCKED`, jamais `PASS`.

## Commandes et scénarios exécutés

Commandes exactes, ordre pertinent et résultats. Séparer client et serveur.

## Preuves

Logs concis, attributs, états, captures et mesures avec provenance. Un lien vers
la donnée brute est préférable à une copie partielle.

## Écarts, risques et inconnues

Checks sautés, limites de l'environnement, erreurs observées et impact sur le
verdict.

## Nettoyage et état final

Hooks temporaires retirés, playtest arrêté, runtime nettoyé, fichiers modifiés,
diff contrôlé et récupération disponible.

## Addenda

Une correction future est ajoutée ici avec date et raison ; ne pas réécrire
silencieusement l'observation originale.
