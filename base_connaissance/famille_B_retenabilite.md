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

**Strategie de diagnostic.**
- Distinguer une coupure du bearer LTE, une perte de la jambe 5G secondaire et une coupure liee a
  la mobilite. La retenabilite concerne un service deja etabli : la question principale est
  "pourquoi tombe-t-il ?".
- Si `Diff_E-RAB_Retainability (%)` est degrade, analyser les drops du bearer LTE et les causes
  radio/transport/mobilite.
- Si `SCG_Radio_Resource_Retainability_Act (%)` est degrade mais que l'E-RAB LTE reste stable,
  orienter vers l'instabilite de la jambe 5G secondaire plutot que vers une coupure totale du
  service.
- Si `SCG_Radio_Resource_Retainability_origin_gNb_Act (%)` est degrade, prioriser le gNB/secteur
  NR indique, mais confirmer par alarmes ou causes de release.
- Si retenabilite et mobilite chutent ensemble, traiter d'abord les frontieres de cellules et les
  echecs de handover/PSCell Change.

**Controles terrain et OSS/NMS.**
- Extraire les releases normales/anormales et leurs causes : radio, RLF, handover failure, SCG
  failure, transport, core, admission ou timeout.
- Controler RSRP/RSRQ/SINR, BLER, HARQ/RLC retransmissions, interference UL/DL et zones bord de
  cellule.
- Comparer charge et drops : PRB, utilisateurs actifs, scheduler, heures de pointe.
- Verifier alarmes radio, transport, synchro, energie, reset eNB/gNB et indisponibilites cellule.
- Comparer secteurs d'un meme node pour detecter probleme local versus probleme site.

**Consignes de generation.**
- Formuler "coupures anormales" ou "liaison secondaire instable" selon le KPI exact.
- Citer les secteurs a inspecter et proposer un ordre : causes de release, radio, charge, alarmes.
- Ne pas conclure a un defaut materiel sans alarme ; ne pas conclure a congestion sans charge.

**Actions correctives types :**
- Optimiser la couverture (tilt, azimut, puissance), combler les trous.
- Réduire l'interférence.
- Ajouter de la capacité si congestion ; traiter les défauts matériels.

**Sources :** 3GPP TS 36.300, TS 32.450 (rétenabilité LTE) ; TS 37.340 (SCG) ;
TS 28.552 / TS 28.554.
