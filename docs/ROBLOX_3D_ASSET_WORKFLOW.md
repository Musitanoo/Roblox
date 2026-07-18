# Workflow canonique `roblox-3d-asset`

Version : 1.9.0  
Date : 2026-07-17  
Autorité : spécification canonique du pipeline 3D de Roblox Top 1  
Cycle de vie : `ACCEPTED`  
Statut de la spécification : `PASS`  
Statut de l'implémentation : `PARTIAL` — workflow v3.14.0 ; constitution
Salvaged Frontier verrouillée créativement, couche précanonique locale `PASS`,
18 canons/48 variantes contractuelles, famille de barricade révision 6
`PASS_LOCAL_TECHNICAL/PASS_INTERNAL_ART/HUMAN_PENDING`, Blender Visual Workbench
`PASS_LOCAL_VERTICAL_SLICE` ; paquet canonique réel 17/17 de la barricade
`PASS_AUTOMATED/HUMAN_PENDING`, cinq autres paquets canoniques, six locks
humains, publication et intégration Studio de la révision courante, mobile
physique et revue finale ouverts  
`productionApproved` : `false`

## 1. Objet

Ce document fige le workflow de création, validation, publication et intégration
des assets 3D de Roblox Top 1.

Le mot « parfait » ne signifie pas qu'une esthétique peut être universellement
parfaite. Il signifie ici :

> aucune hypothèse non déclarée, aucune capacité externe considérée comme
> acquise sans preuve observable, aucune validation subjective présentée comme
> objective, et aucun `PASS` sans les preuves applicables.

Le pipeline vise des assets :

- reproductibles lorsque leur nature le permet ;
- techniquement valides ;
- lisibles sur mobile et à leur distance d'usage ;
- conformes à une direction artistique calibrée ;
- mesurés dans Roblox plutôt que jugés seulement dans Blender ;
- publiés et mis à jour sans compromettre le gameplay ;
- traçables jusqu'à leurs sources, paramètres, versions et décisions humaines.

Cette spécification complète [AGENTS.md](../AGENTS.md) et le
[Game Design Document](../Roblox_Top_1_Game_Design_Document_v1.0.md). En cas de
conflit, l'ordre d'autorité défini par `AGENTS.md` s'applique.

La projection humaine détaillée du territoire, des six objets et des contrats
techniques commence dans
[`tools/roblox-art-bible-sota-v3/docs/README.md`](../tools/roblox-art-bible-sota-v3/docs/README.md).
Les JSON sous `art/` et `STATUS.json` restent les sources machine.

## 2. Principes non négociables

1. Codex conçoit, contraint et orchestre ; ChatGPT Web peut visualiser en phase
   précanonique ; Blender compile ; Roblox publie, intègre et mesure.
2. Un mesh généré par IA n'est jamais automatiquement une géométrie de
   production.
3. L'exploration non déterministe est séparée de la compilation déterministe.
4. Les scripts et validateurs bloquants priment sur les jugements d'agents.
5. La fonction gameplay doit être comprise avant le micro-détail.
6. La silhouette, la cible, la cause et la priorité doivent rester lisibles.
7. Le mobile est la cible de conception, pas une vérification tardive.
8. Le Package visuel ne contient pas l'autorité gameplay.
9. Toute publication se fait en staging par défaut.
10. Toute capacité MCP, Open Cloud ou Studio incertaine reçoit un capability
    probe avant d'entrer dans le chemin de production.
11. Une vérification sautée est `SKIPPED`, jamais `PASS`.
12. Une absence de preuve produit `UNKNOWN`, `PARTIAL` ou `BLOCKED`, selon la
    cause.
13. Le Blender Visual Workbench peut diagnostiquer et expérimenter, mais une
    scène MCP modifiée ne devient jamais une source de production.

La direction artistique de référence est désormais :

> Salvaged Frontier définit l'identité du monde ; Industrial Toy Defense impose
> la discipline de lecture.

Les objets doivent donc exprimer une civilisation frontalière compétente,
réparable et porteuse de mémoire, tout en conservant des silhouettes épaisses,
des fonctions immédiates, une densité de détail contrôlée et des états
gameplay lisibles sur mobile.

## 3. Résultat canonique

```text
Demande explicite
      ↓
Brief, références, budgets et niveau de criticité
      ↓
Application de la constitution Salvaged Frontier
      ↓
Description précanonique et prompt verrouillé
      ↓
Préflight de hashes, budget et autorité sans consommation
      ↓
Exploration visuelle contrôlée, Web optionnel
      ↓
Sélection humaine d'un candidat
      ↓
Définition canonique visuelle multimodale
      ↓
Vérification, acceptation, verrouillage et hash
      ↓
Enveloppe de génération liée au canon exact
      ↓
Compilation Blender déterministe
      ↓
Gates techniques bloquantes
      ↓
Rendus normalisés et revue perceptuelle bornée
      ↓
Export GLB, manifestes et hashes
      ↓
Publication Open Cloud en staging
      ↓
Capability probes Cloud et MCP
      ↓
Package visuel dans un Runtime Wrapper
      ↓
Tests fonctionnels et structurels Studio
      ↓
Benchmarks expérimentaux
      ↓
Rapport structuré
      ↓
Approbation humaine lorsqu'elle est requise
```

### 3.0A Phase précanonique Web

Avant le canon, Codex peut compiler le besoin fonctionnel en un paquet
précanonique versionné :

```text
brief.md
prompt.txt
negative-constraints.txt
requested-views.json
requested-states.json
request.json
```

Le paquet lie par SHA-256 :

- le brief fonctionnel ;
- la constitution Salvaged Frontier sélectionnée ;
- le compilateur précanonique ;
- le prompt exact ;
- les contraintes négatives ;
- les vues et états demandés ;
- le budget maximal.

Le préflight est obligatoire avant toute soumission Web. Il ne consomme aucune
image et bloque :

- un hash périmé ;
- un budget épuisé ;
- la répétition d'un prompt ayant déjà produit un résultat importé ;
- un fallback automatique vers imagegen ou une API ;
- une autorité canonique, géométrique ou de production indue.

Le handoff ChatGPT Web conserve `submissionAuthorized=false`. Une soumission
réelle nécessite l'autorisation bornée du founder. Chrome reste un transport
remplaçable : aucun cookie, secret ou état d'authentification n'est inspecté.

Les seules décisions autorisées après import sont :

```text
REJECTED
REVISION_REQUIRED
PRECANONICAL_CANDIDATE
HUMAN_SELECTED
```

`HUMAN_SELECTED` autorise seulement la rationalisation en définition canonique.
Une image n'est jamais promue directement en `CANONICAL`, ne prouve jamais les
faces cachées et conserve `productionApproved=false`.

### 3.1 Définition canonique visuelle obligatoire

Le brief technique ne suffit plus à autoriser la génération. Entre
l'exploration et la reconstruction, chaque couple `objet × direction
artistique` possède une **définition canonique visuelle** versionnée.

Cette définition répond avant Blender aux questions suivantes :

- qu'est l'objet dans le monde et dans le gameplay ;
- ce que le joueur doit comprendre en une seconde ;
- comment sa silhouette se lit de face, de dos, des côtés, du dessus, du
  dessous, en trois-quarts et depuis la caméra réelle ;
- quelles proportions, masses, zones négatives et asymétries sont obligatoires ;
- quels composants existent, à quoi ils servent, comment ils sont assemblés et
  quels composants peuvent bouger, casser, être remplacés ou disparaître ;
- comment la DA traduit l'objet sans modifier son identité fonctionnelle ;
- quels matériaux et rôles sémantiques appartiennent à chaque zone ;
- comment tous les états applicables dérivent de la même structure ;
- ce qui reste invariant, ce qui peut varier et ce qui est interdit ;
- quelles preuves visuelles doivent être liées avant le verrouillage.

Le contrat sépare deux espaces :

```text
EXPLORATION
créativité ouverte, candidats comparés, production interdite

PRODUCTION
canon verrouillé, créativité limitée à la reconstruction et à l'optimisation
```

La règle normative est :

> La génération ne décide jamais ce qu'est l'objet. Elle reconstruit l'objet
> déjà décidé et doit démontrer sa conformité au canon exact.

### 3.2 Étude aveugle de validation indépendante

Le founder a sélectionné Salvaged Frontier par autorité créative explicite et
a documenté les alternatives rejetées. L'étude aveugle reste un outil de
validation perceptuelle et de réduction des biais ; elle n'est pas présentée
comme la preuve ayant produit cette décision.

Codex et le score automatique ne peuvent toujours ni remplacer ni signer
l'autorité humaine. Lorsque l'étude est exécutée, les trois territoires sont
présentés sous les labels anonymes `A`, `B` et `C`.

Le kit officiel prépare :

- douze slots participants, avec un minimum contractuel de huit ;
- quatre slots experts, avec un minimum contractuel de deux ;
- trente essais chronométrés par participant ;
- vingt-sept notes structurées par expert ;
- des ordres de présentation et de réponses équilibrés ;
- une carte label → territoire conservée dans un dossier privé ;
- deux ZIP distribuables ne contenant aucun identifiant de territoire ;
- une vérification automatique des noms, contenus textuels et hashes ;
- un scellement des sessions brutes avant toute levée de l'aveugle.

Les essais mesurent la silhouette à 60 studs, la fonction à 30 studs, les états
à 15–30 studs et la direction d'impact. Les experts évaluent les neuf
dimensions de la grille officielle sur les Golden Scenes, les cinq assets de
calibration et la tourelle indépendante.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 `
  prepare-study -Open

powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 `
  seal-study -StudyRoot <study-root>
```

Le scoreur peut déclarer un candidat éligible et produire un classement. Il
conserve `selectionAuthority = HUMAN_ONLY` et `automaticSelection = null`.
Un échec de hard gate rend le candidat inéligible quel que soit son score.

### 3.3 Couverture obligatoire

La bibliothèque active contient un canon pour chacun des six objets :

```text
barricade
objective_core
enemy_standard
floor_module
damage_effect
turret_fast_v1
```

dans chacune des trois directions artistiques :

```text
industrial-toy-defense
salvaged-frontier
clean-tactical-diorama
```

Soit :

```text
18 canons objet × DA
48 définitions d'état
```

Les états ne sont jamais générés comme des objets indépendants. Ils conservent
les mêmes composants, pivots, ancres gameplay et relations de construction.
Chaque changement déclare une opération explicite :

```text
PRESERVE | MOVE | ROTATE | EXPOSE | OPEN
BREAK | REMOVE | RECOLOR | EMIT | DEFORM
```

Un état important utilise des signaux redondants de forme, silhouette, valeur,
couleur, lumière, mouvement, VFX et audio. La couleur n'est jamais l'unique
porteur d'information.

### 3.4 Statuts, paquet visuel et verrou

Statuts autorisés :

```text
DRAFT → CANDIDATE → ACCEPTED → LOCKED
                              ↘ REVISED
```

- `DRAFT` : incomplet, aucune génération autorisée ;
- `CANDIDATE` : contrat textuel complet, exploration autorisée ;
- `ACCEPTED` : solution humaine retenue, paquet visuel encore finalisable ;
- `LOCKED` : paquet multimodal complet, hashé et approuvé humainement ;
- `REVISED` : nouvelle version volontaire, justifiée et traçable.

Le paquet visuel exige dix-sept familles de preuves :

```text
orthographic
perspective
black_silhouette
component_breakdown
proportions
materials
semantic_zones
all_states
state_comparison
mobile_near
mobile_mid
mobile_far
lighting_matrix
repetition_1
repetition_30
repetition_100
required_and_forbidden_annotations
```

Si un composant ou un état n'apparaît dans aucune planche liée, le canon est
incomplet. `LOCKED` exige :

```text
visualPacket.status == COMPLETE
chaque board.status == BOUND
chaque artefact existe et correspond à son SHA-256
approval.status == APPROVED
decisionRecord présent
evidencePackageSha256 présent
```

Le verrou est un overlay séparé du candidat. Il ne réécrit pas silencieusement
la proposition qui a été évaluée. Une révision crée une nouvelle version avec
raison, preuves et décision.

### 3.5 Liaison obligatoire à la génération

Avant chaque build canonique, le workflow produit une enveloppe
`generation-authority` contenant :

- le mode `EXPLORATION` ou `PRODUCTION` ;
- le scope `calibration` ou `transfer` ;
- le territoire ;
- le hash du catalogue ;
- le chemin et le hash du compilateur Blender ;
- l'identifiant, le chemin, le statut et le hash de chaque canon consommé.

Le mode `EXPLORATION` accepte au minimum `CANDIDATE`. Le mode `PRODUCTION`
échoue avant Blender si un canon du territoire demandé n'est pas :

```text
LOCKED + COMPLETE + APPROVED
```

Après le build, un rapport de conformité relie le hash exact du rapport Blender
au hash exact du canon et classe séparément :

- conformité géométrique ;
- conformité visuelle ;
- conformité fonctionnelle ;
- conformité technique ;
- conformité perceptuelle ;
- autorité humaine.

La conformité fonctionnelle ne se déduit pas du nombre de meshes. Un
inspecteur Blender séparé relit dans le `.blend` chaque nom d'objet sémantique,
son rôle matériau et sa bande de détail. Une table d'adaptation versionnée et
hashée relie ces noms d'implémentation aux IDs de composants stables du canon.
Le rapport lie le hash de cette table et celui du readback. Cette table peut
expliquer comment retrouver un composant ; elle ne peut pas redéfinir ce qu'est
le composant.

Une belle apparence globale ne compense jamais une exigence absente.

### 3.6 Commandes canoniques

```powershell
.\scripts\art-direction.ps1 canons
.\scripts\art-direction.ps1 validate-canons

# Doit actuellement échouer tant que la DA et les canons ne sont pas verrouillés.
.\scripts\art-direction.ps1 validate-canons -RequireLockedCanons

# Exploration liée aux canons CANDIDATE.
.\scripts\art-direction.ps1 build -RenderMode full -Resume

# Production : préflight bloquant avant Blender.
.\scripts\art-direction.ps1 build -RenderMode full -RequireLockedCanons
```

Le verrou d'un canon n'est applicable qu'après sélection humaine du territoire
final et fourniture du manifeste complet de preuves :

```powershell
.\scripts\art-direction.ps1 lock-canon `
  -Asset barricade `
  -Territory salvaged-frontier `
  -CanonEvidence <visual-evidence-manifest.json> `
  -HumanReview <human-review-completed.json> `
  -Apply
```

Sans `-Apply`, la commande reste un dry-run. Elle ne sélectionne jamais une DA
à la place du fondateur. Un lock réel exige le fichier de revue complet produit
par la galerie : 17 décisions de planche, sept gates, une identité humaine, une
justification, un timestamp et le digest exact du paquet.

### 3.7 Paquet canonique réel par asset

Après compilation déterministe des états, la commande `canon-packet` produit
les dix rendus Blender bruts nécessaires, compose les dix-sept familles de
planches en 1920 × 1080, relance la composition et vérifie les deux niveaux de
déterminisme :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 `
  canon-packet .\assets-3d\defense-barricade-small\asset.json
```

La commande vérifie avant réutilisation du cache les hashes du contrat, du
canon, du `.blend`, du manifeste de build, du renderer et de chaque PNG. Utiliser
`--force` reconstruit explicitement les deux passes Blender. La sortie contient
`evidence-manifest.json`, `human-review.json` et `index.html`.

`index.html` est aussi le poste de revue local : progression sauvegardée dans
le navigateur, aucun choix prérempli, cohérence de la décision vérifiée et
téléchargement de `human-review-completed.json`. Une révision ou un rejet exige
au moins un échec explicite ; `LOCK` exige 17/17 planches et 7/7 gates à `PASS`.

Un résultat automatisé `PASS` signifie uniquement :

```text
evidenceClass == REAL_RENDERED
rawRenderDeterminism == PASS
compositionDeterminism == PASS
17/17 boards présentes, dimensionnées et hashées
humanReview.status == PENDING
productionApproved == false
```

Le paquet ne devient une preuve de verrouillage qu'après une décision humaine
réelle liée à son `evidencePackageSha256`.

## 4. Zones de confiance

### 4.1 Zone A — Gates déterministes

Pour les mêmes entrées canoniques, versions, plateforme et seeds :

- validation des schémas ;
- génération paramétrique Blender ;
- dimensions et axes Blender ;
- topologie, triangles et composantes ;
- UV, matériaux et noms ;
- transformations et pivots déclarés ;
- présence des fichiers ;
- hashes canoniques ;
- structure déclarée du Runtime Wrapper.

Un gate obligatoire exécuté qui échoue produit `FAIL`.

### 4.2 Zone B — Services externes

- authentification et permissions Open Cloud ;
- traitement, modération et versionnement Roblox ;
- disponibilité de Roblox ;
- accès au propriétaire de staging ;
- connexion au Studio MCP ;
- disponibilité de l'instance Studio attendue.

Une dépendance externe empêchant l'exécution produit `BLOCKED`.

### 4.3 Zone C — Mesures expérimentales

- frame time et FPS ;
- mémoire ;
- temps de chargement ;
- physique, rendu et scripts ;
- réseau ;
- température et throttling ;
- différences entre appareils.

Ces mesures sont objectives mais bruitées. Elles exigent un profil matériel,
un protocole, plusieurs passages, une dispersion et une baseline compatible.

### 4.4 Zone D — Évaluation perceptuelle

- silhouette ;
- hiérarchie de formes ;
- cohérence de style ;
- proportions ;
- lisibilité fonctionnelle ;
- palette et matériaux ;
- originalité perçue ;
- impression de finition.

Cette zone aide à décider. Elle ne prouve ni la beauté, ni l'originalité
absolue, ni l'absence de similarité avec toute œuvre existante.

### 4.5 Zone E — Autorité humaine

Le fondateur approuve :

- les références dorées ;
- les hero assets ;
- les éléments centraux du gameplay ;
- les changements majeurs de silhouette ;
- les désaccords perceptuels importants ;
- tout passage final en production avant calibration de la famille d'assets.

## 5. Statuts et états

### 5.1 Verdicts globaux autorisés

- `PASS` : toutes les preuves applicables existent et les gates requis passent.
- `FAIL` : un comportement ou gate obligatoire exécuté échoue.
- `PARTIAL` : un résultat utile existe, mais une preuve secondaire ou une
  approbation requise manque.
- `BLOCKED` : une dépendance ou autorisation externe empêche l'exécution.
- `UNKNOWN` : une capacité obligatoire n'a pas été mesurée ou n'est pas
  observable.

Ordre d'agrégation :

```text
FAIL > BLOCKED > UNKNOWN > PARTIAL > PASS
```

Le rapport conserve toutes les causes ; cet ordre choisit seulement le verdict
global.

### 5.2 Résultats de checks

Un check individuel peut être :

```text
PASS | FAIL | PARTIAL | BLOCKED | UNKNOWN | SKIPPED
```

`SKIPPED` doit inclure une raison et indiquer si le check était applicable.

### 5.3 Capacités externes

Une capacité utilise un vocabulaire distinct :

```text
SUPPORTED | UNSUPPORTED | UNKNOWN | BLOCKED
```

Chaque capacité enregistre sa preuve :

```text
OBSERVED | DOCUMENTED | INFERRED | NOT_RUN
```

Une inférence ne suffit jamais pour faire entrer une capacité dans le chemin de
production.

### 5.4 Approbation de production

`productionApproved` reste un booléen indépendant. Il ne peut devenir `true`
que si :

- le verdict global est `PASS` ;
- les gates humains applicables sont satisfaits ;
- la version, le Package ID et les hashes sont figés ;
- le manifeste correspond à un commit identifié ;
- la cible de publication a été explicitement vérifiée.
- le transfert vers l'asset inédit `turret_fast_v1` passe automatiquement et
  reçoit une approbation humaine liée au territoire sélectionné et au digest
  exact de preuve ;
- les mesures low-tier requises proviennent d'un appareil physique nommé.

État d'implémentation courant au 16 juillet 2026 :

```text
workflow installé                    PASS
validation statique                  PASS
Blender exécution                    PASS
Blender niveau de preuve             BUILD_ONLY
constitution Salvaged Frontier       CREATIVE_DIRECTION_LOCKED
canons sélectionnés                  SELECTED_PARTIAL
Studio constitution sélectionnée     UNKNOWN
Studio Device Simulator              PARTIAL
transfert turret_fast_v1 automatisé  PASS 100/100
transfert final                      PARTIAL (signature humaine)
publication transfert sélectionnée   UNKNOWN
intégration Studio sélectionnée      UNKNOWN
mobile physique                      BLOCKED
sélection artistique founder         PASS
productionApproved                   false
```

Les anciens `PASS` de publication et d'intégration v3.7 sont archivés comme
baseline pré-sélection. Ils ne prouvent pas la constitution optimisée courante.

Commande ergonomique du transfert :

```powershell
.\scripts\art-direction.ps1 transfer -Open
.\scripts\art-direction.ps1 publish-transfer
.\scripts\art-direction.ps1 stage-transfer
```

Les deux dernières commandes sont des dry-runs. La mutation Cloud exige
`-ConfirmPublish`; la transaction Studio exige `-Apply`. Le registre contenant
les identifiants bruts reste local, gitignoré et hors du package remplaçable.

## 6. Modes d'exécution et sécurité de publication

Le pipeline possède trois modes :

```text
ValidateOnly
PublishStaging
PublishProduction
```

Règles :

- `ValidateOnly` est le mode par défaut.
- `PublishStaging` utilise uniquement un propriétaire et des Packages de test
  explicitement autorisés.
- `PublishProduction` exige une demande explicite, un Package ID confirmé, un
  propriétaire confirmé et un hash précédent correspondant au registre.
- Une vertical slice ne touche jamais un Package de production.
- Une mise à jour de production doit conserver une version précédente
  récupérable et une procédure de rollback.

Exemple de politique :

```json
{
  "environment": "staging",
  "allowedCreatorIds": [12345],
  "packageNamePrefix": "DEV_",
  "allowProductionCreate": false,
  "allowProductionUpdate": false
}
```

Les credentials Open Cloud :

- ne sont jamais stockés dans Git ;
- ne sont jamais copiés dans un prompt ou un rapport ;
- sont lus directement par le publisher ;
- sont masqués dans tous les logs et messages d'erreur ;
- utilisent les permissions et ressources minimales ;
- ne sont jamais affichés par une commande de diagnostic ;
- sont limités au propriétaire prévu par une allowlist.

Le publisher vérifie après chaque mutation l'état distant réellement obtenu. Il
ne déduit jamais le succès du seul code HTTP initial.

## 7. Structure minimale du dépôt

La structure est introduite progressivement par la vertical slice :

```text
docs/
└── ROBLOX_3D_ASSET_WORKFLOW.md

plans/
└── defense-barricade-vertical-slice.md

assets-3d/
├── defense-barricade-small/
│   ├── asset.json
│   ├── review.json
│   ├── evidence/
│   ├── qa/
│   └── build/                 # généré, ignoré
└── registry/
    └── staging.json

tools/
└── roblox-3d-asset/
    ├── r3d.py
    ├── pipeline/
    ├── blender/
    ├── publisher/
    ├── schemas/
    ├── studio/
    └── tests/

scripts/
└── r3d.ps1
```

Le skill n'est créé qu'après réussite de la vertical slice. Son emplacement est :

```text
.agents/skills/roblox-3d-asset/SKILL.md
```

Un ExecPlan est obligatoire pour la vertical slice, le publisher Open Cloud,
les changements transversaux du pipeline, les migrations de format et les hero
assets complexes. Un prop routinier utilise ensuite son brief et son manifeste
d'exécution ; il ne nécessite pas automatiquement un ExecPlan.

## 8. Brief canonique d'un asset

Le brief est validé avant toute génération par un validateur standard-library
testé, maintenu en parité avec le JSON Schema versionné. Il définit au minimum :

```json
{
  "schemaVersion": 1,
  "assetKey": "defense_barricade_small",
  "displayName": "Defense Barricade Small",
  "criticality": "P1",
  "gameplayFunction": "Temporary destructible enemy blocker",
  "visualCanon": {
    "canonId": "vc_barricade__industrial-toy-defense__v1",
    "assetId": "barricade",
    "territoryId": "industrial-toy-defense",
    "path": "art/canonical-visuals/industrial-toy-defense/barricade.json",
    "sha256": "<64 lowercase hexadecimal characters>",
    "minimumStatus": "CANDIDATE",
    "productionStatus": "LOCKED"
  },
  "dimensionsStuds": [8, 2, 4],
  "dimensionTolerancePercent": 1,
  "viewDistanceStuds": {
    "minimum": 3,
    "maximum": 60
  },
  "artDirection": ["stylized", "chunky", "readable", "toy-like"],
  "triangleBudget": {
    "target": 1500,
    "maximum": 2500,
    "maximumPerMesh": 20000
  },
  "textureBudget": {
    "albedo": 512,
    "normal": 256,
    "roughness": 256,
    "metalness": 256
  },
  "expectedConcurrentCount": 30,
  "collisionStrategy": "custom_parts",
  "runtime": {
    "anchored": true,
    "canCollideVisual": false,
    "canQueryVisual": true,
    "canTouchVisual": false,
    "castShadow": true,
    "renderFidelity": "Automatic",
    "streamingPolicy": "inherit_experience",
    "lodPolicy": "asset_specific"
  },
  "requiredStates": ["intact", "damaged", "critical"],
  "forbidden": [
    "logos",
    "unapproved text",
    "baked lighting",
    "tiny floating details",
    "uncontrolled texture noise"
  ]
}
```

Les propriétés runtime sont décidées par la fonction. `CanQuery`, `CanTouch`,
`CastShadow`, le LOD, le streaming et les collisions n'ont pas de valeur
universelle.

## 9. Contrat d'unités, axes et pivots

Avant la première compilation, le pipeline définit et teste :

- la conversion entre unités Blender et studs ;
- les axes avant, haut et latéral ;
- le sens des rotations ;
- l'origine de chaque mesh ;
- le pivot du modèle ;
- le point de contact avec le sol ;
- les conventions de nommage et d'imbrication.

Les dimensions Blender ne suffisent pas. Après publication et insertion, Studio
doit mesurer les bounds, axes, pivots et positions réels et les comparer au
brief. Cette vérification est le gate `CAP-CLOUD-002`.

## 10. Exploration et provenance

### 10.1 Nombre de silhouettes

| Criticité | Usage | Candidats indicatifs | Approbation |
|---|---|---:|---|
| P3 | décor banal | 2–3 | automatique après calibration |
| P2 | prop secondaire | 3–4 | humaine pendant calibration |
| P1 | gameplay central | 5–6 | humaine obligatoire |
| P0 | hero asset | 8–12 | humaine obligatoire |

Les LOD, textures finales et variantes de dégâts ne sont produits qu'après
sélection de la silhouette.

### 10.2 Types de sources

La provenance accepte une union explicite.

Source locale :

```json
{
  "kind": "local_file",
  "path": "references/original.glb",
  "sha256": "sha256:...",
  "mimeType": "model/gltf-binary"
}
```

Source Roblox sans faux export GLB :

```json
{
  "kind": "roblox_asset",
  "assetId": 123456789,
  "meshContentId": "rbxassetid://...",
  "captures": ["front.png", "side.png", "three-quarter.png"],
  "hierarchySnapshot": "references/studio-tree.json"
}
```

Recette procédurale :

```json
{
  "kind": "procedural_recipe",
  "generator": "tools/roblox-3d-asset/blender/compile_asset.py",
  "parameters": "asset.json",
  "seed": 1729,
  "gitCommit": "abc1234"
}
```

Un prompt seul n'est jamais une source reproductible. Une génération conserve
le fournisseur, l'outil, la version si elle est exposée, le prompt, la date,
l'identifiant, les captures, les asset IDs, les fichiers disponibles, les
hashes et l'état de revue de provenance. Une licence ou autorisation ne peut pas
être marquée `approved` sans preuve ou décision humaine appropriée.

## 11. Compilation Blender

Commande canonique :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 `
  compile .\assets-3d\defense-barricade-small\asset.json
```

Le doctor résout un chemin absolu et vérifie une version exacte supportée. Il ne
suppose ni le chemin, ni la version de Blender.

Le build enregistre :

```json
{
  "blenderVersion": "exact-version",
  "pipelineVersion": "0.1.0",
  "generatorSha256": "sha256-of-compile_asset.py",
  "gitCommit": "abc1234",
  "gitDirty": false,
  "seed": 1729,
  "operatingSystem": "windows",
  "architecture": "x64"
}
```

Toutes les sources d'aléatoire procédural possèdent une seed explicite. Les
dates, chemins absolus et métadonnées volatiles sont exclus des entrées
canoniques.

### 11.1 Hashes

Le pipeline sépare :

```text
sourceHash          = recettes, paramètres, références et versions
semanticAssetHash   = géométrie, UV, matériaux et hiérarchie normalisés
binaryGlbHash       = octets exacts du GLB canonique/créé
binaryFbxUpdateHash = octets exacts du FBX envoyé lors d'une mise à jour
```

Le manifeste JSON est sérialisé canoniquement. Le publisher n'utilise pas un
hash binaire volatil comme seule définition d'un changement sémantique.
L'exporteur normalise le chemin du `.blend` embarqué dans le FBX. Deux sorties
A/B produites dans des chemins canoniques de même longueur doivent être
bit-identiques. Entre des répertoires de longueurs différentes, le FBX conserve
une longueur de chaîne différente : le pipeline vérifie alors son SHA-256 et sa
taille contre son propre manifeste, tandis que le hash sémantique, la géométrie,
le GLB et les rendus prouvent l'identité du contenu.

### 11.2 Familles d'états déterministes

Un objet possédant plusieurs états ne peut pas être compilé comme plusieurs
concepts indépendants. `asset.json` déclare une structure commune et une liste
fermée d'overrides par état. Les overrides de production peuvent uniquement
modifier :

```text
position
rotationDegrees
material
```

Toute mutation de type, taille, segments, bevel, nom ou nombre de composants
est refusée comme mutation de topologie.

Commandes :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 `
  compile-states .\assets-3d\defense-barricade-small\asset.json

powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 `
  verify-states .\assets-3d\defense-barricade-small\asset.json
```

`compile-states` produit :

```text
build/states/
├── intact/
├── damaged/
├── critical/
├── states-manifest.json
└── state-review.html
```

`verify-states` compile deux fois chaque état et exige :

- couverture exacte du canon ;
- hash de contrat et de canon courants ;
- déterminisme du hash sémantique, du GLB, du FBX aux chemins canoniques, du
  rapport géométrique et des pixels rendus ;
- composants, triangles, dimensions et pivot invariants ;
- hashes sémantiques et GLB distincts entre états ;
- correspondance des sorties publiées avec les références A/B ;
- intégrité du FBX publié contre son manifeste.

La planche `state-review.html` ne reçoit `PASS` dans le rapport final que si sa
famille publiée correspond à la preuve déterministe. L'existence seule du
fichier HTML ne suffit pas.

Le gate `visualReview` ne fait pas confiance au statut déclaré dans
`review.json`. Pour accepter `PARTIAL` ou `PASS`, le rapport final vérifie
également l'identité et la révision de l'asset, confine chaque chemin de preuve
à la racine de l'asset et exige que chaque fichier déclaré existe. Un statut
`PASS` exige en plus les deux décisions
`automationReviewStatus=PASS` et `humanReviewStatus=PASS`. Toute preuve absente,
hors racine ou incohérente produit `FAIL`.

## 11A. Blender Visual Workbench MCP

Après une compilation déterministe et avant une correction visuelle, Codex
peut ouvrir le [Blender Visual Workbench MCP](BLENDER_MCP_WORKBENCH.md).
Cette couche est transactionnelle et non autoritative :

```text
build exact → Reference immuable → Candidate réversible → change set
→ diff + invariants → rollback ou patch source → double recompilation
```

Le mode `OBSERVE` inspecte la référence sans candidat. Le mode `EXPLORE`
travaille exclusivement sur une copie. `PATCH` explique l'intention et lie les
opérations à la recette. `PROMOTE` ne passe que si la source reconstruite
reproduit le candidat et si deux builds sont sémantiquement identiques.

Le chemin normal :

- utilise le MCP local `stdio` déclaré dans `.codex/config.toml` ;
- démarre Blender 5.2 exact en headless ;
- n'expose aucun Python arbitraire, réseau, téléchargement ou secret Roblox ;
- vérifie le hash de la référence, du contrat, du canon et du générateur ;
- sauvegarde uniquement dans `assets-3d/<asset>/workbench/<session>/` ;
- exige une approbation distincte avant de modifier la source autoritative ;
- laisse Studio, le mobile physique et l'humain fermer leurs propres gates.

Une réussite locale du Workbench ne remplace aucun gate géométrique,
perceptuel, Studio, performance ou production décrit ci-dessous.

## 12. Gates géométriques et de contenu

### 12.1 Gates absolus

```text
schema_valid == true
missing_files == 0
duplicate_names == 0
unapplied_transforms == 0
non_manifold_edges == 0
loose_vertices == 0
degenerate_faces == 0
zero_area_faces == 0
unexpected_components == 0
inverted_normals == 0
missing_uv_sets == 0
uv_sets_per_component == 1
uv_outside_0_1 == 0
unexpected_material_slots == 0
missing_textures == 0
triangles <= triangleBudget.maximum
triangles_per_mesh <= 20000
dimensions_error <= configured_tolerance
pivot_error <= configured_tolerance
glb_size_bytes <= 20000000
fbx_update_size_bytes <= 20000000
```

`Mesh.validate()` ne suffit pas. Les contrôles emploient aussi `bmesh` et des
calculs explicites. Toute correction automatique est enregistrée ; une
correction qui modifie la silhouette ou détruit des données provoque `FAIL` au
lieu d'être masquée.

### 12.2 Gates mesurables de qualité

- texel density ;
- occupation et padding UV ;
- taille minimale d'un détail à la distance cible ;
- composantes visibles de silhouette ;
- largeur de biseau ;
- delta de palette ;
- budget matériaux ;
- estimation mémoire des textures ;
- occupation écran aux distances d'usage.

Ces gates détectent des anomalies. Ils ne déclarent pas qu'un asset est beau.

## 13. Rendus et revue perceptuelle

Les caméras, FOV, éclairages, résolutions, arrière-plans et distances sont
versionnés. Les vues minimales sont :

```text
front
back
left
right
top
three-quarter
black-silhouette
mobile-near
mobile-mid
mobile-far
flat-light
harsh-light
night-light
```

Les critiques voient des candidats anonymisés. Elles ne voient ni le candidat
préféré, ni son ordre, ni son coût, ni le prompt, ni la note de l'autre critique.

La sortie perceptuelle contient des sous-notes, les défauts sévères, la
confiance et les désaccords. Il n'existe aucun seuil magique `90/100`.

```text
défaut sévère → FAIL ou PARTIAL selon son caractère bloquant
désaccord >= 2 points → PARTIAL + gate humain
confiance médiane < 0,70 → PARTIAL + gate humain
P0 ou P1 → approbation humaine obligatoire
P2 ou P3 calibré → auto-validation permise
```

Les critiques utilisant le même modèle restent corrélées. Leur désaccord est un
signal d'incertitude, pas une indépendance statistique.

## 14. Publication Open Cloud

La route cible est :

```text
GLB local canonique
→ Assets API Create Asset avec GLB
→ attendre et vérifier l'Operation
→ Package ID de staging
→ export FBX déterministe depuis la même source
→ Assets API Update Asset avec FBX
→ même Package ID, nouvelle version
```

Au 15 juillet 2026, la documentation Roblox présente une contradiction : le
tableau général des Models liste `.fbx`, `.gltf`, `.glb`, `.rbxm` et `.rbxmx`
pour les endpoints de création ou mise à jour, tandis que la section spécifique
« Update an existing asset » limite le remplacement de contenu au FBX. Le
pipeline applique la contrainte la plus restrictive : GLB pour la source et la
création, FBX pour la mise à jour, jusqu'à ce qu'un probe Cloud prouve le
contraire.

Le registre associe une clé stable au Package :

```json
{
  "assetKey": "defense_barricade_small",
  "environment": "staging",
  "packageId": 123456789,
  "lastSourceHash": "sha256:...",
  "lastSemanticAssetHash": "sha256:...",
  "lastPublishedBinary": {
    "format": "fbx",
    "hash": "sha256:..."
  },
  "lastOperationId": "operations/...",
  "lastConfirmedCloudVersion": 2,
  "creator": {
    "type": "Group",
    "id": 12345
  }
}
```

Algorithme :

```text
hash sémantique identique → SKIP
aucun Package ID → CREATE en staging
Package existant + changement → UPDATE après vérification de la cible
Operation en attente → POLL borné
429 → backoff borné avec jitter
permission absente → BLOCKED
réponse incohérente après retries → FAIL
```

Le publisher vérifie le propriétaire et le Package ID avant tout `UPDATE`. Il
ne transforme jamais une erreur de modération ou de permissions en succès.

## 15. Capability probes obligatoires

### 15.1 `CAP-CLOUD-001` — Création et mise à jour du même Package

Prouver :

- création depuis un GLB de staging ;
- Operation terminée ;
- Package ID enregistré ;
- mise à jour FBX du contenu sur le même Package ID ;
- version distante confirmée ;
- ancien état récupérable.

### 15.2 `CAP-CLOUD-002` — Fidélité de l'import

Comparer Blender, manifeste Cloud et Studio :

- noms et hiérarchie ;
- nombre de MeshParts ;
- dimensions et orientation ;
- pivot et contact au sol ;
- matériaux, textures et SurfaceAppearance ;
- présence de toutes les pièces ;
- absence de pièces inattendues ;
- comparaison visuelle normalisée.

Un GLB valide n'implique pas un import fidèle.

### 15.3 `CAP-MCP-001` — Insertion initiale d'un Package

Dans l'instance Studio explicitement sélectionnée :

1. capturer l'état initial du dossier de test ;
2. appeler `insert_asset` avec le Package ID ;
3. localiser exactement la nouvelle instance ;
4. vérifier le conteneur attendu ;
5. rechercher `PackageLink` ;
6. capturer les propriétés réellement lisibles ;
7. capturer la hiérarchie et une image ;
8. supprimer seulement la copie de probe ;
9. vérifier le retour à l'état initial.

La documentation générale des Packages et la capacité MCP annoncée ne sont pas
arbitrées par supposition. Le résultat observable décide.

### 15.4 `CAP-MCP-002` — Réinsertion de la dernière version

Après publication v2 sur le même Package ID :

- réinsérer le Package ;
- prouver que la nouvelle copie contient v2 ;
- comparer dimensions, hiérarchie, géométrie et captures ;
- ne pas dépendre obligatoirement de `PackageLink.VersionNumber` ;
- conserver l'ancienne copie jusqu'à validation complète.

### 15.5 `PackageLink.AutoUpdate`

`PackageLink` n'est pas créable par Luau ordinaire. `AutoUpdate` est `ReadOnly`
dans la référence publique et son écriture est protégée par
`RobloxScriptSecurity`.

Le pipeline ne tente jamais :

```luau
packageLink.AutoUpdate = true
```

Deux stratégies sont admises :

- `AUTOUPDATE_BOOTSTRAPPED` : intervention Studio initiale, sauvegarde, puis
  vérification observable après réouverture ;
- `REINSERT_STAGED_SWAP` : réinsertion de la version courante, validation en
  staging et remplacement récupérable du visuel.

La lecture de `VersionNumber` et l'automatisation d'`AutoUpdate` ne sont pas
requises si `REINSERT_STAGED_SWAP` est prouvé.

## 16. Visual Package et Runtime Wrapper

```text
DEF_BarricadeSmall_Runtime
├── Visual
│   └── PackageRoot
│       └── PackageLink
├── Visual_Staging
├── Visual_Old
├── Collision
│   ├── MainHitbox
│   └── PlacementFootprint
├── Interaction
│   ├── DamageRaycastZone
│   └── RepairAnchor
├── Attachments
├── Metadata
└── RuntimeScripts
```

Le Package contient uniquement :

- géométrie visuelle ;
- matériaux et SurfaceAppearance ;
- pivots visuels ;
- animations et bones purement visuels.

Le wrapper contient :

- collisions et raycast zones ;
- tags et attributs gameplay ;
- scripts et logique réseau ;
- Attachments gameplay ;
- santé et état ;
- références autoritaires.

Les scripts présents dans `data/src` restent modifiés sur disque et synchronisés
par Script Sync. Ils ne sont jamais édités en parallèle via le Studio MCP.

### 16.1 Swap mis en scène et récupérable

Le remplacement n'est pas qualifié d'atomique : Studio ne fournit pas ici de
transaction garantissant l'atomicité.

```text
1. Insérer la nouvelle copie dans Visual_Staging.
2. Vérifier Package ID, hiérarchie, fidélité et comportement.
3. Conserver Visual actif.
4. Renommer Visual en Visual_Old.
5. Promouvoir Visual_Staging en Visual.
6. Vérifier le wrapper complet.
7. Supprimer Visual_Old seulement après succès.
8. En cas d'échec, restaurer Visual_Old.
```

Le configurateur est idempotent et sait récupérer un état interrompu contenant
`Visual_Staging` ou `Visual_Old`.

## 17. Tests Studio

Avant toute modification, Codex :

1. liste les Studio connectés ;
2. sélectionne et confirme l'instance attendue ;
3. confirme les DataModels disponibles ;
4. vérifie les subtrees gérés par Script Sync ;
5. utilise un dossier de staging isolé.

Tests structurels :

- Package et wrapper attendus ;
- noms, tags, attributs et pivots ;
- aucun duplicata ;
- ancienne version absente après validation ;
- idempotence d'une seconde configuration ;
- restauration après échec simulé.

Tests gameplay :

- navigation joueur ;
- collisions ;
- raycasts ;
- placement ;
- projectiles ;
- contacts ;
- pathfinding ;
- dégâts et états visuels ;
- caméra proche ;
- lisibilité aux distances cibles ;
- interactions clavier, tactile et manette applicables.

Le playtest inspecte les sorties client et serveur. Une capture seule ne prouve
pas la logique ; une console propre seule ne prouve pas le gameplay.

## 18. Benchmarks

### 18.1 Scènes

```text
Scene_0   baseline sans asset
Scene_1   un exemplaire
Scene_30  usage normal attendu
Scene_100 stress synthétique
```

`Scene_100` est un stress test, pas une exigence de gameplay normale.

### 18.2 Mesures structurelles

Scene Analysis peut fournir notamment :

- composition d'instances ;
- triangles et draw calls ;
- mémoire de scripts ;
- mémoire audio et animation ;
- instances non parentées.

Il ne fournit pas à lui seul l'ensemble du benchmark runtime.

### 18.3 Mesures runtime

| Mesure | Instrument principal |
|---|---|
| frame time, rendu, physique, scripts | MicroProfiler |
| FPS | Performance Stats |
| mémoire totale, meshes, textures | Developer Console / Stats |
| réseau | Debug Stats / Developer Console |
| chargement | instrumentation dédiée |
| triangles et draw calls | SceneAnalysisService |

### 18.4 Protocole

Vertical slice :

```text
60 s de warm-up
5 passages baseline
5 passages asset
ordre AB/BA alterné
caméra et trajet identiques
médiane + MAD + min/max
```

Release :

```text
90 s de warm-up
10 passages baseline
10 passages asset
ordre randomisé et enregistré
médiane + dispersion + intervalle de confiance
```

Les cold starts et warm runs sont séparés. Aucun seuil fin n'est fixé avant
mesure du bruit :

```json
{
  "status": "UNCALIBRATED",
  "noiseFloor": null,
  "maximumAcceptedDelta": null
}
```

Pour P0 et P1, la validation finale exige Studio, un client desktop publié de
staging et un appareil mobile cible. Les performances sur le PC de développement
ne prouvent pas les performances mobiles.

## 19. Orchestration Codex

Les validateurs déterministes restent des scripts. Les agents ne les remplacent
pas.

Configuration minimale lorsque la délégation est explicitement autorisée et
utile :

```text
Orchestrator
├── scripts déterministes Blender / QA
├── Roblox Integration Auditor
├── Visual Critic A
└── Visual Critic B
```

Les tâches sont bornées et compatibles avec les slots réellement disponibles.
Le pipeline fonctionne aussi sans subagents. `codex exec` est réservé à
l'automatisation non interactive ; une session Codex interactive peut exécuter
directement le même point d'entrée.

Commandes installées pour la vertical slice :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 doctor --repo .
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 test
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 validate .\assets-3d\defense-barricade-small\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 compile .\assets-3d\defense-barricade-small\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 compile-states .\assets-3d\defense-barricade-small\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 verify-states .\assets-3d\defense-barricade-small\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 canon-packet .\assets-3d\defense-barricade-small\asset.json
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 publish .\assets-3d\defense-barricade-small\asset.json --dry-run
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\r3d.ps1 report .\assets-3d\defense-barricade-small\asset.json
```

La mutation Cloud exige trois variables privées dans le processus opérateur :
`ROBLOX_OPEN_CLOUD_API_KEY`, `ROBLOX_STAGING_CREATOR_ID` et
`ROBLOX_3D_ALLOWED_CREATOR_IDS`. L'identifiant du créateur doit apparaître dans
l'allowlist et `--confirm-publish` reste obligatoire. Ces valeurs ne sont jamais
écrites dans le dépôt.

## 20. Doctor, Git et write set

Le doctor vérifie :

```text
Git
Python exact utilisé par l'orchestrateur
Codex lorsque le mode non interactif l'exige
Blender et version exacte
Studio MCP
instance Studio attendue
credentials sans les afficher
permissions du propriétaire de staging
publisher adapter
write set Git
espace disque et dossiers de sortie
```

Politique de worktree :

```text
fichiers sales hors write set → WARN
fichiers asset cible sales → BLOCKED_DIRTY_TARGET
fichiers pipeline sales → BLOCKED_DIRTY_PIPELINE
fichiers utilisateur non liés → préserver
```

Un worktree dédié est recommandé pour un travail parallèle ou risqué, mais son
emplacement n'est pas codé en dur dans le dépôt.

## 21. Politique des binaires

Suivi Git normal :

- briefs et schémas ;
- scripts Python, Luau et PowerShell ;
- ExecPlans applicables ;
- provenance et hashes ;
- registres de Package IDs ;
- rapports finaux légers ;
- captures finales sélectionnées.

Artefacts temporaires ignorés ou stockés hors Git :

- GLB de build reconstruisibles ;
- rendus intermédiaires ;
- logs et dumps MicroProfiler ;
- candidats rejetés ;
- caches et textures dérivées.

Git LFS n'est ajouté qu'après décision explicite et besoin concret, pour une
source binaire réellement autoritative et non reconstruisible. Il n'est pas
installé simplement pour satisfaire cette spécification.

## 22. Politique d'itération

```json
{
  "maximumIterations": 3,
  "maximumExplorationCandidates": 6,
  "stopAfterRepeatedFailureCount": 2,
  "maximumGenerationCost": "configured-per-run"
}
```

```text
itération 1 → correction directe
itération 2 → stratégie alternative
itération 3 → simplification ou reconstruction
nouvel échec → PARTIAL ou FAIL + intervention humaine
même échec deux fois → STOP_REPEATED_FAILURE
```

Le rapport indique la cause probable, les preuves, les tentatives, les
différences et l'action humaine minimale.

## 23. Vertical slice obligatoire

Asset : `defense_barricade_small`  
Dimensions : 8 × 2 × 4 studs  
Budget : moins de 2 000 triangles pour la preuve initiale  
Structure : trois panneaux, deux pieds, un voyant  
Collision : Parts simples dans le wrapper

### Passage v1

```text
doctor
→ compilation déterministe
→ gates
→ rendus
→ Create Asset staging
→ CAP-CLOUD-001 création
→ CAP-CLOUD-002 fidélité
→ CAP-MCP-001 insertion
→ wrapper
→ tests et benchmarks non calibrés
→ rapport
```

### Passage v2

Modifier de façon observable :

- largeur du panneau central ;
- hauteur du voyant ;
- palette d'accent ;
- nombre de renforts.

Puis :

```text
rebuild
→ Update Asset sur le même Package ID
→ CAP-CLOUD-001 mise à jour
→ CAP-MCP-002 dernière version
→ REINSERT_STAGED_SWAP
→ wrapper intact
→ tests de non-régression
→ rapport
```

### Conditions de réussite

```text
[PASS] build v1 déterministe
[PASS] validations v1
[PASS] Package v1 de staging publié
[PASS] fidélité import v1
[PASS] insertion initiale MCP
[PASS] PackageLink présent
[PASS] wrapper configuré
[PASS] tests 1/30/100 exécutés et rapportés honnêtement
[PASS] v2 publiée sur le même Package ID
[PASS] fidélité import v2
[PASS] v2 observable dans Studio
[PASS] staged swap récupérable
[PASS] wrapper, hitboxes, scripts, tags et attributs intacts
[PASS] aucune erreur console pertinente
[PASS] rapport structuré produit
```

Tant que ces critères n'ont pas été observés, le pipeline d'implémentation ne
reçoit pas `PASS`.

## 24. Condition de création du skill

Le skill `roblox-3d-asset` est créé seulement lorsque :

- les passages v1 et v2 sont prouvés ;
- les quatre probes principaux ont un résultat observable ;
- le publisher est idempotent ;
- la récupération d'un swap interrompu est testée ;
- un rapport conforme au schema est produit ;
- les commandes exactes sont stabilisées ;
- les secrets sont absents des artefacts et logs ;
- les comportements inconnus restent explicitement déclarés.

Le skill emballe le workflow prouvé ; il ne sert pas à masquer un prototype
incomplet.

## 25. Rapport machine-readable minimal

```json
{
  "assetKey": "defense_barricade_small",
  "status": "UNKNOWN",
  "productionApproved": false,
  "mode": "PublishStaging",
  "iterationCount": 0,
  "capabilities": {
    "cloudCreateAndUpdatePackage": {
      "status": "UNKNOWN",
      "evidence": "NOT_RUN",
      "required": true
    },
    "cloudImportFidelity": {
      "status": "UNKNOWN",
      "evidence": "NOT_RUN",
      "required": true
    },
    "mcpPackageInitialInsert": {
      "status": "UNKNOWN",
      "evidence": "NOT_RUN",
      "required": true
    },
    "mcpReinsertLatestVersion": {
      "status": "UNKNOWN",
      "evidence": "NOT_RUN",
      "required": true
    },
    "autoUpdateWritableFromLuau": {
      "status": "UNSUPPORTED",
      "evidence": "DOCUMENTED",
      "required": false
    }
  },
  "geometry": {},
  "publication": {},
  "studio": {},
  "performance": {},
  "perceptual": {},
  "humanApproval": {},
  "checks": [],
  "blockingReasons": [],
  "unknowns": []
}
```

## 26. Références officielles

- [Roblox Studio MCP](https://create.roblox.com/docs/studio/mcp)
- [Open Cloud Assets usage guide](https://create.roblox.com/docs/cloud/guides/usage-assets)
- [Open Cloud API keys](https://create.roblox.com/docs/cloud/auth/api-keys)
- [Roblox Packages](https://create.roblox.com/docs/projects/assets/packages)
- [PackageLink API](https://create.roblox.com/docs/reference/engine/classes/PackageLink)
- [Roblox modeling specifications](https://create.roblox.com/docs/art/modeling/specifications)
- [Roblox texture specifications](https://create.roblox.com/docs/art/modeling/texture-specifications)
- [Roblox collisions](https://create.roblox.com/docs/workspace/collisions)
- [Roblox Scene Analysis](https://create.roblox.com/docs/performance-optimization/scene-analysis)
- [Roblox MicroProfiler](https://create.roblox.com/docs/performance-optimization/microprofiler)
- [Roblox hardware testing](https://create.roblox.com/docs/performance-optimization/test-on-hardware)
- [Official Roblox Blender plugin](https://github.com/Roblox/roblox-blender-plugin)
- [Blender command line](https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html)
- [Blender Mesh API](https://docs.blender.org/api/current/bpy.types.Mesh.html)
- [Blender BMesh API](https://docs.blender.org/api/current/bmesh.html)
- [Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [Codex AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
- [Codex non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode)

## 27. Règle finale

> Codex planifie et orchestre. Blender compile. Le Visual Workbench observe,
> diagnostique et expérimente sans devenir la source. Le change set explique ;
> la recette conserve ; la recompilation prouve. Les scripts déterministes
> bloquent les défauts. Open Cloud publie et versionne en staging. Le MCP est
> testé avant d'être cru. Le Package ne contient que le visuel. Le wrapper
> protège le gameplay. Les performances sont expérimentées, pas supposées. Les
> critiques perceptuelles signalent l'incertitude. L'humain conserve l'autorité
> artistique et de production.
