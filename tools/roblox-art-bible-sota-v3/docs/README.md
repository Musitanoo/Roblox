# Documentation — Art Direction et assets 3D

| Champ | Valeur |
| --- | --- |
| ID | `ART-DOC-PORTAL-001` |
| Classe | `REFERENCE` |
| Cycle de vie | `ACTIVE` |
| Scope | Paquet `roblox-art-bible-sota-v3` |
| Dernière revue | 2026-07-16 |

Ce dossier est la porte d'entrée humaine du système artistique. Les valeurs
exécutables restent définies par les JSON sous `../art/`, et le statut courant
par [`../STATUS.json`](../STATUS.json). Une phrase Markdown ne peut pas
transformer une preuve absente en `PASS`.

## Lire en premier

1. [Statut et frontière de vérité](STATUS_CONTRACT.md)
2. [Bible Salvaged Frontier](SALVAGED_FRONTIER_ART_BIBLE.md)
3. [Ontologie des états](STATE_ONTOLOGY.md)
4. [Registre des six objets](OBJECT_REGISTRY.md)
5. [Définitions visuelles canoniques](CANONICAL_VISUAL_DEFINITIONS.md)
6. [Contrat technique Roblox](ROBLOX_TECHNICAL_ART_CONTRACT.md)
7. [Métriques visuelles et critères d'acceptation](VISUAL_METRICS_CONTRACT.md)
8. [Blender Visual Workbench MCP](BLENDER_MCP_WORKBENCH.md)

## Six objets sélectionnés

| Objet | Fonction | États d'intégrité applicables | Fiche |
| --- | --- | --- | --- |
| `barricade` | Blocage défensif temporaire | `INTACT`, `DAMAGED`, `CRITICAL` | [Barricade](objects/BARRICADE.md) |
| `objective_core` | Objectif principal à défendre | `INTACT`, `DAMAGED`, `CRITICAL` | [Objective Core](objects/OBJECTIVE_CORE.md) |
| `enemy_standard` | Rôdeur zombie violet standard | `INTACT`, `DAMAGED`, `CRITICAL` | [Violet Frontier Rôdeur](objects/ENEMY_STANDARD.md) |
| `floor_module` | Cellule répétable de forteresse | `INTACT`, `DAMAGED` | [Floor Module](objects/FLOOR_MODULE.md) |
| `damage_effect` | Explication directionnelle d'un impact | `DAMAGED`, `CRITICAL` | [Damage Effect](objects/DAMAGE_EFFECT.md) |
| `turret_fast_v1` | Tourelle rapide, preuve de transfert | `INTACT`, `DAMAGED`, `CRITICAL` | [Fast Defense Turret](objects/TURRET_FAST_V1.md) |

La matrice contient 16 variantes pour Salvaged Frontier : 13 issues du kit de
calibration et 3 issues du test de transfert. Les six objets sont des probes
canoniques de la DA, pas l'inventaire complet de tous les futurs contenus du
jeu.

## Contrats de production

- [Axes et unités](AXIS_AND_UNITS.md)
- [Compilation Blender](BLENDER_CONTRACT.md)
- [Inspection et expérimentation Blender transactionnelles](BLENDER_MCP_WORKBENCH.md)
- [Contrat technique Roblox](ROBLOX_TECHNICAL_ART_CONTRACT.md)
- [Golden Scene Studio](STUDIO_GOLDEN_SCENE.md)
- [Preuves mobile](MOBILE_EVIDENCE.md)
- [Preuve de transfert](TRANSFER_PROOF.md)
- [Modèle d'assurance](ASSURANCE_MODEL.md)
- [Gouvernance et risques](GOVERNANCE_AND_RISK.md)

## Recherche et décision

- [Politique de références](REFERENCE_POLICY.md)
- [Sources primaires](RESEARCH_SOURCES.md)
- [Protocole d'étude aveugle](BLIND_STUDY_PROTOCOL.md)
- [Verrou créatif](ART_LOCK.md)

## Preuves enregistrées

Les documents de preuve sont des snapshots. Ils n'ont pas autorité sur le
statut courant :

- [Rapport de vérification v3](V3_VERIFICATION_REPORT.md)
- [Audit de qualité visuelle](VISUAL_QUALITY_AUDIT.md)
- [Ledger de remédiation](AUDIT_REMEDIATION.md)

Toute nouvelle preuve doit identifier sa version de constitution, ses hashes,
son environnement, ses limites et le gate exact qu'elle prétend satisfaire.
