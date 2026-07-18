# Références officielles Roblox

| Champ | Valeur |
| --- | --- |
| ID | `REF-ROBLOX-001` |
| Classe | `REFERENCE` |
| Cycle de vie | `ACTIVE` |
| Propriétaire | Équipe de développement |
| Dernière vérification | 2026-07-15 |
| Revue suivante | Avant décision d'API, sécurité, données, conformité, monétisation ou publication |

Ce registre associe une source primaire à l'affirmation qu'elle peut soutenir.
Il ne transforme pas une recommandation Roblox en preuve joueur. Les politiques
et API sont revalidées au moment de leur utilisation.

## Produit, discovery et audience

| Source | Soutient |
| --- | --- |
| [Discovery](https://create.roblox.com/docs/production/promotion/discovery) | Signaux de recommandation, personnalisation, importance de l'engagement, de la rétention, du social et de métadonnées fidèles. |
| [Design for Roblox](https://create.roblox.com/docs/production/game-design/design-for-roblox) | FTUE rapide et visuelle, touristes/locals, social, identité avatar, mobile-first et friction de chargement. |
| [Onboarding](https://create.roblox.com/docs/production/game-design/onboarding) | Conception et mesure d'une première expérience. |
| [Player invite prompts](https://create.roblox.com/docs/production/promotion/invite-prompts) | Invitations contextualisées, invitee ciblé et `LaunchData`. |

## Analytics et expérimentation

| Source | Soutient |
| --- | --- |
| [Analytics](https://create.roblox.com/docs/production/analytics) | D1 et durée de session comme premiers diagnostics ; benchmarks comparables disponibles à partir de 100 DAU. |
| [Retention](https://create.roblox.com/docs/production/analytics/retention) | Définitions D1/D7/D30 et cohortes. |
| [Engagement](https://create.roblox.com/docs/production/analytics/engagement) | Durée moyenne, rétention de première session, accès rapide au plaisir et diagnostic de sessions significatives. |
| [Event types](https://create.roblox.com/docs/production/analytics/event-types) | Événements economy, funnel et custom, validation et limites. |
| [Funnel events](https://create.roblox.com/docs/production/analytics/funnel-events) | Funnel d'onboarding, étapes, cohortes et segmentation. |
| [Custom events](https://create.roblox.com/docs/production/analytics/custom-events) | Événements métier serveur, champs numériques et limites applicables à l'instrumentation des slices. |
| [Experiments](https://create.roblox.com/docs/production/experiments) | A/B tests causaux, MDE, significativité et prudence sous environ 1 000 DAU. |
| [Experience configs](https://create.roblox.com/docs/production/configs) | Valeurs serveur modifiables sans republier, snapshots, staging, historique et rollback. |

## Architecture, sécurité et données

| Source | Soutient |
| --- | --- |
| [Securing the client-server boundary](https://create.roblox.com/docs/scripting/security/client-server-boundary) | Validation de type, valeur, contexte, permission et fréquence des requêtes client. |
| [Remote events and callbacks](https://create.roblox.com/docs/scripting/events/remote) | Communication client-serveur, sens des remotes et distinction entre événements fiables et non fiables. |
| [Data stores](https://create.roblox.com/docs/cloud-services/data-stores) | Persistance entre sessions, accès serveur, échecs réseau et danger d'utiliser Studio contre les données live. |
| [Data store best practices](https://create.roblox.com/docs/cloud-services/data-stores/best-practices) | Organisation, cohérence d'objets et versionnement. |
| [Data store limits](https://create.roblox.com/docs/cloud-services/data-stores/error-codes-and-limits) | Throttling, files bornées et requêtes rejetées. |
| [Data store versioning, listing, and caching](https://create.roblox.com/docs/cloud-services/data-stores/versioning-listing-and-caching) | Backups horaires, expiration des versions écrasées, listing, récupération et comportement du cache. |
| [DataStore request budgets](https://create.roblox.com/docs/reference/engine/classes/DataStoreService/GetRequestBudgetForRequestType) | Lecture du budget disponible par type de requête avant d'émettre une opération. |
| [Data Stores Manager](https://create.roblox.com/docs/cloud-services/data-stores/data-stores-manager) | Inspection et opérations administratives sur les données via Creator Hub. |
| [Open Cloud data stores](https://create.roblox.com/docs/cloud/guides/data-stores) | Accès externe sous scopes explicites pour support, migration et procédures opérateur. |

## Appareils, UI et performance

| Source | Soutient |
| --- | --- |
| [Input Action System](https://create.roblox.com/docs/input/input-action-system) | Actions et bindings cross-platform. |
| [Studio testing modes](https://create.roblox.com/docs/studio/testing-modes) | Différences entre modes de test et preuves multi-client/serveur dans Studio. |
| [Performance optimization](https://create.roblox.com/docs/performance-optimization) | Frame time, mémoire, chargement et cycle mesurer/améliorer/surveiller. |
| [Design for performance](https://create.roblox.com/docs/performance-optimization/design) | Conception pour appareils faibles et limites de l'émulateur Studio. |
| [Test on hardware](https://create.roblox.com/docs/performance-optimization/test-on-hardware) | Appareils réels, throttling thermique et conditions réseau. |
| [MicroProfiler](https://create.roblox.com/docs/performance-optimization/microprofiler) | Frame times, spikes et captures client/Studio pour diagnostiquer les coûts. |
| [On-screen UI containers](https://create.roblox.com/docs/ui/on-screen-containers) | Insets et zones sûres pour UI interactive. |

## LiveOps, économie et conformité

| Source | Soutient |
| --- | --- |
| [LiveOps essentials](https://create.roblox.com/docs/production/game-design/liveops-essentials) | Cadence, mises à jour majeures, QoL, correctifs et capacité réelle de l'équipe. |
| [LiveOps planning](https://create.roblox.com/docs/production/game-design/liveops-planning) | Action joueur, KPI, monitoring et comparaison avant/après événement. |
| [Monetization](https://create.roblox.com/docs/production/monetization) | Pratiques honnêtes, restrictions par utilisateur et absence de fausse urgence. |
| [Paid random items](https://create.roblox.com/docs/production/monetization/paid-random-items) | Probabilités numériques, résultats possibles et restrictions `PolicyService`. |
| [Content maturity and compliance](https://create.roblox.com/docs/production/promotion/content-maturity) | Questionnaire basé sur le contenu le plus mature réellement accessible. |
| [Localization](https://create.roblox.com/docs/production/localization) | Traduction automatique, tables et contrôle manuel. |

## Recherche générale

Le GDD cite aussi la théorie de l'autodétermination. La source primaire utilisée
est Ryan et Deci, 2000, [Self-Determination Theory and the Facilitation of
Intrinsic Motivation, Social Development, and Well-Being](https://www.selfdeterminationtheory.org/SDT/documents/2000_RyanDeci_SDT.pdf),
DOI `10.1037/0003-066X.55.1.68`. Elle soutient le cadre autonomie, compétence et
relation ; elle ne prouve pas directement la rétention de Roblox Top 1.

La doctrine de rétention cite aussi deux sources primaires pour des effets
circonscrits : Kivetz, Urminsky et Zheng (2006),
[The Goal-Gradient Hypothesis Resurrected](https://home.uchicago.edu/ourminsky/Goal-Gradient_Illusionary_Goal_Progress.pdf),
et Loewenstein (1994),
[The Psychology of Curiosity](https://www.cmu.edu/dietrich/sds/docs/loewenstein/PsychofCuriosity.pdf).
Elles soutiennent respectivement des observations sur la proximité perçue d'un
objectif et l'information gap ; elles ne prouvent ni un effet universel ni la
rétention de ce jeu.

La frontière de bien-être utilise la définition institutionnelle du
[trouble du jeu vidéo par l'OMS](https://www.who.int/news-room/questions-and-answers/item/addictive-behaviours-gaming-disorder).
Elle sert à définir un résultat à éviter, pas à diagnostiquer des joueurs.

## Discipline d'usage

Pour chaque décision externe : noter la source, la date consultée, la phrase
supportée et ce qui reste une inférence du projet. Archiver une copie uniquement
si la licence et le besoin l'autorisent ; sinon conserver le lien et la décision
dans un ADR. Ne jamais citer une page de résultat de recherche ou un marqueur de
conversation interne.
