# Contrat de métriques visuelles

| Champ | Valeur |
| --- | --- |
| ID | `ART-VISUAL-METRICS-001` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 1.0.0 |
| Scope | Mesures automatiques, revue visuelle et preuve humaine |
| Dernière revue | 2026-07-16 |

## Ce qu'une métrique peut prouver

Une métrique automatique peut détecter une dérive dimensionnelle, de silhouette,
de contraste, de framing ou de répétition. Elle ne peut pas prouver seule que
l'objet est beau, attachant, culturellement juste ou compris par des joueurs.

Les gates restent séparés :

1. conformité structurelle ;
2. conformité technique ;
3. conformité visuelle mesurable ;
4. lisibilité en Studio ;
5. lisibilité mobile physique ;
6. jugement humain hash-bound.

## Grammaire quantitative Salvaged Frontier

| Dimension | Contrat |
| --- | --- |
| Châssis standard | 75–85 % |
| Adaptation causale | 15–25 % |
| Hiérarchie de forme | 72 % primaire / 23 % secondaire / 5 % tertiaire |
| Asymétrie globale cible | 0,24 |
| Asymétrie globale max | 0,36 |
| Ratio masse primaire/secondaire | 2,5–4,8 |
| Narrations de réparation | max 2 |
| Familles de patches | max 2 |
| Familles de matériaux visibles | max 3 |
| Accent sémantique | max 12 % de surface visible |
| Warning | max 8 % |
| Critical | max 8 % |

Asymétrie cible par objet : barricade 0,24 ; objective 0,22 ; enemy 0,30 ;
floor 0,16 ; damage effect 0,34 ; turret 0,24.

## Lecture à distance

- 60 studs : barricade, objective core, enemy standard, turret ;
- 30 studs : floor module, damage effect.

À la distance cible, la silhouette doit encore transmettre fonction, facing et
état. Les détails tertiaires sous le seuil écran peuvent disparaître sans
invalider le canon.

## Tests automatisables

- bounds et pivot dans la tolérance déclarée ;
- ratio de masses et enveloppe d'asymétrie ;
- triangle/UV/material budgets ;
- différence de silhouette entre états ;
- stabilité du facing en front/back ;
- contraste de valeur des zones sémantiques ;
- viewport et framing landscape/portrait ;
- reuse 1/30/100 et absence de singleton artificiel ;
- durée et enveloppe écran des VFX ;
- digest identique entre canon, build, export, capture et revue.

Une mesure doit enregistrer algorithme, seuil, entrée, version et artefact brut.
Un score synthétique sans sous-mesures n'est pas une preuve suffisante.

## Tests humains

Pour chaque objet et état :

- identification de fonction en une seconde ;
- identification de facing/source causale ;
- distinction des états sans légende ;
- distinction allié/hostile/neutre ;
- localisation de l'interaction ou réparation ;
- préférence et cohérence DA ;
- détection des éléments interdits.

Les réponses doivent être conservées séparément du score agrégé. Une revue
founder explicite peut sélectionner la direction créative ; elle ne remplace pas
les tests de lisibilité et de performance requis pour la production.

## Quatre profils d'éclairage

Chaque canon est inspecté dans :

1. Gameplay Default ;
2. High Contrast ;
3. Adverse Night ;
4. Neutral QA.

Le profil Neutral QA aide le diagnostic. Aucun asset ne doit être optimisé
uniquement pour le hero light ou pour une capture marketing.

## Seuil de décision

- `PASS` automatique : toutes les mesures applicables passent et les artefacts
  sont liés au canon courant.
- `PARTIAL` : les mesures passent mais la preuve Studio/mobile/humaine reste
  ouverte.
- `FAIL` : dérive d'invariant, état illisible ou budget dépassé.
- `UNKNOWN` : image, viewport, version ou provenance non attribuable.

La qualité artistique finale exige la conjonction des couches, jamais la
moyenne d'un score automatique et d'une preuve absente.
