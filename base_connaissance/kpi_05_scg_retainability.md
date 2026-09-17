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

**Lecture 3GPP utile pour le diagnostic.**
- La retenabilite SCG concerne le maintien de la connectivite secondaire NR apres son ajout. Une
  baisse signifie que la jambe SCG est liberee ou perdue de facon anormale, mais ne prouve pas a
  elle seule la cause.
- En MR-DC/EN-DC, les echecs SCG peuvent etre lies a la radio NR, a la mobilite PSCell, a la
  configuration des bearers, au transport ou a la coordination Master Node / Secondary Node.
- Croiser ce KPI avec les KPI de PSCell Change : si la retenabilite chute en meme temps que la
  mobilite SCG, investiguer d'abord les frontieres de cellules et les evenements de changement
  PSCell ; si elle chute seule, investiguer couverture, interference, congestion ou defaut local.

**Controles operationnels a demander.**
- Sur le node et les secteurs donnes, separer les releases normales des releases anormales SCG :
  cause radio, mobility failure, timeout, admission, transport, UE context release si le NMS expose
  ces dimensions.
- Extraire RSRP/RSRQ/SINR NR, BLER, retransmissions HARQ/RLC, radio link failures et mesures de
  qualite par secteur pour confirmer ou exclure une cause radio.
- Verifier les compteurs de charge NR : PRB DL/UL, utilisateurs actifs, PDCCH/PUCCH, saturation
  scheduler et congestion ponctuelle sur la date du ticket.
- Croiser avec les KPI `EN_DC_SETUP_succ_RATE_*` : si setup et retenabilite sont tous deux
  mauvais, le probleme peut commencer des l'ajout ; si setup est bon puis retenabilite mauvaise,
  la perte arrive apres et doit etre traitee comme maintien/mobilite.
- Verifier alarmes radio, transport, synchro et resets DU/CU/gNB avant de parler de defaut materiel.

**Actions formulees pour le technicien.**
- Ecrire "liaison 5G secondaire instable sur le secteur X" plutot que "panne 5G" si seule la
  retenabilite SCG est degradee.
- Demander un tri par cause de release SCG avant action corrective.
- Proposer une trace RRC/SCG failure sur la zone si les compteurs agreges ne suffisent pas.

**Actions correctives types :**
- Optimiser la couverture 5G (tilt, azimut, puissance) et combler les trous de couverture.
- Fiabiliser la mobilité SCG (seuils de PSCell Change, voisinage).
- Réduire l'interférence ; ajouter de la capacité si congestion.

**Sources :** 3GPP TS 37.340 (SCG, gestion de la connectivité secondaire) ;
TS 28.552 / TS 28.554 (mesures de rétenabilité). Convention et seuils dépendants de l'opérateur.
