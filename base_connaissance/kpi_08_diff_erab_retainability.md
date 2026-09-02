# KPI : Diff_E-RAB_Retainability (%)

**Famille :** Rétenabilité (maintien du support radio — ancre LTE).

**Définition.** Rétenabilité du support radio E-RAB côté LTE : capacité à **maintenir** un E-RAB
déjà établi sans coupure anormale. Une dégradation traduit des chutes anormales de bearers (drops)
sur l'ancre 4G. Le préfixe `Diff_` indique un libellé propre à l'opérateur (écart différentiel) ;
interprétation déduite du sens standard de l'E-RAB. Ce KPI permet aussi de vérifier que l'ajout de
la connectivité 5G secondaire ne dégrade pas le service porté par l'ancre 4G.

**Valeur normale (indicative).** Typiquement taux de rétention très élevé / taux de chute faible.

**Causes probables d'une dégradation :**
- Trous de couverture / mauvais SINR (bord de cellule, zones mal couvertes).
- Échecs de mobilité (handovers ratés → coupure).
- Interférence (montante ou descendante).
- Congestion de la cellule.
- Défaut de liaison radio (RLF).

**Vérifications :**
- Couverture RSRP / SINR dans la zone.
- Taux de succès des handovers LTE (voir `Diff_Cell_Mobility_Succ_Rate_LTE`).
- Niveau d'interférence et charge de la cellule.
- Alarmes radio / transport.

**Actions correctives types :**
- Optimiser la couverture (tilt, azimut, puissance) et combler les trous.
- Fiabiliser la mobilité (relations de voisinage, seuils de handover).
- Réduire l'interférence ; ajouter de la capacité si congestion.

**Sources :** 3GPP TS 36.300 (E-RAB) ; TS 32.450 (KPI E-UTRAN) ; TS 28.552.
Libellé `Diff_` propre à l'opérateur — à confirmer côté NMS. Seuils indicatifs.
