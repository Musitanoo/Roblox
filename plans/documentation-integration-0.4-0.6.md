# Intégration documentaire des slices 0.4.1–0.6.1 — ExecPlan

## Outcome

Intégrer les contrats candidats Action 0.4.1, Progression 0.5.1 et Persistence
0.6.1 dans toutes les surfaces documentaires qui déterminent leur découverte,
leur autorité, leurs dépendances, leurs gates, leurs risques ou leurs sources.
L'intégration doit former une chaîne navigable du GDD vers la roadmap, les
contrats et les preuves, sans modifier le runtime, réécrire une preuve historique
ni transformer `IN_REVIEW`, `UNKNOWN` ou `BLOCKED` en autorisation ou en `PASS`.

## Scope sélectionné

- `README.md` : état courant et accès au corpus.
- `Roblox_Top_1_Game_Design_Document_v1.0.md` : carte des contrats
  d'implémentation et liens depuis les systèmes concernés.
- `docs/README.md` : parcours, chaîne de dépendances et inconnues.
- `docs/00-governance/DOCUMENT_REGISTER.md` : inventaire et statut du plan.
- `docs/00-governance/ROADMAP_AND_STAGE_GATES.md` : ordre d'autorisation et
  traitement du founder seul testeur.
- `docs/00-governance/RISK_REGISTER.md` : contrôles précis associés aux trois
  contrats.
- `docs/00-governance/GLOSSARY.md` : termes techniques normatifs introduits.
- `docs/references/ROBLOX_OFFICIAL_SOURCES.md` : sources primaires requises par
  les protocoles, l'analytics et la persistance.
- `docs/ACTION_LOOP_0_4.md`, `docs/PROGRESSION_LOOP_0_5.md` et
  `docs/PERSISTENCE_LOOP_0_6.md` : titres, dépendances et liens d'intégration.
- Ce plan.

Les contrats et rapports Defense/Build restent inchangés : ils constituent une
baseline et des preuves historiques. Leur réécriture n'est pas nécessaire pour
découvrir la chaîne suivante et risquerait de mélanger preuve observée et
intégration éditoriale.

## Acceptance criteria

1. Chaque surface nomme les révisions 0.4.1, 0.5.1 et 0.6.1 sans version
   obsolète lorsqu'elle décrit l'état courant.
2. Une chaîne unique et explicite relie Build 0.3 → Action 0.4.1 → Progression
   0.5.1 → Persistence 0.6.1.
3. G3 reste `UNKNOWN` et son exécution humaine `BLOCKED` avec un seul testeur ;
   tout travail anticipé exige une dérogation explicite et bornée.
4. G4 reste fermé ; Progression et Persistence ne deviennent pas autorisées par
   leur simple intégration documentaire.
5. Le GDD distingue vision acceptée et contrats candidats d'implémentation.
6. Le registre des risques pointe vers les contrôles exacts réseau,
   transactionnels et de persistance.
7. Le glossaire ferme les ambiguïtés de `idempotence`, `révision`, `session
   lock`, `sidegrade` et `READ_ONLY`.
8. Le registre des sources couvre Input Action System, frontière client-serveur,
   RemoteEvents, Analytics custom/funnel, DataStore, budgets, limites,
   versioning, manager et Open Cloud.
9. Tous les liens relatifs sont valides ; UTF-8, titres, tables, blocs et espaces
   sont propres ; les documents normatifs restent enregistrés.
10. `git diff --check` et `scripts/check.ps1` passent. Studio est non applicable
    car aucun comportement runtime n'est modifié.

## Verification

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
git diff --check
git status --short
```

Ajouter un audit déterministe sur tout le corpus Markdown : UTF-8 strict,
caractères de remplacement, espaces finaux, titres dupliqués, blocs de code,
liens relatifs, IDs enregistrés et références de versions courantes.

## Recovery

Les modifications sont uniquement Markdown et restent séparables par fichier.
En cas de conflit avec un changement utilisateur, préserver le changement
utilisateur, conserver le statut le plus prudent et retirer uniquement le lien
d'intégration conflictuel. Ne jamais modifier les données brutes ou verdicts
d'un rapport `EVIDENCE` pour satisfaire une cohérence éditoriale.

## Progress

- 2026-07-15 : corpus et références croisées cartographiés ; onze documents et
  ce plan sélectionnés, rapports historiques explicitement exclus.
- 2026-07-15 : GDD 1.0.1, navigation, roadmap, risques, glossaire, sources et
  contrats alignés ; chaîne Build 0.3 → Action 0.4.1 → Progression 0.5.1 →
  Persistence 0.6.1 navigable dans les deux sens.
- 2026-07-15 : audit des 12 fichiers sélectionnés `PASS` ; séquences T01–T63,
  T01–T75 et T01–T112 continues ; aucune référence courante obsolète.
- 2026-07-15 : audit complet des 39 fichiers Markdown du corpus `PASS` pour
  UTF-8, liens relatifs, titres, blocs, espaces valides et enregistrement.
- 2026-07-15 : `git diff --check` et `scripts/check.ps1` `PASS` ; StyLua,
  Selene et Luau LSP sans erreur ni warning.

## Decisions

- Conserver les noms de fichiers 0.4/0.5/0.6 comme identifiants stables, mais
  afficher les révisions patch 0.4.1/0.5.1/0.6.1 dans l'état courant.
- Ajouter au GDD une carte d'application sans élargir sa vision ni faire des
  candidats `IN_REVIEW` une autorité acceptée.
- Traiter le founder seul comme capacité de preuve technique, jamais comme
  substitut à un panel non briefé.

## Status

Complete. Les contrats restent `IN_REVIEW`, G3 reste `UNKNOWN` avec exécution
humaine `BLOCKED`, G4 reste fermé et aucun changement runtime n'a été effectué.
