# KPI : EN_DC_SETUP_succ_RATE_eNB (%)

**Famille :** Débit / Connectivité 5G (`D_debit_5g`) — classement de référence, conforme à la table
`CATEGORIE_PAR_KPI` du pipeline. Procéduralement, l'ajout EN-DC relève de l'*accessibilité*
(établissement du lien 5G secondaire) ; mais son échec fait retomber le client sur la 4G, d'où un
**symptôme de débit dégradé / perte de 5G** — c'est cette lecture orientée symptôme qui prévaut ici.

**Définition.** Taux de réussite de l'ajout de nœud secondaire 5G (*SgNB Addition*) en EN-DC,
mesuré du **point de vue de l'eNB** (nœud maître). L'eNB pilote la décision et la signalisation
de l'ajout ; ce KPI reflète les échecs imputables au côté maître plutôt qu'à la ressource 5G.

**Valeur normale (indicative).** Typiquement > 97–99 %.

**Interprétation croisée.** Une baisse **isolée côté gNB** oriente vers un problème propre à la
cellule 5G ; une baisse **simultanée eNB + gNB** oriente vers un problème de signalisation X2
entre les deux nœuds.

**Causes probables d'une chute :**
- Échec de la signalisation ou de l'établissement de l'interface X2 entre eNB et gNB.
- Configuration des mesures de déclenchement (événement B1 : seuil de qualité 5G à partir duquel
  l'eNB demande l'ajout du gNB) mal réglée.
- Surcharge de l'eNB (nœud maître) ou rejet côté décision.
- Terminal non compatible EN-DC ou capacité UE non détectée.
- Relations de voisinage / plan de fréquences 5G incohérents.

**Vérifications :**
- État et compteurs de l'interface X2 eNB ↔ gNB.
- Paramétrage de l'événement B1 (seuils, hystérésis, temporisation).
- Charge de l'eNB ; capacités EN-DC des terminaux dans la zone.
- Définition des cellules 5G voisines côté eNB.

**Actions correctives types :**
- Réparer / rétablir l'interface X2 ; corriger la signalisation.
- Ajuster le seuil B1 pour déclencher l'ajout au bon niveau de qualité 5G.
- Vérifier les relations de voisinage et le plan de fréquences.
- Soulager la charge de l'eNB si nécessaire.

**Sources :** 3GPP TS 37.340 (SgNB Addition, EN-DC) ; TS 36.331 (mesures RRC, événement B1) ;
TS 28.552 / TS 28.554. Seuils indicatifs, dépendants de l'opérateur.
