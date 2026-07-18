# Roadmap et stage gates

| Champ | Valeur |
| --- | --- |
| ID | `GOV-CONTRACT-002` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 1.1.0 |
| Propriétaire / approbateur | Founder |
| Scope | Ordre d'autorisation des slices, gates produit et dérogations bornées |
| Source | `AGENTS.md`, GDD v1.0.4, ADR-0002, contrats de slices et preuves enregistrées |
| Dernière revue | 2026-07-18 |
| Revue suivante | Nouveau résultat produit, changement de scope ou demande d'entrer dans un risque fermé |

La roadmap est ordonnée par réduction d'incertitude, pas par dates. Passer un
gate autorise le travail suivant ; cela ne garantit ni succès commercial ni
passage irréversible.

Le
[registre global de définition](PRODUCT_DEFINITION_REGISTER.md)
inventorie les décisions encore ouvertes. Son rôle est de prévenir les oublis,
pas de contourner cet ordre : `DEFERRED_BY_GATE` signifie explicitement
« enregistré mais non autorisé ».

## Journal de révision

- `1.1.0` — ADR-0002 enregistre la dérogation founder au gate participant G3 :
  la preuve reste `UNKNOWN`, mais G3 ne bloque plus la décision Action 0.4.1.
- `1.0.3` — liaison du registre global de définition aux gates ; les sujets
  différés restent inventoriés sans devenir du scope actif.
- `1.0.2` — intégration conditionnelle du runbook Persistence 0.6.1, des budgets
  de performance 1.0.1 et du catalogue Analytics 0.9.1 sans ouverture de gate.
- `1.0.1` — chaîne Build 0.3 → Action 0.4.1 → Progression 0.5.1 → Persistence
  0.6.1 et règle du founder seul testeur explicitées.
- `1.0.0` — roadmap et gates G0–G9 initiaux.

## État présent

| Étape | Statut | Preuve | Limite |
| --- | --- | --- | --- |
| Toolchain et Script Sync | `PASS` documenté | Scripts, checks et workflow dans `TOOLING.md` | Aucun déploiement prouvé |
| Defense Loop 0.1 | `SUPERSEDED` | Première boucle technique historique | Contrat remplacé par 0.2 |
| Defense Loop 0.2 | `PASS TECHNIQUE`, `GO CONDITIONNEL` | Boucle faiblesse → autopsie → modification → rematch | Gate humain `UNKNOWN` |
| Build Loop 0.3 | `PASS TECHNIQUE`, `GO CONDITIONNEL` | Grille autoritaire et T01–T32 `PASS` | Gate humain `UNKNOWN` |
| Gate humain G3 | Preuve `UNKNOWN`, séquencement `WAIVED_BY_FOUNDER` | [ADR-0002](../adr/ADR-0002-waive-g3-participant-gate.md) | Aucun panel non briefé ; aucune revendication de `PASS PRODUIT` |
| Contrats 0.4.1–0.6.1 | `IN_REVIEW` | Spécifications durcies et intégrées dans `docs/` | Action 0.4.1 est la prochaine décision admissible ; les autres gates restent fermés |
| Performance 1.0.1 | `IN_REVIEW`, mesures `UNKNOWN` | Protocole et cibles provisoires intégrés | Aucun appareil mobile baseline réel sélectionné |
| Analytics 0.9.1 | `DRAFT` | Taxonomie candidate intégrée | G6 fermé, aucun événement officiel actif |

## Ordre de dépendance des prochaines slices

| Ordre | Slice | Dépendance minimale | Autorisation actuelle |
| --- | --- | --- | --- |
| 1 | [Action 0.4.1](../ACTION_LOOP_0_4.md) | Build 0.3 techniquement stable | Décision d'acceptation admissible sous ADR-0002 ; contrat encore `IN_REVIEW` |
| 2 | [Progression 0.5.1](../PROGRESSION_LOOP_0_5.md) | Scope Action utilisé techniquement stable | Aucune ; G4 fermé ou dérogation explicite requise |
| 3 | [Persistence 0.6.1](../PERSISTENCE_LOOP_0_6.md) | Schémas Build/Progression acceptés | Aucune ; G4, threat model data et rollback requis |

Cet ordre décrit les dépendances, pas un calendrier ni une permission de lancer
les trois slices. Chaque sous-gate peut s'arrêter avec `FAIL`, `PARTIAL` ou
`UNKNOWN` sans entraîner automatiquement la suivante.

## Gates

### G0 — Fondation reproductible

Exige : toolchain pinée, source de vérité, synchronisation, vérification statique,
récupération locale et aucune ambiguïté d'autorité. **État : `PASS`.**

### G1 — Causalité de la boucle de défense

Exige : menace lisible, résultat autoritaire, première brèche factuelle,
restauration, modification et rematch sans duplication. **État : `PASS
TECHNIQUE`, preuve humaine `UNKNOWN`.**

### G2 — Construction mobile et protocole borné

Exige : fermeture de T25, T27, T31 et T32 ; touch, clavier/souris et manette
applicables ; deux clients ; latence ; abus ; dix cycles ; aucune dérive
runtime. **État : `PASS TECHNIQUE`; preuve humaine `UNKNOWN`.**

Sans dérogation, G2 autorise uniquement la préparation du protocole humain G3,
les correctifs et la dette directement bloquante. ADR-0002 déroge désormais à
cette dépendance uniquement pour rendre admissible la décision Action 0.4.1 ;
Progression 0.5.1 et Persistence 0.6.1 restent fermées.

### G3 — Comprendre → modifier → relancer

Exige un panel non briefé et un protocole de recherche accepté. Les seuils
provisoires du contrat actif sont mesurés sans aide orale, avec observations et
verbatims anonymisés. Le gate décide : continuer, modifier la boucle ou pivoter.
**État de preuve : `UNKNOWN`. Exécution participant : indisponible. Séquencement :
`WAIVED_BY_FOUNDER` par [ADR-0002](../adr/ADR-0002-waive-g3-participant-gate.md).**
Les auto-tests techniques ou de fondateur réduisent les défauts, mais ne
remplacent pas la preuve d'un joueur non briefé.

Tant que la preuve reste `UNKNOWN` : pas de revendication de `PASS PRODUIT`, de
rétention ou de différenciation prouvée.

### G4 — Progression et persistance minimales

Entrée normale : G3 passé. Après ADR-0002, une entrée anticipée exige une
décision founder séparée fondée sur un résultat Action 0.4.1 techniquement
stable. Dans les deux cas, G4 exige avant implémentation : hypothèse de retour, schéma
versionné, menace data, migration/rollback, environnement isolé, idempotence et
test de panne. Le runbook opérateur doit être accepté et répété sur fixtures
avant toute recovery. Scope : une seule progression nécessaire à une preuve de
retour. **État : fermé.**

### G5 — Valeur sociale réelle

Entrée : boucle solo utile et persistance minimale sûres. Exige : hypothèse
sociale précise, permissions/griefing, récompenses non exploitables, reconnexion
et comparaison solo/groupe. **État : fermé.**

### G6 — Alpha instrumentée

Entrée : G3–G5 suffisamment passés. Exige : dictionnaire KPI, taxonomie
d'événements, consentement et minimisation, funnels validés, cohortes et
dashboard d'erreurs/performance. Le catalogue 0.9.1 est un brouillon et
n'autorise aucune émission. **État : fermé.**

### G7 — Économie et monétisation éthiques

Entrée : valeur gratuite et retour observés. Exige : sources/puits, invariants,
double-spend, reçu idempotent, politiques Roblox revalidées, prix et suppression
d'offre, aucun pay-to-win. Trading, hasard payant et battle pass restent des
décisions séparées et non présumées. **État : fermé.**

### G8 — LiveOps soutenable

Entrée : boucle et instrumentation stables. Exige : briques réutilisables,
capacité d'équipe mesurée, KPI/guardrails par événement, fallback, localisation,
fin d'événement et rétrospective. **État : fermé.**

### G9 — Lancement public et scale

Exige : matrice appareils réels, charge, incidents, rollback, sauvegardes,
conformité, support, observabilité et rollout progressif. Les seuils sont fixés
sur données représentatives, pas inventés au prototype. **État : fermé.**

## Gate de capacité transverse — Blender Visual Workbench

Les gates `CAP-BLENDER-MCP-001` à `008` définis dans
[BLENDER_MCP_WORKBENCH.md](../BLENDER_MCP_WORKBENCH.md) autorisent une boucle
locale d'inspection, d'expérimentation et de reproduction déterministe pour les
assets 3D. La vertical slice locale du 17 juillet 2026 est `PASS`.

Ce gate transverse ne change aucun état G0–G9. Il ne prouve pas l'acceptation
artistique, la lisibilité sur appareil réel, le comportement Studio, la
publication staging ou un résultat joueur. Une promotion de source et chaque
preuve Studio/mobile restent soumises à leurs autorités propres.

## Règle de dérogation

Une dérogation nomme la preuve manquante, le risque accepté, le scope maximal,
la date ou condition de réouverture et le décideur. Elle ne change jamais
`UNKNOWN` en `PASS` et n'autorise pas automatiquement le gate suivant.

ADR-0002 satisfait cette règle uniquement pour la transition Build 0.3 →
décision Action 0.4.1. Chaque transition ultérieure exige sa propre autorité.

L'enregistrement ou l'intégration d'un contrat `IN_REVIEW`, y compris Action
0.4.1, Progression 0.5.1 ou Persistence 0.6.1, ne constitue pas une dérogation.
Une autorisation anticipée doit être formulée explicitement par le founder et
respecter la règle ci-dessus.

Avant d'ouvrir un gate, filtrer dans
[PRODUCT_DEFINITION_REGISTER.md](PRODUCT_DEFINITION_REGISTER.md) les domaines
associés, décider ce qui entre réellement dans le scope, puis créer ou accepter
uniquement les contrats nécessaires à la preuve suivante.
