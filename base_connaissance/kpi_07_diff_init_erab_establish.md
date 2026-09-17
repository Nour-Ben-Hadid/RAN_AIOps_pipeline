# KPI : Diff_Init_E-Rab_Establish_Succ_Rate (%)

**Famille :** Accessibilité (établissement du support radio porteur — ancre LTE).

**Définition.** Taux de réussite de l'établissement initial du support radio E-RAB
(*E-UTRAN Radio Access Bearer*) côté LTE, qui porte le trafic utilisateur et sert d'ancre à la
configuration EN-DC. Le préfixe `Diff_` indique un libellé propre à l'opérateur (calculé en écart
différentiel) ; l'interprétation ci-dessous est déduite du sens standard de l'E-RAB.
Un E-RAB qui ne s'établit pas empêche l'accès au service data.

**Valeur normale (indicative).** Typiquement > 98–99 %.

**Causes probables d'une chute :**
- Congestion / surcharge de l'eNB (ressources radio, PRB, utilisateurs).
- Rejet par le contrôle d'admission (capacité, licences).
- Problème de transport ou de signalisation vers le cœur (S1, S-GW/MME).
- Mauvaises conditions radio à l'accès (couverture / SINR insuffisants).
- Incohérence de configuration (QoS, bearer, paramètres cellule).

**Vérifications :**
- Charge de l'eNB (PRB, RRC connectés, échecs d'établissement).
- État de l'interface S1 et des équipements cœur (MME, S-GW).
- Couverture / SINR à l'accès dans la zone.
- Seuils d'admission et licences.

**Lecture 3GPP utile pour le diagnostic.**
- L'E-RAB porte le service utilisateur dans E-UTRAN. Un echec d'etablissement initial signifie que
  le reseau n'arrive pas a creer le bearer necessaire apres la signalisation d'acces.
- Ce KPI est un indicateur d'accessibilite service, different d'un simple probleme de debit :
  l'utilisateur peut percevoir "internet ne demarre pas", "connexion impossible" ou "service
  indisponible".
- Les causes doivent etre separees entre radio/access/admission cote eNB et signalisation coeur
  EPC cote S1/MME/S-GW. Sans compteur de cause, ne pas conclure trop vite.

**Controles operationnels a demander.**
- Sur le node/secteur indique, extraire les tentatives, succes, rejets et echecs d'E-RAB setup,
  avec cause si disponible : admission, radio resource unavailable, transport, MME/S-GW, timeout,
  QoS/bearer.
- Verifier la charge de la cellule LTE : PRB DL/UL, RRC connected users, PDCCH, admission control,
  congestion horaire et comparaison avec les jours precedents.
- Controler l'etat de l'interface S1 et des noeuds coeur associes : MME/S-GW reachability, SCTP,
  GTP-U, pertes, latence, resets et alarmes.
- Verifier la qualite radio a l'acces : RSRP/RSRQ/SINR, interference UL, puissance UE, Random
  Access/RACH si disponible et couverture indoor.
- Controler la configuration bearer/QoS : QCI/5QI mappe, ARP, politiques d'admission, licences,
  restrictions cellule et incoherences de configuration.

**Actions formulees pour le technicien.**
- Citer le secteur cible et orienter l'action vers l'etablissement E-RAB, pas vers la retenabilite
  ou la mobilite.
- Proposer de trier les echecs par cause NMS avant tout reglage radio.
- Si les causes S1/EPC ne sont pas visibles, recommander une verification coordonnee radio + coeur,
  sans affirmer que le coeur est fautif.

**Actions correctives types :**
- Décongestionner (capacité, équilibrage, réglage d'admission).
- Corriger le transport S1 / la signalisation vers le cœur.
- Optimiser la couverture d'accès si la radio est faible.
- Vérifier la configuration QoS / bearer.

**Sources :** 3GPP TS 36.300 (E-RAB, architecture E-UTRAN) ; TS 32.450 (KPI E-UTRAN) ;
TS 28.552. Libellé `Diff_` propre à l'opérateur — à confirmer côté NMS. Seuils indicatifs.
