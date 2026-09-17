# KPI : EN_DC_inter_sgNB_PSCell_Change_succ_rate (%)

**Famille :** Mobilité (mobilité entre gNB distincts).

**Définition.** Taux de réussite des changements de cellule primaire secondaire (*PSCell Change*)
lorsque la cellule cible appartient à un **gNB différent** de la source (changement
**inter-gNB**). La procédure implique une signalisation X2 supplémentaire entre les deux gNB,
ce qui la rend **structurellement plus sensible aux échecs** que le cas intra-gNB.

**Valeur normale (indicative).** Typiquement > 95–98 %, souvent un peu inférieure à l'intra-gNB.
Bon indicateur de la santé du *backhaul* et du plan de fréquences aux frontières de cellules 5G.

**Causes probables d'une chute :**
- Interface X2 défaillante ou latence élevée entre les deux gNB impliqués.
- Relations de voisinage inter-gNB manquantes ou incorrectes (ANR mal configuré).
- Couverture / plan de fréquences 5G dégradés aux frontières entre gNB.
- Congestion de la cellule cible.

**Vérifications :**
- État, latence et compteurs de l'interface X2 entre gNB source et cible.
- Définitions de voisinage inter-gNB (relations ANR).
- Couverture et fréquences aux zones de recouvrement entre gNB.
- Charge de la cellule cible.

**Lecture 3GPP utile pour le diagnostic.**
- En inter-gNB, le changement de PSCell implique un Secondary Node Change ou une coordination entre
  noeuds distincts. La procedure depend donc a la fois du choix radio de la cellule cible et de la
  signalisation/transport entre gNB.
- Une degradation peut provenir d'une preparation qui echoue, d'une execution qui echoue apres
  reconfiguration, d'un mauvais choix de cible, d'une cellule cible saturee ou d'un probleme X2/Xn
  selon l'architecture de transport.
- Ce KPI est plus sensible que l'intra-gNB aux erreurs de voisinage inter-sites, aux delais de
  backhaul et aux incoherences de configuration entre vendors/versions si le reseau est heterogene.

**Controles operationnels a demander.**
- Identifier les couples source-cible impliques autour du node/secteur donne : gNB source,
  gNB cible, cellule NR cible, PCI/SSB/ARFCN et relation de voisinage inter-gNB.
- Extraire les compteurs de preparation et d'execution PSCell Change inter-gNB : demandes,
  acceptations, rejets, timeouts, echec RA sur cible et causes de release SCG si disponibles.
- Verifier l'etat de l'interface X2/Xn ou du transport entre gNB : disponibilite, latence, pertes,
  MTU, routage, synchronisation et alarmes transport.
- Controler la charge et la qualite radio de la cellule cible : une cible surchargee ou mal couverte
  peut refuser ou faire echouer l'execution.
- Comparer les echecs par voisin : un seul voisin defaillant oriente vers relation/transport/cible ;
  plusieurs voisins defaillants orientent vers parametrage de mobilite ou probleme source.

**Actions formulees pour le technicien.**
- Toujours citer le secteur du diagnostic et demander le controle des relations inter-gNB associees.
- Si le diagnostic ne donne pas le gNB cible, proposer d'extraire le top des couples source-cible en
  echec avant toute action de parametrage.
- Ne pas affirmer "interface X2 defaillante" sans compteur timeout, alarme ou mesure transport :
  la formuler comme verification prioritaire.

**Actions correctives types :**
- Réparer / fiabiliser l'interface X2 et le backhaul entre gNB.
- Ajouter / corriger les relations de voisinage inter-gNB.
- Optimiser la couverture et le plan de fréquences aux frontières.
- Décongestionner la cellule cible si nécessaire.

**Sources :** 3GPP TS 37.340 (PSCell Change inter-gNB, EN-DC) ; TS 38.423 (X2/XnAP) ;
TS 28.552 / TS 28.554. Seuils indicatifs, dépendants de l'opérateur.
