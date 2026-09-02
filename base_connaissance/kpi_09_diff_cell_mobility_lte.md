# KPI : Diff_Cell_Mobility_Succ_Rate_LTE (%)

**Famille :** Mobilité (handovers classiques entre cellules LTE — mobilité du MCG).

**Définition.** Taux de réussite des transferts intercellulaires (*handovers*) classiques entre
cellules LTE (mobilité du groupe de cellules maître, MCG). Complémentaire des KPI de mobilité SCG,
il permet de vérifier qu'une éventuelle dégradation de la mobilité 5G secondaire ne s'accompagne
pas d'une dégradation plus large touchant aussi l'ancre 4G. Le préfixe `Diff_` indique un libellé
propre à l'opérateur (écart différentiel).

**Valeur normale (indicative).** Typiquement > 98 %.

**Interprétation croisée.** Une dégradation **simultanée** de la mobilité LTE et de la mobilité SCG
oriente vers une **cause commune** (congestion du site, défaut matériel) plutôt qu'un problème
spécifique à la 5G.

**Causes probables d'une chute :**
- Relations de voisinage manquantes ou incorrectes (ANR mal configuré).
- Seuils / paramètres de handover mal réglés (déclenchement trop tardif ou trop précoce).
- Couverture insuffisante aux frontières de cellules.
- Interface X2 / S1 défaillante pour la préparation du handover.

**Vérifications :**
- Listes de voisins et relations ANR.
- Seuils, hystérésis et temporisation des handovers.
- Couverture / SINR aux zones de recouvrement.
- État des interfaces X2 / S1.

**Actions correctives types :**
- Compléter / corriger les relations de voisinage.
- Ajuster les seuils de handover.
- Optimiser la couverture aux frontières (tilt, azimut, puissance).
- Réparer l'interface X2 / S1 si nécessaire.

**Sources :** 3GPP TS 36.331 (mobilité RRC, handover) ; TS 36.300 ; TS 32.450 (KPI E-UTRAN).
Libellé `Diff_` propre à l'opérateur. Seuils indicatifs.
