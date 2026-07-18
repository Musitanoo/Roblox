# ExecPlan — Audit exhaustif et remise en cohérence du dépôt

## Outcome

Auditer le dépôt `C:\Project\Roblox` dans son état de travail réel, attribuer
une disposition vérifiable à chaque fichier, corriger les défauts confirmés
sans écraser les changements préexistants, puis produire une preuve consolidée
sur :

- la documentation, ses autorités, ses registres et ses gates ;
- le jeu Luau, les contrats client/serveur, les tests et Script Sync ;
- Studio, ses manifests et les preuves runtime applicables ;
- l'art direction, les assets 3D, Blender, les canons et leurs gates ;
- les scripts, configurations, dépendances, sauvegardes et artefacts ;
- la sécurité, les secrets, les frontières de confiance et les chemins
  d'attaque ;
- la cohérence d'ensemble entre spécification, implémentation et preuve.

Le résultat recherché n'est pas une affirmation abstraite de perfection. Le
critère terminal est : aucun défaut connu non traité dans le scope autorisé,
chaque contrôle applicable exécuté, et chaque limite externe encore ouverte
explicitement classée `BLOCKED`, `UNKNOWN` ou `PARTIAL`.

## Baseline — 2026-07-17

- Branche : `agent/github-collaboration`, alignée sur son upstream au début de
  l'audit.
- Git n'était pas installé ou visible ; Git for Windows `2.55.0.windows.3` a
  été installé côté utilisateur afin de pouvoir préserver le worktree.
- Le worktree n'est pas propre avant cet audit :
  - 7 fichiers suivis sont modifiés ;
  - 18 564 fichiers sont non suivis et non ignorés ;
  - 125 779 fichiers sont ignorés ;
  - environ 144 625 fichiers occupent 8,96 Go, principalement dans des
    environnements, builds, sauvegardes et archives 3D.
- Les modifications et fichiers non suivis préexistants appartiennent à
  l'utilisateur. Aucun reset, clean, checkout destructif, renommage massif ou
  suppression n'est autorisé par ce plan.
- Le seul fichier d'instructions découvert est `AGENTS.md` à la racine.
- L'autorité de synchronisation déclarée reste Studio Script Sync :
  `Server`, `Shared` et `Client` vers `data/src/server`, `data/src/shared` et
  `data/src/client`. L'exposition réelle d'une instance Studio reste à
  confirmer.
- Le 2026-07-18, ADR-0002 a renoncé à G3 comme condition de séquencement
  interne. La preuve humaine reste `UNKNOWN` et la technique ne doit pas être
  requalifiée en preuve produit.

## Acceptance criteria

1. Un inventaire stable couvre tous les fichiers présents, avec au minimum :
   chemin, taille, type, hash, couche d'autorité, statut Git/ignore,
   disposition d'audit et contrôles applicables.
2. Chaque fichier source ou documentaire autoritatif reçoit une revue
   sémantique ; les familles générées, vendored, sauvegardées ou binaires
   reçoivent une revue structurelle, de provenance, de duplication et
   d'hygiène proportionnée.
3. Tous les liens Markdown internes, documents enregistrables, statuts,
   versions, gates, citations, encodages et affirmations de preuve sont
   cohérents ou corrigés.
4. Tous les fichiers Luau sont revus pour typage, architecture, sécurité
   client/serveur, bornes, idempotence, nettoyage, performance et conformité
   aux contrats actifs.
5. Les scripts de dépôt, configurations et manifests sont parsés, testés et
   comparés aux commandes réellement exposées.
6. Le pipeline 3D est revu sur ses sources autoritatives, canons, recettes,
   déterminisme, preuves, publication, Studio, mobile, sauvegardes et
   artefacts, sans publication ni génération externe non autorisée.
7. Un scan de sécurité profond multi-passe est terminé avant toute correction
   de ses findings ; chaque finding validé est ensuite corrigé et revalidé.
8. Les changements restent minimaux, explicables et réversibles. Aucun travail
   utilisateur n'est écrasé.
9. `scripts/check.ps1`, les tests ciblés, les tests 3D applicables, les audits
   JSON/Markdown/UTF-8/secrets et `git diff --check` passent après correction.
10. Tout changement runtime applicable est synchronisé puis exercé dans
    l'instance Studio prévue, avec consoles client/serveur et preuve visuelle ;
    si l'instance ou un appareil requis n'est pas accessible, le verdict reste
    non-`PASS`.
11. Le rapport final lie chaque constat à une correction, une décision
    explicite ou une limite résiduelle, et liste tous les fichiers changés.

## Authority and safety

- Ordre d'autorité : demande actuelle, GDD/contrats/ADR acceptés, comportement
  et tests, patterns existants, hypothèses.
- L'audit n'accepte aucun contrat produit. ADR-0002 rend seulement la décision
  Action 0.4.1 admissible ; Progression 0.5, Persistence 0.6, économie,
  monétisation, LiveOps et publication restent soumises à leurs gates.
- Les canons et preuves 3D ne sont jamais modifiés pour faire correspondre un
  résultat. Toute correction doit respecter la chaîne canon verrouillé →
  contrat → source déterministe → build → preuve.
- Aucun secret, identifiant sensible ou reçu brut n'est imprimé ou commité.
- Les sauvegardes et installations historiques ne sont pas supprimées sans une
  décision séparée. Leur prolifération peut être corrigée par isolation,
  ignorance et documentation sans destruction.
- Le scan de sécurité est non mutant. Ses corrections ne commencent qu'après
  clôture et validation des findings.

## Audit ledger

L'inventaire machine est généré dans un répertoire local d'audit avec des
entrées JSONL déterministes. Le rapport durable n'embarque pas des dizaines de
milliers de lignes générées ; il conserve :

- le hash du ledger ;
- les compteurs par couche, type et disposition ;
- les exceptions et findings individuels ;
- les commandes permettant de régénérer le ledger ;
- une table explicite pour chaque source autoritative.

La couverture n'est déclarée complète que si le nombre d'entrées du ledger
égale le nombre de fichiers de la baseline résolue, hors fichiers créés par
l'audit lui-même qui sont ajoutés dans une passe finale.

## Milestones

- [ ] M1 — État de vérité, inventaire, autorités, Git, Studio et baseline.
- [ ] M2 — Documentation/gouvernance : revue, corrections et preuves.
- [ ] M3 — Jeu Luau/tests/Studio : revue, corrections et preuves.
- [ ] M4 — Art direction/assets 3D/outillage : revue, corrections et preuves.
- [ ] M5 — Scan sécurité profond, validation, attaque et rapport canonique.
- [ ] M6 — Correction et revalidation de tous les findings confirmés.
- [ ] M7 — Scripts/configuration/CI/dépendances/temporaires et cohérence globale.
- [ ] M8 — Validation finale, diff complet et rapport de couverture.

## Verification commands

Les commandes exactes seront découvertes avant exécution. La baseline attend au
minimum :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\format.ps1 -Check
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 -?
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 --help
git diff --check
git status --short
```

Les tests Python, Blender, simulation, manifests Studio, liens Markdown,
encodage, JSON Schema, secrets et déterminisme seront ajoutés seulement après
leur découverte dans les surfaces actives.

## Recovery

- Conserver un snapshot de statut Git et des hashes avant chaque famille de
  corrections.
- Modifier par petits lots cohérents, avec tests ciblés immédiatement après.
- Ne jamais utiliser `git reset --hard`, `git clean`, `git checkout --`,
  rebase, amend ou force-push.
- En cas de conflit avec une modification préexistante, arrêter le lot,
  préserver les deux intentions et demander une décision uniquement si aucune
  interprétation sûre et réversible n'existe.
- En cas d'échec d'un artefact généré, ne supprimer que la racine générée
  explicitement vérifiée et documentée par son outil.

## Progress

- 2026-07-17 : objectif persistant adopté.
- 2026-07-17 : `AGENTS.md`, les autorités documentaires principales et les
  compétences d'audit 3D/sécurité ont été lues.
- 2026-07-17 : Git installé ; baseline du worktree et volumétrie établies.
- 2026-07-17 : revues non mutantes documentation, jeu et 3D lancées en
  parallèle.
- 2026-07-18 : `scripts/check.ps1` et `git diff --check` passent sur le
  worktree avant intégration GitHub ; aucun fichier candidat ne dépasse 100 Mo.
- 2026-07-18 : deux exécutions du ledger exhaustif ont dépassé respectivement
  120 s et 420 s pendant le hash des environnements/archives locaux. Le contrôle
  de couverture machine reste `PARTIAL`; l'inventaire Git borné des fichiers
  publiables est complet.
- 2026-07-18 : le founder renonce explicitement à G3 ; décision enregistrée
  dans ADR-0002 sans conversion de la preuve `UNKNOWN` en `PASS`.

## Decisions

- Auditer les 144 625 fichiers par une combinaison de couverture machine
  exhaustive et de revue sémantique des sources autoritatives, plutôt que de
  prétendre qu'un environnement Python ou une archive binaire peut être relu
  ligne par ligne comme du code produit.
- Préserver toutes les modifications préexistantes et traiter leur faible
  suivi Git comme un finding de gouvernance, pas comme une permission de les
  supprimer.
- Maintenir séparés : spécification, implémentation, preuve technique, preuve
  humaine et approbation de production.
- Ne pas bloquer la consolidation GitHub sur le hash intégral de 8+ Go de
  caches, environnements et sauvegardes ignorés ; conserver ce contrôle
  `PARTIAL` et vérifier exhaustivement les fichiers candidats à Git.

## Status

`IN_PROGRESS`.
