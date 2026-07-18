# Changelog

## Unreleased

- Ajoute `r3d canon-packet`, qui rend deux séries Blender réelles, vérifie dix
  vues brutes, compose deux fois les dix-sept familles de planches 1920 × 1080
  et publie une galerie de revue liée aux hashes du canon et du build.
- Ajoute un cache strictement lié au contrat, canon, `.blend`, manifeste de
  build, renderer et SHA-256 de chaque PNG ; `--force` reconstruit les deux
  séries, sans désinstaller ni réinstaller le workflow.
- Ajoute le schéma `visual-canon-evidence`, refuse les chemins absolus ou
  sortants, les dimensions ou hashes dérivés, les autorités manquantes et toute
  preuve synthétique lors d'un lock de production.
- Prouve le paquet de la barricade r6 : `REAL_RENDERED`, 17/17 planches,
  déterminisme brut et composition `PASS`, revue humaine `PENDING` et
  `productionApproved=false`.
- Transforme la galerie en poste de revue local : 17 choix de planche, sept
  gates, progression persistante, décisions cohérentes et téléchargement d'une
  revue humaine liée au digest.
- Exige cette revue structurée pour tout lock réel, la copie dans le paquet de
  preuve lors de `-Apply`, son hash dans l'overlay et le refus des décisions
  incomplètes, contradictoires, dérivées ou simulées.

- Ajoute les familles d'états déterministes `intact`, `damaged` et `critical`
  au compilateur vertical-slice, avec overrides topology-preserving, matériaux
  d'état, rails segmentés et socket arrière protégé.
- Ajoute `compile-states`, la planche ergonomique `state-review.html` et
  `verify-states`, qui compile deux fois chaque état et vérifie géométrie, GLB,
  FBX à chemin canonique, hashes sémantiques, rendus, invariants et
  distinctness.
- Compare désormais la famille publiée aux références A/B. Les PNG sont
  décodés en RGBA8 et doivent être exacts ou respecter trois micro-bornes
  raster enregistrées ; toute différence supérieure bloque
  `stateDeterminism` et `stateReviewBoard`.
- Lie le maximum triangles local au maximum extrait du canon et refuse toute
  dérive ; la barricade révision 6 utilise 1 468 triangles, sous la cible de
  1 500 et le plafond de 2 000.
- Ajoute une inspection Workbench finale de 29 composants, une revue visuelle
  interne révision 6 à 92/100 et un paquet de preuve durable ; aucune de ces
  preuves ne remplace le lock humain, Studio ou le mobile physique.
- Fixe explicitement l’export PNG RGBA8, le dithering et les échantillons
  EEVEE ; ajoute une stabilisation intra-build, un test de régression de
  tolérance pixel et corrige l’ancienne qualification erronée de « PNG
  corrompu » en anomalie d’affichage de l’outil d’inspection.
- Rend les tests de contrat indépendants du chemin d’installation et remplace
  le build exemple révision 3 embarqué par la révision 6 courante ; le wrapper
  `art-direction test` passe ainsi depuis la racine comme depuis le package.
- Désactive les sauvegardes Blender versionnées pour les compilations headless
  et supprime le sidecar généré `source.blend1` dans chaque sortie courante.
- Rend le gate `visualReview` fail-closed : `r3d report` vérifie désormais
  identité, révision, confinement et existence de chaque preuve déclarée, et
  refuse un `PASS` sans approbations automatisée et humaine concordantes.

- Ajoute `simulate-workflow`, une répétition intégrale et isolée des douze
  étapes du pipeline, des seize états précanoniques jusqu'au rollback Studio.
- Exerce les contrats humains, mobiles, Studio et de publication avec des
  doubles synthétiques confinés sous `build/simulations/complete-workflow/`.
- Interdit tout réseau, secret, appel Studio ou mutation cloud pendant cette
  répétition et vérifie par hash que les canons autoritatifs restent inchangés.
- Maintient explicitement `productionApproved=false` et exige que les
  validateurs de production rejettent les preuves synthétiques.

- Corrige le parcours `workbench` : le mode `smoke` saute explicitement la
  queue Studio réservée aux preuves `FULL_COMPLETE`, tandis que le mode `full`
  conserve son gate obligatoire.
- Route le doctor `r3d` depuis la racine réelle du projet et normalise les
  chemins relatifs de tous les rapports Studio, simulateur et mobile.
- Ajoute des régressions contractuelles et une reproduction intégrale du
  parcours `workbench -RenderMode smoke`.

- Ajoute un Blender Visual Workbench MCP local `stdio`, sans listener TCP ni
  outil Python arbitraire, avec douze outils de haut niveau sous allow-list.
- Lie chaque session aux hashes exacts du contrat, du canon, du générateur et
  du build ; sépare `Reference` immuable et `Candidate` réversible.
- Ajoute preview sans sauvegarde, opérations bornées, diff, invariants,
  backups, rollback exact et journal append-only.
- Traduit les expérimentations en change sets et JSON Pointers, puis vérifie la
  reproduction dans une source sandbox par deux compilations déterministes.
- Corrige l'unique octet FBX dépendant de `build-a`/`build-b` en normalisant le
  chemin source embarqué, puis exige GLB et FBX byte-identiques en plus du hash
  sémantique ; le générateur enregistre désormais son propre SHA-256.
- Prouve la vertical slice `defense_barricade_small` : deux pieds modifiés,
  delta triangles nul, rollback au hash baseline et builds A/B identiques.
- Conserve le contrat autoritatif, Studio, le mobile et l'approbation de
  production inchangés ; `productionApproved=false`.

- Ajoute un audit visuel fermé de 32 constats, lié par SHA-256 au premier
  résultat réel sans modifier la requête, le résultat, la revue ou l’image.
- Distingue les limites normales du sheet d’exploration des défauts bloquants
  pour une définition canonique d’état.
- Verrouille une construction unique dans les quatre vues et interdit toute
  dérive de composants, joints, matériaux, usure, réparation ou état.
- Exige cinq évaluations `PASS` et une règle à préserver avant acceptation ;
  exige une correction pour réviser ou rejeter et une interdiction pour rejeter.
- Corrige le canon qui autorisait encore un symbole d’assemblage et interdit
  pseudo-logos, composite minéral, menthe en façade et renfort décoratif.
- Remplace la campagne v1 non consommée par une campagne v2 recompilée, tout
  en conservant v1 comme preuve historique et sans réinstallation.

- Transforme la liste objet × état en explorateur complet : les seize états
  restent sélectionnables, y compris avant leur première génération.
- Ajoute les filtres `pas encore générés`, `avec une génération`, `à revoir`,
  `acceptés`, `bloqués` et `pas encore acceptés`.
- Sépare strictement la consultation de la tâche active : naviguer ne change
  ni `currentTaskId`, ni le budget, ni les preuves.
- Ajoute navigation précédent/suivant, raccourcis clavier, historique du
  navigateur, liens profonds et retour immédiat vers la production active.
- Affiche pour chaque état son statut expliqué, son ordre, sa dépendance de
  continuité, sa décision et toutes ses tentatives.
- Rend individuellement consultables les images rejetées ou à réviser au lieu
  de ne conserver qu’un aperçu de la dernière génération.
- Remplace les états futurs désactivés par des fiches planifiées explicites
  indiquant pourquoi et quand ils seront déverrouillés.
- Adopte le développement in-place : tests ciblés et manifeste vérifié pendant
  l’itération, packaging et réinstallation uniquement aux jalons de release.

## 3.14.0 - 2026-07-16

- Remplace le poste à requête terminale par une campagne persistante couvrant
  exactement les six objets Salvaged Frontier et leurs seize états applicables.
- Exige une génération `gpt-image-2` distincte par couple objet × état, avec
  confirmation visible du modèle et une seule génération par requête.
- Interdit la conception indépendante des états : chaque état suivant reçoit
  comme référence hashée l’état précédent accepté du même objet.
- Ajoute une navigation complète par objet et par état, une progression 0/16,
  un aperçu des résultats enregistrés, la prochaine tâche et un écran final.
- Fait avancer immédiatement une revue acceptée vers l’état ou l’objet suivant
  au lieu de laisser l’interface figée en `REVIEW_RECORDED`.
- Transforme `REVISION_REQUIRED` et `REJECTED` en nouvelles tentatives
  explicites et bornées sur le même état, sans retry automatique.
- Ajoute le schéma fermé de campagne, le compilateur objet × état, la
  réconciliation après interruption, les routes HTTP de consultation et les
  tests de progression complète jusqu’à 16/16.
- Ajoute un remplacement d’installation vérifié fichier par fichier après
  sauvegarde complète lorsque Windows bloque le déplacement atomique du
  dossier surveillé.
- Conserve `precanon-operator` comme voie historique compatible pour les
  preuves déjà créées.

## 3.13.0 - 2026-07-16

- Ajoute une porte d'entrée documentaire unique et un contrat explicite de
  statut séparant verrou créatif, verrou canonique et verrou de production.
- Décrit complètement les six objets Salvaged Frontier et leurs seize variantes
  applicables, sans produit cartésien d'états.
- Ajoute une ontologie orthogonale pour intégrité, exploitation, action,
  interaction, affiliation, lifecycle et événements transitoires.
- Ferme les contrats d'axes, matrices, normales, tangentes, export Blender,
  import Roblox, budgets, collision, instancing, VFX, mobile et accessibilité.
- Formalise les métriques visuelles, responsabilités, waivers, dépréciations,
  risques et menaces du pipeline.
- Marque les preuves Studio/Cloud v3.7 comme historiques et restaure les
  statuts courants `UNKNOWN`, `PARTIAL` et `BLOCKED` applicables.
- Synchronise le portail du dépôt, le registre documentaire, le contrat 3D et
  l'ExecPlan sans modifier les assets ni fabriquer de preuve de production.

## 3.12.0 - 2026-07-16

- Ajoute `precanon-operator`, le pont humain semi-automatique officiel quand
  la tâche Codex n'expose pas le contrôle Browser.
- Réduit l'intervention humaine à copier/coller le texte exact, demander une
  génération, télécharger une image, la déposer et choisir une décision.
- Recalcule automatiquement le preflight et compose un texte de soumission
  unique contenant le prompt et toutes les contraintes négatives liées.
- Ajoute une interface locale autonome, responsive et sans dépendance externe,
  servie uniquement sur `127.0.0.1` avec un jeton non persisté.
- Automatise validation d'image, budget, doublons, import, provenance, hashes,
  identité du résultat, aperçu et revue humaine.
- Ajoute une attestation humaine bornée sans prétendre observer le
  fonctionnement interne de ChatGPT Web.
- Rend les sessions reprenables après import et bloque toute altération du
  texte soumis, des pièces jointes ou du chemin de sortie.
- Conserve zéro API, zéro retry automatique, zéro lecture de cookie et
  `productionApproved=false`.

## 3.11.0 - 2026-07-16

- Corrige l'hypothèse erronée de la version 3.10.1 : le serveur
  `mcp_servers.node_repl`, ses variables `NODE_REPL_*` / `BROWSER_USE_*` et le
  canal natif peuvent être générés légitimement par l'application Codex.
- Interdit leur suppression, copie ou modification manuelle tout en refusant
  de considérer leur présence comme une preuve de capacité de la tâche.
- Ajoute `precanon-browser-doctor`, qui vérifie le plugin sélectionné, le
  backend, le serveur MCP, l'outil `js` et l'hôte natif Chrome sans consommer
  de quota ni contrôler le navigateur.
- Sépare formellement trois gates : contrat artistique local, installation
  Browser locale et exposition de `mcp__node_repl__js` dans la tâche courante.
- Remplace le faux état `READY_FOR_WEB_GENERATION` du preflight par
  `WEB_PREFLIGHT_PASS`.
- Place le handoff en `AWAITING_TASK_BROWSER_CAPABILITY` et exige un rapport
  Browser doctor lié par SHA-256.
- Ajoute l'état d'erreur `WEB_TASK_CAPABILITY_UNAVAILABLE` et interdit aux
  scripts du dépôt d'invoquer directement `node_repl` comme proxy caché.

## 3.10.1 - 2026-07-16 — superseded by 3.11.0

- Avait supprimé de la configuration locale Codex le bridge Browser considéré
  à tort comme obsolète, qui
  persistait un serveur `node_repl`, un drapeau `js_repl` supprimé et un
  identifiant de pipe natif éphémère.
- Clarifie que le preflight précanonique valide le contrat artistique et le
  quota, mais ne prouve pas que la tâche courante expose le transport Browser.
- Interdit de recopier dans `config.toml` des variables internes
  `NODE_REPL_*`, `BROWSER_USE_*` ou des identifiants de canal propres à une
  tâche.
- Exige un redémarrage complet et une tâche fraîche après toute correction de
  configuration Browser.
- Conserve la réparation du native host Chrome dans le flux officiel de
  réinstallation du plugin, sans modification directe du registre.

## 3.10.0 - 2026-07-16

- Ajoute `codex_iab` comme adaptateur officiel explicitement sélectionnable
  pour les requêtes ChatGPT Web sans pièce jointe.
- Conserve `codex_chrome` comme adaptateur par défaut et comme unique transport
  autorisé lorsque des références hashées doivent être envoyées.
- Ajoute un gate préflight qui bloque toute combinaison
  `codex_iab + attachments`.
- Interdit toute bascule automatique entre navigateurs et conserve les
  interdictions de retry, imagegen et API automatiques.
- Propage l'adaptateur exact dans le handoff, la CLI PowerShell et la CLI shell.
- Ajoute des tests de matrice valides et adversariaux pour les schémas,
  le preflight et les handoffs.

## 3.9.0 - 2026-07-16

- Ajoute une couche précanonique avant la définition canonique et Blender.
- Lie chaque demande visuelle à la constitution Salvaged Frontier, au brief,
  au prompt, aux contraintes négatives, aux vues et aux états par SHA-256.
- Ajoute quatre étapes bornées : exploration, consolidation, planche
  précanonique et correction ciblée.
- Ajoute un préflight sans consommation de quota qui bloque les hashes périmés,
  les budgets épuisés, les prompts déjà réussis et tout fallback automatique.
- Ajoute un handoff ChatGPT Web explicite et sanitised dont
  `submissionAuthorized=false`; Chrome reste un transport remplaçable.
- Ajoute l'import des images avec octets bruts, dimensions, format, provenance
  prudente et rejet des doublons.
- Ajoute quatre décisions de revue sans promotion directe en canon :
  `REJECTED`, `REVISION_REQUIRED`, `PRECANONICAL_CANDIDATE` et
  `HUMAN_SELECTED`.
- Exige un reviewer humain nommé et cinq dimensions `PASS` pour
  `HUMAN_SELECTED`, qui autorise seulement la canonicalisation.
- Ajoute un paquet d'exploration réel pour `Defense Barricade Small`, la
  documentation opérateur et des tests adversariaux.
- Conserve `productionApproved=false` et toutes les gates 3D, Studio, mobile
  et humaines existantes.

## 3.8.0 - 2026-07-16

- Enregistre la sélection stratégique du fondateur :
  `salvaged-frontier`.
- Fige la règle de précédence : Salvaged Frontier porte l'identité du monde ;
  Industrial Toy Defense impose uniquement la discipline de lisibilité.
- Ajoute une constitution créative machine-readable couvrant vingt-et-un
  scopes : monde, formes, construction, matériaux, palette, architecture,
  biomes, buildables, objectifs, ennemis, avatars, états, VFX, animation, UI,
  caméra, social, génération, marketing et répétition.
- Ajoute la bible humaine complète
  `docs/SALVAGED_FRONTIER_ART_BIBLE.md`.
- Optimise la grammaire exécutable autour d'un châssis standardisé à 75–85 %,
  d'une adaptation causale à 15–25 %, d'une asymétrie cible de 0,24 et d'une
  hiérarchie 72/23/5.
- Remplace le bois secondaire universel par un composite récupéré et réserve
  le bois aux contextes structurellement plausibles.
- Raffine palette, biseaux, matériaux, recettes des cinq assets et contrat de
  transfert de la tourelle.
- Corrige deux dérives observées dans les rendus : poutre cuivre trop dominante
  sur la barricade et signaux mint alliés sur l'ennemi.
- Migre le vertical slice `Defense Barricade Small` en révision 2 vers le canon
  Salvaged Frontier tout en conservant ses noms de pièces stables.
- Lie chaque canon généré au hash exact de la constitution sélectionnée.
- Régénère `turret_fast_v1` contre les règles courantes : 9 builds, 108 rendus,
  déterminisme `PASS` et score automatique `100/100`; l'approbation humaine
  reste `PENDING`.
- Permet au verrou final d'utiliser soit la décision stratégique du fondateur,
  soit une étude aveugle scellée, sans fabriquer de dataset inexistant.
- Limite correctement le gate de production aux six canons Salvaged Frontier
  sélectionnés.
- Conserve honnêtement `productionApproved=false`: Studio, mobile, les six
  locks multimodaux et les approbations humaines restent ouverts.
- Préserve automatiquement les preuves humaines locales lors d'une
  réinstallation transactionnelle avec `-Replace`.

## 3.7.0 - 2026-07-16

- Ajoute une étude aveugle exécutable pour la sélection finale de la direction
  artistique.
- Prépare douze slots participants et quatre slots experts, avec 30 essais
  chronométrés par participant et 27 évaluations par expert.
- Réencode et anonymise les stimuli, équilibre les ordres, retire les noms de
  territoire et bloque toute fuite dans les dossiers ou ZIP publics.
- Ajoute les interfaces HTML autonomes participant/expert, les schémas de
  sessions, la collecte pseudonymisée et le scellement hash-bound.
- Lie les preuves techniques par candidat sans convertir les gates CVD,
  provenance humaine ou mobile physique manquants en faux `PASS`.
- Ajoute `prepare-study` et `seal-study`; le scoreur reste incapable de choisir
  automatiquement une direction.
- Rafraichit les gates techniques au scellement sans changer le paquet public,
  la carte aveugle ou les sessions humaines.
- Exclut les preuves humaines locales et la carte aveugle privée des archives
  de distribution du workflow.

## 3.6.0 - 2026-07-16

- Ajoute une définition canonique visuelle obligatoire avant toute génération
  de production.
- Compile déterministement 18 canons `objet x DA` couvrant les six objets, les
  trois territoires et les 48 états applicables.
- Lie chaque canon aux hashes exacts du GDD, de la doctrine de rétention, de la
  grammaire artistique, des budgets et du compilateur.
- Décrit identité, lecture en une seconde, vues complètes, proportions,
  composants, matériaux, zones sémantiques, états, transitions, invariants,
  libertés et interdictions.
- Exige dix-sept familles de planches multimodales et des signaux d'état
  redondants au-delà de la couleur.
- Ajoute les statuts `DRAFT`, `CANDIDATE`, `ACCEPTED`, `LOCKED` et `REVISED`,
  avec overlay de verrou séparé, décision humaine et digest de preuves.
- Ajoute les enveloppes pré-génération hashées, les rapports de conformité
  post-build et le gate `-RequireLockedCanons`.
- Ajoute un inspecteur Blender indépendant et une table de correspondance
  hashée pour prouver chaque composant canonique dans chaque état, sans polluer
  le canon artistique avec des noms d'implémentation.
- Lie le moteur r3d par asset au canon exact dans le contrat, la provenance, le
  manifeste de build et la vérification avant publication.
- Conserve honnêtement les 18 canons en `CANDIDATE`: la DA finale, les planches
  liées, la signature humaine et le mobile physique restent ouverts.

## 3.5.0 - 2026-07-16

- Detecte par capture officielle que le round-trip Open Cloud Model vers Studio
  conservait la geometrie mais perdait les couleurs et materiaux du GLB.
- Reapplique deterministement chaque role `ROLE_*` depuis les palettes,
  affectations de surface et profils materiaux canoniques, sans asset ID ni
  configuration artistique ad hoc.
- Accepte les deux formes de nom Roblox observees, `ROLE_primary` et
  `ROLE_primary_Mesh`, tout en rejetant chaque role inconnu ou non lie.
- Ajoute au readback Studio le nombre de MeshParts styles, les roles non lies,
  l'erreur de couleur maximale et le verdict exact des liaisons materiaux.
- Lie les trois captures transfert par territoire, chemin, octets et SHA-256,
  puis verifie leur integrite dans la validation semantique.
- Passe l'integration transfert Studio a `PASS`: 9/9 assets, 59 MeshParts
  styles, zero role non lie, six groupes 30/100, playtest Client/Server propre
  et trois captures viewport fideles.

## 3.4.0 - 2026-07-16

- Ajoute `publish-transfer`, un batch publisher staging-only pour les neuf GLB
  du challenge `turret_fast_v1`.
- Revalide le manifeste, tous les SHA-256, le digest de preuve, la limite de
  20 MB, les credentials presents, le creator numerique et son allowlist avant
  toute mutation.
- Exige `-ConfirmPublish`; sans ce switch, la commande reste un dry-run sans
  ecriture locale ni distante.
- Reprend automatiquement une publication interrompue, verifie chaque identite
  distante et conserve les identifiants Roblox uniquement dans un registre
  local genere et exclu du package.
- Produit une preuve portable sanitisee qui ne contient ni asset ID, ni creator
  ID, ni operation path, ni cle.
- Conserve le registre brut necessaire aux reprises dans
  `assets-3d/registry/*.local.json`, deja gitignore et hors du dossier remplace
  par l'installateur, afin d'eviter toute republication apres mise a jour.
- Preserves byte-for-byte the canonical publication evidence when a confirmed
  rerun only rereads and revalidates the same nine remote identities.
- Publie aussi une copie portable byte-identical du manifeste d'upload et lie
  les preuves live aux hashes du publisher, du client HTTP, du builder de queue,
  du bridge Studio et du client MCP.
- Recharge silencieusement les trois variables staging Windows configurees au
  niveau utilisateur lorsque le processus Codex courant ne les a pas heritees.
- Ajoute `stage-transfer`, un bridge MCP transactionnel qui exige `-Apply`,
  refuse plusieurs sessions Studio, reverifie la place staging et le creator,
  insere les neuf assets, compare leurs bounds aux GLB canoniques, configure
  MeshParts et hitboxes, construit une scene de revue et six groupes 30/100,
  puis lance un playtest Client/Server avec delta de console.
- Maintient l'integration transfer a `PARTIAL` lorsque le coeur 9/9, 30/100 et
  playtest passe mais que le bridge MCP stdio ne retourne pas les captures
  viewport; aucun changement visuel ne recoit un faux PASS.

## 3.3.0 - 2026-07-16

- Ajoute le sixieme asset inedit `turret_fast_v1` sans modifier le compilateur
  ni les cinq assets de calibration.
- Ferme le challenge de transfert par schema: aucune nouvelle palette, famille
  d'angles, classe materielle, famille de biseau ou grammaire de degats.
- Compile trois etats dans les trois territoires, avec neuf builds Blender,
  determinisme A/B, neuf GLB canoniques et 108 rendus de preuve.
- Mesure silhouette intact/damaged/critical, severite, front/arriere,
  distinction inter-territoires et cadrage paysage/portrait.
- Produit 51 artefacts portables de territoire, une galerie et deux contact
  sheets lies par un digest SHA-256 unique.
- Ajoute la commande ergonomique `art-direction transfer -Open` et son mode
  strict `-RequirePass` reserve a l'approbation humaine signee.
- Porte la verification a 35 schemas, 30 instances et 65 tests adversariaux.
- Conserve le transfert global a `PARTIAL`: l'automatisation passe 100/100,
  mais aucun outil ne choisit ni ne signe le territoire a la place de l'humain.

## 3.2.0 - 2026-07-16

- Corrige les cameras de Golden Scene qui restaient hors de l'espace isole,
  ajoute une regression et regenere les 12 captures Studio hash-bound.
- Porte la matrice Blender complete a 1 263 rendus, soit 421 par territoire,
  plus six stress renders, sans changer les 39 exports deterministes.
- Rejoue les trois validations Studio avec sources SHA-256, profils lumineux,
  cameras isolees et repetition 30/100.
- Capture les quatre conditions du benchmark graybox/candidat et retire
  uniquement les proxies de collision totalement invisibles des clones de
  comparaison de rendu.
- Revalide le probe v1 vers v2 observe dans Studio et lie son rapport aux
  hashes actuels sans persister d'identifiant Roblox brut.
- Etend la verification a 30 schemas, 27 instances, 58 tests adversariaux et
  15 tests r3d.
- Exclut du manifeste immutable les deux rapports statiques horodates que les
  validations locales regenerent, afin que le check post-install reste stable.
- Maintient le simulateur a PARTIAL et la production a false tant que LibMP,
  SceneAnalysis, le mobile physique et l'autorite artistique restent ouverts.

## 3.1.0 - 2026-07-16

- Remplace le blockout smoke par trois grammaires visuelles structurelles et
  materielles, avec etats causaux et presentation calibree.
- Execute la matrice Blender complete: 39 variantes, 1 224 rendus, six stress
  renders et determinisme GLB A/B.
- Valide trois Golden Scenes Roblox Studio, 12 captures hash-bound et un
  reimport v1 vers v2 preservant les proprietes Roblox.
- Ajoute un benchmark graybox/candidat 30/100 et un rapport simulateur exact
  qui reste honnetement PARTIAL quand les APIs diagnostiques ne repondent pas.
- Integre le moteur per-asset r3d et compile la barricade a 1 080 triangles.
- Ajoute le skill progressif `roblox-3d-asset`, 52 tests adversariaux et 15
  tests r3d.
- Ajoute un installateur transactionnel avec staging, SHA-256, validations,
  backups et activation atomique a l'echelle des dossiers.
- Transmet explicitement le runtime Python verifie au premier bootstrap stage,
  y compris quand les alias Windows Store ne pointent vers aucun interpreteur.
- Conserve `productionApproved=false` tant que mobile physique, etude aveugle,
  art lock et sixieme asset ne sont pas prouves.

## 3.0.0 — 2026-07-15

- Rebuilt the v2 package around evidence obtained on Windows PowerShell 5.1 and
  Blender 5.2 LTS.
- Added a package-local Python bootstrap with 14 exact dependency versions.
- Replaced the global five-assets-by-three-states assumption with 13 applicable
  variants per territory.
- Classified recipe fields and made every state strategy compiler-recognized.
- Preserved damaged-state proportions through reference-scale plus uniform fit.
- Reduced deterministic blockout geometry so every original triangle budget
  passes without tolerance or budget inflation.
- Canonicalized GLB UV precision and triangle order; added A/B byte-determinism
  verification for all 39 exports.
- Fixed Windows path separators in build reports.
- Fixed Luau generation for reserved keys such as `function` and `local`.
- Added StyLua, Selene and Luau LSP validation with pinned Roblox definitions.
- Added explicit human provenance approval as an art-lock prerequisite.
- Executed 39 builds, 324 smoke renders and six stress renders successfully.
- Added a schema-validated smoke attestation containing the 324 render hashes
  and six stress-render hashes without packaging generated build artifacts.
- Expanded the adversarial suite from 30 to 40 tests.

## 2.0.0 — inherited baseline

- Introduced the executable assurance model, closed schemas, deterministic
  blockout compiler, Golden Scene contracts, evidence scoring and art lock.
