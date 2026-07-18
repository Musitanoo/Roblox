# Modèle d'assurance — aucun faux `PASS`

## Couches indépendantes

| Couche | Signification de `PASS` | État actuel |
|---|---|---|
| Spécification | Contrats fermés, cohérents et validés | `PASS` |
| Constitution créative | Identité, discipline, précédence, scopes et interdictions figés | `PASS` |
| Précanonique Web local | Brief, prompt, contraintes, budget, provenance, doctor local, handoff et revue fermés par contrat | `PASS` |
| Capacité Browser de la tâche | `mcp__node_repl__js` et le backend requis sont effectivement exposés dans la tâche courante | `UNKNOWN` tant que non observé |
| Pont opérateur semi-automatique | Preflight courant, texte soumis hashé, attestation humaine, octets importés et revue liés sans API ni contrôle navigateur | `PASS` après import et revue |
| Exécution ChatGPT Web | Soumission réelle autorisée, image téléchargée et importée | `NOT_REQUESTED` |
| Sélection | Décision explicite du fondateur et alternatives rejetées documentées | `PASS` |
| Étude aveugle | Dataset réel complet, scellé et analysé | `INCOMPLETE`, non utilisé comme preuve |
| Canons candidats | 18 contrats objet x territoire, 48 états, déterminisme | `PASS` |
| Canons sélectionnés production | Six canons Salvaged Frontier, 17 familles de planches et approbations liées par hash | `BLOCKED` |
| Validation statique | Schémas, sémantique, drift et code généré | `PASS` |
| Blender sélectionné | Construction, exports, budgets, composants et matrice complète | `PASS` |
| Studio sélectionné | Import, matériaux, collisions, Golden Scene, 30/100, captures et playtest courants | `UNKNOWN` |
| Mobile physique | Appareil nommé, frame time, mémoire, thermique et interaction | `BLOCKED` |
| Transfert sixième asset | Preuve automatisée courante plus approbation humaine sélectionnée | `PARTIAL` tant que non signé |
| Publication staging sélectionnée | Identité distante et source courante relues | `UNKNOWN` |
| Intégration Studio sélectionnée | Readback courant, bounds, matériaux, hitboxes, groupes et playtest | `UNKNOWN` |
| Production | Tous les gates applicables sont actuels et approuvés | `false` |

Un `PASS` ne remonte jamais automatiquement :

- le fondateur peut verrouiller la direction sans approuver un asset ;
- un preflight `PASS` ne prouve pas la capacité Browser de la tâche ;
- un handoff en attente ne prouve ni soumission ni consommation de quota ;
- une attestation opérateur prouve les actions déclarées et la provenance
  locale, pas le fonctionnement interne de ChatGPT Web ;
- une image Web sélectionnée autorise la canonicalisation, jamais la
  production ;
- Blender ne prouve pas Roblox Studio ;
- Studio ne prouve pas un appareil physique ;
- une étude incomplète ne devient pas une preuve de sélection ;
- une ancienne preuve correcte ne valide pas une constitution dont les hashes
  ont changé ;
- une note automatique ne signe pas une décision artistique.

## Deux verrous différents

### Verrou créatif

Le verrou créatif répond à :

- quel monde voulons-nous ?
- que signifie chaque matériau ?
- comment la forteresse mémorise-t-elle le joueur ?
- quelle grammaire rend le tout lisible ?
- quelles dérives sont interdites ?

Il est matérialisé par :

- `art/decision/founder-direction-decision.json` ;
- `art/selected/salvaged-frontier-constitution.json` ;
- `docs/SALVAGED_FRONTIER_ART_BIBLE.md`.

### Verrou de production

Le verrou de production répond à :

- les six objets sont-ils complètement définis et approuvés ?
- les résultats reconstruisent-ils le canon exact ?
- Studio et mobile confirment-ils la lecture et les performances ?
- le sixième asset prouve-t-il la transférabilité ?

Ce verrou reste fermé tant que toutes ses preuves ne sont pas présentes.

## Politique de preuve

Les preuves courantes sont :

- confinées à des chemins déclarés ;
- liées par SHA-256 aux sources et outils concernés ;
- versionnées ;
- invalidées par une dérive d'entrée ;
- séparées de l'historique ;
- attribuées à l'autorité qui peut réellement les produire.

Les preuves v3.7 de comparaison, publication et Studio sont conservées comme
historique d'ingénierie. Elles ne sont pas présentées comme preuve actuelle de
la constitution Salvaged Frontier optimisée.

## Politique de sortie

- `0` : opération réussie ou gate applicable `PASS` ;
- `1` : contrat ou gate `FAIL` ;
- `2` : `BLOCKED` par une preuve externe incomplète ;
- `19` : exception du contrat Blender Python ;
- `64` : usage invalide.

## Règle de génération

La génération ne décide pas ce qu'est l'objet.

1. Le brief fonctionnel et la constitution ferment le problème à explorer.
2. La couche précanonique peut rendre l'intention visible sous budget.
3. L'humain choisit une proposition comme matière première.
4. Le canon candidat rationalise toutes les faces, structures et inconnues.
5. L'enveloppe d'autorité lie le canon et les sources avant génération.
6. Blender reconstruit.
7. Le rapport de conformité prouve géométrie, budgets et composants.
8. Les planches multimodales prouvent la lecture.
9. L'humain autorisé verrouille.

Une belle image ne peut compenser :

- un composant absent ;
- une fonction ambiguë ;
- un état illisible ;
- un hash dérivé ;
- une preuve Studio manquante ;
- une approbation humaine inexistante.
