# Preuve locale — Blender Visual Workbench 2026-07-17

| Champ | Valeur |
| --- | --- |
| ID | `EVIDENCE-BLENDER-WORKBENCH-001` |
| Classe | `EVIDENCE` |
| Cycle | `RECORDED` |
| Asset | `defense_barricade_small` |
| Session | `workbench-vertical-004` |
| Verdict local | `PASS` |
| Source autoritative modifiée | `false` |
| Studio / mobile | `UNKNOWN` |
| `productionApproved` | `false` |

## Scénario observé

1. liaison du contrat révision 3, du canon CANDIDATE, du compilateur et du
   `source.blend` exacts ;
2. copie `Reference` en lecture seule et copie `Candidate` ;
3. huit captures de baseline ;
4. change set `barricade-feet-balance-001` : largeur `designX` de chaque pied
   `1.6 → 1.8` ;
5. preview sans sauvegarde ;
6. application sur `Candidate` ;
7. comparaison : deux composants changés, zéro triangle ajouté ;
8. rollback au hash sémantique baseline exact ;
9. réapplication ;
10. patch vers une source `PromotionSandbox` ;
11. deux recompilations `--factory-startup` ;
12. comparaison du build reconstruit au candidat.

## Résultats

| Mesure | Résultat |
| --- | --- |
| Hash binaire `Reference/source.blend` | `2a26af173b8127739ebd0b7adebedec5b68b898042294d9f54b73d92f4be9054` |
| Hash sémantique baseline | `91d6d8e6bde8162efb792dd6f56eeb6dae5eab5193f0fcaa21ba0f5fa9047633` |
| Hash candidat | `670b6e56fad371bc95862acb30f16df938ba99c44265c30e2ba026e2d076790a` |
| Hash après rollback | identique à la baseline |
| Composants modifiés | 2 |
| Delta triangles | 0 |
| Invariants déclarés | tous `PASS` |
| Hash build source A | `7a13df22ee1e9a8f8f1109fa22ee363a855ff3a5fd68c9fc4b810d900cb45acb` |
| Hash build source B | identique au build A |
| GLB A/B | `c7afad5222f3956d73611e45feb4a89e46712aea1c11c8a874f78ca533123055` / identique |
| FBX A/B | `2612c02821acd398d91f5143c856d782ac0f1cf1b023b70928c53af89851f21a` / identique |
| Valeurs reconstruites | pied gauche 1.8 ; pied droit 1.8 |
| Référence binaire immuable | `PASS` |
| Publication / Studio | non exécutés |

Les preuves détaillées restent dans le dossier local ignoré :
`assets-3d/defense-barricade-small/workbench/workbench-vertical-004/`.

## Vérifications complémentaires

- suite adversariale du paquet : 130 tests `PASS` ;
- suite par asset `r3d` : 30 tests `PASS` (le miroir source autonome saute
  uniquement la vérification de configuration MCP installée par le dépôt hôte) ;
- cinq schémas Draft 2020-12 et cinq documents de preuve : `PASS` ;
- échange MCP `initialize` puis `tools/list` sur le vrai launcher `stdio` :
  `PASS` ;
- session `OBSERVE` sans `Candidate`, inspection immuable `PASS`, puis
  tentative de création d'un change set refusée explicitement : `PASS` ;
- doctor : Blender 5.2.0 LTS, 12 outils, zéro outil interdit, aucun TCP :
  `PASS` ;
- parsing de `.codex/config.toml` : `PASS` ;
- vérification globale `scripts/check.ps1` : configuration, StyLua, Selene et
  Luau LSP `PASS` ;
- `codex mcp list` dans ce shell : `UNKNOWN`, car `codex.exe` a répondu
  `Accès refusé` ; la configuration sera chargée par la prochaine tâche Codex.

La vérification renforcée a d'abord détecté que l'export FBX incorporait le
chemin `build-a` ou `build-b` du fichier source. Le compilateur normalise
désormais cette métadonnée avant hashing. La répétition finale prouve à la fois
le hash sémantique, le GLB et le FBX identiques ; le défaut n'a pas été masqué.

## Limite de la preuve

Le résultat prouve la boucle locale et transactionnelle. Il ne prouve pas que
la modification visuelle est approuvée, que `asset.json` autoritatif doit être
changé, que Studio a reçu le build, ni que la lisibilité mobile réelle est
meilleure.
