# Famille D — Débit / Connectivité 5G

**Symptôme client typique.** « Internet est devenu très lent, les vidéos ne chargent plus »,
« je n'ai plus la 5G, seulement la 4G alors que j'ai un forfait 5G », « ça rame énormément ».
Le service **fonctionne mais est dégradé** (débit faible, perte de la 5G au profit de la 4G).

**Définition.** Le terminal n'obtient pas ou ne conserve pas la connectivité 5G secondaire
(EN-DC), et retombe sur la seule capacité 4G — d'où un débit fortement réduit. La cause est
souvent l'échec ou l'instabilité de l'ajout du nœud secondaire 5G.

**KPI EN-DC associés :**
- `EN_DC_SETUP_succ_RATE_gNB (%)` — ajout de la connectivité 5G, côté gNB.
- `EN_DC_SETUP_succ_RATE_eNB (%)` — ajout de la connectivité 5G, côté eNB.
- (secondairement) `SCG_Radio_Resource_Retainability_Act (%)` si la 5G est ajoutée puis perdue.

**Causes probables (synthèse) :**
- Échec de l'ajout EN-DC (SgNB Addition) : cellule gNB saturée, mauvaise radio SCG, admission.
- Signalisation X2 entre eNB et gNB défaillante.
- Couverture / SINR 5G insuffisants pour maintenir le débit.
- Seuil de déclenchement (événement B1) mal réglé → 5G jamais ajoutée.

**Vérifications prioritaires :**
- Charge de la cellule gNB (PRB, utilisateurs) et couverture / SINR 5G.
- État de l'interface X2 eNB ↔ gNB.
- Paramétrage de l'événement B1 (seuil d'ajout de la 5G).

**Actions correctives types :**
- Décongestionner / ajouter de la capacité 5G ; optimiser la couverture SCG.
- Réparer la signalisation X2.
- Ajuster le seuil B1 pour déclencher l'ajout 5G au bon niveau de qualité.

**Sources :** 3GPP TS 37.340 (SgNB Addition, EN-DC) ; TS 36.331 (événement B1) ;
TS 28.552 / TS 28.554.
