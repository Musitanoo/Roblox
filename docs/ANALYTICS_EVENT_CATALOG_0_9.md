# Catalogue d'événements Analytics 0.9.1

| Champ | Valeur |
| --- | --- |
| ID | `DATA-CONTRACT-009` |
| Classe | `CONTRACT` de données |
| Cycle de vie | `DRAFT` |
| Version | 0.9.1 |
| Propriétaire / approbateur | Product/Data/Founder |
| Scope | Noms, étapes, champs et QA des événements candidats Roblox Top 1 |
| Source | `tmp/docs/ANALYTICS_EVENT_CATALOG_0.9.md`, corrigé le 2026-07-15 |
| Dépend de | G6, dictionnaire KPI accepté, expérience privée publiée et adapters validés |
| Dernière revue | 2026-07-15 |
| Revue suivante | Entrée G6, changement AnalyticsService, acceptation FTUE ou nouvelle instrumentation |

> Aucun événement officiel de ce catalogue n'est actif. G6 reste fermé. Dans
> Studio, seul un recorder local de test est autorisé ; Roblox indique que les
> funnel/custom events officiels sont émis côté serveur dans une expérience
> publiée. Ce brouillon ne crée ni consentement, ni politique de rétention des
> données, ni preuve de comportement joueur.

## 1. États du catalogue

| État | Signification |
| --- | --- |
| `LOCAL_ONLY` | Événement structuré de test, jamais envoyé à AnalyticsService |
| `CANDIDATE` | Contrat proposé, émission interdite avant acceptation G6 |
| `RESERVED` | Nom préservé pour un futur contrat non accepté ; aucun code actif |
| `ACTIVE` | Autorisé pour un build publié précis après QA et décision enregistrée |
| `RETIRED` | Plus émis ; définition conservée pour interpréter l'historique |

Passer à `ACTIVE` exige un owner, un build de début, une finalité, les champs,
la preuve serveur, le volume attendu, les guardrails et une procédure de retrait.
Un changement d'ordre sémantique crée une nouvelle version ; il ne réécrit pas
un funnel déjà collecté.

## 2. Règles communes

- Émission officielle uniquement côté serveur après résultat autoritaire.
- Le client peut transmettre une intention bornée, jamais un nom d'événement ou
  une valeur Analytics arbitraire.
- Maximum trois custom fields par appel est une limite projet volontaire.
- Valeurs enum whitelistées ; aucun texte libre ou identifiant à cardinalité
  non bornée.
- Interdits dans custom fields : UserId, DisplayName, JobId, place privée,
  requestId, GUID de session, position exacte, payload brut ou erreur libre.
- Les identifiants nécessaires à l'API Roblox sont passés dans leurs paramètres
  dédiés, jamais recopiés comme dimensions analytiques.
- Analytics ne décide jamais d'une récompense, d'un gate ou du gameplay.
- Un échec d'émission est observable mais n'annule pas une transaction gameplay.

## 3. Dictionnaire de champs candidat

| Champ | Valeurs admises |
| --- | --- |
| `InputMode` | `TOUCH`, `KEYBOARD_MOUSE`, `GAMEPAD`, `UNKNOWN` |
| `PartySize` | `1`, `2`, `3`, `4` |
| `ChallengeId` | `CH01`, `CH02`, `CH03` |
| `Difficulty` | `RECRUIT`, `VETERAN`, `ONSLAUGHT` |
| `Result` | `VICTORY`, `DEFEAT`, `ABANDONED`, `ERROR` |
| `ActionMilestone` | Valeurs de la section 5.1 |
| `BlueprintAction` | `VIEWED`, `UNLOCKED`, `USED`, `REJECTED` |
| `Variant` | Valeurs définies par un contrat d'expérience accepté |
| `ReasonCode` | Enum versionnée et bornée propre au système |

Les valeurs inconnues sont rejetées ou mappées vers `UNKNOWN` uniquement lorsque
le contrat du champ l'autorise. Ne jamais convertir une chaîne arbitraire en
nouvelle dimension.

## 4. Funnels candidats

### 4.1 `CoreLoopV1` — `CANDIDATE`

Funnel récurrent via `AnalyticsService:LogFunnelStepEvent()` avec un
`funnelSessionId` GUID généré côté serveur par tentative.

| Step | Name | Preuve serveur minimale |
| ---: | --- | --- |
| 1 | Challenge Viewed | Snapshot du board envoyé au joueur |
| 2 | Challenge Selected | Sélection valide acceptée |
| 3 | Build Changed | Mutation Build post-review acceptée |
| 4 | Challenge Started | Transition autoritaire `STARTING` |
| 5 | Challenge Resolved | `VICTORY` ou `DEFEAT` figé |
| 6 | Review Viewed | Ack borné associé au report existant |
| 7 | Post Review Edit | Mutation valide après ce report |
| 8 | Rematch Or Next Activity | Nouvelle activité autoritaire démarrée |

Ce funnel reste candidat tant que son point de départ et les chemins sans
modification de build ne sont pas validés par un brief G6.

### 4.2 `OnboardingV1` — `RESERVED`

`LogOnboardingFunnelStepEvent()` convient à un funnel one-time et ne requiert
pas de `funnelSessionId`. Les dix étapes proposées par la source temporaire ne
sont pas intégrées comme contrat actif : aucune slice FTUE n'est acceptée. Elles
seront redéfinies à partir du comportement réellement autorisé avant G6.

### 4.3 Noms futurs réservés

| Nom | État | Condition |
| --- | --- | --- |
| `ProgressionLoopV1` | `CANDIDATE` | Progression 0.5.1 acceptée et G6 ouvert |
| `ExpeditionRun` | `RESERVED` | Contrat Expedition accepté |
| `SocialAid` | `RESERVED` | Contrat Social/G5 accepté |

Aucun nom `RESERVED` ne doit apparaître dans le code de production actuel.

## 5. Custom events candidats

### 5.1 `ActionMilestone` — `CANDIDATE`

Valeur numérique : durée depuis le début du challenge en millisecondes, entière,
bornée par la durée maximale du challenge. Champs : `ActionMilestone`,
`ChallengeId`, `PartySize`.

Valeurs `ActionMilestone` :

```text
FIRST_SHOT
FIRST_CONFIRMED_HIT
FIRST_RELOAD
FIRST_REPAIR_STARTED
FIRST_REPAIR_COMPLETED
BLACKOUT_WARNING
BLACKOUT_STARTED
RELAY_REPAIR_STARTED
RELAY_RESTORED
RELAY_BACKUP_TRIGGERED
PLAYER_DOWNED
REVIVE_STARTED
REVIVE_COMPLETED
SOLO_RECOVERY
CHALLENGE_COMPLETED
```

Ces valeurs reprennent les signaux locaux d'Action 0.4.1 tout en limitant la
cardinalité des noms d'événements officiels.

### 5.2 Progression — `CANDIDATE`

| Event name | Valeur | Champs proposés |
| --- | --- | --- |
| `ChallengeResult` | durée en secondes | `ChallengeId`, `Difficulty`, `Result` |
| `MasteryEarned` | nombre de marks nouveaux | `ChallengeId`, `Difficulty`, `PartySize` |
| `BlueprintAction` | coût/0 selon action | `BlueprintAction`, `ChallengeId`, `PartySize` |

Les gains sont loggés après transaction acceptée, jamais à l'intention client.
`ReasonCode` peut remplacer un champ seulement avec enum stable documentée.

### 5.3 Persistence — logs privés, pas custom events joueur

Les événements `PROFILE_*` de Persistence 0.6.1 appartiennent d'abord aux logs
et métriques opérationnels privés. Ils ne sont pas envoyés comme événements
joueur sans finalité G6 séparée. Les logs utilisent un
`profileCorrelationId` opaque et n'incluent jamais le profil complet.

## 6. Recorder Studio

```lua
export type RecordedAnalyticsEvent = {
    adapter: "STUDIO",
    catalogVersion: "0.9.1",
    eventKind: "FUNNEL" | "CUSTOM" | "OPERATIONAL",
    eventName: string,
    funnelSessionId: string?,
    step: number?,
    numericValue: number?,
    fields: { [string]: string },
    serverTimestamp: number,
    sequence: number,
}
```

Le recorder est injecté côté serveur et exporte un artefact de test local. Il
valide ordre, once-only, whitelist, maximum trois champs, types/valeurs bornés et
absence de PII. Il n'appelle pas AnalyticsService et ne prétend pas prouver la
réception par Creator Hub.

## 7. QA avant activation d'un événement

1. Accepter le KPI, la finalité et le propriétaire.
2. Fixer version, build de début, preuve serveur et volume attendu.
3. Exécuter le scénario avec recorder et comparer exactement la séquence.
4. Tester duplications, retries, erreurs adapter et payloads hostiles.
5. Vérifier aucune donnée interdite et aucune dépendance gameplay.
6. Publier uniquement dans une expérience privée autorisée.
7. Confirmer dans Event Viewer, puis après agrégation ; les graphiques peuvent
   nécessiter jusqu'à 24 heures.
8. Enregistrer le verdict, les limites et la décision `ACTIVE` ou rollback.

## 8. Sources revalidées

- [Funnel events](https://create.roblox.com/docs/production/analytics/funnel-events)
- [Custom events](https://create.roblox.com/docs/production/analytics/custom-events)
- [AnalyticsService](https://create.roblox.com/docs/reference/engine/classes/AnalyticsService)

Sources consultées le 2026-07-15. Revalidation obligatoire avant G6 ou toute
émission publiée.
