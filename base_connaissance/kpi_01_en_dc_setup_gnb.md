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

**Lecture 3GPP utile pour le diagnostic.**
- La procedure de Secondary Node Addition est initiee par le Master Node et sert a etablir le
  contexte UE au Secondary Node afin d'allouer des ressources NR/SCG. Cote gNB, un echec pointe
  d'abord vers l'allocation de ressources, la configuration SCG, la cellule NR cible ou le dialogue
  de signalisation avec le Master Node.
- Ne pas assimiler automatiquement ce KPI a un debit radio faible : il mesure l'acces a la jambe
  5G secondaire. Le debit client baisse parce que la 5G n'est pas ajoutee ou reste indisponible,
  mais la cause initiale peut etre admission, couverture, configuration ou transport.
- Si `EN_DC_SETUP_succ_RATE_eNB` est bon et que seul le KPI gNB chute, privilegier une hypothese
  localisee cote gNB/NR. Si les deux KPI chutent ensemble, verifier la signalisation eNB-gNB et la
  coherence de configuration entre les deux noeuds.

**Controles operationnels a demander.**
- Sur le node et les secteurs donnes par le diagnostic, extraire les compteurs de demande,
  acceptation, rejet et echec de SgNB Addition, avec repartition par cause si le NMS la fournit
  (admission, radio, transport, timeout, configuration).
- Verifier la charge NR du secteur : PRB DL/UL, utilisateurs actifs, RRC/UE contexts, ressources
  PDCCH/PUCCH si disponibles, et comparer avec les heures normales de la meme cellule.
- Controler la qualite radio NR autour du secteur : RSRP, RSRQ, SINR, beam/SSB dominant,
  couverture indoor/outdoor, et coherences PCI/SSB/ARFCN.
- Verifier les alarmes gNB, DU/CU/F1 si architecture split, synchro/PTP, transport IP et pertes ou
  latence sur le chemin eNB-gNB.
- Controler la configuration EN-DC : cellule NR autorisee, mapping eNB-gNB, voisinage LTE-NR,
  options de bearer, licences/capacites et politiques d'admission.

**Actions formulees pour le technicien.**
- Citer explicitement le node et le secteur cible ; ne pas dire seulement "la cellule gNB".
- Proposer de comparer les compteurs `attempt/success/reject/failure` de SgNB Addition avant et
  pendant l'anomalie, puis d'isoler la cause dominante.
- Si aucune alarme ou compteur de cause n'est fourni, ecrire "hypothese a verifier" pour congestion,
  defaut transport ou couverture NR.

**Actions correctives types :**
- Soulager la congestion (ajout de capacité, équilibrage de charge, réglage des seuils d'admission).
- Optimiser la couverture 5G (tilt, azimut, puissance) si la radio SCG est faible.
- Corriger le transport/signalisation X2/F1 ; lever les alarmes matérielles.
- Réviser la configuration de la cellule et du voisinage.

**Sources :** 3GPP TS 37.340 (procédure SgNB Addition, EN-DC) ; TS 28.552 / TS 28.554
(définitions de mesures et KPI). Seuils indicatifs, dépendants de l'opérateur.
