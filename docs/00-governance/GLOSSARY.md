# Glossaire contrôlé

| Champ | Valeur |
| --- | --- |
| ID | `GOV-REF-001` |
| Classe | `REFERENCE` |
| Cycle de vie | `ACTIVE` |
| Propriétaire | Product design |
| Dernière revue | 2026-07-16 |
| Revue suivante | Introduction ou ambiguïté d'un terme produit, technique ou analytique |

Un contrat utilise ces sens ou définit explicitement une variante locale.

| Terme | Définition du projet |
| --- | --- |
| Autopsie | Restitution factuelle d'une défense : événement causal, première brèche, dégâts, routes et résultat. Elle ne doit pas inventer une recommandation non observée. |
| Activité qualifiée | Diagnostic interne `RT1_*` fondé sur une action de valeur versionnée, hors AFK, attente forcée, bot, alt abusif ou blocage technique. Il ne remplace ni ne renomme le temps de session ou le CCU Roblox. |
| Canon | Identité et règle durable dont la modification exige une décision explicite et une nouvelle version. |
| CCU30 moyen observé | Moyenne du nombre de joueurs simultanés observé sur 30 jours ; avec une mesure continue, équivalente aux minutes-joueur de présence divisées par 43 200. La présence conserve la définition de la source et ne prouve pas la satisfaction. |
| Challenge | Défense volontaire avec règles, menace, difficulté, résultat et éligibilité de récompense définis par le serveur. |
| Config | Valeur ajustable, bornée et versionnée ; elle ne transforme pas une hypothèse en vérité. |
| Contract | Comportement normatif accepté dans un scope et une version. |
| Defense / défense | Phase d'assaut autoritaire pendant laquelle la préparation est verrouillée et le résultat est calculé. |
| Dark pattern | Choix de conception qui obtient temps, argent, données ou engagement par tromperie, pression, obstruction ou exploitation d'une vulnérabilité plutôt que par valeur comprise et consentie. |
| `DEFINED_ACCEPTED` | Maturité documentaire indiquant qu'un scope possède un contrat accepté suffisamment précis. Elle ne prouve ni implémentation ni résultat. |
| `DEFERRED_BY_GATE` | Sujet inventorié mais volontairement non détaillé ou non autorisé tant que son stage gate reste fermé. |
| Dérogation | Décision explicite et bornée qui nomme la preuve manquante, le risque accepté, le scope autorisé, le décideur et la condition de réouverture. Elle ne change jamais `UNKNOWN` en `PASS`. |
| Evidence / preuve | Observation traçable. Une preuve ne vaut que pour son environnement, son scénario et ses limites. |
| Forteresse | Base personnelle qui porte la stratégie, l'identité et, plus tard seulement, la persistance du joueur. |
| FTUE | `First-Time User Experience`, depuis l'arrivée jusqu'à la compréhension et la première boucle utile définies par le contrat actif. |
| Gate | Décision conditionnelle empêchant un élargissement de scope tant que les preuves exigées ne sont pas obtenues ou explicitement dérogées. |
| Gate humain | Vérification auprès de joueurs représentatifs non briefés. Une simulation, un agent ou une revue visuelle ne le remplace pas. |
| Hypothesis / hypothèse | Affirmation falsifiable non suffisamment prouvée ; elle indique la preuve qui la ferait conserver, modifier ou abandonner. |
| Idempotence | Propriété d'une opération répétée avec la même identité et le même contenu : elle produit au plus un effet autoritaire et renvoie le résultat déjà décidé. Une identité réutilisée avec un contenu différent est rejetée. |
| North Star | Ambition de première expérience Roblox mondiale par CCU moyen sur 30 jours. Ce n'est pas la métrique d'acceptation d'une slice prototype. |
| `OPEN` | Maturité de définition signalant qu'au moins une décision nécessaire ne possède pas encore de contrat suffisant. |
| `OPTIONAL_DECISION` | Sujet pour lequel la première décision est de déterminer s'il doit exister ; aucune implémentation n'est présumée. |
| `PASS PRODUIT` | Tous les critères produit applicables, dont les observations humaines requises, sont passés. |
| `PASS PROVISOIRE / GO CONDITIONNEL` | Dérogation explicite autorisant uniquement une prochaine étape étroite et réversible malgré une preuve manquante nommée. |
| `WAIVED_BY_FOUNDER` | Condition de séquencement explicitement levée par le founder ; la preuve absente conserve son verdict `UNKNOWN` et ne devient jamais un `PASS`. |
| `PASS TECHNIQUE` | Contrat technique vérifié ; aucune conclusion automatique sur plaisir, compréhension ou rétention. |
| Phase | État exclusif de la boucle runtime, par exemple `PREPARATION`, `DEFENDING` ou `REVIEW`. |
| Plan | ExecPlan temporaire qui décrit comment atteindre et prouver un résultat sans devenir le contrat produit. |
| `READ_ONLY` | Mode de sécurité d'un profil chargé mais non autorisé à accepter des mutations persistantes, notamment lorsque le lock ou la confirmation d'écriture n'est plus fiable. Ce n'est pas un profil vide ni une sauvegarde réussie. |
| Recovery / récupération | Procédure contrôlée qui restaure une version validée sous une nouvelle révision et un nouveau lock, avec preuve et rollback ; elle ne copie jamais un ancien lock de session. |
| Rematch | Nouvelle défense initiée après analyse et modification, sans duplication de récompense ou d'état. |
| Révision | Nombre monotone appartenant à un état canonique. Une mutation acceptée avance la révision selon son contrat ; une base obsolète ou un conflit distant échoue sans écrasement silencieux. |
| Rétention durable | Objectif qualitatif : retour volontaire soutenu par une valeur réelle et la confiance, avec possibilité de quitter proprement et sans punition de l'absence. Ce n'est pas une métrique composite ; D1/D7/D30 et les diagnostics internes restent séparés. |
| Session qualifiée | Terme analytique à définir avant instrumentation selon la métrique Roblox ou le contrat local utilisé ; aucun seuil local n'est actuellement canonique. |
| Session lock | Bail persistant borné qui attribue temporairement l'écriture d'un profil à une session serveur identifiée. Son expiration ou sa perte impose un échec fermé ; il ne prouve pas qu'une sauvegarde a réussi. |
| Sidegrade | Déblocage horizontal qui change les possibilités, coûts ou interactions sans constituer une augmentation universelle de puissance. |
| Slice | Expérience verticale bornée qui relie un résultat joueur à l'implémentation et aux preuves nécessaires. |
| Snapshot | Copie immuable et versionnée de l'état préparé utilisée pour lancer, restaurer ou comparer une défense. |
| Stage gate | Ensemble de preuves minimales autorisant une classe de risque ou un élargissement de produit. |
| Verdict | `PASS`, `FAIL`, `PARTIAL`, `BLOCKED` ou `UNKNOWN` selon les observations applicables. |

## Expressions interdites sans qualification

- « rétention parfaite » ;
- « validé » sans scénario, population et verdict ;
- « production-ready » sans définition de production ;
- « sécurisé » sans périmètre et menace ;
- « performant » sans appareil, charge et mesure ;
- « les joueurs aiment » sans observation représentative.
