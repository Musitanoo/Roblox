# Roblox Top 1

Expérience Roblox PvE coopérative, mobile-first, construite selon un principe de
validation :

> One verb. Infinite situations. Persistent identity. Better with friends.

## État actuel

- Ambition long terme : première expérience Roblox mondiale par CCU moyen sur
  30 jours.
- Boucle technique Defense 0.2 : `PASS TECHNIQUE` et
  `PASS PROVISOIRE / GO CONDITIONNEL` ; compréhension humaine `UNKNOWN`.
- Build Loop 0.3 : `PASS TECHNIQUE` ; T01 à T32 sont `PASS`, tandis que le gate
  humain reste `UNKNOWN`. Son exécution participant est
  `WAIVED_BY_FOUNDER` pour le séquencement interne par ADR-0002, sans
  `PASS PRODUIT`.
- Action Loop 0.4.1, Progression Loop 0.5.1 et Persistence Loop 0.6.1 :
  spécifications candidates intégrées au corpus et enregistrées `IN_REVIEW`,
  sans autorisation automatique d'implémentation.
- Progression persistante, économie, trading, monétisation et LiveOps étendus :
  non autorisés avant leurs stage gates.

Commencer par le [portail documentaire](docs/README.md). Le
[registre](docs/00-governance/DOCUMENT_REGISTER.md) indique l'autorité, le
statut et le déclencheur de revue de chaque document.

Le
[registre global de définition](docs/00-governance/PRODUCT_DEFINITION_REGISTER.md)
inventorie tout ce qui reste à décider, accepter ou prouver sans ouvrir
prématurément les gates correspondants.

Chaîne actuelle : Build 0.3 (`PASS TECHNIQUE`) → G3 (preuve `UNKNOWN`,
séquencement `WAIVED_BY_FOUNDER`) → Action 0.4.1 (`IN_REVIEW`, prochaine
décision admissible) → Progression 0.5.1 (`IN_REVIEW`, G4 fermé) → Persistence
0.6.1 (`IN_REVIEW`, G4 fermé).

## Commande de vérification

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\check.ps1
```
