# KPI : SCG_Radio_Resource_Retainability_origin_gNb_Act (%)

**Famille :** Rétenabilité (maintien de la connectivité 5G secondaire — cause côté gNB).

**Définition.** Variante de la rétenabilité des ressources radio SCG qui **isole les chutes dont
la cause a été localisée au niveau du gNB**. Elle permet de distinguer une dégradation
**intrinsèque à la cellule 5G** (défaut, congestion, couverture propre au gNB) d'une dégradation
liée à d'autres facteurs (mobilité du terminal hors couverture SCG, signalisation côté eNB maître).

**Valeur normale (indicative).** À interpréter conjointement avec
`SCG_Radio_Resource_Retainability_Act` selon la convention de l'opérateur.

**Interprétation croisée.**
- Dégradation **concentrée sur la variante origin_gNb** → cause propre à la cellule 5G
  (défaut matériel, congestion, couverture locale). Diagnostic orienté **côté gNB**.
- Dégradation sur la rétenabilité **globale mais pas** sur origin_gNb → cause plutôt liée à la
  mobilité ou au nœud maître.

**Causes probables (côté gNB) :**
- Défaut matériel ou alarme sur la cellule gNB.
- Congestion de la cellule 5G.
- Trou de couverture 5G propre au secteur.

**Vérifications :**
- Alarmes et état matériel de la cellule gNB.
- Charge (PRB, utilisateurs) de la cellule 5G.
- Couverture / SINR 5G dans le secteur concerné.

**Lecture 3GPP utile pour le diagnostic.**
- Cette variante oriente l'analyse vers une origine declaree cote gNB/Secondary Node. Elle est plus
  prescriptive que la retenabilite SCG globale, mais elle ne remplace pas les compteurs de cause :
  elle indique ou commencer l'investigation.
- Une degradation origin_gNb peut venir du secteur NR lui-meme, de ressources insuffisantes, de
  resets/alarmes gNB, d'une rupture de configuration SCG ou d'une qualite radio locale degradee.
- Si `SCG_Radio_Resource_Retainability_Act` est degrade mais pas `origin_gNb`, ne pas forcer une
  cause gNB ; verifier plutot mobilite, eNB maitre ou conditions UE. Si les deux sont degrads, le
  gNB devient prioritaire.

**Controles operationnels a demander.**
- Sur le node/secteur indique, consulter les alarmes gNB, DU/CU, RRU/AAU, synchronisation,
  redemarrages, indisponibilites cellule et erreurs transport proches de la date du ticket.
- Extraire les causes de release SCG origin_gNb : radio, resource unavailable, admission,
  configuration, timeout, hardware/transport si disponibles dans l'OSS/NMS.
- Verifier la charge NR et les ressources scheduler : PRB, utilisateurs, PDCCH/PUCCH, congestion,
  limites de licence/capacite et refus d'allocation.
- Controler la qualite radio du secteur : RSRP/RSRQ/SINR, interference, BLER, beam dominant,
  voisinage NR et zones de recouvrement.
- Comparer le secteur touche avec les autres secteurs du meme node : un seul secteur pointe vers
  radio/antenne/config locale ; tous les secteurs pointent vers node, transport, synchro ou energie.

**Actions formulees pour le technicien.**
- Citer que l'origine est orientee gNB et demander les alarmes/compteurs du node precise.
- Ne pas ecrire "defaut materiel" comme certitude sans alarme ; ecrire "hypothese materielle ou
  transport a verifier".
- Prioriser la comparaison intra-site : secteur touche versus autres secteurs du meme node.

**Actions correctives types :**
- Traiter le défaut matériel / lever les alarmes.
- Ajouter de la capacité ou équilibrer la charge.
- Optimiser la couverture du secteur 5G.

**Sources :** 3GPP TS 37.340 (SCG côté gNB) ; TS 28.552 / TS 28.554.
Convention et seuils dépendants de l'opérateur.
