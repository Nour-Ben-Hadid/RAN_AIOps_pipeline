# KPI : EN_DC_SETUP_succ_RATE_gNB (%)

**Famille :** Débit / Connectivité 5G (`D_debit_5g`) — classement de référence, conforme à la table
`CATEGORIE_PAR_KPI` du pipeline. Sur le plan strictement procédural, l'ajout EN-DC est une étape
d'*accessibilité* (établissement du lien 5G secondaire) ; mais côté client, son échec fait retomber
le terminal sur la seule 4G, d'où un **symptôme de débit dégradé / perte de 5G** — c'est cette
lecture orientée symptôme qui prévaut ici.

**Définition.** Taux de réussite de la procédure d'ajout de nœud secondaire 5G (*SgNB Addition*)
en EN-DC, mesuré du **point de vue du gNB** (nœud secondaire). Il reflète la proportion de
demandes d'ajout de connectivité 5G que la cellule gNB accepte et mène à terme.

**Valeur normale (indicative).** Typiquement > 97–99 %. Une baisse marquée signale que la
cellule 5G refuse ou n'aboutit pas les ajouts EN-DC.

**Causes probables d'une chute :**
- Congestion / surcharge de la cellule gNB (ressources radio PRB, CPU, utilisateurs simultanés).
- Mauvaises conditions radio du SCG (couverture ou SINR 5G insuffisants côté secondaire).
- Rejet par le contrôle d'admission (seuils, capacité, licences).
- Problème de transport ou de signalisation entre eNB et gNB (interface X2, F1).
- Incohérence de configuration de la cellule 5G (paramètres, fréquence, voisinage).

**Vérifications :**
- Charge de la cellule gNB (taux d'utilisation PRB, CPU, nombre d'utilisateurs).
- Couverture / SINR 5G dans la zone de la cellule.
- État de l'interface X2/F1 et alarmes matérielles/transport du site.
- Seuils et compteurs du contrôle d'admission ; état des licences EN-DC.

**Actions correctives types :**
- Soulager la congestion (ajout de capacité, équilibrage de charge, réglage des seuils d'admission).
- Optimiser la couverture 5G (tilt, azimut, puissance) si la radio SCG est faible.
- Corriger le transport/signalisation X2/F1 ; lever les alarmes matérielles.
- Réviser la configuration de la cellule et du voisinage.

**Sources :** 3GPP TS 37.340 (procédure SgNB Addition, EN-DC) ; TS 28.552 / TS 28.554
(définitions de mesures et KPI). Seuils indicatifs, dépendants de l'opérateur.
