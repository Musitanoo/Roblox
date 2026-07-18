# ADR-0002 — Dérogation au gate participant G3

| Champ | Valeur |
| --- | --- |
| ID | `ADR-0002` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 1.0.0 |
| Propriétaire / approbateur | Founder |
| Scope | Séquencement produit après Build Loop 0.3 en l'absence durable de participants non briefés |
| Source | Décision explicite du founder du 2026-07-18 |
| Remplace | Obligation de fermer G3 avant de préparer la slice Action 0.4.1 |
| Date de décision | 2026-07-18 |
| Dernière revue | 2026-07-18 |
| Revue suivante | Participants représentatifs disponibles, résultat joueur contradictoire, ou préparation d'un lancement externe |

## Contexte

G3 devait mesurer auprès de joueurs représentatifs non briefés la boucle
comprendre → modifier → relancer. Aucun participant ne sera disponible dans
l'horizon de développement actuel. Conserver G3 comme condition d'entrée
bloquante arrêterait le développement sans produire la preuve manquante.

La Build Loop 0.3 possède une preuve technique enregistrée T01–T32. Cette preuve
ne mesure ni compréhension humaine, ni confort, ni désir de rematch.

## Décision

1. L'exécution participant de G3 est `WAIVED_BY_FOUNDER` pour le séquencement
   interne du développement.
2. La preuve joueur G3 reste `UNKNOWN`. La dérogation n'est ni un `PASS`, ni un
   `PASS PRODUIT`.
3. Action 0.4.1 devient la prochaine slice admissible à l'acceptation et à une
   implémentation séquencée. Son contrat `IN_REVIEW` doit encore être accepté
   avant l'implémentation ; la dérogation n'accepte pas silencieusement tout son
   scope.
4. Progression, persistance, social, analytics, économie, monétisation, LiveOps
   et lancement restent soumis à leurs propres contrats, risques et gates.
5. Toute affirmation de compréhension, de rétention, de différenciation ou de
   valeur produit demeure interdite sans preuve représentative.
6. Les tests founder, automatisés et Studio peuvent produire des verdicts
   techniques seulement.

## Risque accepté

Le founder accepte explicitement de poursuivre le développement sans savoir si
un nouveau joueur comprend la faiblesse, effectue une modification pertinente
et relance volontairement. Le risque `R-001` reste matériel et doit accompagner
toute décision de scope ou de lancement.

## Limites

- Cette dérogation autorise uniquement le passage de la baseline Build 0.3 vers
  la décision Action 0.4.1.
- Elle n'ouvre pas automatiquement G4–G9.
- Elle n'autorise aucune publication de production.
- Elle ne permet pas de remplacer des observations absentes par des métriques
  synthétiques, des captures ou une opinion du founder.
- Une feature client-triggerable reste bloquée sans ses contrôles de sécurité,
  tests hostiles et preuve runtime.

## Alternatives

### Arrêter le développement jusqu'à disponibilité d'un panel

Rejeté par le founder : aucun participant ne sera disponible et l'attente
n'apporterait pas de preuve supplémentaire.

### Déclarer G3 `PASS`

Rejeté : cela falsifierait la preuve et rendrait les décisions futures
inexploitables.

### Ouvrir toutes les slices futures

Rejeté : la dérogation concerne une dépendance précise et ne supprime pas les
risques de données, sécurité, performance, économie ou exploitation.

## Conséquences

- La roadmap distingue désormais état de preuve et décision de séquencement.
- `PD-01` reste ouvert avec preuve `UNKNOWN`, mais n'est plus le blocker
  opérationnel immédiat.
- La prochaine décision produit est l'acceptation, la réduction ou le rejet
  d'Action 0.4.1.
- Tout rapport futur doit rappeler la dérogation lorsqu'il dépend du passage de
  G3.

## Récupération et réévaluation

La dérogation est réversible sans migration de données. Si des participants
deviennent disponibles, rouvrir G3 avec un build figé et un protocole accepté.
Avant tout lancement externe, réévaluer explicitement `R-001` et décider si une
preuve humaine devient obligatoire.
