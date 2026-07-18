# [Système] — Spécification [version]

| Champ | Valeur |
| --- | --- |
| ID | `DOMAIN-CONTRACT-NNN` |
| Classe | `CONTRACT` ou `HYPOTHESIS` |
| Cycle de vie | `DRAFT` |
| Version | 0.1.0 |
| Propriétaire / approbateur | Rôles |
| Scope | Slice, place et version |
| Source | GDD, ADR, preuve ou demande explicite |
| Remplace | Document ou `Aucun` |
| Dernière revue | YYYY-MM-DD |
| Revue suivante | Déclencheur, pas une date arbitraire |

## Objectif joueur

Résultat observable pour le joueur. Éviter les descriptions d'implémentation.

## Hypothèse et décision possible

Parce que **cause**, nous attendons **comportement**, mesuré par **preuve**. Si
elle échoue, indiquer ce qui est supprimé, modifié ou retesté.

## Scope / hors scope

Définir explicitement le plus petit incrément et les systèmes non autorisés.

## Invariants

Règles qui doivent rester vraies, notamment autorité, bornes, idempotence,
équité, récupération et éthique.

## Flux, états et règles

Entrées, sorties, transitions, interruptions, résultats et responsabilité de
chaque côté de la frontière.

## Critères d'acceptation

Table numérotée : observation requise, niveau de test, environnement et preuve.
Chaque ligne reçoit `PASS`, `FAIL`, `PARTIAL`, `BLOCKED` ou `UNKNOWN`.

## Plan de vérification

Commandes exactes, scénario Studio, clients, appareils, logs et artefacts. Dire
ce qui est non applicable.

## Erreurs, récupération et inconnues

Échecs attendus, fallback, nettoyage, stop conditions et questions ouvertes.

## Sections conditionnelles

Supprimer uniquement celles qui sont véritablement non applicables et noter la
raison dans le plan de vérification.

### Réseau, sécurité et abus

Schémas, validation cheap-to-expensive, permissions, spatialité, rate limit,
replay, duplication, NaN/infini, tables énormes et fail closed.

### Données, persistance et migration

Schéma/version, taille, concurrence, retry, idempotence, rollback, corruption,
environnement isolé et droit à l'effacement.

### Performance

Appareil/charge cible, CPU, mémoire, réseau, instances, pathfinding, physique,
fréquence et méthode de mesure.

### Analytics et expérimentation

Événements serveur/client, population, métrique primaire, guardrails, qualité
des données, MDE et règle de décision.

### UI, input et accessibilité

Touch, clavier/souris, manette, safe areas, contraste, texte, mouvement, audio,
feedback et récupération d'erreur.

### Rollout, rollback et compatibilité

Feature flag, serveurs déjà lancés, pourcentage, métriques bloquantes, kill
switch et données déjà migrées.

### Conformité, localisation et assets

Maturité, politiques, clés de traduction, provenance, licence et modération.

## Décisions et preuves liées

ADR, ExecPlan, rapport de test, incidents et versions applicables.
