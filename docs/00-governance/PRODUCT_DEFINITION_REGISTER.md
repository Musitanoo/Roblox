# Registre global de définition du produit

| Champ | Valeur |
| --- | --- |
| ID | `GOV-REGISTER-002` |
| Classe | `REFERENCE` |
| Cycle de vie | `ACTIVE` |
| Version | 1.0.0 |
| Propriétaire | Founder |
| Mainteneurs | Product, Engineering, Art |
| Scope | Tout Roblox Top 1, de la preuve prototype au lancement public |
| Sources | GDD v1.0.4, roadmap, risques, contrats de slices et paquet artistique |
| Dernière revue | 2026-07-18 |
| Revue suivante | Gate, décision de scope, nouveau contrat, preuve ou rejet d'un système |

## Objet

Ce registre répond à une question unique :

> Qu'est-ce qui reste encore à définir, décider, accepter, implémenter ou
> prouver avant que la vision complète du jeu puisse devenir un produit
> exploitable ?

Il est exhaustif par rapport au corpus connu à sa date de revue. Toute nouvelle
feature, famille de contenu, dépendance ou obligation doit être ajoutée ici
avant son implémentation si elle n'est pas déjà couverte.

Ce document n'est pas un contrat d'implémentation. Enregistrer une possibilité
ne l'autorise pas. La [roadmap](ROADMAP_AND_STAGE_GATES.md) décide quand un
risque peut être ouvert ; le contrat dédié décide ensuite quoi livrer.

## Axes de statut

La maturité de définition, l'implémentation et la preuve sont indépendantes.

### Maturité de définition

| État | Sens |
| --- | --- |
| `DEFINED_ACCEPTED` | Le scope courant possède un contrat accepté suffisamment précis. |
| `SPECIFIED_IN_REVIEW` | Une proposition détaillée existe, mais n'est pas autoritaire. |
| `OPEN` | Une ou plusieurs décisions nécessaires ne possèdent pas encore de contrat suffisant. |
| `DEFERRED_BY_GATE` | Le sujet est volontairement non détaillé tant que son gate est fermé. |
| `OPTIONAL_DECISION` | Le projet doit d'abord décider si le système existera. |
| `REJECTED` | Le système a été explicitement écarté avec une raison enregistrée. |

### Implémentation

`NOT_STARTED`, `PARTIAL`, `IMPLEMENTED` ou `NOT_APPLICABLE`.

### Preuve

`PASS`, `FAIL`, `PARTIAL`, `BLOCKED` ou `UNKNOWN`, selon `AGENTS.md`.

Un domaine peut donc être `DEFINED_ACCEPTED / NOT_STARTED / UNKNOWN`. Une
spécification parfaite ne prouve pas son implémentation.

## Règle de fermeture

Un domaine ou élément passe à `DEFINED_ACCEPTED` seulement si :

1. son objectif joueur ou opérateur est explicite ;
2. scope, hors scope et invariants sont fermés ;
3. valeurs ajustables et bornes sont séparées du contrat ;
4. erreurs, abus, sécurité, performance et accessibilité applicables sont
   traités ;
5. critères d'acceptation et preuves attendues sont définis ;
6. compatibilité, migration et rollback existent si nécessaire ;
7. l'owner et l'approbateur sont identifiés ;
8. le gate autorise cette définition ou une dérogation explicite existe.

La fermeture de définition n'implique ni `IMPLEMENTED`, ni `PASS`.

## Carte globale

| ID | Domaine | Définition actuelle | Implémentation | Preuve | Qualificatif / portée | Gate principal |
| --- | --- | --- | --- | --- | --- | --- |
| `PD-01` | Preuve fondamentale du produit | `OPEN` | `PARTIAL` | `UNKNOWN` | Panel G3 renoncé par ADR-0002 ; risque accepté, preuve absente | G3 waived |
| `PD-02` | Action directe du joueur | `SPECIFIED_IN_REVIEW` | `NOT_STARTED` | `UNKNOWN` | Prochaine décision admissible ; acceptation du contrat requise | Après ADR-0002 |
| `PD-03` | Bestiaire | `OPEN` | `PARTIAL` | `UNKNOWN` | Catalogue partiel | G3 puis slices |
| `PD-04` | Horde adaptative | `DEFERRED_BY_GATE` | `NOT_STARTED` | `UNKNOWN` | Après `H-FAILURE-001` | Après H-FAILURE-001 |
| `PD-05` | Vagues, challenges et difficulté | `OPEN` | `PARTIAL` | `PARTIAL` | Preuve technique seulement | G3 |
| `PD-06` | Forteresse et construction complète | `OPEN` | `PARTIAL` | `PASS` | Technique, scope borné | G3 puis G4 |
| `PD-07` | Défenses et combinaisons | `OPEN` | `PARTIAL` | `UNKNOWN` | Résultat global non prouvé | G3 |
| `PD-08` | Objectif, dégâts et échec | `OPEN` | `PARTIAL` | `PARTIAL` | Preuve technique seulement | G3 |
| `PD-09` | Autopsie de défense | `OPEN` | `PARTIAL` | `UNKNOWN` | Preuve humaine absente | G3 |
| `PD-10` | Progression | `SPECIFIED_IN_REVIEW` | `NOT_STARTED` | `UNKNOWN` | — | G4 |
| `PD-11` | Persistance | `SPECIFIED_IN_REVIEW` | `NOT_STARTED` | `UNKNOWN` | — | G4 |
| `PD-12` | Expéditions | `DEFERRED_BY_GATE` | `NOT_STARTED` | `UNKNOWN` | — | Après G3/G4 |
| `PD-13` | Régions et biomes | `OPEN` | `PARTIAL` | `UNKNOWN` | Implémentation artistique partielle ; gameplay non prouvé | Après G3 |
| `PD-14` | Coopération synchrone | `DEFERRED_BY_GATE` | `PARTIAL` | `UNKNOWN` | Technique locale seulement ; produit non prouvé | G5 |
| `PD-15` | Social asynchrone | `DEFERRED_BY_GATE` | `NOT_STARTED` | `UNKNOWN` | — | G5 |
| `PD-16` | FTUE et onboarding | `OPEN` | `PARTIAL` | `UNKNOWN` | Preuve humaine absente | G3 |
| `PD-17` | UI, UX et accessibilité | `OPEN` | `PARTIAL` | `UNKNOWN` | Preuve multi-appareils absente | G2/G3/G9 |
| `PD-18` | Direction artistique et contenu visuel | `OPEN` | `PARTIAL` | `PARTIAL` | Scope hors constitution sélectionnée encore ouvert | Gates art + G9 |
| `PD-19` | Audio | `OPEN` | `NOT_STARTED` | `UNKNOWN` | Résultat global non prouvé | Slice concernée |
| `PD-20` | Économie | `DEFERRED_BY_GATE` | `NOT_STARTED` | `UNKNOWN` | — | G7 |
| `PD-21` | Trading | `OPTIONAL_DECISION` | `NOT_STARTED` | `UNKNOWN` | — | G7 séparé |
| `PD-22` | Monétisation | `DEFERRED_BY_GATE` | `NOT_STARTED` | `UNKNOWN` | — | G7 |
| `PD-23` | Analytics et expérimentation | `SPECIFIED_IN_REVIEW` | `NOT_STARTED` | `UNKNOWN` | Catalogue Analytics encore `DRAFT` | G6 |
| `PD-24` | Performance et architecture de scale | `SPECIFIED_IN_REVIEW` | `PARTIAL` | `UNKNOWN` | Résultat global non prouvé | G2/G9 |
| `PD-25` | Sécurité et anti-abus | `OPEN` | `PARTIAL` | `PARTIAL` | Fermeture exigée par feature client-triggerable | Tous gates |
| `PD-26` | LiveOps | `DEFERRED_BY_GATE` | `NOT_STARTED` | `UNKNOWN` | — | G8 |
| `PD-27` | Publication et exploitation | `DEFERRED_BY_GATE` | `PARTIAL` | `UNKNOWN` | Tooling partiel ; production non prouvée | G9 |
| `PD-28` | Marque et commercialisation | `OPEN` | `PARTIAL` | `UNKNOWN` | Direction artistique partielle ; marché non prouvé | G3 puis G9 |

## Priorité de travail

### `P0 — maintenant`

- `PD-02` : accepter, réduire ou rejeter Action 0.4.1, puis n'autoriser qu'une
  sous-tranche réversible ;
- `PD-05`, `PD-08`, `PD-09`, `PD-16` : préserver la lisibilité de
  comprendre → modifier → relancer malgré la preuve humaine absente ;
- `PD-03` et `PD-07` : seulement les ennemis et défenses nécessaires à la
  sous-tranche active ;
- `PD-17`, `PD-24`, `PD-25` : confort mobile, performance et sécurité du scope
  techniquement testé.

### `P1 — après signal technique Action suffisant`

- consolidation du bestiaire, des challenges et de l'autopsie ;
- décision d'expérimentation `H-HORDE-001` ;
- définition minimale de progression/persistance pour G4.

### `P2 — gates G4 à G6`

- progression, persistance, expéditions ;
- coopération et social ;
- analytics et expérimentation représentative.

### `P3 — gates G7 à G9`

- économie, éventuel trading et monétisation ;
- LiveOps ;
- exploitation, scale, conformité et lancement ;
- commercialisation fondée sur des capacités réellement prouvées.

---

## `PD-01` — Preuve fondamentale du produit

### PD-01 — Déjà défini

- résultat recherché : comprendre une faiblesse, modifier la forteresse et
  relancer volontairement ;
- distinction `PASS TECHNIQUE` / `PASS PRODUIT` ;
- G3 exige normalement des joueurs représentatifs non briefés ;
- ADR-0002 renonce à cette exécution comme condition de séquencement interne,
  sans fermer la preuve.

### PD-01 — Reste à définir ou produire

- protocole de recherche accepté ;
- profils, nombre minimal et recrutement des testeurs ;
- scénario, durée, appareil et ordre des tâches ;
- consignes écrites et interdiction d'aide orale ;
- événements observés et grille de codage ;
- seuils de compréhension, modification et rematch ;
- verbatims et observations anonymisés ;
- critères de confusion, frustration et abandon ;
- règles d'arrêt anticipé ;
- traitement des données manquantes ;
- décisions possibles : continuer, corriger, réduire ou pivoter ;
- rapport de recherche et conservation des données brutes ;
- procédure de nouvelle exécution après modification.

### PD-01 — Fermeture

`PASS PRODUIT` seulement après un panel non briefé conforme. Le founder seul,
un agent, un test automatisé ou une capture ne peuvent fermer ce domaine.
ADR-0002 accepte que ce domaine reste ouvert et `UNKNOWN` pendant le
développement interne.

---

## `PD-02` — Action directe du joueur

Source candidate :
[ACTION_LOOP_0_4.md](../ACTION_LOOP_0_4.md).

### PD-02 — Reste à accepter, définir ou éprouver

- rôle exact du combat manuel face aux défenses automatiques ;
- actions retenues : Fight, Repair, Rescue et éventuels gadgets ;
- modèle de visée tactile, clavier/souris et manette ;
- arsenal minimal et critères de sélection ;
- dégâts, cadence, portée, dispersion, munitions et rechargement ;
- targeting, hit validation et feedback de hit ;
- réparation : cible, canalisation, coût, interruption et résultat ;
- sauvetage/réanimation : conditions, durée, immunité et échec ;
- priorité lorsque plusieurs interactions se chevauchent ;
- animation cancel, cooldown, recovery et changement d'outil ;
- mouvement pendant l'action ;
- caméra, aim assist et limites d'assistance ;
- contribution mesurable sans rendre le joueur obligatoire partout ;
- anti-spam, rate limits, replay, ordre et idempotence ;
- comportement à haute latence et avec deux clients ;
- critères de plaisir, lisibilité, maîtrise et fatigue mobile.

### PD-02 — Fermeture

Contrat 0.4.1 accepté ou remplacé, tests techniques applicables passés, puis
preuve humaine séparée.

---

## `PD-03` — Bestiaire

Le GDD définit des rôles, pas encore tous leurs contrats exécutables. Seul
`enemy_standard` possède un canon visuel Salvaged Frontier détaillé, encore
`CANDIDATE`.

### PD-03 — Catalogue à décider

- envahisseurs : rôdeur, coureur, essaim, blindé ;
- destructeurs : brute, grimpeur, creuseur, pousseur ;
- saboteurs : coupe-circuit, brouilleur, voleur de munitions,
  désactivateur de piège ;
- soutiens : hurleur, gardien, soigneur, porteur ;
- manipulateurs : ravisseur, leurreur, contaminateur, faux éclaireur ;
- éclaireur et boss ;
- liste réellement nécessaire au vertical slice et au lancement.

### PD-03 — Pour chaque rôle retenu

- problème tactique et promesse d'une seconde ;
- cible et priorité ;
- navigation, vitesse, rayon et franchissement ;
- santé, dégâts, portée, cadence et résistances ;
- faiblesse, fenêtre de contre et coût d'erreur ;
- hitbox, collision et network ownership ;
- télégraphe silhouette/son/animation/VFX ;
- machine d'états et interruptions ;
- interaction avec murs, pièges, joueurs, objectif et autres ennemis ;
- spawn, despawn, pooling et limite simultanée ;
- récompense et éligibilité ;
- variantes de difficulté autorisées ;
- comportement solo et groupe ;
- déterminisme, seed et reproduction de bug ;
- budget CPU, pathfinding, physique, réseau, mémoire et rendu ;
- canon visuel, composants, matériaux, états et interdictions ;
- animation, audio, VFX et accessibilité ;
- preuve 1/30/100 et appareil mobile.

### PD-03 — Fermeture

Chaque ennemi possède un contrat gameplay, un canon visuel applicable et une
preuve runtime. Une recoloration ou davantage de santé ne crée pas un nouveau
rôle valide.

---

## `PD-04` — Horde adaptative

Hypothèse : `H-HORDE-001 / The Horde Learns`.

### PD-04 — Reste à définir après autorisation

- informations réellement observables par la horde ;
- données interdites et séparation serveur ;
- rôle et limites des éclaireurs ;
- mesure des dépendances de la base ;
- scores de vulnérabilité et bornes ;
- budget d'adaptation par challenge/difficulté ;
- fraction maximale d'ennemis remplacée ;
- changement d'axe et création de crise ;
- synchronisation de rôles ;
- mémoire intra-challenge et inter-challenges ;
- oubli progressif et variation régionale ;
- protection contre le contre parfait ;
- télégraphie avant application ;
- reproductibilité par seed ;
- explication factuelle dans l'autopsie ;
- détection de stratégie dominante ;
- coûts pathfinding/CPU ;
- critères humains : intelligent, compréhensible, non tricheur ;
- kill criteria si l'adaptation réduit confiance ou rematch.

### PD-04 — Fermeture

Ne pas détailler ni implémenter avant un signal suffisant sur
`H-FAILURE-001`. Une adaptation secrète ou un contre parfait est interdite.

---

## `PD-05` — Vagues, challenges et difficulté

### PD-05 — Reste à définir

- modèle de budget de vague ;
- composition, ordre et cadence ;
- nombre maximal d'ennemis actifs ;
- points de spawn, axes et routes ;
- structure dramatique et mini-crises ;
- temps de préparation et d'annonce ;
- conditions victoire, échec, abandon et timeout ;
- comportement lorsque l'objectif est critique ou détruit ;
- tutoriel, standard, gate, endurance et difficultés ;
- durée réelle de chaque format ;
- scaling solo à quatre joueurs ;
- comeback et récupération ;
- anti-stall, anti-kiting et anti-safe-zone ;
- seeds et reproduction exacte ;
- règles de boss ;
- récompense et multiplicateurs bornés ;
- rematch et restauration ;
- lisibilité de la prochaine menace ;
- difficulté issue de nouvelles situations plutôt que de santé brute ;
- mesures de fairness, frustration et diversité stratégique.

### PD-05 — Fermeture

Une matrice challenge × difficulté × taille de groupe est acceptée et testée
sur le scope nécessaire. Les valeurs de tuning restent en `CONFIG`.

---

## `PD-06` — Forteresse et construction complète

La grille, les snapshots et le rematch possèdent une preuve technique bornée.
Le système cible complet reste ouvert.

### PD-06 — Reste à définir

- catalogue de pièces : murs, portes, sols, rampes, supports et variantes ;
- dimensions, pivots, rotations et snapping ;
- construction verticale et niveaux ;
- règles structurelles et supports ;
- validation de placement et overlap ;
- routes ennemies et interdiction de blocage impossible ;
- limites de hauteur, surface, pièces et coût ;
- suppression, déplacement, remboursement et undo ;
- propriété et permissions ;
- édition simultanée et conflits de révision ;
- plans, duplication, import et versionnement ;
- sélection, multi-sélection et édition mobile ;
- preview, confirmation et récupération d'erreur ;
- états endommagés, détruits et réparés ;
- collision autoritaire par état ;
- restauration après assaut ;
- compatibilité des anciennes pièces ;
- sauvegarde et migration futures ;
- budgets réseau, mémoire, rendu et validation serveur ;
- confort sur grande base et appareils faibles.

### PD-06 — Fermeture

Contrats séparés pour structure, placement, ownership et persistance lorsque
leurs gates ouvrent. Le scope actuel ne prouve pas la forteresse complète.

---

## `PD-07` — Défenses et interactions combinatoires

### PD-07 — Familles à décider

- barricade ;
- ralentisseur ;
- piège de dégâts ;
- tourelle ;
- canon manuel ;
- générateur ;
- batterie ;
- contrôle de mouvement ;
- soutien et réparation.

### PD-07 — Pour chaque défense retenue

- fonction, footprint, orientation et socket ;
- coût de construction et éventuelle énergie ;
- targeting, portée, cadence, effet et priorité ;
- projectile/raycast et autorité serveur ;
- états, réparation, désactivation et destruction ;
- upgrade/sidegrade et limite de puissance ;
- synergies et contres ;
- nombre maximal et stacking ;
- collision et navigation ;
- sécurité, spam et double-spend ;
- comportement sans propriétaire ou après déconnexion ;
- analytics futures ;
- budget CPU, réseau, VFX et rendu ;
- canon visuel Salvaged Frontier et preuve mobile ;
- interaction avec tous les rôles ennemis nécessaires.

### PD-07 — Règles globales encore ouvertes

- modèle d'énergie ;
- modèle de munitions ;
- ordre de targeting ;
- friendly fire éventuel ;
- limites empêchant une combinaison universelle ;
- matrice de compatibilité des effets ;
- résolution des ralentissements, buffs et debuffs ;
- lisibilité de 30/100 défenses simultanées.

---

## `PD-08` — Objectif, dégâts et échec

### PD-08 — Reste à définir

- santé, phases et seuils de l'Objective Core ;
- bouclier ou protection éventuelle ;
- règles de ciblage ennemies ;
- propagation et attribution des dégâts ;
- invulnérabilité transitoire éventuelle ;
- réparation en assaut et hors assaut ;
- signal `DAMAGED` / `CRITICAL` ;
- conséquences fonctionnelles de chaque seuil ;
- condition exacte de défaite ;
- animation et durée de la défaite ;
- restauration après challenge ;
- perte persistante maximale ;
- relation à l'énergie et aux autres systèmes ;
- contributions coopératives ;
- HUD, world cues, audio et accessibilité ;
- idempotence des dégâts/réparations ;
- protection contre double application et valeurs impossibles ;
- comportement en reconnexion ou fermeture serveur.

### PD-08 — Fermeture

Le spectacle de destruction reste compatible avec une perte limitée,
compréhensible et récupérable.

---

## `PD-09` — Autopsie de défense

### PD-09 — Reste à définir ou valider

- événement causal et première brèche ;
- données collectées et durée de conservation ;
- attribution ennemi/défense/joueur ;
- timeline et replay accéléré ;
- heatmaps, routes, axes et concentrations ;
- dégâts, désactivations, surcharges et temps critiques ;
- affichage de faits distinct des hypothèses ;
- recommandation facultative, justifiée et non prescriptive ;
- mise en évidence de la faiblesse observée ;
- passage direct à la modification ;
- comparaison avant/après ;
- mesure du changement réellement effectué ;
- mesure du rematch volontaire ;
- traitement d'une bataille sans cause unique ;
- traitement de données incomplètes ;
- interface mobile et temps de lecture ;
- export de preuve pour QA sans données personnelles ;
- seuils humains prouvant la compréhension.

### PD-09 — Fermeture

G3 doit montrer que l'autopsie produit effectivement compréhension,
modification pertinente et volonté de retester.

---

## `PD-10` — Progression

Source candidate :
[PROGRESSION_LOOP_0_5.md](../PROGRESSION_LOOP_0_5.md).

### PD-10 — Reste à accepter, définir ou prouver

- raison précise de retour nécessitant une progression ;
- séparation maîtrise, recherche et identité ;
- catalogue initial de plans/sidegrades ;
- conditions et ordre de déblocage ;
- ressources temporaires et persistantes ;
- coûts, récompenses et plafonds ;
- progression de difficulté et de région ;
- puissance verticale maximale ;
- compensation et duplicate handling ;
- respec, remboursement et rollback ;
- progression solo/groupe ;
- catch-up sans invalider la maîtrise ;
- prévention du grind et de la stratégie dominante ;
- transactions serveur et idempotence ;
- anti-double-claim ;
- migration BuildPlan et compatibilité ;
- UX et feedback ;
- critères montrant davantage de possibilités, pas seulement davantage de
  statistiques.

### PD-10 — Fermeture

G4 ou dérogation explicite, contrat accepté, tests transactionnels et preuve
que la progression améliore une décision réelle.

---

## `PD-11` — Persistance

Sources candidates :
[PERSISTENCE_LOOP_0_6.md](../PERSISTENCE_LOOP_0_6.md) et
[runbook](../PERSISTENCE_OPERATIONS_RUNBOOK_0_6.md).

### PD-11 — Reste à accepter, définir ou prouver

- schéma canonique du profil ;
- séparation Data Test / staging / production ;
- version de schéma ;
- migrations forward et rollback ;
- données sauvegardées et volontairement non sauvegardées ;
- save/load, autosave et shutdown ;
- retry et backoff ;
- idempotence des mutations ;
- session lock et perte de lock ;
- conflits multi-serveurs ;
- read-only et récupération ;
- corruption, sauvegarde de secours et restauration ;
- suppression de données et demandes utilisateur ;
- quotas, budgets et réduction de writes ;
- fixtures et fault injection ;
- observabilité, alertes et support ;
- runbook répété sans données réelles ;
- threat model data ;
- confidentialité et minimisation ;
- plan de rollback testé.

### PD-11 — Fermeture

G4 ouvert, contrats acceptés et protocole de panne passé dans un univers
isolé. Aucun test ne doit utiliser les données de production.

---

## `PD-12` — Expéditions

### PD-12 — Reste à décider et définir

- valeur indispensable pour la boucle centrale ;
- format de carte fixe, modulaire ou procédural ;
- durée et structure ;
- objectifs, foreuse et extraction ;
- navigation, combat et hazards ;
- risque optionnel et information préalable ;
- victoire, échec, abandon et reconnexion ;
- récompenses et relation à la prochaine menace ;
- ressources/technologies récupérables ;
- anti-corvée et répétition ;
- difficulté solo/groupe ;
- matchmaking et ownership ;
- biomes et variantes ;
- quantité de contenu viable pour deux personnes ;
- performance, streaming et mobile ;
- réutilisation dans LiveOps future.

### PD-12 — Fermeture

Le système ne s'ouvre qu'après preuve du noyau et doit enrichir la préparation,
pas devenir un second jeu concurrent.

---

## `PD-13` — Régions et biomes

### PD-13 — Reste à définir

- nombre initial et ordre ;
- condition de déblocage ;
- règle mécanique nouvelle par région ;
- menaces et rôles ennemis associés ;
- ressources et technologie récupérable ;
- architecture et kit modulaire ;
- terrain, végétation, props et hazards ;
- météo, lighting, VFX et audio ;
- expéditions et gate/boss ;
- interaction avec la forteresse ;
- variété sans inflation de contenu ;
- budgets et streaming ;
- accessibilité des contrastes ;
- canons visuels par famille ;
- critères permettant de distinguer mécanique réelle et simple recoloration.

### PD-13 — Fermeture

La constitution Salvaged Frontier reste commune. Chaque biome ajoute une cause,
une contrainte et une opportunité gameplay, jamais seulement une palette.

---

## `PD-14` — Coopération synchrone

### PD-14 — Reste à définir

- valeur sociale précise et hypothèse G5 ;
- expérience viable en solo ;
- taille 1–4 et scaling ;
- rôles émergents ;
- propriété de la forteresse ;
- permissions construire/déplacer/supprimer/dépenser ;
- partage de ressources ;
- contribution et récompenses ;
- revive, repair et coordination ;
- communication rapide mobile ;
- late join et reconnexion ;
- déconnexion du propriétaire ;
- AFK et comportements opportunistes ;
- griefing, kick, block et signalement ;
- matchmaking et groupe privé ;
- comparaison solo/groupe ;
- anti-exploit des récompenses ;
- critères de valeur sociale réelle.

### PD-14 — Fermeture

G5 exige une coopération qui crée des possibilités et des histoires, sans
punir le solo ni transformer le groupe en simple multiplicateur de dégâts.

---

## `PD-15` — Social asynchrone et communauté

### PD-15 — Reste à décider et définir

- visites de forteresses ;
- mode lecture seule ;
- commentaires, appréciations ou absence volontaire ;
- plans partagés et copie ;
- attribution, version et compatibilité ;
- confidentialité et visibilité ;
- modération des noms et contenus ;
- défis communautaires ;
- demandes d'aide et `Answer the Call` ;
- notifications, fréquence et opt-out ;
- anti-spam et abus ;
- récompenses non exploitables ;
- statut social sain ;
- protection des mineurs et conformité ;
- support et suppression de contenu.

### PD-15 — Fermeture

G5 ouvert, permissions et griefing fermés, valeur sociale mesurée. Aucun
mécanisme ne punit l'absence ou force l'invitation.

---

## `PD-16` — FTUE et onboarding

### PD-16 — Reste à définir ou valider

- scène d'arrivée et promesse en dix secondes ;
- premier placement ;
- premier ennemi et première attaque ;
- première brèche ;
- première réparation ;
- première autopsie ;
- première modification ;
- premier rematch ;
- temps cible réel par étape ;
- instructions minimales et wording ;
- erreurs récupérables ;
- skip, reprise et replay du tutoriel ;
- onboarding clavier/manette/tactile ;
- onboarding solo et coop ;
- accessibilité ;
- funnel et événements futurs ;
- critères de compréhension sans aide ;
- abandon, confusion et correction ;
- relation entre tutoriel et vraie boucle.

### PD-16 — Fermeture

Panel non briefé conforme à G3. Une chronologie écrite ne prouve pas un FTUE
réussi.

---

## `PD-17` — UI, UX et accessibilité

### PD-17 — Surfaces à définir

- HUD préparation ;
- construction et sélection ;
- menace annoncée ;
- HUD défense ;
- objectif, énergie, munitions et cooldowns ;
- réparation, interaction et revive ;
- autopsie ;
- progression et inventaire ;
- expédition ;
- social ;
- paramètres, support et erreurs.

### PD-17 — Contrats transversaux ouverts

- navigation tactile, clavier/souris et manette ;
- safe areas, orientation, résolutions et densités ;
- tailles tactiles et prévention des mis-taps ;
- hiérarchie, focus et profondeur de menus ;
- text scaling et localisation ;
- contraste et daltonisme ;
- couleur jamais unique ;
- sous-titres et signaux non audio ;
- reduced motion, flash et caméra ;
- erreurs, confirmation et undo ;
- état loading/offline/retry ;
- cohérence iconographique ;
- test avec appareils physiques et besoins d'accessibilité.

### PD-17 — Fermeture

Chaque action centrale passe les scénarios appareil/input applicables. Le
simulateur Studio ne remplace pas le mobile physique.

---

## `PD-18` — Direction artistique et contenu visuel

### PD-18 — Déjà défini

- constitution Salvaged Frontier `CREATIVE_DIRECTION_LOCKED` ;
- grammaire, palette, matériaux et ontologie ;
- six canons d'objet sélectionnés en `CANDIDATE`.

### PD-18 — Reste à produire, définir ou verrouiller

- 17 familles de planches et signature des six objets ;
- import et preuve Studio courants ;
- appareil mobile physique ;
- canons du bestiaire retenu ;
- canons des défenses retenues ;
- architecture et kits de biomes ;
- armes, outils et gadgets ;
- avatars, rôles et équipements ;
- ressources, collectibles et props ;
- végétation et hazards ;
- UI, iconographie et signalétique ;
- animation et rigging ;
- VFX complet ;
- lighting par région ;
- cosmétique et règles de variation ;
- marketing art ;
- LOD/RenderFidelity, collisions et budgets ;
- provenance, licences et maintenance ;
- pipeline d'extension à de nouvelles familles.

### PD-18 — Fermeture

Séparer toujours :

```text
constitution créative
canon d'objet
implémentation Blender
intégration Studio
preuve mobile physique
approbation humaine
productionApproved
```

Une belle image GPT, un canon textuel ou un build Blender ne ferme pas les
gates suivants.

---

## `PD-19` — Audio

### PD-19 — Reste à définir

- identité musicale ;
- ambiance forteresse et régions ;
- signature de chaque ennemi ;
- télégraphes et attaques ;
- damage, critical et mort non gore ;
- construction, réparation et upgrade ;
- armes, défenses et objectif ;
- UI, succès, erreur, victoire et échec ;
- spatialisation et distance ;
- mixage d'une horde dense ;
- priorité, ducking et voice limits ;
- variations anti-répétition ;
- sous-titres et équivalents visuels ;
- volume, catégories et paramètres ;
- droits, provenance et pipeline ;
- budgets mémoire/streaming ;
- tests sur haut-parleurs mobiles et écouteurs.

### PD-19 — Fermeture

Chaque son possède une fonction, une priorité et un fallback perceptuel. Le son
ne porte jamais seul une information indispensable.

---

## `PD-20` — Économie

### PD-20 — Reste volontairement différé

- nécessité et nombre de monnaies ;
- sources et puits ;
- inventaire et capacités ;
- coûts, gains, plafonds et inflation ;
- récompenses challenge/expédition/social ;
- compensation et duplicate handling ;
- sinks cosmétiques ;
- transactions et atomicité ;
- anti-duplication et multi-comptes ;
- observabilité et correction ;
- équilibre gratuit ;
- relation progression/monétisation ;
- migration et rollback ;
- simulation économique et kill switches.

### PD-20 — Fermeture

G7 seulement après valeur gratuite et retour observés. Le prototype ne doit pas
construire une économie complète pour remplir le GDD.

---

## `PD-21` — Trading

### PD-21 — Décision préalable

Déterminer si le trading apporte une valeur compatible avec le jeu et la
capacité d'équipe. `Ne jamais l'ajouter` reste une décision valide.

### PD-21 — Si retenu

- objets échangeables et non échangeables ;
- ownership et valeur ;
- escrow, confirmation et annulation ;
- atomicité et idempotence ;
- double-spend, replay et conflits ;
- fraude, bots, multi-comptes et blanchiment de valeur ;
- limites, cooldown et âge ;
- historique, support et rollback ;
- modération et conformité ;
- impact sur progression et économie ;
- UX prévenant erreur et pression sociale.

### PD-21 — Fermeture

Décision G7 séparée, threat model complet et preuve anti-abus avant toute
mutation d'inventaire.

---

## `PD-22` — Monétisation

### PD-22 — Reste volontairement différé

- proposition de valeur payante ;
- catalogue et prix ;
- cosmétiques ;
- confort éventuel et limites ;
- abonnement éventuel ;
- battle pass : décision séparée ;
- produits répétables/non répétables ;
- reçus idempotents ;
- restauration et remboursements ;
- retrait ou modification d'offre ;
- régionalisation et conformité ;
- contrôles parentaux et disclosure ;
- analytics et support ;
- absence de pay-to-win ;
- absence de hasard opaque ;
- absence de FOMO destructrice ;
- tests de confiance et critères de dommage.

### PD-22 — Fermeture

G7, politiques Roblox revalidées et valeur gratuite prouvée. Aucun achat ne
répare une frustration artificiellement créée.

---

## `PD-23` — Analytics et expérimentation

Source candidate :
[ANALYTICS_EVENT_CATALOG_0_9.md](../ANALYTICS_EVENT_CATALOG_0_9.md).

### PD-23 — Reste à accepter, définir ou produire

- dictionnaire KPI ;
- séparation métriques Roblox et diagnostics `RT1_*` ;
- événements réellement nécessaires ;
- schémas, propriétés et versions ;
- session, player et experiment IDs minimisés ;
- déduplication et ordre ;
- consentement et conformité ;
- durée de conservation ;
- qualité, pertes et late events ;
- funnels onboarding, central, expédition et social ;
- cohortes et segmentation ;
- dashboards produit, erreurs et performance ;
- alertes et owners ;
- A/B testing, assignation et exposition ;
- taille d'échantillon et puissance ;
- critères d'arrêt et décisions ;
- guardrails confiance, bien-être et équité ;
- accès, export et suppression.

### PD-23 — Fermeture

G6 ouvert, catalogue accepté et validation end-to-end. Le document `DRAFT`
n'autorise aucune émission officielle.

---

## `PD-24` — Performance et architecture de scale

Source candidate :
[PERFORMANCE_BUDGETS_1_0.md](../PERFORMANCE_BUDGETS_1_0.md).

### PD-24 — Reste à définir ou mesurer

- appareils baseline et matrice cible ;
- frame time, FPS, mémoire et thermique ;
- temps de chargement et reconnexion ;
- budgets serveur, client, réseau et réplication ;
- horde maximale ;
- pathfinding et files de requêtes ;
- physique, network ownership et collisions ;
- projectiles, raycasts et tourelles ;
- VFX, transparence et audio ;
- forteresse maximale et streaming ;
- tâches, boucles, connexions et nettoyage ;
- garbage collection et memory leaks ;
- budgets DataStore et services externes ;
- charge multi-serveur ;
- profils MicroProfiler ;
- sessions soutenues ;
- dégradation contrôlée ;
- seuils d'alerte ;
- tests de charge et capacité de rollout.

### PD-24 — Fermeture

Les budgets deviennent `ACCEPTED` après mesures représentatives. « Performant »
est interdit sans appareil, charge et scénario.

---

## `PD-25` — Sécurité et anti-abus

### PD-25 — À fermer pour chaque feature client-triggerable

- type, structure, taille et profondeur ;
- nombres finis et bornés ;
- enum et string lengths ;
- ownership, permissions et progression ;
- distance et état serveur ;
- timestamps et ordre ;
- replay, duplication et idempotence ;
- rate limit et queues bornées ;
- travail bon marché avant travail coûteux ;
- prix, dégâts, récompenses et résultat calculés serveur ;
- instances et positions client non fiables ;
- erreur fail-closed sans crash ;
- logs sans secret ni données inutiles.

### PD-25 — Threat models spécifiques encore nécessaires

- Action 0.4.1 ;
- progression et récompenses ;
- persistance et recovery ;
- social, permissions et griefing ;
- économie et reçus ;
- trading si retenu ;
- analytics poisoning ;
- publication Cloud et credentials ;
- plans partagés et contenu utilisateur ;
- opérations d'administration/support.

### PD-25 — Fermeture

Chaque contrat applicable contient son threat model, ses tests adversariaux et
sa récupération. La sécurité globale ne peut pas être déclarée une fois pour
toutes.

---

## `PD-26` — LiveOps

### PD-26 — Reste volontairement différé

- capacité réelle d'une équipe de deux ;
- cadence ;
- types d'événements ;
- templates et briques réutilisables ;
- configuration, version et rollout ;
- localisation ;
- début, fin et nettoyage ;
- fallback et kill switch ;
- récompenses ;
- KPI et guardrails ;
- compatibilité des versions ;
- support et incidents ;
- réutilisation/retour du contenu ;
- calendrier sans surcharge ;
- rétrospective ;
- absence de FOMO destructrice.

### PD-26 — Fermeture

G8 après boucle et instrumentation stables. La cadence est mesurée, pas
souhaitée.

---

## `PD-27` — Publication et exploitation

### PD-27 — Reste à définir avant G9

- environnements dev, staging et production ;
- univers, places et ownership ;
- permissions équipe et séparation des rôles ;
- secrets et rotation ;
- publication code/assets/config ;
- stratégie de version et migration ;
- rollout progressif ;
- critères go/no-go ;
- rollback et sauvegardes ;
- monitoring, logs, métriques et alertes ;
- réponse incident et responsabilités ;
- récupération après panne ;
- support joueur ;
- modération ;
- confidentialité, âge et conformité ;
- localisation ;
- matrice appareils ;
- charge et capacité ;
- publication Roblox et validation post-release ;
- maintenance et dépréciation ;
- communication d'incident.

### PD-27 — Fermeture

G9 avec preuves représentatives. Les outils staging ou dry-run ne prouvent pas
une exploitation de production.

---

## `PD-28` — Marque et commercialisation

### PD-28 — Reste à définir

- nom commercial ;
- logo et système de marque ;
- icône Roblox ;
- thumbnails ;
- trailer ;
- screenshots ;
- description de page ;
- promesse publique finale ;
- mots-clés et positionnement ;
- représentation honnête de la horde adaptative ;
- distinction commerciale ;
- marketing art Salvaged Frontier ;
- cohérence entre publicité et première minute ;
- localisation marketing ;
- stratégie de lancement ;
- creators, communauté et outreach ;
- tests de page et conversion ;
- règles interdisant les claims non prouvés.

### PD-28 — Fermeture

Les claims marketing ne dépassent jamais les capacités observées. Avant preuve
de `H-HORDE-001`, « la horde apprend » reste une ambition ou une hypothèse
clairement qualifiée, pas une promesse mensongère.

---

## Maintenance du registre

### Ajouter un élément

Ajouter ou étendre un domaine si une décision nouvelle :

- modifie le résultat joueur ;
- introduit un risque de sécurité, donnée, économie ou conformité ;
- crée une famille de contenu ;
- nécessite un owner ou une preuve distincte ;
- ne rentre pas sans ambiguïté dans un contrat existant.

### Fermer un élément

Enregistrer :

- décision ;
- contrat ou ADR ;
- version ;
- owner et approbateur ;
- preuve attendue ;
- gate ;
- liens de migration/rollback ;
- éléments rejetés ou remplacés.

### Ne pas faire

- créer immédiatement 28 spécifications détaillées ;
- confondre « enregistré » et « autorisé » ;
- convertir `DEFERRED_BY_GATE` en backlog actif ;
- faire passer une proposition GDD pour une obligation de lancement ;
- annoncer `PASS` à partir d'une documentation complète ;
- supprimer une option rejetée sans conserver la raison.

## Prochaine décision autorisée

Le registre n'ouvre pas un nouveau système. Après ADR-0002, la prochaine
décision autorisée à plus forte valeur est d'accepter, réduire ou rejeter le
contrat Action 0.4.1. La preuve humaine comprendre → modifier → relancer reste
ouverte et `UNKNOWN`.
