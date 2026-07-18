# Documentation — Roblox Top 1

| Champ | Valeur |
| --- | --- |
| ID | `DOCS-INDEX` |
| Classe | `REFERENCE` |
| Cycle de vie | `ACTIVE` |
| Propriétaire | Founder |
| Dernière revue | 2026-07-18 |
| Revue suivante | À chaque changement de gate, de document autoritaire ou de workflow |

Ce fichier est l'unique porte d'entrée du corpus. Il décrit où trouver la
vérité ; il ne duplique pas les contrats détaillés.

Inventaire complet :
[DOCUMENT_REGISTER.md](00-governance/DOCUMENT_REGISTER.md).

Inventaire exhaustif des décisions, systèmes, contenus et preuves qui restent
à fermer :
[PRODUCT_DEFINITION_REGISTER.md](00-governance/PRODUCT_DEFINITION_REGISTER.md).

## Situation en une minute

La North Star est une ambition long terme, pas une preuve de product-market fit.
Le résultat produit recherché maintenant est plus étroit : un joueur comprend
une faiblesse de sa forteresse, la modifie et relance volontairement.

Le dernier build enregistré de la Defense Loop 0.2 possède un `PASS TECHNIQUE`
et un `PASS PROVISOIRE / GO CONDITIONNEL`. Le dernier build enregistré de la
Build Loop 0.3 possède également un `PASS TECHNIQUE` avec T01–T32 `PASS`. Ces
verdicts sont liés aux exécutions décrites dans leurs rapports : ils ne
certifient pas automatiquement le worktree courant après modification. Aucun
test avec un panel de joueurs non briefés n'a transformé cette preuve technique
en `PASS PRODUIT` ; la compréhension humaine reste `UNKNOWN`. Le founder a
renoncé à l'exécution participant de G3 pour le séquencement interne par
[ADR-0002](adr/ADR-0002-waive-g3-participant-gate.md), sans modifier ce verdict.

Les spécifications candidates [Action Loop 0.4.1](ACTION_LOOP_0_4.md),
[Progression Loop 0.5.1](PROGRESSION_LOOP_0_5.md) et
[Persistence Loop 0.6.1](PERSISTENCE_LOOP_0_6.md) sont enregistrées
intégralement avec un cycle `IN_REVIEW`. Elles préservent les prochaines options
de design, mais leur présence ne constitue ni acceptation, ni dérogation aux
stage gates, ni preuve d'un résultat joueur.

## Chaîne d'intégration actuelle

| Étape | Contrat / preuve | État | Condition d'entrée suivante |
| --- | --- | --- | --- |
| Baseline | [Build Loop 0.3](BUILD_LOOP_0_3.md) et son [rapport](BUILD_LOOP_0_3_TEST_REPORT.md) | T01–T32 `PASS`, gate humain `UNKNOWN`, séquencement waived | Décision Action 0.4.1 |
| Action | [Action Loop 0.4.1](ACTION_LOOP_0_4.md) | `IN_REVIEW`, 63 tests spécifiés | Acceptation founder puis preuve technique ; humain séparé |
| Progression | [Progression Loop 0.5.1](PROGRESSION_LOOP_0_5.md) | `IN_REVIEW`, 75 tests spécifiés, mémoire serveur | G4 ou dérogation explicite |
| Persistence | [Persistence Loop 0.6.1](PERSISTENCE_LOOP_0_6.md) | `IN_REVIEW`, 112 tests spécifiés, DataStore inactif | G4, schémas acceptés, threat model et rollback |

Le founder seul peut exécuter des preuves techniques autorisées, mais ne peut
pas produire la preuve humaine G3 d'un joueur représentatif non briefé. Cette
limite est un manque de preuve accepté par ADR-0002, pas un échec du prototype
ni une preuve positive.

## Ordre d'autorité

1. Demande explicite actuelle du founder.
2. GDD accepté, contrats acceptés et ADR applicables.
3. Comportement exécutable et tests, qui décrivent la réalité observée.
4. Patterns d'implémentation existants.
5. Hypothèses explicitement étiquetées.

Si le code contredit un contrat accepté, le code révèle un écart : il ne modifie
pas silencieusement le produit. La procédure complète est définie dans
[DOCUMENTATION_STANDARD.md](00-governance/DOCUMENTATION_STANDARD.md).

## Parcours de lecture

### Décider du produit

1. [PRODUCT_CONSTITUTION.md](00-governance/PRODUCT_CONSTITUTION.md)
2. [Game Design Document v1.0.4](../Roblox_Top_1_Game_Design_Document_v1.0.md)
3. [Méthode de rétention et registre d’hypothèses d’innovation](PRODUCT_INNOVATION_AND_RETENTION_DOCTRINE.md)
4. [ROADMAP_AND_STAGE_GATES.md](00-governance/ROADMAP_AND_STAGE_GATES.md)
5. [Registre global de ce qui reste à définir](00-governance/PRODUCT_DEFINITION_REGISTER.md)
6. Contrat de la slice active : [BUILD_LOOP_0_3.md](BUILD_LOOP_0_3.md)
7. Preuve actuelle : [BUILD_LOOP_0_3_TEST_REPORT.md](BUILD_LOOP_0_3_TEST_REPORT.md)
8. Candidats suivants, dans l'ordre de dépendance :
   [Action 0.4.1](ACTION_LOOP_0_4.md),
   [Progression 0.5.1](PROGRESSION_LOOP_0_5.md), puis
   [Persistence 0.6.1](PERSISTENCE_LOOP_0_6.md)

### Implémenter ou vérifier

1. [AGENTS.md](../AGENTS.md)
2. [TOOLING.md](TOOLING.md)
3. [Blender Visual Workbench MCP](BLENDER_MCP_WORKBENCH.md) pour toute
   inspection ou correction visuelle Blender interactive
4. Contrat de la slice concernée
5. ExecPlan correspondant sous [`plans/`](../plans/)
6. [Budgets et protocole de performance](PERFORMANCE_BUDGETS_1_0.md) lorsque le
   changement affecte runtime, appareils, réseau ou charge
7. [Runbook Persistence](PERSISTENCE_OPERATIONS_RUNBOOK_0_6.md) uniquement pour
   une opération 0.6.1 explicitement autorisée
8. Tests et rapport de preuve ; utiliser le
   [modèle de triage](templates/BUG_TRIAGE_TEMPLATE.md) pour un défaut

### Comprendre un terme, un risque ou une décision

- [GLOSSARY.md](00-governance/GLOSSARY.md)
- [RISK_REGISTER.md](00-governance/RISK_REGISTER.md)
- [PRODUCT_DEFINITION_REGISTER.md](00-governance/PRODUCT_DEFINITION_REGISTER.md)
- [ADR](adr/README.md)
- [Références officielles](references/ROBLOX_OFFICIAL_SOURCES.md)
- [Catalogue Analytics candidat](ANALYTICS_EVENT_CATALOG_0_9.md) — `DRAFT`, G6
  fermé, aucun événement officiel actif
- [Relevé d'intake de `tmp/docs`](references/TMP_DOCS_INTAKE_2026-07-15.md)

## Classes documentaires

| Classe | Question | Autorité |
| --- | --- | --- |
| `CANON` | Qu'est fondamentalement le jeu ? | Normative, modification exceptionnelle |
| `CONTRACT` | Quel comportement doit être livré ? | Normative dans son scope/version |
| `HYPOTHESIS` | Que pensons-nous sans preuve suffisante ? | Non normative |
| `CONFIG` | Quelle valeur ajustable est active et dans quelles bornes ? | Normative pour l'exécution concernée |
| `PLAN` | Comment allons-nous produire et vérifier un changement ? | Opérationnelle, temporaire |
| `EVIDENCE` | Qu'avons-nous réellement observé ? | Factuelle, jamais promesse produit |
| `REFERENCE` | Comment naviguer ou appliquer une pratique ? | Informative sauf délégation explicite |

La classe, le cycle de vie et le verdict sont trois dimensions séparées. Un
rapport `EVIDENCE` peut être `RECORDED` avec un verdict global `PARTIAL`.

## Inconnues bloquantes ou structurantes

- Compréhension, confort et rematch volontaire par des joueurs non briefés :
  `UNKNOWN`; exécution participant renoncée pour le séquencement interne par
  ADR-0002, sans `PASS PRODUIT`.
- Build Loop 0.3 T01–T32 : `PASS`; gate humain : `UNKNOWN`.
- Action 0.4.1, Progression 0.5.1 et Persistence 0.6.1 : contrats candidats
  `IN_REVIEW`, intégrés au corpus mais sans preuve d'implémentation.
- Rétention D1/D7/D30, comportement social réel et compatibilité appareil à
  grande échelle : `UNKNOWN` avant trafic représentatif.
- Persistance, économie, monétisation, trading et LiveOps : non validés et hors
  scope actuel.
- Budgets de performance 1.0.1 : `IN_REVIEW` ; aucune baseline mobile réelle
  encore sélectionnée, donc mesures globales `UNKNOWN`.
- Catalogue Analytics 0.9.1 : `DRAFT` ; G6 fermé et aucune émission officielle
  autorisée.
- Workflow d'assets 3D : contrat 1.9.0 `ACCEPTED`, implémentation v3.14.0
  `PARTIAL` ; Salvaged Frontier est verrouillée créativement, la couche
  précanonique locale est `PASS`, 18 canons / 48 variantes sont validés, et le
  Visual Workbench MCP possède une vertical slice locale transactionnelle
  `PASS`.
  Les six canons sélectionnés restent `CANDIDATE`, Studio courant est `UNKNOWN`,
  le mobile physique est `BLOCKED` et la production n'est pas approuvée. Le
  sous-corpus détaillé commence dans
  [`tools/roblox-art-bible-sota-v3/docs/README.md`](../tools/roblox-art-bible-sota-v3/docs/README.md).

## Règle de croissance du corpus

Un document n'est créé que s'il possède un lecteur, une décision ou un risque,
une autorité, un propriétaire et un déclencheur de revue. Les documents futurs
sont déclenchés par les [stage gates](00-governance/ROADMAP_AND_STAGE_GATES.md),
pas par le désir de remplir une arborescence.

Le registre de définition conserve les sujets futurs dans un document unique.
Un contrat séparé n'est créé qu'au moment où son gate s'ouvre, où une
dérogation l'autorise ou lorsqu'une ambiguïté actuelle crée déjà un risque.
