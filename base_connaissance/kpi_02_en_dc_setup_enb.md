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

**Lecture 3GPP utile pour le diagnostic.**
- Cote eNB, la procedure EN-DC depend du Master Node : mesures UE, decision d'ajout du Secondary
  Node, preparation du SgNB Addition et transfert de configuration RRC vers l'UE.
- Une degradation cote eNB peut venir d'un mauvais declenchement des mesures NR, d'un voisinage
  LTE-NR incomplet, d'une incoherence de configuration avec le gNB, d'un probleme X2 ou d'une
  surcharge/admission cote noeud maitre.
- L'evenement B1 de mesure inter-RAT sert typiquement a detecter qu'une cellule NR devient assez
  bonne pour declencher l'ajout. Des seuils trop stricts empechent l'ajout ; des seuils trop
  permissifs peuvent declencher trop tot et produire des echecs.

**Controles operationnels a demander.**
- Sur le secteur LTE indique, verifier la configuration des mesures NR : B1, seuils, hysteresis,
  Time-To-Trigger, frequences NR surveillees et liste des cellules NR voisines.
- Comparer les compteurs EN-DC setup cote eNB et cote gNB : si les demandes partent mais echouent
  cote gNB, basculer l'analyse vers la cellule NR ; si les demandes ne partent pas, analyser la
  decision cote eNB et les mesures UE.
- Controler la relation X2 eNB-gNB : etat administratif/operationnel, timeouts de preparation,
  erreurs de configuration, latence ou pertes transport.
- Verifier les capacites UE et politiques d'activation EN-DC : terminaux compatibles, feature
  activee, restrictions par cellule, licences et admission.
- Croiser avec la charge LTE : PRB, RRC connected, PDCCH, rejets admission, car un eNB sature peut
  refuser ou retarder l'ajout du Secondary Node.

**Actions formulees pour le technicien.**
- Citer le secteur LTE cible et demander explicitement le controle du voisinage LTE-NR associe.
- Employer des formulations conditionnelles : "si les compteurs montrent des timeouts X2",
  "si les mesures B1 ne sont pas declenchees", "si la cellule NR cible est saturee".
- Ne pas conclure a un terminal incompatible sans distribution UE/capability ou traces RRC.

**Actions correctives types :**
- Réparer / rétablir l'interface X2 ; corriger la signalisation.
- Ajuster le seuil B1 pour déclencher l'ajout au bon niveau de qualité 5G.
- Vérifier les relations de voisinage et le plan de fréquences.
- Soulager la charge de l'eNB si nécessaire.

**Sources :** 3GPP TS 37.340 (SgNB Addition, EN-DC) ; TS 36.331 (mesures RRC, événement B1) ;
TS 28.552 / TS 28.554. Seuils indicatifs, dépendants de l'opérateur.
