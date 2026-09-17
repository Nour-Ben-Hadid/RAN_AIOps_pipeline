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

**Lecture 3GPP utile pour le diagnostic.**
- La retenabilite E-RAB mesure la capacite a maintenir un bearer deja etabli. Elle doit etre lue
  comme un probleme de coupure/drop, pas comme un probleme d'acces initial.
- Les definitions KPI E-UTRAN distinguent l'accessibilite, la retenabilite, la mobilite et
  l'integrite. Pour ce KPI, le diagnostic doit donc chercher pourquoi le service tombe apres avoir
  commence : radio link failure, handover rate, interference, congestion ou transport.
- Un mauvais E-RAB retainability peut etre une consequence d'echecs de mobilite LTE ; il faut le
  croiser avec `Diff_Cell_Mobility_Succ_Rate_LTE (%)`.

**Controles operationnels a demander.**
- Sur le node/secteur indique, extraire les releases E-RAB normales/anormales avec cause si le NMS
  l'expose : radio connection with UE lost, handover failure, transport, core network, inactivity
  normale a exclure.
- Verifier les indicateurs radio LTE : RSRP/RSRQ/SINR, interference UL/DL, BLER, RLC/HARQ
  retransmissions, RLF, puissance UE et zones indoor/bord cellule.
- Croiser avec la mobilite : taux de succes handover, preparation/execution HO, voisins manquants,
  ping-pong, too-late/too-early handover.
- Croiser avec la charge : PRB, utilisateurs actifs, PDCCH, congestion et degradation concentree
  sur les heures de pointe.
- Controler alarmes transport/radio, coupures energie, resets eNB et pertes S1/GTP-U si plusieurs
  secteurs ou plusieurs KPI chutent en meme temps.

**Actions formulees pour le technicien.**
- Utiliser une formulation de type "coupures anormales du bearer sur le secteur X" plutot que
  "probleme d'acces".
- Prioriser les controles radio et handover si la plainte parle de coupures en cours d'usage.
- Ne pas proposer de changement de seuil d'admission comme action principale sauf si les compteurs
  montrent une congestion/admission.

**Actions correctives types :**
- Optimiser la couverture (tilt, azimut, puissance) et combler les trous.
- Fiabiliser la mobilité (relations de voisinage, seuils de handover).
- Réduire l'interférence ; ajouter de la capacité si congestion.

**Sources :** 3GPP TS 36.300 (E-RAB) ; TS 32.450 (KPI E-UTRAN) ; TS 28.552.
Libellé `Diff_` propre à l'opérateur — à confirmer côté NMS. Seuils indicatifs.
