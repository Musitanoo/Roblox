# Gouvernance, responsabilités et risques artistiques

| Champ | Valeur |
| --- | --- |
| ID | `ART-GOV-RISK-001` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 1.0.0 |
| Dernière revue | 2026-07-16 |

## Responsabilités

| Décision | Responsable | Approbateur | Consultés | Preuve |
| --- | --- | --- | --- | --- |
| Constitution créative | Direction artistique/Codex | Founder | Design, gameplay | Constitution + décision founder |
| Canon d'objet | Art owner | Founder/art reviewer | Gameplay, tech art | JSON + 17 planches + digest |
| Budget technique | Tech art | Engineering owner | Mobile/performance | Rapport Blender/Studio/device |
| Publication staging | Pipeline owner | Founder explicite | Security | Plan dry-run + registry locale |
| Intégration Studio | Studio operator | Art/engineering reviewer | Gameplay | Transaction + consoles + captures |
| Approbation production | Founder + owners applicables | Founder | Art, engineering, QA | Tous gates courants |

Codex peut compiler, contrôler et recommander. Il ne signe pas une décision
humaine, ne sélectionne pas un asset par simple score et ne transforme pas une
capacité externe inconnue en preuve.

## Risques prioritaires

| Risque | Impact | Contrôle | Statut courant |
| --- | --- | --- | --- |
| Markdown contredit la machine | Mauvaise décision de production | `STATUS.json` prioritaire + snapshots marqués | Réduit par ce corpus |
| Six objets pris pour tout le jeu | Sous-spécification future | Registre les nomme probes, extension versionnée | Contrôlé |
| États mélangés | Variantes inutiles, bugs de lecture | Ontologie orthogonale | Contrat fermé, runtime non prouvé |
| Hybride DA 50/50 | Identité diluée | Précédence Salvaged > discipline Industrial | Interdit |
| Damage color-only | Inaccessibilité, mauvaise lecture | Deux canaux minimum | Contrat fermé, test ouvert |
| Détails trop fins | Mobile illisible | distances 30/60 + hiérarchie 72/23/5 | Validation par asset requise |
| Mesh/texture trop coûteux | Régression mobile | budgets internes + 1/30/100 | Device physique bloqué |
| Collision suit le visuel | Gameplay injuste | proxies simples et invariants | Studio courant inconnu |
| Preuve historique réutilisée | Faux `PASS` | constitution hashée + archive | v3.7 historique |
| Publication non autorisée | Mutation externe | dry-run, allowlist, confirmation | Aucune publication dans ce travail |

## Waivers

Une dérogation n'est valide que si elle contient :

- ID, owner et date ;
- règle dérogée ;
- asset/état/version exacts ;
- raison gameplay ou technique ;
- métrique avant/après ;
- impact mobile, collision, mémoire et lisibilité ;
- expiration ou déclencheur de revue ;
- rollback ;
- approbateur humain.

Une waiver ne peut pas autoriser secret, publication de production, donnée
inventée, état non applicable ou suppression d'une preuve négative.

## Dépréciation

Lorsqu'un canon, une palette ou une preuve est remplacé :

1. conserver l'ancien artefact en lecture seule ;
2. le marquer `SUPERSEDED` ou `ARCHIVED` ;
3. nommer le successeur ;
4. enregistrer le motif et l'impact ;
5. invalider explicitement les hashes et preuves dépendantes ;
6. ne jamais réécrire l'historique comme si la nouvelle version avait été
   testée à l'époque.

Les preuves Cloud/Studio v3.7 sont conservées comme baseline d'ingénierie
pré-sélection. Elles ne soutiennent pas la constitution Salvaged Frontier
optimisée.

## Menaces au pipeline

- asset ou état forgé hors catalogue ;
- NaN, infini, dimensions énormes ou path traversal dans les contrats ;
- hash manquant, mal formé ou réutilisé après mutation ;
- zip/GLB contenant un fichier inattendu ;
- publication répétée ou vers un creator non allowlisté ;
- faux rapport `pass: true` incohérent avec les sous-mesures ;
- capture liée au mauvais viewport, territoire ou asset ;
- payload externe contenant secret, cookie ou identifiant brut.

Les validateurs doivent échouer fermés, contrôler les entrées avant le travail
coûteux et ne jamais loguer de credential.

## Review triggers

Revue obligatoire si :

- la constitution, palette, matériaux ou grammaire change ;
- un objet change de fonction, dimensions, pivot, états ou collision ;
- Roblox modifie import, texture, asset API ou limites pertinentes ;
- une preuve Studio/mobile courante devient disponible ;
- un nouveau type d'objet n'entre pas dans la grammaire sans exception ;
- un incident révèle une ambiguïté d'autorité ou de statut.
