# Budgets de performance 1.0.1

| Champ | Valeur |
| --- | --- |
| ID | `CONFIG-PERF-001` |
| Classe | `CONFIG` |
| Cycle de vie | `IN_REVIEW` |
| Version | 1.0.1 |
| Propriétaire / approbateur | Engineering/Founder |
| Scope | Cibles internes, protocole de mesure et artefacts de performance |
| Source | `tmp/docs/PERFORMANCE_BUDGETS_1.0.md`, corrigé le 2026-07-15 |
| Dernière revue | 2026-07-15 |
| Revue suivante | Appareil baseline choisi, nouvelle slice runtime, changement de charge ou première mesure réelle |

> Ces valeurs sont des cibles projet provisoires, jamais des limites Roblox ni
> une preuve actuelle. Le baseline mobile réel n'est pas encore nommé et les
> résultats sont donc `UNKNOWN`. L'émulateur Studio valide layout/input, pas la
> mémoire, la chauffe ou les performances d'un appareil physique.

## 1. Règles d'acceptation

Un résultat de performance indique obligatoirement : build/commit, place
version, scénario, durée, appareil exact, OS, qualité graphique, input, nombre
de joueurs, ennemis/instances, réseau, p50/p95/pire frame, mémoire début/fin,
artefacts et conditions thermiques.

- Aucun screenshot FPS isolé ne reçoit `PASS`.
- Une moyenne ne masque pas un p95 ou un hitch bloquant.
- Studio, desktop et appareil mobile ne se substituent pas entre eux.
- Une cible non applicable est `SKIPPED` avec motif, jamais `PASS`.
- Une mesure après modification est comparée à une baseline prise avec le même
  protocole et la même charge.
- Toute optimisation préserve le comportement et les tests du contrat actif.

## 2. Matrice appareils

| Tier | Baseline exigée | État |
| --- | --- | --- |
| Mobile faible | Appareil Android physique représentant le bas de cible, modèle/SoC/RAM à enregistrer | `UNKNOWN` — non sélectionné |
| Mobile principal | Android ou iPhone physique représentatif, modèle/SoC/RAM à enregistrer | `UNKNOWN` — non sélectionné |
| Desktop développement | Machine Windows actuelle, configuration enregistrée dans l'artefact | Disponible pour diagnostic, pas baseline mobile |
| Manette | Chemin contrôleur sur appareil compatible | Preuve input séparée de la performance |

Le choix des appareils est une décision de configuration versionnée. Après
trafic réel, la matrice est réévaluée à partir des appareils réellement utilisés.

## 3. Cibles de frame provisoires

| Tier | Cible soutenue | p95 frame time | Interprétation |
| --- | ---: | ---: | --- |
| Mobile faible | 30 FPS | ≤ 33,3 ms | Gate minimal proposé, à confirmer sur baseline réelle |
| Mobile principal | 45 FPS ou mieux | ≤ 22,2 ms | La qualité adaptative et l'appareil sont consignés |
| Desktop de référence | 60 FPS | ≤ 16,7 ms | Diagnostic/régression, pas preuve mobile |

Cible provisoire de hitch gameplay : aucun frame time supérieur à 500 ms hors
chargement explicitement isolé. Un seul hitch de cette ampleur produit au mieux
`PARTIAL` jusqu'à diagnostic ; il n'est pas dilué dans une moyenne.

## 4. Scénarios et applicabilité

| Scénario | Gate/contrat | Charge contrôlée | État actuel |
| --- | --- | --- | --- |
| Build dense + edit/undo/redo | Build 0.3 | Plan proche des budgets autorisés | Applicable |
| Dix rematchs | Defense 0.2/Build 0.3 | Même seed/config et comptages avant/après | Applicable |
| Fight/Repair/Blackout | Action 0.4.1 | Charge définie par la sous-tranche autorisée | Fermé sans dérogation |
| Progression UI/transactions | Progression 0.5.1 | Aucun DataStore | G4 fermé |
| Persistence/reconnexion | Persistence 0.6.1 | Univers Data Test isolé | G4 fermé |
| CH03 quatre joueurs | Futur social | Contrat et cap ennemis acceptés requis | G5 fermé |
| Expédition/overload | Future slice Expedition | Aucun contrat accepté | Non applicable |

Les budgets ne créent ni ennemi, ni taille de groupe, ni scénario. Les caps de
charge viennent du contrat runtime accepté et sont enregistrés dans l'artefact.

## 5. Mémoire et stabilité

Cibles provisoires : zéro OOM/crash, aucune croissance monotone inexpliquée et
moins de 15 % de croissance de la mémoire mesurée entre l'état stabilisé initial
et la fin de dix cycles identiques. La comparaison exclut le warm-up initial et
documente le garbage collection ; elle ne prétend pas que toute hausse est une
fuite.

À chaque reset/rematch, compter au minimum : Runtime, ennemis, défenses rendues,
connexions instrumentées, tâches longues, UI/ghosts et instances temporaires.
Une dérive continue bloque le `PASS` même si le FPS reste acceptable.

## 6. Réseau

Seuils de diagnostic initiaux, à calibrer avant acceptation :

```text
average receive per client <= 50 KB/s
average send per client    <= 35 KB/s
short peak                 <= 150 KB/s
```

Ils ne sont pas des limites plateforme. Capturer moyenne, p95/pic, durée,
direction, nombre de joueurs et scénario. Tester au minimum réseau normal puis
150 ms ; ajouter jitter/perte seulement lorsque le contrat de la slice l'exige.
L'idempotence et l'autorité serveur restent des critères fonctionnels séparés.

## 7. Chargement et contrôle

Cibles futures à mesurer dans une expérience publiée représentative : médiane
join-to-control ≤ 8 s et p90 ≤ 15 s. Avant profil/persistance/FTUE acceptés, ces
valeurs restent des hypothèses et ne bloquent pas Build 0.3.

Décomposer : connexion, profil, personnage, UI, streaming/synchronisation et
première action. Aucun indicateur visuel ne prétend qu'une étape est terminée
avant confirmation.

## 8. Budgets de travail runtime

- préférer événements et fréquences bornées au travail par frame ;
- aucun scan global non borné ;
- files, raycasts, pathfinding, particules, sons et tâches possèdent des caps ;
- les caps ennemis/effets proviennent du contrat actif, pas de ce document ;
- pooling uniquement après mesure d'un coût réel et avec cleanup vérifié ;
- collisions, streaming et LOD sont mesurés dans la scène applicable ;
- la réduction de qualité conserve warnings, objectifs et accessibilité.

## 9. Protocole de capture

1. Synchroniser et confirmer la place/build visés.
2. Fermer les outils parasites et fixer qualité/résolution.
3. Enregistrer l'état initial et effectuer un warm-up reproductible.
4. Exécuter le scénario complet pendant une durée suffisante ; sur mobile,
   inclure 10–15 minutes pour observer la chauffe lorsque applicable.
5. Capturer Performance Stats, Developer Console et MicroProfiler sur le côté
   client/serveur pertinent.
6. Refaire au moins trois runs comparables ; conserver tous les résultats.
7. Inspecter les anomalies, Output et comptages de cleanup.
8. Produire verdict et comparaison baseline ; ne pas optimiser par intuition.

## 10. Artefact minimal

```text
measurementId:
build/commit/placeVersion:
scenario and acceptance criterion:
device/OS/SoC/RAM:
graphics/resolution/input:
players/enemies/instances:
network condition:
duration/warm-up:
p50/p95/worst frame time:
memory start/end/delta:
network average/p95/peak:
hitches/crashes/OOM:
client/server Output:
MicroProfiler and screenshots/exports:
expected/observed:
cleanup counts:
verdict:
limits and follow-up:
```

Ce document ne reçoit `ACCEPTED` qu'après choix des appareils baseline et une
première campagne de mesures reproductibles. Jusque-là, ses chiffres guident la
collecte et ne prouvent aucune performance actuelle.
