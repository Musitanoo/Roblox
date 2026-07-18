# Doctrine d’innovation et de rétention durable

| Champ | Valeur |
| --- | --- |
| ID | `PRODUCT-RETENTION-001` |
| Classe | `CONTRACT` méthodologique avec registre d’`HYPOTHESIS` |
| Cycle de vie | `ACCEPTED` |
| Version | 1.0.1 |
| Propriétaire / approbateur | Founder |
| Scope | Règles d’éthique, de mesure et d’expérimentation ; hypothèses de différenciation et de rétention |
| Source | GDD v1.0.4, deux analyses fournies par le founder, sources primaires et Roblox Creator Hub |
| Dernière revue | 2026-07-17 |
| Revue suivante | Nouvelle preuve joueur, changement Discovery/Analytics/Policy, ou ouverture de G3, G6, G7 ou G9 |

## Journal de révision

- `1.0.1` — alignement sur les huit signaux Home et les segments temporels
  publiés dans la source Roblox Creator Docs courante ; retrait du nom `qPTR`
  devenu obsolète dans cette source.
- `1.0.0` — méthode éthique, métriques, niveaux de preuve et registre
  d'hypothèses initiaux.

Ce document complète le GDD. Son cycle `ACCEPTED` accepte la **méthode** :
frontière éthique, définitions, ordre des preuves, gates et règles de décision.
Il n’accepte pas comme faits les mécanismes, motivations, horloges ou effets
comportementaux qu’il inventorie. Ceux-ci restent des `HYPOTHESIS` jusqu’à une
preuve enregistrée. Le GDD reste l’autorité sur la vision ; la constitution
produit reste supérieure sur l’éthique et les invariants ; les contrats de slice
limitent ce qui peut être construit maintenant.

### 0.1 Légende d’autorité

| Marqueur | Sens | Peut autoriser une implémentation ? |
| --- | --- | --- |
| `RULE` | contrainte normative acceptée par le projet | oui, dans le scope du gate applicable |
| `PLATFORM FACT` | définition ou règle Roblox vérifiée et datée | seulement avec revalidation au moment d’usage |
| `HYPOTHESIS` | mécanisme plausible mais non prouvé pour ce jeu | non, sauf expérience autorisée par un gate |
| `INTERNAL METRIC` | diagnostic défini par le projet | non ; ne remplace jamais une métrique officielle |
| `EVIDENCE` | observation contextualisée et conservée | seulement dans les limites de son protocole |

## 1. Frontière de vérité

Il n’existe pas de jeu qui plaise à tout le monde, de règle psychologique qui
garantisse le retour, ni de formule produisant une rétention parfaite. Une
audience n’est pas une moyenne : elle contient des goûts, contraintes,
appareils, cultures, âges, situations sociales et disponibilités incompatibles.

Dans ce projet, « parfaitement addictif » est remplacé par :

> **Immédiatement compréhensible, volontairement rejouable, durablement
> satisfaisant, facile à quitter et désirable à retrouver.**

L’addiction n’est pas une métrique produit. L’OMS caractérise le trouble du jeu
vidéo par une perte de contrôle, une priorité croissante donnée au jeu et la
poursuite malgré des conséquences négatives. Ces résultats sont des échecs de
sécurité, pas des succès d’engagement. ([OMS — Trouble du jeu
vidéo](https://www.who.int/news-room/questions-and-answers/item/addictive-behaviours-gaming-disorder))

Toute affirmation de ce document appartient à l’une de ces catégories :

- **règle** : contrainte choisie par le projet ;
- **hypothèse** : relation plausible à tester ;
- **signal** : mesure corrélée qui peut diagnostiquer sans prouver la cause ;
- **preuve** : observation datée dans une population et un contexte nommés.

## 2. Thèse d’innovation

**Statut : `HYPOTHESIS H-INNOV-CORE-001 — UNTESTED`.**

« Construire une base et survivre à des zombies » est une catégorie générique.
La différenciation vient de la relation causale entre trois acteurs :

> **La forteresse exprime une hypothèse du joueur. La horde teste ses
> dépendances de façon lisible. L’autopsie transforme le résultat en nouvelle
> connaissance.**

La boucle signature est :

```text
menace lisible
→ préparation simple
→ défense dynamique
→ cause observable
→ modification significative
→ rematch volontaire
```

Dans ce projet, une fonctionnalité ne sera **considérée comme différenciante**
que si un joueur représentatif peut :

1. décrire ce qu’elle change dans ses décisions ;
2. reconnaître son effet pendant la partie ;
3. raconter un moment qu’elle a produit ;
4. vouloir l’utiliser autrement lors d’un nouvel essai.

La nouveauté technique, le volume de contenu et la complexité ne satisfont pas
ces conditions à eux seuls.

## 3. Simplicité d’accès, profondeur plurielle

**Statut : `HYPOTHESIS H-AUDIENCE-001 — UNTESTED`.** Cette matrice est une
couverture candidate de motivations, pas une segmentation prouvée de l’audience.

Le projet ne cherche pas une mécanique différente pour chaque profil. Il offre
une situation commune et plusieurs contributions utiles à la même victoire.

| Motivation | Entrée simple | Profondeur optionnelle | Échec à éviter |
| --- | --- | --- | --- |
| Action | tirer, réparer, déclencher | priorité de crise, timing, précision | combat décoratif ou dominant |
| Création | poser une pièce | architecture, routage, combinaisons | éditeur illisible sur mobile |
| Maîtrise | voir cause et effet | anticiper, tester, optimiser | statistiques opaques |
| Exploration | chercher une réponse | risque, routes, préparation ciblée | farming sans décision |
| Collection | obtenir un plan | construire un langage personnel | collection = inflation de puissance |
| Identité | personnaliser la base | style reconnu, histoire, trophées | prestige acheté présenté comme maîtrise |
| Relation | aider immédiatement | rôles émergents, coordination, mémoire commune | solo puni ou social forcé |
| Altruisme | réparer ou sauver | mentorat, appel de détresse | récompenses exploitables entre comptes |

L’interface applique une profondeur progressive :

- le débutant comprend objectif, menace et action utile ;
- l’intermédiaire comprend les interactions ;
- l’expert manipule les compromis et les situations, pas davantage de boutons.

## 4. Modèle complet du CCU

Le modèle sépare strictement mesures de plateforme et diagnostics internes.
Une métrique interne porte toujours un autre nom, une définition versionnée et
une source d’événements. Elle ne modifie jamais la définition affichée par
Roblox.

### 4.1 Identité mathématique

Sur une fenêtre de 30 jours :

```text
CCU30 moyen observé = somme(CCU_i × durée_i) / somme(durée_i)
```

Avec des échantillons uniformément espacés, cette moyenne pondérée devient la
moyenne arithmétique des échantillons. Lorsque l’intégrale exacte du nombre de
joueurs est disponible, l’identité équivalente est :

```text
CCU30 moyen observé = minutes-joueur de présence totales / 43 200 minutes
```

Ici, « présence » conserve la définition de la source Roblox. Elle n’est pas
silencieusement filtrée selon une notion interne de qualité.

De manière équivalente, sous une activité suffisamment stable :

```text
CCU ≈ démarrages de session par minute × durée active moyenne d’une session
```

Cette identité décrit le résultat ; elle ne dit pas comment l’améliorer. Une
session artificiellement prolongée peut augmenter temporairement le numérateur
tout en détruisant satisfaction et retours futurs.

### 4.2 Chaîne de valeur approximative

```text
audience éligible
× exposition pertinente
× conversion honnête en partie
× activation de la boucle
× jours de retour
× sessions par jour actif
× minutes de présence par session
÷ durée de la fenêtre
```

Cette décomposition est diagnostique. Les facteurs interagissent : une meilleure
rétention peut accroître Discovery ; une mauvaise performance peut réduire à la
fois activation, durée et retour ; les amis peuvent augmenter acquisition,
fréquence et qualité de session.

### 4.3 Tous les domaines opérables

| Domaine | Facteurs | Signal utile | Anti-signal |
| --- | --- | --- | --- |
| Découvrabilité | promesse distincte, métadonnées fidèles, audience pertinente | impressions, play through rate et first play bounce rate | miniature trompeuse |
| Accès | chargement, crash, compatibilité appareil/réseau | lancement réussi, temps avant contrôle | utilisateurs perdus avant action |
| Activation | première action, compréhension, premier plaisir | funnel FTUE, boucle qualifiée | tutoriel terminé sans plaisir |
| Valeur centrale | décisions, feedback, cause/effet, maîtrise | modification puis rematch volontaire | répétition pour remplir une barre |
| Retour | aspiration, progression, identité, confiance | D1/D7/D30 par cohorte | connexion motivée par peur de perdre |
| Fréquence | objectifs naturels, amis, nouveauté pertinente | jours joués par utilisateur | obligation quotidienne |
| Durée | arcs complets, variété, coopération | durée de session Roblox + part interne de sessions de valeur | AFK, attente, absence de sortie |
| Social | invitation intentionnelle, utilité mutuelle, sécurité | jours de co-play intentionnel | matchmaking compté comme amitié |
| Réactivation | mise à jour, ami, création visitée, nouveau problème | retour de joueurs inactifs | spam de notifications |
| Couverture mondiale | langue, fuseaux, prix, appareils, accessibilité | activation/retour par segment | moyenne globale masquant un segment cassé |
| Fiabilité | FPS, mémoire, réseau, serveur, sauvegarde | crash, erreur, latence, perte | sessions longues dues à blocage |
| Confiance | règles, modération, prix, équité, récupération | satisfaction, plaintes, remboursements | dépense ou temps obtenu par pression |
| Exploitation | bots, alts, fraude, AFK | diagnostic interne séparé après filtrage documenté | présenter le diagnostic filtré comme CCU Roblox |

La source Roblox Creator Docs courante expose huit familles de signaux Home :
play through rate, first play bounce rate, play days per user, playtime per
user, intentional co-play days per user, qualified play sessions per user,
spend days per user et Robux spent per user. Les signaux récurrents sont
segmentés en D1, D2–7 et D8–28 ; le bounce initial distingue notamment les
sessions de moins de 60 secondes et celles de 61 à 180 secondes. Ce sont des
signaux de plateforme susceptibles d’évoluer, pas une spécification du plaisir.
([Roblox Creator Docs — Discovery, source courante](https://github.com/Roblox/creator-docs/blob/main/content/en-us/discovery.md))

## 5. Système KPI par maturité

Les métriques ne sont pas toutes « North Star ». À chaque gate, l’équipe choisit
un à trois résultats primaires, un ou deux moteurs par résultat si nécessaires,
et un ou deux guardrails matériels. Aucun seuil universel n’est fixé sans
baseline ou benchmark comparable. Une métrique Roblox garde son libellé et sa
définition Roblox ; un diagnostic local porte le préfixe `RT1` dans les schémas
et dashboards futurs.

### 5.1 G2–G3 : prouver la boucle

| Rôle | Nom | Type/source | Définition opérationnelle | Décision |
| --- | --- | --- | --- | --- |
| Primaire | `RT1_CausalComprehensionRate` | `INTERNAL METRIC` observation | part des joueurs qui nomment correctement la première faiblesse sans aide orale | simplifier si l’explication vient de l’observateur |
| Primaire | `RT1_MeaningfulChangeRate` | `INTERNAL METRIC` observation | part qui change un élément susceptible de répondre à la cause observée | revoir autopsie/contrôles si modification cosmétique ou aléatoire |
| Primaire | `RT1_VoluntaryRematchRate` | `INTERNAL METRIC` observation | part qui relance après cette modification sans consigne ni récompense obligatoire | pivoter si le désir de retest n’apparaît pas |
| Moteur | `RT1_TimeToFirstValue` | `INTERNAL METRIC` événements | entrée → contrôle, pose, effet et micro-défense | retirer friction avant d’ajouter progression |
| Guardrail | `RT1_CleanExitAndDistress` | `INTERNAL METRIC` observation | sortie possible, cause d’abandon, aide demandée, inconfort | aucun gain ne compense humiliation ou contrainte |
| Guardrail | santé technique | Roblox + logs | crash, FPS, mémoire, erreurs, latence par appareil | résultat produit invalide si l’expérience est techniquement dégradée |

Les seuils provisoires du GDD pour le panel initial restent des critères internes,
pas des benchmarks Roblox.

### 5.2 G4–G6 : prouver le retour et le social

| Rôle | Nom | Type/source | Définition |
| --- | --- | --- | --- |
| Primaire | D1 puis D7 retention | `PLATFORM FACT`, Roblox | définitions de cohortes Roblox inchangées |
| Primaire | Play days per user | `PLATFORM FACT`, Roblox Discovery | jours distincts joués, analysés séparément en D1, D2–7 et D8–28 |
| Primaire | Intentional co-play days per user | `PLATFORM FACT`, Roblox Discovery | jours de co-play intentionnel via join, invitation ou serveur privé, segmentés en D1, D2–7 et D8–28 |
| Diagnostic | `RT1_ReturnedCoreLoopRate` | `INTERNAL METRIC` | parmi les revenus, part ayant commencé une boucle centrale de valeur |
| Diagnostic | `RT1_SharedContributionRate` | `INTERNAL METRIC` | sessions de co-play où au moins deux joueurs contribuent selon le contrat |
| Guardrail | équité solo/social | tests et événements internes | solo viable ; aucun multi-compte ou carry obligatoire avantagé |
| Guardrail | intégrité des données | tests et incidents | aucune perte, duplication, récompense rejouée ou migration silencieuse |

À G4, D1 est le résultat de retour prioritaire ; D7 le remplace comme résultat
principal lorsque les cohortes sont assez mûres. Ils ne sont pas optimisés
simultanément comme une métrique fusionnée.

### 5.3 G7–G9 : exploiter sans dégrader la confiance

| Rôle | Nom | Type/source | Définition |
| --- | --- | --- | --- |
| Primaire | CCU30 moyen observé | Roblox/observabilité, calcul versionné | moyenne du nombre simultané observé sur 30 jours, sans renommage « qualifié » |
| Primaire | D30 retention | `PLATFORM FACT`, Roblox | retour de la cohorte selon la définition Roblox inchangée |
| Primaire | Intentional co-play days per user | `PLATFORM FACT`, Roblox Discovery | fréquence de jeu intentionnel avec amis, segmentée en D1, D2–7 et D8–28 |
| Moteurs | play through rate, first play bounce rate, D1, play days, playtime | Roblox | diagnostics d’acquisition, activation, fréquence et durée |
| Diagnostics | `RT1_ValueSessionShare`, feedback et motifs de sortie | `INTERNAL METRIC` | faisceau séparé ; jamais agrégé en score opaque de « satisfaction » |
| Guardrail | monétisation équitable | audit segmenté | payeurs et non-payeurs conservent agence, progression viable et règles claires |
| Guardrail | bien-être et confiance | enquête, plaintes, remboursements, sortie | absence de pression ; résultat analysé par composante, sans score composite magique |

Les noms `RT1_*` réservent un contrat futur ; ils ne prouvent pas qu’une
instrumentation existe aujourd’hui. Les observations G2/G3 sont manuelles. Les
événements de production exigent le dictionnaire, la taxonomie et le plan de
qualité des données de G6.

Roblox définit D1, D7 et D30 par cohortes de première visite et recommande de
diagnostiquer D1 par la boucle, le FTUE et la performance, puis D7 par la
progression et D30 par les objectifs durables, le contenu et le social.
([Roblox — Rétention](https://create.roblox.com/docs/production/analytics/retention))

## 6. Les douze lois opératoires

Les lois sont des `RULE` de conception. Elles imposent une direction et des
interdictions ; elles ne prédisent pas un niveau de rétention.

1. **Promesse avant profondeur** : l’image, le titre et les dix premières
   secondes montrent la même expérience réelle.
2. **Action avant explication** : apprendre par une action sûre et visible.
3. **Un verbe, plusieurs conséquences** : enrichir les interactions avant les
   commandes.
4. **Autonomie, compétence, relation** : offrir choix réel, progression de
   maîtrise et utilité mutuelle. La théorie de l’autodétermination soutient ce
   cadre motivationnel sans prouver la rétention du jeu. ([Ryan & Deci,
   2000](https://selfdeterminationtheory.org/SDT/documents/2000_RyanDeci_SDT.pdf))
5. **Difficulté informative** : créer des problèmes contrables, pas de
   l’humiliation ou seulement davantage de santé.
6. **Chaque action répond** : anticipation, action, effet et conséquence restent
   perceptibles.
7. **Trois horizons** : valeur maintenant, objectif de prochaine session,
   identité durable.
8. **Prochain pas visible** : montrer une aspiration atteignable sans transformer
   l’avenir en checklist infinie.
9. **Surprise équitable** : randomiser les situations, jamais la dignité ou le
   portefeuille.
10. **Les joueurs créent de la variété** : interaction utile, création et remix
    sous permissions sûres.
11. **Identité avant inventaire** : ce que le joueur construit et devient compte
    davantage que le volume accumulé.
12. **Session complète** : intention, montée, décision, climax, résolution,
    trace et sortie propre.

## 7. Catalogue opérationnel des effets comportementaux

Ce catalogue couvre les effets pertinents identifiés dans les analyses fournies.
Il n’est ni exhaustif ni une preuve d’efficacité. Chaque ligne reste une
`HYPOTHESIS` locale. Niveau de support documentaire :

- `B` : source primaire générale examinée, aucune preuve Roblox Top 1 ;
- `C` : heuristique issue des analyses fournies ou de la pratique de design,
  sans source primaire spécifique enregistrée ici.

Aucun niveau `A` n’est attribué : aucune ligne n’est prouvée causalement pour ce
jeu.

| Effet ou heuristique | Support | Usage candidat | Dérive interdite | Preuve locale attendue |
| --- | --- | --- | --- | --- |
| Goal-gradient | `B` | progression exacte, sous-objectifs utiles | déplacer la cible ou créer un faux « presque fini » | effort accru sans frustration ni abandon aval |
| Endowed progress | `B`, même famille expérimentale | offrir le premier outil réellement utile | fausse avance suivie d’un grind gonflé | activation supérieure et compréhension conservée |
| Information gap | `B` | question claire, menace partiellement lisible | mystère opaque ou récompense cachée payante | curiosité formulée et exploration volontaire |
| Endowment | `C` | base, plan ou compagnon réellement possédé | menacer de retirer l’acquis | attachement sans peur de perte |
| Effet IKEA | `C` | création simple puis améliorable | travail répétitif présenté comme création | diversité des créations et fierté exprimée |
| Réciprocité | `C` | aide, sauvetage, contribution commune | dette sociale ou sollicitation agressive | aide rendue sans exploitation ni obligation |
| Preuve sociale | `C` | montrer activité et créations authentiques | faux compteur, faux joueurs, honte du solo | découverte utile sans convergence forcée |
| Engagement/cohérence | `C` | objectif choisi par le joueur | engagement irréversible ou culpabilisation | reprise volontaire de l’intention choisie |
| Fresh-start | `C` | nouveau cycle accessible et rattrapable | reset punitif ou invalidation du passé | réactivation sans perte ni anxiété |
| Peak-end | `C` | climax lisible et récapitulatif honnête | masquer une session médiocre par une récompense | souvenir causal et intention de retour |
| Progressive disclosure | `C`, heuristique UX | révéler la profondeur après maîtrise | cacher prix, risque ou règle importante | moins d’erreurs sans perte d’agence |
| Defaults | `C`, règle de sûreté | réglage sûr, accessible et réversible | opt-in trompeur, dépense ou partage par défaut | choix compris et facilement modifiable |
| Anchoring/contraste | `C` | comparer des stratégies avec mêmes règles | prix barré fictif ou option leurre | décision mieux comprise, pas seulement déplacée |
| Statut/reconnaissance | `C` | maîtrise, aide, création et contribution visibles | classement humiliant ou statut acheté ambigu | pluralité de voies reconnues |
| Rareté | `C` | accomplissement réel ou contenu revenant | rareté mensongère, essentiel irrécupérable | prestige sans peur disproportionnée |
| Streak | `C` | trace positive, rattrapage et protection | perte de puissance ou acquis après absence | retour additionnel sans anxiété déclarée |
| Loss aversion | `C`, utilisé seulement pour protéger | protéger, prévenir, restaurer | menacer sauvegarde, progression ou groupe | confiance et récupération accrues |
| Récompense variable | `C`, haut risque | variété gratuite avec bornes et garantie | near-miss, achat de chance, répétition sans borne | surprise sans dépense ni progression bloquée |
| Sunk cost | `C`, anti-pattern uniquement | aucun usage comme moteur | rendre l’arrêt douloureux parce que beaucoup fut investi | départ propre et retour motivé par l’avenir |
| Valeur immédiate | `C`, heuristique produit | feedback et première utilité rapides | crédit, dette ou coût futur dissimulé | compréhension des conséquences différées |

L’effet goal-gradient a été observé dans des programmes de récompense, y compris
lorsqu’une avance initiale rend la progression perçue plus proche ; cela ne
justifie jamais une fausse progression. ([Kivetz, Urminsky & Zheng,
2006](https://home.uchicago.edu/ourminsky/Goal-Gradient_Illusionary_Goal_Progress.pdf))
L’information gap décrit une curiosité créée par un manque d’information
spécifique et perceptible, pas par la confusion. ([Loewenstein,
1994](https://www.cmu.edu/dietrich/sds/docs/loewenstein/PsychofCuriosity.pdf))

## 8. Leviers à haut risque

Les leviers suivants exigent un test explicite de dommage, pas seulement une
mesure de conversion :

- **récompenses variables** : situations gratuites et garanties bornées
  seulement ; aucune progression essentielle derrière le hasard ;
- **FOMO** : calendrier honnête, durée raisonnable, retour annoncé et rattrapage ;
- **streaks** : jamais de perte d’acquis, puissance ou statut essentiel ;
- **notifications** : opt-in compréhensible, fréquence bornée, événement
  réellement utile ;
- **pression sociale** : aucune pénalité imposée à des amis ou à une guilde à
  cause d’une absence ;
- **monétisation** : achat clair et délibéré, aucune frustration fabriquée,
  aucun faux prix ou faux compte à rebours ;
- **hasard payant** : non présumé. S’il est un jour proposé, G7, conformité,
  probabilités réelles et `PolicyService` s’appliquent. Roblox exige notamment
  les résultats possibles et leurs probabilités numériques pour les objets
  aléatoires payants. ([Roblox — Paid random
  items](https://create.roblox.com/docs/production/monetization/paid-random-items))

Un levier échoue même si une métrique monte lorsqu’il augmente tromperie,
regret, anxiété, dépenses non intentionnelles, conflits sociaux, incapacité à
s’arrêter ou exclusion d’un segment vulnérable.

## 9. Portefeuille d’innovation priorisé

Chaque signature est une `HYPOTHESIS`, pas une promesse de roadmap.

| Ordre | ID / signature | Statut | Entrée autorisée | Plus petit test | Continuer si | Tuer/pivoter si |
| --- | --- | --- | --- | --- | --- | --- |
| P0a | `H-FAILURE-001` / `Every Failure Teaches` | `TESTING` via boucle actuelle | G2 `PASS TECHNIQUE` enregistré ; revalidation du worktree puis preuve G3 | première brèche factuelle + autopsie + modification + rematch | cause comprise et modification cohérente sans aide | l’autopsie dicte, n’éclaire rien ou ne crée aucun désir de retest |
| P0b | `H-HORDE-001` / `The Horde Learns` | `UNTESTED` | seulement après signal P0a suffisant et protocole G3 accepté | une dépendance, un éclaireur, une réponse télégraphiée | adaptation reconnue, juste, limitée et contrable | elle paraît aléatoire, omnisciente, punitive ou n’ajoute pas de meilleure décision |
| P1a | `H-FORTRESS-001` / `The Living Fortress` | `DEFERRED` | G3 passé ; contrat minimal séparé | deux sous-systèmes qui interagissent | plusieurs architectures viables et racontables | gestion devient corvée ou solution unique |
| P1b | `H-SOCIAL-001` / `Answer the Call` | `DEFERRED` | G5 ouvert | appel volontaire + permission + contribution visible | valeur bilatérale sans solo puni | griefing, carry obligatoire ou multi-compte |
| P2 | `H-PREPARE-001` / `Prepare for Tomorrow` | `DEFERRED` | G3 passé et besoin de retour explicitement choisi | une menace et deux expéditions aux réponses différentes | choix compris et utilisé dans la défense | farming choisi pour rendement brut seulement |

La thèse long terme, seulement si les hypothèses séquentielles passent, est :

> **Une forteresse vivante confrontée à une horde limitée qui apprend, puis une
> autopsie qui rend chaque échec utile.**

`H-FAILURE-001` est la seule hypothèse produit actuellement prioritaire.
`H-HORDE-001` n’est pas une seconde P0 parallèle : elle est une expérience
subordonnée. Les signatures P1/P2 sont interdites d’implémentation avant leur
entrée explicite. L’ordre vient de la réduction d’incertitude, pas de leur
attrait conceptuel.

## 10. Rejouabilité systémique

**Statut : `HYPOTHESIS H-REPLAY-001 — UNTESTED`.** Les sept sources ci-dessous
sont un modèle de conception à comparer aux comportements réels, pas une recette
de rejouabilité.

Un jeu simple reste profond lorsque la variété vient de relations, pas d’une
liste infinie de contenu :

1. **combinaisons** entre quelques éléments ;
2. **décisions situatives** sans réponse toujours dominante ;
3. **expression de compétence** observable ;
4. **incertitude contrôlable** que l’information et la préparation réduisent ;
5. **interactions sociales** qui changent les possibilités ;
6. **transformation persistante** qui porte identité et mémoire ;
7. **LiveOps systémique** réutilisant les mêmes briques.

Une nouvelle pièce doit idéalement interagir avec au moins trois éléments
existants, créer un compromis et être contrable. Une nouvelle région ajoute une
règle ; un nouvel ennemi ajoute une décision ; un événement recompose le
système. Le contenu isolé qui ne fait qu’ajouter des statistiques est rejeté.

## 11. Horloges de valeur

**Statut : `HYPOTHESIS H-PACING-001 — UNTESTED`.** Les intervalles sont des
plages de prototypage. Aucun n’est un seuil psychologique universel.

| Rythme | Valeur attendue | Exemple projet | Guardrail |
| --- | --- | --- | --- |
| chaque seconde | contrôle et information | pose, tir, impact, menace | aucun bruit visuel masquant la cause |
| 20–60 secondes | décision et mini-résultat | route, crise, réparation | pas de micro-récompense automatique vide |
| 3–5 minutes | boucle partielle et révélation | première brèche, nouvelle interaction | pas d’attente obligatoire |
| 8–20 minutes | arc complet | défense, climax, autopsie, sortie | durée adaptable, point de sortie clair |
| prochaine session | intention concrète | corriger une faiblesse | pas de deadline punitive |
| semaine | recombinaison | mutation ou défi | cadence compatible avec l’équipe |
| saison | aspiration durable | nouvelle règle ou identité | acquis préservés, retour possible |

Roblox recommande un FTUE court, centré sur l’essentiel et l’accès rapide au
plaisir, puis des objectifs courts, moyens et longs. ([Roblox —
Onboarding](https://create.roblox.com/docs/production/game-design/onboarding))
Pour LiveOps, la cadence doit correspondre aux capacités réelles de l’équipe et
réutiliser les systèmes existants. ([Roblox — LiveOps
essentials](https://create.roblox.com/docs/production/game-design/liveops-essentials))

## 12. Protocole d’expérimentation

Chaque proposition utilise une fiche contenant :

1. **population et situation** ;
2. **comportement attendu**, pas seulement sentiment déclaré ;
3. **mécanisme supposé** ;
4. **une métrique primaire** ;
5. **un ou deux diagnostics** ;
6. **un ou deux guardrails** ;
7. **contre-factuel ou baseline** ;
8. **durée et taille minimales justifiées** ;
9. **décision `CONTINUE`, `MODIFY`, `PIVOT` ou `STOP`** ;
10. **preuve conservée**, y compris résultat négatif.

Ordre de preuve :

```text
test déterministe
→ observation qualitative non briefée
→ playtest comparatif
→ cohorte instrumentée
→ expérience contrôlée lorsque le trafic le permet
```

Une corrélation entre durée et retour ne prouve pas que prolonger la session
cause le retour. Une hausse de CCU après une mise à jour peut venir de
l’acquisition, de la saisonnalité, d’amis, d’une panne concurrente ou d’un
changement Discovery. Segmenter par appareil, langue, pays, source, cohorte,
version, solo/groupe et exposition expérimentale avant de conclure.

## 13. Checklist de décision feature

Avant d’ajouter une feature de « rétention », répondre `YES` à toutes les lignes
applicables :

- renforce-t-elle la boucle préparer → tester → comprendre → modifier ?
- ajoute-t-elle une décision plutôt qu’une obligation ?
- reste-t-elle explicable en une phrase joueur ?
- produit-elle de la profondeur avec des systèmes existants ?
- possède-t-elle une hypothèse falsifiable et une métrique de décision ?
- possède-t-elle un guardrail de confiance ou de bien-être ?
- respecte-t-elle mobile, solo, serveur autoritaire et sortie propre ?
- est-elle autorisée par le stage gate actuel ?
- peut-elle être supprimée ou ajustée sans perdre les acquis ?
- sa réussite signifie-t-elle davantage que temps, clics ou dépenses bruts ?

Un `NO` bloque l’implémentation ou exige une dérogation explicite. Un `UNKNOWN`
reste `UNKNOWN`.

## 14. Décision finale

La stratégie n’est pas d’empiler toutes les motivations et tous les biais. Elle
est de tester d’abord une seule proposition : un échec compris produit-il une
modification puis un rematch volontaire ? Les autres motivations et signatures
ne sont conservées que si elles améliorent ensuite un comportement nommé sans
dégrader les guardrails.

> **Le CCU durable est la conséquence agrégée de joueurs pertinents qui entrent,
> trouvent rapidement une valeur réelle, reviennent librement, jouent parfois
> ensemble et font confiance au jeu.**

Le prochain travail autorisé reste la correction et la revalidation du
worktree sur le périmètre G2, puis la preuve humaine G3.
Persistance, social large, analytics de production, économie et LiveOps restent
soumis aux stage gates existants.
