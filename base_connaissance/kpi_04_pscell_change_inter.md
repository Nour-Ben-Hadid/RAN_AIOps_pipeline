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

**Actions correctives types :**
- Réparer / fiabiliser l'interface X2 et le backhaul entre gNB.
- Ajouter / corriger les relations de voisinage inter-gNB.
- Optimiser la couverture et le plan de fréquences aux frontières.
- Décongestionner la cellule cible si nécessaire.

**Sources :** 3GPP TS 37.340 (PSCell Change inter-gNB, EN-DC) ; TS 38.423 (X2/XnAP) ;
TS 28.552 / TS 28.554. Seuils indicatifs, dépendants de l'opérateur.
