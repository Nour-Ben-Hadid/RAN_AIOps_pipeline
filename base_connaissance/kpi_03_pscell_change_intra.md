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

**Actions correctives types :**
- Ajuster les seuils et hystérésis de changement de PSCell.
- Compléter/corriger les relations de voisinage intra-gNB.
- Optimiser la couverture (tilt, azimut, puissance) et réduire l'interférence aux frontières.

**Sources :** 3GPP TS 37.340 (PSCell Change, mobilité SCG) ; TS 38.331 (mesures NR) ;
TS 28.552 / TS 28.554. Seuils indicatifs, dépendants de l'opérateur.
