# Product Definition Register Integration — ExecPlan

## Outcome

Intégrer dans le corpus autoritaire un registre unique et exhaustif, à la date
de revue, de tout ce qui reste à définir, décider, accepter, implémenter ou
prouver pour Roblox Top 1.

Le registre doit transformer la destination large du GDD en un inventaire
actionnable sans autoriser prématurément les systèmes fermés. Pour chaque
domaine, il indique :

- la maturité de définition ;
- le statut d'implémentation ou de preuve ;
- le gate applicable ;
- les décisions encore ouvertes ;
- la source qui deviendra autoritaire ;
- la preuve minimale de fermeture ;
- le déclencheur de revue.

Ce travail est documentaire uniquement. Il n'autorise aucune feature, aucune
publication, aucune mutation Studio, aucune collecte Analytics et aucune
ouverture de G4 à G9.

## Baseline — 2026-07-16

- `G0 = PASS`.
- `G1` et `G2 = PASS TECHNIQUE`, preuve humaine `UNKNOWN`.
- `G3 = UNKNOWN`, exécution `BLOCKED` faute de panel non briefé.
- `G4` à `G9` sont fermés.
- Action 0.4.1, Progression 0.5.1 et Persistence 0.6.1 sont `IN_REVIEW`.
- Analytics 0.9.1 est `DRAFT`.
- Les budgets de performance sont `IN_REVIEW` et sans baseline physique.
- Salvaged Frontier est verrouillée créativement ; les six objets sélectionnés
  restent `CANDIDATE`, Studio `UNKNOWN`, mobile physique `BLOCKED` et
  `productionApproved=false`.
- Le GDD décrit une destination large couvrant produit, gameplay, contenu,
  social, données, économie, LiveOps et lancement, mais ne ferme pas chaque
  décision exécutable.

## Acceptance criteria

1. Un document unique couvre les 28 domaines ouverts identifiés dans le GDD,
   la roadmap, les risques et les contrats candidats.
2. Chaque domaine sépare maturité de définition, implémentation et preuve.
3. Les éléments fermés par gate sont enregistrés `DEFERRED_BY_GATE`, jamais
   promus en backlog actif.
4. Les éléments optionnels comme trading, battle pass ou véhicules exigent une
   décision explicite avant toute spécification détaillée.
5. Les éléments artistiques séparent constitution créative, canon d'objet,
   implémentation Blender, Studio, mobile physique et approbation humaine.
6. Le registre définit une règle d'entrée, de fermeture et de dépréciation des
   éléments.
7. GDD, portail documentaire, roadmap, registre documentaire et registre des
   risques routent vers le nouveau document.
8. Aucun statut de gate ou contrat existant n'est renforcé sans preuve.
9. UTF-8, liens, registre, checks du dépôt et whitespace passent.

## Intended files

- Ajouter `docs/00-governance/PRODUCT_DEFINITION_REGISTER.md`.
- Mettre à jour :
  - `docs/README.md`
  - `docs/00-governance/DOCUMENT_REGISTER.md`
  - `docs/00-governance/ROADMAP_AND_STAGE_GATES.md`
  - `docs/00-governance/RISK_REGISTER.md`
  - `docs/00-governance/GLOSSARY.md`
  - `Roblox_Top_1_Game_Design_Document_v1.0.md`
- Enregistrer ce plan dans le registre documentaire.

## Verification

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
git diff --check
git status --short
```

Exécuter aussi un audit UTF-8, H1, liens relatifs et présence au registre sur
les documents modifiés.

Studio et tests runtime sont non applicables : aucun fichier gameplay, Studio
ou asset n'est modifié.

## Recovery

- Préserver les formulations et statuts live plus récents.
- Si une ligne contredit un contrat accepté, corriger le registre, pas le
  contrat.
- Ne pas créer un document détaillé par futur système : le registre est
  l'inventaire, les contrats sont créés just-in-time à l'ouverture du gate.
- Toute suppression future conserve le motif : défini, rejeté, remplacé ou hors
  scope.

## Progress

- 2026-07-16 : sources d'autorité, gates, risques, GDD et registre relus.
- 2026-07-16 : taxonomie et périmètre du registre fixés.
- 2026-07-16 : registre actif créé avec 28 domaines, statuts indépendants,
  détails de fermeture et priorités P0 à P3.
- 2026-07-16 : GDD 1.0.2, portail, roadmap 1.0.3, risques, glossaire, README et
  registre documentaire synchronisés.
- 2026-07-16 : `scripts/check.ps1`, `git diff --check`, audit UTF-8/H1/liens
  sur 46 fichiers et audit exhaustif du registre documentaire passent.
