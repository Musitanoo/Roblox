# Intake et intégration de `tmp/docs` — ExecPlan

## Outcome

Lire intégralement les 25 fichiers fournis sous `tmp/docs`, distinguer les
apports durables des doublons et des systèmes prématurés, puis intégrer
uniquement les documents qui réduisent un risque actuel ou préparent un gate
déjà défini. Toute intégration conserve les statuts réels : aucun fichier
temporaire ne devient canonique par simple copie, aucune fonctionnalité n'est
autorisée et aucun verdict non observé ne devient `PASS`.

## Sélection

Quatre sources sont retenues après comparaison avec le corpus :

1. `PERSISTENCE_OPERATIONS_RUNBOOK_0.6.md` → runbook 0.6.1 aligné sur le contrat
   Persistence, avec lock opérateur et recovery sans ancienne metadata.
2. `PERFORMANCE_BUDGETS_1.0.md` → configuration 1.0.1 provisoire, mesurable et
   conditionnée à un appareil de référence réel.
3. `ANALYTICS_EVENT_CATALOG_0.9.md` → contrat candidat 0.9.1 limité à G6, sans
   émission Analytics en Studio ni activation de funnels futurs.
4. `BUG_TRIAGE_TEMPLATE.md` → modèle actif, reproductible et sans données
   personnelles inutiles.

Un relevé `EVIDENCE` enregistre la décision pour les 25 fichiers. Les autres
sources restent dans `tmp/` : elles sont soit dupliquées, soit dépendantes de
G5–G9, soit incompatibles avec les versions actuelles et ne sont donc pas
promues dans `docs/`.

## Acceptance criteria

1. Les 25 fichiers ont une décision `INTEGRATE`, `DEFER` ou `REJECT` avec une
   justification précise.
2. Les quatre documents retenus possèdent métadonnées, autorité, version,
   dépendances, scope, interdictions et déclencheur de revue.
3. Le runbook Persistence est cohérent avec 0.6.1, T01–T112, les métadonnées
   compactes, les écritures ambiguës, les UserIds, le lock opérateur et les
   snapshots privilégiés.
4. Les budgets de performance sont identifiés comme cibles projet provisoires,
   jamais comme limites Roblox, et un résultat sans appareil/scénario/capture
   reste `UNKNOWN`.
5. Le catalogue Analytics distingue événements candidats, actifs et réservés ;
   les événements officiels restent serveur-only et published-only.
6. Le modèle de bug capture reproduction, environnement, impact, preuve,
   sécurité, régression et vérification sans PII.
7. Navigation, registre, roadmap, risques, contrat Persistence et sources
   officielles pointent vers les nouveaux documents sans ouvrir G4, G6 ou G9.
8. Les formats Markdown passent UTF-8, liens, titres, tables, blocs et espaces ;
   le catalogue garde une taxonomie bornée et le runbook ne contient aucun
   secret ou identifiant réel.
9. `git diff --check` et `scripts/check.ps1` passent. Studio est non applicable
   à cette intégration documentaire.

## Intended files

- Ajouter `docs/PERSISTENCE_OPERATIONS_RUNBOOK_0_6.md`.
- Ajouter `docs/PERFORMANCE_BUDGETS_1_0.md`.
- Ajouter `docs/ANALYTICS_EVENT_CATALOG_0_9.md`.
- Ajouter `docs/templates/BUG_TRIAGE_TEMPLATE.md`.
- Ajouter `docs/references/TMP_DOCS_INTAKE_2026-07-15.md`.
- Modifier les index et contrats directement concernés.
- Modifier ce plan et le registre documentaire.

## Verification

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
git diff --check
git status --short
```

Ajouter un audit déterministe du corpus Markdown, de l'enregistrement de tous
les documents et des séquences de tests 0.4.1–0.6.1. Vérifier séparément que les
25 fichiers source ont tous été classés une fois.

## Recovery

Les sources sous `tmp/docs` restent intactes. Les documents intégrés sont de
nouveaux fichiers ou des liens documentaires réversibles. En cas de conflit,
retirer l'intégration concernée et conserver la source temporaire ; ne jamais
modifier un rapport historique ni contourner un gate pour préserver un nouveau
document.

## Progress

- 2026-07-15 : 25/25 fichiers lus intégralement, y compris les quatre grandes
  spécifications 0.7–1.0 et leurs sections tronquées relues par plages.
- 2026-07-15 : comparaison des doublons, dépendances, gates et actifs existants
  terminée ; quatre documents retenus.
- 2026-07-15 : les quatre documents retenus ont été réécrits, reliés au corpus
  canonique et enregistrés sans promouvoir leur statut au-delà des preuves.
- 2026-07-15 : couverture d'intake `25/25` (`4 INTEGRATE`, `14 DEFER`,
  `7 REJECT`), formats JSON/CSV temporaires, liens, UTF-8, titres, fences et
  registre documentaire vérifiés.
- 2026-07-15 : séquences contractuelles T01–T63, T01–T75 et T01–T112
  intactes ; `git diff --check` et `scripts/check.ps1` réussis.

## Decisions

- Ne pas promouvoir Expedition 0.7, Social 0.8, Retention 0.9 ou Beta 1.0 : ils
  supposent des gates fermés et des schémas V3–V5 inexistants.
- Ne pas importer les checklists `VERIFY_*` : elles dupliquent les Definitions
  of Done et utilisent notamment T50/T65/T90 au lieu de T63/T75/T112.
- Ne pas importer la bible Art & Audio : le territoire visuel n'est pas encore
  sélectionné par le plan Art Direction actif.
- Ne pas importer le CSV d'assets : `assets-3d/registry/staging.json` et le
  workflow 3D sont déjà les sources de vérité.

## Status

Complete. L'intégration documentaire est terminée ; les gates G4, G6 et G9
restent fermés et aucun résultat runtime n'est revendiqué.
