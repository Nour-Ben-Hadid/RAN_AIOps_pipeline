# KPI : Diff_Cell_Mobility_Succ_Rate_LTE (%)

**Famille :** Mobilité (handovers classiques entre cellules LTE — mobilité du MCG).

**Définition.** Taux de réussite des transferts intercellulaires (*handovers*) classiques entre
cellules LTE (mobilité du groupe de cellules maître, MCG). Complémentaire des KPI de mobilité SCG,
il permet de vérifier qu'une éventuelle dégradation de la mobilité 5G secondaire ne s'accompagne
pas d'une dégradation plus large touchant aussi l'ancre 4G. Le préfixe `Diff_` indique un libellé
propre à l'opérateur (écart différentiel).

**Valeur normale (indicative).** Typiquement > 98 %.

**Interprétation croisée.** Une dégradation **simultanée** de la mobilité LTE et de la mobilité SCG
oriente vers une **cause commune** (congestion du site, défaut matériel) plutôt qu'un problème
spécifique à la 5G.

**Causes probables d'une chute :**
- Relations de voisinage manquantes ou incorrectes (ANR mal configuré).
- Seuils / paramètres de handover mal réglés (déclenchement trop tardif ou trop précoce).
- Couverture insuffisante aux frontières de cellules.
- Interface X2 / S1 défaillante pour la préparation du handover.

**Vérifications :**
- Listes de voisins et relations ANR.
- Seuils, hystérésis et temporisation des handovers.
- Couverture / SINR aux zones de recouvrement.
- État des interfaces X2 / S1.

**Lecture 3GPP utile pour le diagnostic.**
- Les KPI de mobilite E-UTRAN couvrent le succes du handover, avec une phase de preparation et une
  phase d'execution. Une degradation peut donc venir de la relation de voisinage/source-cible, de
  la preparation de ressources, de l'execution radio cote UE ou d'un mauvais declenchement.
- Un echec de mobilite LTE peut provoquer ensuite une coupure E-RAB ; croiser avec
  `Diff_E-RAB_Retainability (%)` permet de savoir si la mobilite degrade aussi la continuite du
  service.
- Les parametres RRC de mesure et de mobilite (evenements A2/A3, offsets, hysteresis,
  Time-To-Trigger) servent a declencher le handover au bon moment. Mal calibres, ils peuvent creer
  un handover trop tardif, trop precoce, ou vers une mauvaise cellule.

**Controles operationnels a demander.**
- Sur le secteur donne, extraire les echecs de handover par couple source-cible, et separer
  preparation failure, execution failure, timeout, cible indisponible et echec radio si disponible.
- Verifier la NRT/ANR : voisins manquants, voisins interdits, relations asymetriques,
  mauvaise priorite, PCI confusion/mod3, incoherence EARFCN ou cellule cible mal declaree.
- Controler les parametres de mobilite LTE : A2/A3, cell individual offset, hysteresis,
  Time-To-Trigger, marge de declenchement, offsets inter-frequences et restrictions de handover.
- Analyser la zone de recouvrement source-cible : RSRP/RSRQ/SINR, interference, overshooting,
  trous de couverture, azimut/tilt et difference entre indoor et axe routier.
- Rechercher ping-pong, too-late HO et too-early HO via traces RRC, drive test ou compteurs MRO
  si disponibles.

**Formulation operationnelle recommandee :**
- Appliquer les controles au `Node` et aux `Secteurs a inspecter` fournis par le diagnostic.
- Verifier la NRT / ANR du secteur concerne et rechercher les voisins manquants, incoherents ou
  asymetriques avec les cellules adjacentes.
- Comparer les compteurs de preparation et d'execution handover du secteur avec ses voisins pour
  distinguer un echec de voisinage, un declenchement trop tardif ou une frontiere de couverture.
- Controler les parametres de mobilite disponibles dans l'OSS/NMS : seuils A2/A3, hysteresis,
  Time-To-Trigger et offsets inter-cellules.
- Si la plainte mentionne un deplacement, proposer un drive test cible ou une trace en mobilite
  autour de la zone couverte par le secteur.
- Ne pas affirmer une panne X2/S1 sans alarme ou compteur associe : la presenter comme hypothese
  a verifier.

**Actions correctives types :**
- Compléter / corriger les relations de voisinage.
- Ajuster les seuils de handover.
- Optimiser la couverture aux frontières (tilt, azimut, puissance).
- Réparer l'interface X2 / S1 si nécessaire.

**Sources :** 3GPP TS 36.331 (mobilité RRC, handover) ; TS 36.300 ; TS 32.450 (KPI E-UTRAN).
Libellé `Diff_` propre à l'opérateur. Seuils indicatifs.
