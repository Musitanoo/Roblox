# ExecPlan - v3 Production SOTA

## Objectif

Transformer la v2 auditee en un workflow autonome qui genere de facon
deterministe des familles 3D Roblox stylisees, lisibles, techniquement valides,
reproductibles et simples a exploiter. La production n'est approuvee que par
des preuves de chaque couche, sans extrapolation.

## Criteres observables

### Visuel

- trois territoires differencies par topologie, construction et materiaux;
- masses primaires, construction secondaire, fonction et signature lisibles;
- etats intact/damaged/critical causalement distincts sans dependre de la hue;
- matrice complete: distance, quatre lumieres, fonds, resolutions et diagnostics;
- repetition 30/100 sans explosion des MeshIds uniques;
- aucune geometrie flottante, artefact IA brut, texte ou logo non demande;
- etude aveugle: fonction et etat reconnus par au moins 7/8 participants;
- deux experts au-dessus de chaque floor et score reconcilie d'au moins 90/100.

### Roblox

- place exclusivement staging et identite confirmee sans journaliser de secret;
- import/readback des meshes, dimensions, pivots, materiaux, collisions,
  RenderFidelity, CastShadow, tags et attributs;
- Golden Scenes et repetitions 1/30/100;
- reimport v1 vers v2 preserve les proprietes Roblox;
- mobile physique low-tier valide frame time, memoire, thermique et interaction.

### Ergonomie

- commande unique et workbench pour construire, reprendre, revoir et reporter;
- doctor actionnable et redige;
- dry-run, resume, scopes, seed et JSON machine-readable;
- echec preserve les preuves et designe la premiere cause actionnable;
- extraction propre autonome;
- publication impossible hors staging ou sans gates applicables.

## Jalons

### M1 - Cibles et audit: COMPLETE

- baseline smoke conservee et explicitement rejetee;
- trois cibles originales et audit comparatif produits;
- criteres de qualite et statut non autoritaire documentes.

### M2 - Architecture du generateur: COMPLETE

- grammaires shape/material/damage/composition separees;
- modules reutilisables de construction;
- identites de territoire topologiques, pas seulement chromatiques.

### M3 - Materiaux et presentation: COMPLETE

- hierarchie deterministic de materiaux Roblox-compatible;
- cadrage, contact, eclairage et vues mobile calibres;
- turntables, diagnostics et contact sheets.

### M4 - Etats et variation: COMPLETE

- transformations causales par asset;
- variation bornee et reutilisation des meshes;
- validations silhouette, pixels occupes, palette, etat et repetition.

### M5 - Workflow developpeur: COMPLETE

- workbench, doctor, production-build, resume, review et reports;
- skill progressif `roblox-3d-asset` valide;
- moteur vertical-slice r3d integre;
- installateur transactionnel et package deterministe.

### M6 - Preuve Blender complete: COMPLETE

- 39 variantes et 1 263 rendus PASS;
- six stress renders PASS;
- determinisme A/B des 39 GLB PASS;
- erreurs, dependances et Luau couverts par tests.

### M7 - Preuve Studio staging: COMPLETE

- cible staging confirmee;
- trois kits integres et trois Golden Scenes PASS;
- 12 captures fraiches hash-bound, avec cameras verifiees dans l'espace isole;
- readback et reimport v1 vers v2 PASS;
- scenes isolees 30/100 et builder benchmark installes;
- quatre captures A/B graybox/candidat 30/100 et aucun proxy invisible dans
  les clones du benchmark de rendu.

### M8 - Transfert sixieme asset et Studio staging: COMPLETE

- `turret_fast_v1` compile dans trois territoires et trois etats;
- neuf GLB deterministes, 108 rendus et score automatique 100/100;
- neuf identites staging publiees, relues et reprises sans doublon;
- integration Studio 9/9, bounds a moins de 0,030 %, 59 liaisons de roles
  materiaux, six groupes 30/100 et playtest Client/Server PASS;
- trois captures transfer-specific liees par chemin, octets et SHA-256.

### M9 - Definitions canoniques visuelles: PARTIAL / BLOCKED

- 18 canons `objet x territoire` et 48 definitions d'etat: COMPLETE;
- identite, lecture une seconde, vues, proportions, composants, materiaux,
  zones semantiques, transitions, invariants, variations et interdictions:
  COMPLETE comme contrats `CANDIDATE`;
- enveloppes pre-generation et rapports post-build lies aux hashes: COMPLETE;
- liaison r3d par asset au canon exact: COMPLETE;
- planches multimodales completes et liees: PENDING;
- selection du territoire et lock humain des six canons retenus: BLOCKED;
- toute production `-RequireLockedCanons` echoue avant Blender tant que ces
  preuves externes manquent.

### M10 - Mobile et humain: PARTIAL / BLOCKED

- simulateur exact, benchmark structurel et captures Studio: PARTIAL documente
  uniquement a cause des APIs diagnostiques encore bloquees;
- appareil physique low-tier: BLOCKED, materiel externe absent;
- kit d'etude aveugle: COMPLETE, avec 12 slots participants, 4 slots experts,
  30 essais chronometres, interfaces anonymes, carte privee et scellement;
- collecte, reconciliation expert et signature: PENDING, humains absents;
- aucun resultat synthetique n'est substitue a ces preuves.

### M11 - Selection et lock: BLOCKED

- exige le territoire selectionne et signe par M10;
- exige les six canons du territoire `LOCKED + COMPLETE + APPROVED`;
- exige l'approbation humaine du sixieme asset deja produit contre le digest
  courant;
- produira ensuite l'art lock, le package de production et la preuve de
  rollback.

### M12 - Reconstruction barricade revision 6: PARTIAL

- contrat lie au canon Salvaged Frontier courant: COMPLETE;
- maximum local refuse s'il depasse les 2 000 triangles canoniques: COMPLETE;
- famille topology-preserving `intact/damaged/critical`: COMPLETE;
- 29 composants, 1 468 triangles et dimensions 8 x 4 x 2 invariants: COMPLETE;
- deux compilations A/B, GLB, FBX aux chemins canoniques, geometrie, hashes
  semantiques et 24 rendus: PASS;
- comparaison de la famille publiee aux references A/B: PASS;
- inspection Workbench finale en lecture seule: PASS;
- revue artistique interne: 92/100, `PASS_INTERNAL_HUMAN_PENDING`;
- panneau de remplacement, reparation cuivre, lecture mobile de `damaged` et
  motif signature fonctionnel: COMPLETE;
- comparaison RGBA8 exacte ou micro-tolerance bornee et reportee: PASS;
- lock humain, publication staging de cette revision, Studio et mobile:
  BLOCKED.

## Recuperation et securite

- v2 reste immuable; v3 reste isolee jusqu'a installation acceptee;
- ecritures Roblox limitees au staging;
- aucune valeur de secret ou identifiant brut dans les rapports;
- build genere reproductible et jetable;
- installation via stage, verification de hash, tests, puis activation;
- remplacement explicite seulement, avec backup horodate.

## Etat courant

M1 a M8 decrivent les preuves historiques du package. La partie autonome de M9
et M10 est complete. M12 prouve que le pipeline courant reconstruit une vraie
famille d'etats revision 6 sous la cible triangles et au-dessus du floor visuel
interne. Les planches canoniques verrouillees, les preuves Studio de la
revision courante, la preuve mobile physique et l'approbation humaine bloquent
legitimement M11. Le workflow reste utilisable en preproduction;
`productionApproved` reste `false`.
