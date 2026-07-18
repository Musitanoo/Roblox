# Standard documentaire

| Champ | Valeur |
| --- | --- |
| ID | `GOV-STD-001` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 1.1.0 |
| Propriétaire | Founder |
| Mainteneur | Équipe de développement |
| Scope | Corpus Markdown durable, registre, métadonnées, liens et preuves du dépôt |
| Source | `AGENTS.md`, ADR-0001 et défauts observés pendant l'audit du 2026-07-17 |
| Dernière revue | 2026-07-17 |
| Revue suivante | Nouvelle classe documentaire, exclusion, ambiguïté d'autorité ou défaut non détecté par le check |

## Journal de révision

- `1.1.0` — métadonnées complètes, contrôle automatisé du corpus durable et
  exclusions historiques explicites.
- `1.0.0` — taxonomie, hiérarchie et règles de qualité initiales.

## Objectif

Maintenir une documentation plus petite que le système qu'elle gouverne,
traçable vers des décisions et des preuves, et suffisamment précise pour éviter
deux implémentations plausibles d'un même contrat.

## Les trois dimensions obligatoires

### 1. Classe d'autorité

- `CANON` : identité, principes et limites durables.
- `CONTRACT` : comportement normatif dans un scope et une version.
- `HYPOTHESIS` : affirmation testable non encore suffisamment prouvée.
- `CONFIG` : valeur active, bornes, environnement et fallback.
- `PLAN` : séquence de travail et de vérification temporaire.
- `EVIDENCE` : observation horodatée, reproductible autant que possible.
- `REFERENCE` : index, glossaire, source externe ou guide.

### 2. Cycle de vie

- `DRAFT` : modifiable, non autoritaire.
- `IN_REVIEW` : proposé pour décision.
- `ACCEPTED` : autoritaire dans son scope.
- `ACTIVE` : guide ou registre maintenu en continu.
- `RECORDED` : preuve close ; corrections uniquement par addendum visible.
- `SUPERSEDED` : remplacé, conservé pour l'historique.
- `DEPRECATED` : encore présent pendant une transition annoncée.
- `ARCHIVED` : historique, aucune action active.

### 3. Verdict de preuve

`PASS`, `FAIL`, `PARTIAL`, `BLOCKED` ou `UNKNOWN`, selon `AGENTS.md`. Le verdict
n'est utilisé que lorsqu'un document rapporte une vérification.

## Métadonnées minimales

Chaque nouveau document normatif ou de preuve indique :

- ID stable ;
- classe ;
- cycle de vie ;
- version si normative ;
- propriétaire et approbateur lorsque différents ;
- scope ;
- source ou documents remplacés ;
- date de dernière revue ;
- déclencheur de prochaine revue.

L'absence de date calendrier est volontaire : la revue est d'abord déclenchée
par un changement de risque, de gate, de comportement ou de source externe.

## Autorité par domaine

| Domaine | Source normative | Preuve de réalité |
| --- | --- | --- |
| Identité et éthique | Constitution produit | Playtests, audits et décisions |
| Vision et systèmes | GDD + ADR produit | Contrats de slice et tests joueurs |
| Feature active | Contrat accepté de la slice | Code, tests et rapport d'acceptation |
| Luau synchronisé | Fichiers sous `data/src` | Script Sync observé + playtest |
| Monde non synchronisé | DataModel Studio actif | Inspection, manifestes et captures |
| Toolchain | `rokit.toml` + `docs/TOOLING.md` | Scripts de vérification |
| Valeurs | Config versionnée applicable | État runtime et historique de config |
| Données persistantes | Schéma/migration acceptés | Tests isolés et métriques d'échec |
| Publication | Creator Dashboard + procédure de release | Version publiée et monitoring |

Le comportement exécutable décrit ce qui existe. Lorsqu'il contredit un contrat
accepté, ouvrir un écart et choisir explicitement : corriger le comportement ou
versionner le contrat. Ne jamais laisser le code redéfinir silencieusement le
produit.

## Hiérarchie et résolution de conflit

1. Arrêter la modification en conflit.
2. Citer les deux sources avec leur classe, version et scope.
3. Appliquer l'ordre d'autorité d'`AGENTS.md`.
4. Choisir l'interprétation la plus sûre, étroite et réversible.
5. Enregistrer toute décision matérielle dans un ADR.
6. Mettre à jour registre, contrats, tests et migration applicables dans le même
   changement.

## Changements par classe

| Changement | Exigences |
| --- | --- |
| `CANON` | Approbation founder, ADR, analyse d'impact, version majeure |
| `CONTRACT` | Critères modifiés, tests, compatibilité ; migration/rollback si applicables |
| `HYPOTHESIS` | Cause attendue, métrique primaire, guardrails et décision possible |
| `CONFIG` | Bornes, fallback, environnement, propriétaire et historique |
| `PLAN` | État courant, décisions, récupération et preuve attendue |
| `EVIDENCE` | Données brutes préservées ; correction par addendum, jamais effacement silencieux |
| `REFERENCE` | Vérifier les liens et la source lors d'un usage décisionnel |

## Création just-in-time

Créer un document séparé seulement si au moins un déclencheur existe :

- une décision possède plusieurs options raisonnables et des conséquences ;
- deux composants ou rôles doivent partager un contrat stable ;
- une erreur pourrait perdre des données, créer un exploit ou empêcher un
  rollback ;
- un gate exige une preuve reproductible ;
- une source externe instable influence une décision ;
- le document existant devient ambigu ou possède deux cycles de revue distincts.

Sinon, enrichir le contrat actif. Une arborescence vide n'est pas une preuve de
maturité.

## Structure d'une spécification

Noyau obligatoire : objectif joueur, hypothèse, scope/hors scope, invariants,
flux ou règles, critères d'acceptation, plan de vérification, inconnues et
décisions.

Sections conditionnelles obligatoires lorsque le risque existe : réseau et
abus, données et migration, performance, analytics, UI/input/accessibilité,
erreurs et récupération, rollout/rollback, conformité et localisation.

Le modèle autoritaire est
[SYSTEM_SPEC_TEMPLATE.md](../templates/SYSTEM_SPEC_TEMPLATE.md).

## Preuves

Toute preuve indique environnement, version, scénario, résultat attendu,
observation, verdict, logs ou artefacts, limites et nettoyages temporaires. Les
preuves reproductibles priment sur les résumés. Un résultat synthétique ou une
revue visuelle indépendante doit être nommé comme tel et ne remplace jamais un
panel humain.

## Sources externes et citations

- Préférer sources primaires, documentation officielle et politiques en vigueur.
- Utiliser un lien sans paramètre de tracking, un titre, une date de consultation
  et la décision ou affirmation supportée.
- Une recommandation de plateforme est un contexte, pas une preuve que le jeu
  satisfait le joueur.
- Revalider avant tout changement de sécurité, conformité, monétisation,
  publication ou API.
- Le registre courant est
  [ROBLOX_OFFICIAL_SOURCES.md](../references/ROBLOX_OFFICIAL_SOURCES.md).

## Qualité et maintenance

Avant acceptation : liens relatifs valides, UTF-8, titres uniques, absence de
marqueurs de citation internes, cohérence avec le registre, diff sans espace
invalide, et vérifications du dépôt applicables. Les documents remplacés restent
accessibles et portent un lien vers leur successeur.

Le contrôle déterministe est `scripts/check-docs.ps1`, appelé par
`scripts/check.ps1` et donc par la CI. Il couvre le corpus Markdown durable
enregistré : décodage UTF-8 strict, liens relatifs, fences, titres uniques,
complétude du registre, métadonnées applicables et vocabulaire du registre
produit. Une exclusion n'est admise que si son chemin et sa justification sont
nommés dans le script. Les preuves `RECORDED` et contrats historiques antérieurs
à ADR-0001 restent immuables ; ils sont corrigés par addendum ou explicitement
exclus, jamais silencieusement réécrits.
