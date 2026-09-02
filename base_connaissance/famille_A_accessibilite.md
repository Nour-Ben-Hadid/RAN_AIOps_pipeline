# Famille A — Accessibilité

**Symptôme client typique.** « Je n'ai aucun accès à internet », « ça ne se connecte pas du tout »,
« mes appels ne passent jamais », « aucune connexion possible ». Le service **ne s'établit pas**.

**Définition.** Incapacité du réseau à accepter et établir une nouvelle demande de service
(connexion, session data, ajout de connectivité secondaire). C'est la première étape d'accès :
son échec empêche tout usage, quel que soit l'état du reste du réseau.

**KPI EN-DC associés :**
- `Diff_Init_E-Rab_Establish_Succ_Rate (%)` — établissement du support radio (ancre LTE).

> Remarque : les KPI `EN_DC_SETUP_succ_RATE_gNB/eNB` relèvent *procéduralement* de
> l'accessibilité (ajout du lien 5G secondaire), mais le pipeline les classe en famille
> **D — Débit / 5G** (`CATEGORIE_PAR_KPI`), car leur échec se traduit côté client par une perte
> de débit 5G. Voir la fiche « Famille D ».

**Causes probables (synthèse) :**
- Congestion / surcharge de la cellule (ressources radio saturées).
- Rejet par le contrôle d'admission (capacité, licences).
- Problème de transport / signalisation vers le cœur (S1) ou entre eNB et gNB (X2).
- Mauvaises conditions radio à l'accès (couverture / SINR insuffisants).

**Vérifications prioritaires :**
- Charge de la cellule (PRB, utilisateurs, échecs d'établissement).
- État des interfaces (S1 vers le cœur, X2 pour l'EN-DC) et alarmes du site.
- Couverture / SINR dans la zone.
- Seuils d'admission et licences.

**Actions correctives types :**
- Décongestionner (capacité, équilibrage de charge, réglage d'admission).
- Corriger le transport / la signalisation.
- Optimiser la couverture d'accès.

**Sources :** 3GPP TS 36.300, TS 32.450 (accessibilité LTE) ; TS 37.340 (accès EN-DC) ;
TS 28.552 / TS 28.554.
