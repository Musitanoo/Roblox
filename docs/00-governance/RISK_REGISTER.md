# Registre des risques

| Champ | Valeur |
| --- | --- |
| ID | `GOV-RISK-001` |
| Classe | `REFERENCE` |
| Cycle de vie | `ACTIVE` |
| Propriétaire | Founder |
| Dernière revue | 2026-07-18 |
| Revue suivante | Changement de gate, incident, nouvelle dépendance ou nouvelle preuve |

Échelle : probabilité et impact `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`. Le niveau
est une appréciation actuelle, pas une mesure statistique.

Les décisions et systèmes non fermés associés à ces risques sont suivis dans
le [registre global de définition](PRODUCT_DEFINITION_REGISTER.md). Le registre
des risques explique pourquoi un contrôle est nécessaire ; le registre de
définition précise ce qui reste à décider avant de pouvoir l'exécuter.

| ID | Risque | P | I | Signal précoce | Contrôle / preuve attendue | Propriétaire | État |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R-001 | La boucle est techniquement correcte mais non comprise ou sans rematch volontaire | HIGH | CRITICAL | Joueur attend une instruction, ne relie pas brèche et modification | Risque accepté par ADR-0002 pour le développement interne ; aucune revendication produit ; réouverture avant lancement externe | Founder/Product | ACCEPTED |
| R-002 | Surdocumentation ralentissant les expériences et créant des sources concurrentes | HIGH | HIGH | Documents sans lecteur, doublons, contrats divergents | Registre, création just-in-time, un contrat actif par scope | Founder | MITIGATING |
| R-003 | Construction inconfortable ou imprécise sur mobile faible | HIGH | CRITICAL | Mis-taps, occlusion, abandon, chauffe ou FPS instable | Appareils réels, sessions longues, mesures input/performance, G2/G9 | UX/Engineering | OPEN |
| R-004 | Client capable de forger, rejouer ou saturer des opérations | MEDIUM | CRITICAL | Révisions divergentes, double opération, budget négatif, file non bornée | Build T27 + validations, idempotence, caches et rate limits d'Action 0.4.1/Progression 0.5.1 | Engineering | OPEN |
| R-005 | Pathfinding, NPC ou physique dépassant le budget serveur/client | HIGH | HIGH | Heartbeat bas, files de path, oscillations, mémoire croissante | [Performance 1.0.1](../PERFORMANCE_BUDGETS_1_0.md), charges bornées, profiler et appareils réels avant scale | Engineering | OPEN |
| R-006 | Corruption, perte ou duplication de progression | MEDIUM | CRITICAL | Retry non idempotent, conflit multi-serveur, write ambigu ou lock perdu | G4 fermé ; contrat 0.6.1 + [runbook opérateur](../PERSISTENCE_OPERATIONS_RUNBOOK_0_6.md), fault injection et univers isolé | Engineering | AVOIDED NOW |
| R-007 | Scope prématuré : économie, trading, contenu ou infrastructure avant preuve | HIGH | HIGH | Plusieurs systèmes incomplets, délai au prochain playtest | Stage gates, vertical slice stricte, décision founder | Founder | MITIGATING |
| R-008 | Une stratégie dominante détruit adaptation et créativité | MEDIUM | HIGH | Même plan gagne partout, choix sans coût, autopsie inutile | Seeds reproductibles, télémétrie de victoire, contres lisibles | Game design | OPEN |
| R-009 | Coopération superficielle, obligatoire ou exploitable | MEDIUM | HIGH | Groupe = multiplicateur de dégâts, solo puni, griefing | Hypothèse sociale G5, permissions, contribution et comparaison solo/groupe | Product | DEFERRED |
| R-010 | Preuves surestimées ou non reproductibles | HIGH | CRITICAL | Screenshot présenté comme logique, skipped devenu PASS | Verdicts stricts, rapports avec limites, [triage reproductible](../templates/BUG_TRIAGE_TEMPLATE.md), audit du diff et des logs | Whole team | MITIGATING |
| R-011 | Dérive entre disque, Script Sync et Studio | MEDIUM | HIGH | Duplicate folders, script absent, mauvaise instance active | Workflow `TOOLING.md`, witness sync, manifests, instance confirmée | Engineering | MONITORED |
| R-012 | Cadence LiveOps insoutenable pour deux personnes | HIGH | HIGH | Dette, bugs, saisons préparées avant boucle stable | G8 fermé, contenu combinatoire, capacité mesurée et calendrier avec fallback | Founder | DEFERRED |
| R-013 | Asset ou dépendance sans provenance, licence ou maintenance | MEDIUM | HIGH | Source introuvable, version flottante, retrait de modération | Registre avant ajout, licence, pinning, alternative et owner | Engineering/Art | OPEN |
| R-014 | Politique Roblox ou conformité devenue obsolète | MEDIUM | CRITICAL | API/politique modifiée, restriction régionale non appliquée | Sources officielles datées, revalidation à G7/G9, fail closed | Founder/Engineering | DEFERRED |
| R-015 | Optimisation d’un proxy CCU au détriment de la valeur joueur | HIGH | CRITICAL | AFK, attente, sessions sans sortie, trafic non qualifié, D1 en hausse mais satisfaction en baisse | KPI par gate, activité qualifiée, guardrails confiance/bien-être et segmentation | Product/Data | MITIGATING |
| R-016 | Levier comportemental transformé en pression ou dark pattern | MEDIUM | CRITICAL | absence punie, urgence artificielle, dépense non intentionnelle, anxiété ou plainte | Doctrine de rétention, revue G7, sortie propre, kill criteria et test de dommage | Founder/Product | MITIGATING |
| R-017 | Portefeuille d’innovation trop large avant preuve du noyau | HIGH | HIGH | plusieurs signatures P1/P2 en développement, boucle P0 toujours `UNKNOWN` | priorité `Every Failure Teaches` + `The Horde Learns`, G2/G3 et tests falsifiables | Founder/Product | MITIGATING |

## Traitement

- `OPEN` : mitigation ou preuve active nécessaire.
- `MITIGATING` : contrôle en place, efficacité encore à confirmer.
- `MONITORED` : contrôle observé, surveiller les déclencheurs.
- `DEFERRED` : risque interdit par un gate ; réouvrir avant entrée.
- `AVOIDED NOW` : fonctionnalité volontairement absente.
- `ACCEPTED` : décision explicite avec justification et limite.
- `CLOSED` : preuve de réduction enregistrée ; peut être réouvert.

Tout risque `CRITICAL` qui devient applicable bloque un `PASS` tant que son
contrôle requis est `UNKNOWN`, sauf dérogation explicite conforme aux stage
gates.

## Couverture des contrats candidats intégrés

| Contrat | Risques principalement couverts | Contrôle restant avant autorisation |
| --- | --- | --- |
| Action 0.4.1 | R-001, R-003, R-004, R-005, R-009 | Acceptation founder, scope séquencé, tests T01–T63 et preuve appareil/runtime applicable |
| Progression 0.5.1 | R-004, R-007, R-008, R-015, R-016 | G4 ou dérogation, transactions T01–T75 et absence de grind/exploit observée |
| Persistence 0.6.1 | R-004, R-006, R-010, R-014 | Schémas acceptés, threat model, rollback et T01–T112 en environnement isolé |

Cette couverture décrit des contrôles proposés. Tant que les contrats restent
`IN_REVIEW` et leurs tests non exécutés, elle ne réduit pas à elle seule la
probabilité ou l'impact des risques.
