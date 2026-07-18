# Registre documentaire

| Champ | Valeur |
| --- | --- |
| ID | `GOV-REGISTER-001` |
| Classe | `REFERENCE` |
| Cycle de vie | `ACTIVE` |
| Propriétaire | Founder |
| Dernière revue | 2026-07-18 |
| Revue suivante | Ajout, renommage, remplacement ou changement d'autorité d'un document |

Le registre couvre le corpus Markdown durable du dépôt à la date de revue. Les
prototypes jetables sous `tmp/`, caches et artefacts générés ne font pas partie
du corpus. Il classe les documents sans réécrire leur historique. Le contenu du
document reste la source de son scope ; ce registre tranche son rôle dans le
corpus.

## Autorité fondatrice et navigation

| ID | Document | Classe | Cycle | Portée / état | Owner | Déclencheur de revue |
| --- | --- | --- | --- | --- | --- | --- |
| `EXEC-CONSTITUTION` | [AGENTS.md](../../AGENTS.md) | `CONTRACT` | `ACCEPTED` | Constitution d'exécution, sécurité, preuve et Git | Founder | Changement de workflow, risque ou règle Codex |
| `PRODUCT-GDD-001` | [GDD v1.0.4](../../Roblox_Top_1_Game_Design_Document_v1.0.md) | `CONTRACT` | `ACCEPTED` | Vision v1.0 + G3 waived pour le séquencement interne + promesse publique bornée aux capacités prouvées ; résultats joueur non prouvés | Founder | Décision produit, preuve invalidante ou acceptation d'une slice |
| `ROOT-INDEX` | [README.md](../../README.md) | `REFERENCE` | `ACTIVE` | Résumé dépôt et état courant | Engineering | Gate ou commande principale modifiés |
| `DOCS-INDEX` | [docs/README.md](../README.md) | `REFERENCE` | `ACTIVE` | Porte d'entrée du corpus | Founder | Toute modification d'autorité ou de gate |
| `GOV-REGISTER-001` | `DOCUMENT_REGISTER.md` | `REFERENCE` | `ACTIVE` | Inventaire complet | Founder | Tout fichier documentaire ajouté ou déplacé |

## Gouvernance

| ID | Document | Classe | Cycle | Portée / état | Owner | Déclencheur de revue |
| --- | --- | --- | --- | --- | --- | --- |
| `GOV-CANON-001` | [PRODUCT_CONSTITUTION.md](PRODUCT_CONSTITUTION.md) | `CANON` | `ACCEPTED` | Identité, principes et limites durables | Founder | Modification canonique explicite |
| `GOV-STD-001` | [DOCUMENTATION_STANDARD.md](DOCUMENTATION_STANDARD.md) | `CONTRACT` | `ACCEPTED` | v1.1.0 ; taxonomie, autorité, lifecycle et qualité automatisée | Founder | Ambiguïté récurrente, exclusion ou croissance d'équipe |
| `GOV-CONTRACT-002` | [ROADMAP_AND_STAGE_GATES.md](ROADMAP_AND_STAGE_GATES.md) | `CONTRACT` | `ACCEPTED` | v1.1.0 ; G3 waived par ADR-0002 sans `PASS PRODUIT`, autorisations de scope et domaines ouverts | Founder | Nouveau gate, dérogation ou obligation documentaire |
| `GOV-RISK-001` | [RISK_REGISTER.md](RISK_REGISTER.md) | `REFERENCE` | `ACTIVE` | Risques, signaux et contrôles | Founder | Incident, gate, dépendance ou preuve |
| `GOV-REF-001` | [GLOSSARY.md](GLOSSARY.md) | `REFERENCE` | `ACTIVE` | Vocabulaire contrôlé | Product design | Nouveau terme ou ambiguïté |
| `GOV-REGISTER-002` | [PRODUCT_DEFINITION_REGISTER.md](PRODUCT_DEFINITION_REGISTER.md) | `REFERENCE` | `ACTIVE` | 28 domaines ; inventaire exhaustif des décisions, contenus, systèmes et preuves encore ouverts ou différés | Founder/Product | Gate, décision de scope, contrat, preuve ou rejet |
| `PRODUCT-RETENTION-001` | [PRODUCT_INNOVATION_AND_RETENTION_DOCTRINE.md](../PRODUCT_INNOVATION_AND_RETENTION_DOCTRINE.md) | `CONTRACT` | `ACCEPTED` | Méthode éthique/mesure acceptée ; registre interne d’hypothèses non prouvées | Founder/Product | Nouvelle preuve joueur, changement plateforme ou ouverture G3/G6/G7/G9 |

## Contrats et preuves de slices

| ID | Document | Classe | Cycle | Portée / verdict | Owner | Déclencheur de revue |
| --- | --- | --- | --- | --- | --- | --- |
| `SLICE-DEF-001` | [DEFENSE_LOOP_0_1.md](../DEFENSE_LOOP_0_1.md) | `CONTRACT` | `SUPERSEDED` | Première boucle historique, remplacée par 0.2 | Product/Engineering | Régression nécessitant l'historique 0.1 |
| `SLICE-DEF-002` | [DEFENSE_LOOP_0_2.md](../DEFENSE_LOOP_0_2.md) | `CONTRACT` | `ACCEPTED` | Baseline défense ; `PASS TECHNIQUE`, gate humain `UNKNOWN` | Product/Engineering | Modification de la boucle conservée par 0.3 |
| `SLICE-BUILD-003` | [BUILD_LOOP_0_3.md](../BUILD_LOOP_0_3.md) | `CONTRACT` | `ACCEPTED` | Dernier build enregistré : `PASS TECHNIQUE`, T01–T32 `PASS`; worktree ultérieur non couvert automatiquement ; gate humain `UNKNOWN` | Product/Engineering | Résultat G3, modification runtime ou changement de scope |
| `EVIDENCE-BUILD-003` | [BUILD_LOOP_0_3_TEST_REPORT.md](../BUILD_LOOP_0_3_TEST_REPORT.md) | `EVIDENCE` | `RECORDED` | Exécution historique liée au build testé : `PASS TECHNIQUE`; gate humain `UNKNOWN` | Engineering | Addendum après toute modification ou nouvelle exécution |
| `SLICE-ACTION-004` | [ACTION_LOOP_0_4.md](../ACTION_LOOP_0_4.md) | `CONTRACT` | `IN_REVIEW` | Révision 0.4.1 ; prochaine décision admissible sous ADR-0002 ; aucune implémentation ni preuve joueur enregistrée | Founder/Product/Engineering | Acceptation, résultat de slice ou changement de scope |
| `SLICE-PROGRESSION-005` | [PROGRESSION_LOOP_0_5.md](../PROGRESSION_LOOP_0_5.md) | `CONTRACT` | `IN_REVIEW` | Révision 0.5.1 ; progression transactionnelle et migration BuildPlan 1→2 ; G4 fermé | Founder/Product/Engineering | Entrée G4 ou dérogation explicite, résultat Action 0.4.1 ou changement de progression |
| `SLICE-PERSISTENCE-006` | [PERSISTENCE_LOOP_0_6.md](../PERSISTENCE_LOOP_0_6.md) | `CONTRACT` | `IN_REVIEW` | Révision 0.6.1 ; persistance, conflits et récupération bornés ; DataStore non autorisé | Founder/Product/Engineering | Entrée G4 ou dérogation explicite, acceptation du schéma ou changement de risque data |
| `OPS-PERSIST-006` | [PERSISTENCE_OPERATIONS_RUNBOOK_0_6.md](../PERSISTENCE_OPERATIONS_RUNBOOK_0_6.md) | `CONTRACT` | `IN_REVIEW` | Opérations Data Test et recovery 0.6.1 ; aucune autorisation opérateur active | Founder/Engineering | Acceptation 0.6.1, incident, schéma ou API DataStore modifiés |
| `ASSET3D-CONTRACT-001` | [ROBLOX_3D_ASSET_WORKFLOW.md](../ROBLOX_3D_ASSET_WORKFLOW.md) | `CONTRACT` | `ACCEPTED` | Version 1.9.0 ; workflow v3.14.0, Salvaged Frontier `CREATIVE_DIRECTION_LOCKED`, précanonique local `PASS`, 18 canons/48 variantes et Visual Workbench local `PASS` ; six canons sélectionnés `CANDIDATE`, Studio `UNKNOWN`, mobile `BLOCKED`, `productionApproved=false` | Founder/3D | Verrou d'un canon, preuve Studio/mobile courante, révision de constitution ou contrat plateforme |
| `ASSET3D-WORKBENCH-001` | [BLENDER_MCP_WORKBENCH.md](../BLENDER_MCP_WORKBENCH.md) | `CONTRACT` | `IN_REVIEW` | MCP Blender `stdio` borné et transactionnel ; vertical slice locale `PASS`, promotion autoritative et Studio `UNKNOWN`, `productionApproved=false` | Founder/Tech Art | Approbation du contrat, évolution d'outil ou nouvelle preuve Studio/mobile |
| `EVIDENCE-BLENDER-WORKBENCH-001` | [Preuve Workbench 2026-07-17](../evidence/BLENDER_WORKBENCH_VERTICAL_SLICE_2026-07-17.md) | `EVIDENCE` | `RECORDED` | Deux pieds modifiés, rollback exact, double recompilation identique ; source autoritative inchangée et Studio non exécuté | Engineering/Tech Art | Nouvelle exécution ou promotion source explicite |
| `ASSET3D-PORTAL-001` | [Paquet Art Direction — portail](../../tools/roblox-art-bible-sota-v3/docs/README.md) | `REFERENCE` | `ACTIVE` | Bible, statut, ontologie, registre des six objets, contrats Roblox/Blender, métriques, preuves et risques | Art/Tech Art | Toute révision du paquet, d'un objet ou d'un gate |

`ROBLOX_3D_ASSET_WORKFLOW.md` est normalisé dans le corpus, lie l'exploration
Web à un paquet précanonique borné puis la génération à une définition
canonique visuelle hashée. La sélection Salvaged Frontier est une décision
explicite du founder ; l'étude aveugle reste une validation indépendante. Son
cycle `ACCEPTED` autorise l'usage de la spécification et de la constitution
créative dans leur scope. L'implémentation `PARTIAL` ne remplace pas les gates
produit, les locks d'objets, Studio, le mobile physique ou l'approbation de
production, et n'autorise aucune publication de production.

Les contrats 0.4.1, 0.5.1 et 0.6.1 sont enregistrés intégralement afin de
préserver la direction proposée et ses critères. Leur cycle `IN_REVIEW` signifie
qu'ils ne remplacent pas la roadmap, ne constituent pas une dérogation et ne
transforment aucune preuve `UNKNOWN` en `PASS`.

## Tooling, Studio et collaboration

| ID | Document | Classe | Cycle | Portée / état | Owner | Déclencheur de revue |
| --- | --- | --- | --- | --- | --- | --- |
| `ENG-TOOLING-001` | [TOOLING.md](../TOOLING.md) | `CONTRACT` | `ACCEPTED` | Toolchain, Script Sync et Studio MCP | Engineering | Version, commande ou mapping modifié |
| `CONFIG-PERF-001` | [PERFORMANCE_BUDGETS_1_0.md](../PERFORMANCE_BUDGETS_1_0.md) | `CONFIG` | `IN_REVIEW` | Cibles/protocole provisoires ; baseline mobile réelle `UNKNOWN` | Engineering/Founder | Appareil choisi, mesure réelle ou nouvelle charge runtime |
| `STUDIO-RECOVERY-001` | [studio/README.md](../../studio/README.md) | `REFERENCE` | `ACTIVE` | Snapshots locaux, manifests et récupération | Engineering | Nouveau snapshot ou migration Studio |
| `COLLAB-PR-001` | [.github/pull_request_template.md](../../.github/pull_request_template.md) | `REFERENCE` | `ACTIVE` | Checklist de pull request | Engineering | Definition of Done ou CI modifiée |

## ExecPlans

| ID | Document | Classe | Cycle | Portée / état | Owner | Déclencheur de revue |
| --- | --- | --- | --- | --- | --- | --- |
| `PLAN-TOOLING-001` | [toolchain-bootstrap.md](../../plans/toolchain-bootstrap.md) | `PLAN` | `ARCHIVED` | Bootstrap complet | Engineering | Investigation historique |
| `PLAN-DEF-001` | [defense-loop-0.1.md](../../plans/defense-loop-0.1.md) | `PLAN` | `ARCHIVED` | Exécution 0.1 historique | Engineering | Investigation historique |
| `PLAN-DEF-002` | [defense-loop-0.2.md](../../plans/defense-loop-0.2.md) | `PLAN` | `ARCHIVED` | Exécution 0.2 et décision conditionnelle | Engineering | Réouverture du gate humain 0.2 |
| `PLAN-BUILD-003` | [build-loop-0.3.md](../../plans/build-loop-0.3.md) | `PLAN` | `ACTIVE` | Dernière exécution enregistrée `PASS TECHNIQUE`; preuve humaine `UNKNOWN`, séquencement waived ; revalidation de tout worktree ultérieur ouverte | Engineering | Nouvelle modification, exécution ou réouverture G3 |
| `PLAN-BUILD-FIX-003` | [build-loop-0.3-critical-gameplay-fixes.md](../../plans/build-loop-0.3-critical-gameplay-fixes.md) | `PLAN` | `ACTIVE` | Correctifs bornés de propriété, ingress hostile, contrôles d'édition et récupération de vague en cours | Engineering | Vérification statique/Studio, fermeture des quatre régressions ou abandon explicite |
| `PLAN-DOCS-001` | [documentation-system-1.0.md](../../plans/documentation-system-1.0.md) | `PLAN` | `ARCHIVED` | Migration documentaire 1.0 complète | Engineering | Investigation ou évolution de la taxonomie |
| `PLAN-ASSET3D-001` | [defense-barricade-vertical-slice.md](../../plans/defense-barricade-vertical-slice.md) | `PLAN` | `ACTIVE` | Fabrique 3D locale `PARTIAL`; activation Cloud/Studio `BLOCKED` | Engineering/3D | Credentials staging, nouvelle preuve Cloud/Studio ou fermeture de gate |
| `PLAN-BLENDER-MCP-001` | [blender-mcp-workbench-integration.md](../../plans/blender-mcp-workbench-integration.md) | `PLAN` | `ACTIVE` | Workbench borné intégré et vertical slice locale `PASS`; promotion autoritative et Studio restent ouverts | Engineering/Tech Art | Approbation du contrat, promotion source ou preuve Studio/mobile |
| `PLAN-ART-DIRECTION-001` | [art-direction-vertical-slice.md](../../plans/art-direction-vertical-slice.md) | `PLAN` | `ACTIVE` | Trois territoires visuels, sélection humaine et transfert ; implémentation en cours, preuves Studio/mobile `UNKNOWN` | Art/Engineering | Nouveau territoire, preuve Studio/mobile ou décision humaine |
| `PLAN-PRECANONICAL-001` | [precanonical-web-integration.md](../../plans/precanonical-web-integration.md) | `PLAN` | `ACTIVE` | Intégration précanonique locale, budget, provenance et adaptateur Web ; exécution Web externe non demandée | Art/Engineering | Première soumission Web autorisée, changement d'interface ou promotion vers canon |
| `PLAN-RETENTION-001` | [product-innovation-retention-doctrine.md](../../plans/product-innovation-retention-doctrine.md) | `PLAN` | `ARCHIVED` | Intégration et correction critique de la doctrine terminées ; hypothèses produit toujours non prouvées | Product/Engineering | Révision de doctrine ou nouvelle preuve joueur |
| `PLAN-WORKFLOW-SIM-001` | [complete-3d-workflow-simulation.md](../../plans/complete-3d-workflow-simulation.md) | `PLAN` | `ARCHIVED` | Simulation locale complète `PASS`; production réelle `BLOCKED`, `productionApproved=false` | Engineering/3D | Régression de simulation ou activation d'une preuve réelle |
| `PLAN-REPO-AUDIT-001` | [repository-complete-audit-2026-07-17.md](../../plans/repository-complete-audit-2026-07-17.md) | `PLAN` | `ACTIVE` | Audit exhaustif fichier-par-fichier, corrections et validation finale en cours | Engineering | Clôture de l'audit ou nouveau finding |
| `PLAN-ART-DOCS-001` | [salvaged-frontier-docs-sota-hardening.md](../../plans/salvaged-frontier-docs-sota-hardening.md) | `PLAN` | `ARCHIVED` | Durcissement du sous-corpus Salvaged Frontier terminé ; preuves de production toujours séparées | Art/Tech Art | Révision de constitution, objets ou contrats artistiques |
| `PLAN-PRODUCT-DEFINITION-001` | [product-definition-register-integration.md](../../plans/product-definition-register-integration.md) | `PLAN` | `ARCHIVED` | Intégration du registre exhaustif des 28 domaines terminée | Product/Engineering | Révision du registre ou nouvelle famille de scope |
| `PLAN-SPECS-004-006` | [next-slice-specs-hardening.md](../../plans/next-slice-specs-hardening.md) | `PLAN` | `ARCHIVED` | Durcissement documentaire 0.4.1–0.6.1 terminé ; contrats toujours `IN_REVIEW` | Product/Engineering | Réouverture d'un contrat ou nouvelle décision de scope |
| `PLAN-DOCS-INTEGRATION-004-006` | [documentation-integration-0.4-0.6.md](../../plans/documentation-integration-0.4-0.6.md) | `PLAN` | `ARCHIVED` | Intégration transversale 0.4.1–0.6.1 terminée ; aucun gate modifié | Product/Engineering | Nouvelle révision ou changement d'autorité |
| `PLAN-TMP-DOCS-INTAKE-001` | [tmp-docs-intake-integration.md](../../plans/tmp-docs-intake-integration.md) | `PLAN` | `ARCHIVED` | Lecture de 25 sources temporaires et intégration sélective de quatre documents terminée | Product/Engineering | Nouvelle source temporaire ou réouverture explicite de l'intake |

## ADR, références et modèles

| ID | Document | Classe | Cycle | Portée / état | Owner | Déclencheur de revue |
| --- | --- | --- | --- | --- | --- | --- |
| `ADR-INDEX` | [adr/README.md](../adr/README.md) | `REFERENCE` | `ACTIVE` | Convention et index ADR | Engineering | Nouvel ADR ou changement de convention |
| `ADR-0001` | [ADR-0001-documentation-system.md](../adr/ADR-0001-documentation-system.md) | `CONTRACT` | `ACCEPTED` | Système documentaire just-in-time | Founder | Déclencheur indiqué dans l'ADR |
| `ADR-0002` | [ADR-0002-waive-g3-participant-gate.md](../adr/ADR-0002-waive-g3-participant-gate.md) | `CONTRACT` | `ACCEPTED` | G3 participant waived pour le séquencement interne ; preuve joueur `UNKNOWN` | Founder | Participants disponibles, résultat contradictoire ou lancement externe |
| `REF-ROBLOX-001` | [ROBLOX_OFFICIAL_SOURCES.md](../references/ROBLOX_OFFICIAL_SOURCES.md) | `REFERENCE` | `ACTIVE` | Sources primaires vérifiées | Engineering | Usage décisionnel ou changement externe |
| `EVIDENCE-DOC-INTAKE-001` | [TMP_DOCS_INTAKE_2026-07-15.md](../references/TMP_DOCS_INTAKE_2026-07-15.md) | `EVIDENCE` | `RECORDED` | 25 sources temporaires lues ; 4 intégrées, 14 différées, 7 rejetées | Product/Engineering | Nouvelle source ou ouverture d'un gate différé |
| `DATA-CONTRACT-009` | [ANALYTICS_EVENT_CATALOG_0_9.md](../ANALYTICS_EVENT_CATALOG_0_9.md) | `CONTRACT` | `DRAFT` | Taxonomie candidate 0.9.1 ; G6 fermé, aucun événement officiel actif | Product/Data | Entrée G6 ou changement AnalyticsService |
| `TPL-ADR` | [ADR_TEMPLATE.md](../templates/ADR_TEMPLATE.md) | `REFERENCE` | `ACTIVE` | Modèle de décision | Engineering | Échec du modèle à capturer une décision |
| `TPL-SPEC` | [SYSTEM_SPEC_TEMPLATE.md](../templates/SYSTEM_SPEC_TEMPLATE.md) | `REFERENCE` | `ACTIVE` | Modèle de contrat/hypothèse | Product/Engineering | Nouveau risque non couvert |
| `TPL-EVIDENCE` | [EVIDENCE_REPORT_TEMPLATE.md](../templates/EVIDENCE_REPORT_TEMPLATE.md) | `REFERENCE` | `ACTIVE` | Modèle de preuve | Engineering | Rapport ambigu ou non reproductible |
| `TPL-EXPERIMENT` | [EXPERIMENT_BRIEF_TEMPLATE.md](../templates/EXPERIMENT_BRIEF_TEMPLATE.md) | `REFERENCE` | `ACTIVE` | Hypothèse et décision expérimentale | Product/Data | Méthode de recherche modifiée |
| `TPL-BUG` | [BUG_TRIAGE_TEMPLATE.md](../templates/BUG_TRIAGE_TEMPLATE.md) | `REFERENCE` | `ACTIVE` | Reproduction, sévérité, preuve, correction et vérification d'un défaut | Engineering | Rapport ambigu ou nouveau workflow de tickets |

## Obligations documentaires par gate

| Gate | Document minimal à accepter ou créer avant implémentation |
| --- | --- |
| G3 | Protocole de playtest non briefé + rapport de recherche |
| G4 | Contrats Action/Progression/Persistence applicables, schéma, migrations, rollback, threat model data et runbook opérateur acceptés ; les candidats enregistrés restent `IN_REVIEW` |
| G5 | Contrat social, permissions, griefing et récompenses de groupe |
| G6 | Dictionnaire KPI, taxonomie d'événements acceptée et plan de qualité des données ; le catalogue 0.9.1 reste `DRAFT` |
| G7 | Contrat économie/monétisation, reçus, conformité et kill switches |
| G8 | Système LiveOps et capacité/cadence mesurée |
| G9 | Release, rollout/rollback, incident response, baselines/budgets de performance acceptés, appareils et conformité |

Ces lignes sont des obligations conditionnelles, pas une autorisation de créer
ou d'implémenter prématurément. Un candidat déjà enregistré doit encore être
accepté dans le scope du gate ou couvert par une dérogation explicite.
