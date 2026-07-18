# Étude aveugle de sélection de la direction artistique

## Statut

Le workflow prépare une étude locale réellement aveugle, mais ne fabrique ni
participants, ni experts, ni approbation humaine.

```json
{
  "studyPreparation": "PASS",
  "humanCollection": "PENDING",
  "automaticSelection": false,
  "productionApproved": false
}
```

## Objectif

Comparer les trois candidats sous des conditions identiques sans révéler leurs
noms, puis produire un jeu de soumissions scellé et compatible avec le scoreur
officiel. Le scoreur classe les candidats éligibles mais ne sélectionne jamais
la direction à la place du fondateur.

## Population

- minimum contractuel : 8 participants et 2 experts ;
- cible préparée : 12 participants et 4 experts ;
- participants pseudonymisés `P01` à `P12` ;
- experts pseudonymisés `R01` à `R04` ;
- deux focalisations expertes alternées :
  `function_silhouette` et `art_direction_coherence`.

Le minimum est une porte directionnelle, pas une estimation représentative de
la population Roblox.

## Épreuves participantes

Chaque participant effectue 30 essais :

```text
3 candidats anonymes
x
10 tâches
=
30 essais
```

Les tâches couvrent :

- reconnaissance des silhouettes à 60 studs ;
- reconnaissance de la fonction à 30 studs ;
- reconnaissance des états intact, endommagé et critique ;
- lecture de la direction d’un impact.

Chaque stimulus est montré pendant cinq secondes, puis masqué. L’ordre des
tâches, des candidats et des réponses est équilibré et déterministe par
identifiant participant. Aucun retour arrière n’est autorisé.

## Revue experte

Chaque expert note les trois candidats sur les neuf dimensions de
`art/qa/visual-rubric.json`. Le paquet montre :

- les Golden Scenes Studio sous quatre éclairages ;
- les silhouettes et états des cinq objets de calibration ;
- la tourelle indépendante dans ses états, vues mobile et silhouettes
  avant/arrière.

Les experts ne voient que les labels `A`, `B` et `C`.

## Confidentialité expérimentale

Le générateur :

- crée une bijection aléatoire privée entre labels et territoires ;
- réencode toutes les images pour retirer leurs métadonnées ;
- remplace tous les noms de fichiers par des identifiants anonymes ;
- analyse le dossier public et les ZIP contre les trois identifiants interdits ;
- conserve la carte privée hors des paquets distribuables ;
- lie tous les stimuli et interfaces par SHA-256.

Ne jamais partager les dossiers `private/` et `operator/`.

## Préparation

Les rendus Blender complets doivent exister :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 `
  build -RenderMode full -Resume
```

Puis :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 `
  prepare-study -Open
```

Le dossier local produit est :

```text
evidence/human/art-direction-study-v1/
├── participant-kit.zip
├── expert-kit.zip
├── public/
├── operator/
├── private/
├── sessions/
└── study-manifest.json
```

## Collecte et scellement

Déposer les exports JSON dans :

```text
sessions/participants/
sessions/experts/
```

Puis :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 `
  seal-study -StudyRoot .\tools\roblox-art-bible-sota-v3\evidence\human\art-direction-study-v1
```

Le scellement refuse :

- les matrices incomplètes ou dupliquées ;
- les IDs en double ;
- les sessions liées à un autre paquet ;
- moins de huit participants ou de deux experts ;
- les réponses hors schéma ;
- une altération du paquet public.

Avant de sceller, il réévalue uniquement les gates techniques depuis les
preuves courantes. Ce rafraîchissement ne change ni les stimuli, ni les labels,
ni la carte privée, ni les sessions brutes. Les preuves CVD, provenance et
mobile obtenues après la préparation peuvent donc être intégrées sans
recommencer l’étude.

Il génère `operator/reviewer-submissions.sealed.json` et inscrit son SHA-256
exact dans `private/blind-map.json`.

## Score

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\art-direction.ps1 score `
  -Submissions <reviewer-submissions.sealed.json> `
  -BlindMap <blind-map.json> `
  -Output <scoring-report.json>
```

Un candidat reste inéligible si un seul hard gate échoue, même s’il obtient le
meilleur score visuel.

## Gates encore externes

Le paquet actuel doit signaler honnêtement les gates encore absents :

- captures exécutées en niveaux de gris et simulations CVD ;
- approbation humaine de la provenance des références ;
- test de performance sur appareil mobile physique bas de gamme.

La collecte perceptuelle peut commencer avant leur fermeture, mais la décision
finale et l’Art Lock doivent attendre qu’ils passent.
