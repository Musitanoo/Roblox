# Roblox Top 1 — Game Design Document v1.0.4

| Champ | Valeur |
| --- | --- |
| ID | `PRODUCT-GDD-001` |
| Classe | `CONTRACT` de vision et de conception |
| Cycle de vie | `ACCEPTED` |
| Version | 1.0.4 |
| Propriétaire / approbateur | Founder |
| Scope | Vision produit, systèmes cibles et garde-fous ; 1 à 4 joueurs, mobile-first |
| Remplace | Version 1.0.3 du même document |
| Dernière revue | 2026-07-18 |
| Revue suivante | Décision produit, preuve invalidante ou acceptation d'un nouveau contrat de slice |
| Nom commercial | À définir |
| North Star | Première expérience Roblox mondiale par CCU moyen sur 30 jours |
| Preuve de rétention | `UNKNOWN` jusqu'aux playtests et cohortes réelles |

## Journal de révision

- `1.0.4` — ADR-0002 renonce au gate participant G3 pour le séquencement
  interne ; la preuve joueur reste `UNKNOWN` et Action 0.4.1 demeure
  `IN_REVIEW` jusqu'à son acceptation explicite.
- `1.0.3` — remplacement de la promesse publique non prouvée « la horde
  apprend » par la boucle effectivement testée ; `H-HORDE-001` reste une
  variante marketing conditionnelle jusqu'à sa validation.
- `1.0.2` — ajout du registre global de définition qui inventorie toutes les
  décisions encore ouvertes sans autoriser les gates futurs.
- `1.0.1` — intégration des contrats candidats Action 0.4.1, Progression 0.5.1
  et Persistence 0.6.1 ; aucune extension de scope runtime.
- `1.0.0` — vision founder acceptée pour préproduction et vertical slices.

Les principes réellement immuables sont extraits dans la
[Constitution produit](docs/00-governance/PRODUCT_CONSTITUTION.md). Les systèmes,
valeurs et seuils non observés de ce GDD restent des hypothèses à valider ; le
statut `ACCEPTED` autorise leur test, pas une revendication de résultat joueur.
La [Doctrine d’innovation et de rétention durable](docs/PRODUCT_INNOVATION_AND_RETENTION_DOCTRINE.md)
accepte une méthode de mesure et d’expérimentation. Ses signatures, motivations,
horloges et effets comportementaux restent des hypothèses nommées ; elle sépare
les métriques Roblox officielles des diagnostics internes `RT1_*`.

---

# 0. Avertissement de vérité

Ce document est conçu pour maximiser la probabilité de rétention volontaire, de divertissement durable et de compatibilité avec les signaux de distribution Roblox. Il ne peut pas garantir une « rétention parfaite ». Roblox décrit notamment des signaux de recommandation liés au play-through qualifié, à la rétention, à l'engagement, à la monétisation et au jeu entre amis. Le système de recommandation personnalise ensuite la sélection et le classement des expériences. ([Roblox — Discovery](https://create.roblox.com/docs/production/promotion/discovery))

La rétention ne sera considérée comme prouvée que lorsque de vrais joueurs :

1. comprennent la promesse ;
2. atteignent rapidement le plaisir ;
3. terminent une première boucle ;
4. modifient leur base après avoir compris une faiblesse ;
5. relancent volontairement ;
6. reviennent lors des jours suivants ;
7. invitent ou rejoignent réellement des amis.

## 0.1 Carte d'application actuelle

Le GDD décrit la destination produit. Les contrats de slice décrivent un
sous-ensemble implémentable et testable ; ils ne deviennent autoritaires dans
leur scope qu'après acceptation ou dérogation explicite conforme à la
[roadmap](docs/00-governance/ROADMAP_AND_STAGE_GATES.md).

| Niveau | Document | Autorité actuelle | Relation au GDD |
| --- | --- | --- | --- |
| Baseline exécutable | [Build Loop 0.3](docs/BUILD_LOOP_0_3.md) | `ACCEPTED`, `PASS TECHNIQUE` | Construction sur grille, snapshot et rematch |
| Action | [Action Loop 0.4.1](docs/ACTION_LOOP_0_4.md) | `IN_REVIEW` | Sous-ensemble Fight, Repair, Rescue des sections 11 et 14 |
| Progression | [Progression Loop 0.5.1](docs/PROGRESSION_LOOP_0_5.md) | `IN_REVIEW` | Sous-ensemble temporaire et horizontal de la section 17 |
| Persistence | [Persistence Loop 0.6.1](docs/PERSISTENCE_LOOP_0_6.md) | `IN_REVIEW` | Profil versionné et récupérable pour les sections 8 et 17 |

Cette carte est un routage documentaire, pas une preuve d'implémentation. G3
reste `UNKNOWN`, mais son exécution participant est `WAIVED_BY_FOUNDER` pour le
séquencement interne par ADR-0002. Action 0.4.1 reste `IN_REVIEW` et G4 reste
fermé.

Les décisions non fermées de l'ensemble du GDD sont inventoriées dans le
[registre global de définition](docs/00-governance/PRODUCT_DEFINITION_REGISTER.md).
Une entrée `OPEN`, `DEFERRED_BY_GATE` ou `OPTIONAL_DECISION` conserve une
question sans transformer la vision en scope autorisé.

---

# 1. Vision du jeu

## 1.1 Définition en une phrase

Un jeu Roblox PvE coopératif dans lequel chaque joueur construit librement une forteresse persistante, explore des territoires pour obtenir des ressources et technologies, puis déclenche volontairement des invasions de difficulté croissante afin de tester, comprendre et perfectionner sa défense avec ses amis.

## 1.2 Fantasme principal

> **Je possède une forteresse réellement personnelle. Je peux comprendre pourquoi elle fonctionne, découvrir ses défauts et inventer une meilleure solution.**

Le joueur n’est pas seulement un tireur. Il est simultanément :

- architecte ;
- ingénieur ;
- combattant ;
- explorateur ;
- collectionneur ;
- analyste ;
- allié utile ;
- propriétaire d’un lieu reconnaissable.

## 1.3 Promesse publique compatible avec l'état prouvé

> **Construis ta forteresse. Comprends sa chute. Prouve qu’elle peut survivre.**

La variante historique « La horde apprend » reste la promesse candidate de
`H-HORDE-001`. Elle ne doit pas être publiée comme une capacité du jeu tant que
l'adaptation limitée, lisible et contrable de la horde n'a pas été implémentée
et validée par le protocole prévu.

## 1.4 Boucle émotionnelle

> **J’ai construit → cela a presque fonctionné → j’ai compris → je veux recommencer.**

Cette boucle est prioritaire sur toute autre motivation. Les points, le loot et les mondes ne doivent jamais la remplacer.

---

# 2. Positionnement

## 2.1 Ce que le jeu est

- un jeu de forteresse persistante ;
- un jeu de défense active ;
- un jeu de maîtrise et d’expérimentation ;
- un jeu coopératif utile ;
- un jeu de progression horizontale ;
- un jeu LiveOps fondé sur des systèmes combinatoires ;
- un jeu accessible immédiatement, mais profond à maîtriser.

## 2.2 Ce que le jeu n’est pas

- un tower defense à route fixe ;
- un clicker ;
- un simulateur de nombres ;
- un idle game ;
- un shooter où la construction est décorative ;
- un open world gigantesque au lancement ;
- une copie directe de Fortnite: Save the World ;
- un jeu où les investissements sont détruits en permanence ;
- un jeu pay-to-win ;
- un jeu dont l’endgame est seulement « davantage de santé et de dégâts ».

---

# 3. Public cible

## 3.1 Cœur de cible

Joueurs Roblox recherchant :

- construction simple ;
- progression visible ;
- action coopérative ;
- collection ;
- stratégie accessible ;
- moments partageables ;
- expérience jouable seul mais meilleure avec des amis.

## 3.2 Double accessibilité

Le jeu doit satisfaire deux profils sans créer deux jeux séparés.

### Touriste

- comprend la promesse en dix secondes ;
- pose une défense immédiatement ;
- participe sans maîtriser tous les systèmes ;
- termine une session courte ;
- voit une récompense claire.

### Local

- optimise sa forteresse ;
- maîtrise les interactions ;
- spécialise son rôle ;
- collectionne des plans ;
- aide d’autres joueurs ;
- participe aux défis et événements ;
- développe une identité reconnue.

Roblox recommande de concevoir simultanément pour les joueurs qui passent rapidement d’une expérience à l’autre et pour ceux qui deviennent profondément engagés. La plateforme souligne aussi que les FTUE rapides, le jeu social et le mobile-first sont particulièrement importants. ([Roblox — Design for Roblox](https://create.roblox.com/docs/production/game-design/design-for-roblox))

---

# 4. Principes non négociables

## 4.1 One verb, infinite situations

Le verbe principal est :

> **Préparer une défense et la tester.**

La complexité vient des situations, pas du nombre de boutons.

## 4.2 No proof, no progression

Les grands déblocages sont obtenus en réussissant des challenges, pas en remplissant uniquement une barre par répétition.

## 4.3 Failure teaches

Un échec doit être :

- compréhensible ;
- récupérable ;
- utile ;
- suffisamment court pour donner envie de retenter.

## 4.4 Better with friends, viable alone

La coopération ajoute des stratégies et des histoires. Elle ne doit pas rendre le solo impossible.

## 4.5 Destruction spectaculaire, perte limitée

La bataille peut ravager visuellement la forteresse, mais le plan sauvegardé est restauré après l’assaut.

## 4.6 Horizontal before vertical

Les nouveaux outils, interactions et choix sont plus importants que l’augmentation des statistiques.

## 4.7 Mobile first

Toute action centrale doit être réalisable confortablement au tactile. Roblox indique que la majorité de son audience joue sur mobile et recommande une UI principalement visuelle et pensée d’abord pour ces appareils. ([Roblox — Design for Roblox](https://create.roblox.com/docs/production/game-design/design-for-roblox))

## 4.8 Easy to stop, desirable to return

Aucune dégradation hors ligne, aucune série punitive, aucune perte liée à l’absence.

---

# 5. Les six moteurs de rétention

## 5.1 Plaisir immédiat

Le joueur doit :

- contrôler son avatar immédiatement ;
- poser une première défense en moins de 20 secondes ;
- voir cette défense agir en moins de 40 secondes ;
- combattre lui-même avant 60 secondes ;
- terminer une première micro-défense avant 3 minutes.

## 5.2 Maîtrise

Le joueur apprend à :

- dessiner des chemins ;
- répartir l’énergie ;
- combiner les pièges ;
- lire les ennemis ;
- prioriser les crises ;
- coopérer ;
- adapter sa stratégie.

La théorie de l’autodétermination identifie autonomie, compétence et relation comme besoins psychologiques associés à la motivation et au bien-être. Cette théorie informe une hypothèse de design ; elle ne prouve pas la rétention de ce jeu. ([Ryan & Deci, 2000](https://www.selfdeterminationtheory.org/SDT/documents/2000_RyanDeci_SDT.pdf))

## 5.3 Progression

Chaque session doit produire au moins une transformation :

- nouvelle possibilité ;
- nouvelle connaissance ;
- amélioration visible ;
- étape vers un gate ;
- trophée ;
- modification de forteresse ;
- relation sociale renforcée.

## 5.4 Variation

Elle provient de :

- l’architecture du joueur ;
- la composition de la horde ;
- les directions d’attaque ;
- les crises ;
- les modificateurs ;
- les biomes ;
- les alliés ;
- les combinaisons de systèmes.

## 5.5 Relation

Les amis changent réellement le résultat par :

- rôles complémentaires ;
- sauvetages ;
- construction sous permission ;
- coordination ;
- historique commun ;
- visites ;
- appels de détresse.

Roblox inclut le jeu entre amis parmi les signaux de recommandation et décrit les joueurs comme une source durable de contenu les uns pour les autres. ([Roblox — Discovery](https://create.roblox.com/docs/production/promotion/discovery), [Design for Roblox](https://create.roblox.com/docs/production/game-design/design-for-roblox))

## 5.6 Anticipation

À la fin d’une session, le joueur doit connaître une prochaine intention concrète :

- corriger une brèche ;
- fabriquer un module ;
- débloquer un plan ;
- tenter un modificateur ;
- rejoindre un ami ;
- explorer une nouvelle région.

---

# 6. Boucles de jeu

## 6.1 Boucle centrale

1. observer la prochaine menace ;
2. préparer librement la forteresse ;
3. sélectionner un challenge ;
4. verrouiller un instantané de la base ;
5. défendre activement ;
6. analyser la bataille ;
7. améliorer la base ;
8. retenter ou avancer.

## 6.2 Boucle d’expédition

1. identifier un besoin ;
2. choisir une mission ciblée ;
3. entrer dans une zone ;
4. accomplir un objectif actif ;
5. choisir un niveau de risque ;
6. extraire ;
7. utiliser la récompense dans la forteresse.

## 6.3 Boucle sociale

1. visiter, inviter ou répondre à un appel ;
2. choisir une contribution ;
3. préparer ensemble ;
4. défendre ;
5. reconnaître les contributions ;
6. conserver une trace commune ;
7. proposer une prochaine action.

## 6.4 Boucle long terme

1. franchir un gate ;
2. accéder à une région ;
3. apprendre une nouvelle règle ;
4. obtenir de nouvelles possibilités ;
5. développer une spécialité ;
6. aider ou défier la communauté ;
7. participer aux saisons.

---

# 7. Première expérience utilisateur

Roblox définit l’onboarding comme les premières minutes et recommande de limiter les abandons grâce à une expérience rapide, visuelle et mesurable par funnel et expérimentation. ([Roblox — Onboarding](https://create.roblox.com/docs/production/game-design/onboarding), [Experiments](https://create.roblox.com/docs/production/experiments))

## 7.1 Règle fondamentale

Le nouveau joueur ne commence jamais devant un terrain vide.

Il commence dans une mini-forteresse fonctionnelle, volontairement imparfaite.

## 7.2 Chronologie cible

### 0–10 secondes

- le noyau est visible ;
- trois zombies approchent ;
- une zone de placement lumineuse apparaît ;
- aucun texte long.

### 10–25 secondes

- le joueur pose gratuitement une tourelle ;
- elle tire immédiatement ;
- animation, son et réaction ennemie confirment la causalité.

### 25–50 secondes

- le joueur reçoit une arme simple ;
- il termine les ennemis restants.

### 50–90 secondes

- une brute arrive ;
- elle ouvre une brèche visible ;
- le joueur pose un mur ou répare.

### 90–180 secondes

- micro-challenge final ;
- première victoire ;
- écran de résultat très court ;
- la faiblesse observée est mise en évidence.

### 3–6 minutes

- le joueur déplace un piège ;
- lance un rematch court ;
- choisit son premier déblocage horizontal.

### 6–10 minutes

- première invitation contextuelle possible ;
- aperçu d’une expédition ;
- prochaine menace annoncée.

## 7.3 Objectifs de funnel

Événements serveur :

1. `JOINED`
2. `CONTROL_GAINED`
3. `FIRST_DEFENSE_PLACED`
4. `FIRST_ENEMY_DEFEATED`
5. `FIRST_REPAIR`
6. `FIRST_CHALLENGE_STARTED`
7. `FIRST_CHALLENGE_COMPLETED`
8. `FIRST_BASE_EDIT`
9. `FIRST_REMATCH`
10. `FIRST_FUTURE_GOAL_VIEWED`

## 7.4 Interdictions FTUE

- cinématique longue ;
- dialogue obligatoire ;
- création de classe avant de jouer ;
- inventaire complexe ;
- arbre de compétences ;
- choix irréversible ;
- tutoriel de farming avant la défense ;
- boutique dans les premières minutes.

---

# 8. La forteresse persistante

Le contrat candidat [Persistence Loop 0.6.1](docs/PERSISTENCE_LOOP_0_6.md)
spécifie uniquement la couche de profil nécessaire à la première preuve de
retour. Il ne rend pas persistants par défaut tous les systèmes décrits dans ce
chapitre et reste soumis à G4.

## 8.1 Rôle

La forteresse est :

- le foyer ;
- l’atelier ;
- le terrain stratégique ;
- la représentation de la progression ;
- l’espace social ;
- le musée des accomplissements.

## 8.2 Préparation sans chronomètre

Le joueur peut construire sans limite de temps.

Le jeu doit toutefois éviter la paralysie par :

- modèles de départ ;
- recommandations non obligatoires ;
- mini-tests ;
- indicateur de préparation ;
- prochaine action clairement visible ;
- bouton de challenge toujours accessible.

## 8.3 Construction sur grille

Le système utilise :

- cellules larges ;
- rotation par incréments ;
- aperçu fantôme ;
- validation visuelle immédiate ;
- undo ;
- déplacement sans coût hors challenge ;
- sélection tactile confortable.

## 8.4 Budgets

Chaque base possède trois limites lisibles :

### Structure

Nombre ou poids maximal de pièces.

### Énergie

Capacité des dispositifs actifs.

### Complexité

Budget technique limitant les mécanismes lourds.

Ces limites servent simultanément l’équilibrage, les performances et la créativité.

## 8.5 Instantané

Au lancement d’un challenge :

- le plan est sauvegardé ;
- l’équipement est enregistré ;
- les permissions sont verrouillées ;
- l’assaut utilise cette version.

Après l’assaut :

- la base revient à cet instantané ;
- les dégâts structurels ne sont pas permanents ;
- les récompenses et consommables légers suivent les règles du challenge.

## 8.6 Tests gratuits

Le joueur peut lancer :

- test de chemin ;
- test d’énergie ;
- mini-vague de 30 secondes ;
- test d’un ennemi ;
- simulation d’une section.

Ces tests n’accordent pas de récompense de progression.

---

# 9. Systèmes de forteresse

## 9.1 Architecture

- mur ;
- sol ;
- rampe ;
- porte ;
- plateforme ;
- barricade.

## 9.2 Énergie

- générateur ;
- relais ;
- batterie ;
- interrupteur ;
- circuits séparés.

Règle : une base centralisée est puissante mais fragile ; une base distribuée est robuste mais coûteuse.

## 9.3 Contrôle de mouvement

- ralentissement ;
- poussée ;
- attraction ;
- tapis roulant ;
- porte conditionnelle ;
- leurre.

## 9.4 Dégâts automatiques

- tourelle rapide ;
- tourelle lourde ;
- piège perforant ;
- piège de zone ;
- piège élémentaire.

## 9.5 Défenses manuelles

- canon ;
- décharge ;
- broyeur ;
- porte écrasante ;
- capacité de forteresse.

## 9.6 Soutien

- station de soin ;
- distributeur ;
- drone de réparation ;
- capteur ;
- balise de réanimation.

---

# 10. Interactions combinatoires

Le jeu doit lancer avec peu d’éléments et beaucoup d’interactions.

Exemples :

- eau + électricité ;
- huile + feu ;
- gel + écrasement ;
- poussée + fosse ;
- ralentissement + perforation ;
- leurre + explosion ;
- marquage + tourelle précise ;
- porte + séparation d’une brute et de son soutien ;
- batterie + réseau de secours ;
- convoyeur + zone de dégâts.

## 10.1 Règle de contenu

Un nouvel élément LiveOps est prioritaire s’il interagit utilement avec au moins trois éléments existants.

## 10.2 Pas de solution parfaite

Toute stratégie forte doit avoir :

- un coût ;
- une vulnérabilité ;
- une situation où elle excelle ;
- une situation où elle est moins adaptée.

---

# 11. Challenges de défense

## 11.1 Sélection volontaire

Le joueur choisit le challenge lorsqu’il se juge prêt.

La fiche affiche :

- nom ;
- difficulté ;
- durée estimée ;
- menaces connues ;
- directions probables ;
- modificateurs ;
- récompenses ;
- objectif bonus ;
- niveau de maîtrise recommandé.

## 11.2 Durées

- tutoriel : 3–4 minutes ;
- challenge précoce : 5–7 minutes ;
- standard : 7–10 minutes ;
- gate ou boss : 10–12 minutes ;
- endurance volontaire : 15–30 minutes.

## 11.3 Structure dramatique

1. reconnaissance ;
2. premier assaut ;
3. respiration courte ;
4. contre-stratégie ;
5. crise ;
6. assaut final ;
7. résolution.

Chaque 45 à 90 secondes doit apparaître au moins un changement significatif.

## 11.4 Pendant l’assaut

La construction lourde est verrouillée.

Le joueur peut :

- réparer ;
- reconstruire une défense d’urgence limitée ;
- réapprovisionner ;
- ouvrir et fermer ;
- activer ;
- combattre ;
- sauver ;
- déplacer certains dispositifs mobiles.

---

# 12. The Horde Learns

## 12.1 Objectif

Faire paraître la horde intelligente sans lui permettre de tricher.

## 12.2 Sources d’information

La horde connaît uniquement :

- la géométrie accessible ;
- ce que ses éclaireurs ont vu ;
- ce que les vagues précédentes ont rencontré ;
- quelques signatures visibles : énergie, bruit, tirs, densité.

## 12.3 Profil de base

Le jeu calcule des scores bornés :

- dépendance énergétique ;
- concentration sur un axe ;
- vulnérabilité aux brutes ;
- vulnérabilité aérienne ;
- densité de pièges au sol ;
- couverture arrière ;
- résistance structurelle ;
- capacité de réparation.

## 12.4 Budget d’adaptation

Chaque challenge attribue à la horde un budget limité.

Elle peut utiliser ce budget pour :

- remplacer une fraction d’ennemis ;
- changer un axe ;
- introduire un saboteur ;
- synchroniser deux rôles ;
- déclencher une crise annoncée.

Elle ne peut jamais :

- générer le contre parfait ;
- modifier secrètement les dégâts ;
- ignorer une règle ;
- apparaître directement au noyau ;
- supprimer une défense sans télégraphie.

## 12.5 Télégraphie

Avant une menace importante :

- silhouette ;
- son ;
- icône ;
- direction approximative ;
- temps court de réaction.

## 12.6 Mémoire

La horde possède :

- mémoire du challenge courant ;
- mémoire légère des derniers challenges ;
- oubli progressif ;
- adaptation différente selon la région.

Ainsi, changer de stratégie redevient utile.

---

# 13. Familles d’ennemis

## 13.1 Envahisseurs

- rôdeur : standard ;
- coureur : rapide et fragile ;
- essaim : nombreux petits ennemis ;
- blindé : résiste aux tirs frontaux.

## 13.2 Destructeurs

- brute : attaque les murs ;
- grimpeur : franchit certaines hauteurs ;
- creuseur : crée un passage lentement ;
- pousseur : déplace des protections légères.

## 13.3 Saboteurs

- coupe-circuit ;
- brouilleur de tourelle ;
- voleur de munitions ;
- désactivateur de piège.

## 13.4 Soutiens

- hurleur : accélère ;
- gardien : protège ;
- soigneur : restaure ;
- porteur : transporte de petits ennemis.

## 13.5 Manipulateurs

- ravisseur : immobilise un joueur ;
- leurreur : attire le tir automatique ;
- contaminateur : rend une zone dangereuse ;
- faux éclaireur : crée un signal trompeur mais identifiable.

## 13.6 Boss

Un boss ajoute une règle, pas seulement des points de vie.

Exemples :

- ouvre périodiquement une nouvelle route ;
- protège une formation ;
- provoque des coupures ;
- transforme une zone ;
- exige une action coordonnée.

---

# 14. Combat manuel

Le premier profil d'implémentation candidat est
[Action Loop 0.4.1](docs/ACTION_LOOP_0_4.md). Son scope Fight, Repair, Rescue est
plus étroit que la liste cible de ce chapitre et doit être livré par sous-gates
réversibles s'il est explicitement autorisé.

## 14.1 Rôle

> **La forteresse gère l’ordinaire. Les joueurs gèrent l’extraordinaire.**

## 14.2 Actions

- tirer ;
- viser une priorité ;
- réparer ;
- réapprovisionner ;
- réanimer ;
- activer une machine ;
- fermer une brèche ;
- déplacer un gadget ;
- marquer une cible.

## 14.3 Arsenal de lancement

- fusil polyvalent ;
- arme de contrôle ;
- outil de réparation ;
- gadget de crise.

## 14.4 Garde-fous

- les armes ne remplacent pas la base ;
- les tourelles ne permettent pas l’AFK ;
- les dégâts ne dominent pas toutes les contributions ;
- la précision mobile reste assistée mais non automatique.

---

# 15. Autopsie de défense

## 15.1 Objectif

Transformer chaque échec en prochaine action.

## 15.2 Données affichées

- première brèche ;
- chemin dominant ;
- temps de coupure ;
- structure la plus utile ;
- structure sous-utilisée ;
- ennemi principal ;
- moment critique ;
- contribution de chaque joueur ;
- état final du noyau.

## 15.3 Replay accéléré

- trajectoires ;
- heatmap ;
- événements clés ;
- retour 30 secondes avant le point critique ;
- comparaison avec le challenge précédent.

## 15.4 Recommandations

Le jeu ne donne pas la solution.

Il peut dire :

- « 72 % des ennemis ont utilisé l’axe est » ;
- « le réseau principal est resté hors ligne 28 secondes » ;
- « aucun outil ne ciblait les grimpeurs ».

Il ne doit pas dire :

- « place exactement cette tourelle ici ».

## 15.5 Sortie

Boutons prioritaires :

1. modifier la base ;
2. relancer ;
3. demander de l’aide ;
4. changer de challenge.

---

# 16. Expéditions

## 16.1 Règle

Le farming doit toujours être du gameplay.

## 16.2 Durée

6 à 10 minutes standard.

## 16.3 Structure

1. briefing court ;
2. objectif ;
3. exploration active ;
4. complication ;
5. choix de risque ;
6. extraction ;
7. récompense ciblée.

## 16.4 Missions

- défendre une foreuse ;
- réparer une centrale ;
- sauver un ingénieur ;
- transporter une batterie ;
- capturer un spécimen ;
- escorter ;
- infiltrer ;
- récupérer puis extraire.

## 16.5 Risque

Le joueur choisit :

- extraction sûre ;
- objectif bonus ;
- zone dangereuse ;
- modificateur facultatif.

## 16.6 Récompenses

- matériaux ;
- composants ;
- plan ;
- information ennemie ;
- survivant ;
- cosmétique ;
- recherche.

## 16.7 Anti-corvée

- pas de récolte passive prolongée ;
- pas de respawn d’objet attendu sans activité ;
- pas de marche inutile ;
- pas de ressource essentielle dépendant d’un taux opaque extrêmement faible ;
- mécanisme de garantie pour les drops nécessaires à la progression.

---

# 17. Progression

[Progression Loop 0.5.1](docs/PROGRESSION_LOOP_0_5.md) est le contrat candidat
minimal : état mémoire serveur, trois difficultés et cinq sidegrades. Les
matériaux, la progression multi-session et l'économie complète du présent
chapitre restent hors de cette slice.

Le concept canonique conserve le principe :

> **Une difficulté plus élevée peut accélérer la progression.**

Mais cette accélération est bornée et ne doit pas créer un grind circulaire.

## 17.1 Trois systèmes séparés

### A. Indice de maîtrise

Non dépensable.

Calculé à partir de :

- difficulté réussie ;
- première réussite ;
- modificateurs ;
- objectifs bonus ;
- variété des stratégies ;
- contraintes volontaires ;
- efficacité.

Il sert à :

- représenter le niveau réel ;
- débloquer les gates ;
- accéder aux régions ;
- recommander des challenges ;
- afficher du statut.

### B. Recherche

Ressource de déblocage.

Obtenue surtout par :

- première réussite ;
- nouvelle menace comprise ;
- expédition de recherche ;
- challenge de maîtrise ;
- découverte.

Elle débloque :

- pièges ;
- modules ;
- interactions ;
- comportements ;
- variantes.

### C. Matériaux

Obtenus en expédition.

Ils servent à :

- fabriquer ;
- améliorer modérément ;
- préparer ;
- personnaliser.

## 17.2 Récompense de difficulté

Une difficulté supérieure donne davantage de maîtrise et de recherche, mais :

- rendement plafonné ;
- bonus de première réussite ;
- bonus de variété ;
- rendement décroissant sur répétition identique ;
- aucun challenge obligatoire au-dessus du confort du joueur ;
- récompense utile aussi en solo et en soutien.

## 17.3 Progression horizontale

Prioritaire :

- nouveaux outils ;
- nouvelles synergies ;
- nouvelles règles ;
- spécialités ;
- options de base.

## 17.4 Progression verticale

Modérée :

- durabilité ;
- capacité ;
- portée ;
- vitesse ;
- efficacité.

Plafonds stricts pour éviter que les anciens joueurs annulent le challenge des nouveaux.

## 17.5 Progression identitaire

- style de forteresse ;
- spécialité ;
- trophées ;
- bannière ;
- survivants ;
- galerie ;
- titres ;
- replays ;
- historique social.

---

# 18. Régions et gates

## 18.1 Déblocage

Une région exige :

- un seuil de maîtrise ;
- la réussite du gate précédent ;
- éventuellement une découverte ou technologie.

Pas seulement un total de points accumulés.

## 18.2 Chaque région ajoute une règle

### Banlieue abandonnée

Fondamentaux.

### Zone inondée

Eau conductrice, chemins mouvants.

### Région glacée

Sols glissants, systèmes ralentis.

### Désert industriel

Surchauffe, faible énergie.

### Centrale

Énergie abondante mais instable.

### Zone organique

Terrain contaminé et routes évolutives.

## 18.3 Règle d’escalade

Une nouvelle région doit introduire au moins :

- une règle environnementale ;
- deux ennemis ;
- une famille de ressources ;
- une interaction défensive ;
- un gate mémorable.

---

# 19. Coopération

## 19.1 Taille

1 à 4 joueurs.

## 19.2 Rôles émergents

Pas de classe obligatoire.

L’équipement produit les rôles :

- architecte ;
- combattant ;
- réparateur ;
- opérateur ;
- soutien ;
- éclaireur.

## 19.3 Mise à l’échelle

La coopération augmente :

- variété des crises ;
- fronts ;
- actions simultanées ;
- objectifs optionnels.

Elle ne multiplie pas uniquement la santé ennemie.

## 19.4 Contributions reconnues

- dégâts ;
- ralentissement ;
- réparations ;
- sauvetages ;
- alimentation ;
- contrôle ;
- construction ;
- information ;
- maintien du noyau.

## 19.5 Answer the Call

Après une défaite ou avant un challenge difficile :

- appel à un ami ;
- invitation contextuelle ;
- lancement direct vers la base ;
- rôle suggéré ;
- récompense équitable.

Roblox permet des invitations contextualisées avec données de lancement afin de router ou personnaliser l’arrivée de l’ami. ([Roblox — Player invite prompts](https://create.roblox.com/docs/production/promotion/invite-prompts))

## 19.6 Permissions

- visite ;
- interaction ;
- réparation ;
- construction temporaire ;
- zone autorisée ;
- construction complète.

Le propriétaire garde toujours le contrôle final.

---

# 20. Social asynchrone et communauté

## 20.1 Visites

Les joueurs peuvent :

- visiter une forteresse ;
- tester une section ;
- admirer les trophées ;
- laisser une réaction ;
- proposer une amélioration.

## 20.2 Plans

Après la bêta seulement :

- publication d’un module limité ;
- remix ;
- attribution du créateur ;
- test avant utilisation ;
- signalement.

## 20.3 Défis communautaires

- menace mondiale ;
- objectif collectif ;
- boss ;
- contrainte hebdomadaire ;
- reconstruction d’une région.

## 20.4 Statut sain

Classements séparés :

- maîtrise ;
- efficacité ;
- créativité ;
- soutien ;
- challenge minimaliste ;
- endurance.

Pas un seul classement dominé par le temps joué ou les dépenses.

---

# 21. Session design

## 21.1 Construction

Durée libre, mais jalons visibles.

Sortie propre :

- plan sauvegardé ;
- mini-test effectué ;
- prochaine tâche marquée.

## 21.2 Défense éclair

4–5 minutes.

Objectif : test rapide.

## 21.3 Défense standard

7–10 minutes.

Objectif : boucle centrale.

## 21.4 Gate

10–12 minutes.

Objectif : progression majeure.

## 21.5 Expédition

6–10 minutes.

Objectif : préparation ciblée.

## 21.6 Endurance

15–30 minutes, volontaire.

Objectif : maîtrise et statut.

## 21.7 Session sociale

Visite, aide ou test court.

Objectif : relation et contenu humain.

---

# 22. Difficulté

## 22.1 Ce qui augmente

- composition ;
- simultanéité ;
- axes ;
- comportements ;
- environnement ;
- contraintes ;
- information incomplète ;
- coordination.

## 22.2 Ce qui augmente peu

- santé ;
- dégâts ;
- vitesse brute.

## 22.3 Comeback

- réparation d’urgence ;
- batterie de secours ;
- réanimation ;
- sacrifice d’une zone ;
- ressource ponctuelle ;
- dernier rempart.

## 22.4 Échec lisible

Une défaite doit être attribuable à :

- décision ;
- préparation ;
- exécution ;
- connaissance encore incomplète.

Jamais à une règle cachée ou à un contre parfait.

---

# 23. Feedback et sensations

## 23.1 Chaque action

Doit produire :

- animation ;
- son ;
- réaction ;
- information ;
- conséquence.

## 23.2 Ennemis

Chaque rôle possède :

- silhouette ;
- couleur ou matière ;
- son ;
- animation préparatoire ;
- réaction particulière.

## 23.3 Forteresse

États immédiatement visibles :

- alimenté ;
- désactivé ;
- endommagé ;
- vide ;
- surchargé ;
- ciblé.

## 23.4 Spectacle lisible

Les effets ne doivent jamais masquer :

- la direction ;
- la cible ;
- la cause ;
- la priorité.

---

# 24. Direction artistique

## 24.1 Ton

- stylisé ;
- expressif ;
- non gore ;
- légèrement inquiétant ;
- drôle par moments ;
- fortement lisible.

## 24.2 Monde

La civilisation survit grâce à des forteresses improvisées et à des expéditions technologiques.

## 24.3 Zombies

Ils doivent être mémorisables et commercialement distinctifs.

## 24.4 Avatar

Conserver l’identité Roblox du joueur autant que possible, car la visibilité de l’avatar et l’identité commune à la plateforme soutiennent l’expression sociale. ([Roblox — Design for Roblox](https://create.roblox.com/docs/production/game-design/design-for-roblox))

---

# 25. UI/UX

## 25.1 Principes

- tactile d’abord ;
- icônes cohérentes ;
- texte minimal ;
- actions centrales accessibles en un geste ;
- pas de menus profonds pendant une crise.

## 25.2 Construction mobile

- glisser ;
- rotation ;
- confirmer ;
- annuler ;
- suppression protégée ;
- multi-sélection ultérieure.

## 25.3 HUD de défense

Afficher seulement :

- santé du noyau ;
- phase ;
- menace prioritaire ;
- état énergétique ;
- équipement ;
- alliés en danger.

## 25.4 Accessibilité

- taille de texte ;
- contraste ;
- signaux non dépendants uniquement de la couleur ;
- réduction d’effets ;
- sensibilité caméra ;
- aides de visée ;
- sous-titres des signaux critiques.

---

# 26. Économie

## 26.1 Ressources maximales au lancement

- matériaux communs ;
- composants techniques ;
- recherche ;
- indice de maîtrise non dépensable.

## 26.2 Sources

- expéditions ;
- challenges ;
- premiers clears ;
- objectifs bonus ;
- aide sociale.

## 26.3 Puits

- fabrication ;
- amélioration ;
- personnalisation ;
- préparation.

## 26.4 Garde-fous

- pas de vingt monnaies ;
- pas de coûts cachés ;
- pas de réparation payante punitive ;
- pas d’inflation incontrôlée ;
- pas de ressource essentielle uniquement aléatoire.

---

# 27. Trading

## 27.1 Statut

Reporté après validation de :

- boucle ;
- économie ;
- sauvegarde ;
- sécurité ;
- stabilité des valeurs.

## 27.2 Échangeable à terme

- matériaux standards ;
- décorations ;
- plans ordinaires ;
- consommables sociaux.

## 27.3 Non échangeable

- indice de maîtrise ;
- gates ;
- trophées ;
- récompenses d’accomplissement ;
- objets essentiels payants.

## 27.4 Sécurité

- validation serveur ;
- transaction atomique ;
- journal ;
- fenêtre de confirmation ;
- limites ;
- protection contre duplication et fraude.

Les règles Roblox imposent aussi des restrictions par utilisateur pour certains échanges et objets aléatoires payants ; le jeu devra consulter les politiques applicables avant d’exposer ces fonctions. ([Roblox — Paid random items policy guidelines](https://create.roblox.com/docs/production/monetization/paid-random-items))

---

# 28. Monétisation

## 28.1 Principe

Monétiser l’identité et le confort social, pas la victoire.

## 28.2 Produits appropriés

- thèmes de forteresse ;
- apparences de pièges ;
- skins de tourelles ;
- effets de construction ;
- tenues ;
- bannières ;
- emotes ;
- décorations ;
- apparence du noyau ;
- serveur privé raisonnablement tarifé ;
- passe cosmétique saisonnier.

## 28.3 Interdictions

- puissance exclusive ;
- matériaux artificiellement ralentis ;
- paiement pour restaurer après une défaite ;
- achat de chance nécessaire ;
- timers vendus comme problème puis solution ;
- loot boxes de puissance ;
- private servers prohibitifs.

Roblox déconseille les pratiques de monétisation trompeuses ou créant une fausse urgence et recommande de ne pas entraver le jeu social. ([Roblox — Monetization](https://create.roblox.com/docs/production/monetization), [Design for Roblox](https://create.roblox.com/docs/production/game-design/design-for-roblox))

---

# 29. LiveOps

Roblox décrit le LiveOps comme une combinaison de cadence de contenu, mises à jour majeures, qualité de vie et correctifs. La cadence légère doit réutiliser les systèmes existants afin de réduire le coût de production et de débogage. ([Roblox — LiveOps essentials](https://create.roblox.com/docs/production/game-design/liveops-essentials))

## 29.1 Cadence réaliste pour deux personnes

### Rotation hebdomadaire automatisée

- modificateur ;
- contrat ;
- composition de horde ;
- défi de construction ;
- récompense cosmétique.

### Mise à jour mensuelle

- ennemi ;
- piège ou module ;
- expédition ;
- amélioration de qualité de vie.

### Saison trimestrielle

- région ;
- boss ;
- règle environnementale ;
- arc communautaire.

## 29.2 Règle de planification

Chaque événement doit définir :

- action attendue ;
- KPI visé ;
- impact économique ;
- communication ;
- mesure après événement.

Roblox recommande de lier les événements à des actions et KPIs explicites, puis de mesurer leur effet. ([Roblox — LiveOps planning](https://create.roblox.com/docs/production/game-design/liveops-planning))

## 29.3 Pas de FOMO destructrice

- contenu essentiel permanent ou récurrent ;
- calendrier annoncé ;
- récompenses cosmétiques ;
- aucune perte de puissance liée à l’absence ;
- rattrapage possible.

---

# 30. Horloges de rétention

## Chaque seconde

- mouvement agréable ;
- contrôle réactif ;
- feedback.

## Toutes les 20–60 secondes

- décision ;
- mini-résultat ;
- changement ;
- contribution.

## Toutes les 3–5 minutes

- boucle partielle ;
- révélation ;
- choix ;
- moment social.

## Chaque session

- résolution ;
- transformation ;
- prochaine aspiration.

## Chaque jour

- plan à poursuivre ;
- menace ;
- ami ;
- objectif léger.

## Chaque semaine

- mutation ;
- défi ;
- événement ;
- nouvelle combinaison.

## Chaque saison

- région ;
- identité ;
- transformation communautaire.

---

# 31. Analytics

Roblox recommande d’optimiser d’abord D1 et le temps de session avant d’accélérer fortement l’acquisition. Les benchmark scorecards comparables deviennent disponibles à partir de 100 DAU. ([Roblox — Analytics](https://create.roblox.com/docs/production/analytics))

## 31.1 Funnel onboarding

Voir section 7.

## 31.2 Funnel central

1. menace consultée ;
2. modification de base ;
3. challenge sélectionné ;
4. challenge lancé ;
5. première crise ;
6. challenge terminé ;
7. autopsie consultée ;
8. modification post-challenge ;
9. rematch.

## 31.3 Funnel expédition

1. besoin identifié ;
2. mission choisie ;
3. objectif commencé ;
4. risque choisi ;
5. extraction ;
6. récompense utilisée.

## 31.4 Social

- invitation affichée ;
- invitation envoyée ;
- ami rejoint ;
- challenge joué ensemble ;
- nouvelle session commune ;
- appel de détresse ;
- aide donnée.

## 31.5 Segmentation

- appareil ;
- pays ;
- langue ;
- nouveau/ancien ;
- solo/groupe ;
- challenge ;
- région ;
- version ;
- variante expérimentale.

## 31.6 Questions analytiques

- combien de temps avant la première action ?
- où les joueurs quittent-ils ?
- combien modifient après une défaite ?
- combien relancent ?
- quelle part revient avec un ami ?
- quels outils créent de vraies stratégies ?
- une difficulté augmente-t-elle la satisfaction ou seulement le grind ?
- quelles bases convergent vers une stratégie dominante ?

---

# 32. Expérimentation

Roblox permet d’utiliser les funnels et expériences pour mesurer l’impact causal de variantes d’onboarding. Les expériences avec moins d'environ 1 000 DAU peuvent manquer de puissance statistique ; les playtests et tests déterministes restent donc nécessaires au stade prototype. ([Roblox — Experiments](https://create.roblox.com/docs/production/experiments))

## 32.1 Tests prioritaires

- défense immédiate vs courte introduction ;
- trois vs cinq éléments initiaux ;
- autopsie automatique vs facultative ;
- durée 5 vs 7 vs 9 minutes ;
- récompense de première réussite ;
- invite après victoire vs après défaite ;
- menace entièrement révélée vs partiellement révélée.

## 32.2 Règle

Un seul changement majeur par expérience.

---

# 33. Critères internes de validation

Ces seuils sont des gates internes, pas des benchmarks officiels Roblox.

## 33.1 Test de 20 joueurs

- 16/20 posent la première défense sans aide orale ;
- 15/20 terminent la micro-défense ;
- 12/20 comprennent pourquoi la brèche s’est produite ;
- 10/20 modifient volontairement ;
- 8/20 relancent immédiatement ;
- 5/20 demandent ou acceptent de jouer avec quelqu’un ;
- plusieurs décrivent clairement la différence du jeu.

## 33.2 Vertical slice

PASS seulement si :

- le rematch volontaire existe ;
- aucune stratégie unique ne domine ;
- l’autopsie est comprise ;
- le solo et la coopération sont viables ;
- le farming est jugé amusant en lui-même ;
- aucune erreur ou perte de sauvegarde critique ;
- mobile confortable.

## 33.3 Bêta

Comparer ensuite aux benchmarks Roblox similaires plutôt qu’appliquer un chiffre universel. Les cohortes quotidiennes et hebdomadaires permettent de suivre les retours et l’effet des mises à jour. ([Roblox — Retention](https://create.roblox.com/docs/production/analytics/retention))

---

# 34. Vertical slice v1.0

Cette section est un inventaire cible de vision, non une autorisation de tout
implémenter simultanément. L'ordre et le scope réellement autorisés sont ceux de
la [roadmap et des stage gates](docs/00-governance/ROADMAP_AND_STAGE_GATES.md),
puis du contrat de slice accepté applicable.

## 34.1 Base

- un terrain compact ;
- un noyau ;
- une grille ;
- snapshot ;
- sauvegarde simple.

## 34.2 Construction

- mur ;
- porte ;
- sol ;
- rampe.

## 34.3 Défenses

- ralentisseur ;
- piège de dégâts ;
- tourelle ;
- canon manuel ;
- générateur ;
- batterie.

## 34.4 Combat

- fusil ;
- réparation ;
- gadget ;
- réanimation.

## 34.5 Ennemis

- rôdeur ;
- coureur ;
- brute ;
- saboteur ;
- éclaireur ;
- boss.

## 34.6 Challenges

- tutoriel ;
- standard ;
- gate ;
- trois difficultés ;
- trois vulnérabilités détectables ;
- budget d’adaptation ;
- autopsie.

## 34.7 Expédition

- une carte ;
- une foreuse ;
- un risque optionnel ;
- extraction ;
- composant utile au gate.

## 34.8 Social

- 1–4 joueurs ;
- permissions simples ;
- difficulté adaptée ;
- contributions reconnues ;
- invitation contextuelle.

## 34.9 Progression

- indice de maîtrise ;
- recherche ;
- matériaux ;
- cinq déblocages horizontaux ;
- aucun trading ;
- aucune boutique de puissance.

---

# 35. Contenu interdit avant validation

- monde ouvert ;
- plusieurs grandes expéditions ;
- trading ;
- clans ;
- PvP destructeur ;
- UGC complet ;
- dizaines de monnaies ;
- centaines d’ennemis ;
- construction physique libre non bornée ;
- crafting complexe ;
- marketplace ;
- battle pass ;
- monétisation de puissance ;
- narration longue ;
- plusieurs saisons en avance.

---

# 36. Risques principaux

## 36.1 Scope

Réponse : vertical slice strict.

## 36.2 Pathfinding et horde

Réponse : grille de coûts, recalcul borné, ennemis limités, agrégation éventuelle.

## 36.3 Construction mobile

Réponse : grille large, gestes simples, playtests tactiles constants.

## 36.4 Stratégie dominante

Réponse : contre-mesures lisibles, coûts, régions, données de victoire.

## 36.5 Grind

Réponse : first-clear, variété, rendement décroissant, progression horizontale.

## 36.6 Coopération déséquilibrée

Réponse : normalisation partielle et rôles non fondés seulement sur les dégâts.

## 36.7 Social superficiel

Réponse : appels, rôles, visites, traces communes.

## 36.8 Difficulté injuste

Réponse : télégraphie, budget d’adaptation et autopsie.

---

# 37. Matrice de conformité aux douze lois

| Loi | Réponse de conception |
|---|---|
| Promesse immédiate | Forteresse + chute compréhensible visibles dans le marketing et la première minute ; horde apprenante réservée à `H-HORDE-001` après validation |
| Action avant explication | Tourelle, tir et micro-défense immédiats |
| Verbe simple, conséquences profondes | Préparer et tester, avec systèmes combinatoires |
| Autonomie, compétence, relation | Base libre, maîtrise réelle, coopération utile |
| Difficulté saine | Complexité plutôt qu’inflation, comeback et échec lisible |
| Feedback | Signaux temps réel + autopsie |
| Trois horizons | action, région, identité et communauté |
| Prochain progrès | menace, déblocage et correction visibles |
| Curiosité équitable | ennemis et règles teasés, pas de hasard opaque obligatoire |
| Joueurs comme contenu | aides, visites, plans et défis |
| Identité | forteresse, spécialité, trophées et histoire |
| Histoire de session | intention, montée, crise, climax, analyse et prochaine action |

---

# 38. Commandements de design

1. Le joueur joue avant de lire.
2. La première défense arrive avant la première économie.
3. La base est le personnage principal.
4. La difficulté ajoute des problèmes, pas seulement des statistiques.
5. Les points mesurent une preuve ; ils ne remplacent pas le plaisir.
6. Chaque échec révèle une information.
7. Chaque ami apporte une possibilité.
8. Chaque objet nouveau doit interagir avec l’existant.
9. Chaque session se termine proprement.
10. Aucune rétention ne justifie de punir l’absence.
11. Aucun achat ne doit réparer une frustration créée volontairement.
12. Aucune fonctionnalité n’est validée sans observation de joueurs.

---

# 39. Déclaration de vision v1.0

Cette déclaration décrit la direction si ses hypothèses successives passent. Elle
ne rend pas la horde adaptative, les expéditions, la persistance ou le social
autorisés avant leurs gates.

**Roblox Top 1 vise un PvE coopératif de forteresse persistante. Chaque joueur construit et prépare librement une base personnelle, explore des territoires pour obtenir les matériaux et technologies adaptés aux menaces futures, puis sélectionne volontairement des challenges de difficulté croissante. Pendant la défense, ses pièges et tourelles gèrent la pression ordinaire tandis que les joueurs combattent, réparent, coordonnent et répondent aux crises. Si `H-HORDE-001` est validée, une horde lisible observe certaines dépendances de la base et adapte une partie de ses attaques dans un budget limité, sans tricher. Après chaque assaut, la forteresse est restaurée, la bataille est analysée et le joueur peut modifier sa stratégie puis relancer. Les difficultés supérieures accélèrent une progression bornée fondée sur la maîtrise, la recherche et les nouvelles possibilités, tandis que la puissance brute reste plafonnée. La forteresse, les relations et l’histoire des défenses constituent l’identité durable visée du joueur.**

---

# 40. Formule directrice v1.0

> **La base est une hypothèse.**<br>
> **La horde est le test.**<br>
> **La bataille produit les preuves.**<br>
> **La reconstruction est la progression.**

---

# 41. Méthode acceptée et hypothèses d’innovation

Le projet ne cherche ni à plaire littéralement à tous ni à rendre le joueur
incapable de s’arrêter. Il cherche une entrée rapidement lisible pour ses
segments cibles, plusieurs formes de contribution utiles et un retour volontaire
fondé sur la maîtrise, l’identité, la relation et la confiance.

Les cinq signatures candidates ne sont pas des fonctionnalités promises. Elles
forment un registre d’hypothèses ordonné :

1. `H-FAILURE-001 / Every Failure Teaches` : hypothèse active ;
2. `H-HORDE-001 / The Horde Learns` : non testée, subordonnée à la première ;
3. `H-FORTRESS-001 / The Living Fortress` : différée après G3 ;
4. `H-SOCIAL-001 / Answer the Call` : différée jusqu’à G5 ;
5. `H-PREPARE-001 / Prepare for Tomorrow` : différée après preuve de la boucle.

Seule `H-FAILURE-001` est prioritaire maintenant. Une horde adaptative n’est
testée qu’après un signal suffisant que l’autopsie seule produit compréhension,
modification et rematch. Aucun biais psychologique, signal Discovery, diagnostic
interne ou KPI brut ne remplace cette observation.

La méthode complète, y compris la formule du CCU30 observé, la séparation entre
métriques officielles et internes, les guardrails, les niveaux de preuve et les
critères de décision, est
[PRODUCT_INNOVATION_AND_RETENTION_DOCTRINE.md](docs/PRODUCT_INNOVATION_AND_RETENTION_DOCTRINE.md).
