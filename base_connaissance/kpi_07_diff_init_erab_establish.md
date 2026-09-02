# KPI : Diff_Init_E-Rab_Establish_Succ_Rate (%)

**Famille :** Accessibilité (établissement du support radio porteur — ancre LTE).

**Définition.** Taux de réussite de l'établissement initial du support radio E-RAB
(*E-UTRAN Radio Access Bearer*) côté LTE, qui porte le trafic utilisateur et sert d'ancre à la
configuration EN-DC. Le préfixe `Diff_` indique un libellé propre à l'opérateur (calculé en écart
différentiel) ; l'interprétation ci-dessous est déduite du sens standard de l'E-RAB.
Un E-RAB qui ne s'établit pas empêche l'accès au service data.

**Valeur normale (indicative).** Typiquement > 98–99 %.

**Causes probables d'une chute :**
- Congestion / surcharge de l'eNB (ressources radio, PRB, utilisateurs).
- Rejet par le contrôle d'admission (capacité, licences).
- Problème de transport ou de signalisation vers le cœur (S1, S-GW/MME).
- Mauvaises conditions radio à l'accès (couverture / SINR insuffisants).
- Incohérence de configuration (QoS, bearer, paramètres cellule).

**Vérifications :**
- Charge de l'eNB (PRB, RRC connectés, échecs d'établissement).
- État de l'interface S1 et des équipements cœur (MME, S-GW).
- Couverture / SINR à l'accès dans la zone.
- Seuils d'admission et licences.

**Actions correctives types :**
- Décongestionner (capacité, équilibrage, réglage d'admission).
- Corriger le transport S1 / la signalisation vers le cœur.
- Optimiser la couverture d'accès si la radio est faible.
- Vérifier la configuration QoS / bearer.

**Sources :** 3GPP TS 36.300 (E-RAB, architecture E-UTRAN) ; TS 32.450 (KPI E-UTRAN) ;
TS 28.552. Libellé `Diff_` propre à l'opérateur — à confirmer côté NMS. Seuils indicatifs.
