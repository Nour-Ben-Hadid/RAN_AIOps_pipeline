# KPI : SCG_Radio_Resource_Retainability_Act (%)

**Famille :** Rétenabilité (maintien de la connectivité 5G secondaire).

**Définition.** Rétenabilité des ressources radio du groupe de cellules secondaires (SCG) :
mesure la capacité à **maintenir** la connexion 5G secondaire une fois établie, sans chute
anormale. Une dégradation traduit une proportion élevée de coupures anormales de la liaison SCG
(par opposition aux libérations normales).

**Valeur normale (indicative).** Interprétation à confirmer côté NMS selon la convention de
l'opérateur (taux de rétention élevé = bon, ou taux de chute faible = bon). Dans tous les cas,
une variation défavorable signale des chutes anormales de la liaison 5G secondaire.

**Causes probables d'une dégradation :**
- Couverture ou SINR 5G insuffisants (trous de couverture SCG, bord de cellule).
- Échecs de mobilité SCG (changements de PSCell ratés → perte de la liaison).
- Interférence 5G.
- Congestion de la cellule secondaire.
- Défaut de liaison radio (RLF) côté SCG.

**Vérifications :**
- Couverture / SINR 5G dans la zone.
- Taux de succès des changements de PSCell (intra et inter).
- Niveau d'interférence et charge de la cellule.
- Alarmes radio / transport du site.

**Actions correctives types :**
- Optimiser la couverture 5G (tilt, azimut, puissance) et combler les trous de couverture.
- Fiabiliser la mobilité SCG (seuils de PSCell Change, voisinage).
- Réduire l'interférence ; ajouter de la capacité si congestion.

**Sources :** 3GPP TS 37.340 (SCG, gestion de la connectivité secondaire) ;
TS 28.552 / TS 28.554 (mesures de rétenabilité). Convention et seuils dépendants de l'opérateur.
