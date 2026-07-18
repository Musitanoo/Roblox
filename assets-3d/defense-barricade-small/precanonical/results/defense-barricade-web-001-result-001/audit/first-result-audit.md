# Audit visuel exhaustif — premier résultat de la barricade

Verdict : `REVISION_REQUIRED`

Cet audit porte sur le résultat historique `defense-barricade-web-001-result-001`. Il distingue strictement deux usages :

- comme exploration, l’image propose quatre candidats et possède une base visuelle exploitable ;
- comme définition canonique d’un objet et de ses états, elle est insuffisante et ne doit pas être promue.

L’image, le résultat, la requête et la revue d’origine restent immuables. Le registre machine [first-result-audit.json](first-result-audit.json) lie chaque preuve par SHA-256 et constitue la liste normative des constats.

## Ce qu’il faut préserver

- silhouette large, basse, stable et immédiatement défensive ;
- deux pieds extérieurs lisibles et trois grands panneaux dans un cadre continu ;
- palette ardoise sombre, os-sable, cuivre et menthe bien séparée en valeur ;
- biseaux épais, plans primaires calmes et présentation neutre propre ;
- lecture rapide de prop allié sans texte généré.

## Diagnostic fondamental

Le résultat répond au contrat historique d’`exploration` : il montre quatre solutions. Il ne faut donc pas lui reprocher rétroactivement de ne pas être un turnaround. En revanche, ses variations sont trop superficielles pour quatre silhouettes réellement distinctes, et la revue l’a promu alors que trois dimensions restaient `UNKNOWN`.

La correction structurelle est de ne plus utiliser ce sheet comme parent canonique. La campagne v2 demande désormais une image distincte par objet et par état, avec quatre vues du même objet verrouillé, puis relie chaque état au précédent par hash.

## Registre complet des problèmes

| ID | Problème observé | Impact | Correction |
|---|---|---:|---|
| F-001 | Quatre objets alternatifs au lieu de quatre vues d’un objet gelé | Bloquant en aval | Contrat v2 « un objet, un état » et verrou inter-vues |
| F-002 | Diversité d’exploration trop faible ; variations surtout limitées à la barre cuivre | Élevé | Deux décisions de masse primaire ou d’espace négatif minimum par candidat |
| F-003 | Aucun candidat ni quadrant sélectionné comme identité persistante | Bloquant | Nouveau départ depuis le canon fermé et règle de préservation obligatoire |
| F-004 | Aucune vue arrière mécaniquement exploitable | Bloquant | Trois-quarts arrière obligatoire du même objet |
| F-005 | Aucune silhouette noire | Élevé | Silhouette noire correspondant exactement au contour du hero view |
| F-006 | Aucune vue caméra mobile Roblox | Élevé | Vue de gameplay surélevée obligatoire |
| F-007 | États intact, endommagé et critique non définis séparément | Bloquant | Une génération GPT Image 2 par objet et par état |
| F-008 | Aucune continuité prouvée entre les états | Bloquant | Endommagé lié à intact accepté, critique lié à endommagé accepté |
| F-009 | Face menace et face joueur ambiguës | Élevé | Avant blindé continu ; arrière de service calme |
| F-010 | Signal menthe visible sur la face présentée côté menace | Élevé | Menthe locale uniquement dans le socket arrière protégé |
| F-011 | Renfort cuivre décoratif plutôt que porteur | Élevé | Deux terminaisons sur de vrais joints structurels et faible portée causale explicite |
| F-012 | Identité Salvaged Frontier trop générique | Élevé | Une réparation causale et une histoire de remplacement bornée |
| F-013 | Industrial Toy Defense domine l’identité | Élevé | Toy Defense limité à la discipline de lecture ; Frontier porte le monde |
| F-014 | Panneaux os-sable lisibles comme pierre, béton, parchemin ou céramique | Élevé | Composite manufacturé, bords formés, couches et fixations fonctionnelles |
| F-015 | Cuivre trop propre et ornemental | Moyen | Usure fonctionnelle localisée aux contacts et fixations |
| F-016 | Rayures et détresse trop uniformes | Moyen | Usure directionnelle bornée aux pieds, angles, attaches et zones de contact |
| F-017 | Asymétrie surtout décorative | Moyen | Asymétrie causale concentrée dans une réparation ou un remplacement |
| F-018 | Pseudo-logo triangulaire sur le candidat inférieur gauche | Élevé | Interdiction des emblèmes ; tertiaire seulement sur les vrais joints |
| F-019 | Topologie et attaches changent entre les quadrants | Bloquant en aval | Verrou de nombre, position, joint, matériau, usure et état |
| F-020 | Montage et destructibilité des panneaux peu expliqués | Moyen | Attaches stables et un chemin de rupture déclaré |
| F-021 | Dimensions 8 × 4 × 2 et pivot non prouvés | Inconnu | Validation numérique Blender ; aucune inférence depuis l’image |
| F-022 | Lecture à 60 studs non prouvée | Élevé | Preuve mobile-distance et test Roblox ultérieur |
| F-023 | Répétition à 30 exemplaires et performances non prouvées | Moyen | Tests 1, 30 et stress après reconstruction 3D |
| F-024 | Arrière, dessous, collision, topologie et UV non observables | Bloquant | Maintenir `UNKNOWN` jusqu’aux validateurs Blender et Roblox |
| F-025 | Modèle GPT Image 2 non confirmé | Élevé | Attestation explicite visible avant import |
| F-026 | Candidat accepté avec trois dimensions `UNKNOWN` | Bloquant | Cinq dimensions `PASS` obligatoires pour accepter |
| F-027 | Aucune règle « à préserver » dans la revue acceptée | Élevé | Au moins une règle de préservation obligatoire |
| F-028 | Aucune correction malgré les inconnues | Élevé | Correction obligatoire pour `REVISION_REQUIRED` et `REJECTED` |
| F-029 | Aucune interdiction exigée pour un rejet | Moyen | Au moins une interdiction obligatoire pour `REJECTED` |
| F-030 | Aucun reviewer ni horodatage | Moyen | Candidat non autoritaire ; identité et date obligatoires pour `HUMAN_SELECTED` |
| F-031 | Conformité DA marquée `PASS` malgré les écarts visibles | Élevé | Libellé de contrôle précis et acceptation seulement après cinq `PASS` |
| F-032 | Le sheet complet a été promu sans région choisie | Bloquant | Conserver comme exploration historique ; ne pas le promouvoir |

## Corrections déjà intégrées au workflow

- verrou inter-vues explicitant que le 2×2 n’est jamais un sheet de quatre concepts ;
- une génération distincte pour chacun des seize couples objet × état ;
- héritage hashé des états et corrections ciblées ;
- vues hero avant, arrière, silhouette noire et caméra mobile ;
- interdictions du signal menthe en façade, du composite minéral, des pseudo-logos et des renforts décoratifs ;
- suppression de la contradiction canonique qui autorisait un symbole d’assemblage ;
- gate d’acceptation : cinq `PASS` et au moins une règle à préserver ;
- gate de révision : correction obligatoire ; gate de rejet : correction et interdiction obligatoires ;
- UI opérateur bloquant le bouton tant que la revue n’est pas recevable ;
- campagne v2 séparée pour ne pas modifier silencieusement la campagne v1.

## Ce qui exige encore une nouvelle génération

Le code peut empêcher les erreurs de contrat, mais il ne peut pas transformer rétroactivement les pixels. Les constats F-009 à F-017 et F-020 doivent être jugés sur la prochaine image. Celle-ci ne passe que si les dix critères `acceptanceForNextGeneration` du registre JSON sont tous observables.

Les dimensions, la géométrie cachée, les UV, les collisions, la répétition et les performances restent volontairement `UNKNOWN` avant reconstruction 3D et tests Roblox. Les déclarer `PASS` à ce stade serait une fausse preuve.
