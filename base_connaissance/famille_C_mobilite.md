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

**Adaptation au ticket :**
- Le diagnostic calcule fournit le node et les secteurs candidats : les citer dans la reponse et
  orienter chaque verification vers ces secteurs, pas vers le reseau en general.
- Pour une plainte en deplacement, prioriser les verifications de mobilite : NRT/ANR, voisins
  manquants, seuils A2/A3, hysteresis, Time-To-Trigger, offsets inter-cellules et zones de
  recouvrement.
- Si plusieurs KPI de mobilite sont en cause, separer le controle LTE/MCG du controle PSCell/SCG,
  puis rechercher une cause commune seulement si les deux familles de compteurs se degradent.
- Presenter les causes comme hypotheses a verifier tant qu'aucune alarme, trace RRC, compteur de
  handover detaille ou mesure terrain ne confirme la cause.

**Strategie de diagnostic.**
- Toujours raisonner en couple source-cible : un KPI de mobilite ne se diagnostique pas seulement
  sur une cellule isolee. Il faut identifier les voisins ou PSCell cibles qui concentrent les
  echecs.
- Separer preparation et execution. Un echec de preparation oriente vers voisinage, admission de
  la cible, transport ou configuration ; un echec d'execution oriente davantage vers radio UE,
  timing, couverture, random access ou mauvais choix de cible.
- Pour `Diff_Cell_Mobility_Succ_Rate_LTE (%)`, l'analyse porte sur le handover LTE/MCG. Pour les
  KPI PSCell, l'analyse porte sur la jambe secondaire NR/SCG. Ne pas melanger les deux sans
  l'ecrire clairement.
- Utiliser les concepts MRO comme hypotheses : too-late handover, too-early handover, wrong-cell
  handover, ping-pong ou voisin manquant.

**Controles terrain et OSS/NMS.**
- Extraire le top des relations source-cible en echec et comparer tentative/succes/preparation/
  execution.
- Verifier NRT/ANR, PCI/SSB, EARFCN/ARFCN, offsets, blacklists, priorites inter-frequences et
  relations asymetriques.
- Controler A2/A3, hysteresis, Time-To-Trigger, cell individual offset, seuils PSCell Change et
  timers de reconfiguration.
- Realiser ou demander une trace RRC/drive test cible sur l'axe de deplacement indique ou autour
  du secteur retenu.

**Actions correctives types :**
- Compléter / corriger les relations de voisinage.
- Ajuster les seuils de mobilité.
- Optimiser la couverture aux frontières (tilt, azimut, puissance).
- Fiabiliser l'interface X2 / le backhaul (cas inter-gNB).

**Sources :** 3GPP TS 36.331 (handover LTE) ; TS 37.340 (PSCell Change) ; TS 38.423 (X2/Xn) ;
TS 32.450 / TS 28.552.
