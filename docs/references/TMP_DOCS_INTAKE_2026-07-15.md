# Relevé d'intake — `tmp/docs` — 2026-07-15

| Champ | Valeur |
| --- | --- |
| ID | `EVIDENCE-DOC-INTAKE-001` |
| Classe | `EVIDENCE` |
| Cycle de vie | `RECORDED` |
| Propriétaire | Founder |
| Mainteneur | Product/Engineering |
| Scope | 25 fichiers présents sous `tmp/docs` le 2026-07-15 |
| Source | Lecture intégrale locale et comparaison au corpus autoritaire |
| Dernière revue | 2026-07-15 |
| Revue suivante | Nouvelle source, ouverture du gate concerné ou demande explicite de réévaluation |

## Méthode

Chaque fichier a été lu intégralement puis comparé au GDD 1.0.1, aux stage
gates, aux contrats 0.4.1–0.6.1, aux actifs existants et au standard
documentaire. Les décisions signifient :

- `INTEGRATE` : valeur durable, faible duplication et risque actuel réduit ;
- `DEFER` : contenu potentiellement utile, mais dépendance ou gate fermé ;
- `REJECT` : doublon, contradiction, version obsolète ou mauvaise forme
  documentaire.

`DEFER` n'est ni une acceptation ni une promesse de future implémentation. Les
sources restent intactes dans `tmp/` et ne possèdent aucune autorité produit.

## Décisions 25/25

| Fichier source | Décision | Motif | Destination ou condition de réexamen |
| --- | --- | --- | --- |
| `ANALYTICS_EVENT_CATALOG_0.9.md` | `INTEGRATE` | Taxonomie bornée utile pour préparer G6, à condition de séparer candidats et événements actifs | `docs/ANALYTICS_EVENT_CATALOG_0_9.md`, révision 0.9.1 `DRAFT` |
| `ART_AUDIO_PRODUCTION_BIBLE_1.0.md` | `REJECT` | Déclare prématurément `Industrial Toy Defense` alors que le plan Art Direction compare encore trois territoires | Réexaminer seulement après sélection humaine et Art Bible gelée |
| `ASSET_REGISTRY_TEMPLATE.csv` | `REJECT` | Duplique le registre JSON et le workflow 3D déjà autoritaires | Utiliser `assets-3d/registry/staging.json` |
| `BETA_BUILD_MANIFEST_TEMPLATE.json` | `DEFER` | Suppose profil V5 et features 0.7–0.9 inexistantes | G6/G9 après acceptation des schémas et flags réels |
| `BETA_EXPERIMENT_RUNBOOK_0.9.md` | `DEFER` | Expérimentation publiée et cohortes non autorisées ; dépend d'une instrumentation G6 | Réexaminer à l'entrée G6 |
| `BETA_RELEASE_RUNBOOK_1.0.md` | `DEFER` | Publication Limited et rollback de release appartiennent à G9 | Réexaminer à l'entrée G9 |
| `BUG_TRIAGE_TEMPLATE.md` | `INTEGRATE` | Modèle immédiatement utile, indépendant du scope gameplay | `docs/templates/BUG_TRIAGE_TEMPLATE.md` |
| `CODEX_PROMPT_Expedition_Loop_0.7.md` | `REJECT` | Duplique `AGENTS.md`, présume schéma V3 et autorise une slice fermée | Créer un ExecPlan seulement après autorisation de la slice |
| `CODEX_PROMPT_Social_Loop_0.8.md` | `REJECT` | Duplique `AGENTS.md`, présume G5 et des services live non autorisés | Créer un ExecPlan seulement après ouverture G5 |
| `COMPLIANCE_RELEASE_CHECKLIST_1.0.md` | `DEFER` | Checklist dépendante de politiques et d'une release G9 ; revalidation live obligatoire | Réexaminer à l'entrée G9 |
| `EXPEDITION_PLAYTEST_RUNBOOK_0.7.md` | `DEFER` | Dépend du contrat Expedition non accepté et de Persistence stable | Réexaminer avec une slice Expedition acceptée |
| `PERFORMANCE_BUDGETS_1.0.md` | `INTEGRATE` | Cadre de mesure mobile utile maintenant, après suppression des faux absolus et scénarios futurs actifs | `docs/PERFORMANCE_BUDGETS_1_0.md`, révision 1.0.1 `IN_REVIEW` |
| `PERSISTENCE_OPERATIONS_RUNBOOK_0.6.md` | `INTEGRATE` | Ferme le risque opérationnel recovery, mais doit suivre le contrat 0.6.1 et T01–T112 | `docs/PERSISTENCE_OPERATIONS_RUNBOOK_0_6.md`, révision 0.6.1 `IN_REVIEW` |
| `Roblox_Top_1_Expedition_Loop_0.7.md` | `DEFER` | Bonne hypothèse, mais dépend de G4, Persistence et d'une migration V3 inexistante ; architecture disque fictive | Réexaminer après preuve 0.6.1 et décision de scope Expedition |
| `Roblox_Top_1_Retention_Onboarding_Loop_0.9.md` | `DEFER` | Mélange FTUE, G6, expérimentation, localisation et bêta ; présume V5 et toutes les slices précédentes | Découper just-in-time après G3–G6 |
| `Roblox_Top_1_Social_Loop_0.8.md` | `DEFER` | Dépend de G5, Persistence, MemoryStore, Teleport et preuves live privées inexistantes | Réexaminer à l'entrée G5 |
| `Roblox_Top_1_Vertical_Slice_1.0_Beta_Candidate.md` | `DEFER` | Assemble tous les systèmes futurs et une release G9 sans preuves intermédiaires | Réexaminer seulement après gates G3–G9 applicables |
| `SOCIAL_INTEGRATION_RUNBOOK_0.8.md` | `DEFER` | Dépend du contrat Social, de G5 et de tests live multi-comptes | Réexaminer avec le contrat Social accepté |
| `VERIFY_Action_Loop_0.4.md` | `REJECT` | Duplique le contrat et s'arrête à T50 au lieu de T63 | Utiliser la Definition of Done 0.4.1 |
| `VERIFY_Expedition_Loop_0.7.md` | `DEFER` | Duplique une future Definition of Done non acceptée | Réexaminer avec une éventuelle 0.7 révisée |
| `VERIFY_Persistence_Loop_0.6.md` | `REJECT` | Duplique le contrat, utilise T90 au lieu de T112 et contient d'anciennes métadonnées | Utiliser le contrat 0.6.1 et son nouveau runbook |
| `VERIFY_Progression_Loop_0.5.md` | `REJECT` | Duplique le contrat, utilise T65 au lieu de T75 et l'ancien `SessionProfile` | Utiliser la Definition of Done 0.5.1 |
| `VERIFY_Retention_Onboarding_Loop_0.9.md` | `DEFER` | Dépend de la spécification 0.9 non acceptée et de G6 | Réexaminer après découpage d'une slice FTUE autorisée |
| `VERIFY_Social_Loop_0.8.md` | `DEFER` | Dépend de G5 et de services live non autorisés | Réexaminer avec une éventuelle 0.8 acceptée |
| `VERIFY_Vertical_Slice_1.0.md` | `DEFER` | Gate de release G9 prématuré et dépendances non prouvées | Réexaminer avec une Beta Candidate réellement autorisée |

## Résultat

- `INTEGRATE` : 4 fichiers.
- `DEFER` : 14 fichiers.
- `REJECT` : 7 fichiers.
- Fichiers lus et classés : 25/25.

Cette sélection optimise la valeur documentaire actuelle : récupération des
données, mesure de performance, préparation analytique et qualité de triage.
Elle évite d'étendre silencieusement le produit vers Expedition, Social,
Onboarding ou Beta avant leurs gates.
