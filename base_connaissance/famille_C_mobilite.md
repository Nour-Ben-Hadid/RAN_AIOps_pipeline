# Famille C — Mobilité

**Symptôme client typique.** « Le réseau lâche dès que je prends la voiture », « quand je me
déplace ça perd le réseau, mais chez moi ça va », « en changeant de quartier je perds la
connexion ». La dégradation est **liée au déplacement** ; stable à l'arrêt.

**Définition.** Incapacité du réseau à assurer la continuité du service lorsque le terminal passe
d'une cellule à une autre (handover LTE, changement de PSCell 5G).

**KPI EN-DC associés :**
- `Diff_Cell_Mobility_Succ_Rate_LTE (%)` — handovers entre cellules LTE (mobilité MCG).
- `EN_DC_intra_sgNB_PSCell_Change_succ_rate (%)` — changement de PSCell au sein d'un gNB.
- `EN_DC_inter_sgNB_PSCell_Change_succ_rate (%)` — changement de PSCell entre gNB (via X2).

**Causes probables (synthèse) :**
- Relations de voisinage manquantes ou incorrectes (ANR mal configuré).
- Seuils / hystérésis de handover ou de PSCell Change mal réglés.
- Couverture insuffisante aux frontières de cellules.
- Interface X2 défaillante ou latence élevée (surtout pour l'inter-gNB).

**Vérifications prioritaires :**
- Listes de voisins / relations ANR (LTE et 5G, intra et inter-gNB).
- Seuils, hystérésis, temporisation des handovers et PSCell Change.
- Couverture / SINR aux zones de recouvrement.
- État et latence des interfaces X2.

**Actions correctives types :**
- Compléter / corriger les relations de voisinage.
- Ajuster les seuils de mobilité.
- Optimiser la couverture aux frontières (tilt, azimut, puissance).
- Fiabiliser l'interface X2 / le backhaul (cas inter-gNB).

**Sources :** 3GPP TS 36.331 (handover LTE) ; TS 37.340 (PSCell Change) ; TS 38.423 (X2/Xn) ;
TS 32.450 / TS 28.552.
