# Contrat de statut et frontière de vérité

| Champ | Valeur |
| --- | --- |
| ID | `ART-STATUS-001` |
| Classe | `CONTRACT` |
| Cycle de vie | `ACCEPTED` |
| Version | 1.0.0 |
| Source machine | [`../STATUS.json`](../STATUS.json) |
| Dernière revue | 2026-07-16 |

## Résultat actuel

| Couche | Statut courant | Ce que cela prouve |
| --- | --- | --- |
| Spécification | `PASS` | Les contrats requis existent et sont validables. |
| Vérification statique | `PASS` | Les schémas, manifests et tests statiques applicables passent. |
| Workflow précanonique | `PASS` | Les contrats locaux, budgets, hashes et handoffs sont fermés. |
| Exécution Blender | `PASS` | Les builds déterministes requis ont été exécutés. |
| Niveau de preuve Blender | `BUILD_ONLY` | La reconstruction existe ; ce n'est pas une approbation de production. |
| Sélection humaine | `PASS` | Le founder a sélectionné Salvaged Frontier. |
| Constitution créative | `CREATIVE_DIRECTION_LOCKED` | L'identité et ses règles ne sont plus un espace d'exploration libre. |
| Canons visuels sélectionnés | `SELECTED_PARTIAL` | Six contrats `CANDIDATE` existent ; leurs paquets et signatures restent ouverts. |
| Studio sélectionné | `UNKNOWN` | La constitution actuelle n'a pas de preuve Studio complète et fraîche. |
| Simulateur Studio | `PARTIAL` | La composition est observée, pas les performances physiques. |
| Mobile physique | `BLOCKED` | Aucun appareil baseline nommé n'a exécuté le protocole complet. |
| Transfert tourelle | `PARTIAL` | Automatisation `PASS`, approbation humaine courante `PENDING`. |
| Cloud/Studio transfert sélectionné | `UNKNOWN` | Les preuves v3.7 sont historiques et antérieures au verrou courant. |
| Production | `false` | Aucun usage de production ne peut être déclaré approuvé. |

## Trois verrous distincts

### 1. Verrou créatif

Le founder a figé la direction :

> Salvaged Frontier porte l'identité du monde ; Industrial Toy Defense impose
> uniquement la discipline de lisibilité.

Ce verrou interdit le retour silencieux à un hybride 50/50 ou à une nouvelle
palette, mais n'approuve aucun mesh.

### 2. Verrou canonique d'objet

Un objet devient `LOCKED` seulement si sa définition JSON, ses 17 planches
requises, son rapport de conformité, sa provenance et son approbation humaine
sont liés au même digest. Les six objets sont actuellement `CANDIDATE` avec
approbation `PENDING`.

### 3. Verrou de production

`productionApproved=true` exige en plus les preuves Studio fraîches, le
protocole mobile physique, la preuve de transfert sélectionnée et les gates
humains applicables. Aucun verrou inférieur ne se substitue à ce gate.

## Priorité des sources

1. `STATUS.json` : statut courant consolidé.
2. JSON sous `art/` : valeurs, contrats et états machine.
3. Rapports sous `evidence/` : observations horodatées.
4. Markdown : explication et navigation.

Un snapshot historique reste valide pour ce qu'il a réellement observé, mais
ne peut pas approuver une constitution créée après lui.

## Règles de verdict

- `PASS` : tous les critères applicables ont une preuve courante.
- `FAIL` : au moins un critère requis a échoué.
- `PARTIAL` : une partie utile est prouvée, l'acceptation reste incomplète.
- `BLOCKED` : une dépendance externe empêche le test.
- `UNKNOWN` : le résultat n'a pas été observé ou ne peut pas être attribué à
  la version sélectionnée.
- `PENDING` : décision humaine ou action prévue, sans verdict de preuve.

Une vérification sautée, un exit code isolé, une capture seule ou un document
déclaratif ne valent jamais `PASS`.
