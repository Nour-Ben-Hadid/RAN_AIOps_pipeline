# Famille B — Rétenabilité

**Symptôme client typique.** « Mes appels coupent tout le temps », « ça se déconnecte sans arrêt,
même quand je reste immobile », « la connexion tombe toutes les 5 minutes ». Le service
**s'établit puis tombe**, sans lien avec un déplacement.

**Définition.** Incapacité du réseau à **maintenir** une connexion déjà établie sans coupure
anormale (drop). À distinguer de la mobilité : ici la dégradation survient même à l'arrêt.

**KPI EN-DC associés :**
- `Diff_E-RAB_Retainability (%)` — maintien du support radio (ancre LTE).
- `SCG_Radio_Resource_Retainability_Act (%)` — maintien de la liaison 5G secondaire.
- `SCG_Radio_Resource_Retainability_origin_gNb_Act (%)` — chutes localisées côté gNB.

**Causes probables (synthèse) :**
- Trous de couverture / mauvais SINR (bord de cellule, zones mal couvertes).
- Interférence (montante ou descendante).
- Congestion de la cellule.
- Défaut de liaison radio (RLF), défaut matériel de la cellule.

**Vérifications prioritaires :**
- Couverture RSRP / SINR dans la zone.
- Niveau d'interférence et charge de la cellule.
- Alarmes radio / matériel du site (côté gNB si la variante origin_gNb est touchée).

**Actions correctives types :**
- Optimiser la couverture (tilt, azimut, puissance), combler les trous.
- Réduire l'interférence.
- Ajouter de la capacité si congestion ; traiter les défauts matériels.

**Sources :** 3GPP TS 36.300, TS 32.450 (rétenabilité LTE) ; TS 37.340 (SCG) ;
TS 28.552 / TS 28.554.
