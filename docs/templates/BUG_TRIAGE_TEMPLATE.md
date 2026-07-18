# Modèle de triage de bug

| Champ | Valeur |
| --- | --- |
| ID | `TPL-BUG` |
| Classe | `REFERENCE` |
| Cycle de vie | `ACTIVE` |
| Version | 1.0.0 |
| Propriétaire | Engineering |
| Scope | Rapport, triage, correction et vérification d'un défaut reproductible |
| Source | `tmp/docs/BUG_TRIAGE_TEMPLATE.md`, corrigé le 2026-07-15 |
| Dernière revue | 2026-07-15 |
| Revue suivante | Rapport ambigu, incident, nouvelle classe de preuve ou workflow de tickets |

Copier ce modèle dans le système de suivi ou le rapport concerné. Supprimer les
sections non applicables en indiquant pourquoi. Ne jamais joindre credentials,
cookies, profils complets, UserIds bruts, conversations ou données personnelles
inutiles.

## 1. Identification

```text
Bug ID:
Title:
Reported at UTC:
Reporter/owner:
Status: NEW | TRIAGED | IN_PROGRESS | FIXED | VERIFIED | CLOSED
Build/commit:
Last known good build:
First known bad build:
Place version/universe alias:
Related contract/test/risk:
```

## 2. Sévérité et priorité

Cocher une seule sévérité et expliquer l'impact observable.

- [ ] `Sev0` — perte/corruption de données, duplication/exploit critique,
  indisponibilité générale ou risque grave pour les joueurs ; stop-ship.
- [ ] `Sev1` — boucle centrale, chargement, sauvegarde ou appareil prioritaire
  bloqué sans contournement sûr.
- [ ] `Sev2` — fonctionnalité importante dégradée avec contournement borné.
- [ ] `Sev3` — défaut mineur, cosmétique ou de polish sans impact critique.

```text
Severity rationale:
Priority:
Affected users/scope:
Frequency: ALWAYS | FREQUENT | INTERMITTENT | ONCE | UNKNOWN
Regression: YES | NO | UNKNOWN
Stop-ship: YES | NO
```

## 3. Environnement

```text
Platform/device/model:
OS:
Input mode:
Locale:
Viewport/graphics quality:
Party size and role:
Network latency/jitter/loss:
Studio mode or published audience:
Client/Server DataModel:
Script Sync confirmed: PASS | FAIL | UNKNOWN | N/A
Profile schema/revision correlation (no raw profile):
Feature flags/config version:
```

## 4. Préconditions et reproduction minimale

```text
Preconditions:
Seed/fixture (non-sensitive):
Reproduction rate: __ / __ attempts
```

1. Étape :
2. Étape :
3. Étape :

Réduire les étapes au plus petit scénario qui reproduit le défaut. Indiquer le
moment exact où l'observation diverge du résultat attendu.

## 5. Attendu et observé

```text
Expected behavior and acceptance criterion:
Observed behavior:
Error/reason code:
Player-visible impact:
Data/economy/security impact:
Cleanup or residual state:
```

## 6. Preuves

- Client Output :
- Server Output :
- Capture vidéo/screenshot :
- MicroProfiler/performance/network artifact :
- Runtime instance/state inspection :
- DataStore/metadata summary privé et expurgé :
- Test automatisé ou fixture :

Une capture seule ne prouve pas la logique. Expurger secrets, IDs sensibles et
données personnelles avant partage.

## 7. Triage technique

```text
Suspected component/owner:
Confirmed cause or hypothesis:
Security boundary affected:
Persistence/migration risk:
Performance risk:
Can reproduce before fix: PASS | FAIL | UNKNOWN
Smallest safe remediation:
Workaround and limitations:
Rollback/kill switch:
Related or duplicate bugs:
```

Séparer la cause confirmée des hypothèses. Un diagnostic n'autorise pas à
implémenter une correction hors scope sans décision correspondante.

## 8. Correction

```text
Fix build/commit:
Files/Instances changed:
Behavior changed:
Migration or compatibility:
Regression test added:
Unrelated changes: NONE | LIST
```

## 9. Vérification indépendante

```text
Verifier:
Environment/build:
Original reproduction after fix:
Regression test:
Adjacent scenarios:
Client Output:
Server Output:
Cleanup:
Result: PASS | FAIL | PARTIAL | BLOCKED | UNKNOWN
Evidence links:
Remaining risks:
```

`FIXED` signifie que la modification existe. `VERIFIED` exige une preuve sur le
build corrigé. Un check skipped ou un scénario non reproduit reste explicitement
`UNKNOWN`/`BLOCKED` et ne devient pas `PASS`.
