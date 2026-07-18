# [Hypothèse] — Brief d'expérience

| Champ | Valeur |
| --- | --- |
| ID | `EXP-NNN` |
| Classe | `HYPOTHESIS` |
| Cycle de vie | `DRAFT` |
| Version | 0.1.0 |
| Propriétaire / approbateur | Rôles |
| Scope | Population, build et surface expérimentale |
| Source | Observation, contrat ou décision déclencheuse |
| Remplace | Brief ou `Aucun` |
| Dernière revue | YYYY-MM-DD |
| Revue suivante | Résultat, changement de variante ou de population |
| Population | Profil et critères |
| Décision attendue | Conserver, modifier ou arrêter |

## Hypothèse causale

Si nous changeons **X** pour **population Y**, alors **métrique primaire Z**
évoluera dans la direction attendue parce que **raison**.

## Méthode adaptée au trafic

Choisir le plus petit niveau suffisant : test déterministe, playtest qualitatif,
test comparatif contrôlé, puis A/B Roblox lorsque le MDE et le trafic rendent le
résultat interprétable.

## Variante, contrôle et exposition

Une différence majeure, assignation, exclusions, durée et contamination
possible.

## Mesures

- métrique primaire et formule ;
- guardrails ;
- segments prévus ;
- instrumentation et validation des événements ;
- taille minimale/MDE lorsque statistique ;
- données qualitatives complémentaires.

## Règle de décision

Seuils fixés avant observation, traitement des résultats non significatifs,
tradeoffs et condition d'arrêt sécurité/éthique.

## Résultat

Renseigné après le test : données, limites, décision, config retenue et lien vers
la preuve. Un résultat non significatif n'est pas un succès ni un échec produit.
