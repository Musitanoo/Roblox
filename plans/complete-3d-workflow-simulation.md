# ExecPlan — Simulation intégrale non-production du workflow 3D

## Outcome

Ajouter puis exécuter une simulation de bout en bout qui exerce les branches
locales, humaines et externes du workflow 3D sans appeler ChatGPT Web, Roblox
Open Cloud, un appareil physique ou une mutation Studio.

Le résultat attendu est :

```json
{
  "simulationStatus": "PASS",
  "realProductionStatus": "BLOCKED",
  "productionApproved": false
}
```

Un `PASS` de simulation prouve que les contrats et transitions peuvent être
parcourus avec des doubles synthétiques. Il ne constitue jamais une preuve
humaine, Studio, mobile, cloud ou de production.

## Authority and safety

- Les sources, canons, registres et preuves officielles restent immuables.
- Toutes les données synthétiques vivent sous
  `build/simulations/complete-workflow/`.
- Les sessions synthétiques portent une enveloppe `SIMULATION_ONLY`.
- Aucun secret Roblox n'est lu, copié ou sérialisé.
- Aucune commande `-Apply`, `-ConfirmPublish` ou écriture réseau n'est permise.
- Le rapport final de simulation impose `productionApproved=false`.
- Après simulation, le vrai rapport `r3d` doit rester `BLOCKED`; un passage à
  `PASS` est un échec critique de confinement.

## Coverage

1. Validation des contrats, canons et code généré.
2. Campagne précanonique complète : six objets, seize états, une génération
   synthétique distincte par état et continuité parent/enfant.
3. Revue synthétique de chaque état et progression jusqu'à `COMPLETE`.
4. Validation des preuves Blender full/smoke et de la déterminisme A/B.
5. Validation des trois rapports Golden Scene Studio existants.
6. Double synthétique du simulateur et du mobile physique, avec métriques,
   artefacts et calculs de seuils.
7. Étude aveugle synthétique complète : douze participants, quatre experts,
   scellement, score et sélection simulée.
8. Six verrous de canon synthétiques complets et conformes au schéma, sans
   écriture dans `art/canonical-visuals/locks/`.
9. Publication v1/v2 et intégration Studio simulées comme transactions
   locales avec identité stable et rollback.
10. Rapport final synthétique hashé et audit de confinement.

## Files

- `tools/roblox-art-bible-sota-v3/tools/art/simulate_complete_workflow.py`
- `tools/roblox-art-bible-sota-v3/schemas/workflow-simulation-report.schema.json`
- `tools/roblox-art-bible-sota-v3/tests/test_complete_workflow_simulation.py`
- `tools/roblox-art-bible-sota-v3/scripts/art-direction.ps1`
- `tools/roblox-art-bible-sota-v3/README.md`
- `tools/roblox-art-bible-sota-v3/CHANGELOG.md`

## Milestones

- [x] Inspecter les gates réels et les contrats existants.
- [x] Implémenter le sandbox, les doubles et le rapport fermé.
- [x] Ajouter les tests positifs et les tests fail-closed.
- [x] Exécuter la simulation complète.
- [x] Rejouer les validations globales.
- [x] Consigner les constats et limites.

## Acceptance

- La commande de simulation termine avec code `0`.
- Les seize tâches précanoniques sont distinctes et acceptées.
- Les douze sessions participant et quatre sessions expert sont scellées.
- Le score synthétique est complet et sélectionne le territoire demandé sans
  modifier la décision officielle.
- Les six verrous synthétiques valident le schéma.
- Les transactions cloud/Studio synthétiques prouvent identité v1/v2,
  idempotence et rollback.
- Le rapport de simulation valide son schéma et tous ses hashes.
- Les hashes des surfaces officielles protégées sont identiques avant/après.
- Le vrai rapport final reste `BLOCKED` et `productionApproved=false`.
- Les tests statiques, Python, `r3d`, Luau et le manifeste passent.

## Recovery

La simulation est régénérable. En cas d'échec, supprimer uniquement le dossier
résolu sous `build/simulations/complete-workflow/`, après vérification qu'il
reste sous cette racine. Ne jamais restaurer ou écraser une preuve officielle.

## Execution evidence — 2026-07-17

La commande suivante a terminé avec code `0` :

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  .\scripts\art-direction.ps1 simulate-workflow -Resume
```

Résultats observés :

- simulation `PASS`, douze étapes sur douze ;
- seize tâches précanoniques distinctes terminées pour six objets, avec dix
  liens de continuité parent/enfant ;
- 1 263 rendus full sur 1 263 et six stress renders ;
- déterminisme A/B `PASS` pour les trois territoires ;
- douze sessions participant et quatre sessions expert synthétiques scellées ;
- six overlays de canon simulés, chacun lié à dix-sept familles de planches,
  sans mutation des locks officiels ;
- transactions cloud v1/v2 idempotentes et rollback Studio exact, avec zéro
  appel réseau, mutation cloud ou mutation Studio ;
- douze artefacts d'étape présents avec taille et SHA-256 exacts ;
- hashes des surfaces protégées identiques avant et après ;
- validation adversariale complète à 100 % ;
- trente tests `r3d` réussis et un test explicitement ignoré car sa
  configuration MCP relève de l'installation du dépôt hôte ;
- rapport réel inchangé : `BLOCKED`, `productionApproved=false`.

Le rapport autoritatif de cette répétition est :

```text
tools/roblox-art-bible-sota-v3/build/simulations/complete-workflow/current/
  workflow-simulation-report.json
```

Son SHA-256 est enregistré dans `workflow-simulation-report.sha256`.

## Residual limits

- Les réponses participant/expert sont synthétiques et ne valent pas décision
  humaine.
- Les métriques mobile sont des doubles contractuels, pas des mesures
  d'appareil physique.
- Les reçus cloud ne prouvent ni publication Roblox ni modération.
- La transaction Studio ne prouve pas un playtest sur DataModel actif.
- La conformité canonique de production reste bloquée tant que les locks
  humains officiels ne sont pas créés.
