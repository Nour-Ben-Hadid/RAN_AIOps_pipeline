# KPI : EN_DC_intra_sgNB_PSCell_Change_succ_rate (%)

**Famille :** Mobilité (mobilité au sein du groupe de cellules secondaires SCG).

**Définition.** Taux de réussite des changements de cellule primaire secondaire (*PSCell Change*)
lorsque la cellule cible appartient au **même gNB physique** que la cellule source (changement
**intra-gNB**). Mesure la continuité de la connectivité 5G secondaire quand l'utilisateur se
déplace à l'intérieur de la couverture d'un même gNB.

**Valeur normale (indicative).** Typiquement > 98 %. Structurellement plus fiable que le
changement inter-gNB (pas de dépendance à une interface X2 entre gNB distincts).

**Causes probables d'une chute :**
- Paramétrage de mobilité SCG mal réglé (seuils, hystérésis, temporisation du changement).
- Relations de voisinage internes au gNB incomplètes ou incorrectes.
- Conditions radio dégradées (SINR/couverture 5G) aux frontières des cellules du gNB.
- Interférence 5G locale.

**Vérifications :**
- Paramètres de déclenchement du PSCell Change (seuils, hystérésis).
- Définition des cellules PSCell voisines au sein du gNB.
- Couverture / SINR 5G aux zones de recouvrement.

**Lecture 3GPP utile pour le diagnostic.**
- Le PSCell Change est une reconfiguration synchronisee de la liaison SCG vers une nouvelle
  cellule primaire secondaire. En intra-gNB, la procedure reste dans le meme Secondary Node : la
  signalisation inter-noeuds est moins critique que la qualite radio, le choix de cible et les
  parametres de mobilite SCG.
- Une chute du taux de succes signifie que l'UE n'arrive pas de maniere fiable a terminer le
  changement vers la PSCell cible. Les causes a separer sont : declenchement trop tardif,
  declenchement trop tot, mauvais choix de PSCell cible, echec de random access sur la cible,
  frontiere de couverture ou interference NR.
- Si ce KPI est degrade sans degradation LTE, la mobilite de l'ancre 4G peut rester correcte tandis
  que la jambe 5G secondaire est instable.

**Controles operationnels a demander.**
- Sur le node et les secteurs indiques, verifier les relations de voisinage NR intra-gNB :
  cellules source/cible, PCI, SSB/beam, ARFCN, priorites et coherences de configuration.
- Extraire les compteurs de PSCell Change : tentatives, succes, echecs de preparation,
  echecs d'execution, echecs de random access et timers expires si disponibles.
- Controler les parametres de mobilite SCG : seuils de declenchement, offsets source/cible,
  hysteresis, Time-To-Trigger, T304 ou timer equivalent de reconfiguration synchronisee.
- Analyser la qualite NR sur les zones de recouvrement : RSRP/RSRQ/SINR, interference, beams
  dominants et trous de couverture entre source et cible.
- Comparer les echecs par couple source-cible pour detecter une cible unique mal configuree ou
  un probleme general de parametrage.

**Actions formulees pour le technicien.**
- Nommer le secteur source ou candidat fourni par le diagnostic et demander une verification
  source-cible, pas seulement "optimiser la mobilite".
- Pour une plainte en deplacement, recommander une trace RRC/drive test sur la frontiere entre
  cellules du meme gNB.
- Presenter "too late", "too early" ou "wrong PSCell" comme hypotheses de MRO a confirmer par
  mesures UE/traces, pas comme conclusions automatiques.

**Actions correctives types :**
- Ajuster les seuils et hystérésis de changement de PSCell.
- Compléter/corriger les relations de voisinage intra-gNB.
- Optimiser la couverture (tilt, azimut, puissance) et réduire l'interférence aux frontières.

**Sources :** 3GPP TS 37.340 (PSCell Change, mobilité SCG) ; TS 38.331 (mesures NR) ;
TS 28.552 / TS 28.554. Seuils indicatifs, dépendants de l'opérateur.
