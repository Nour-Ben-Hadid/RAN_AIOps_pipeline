# KPI : SCG_Radio_Resource_Retainability_origin_gNb_Act (%)

**Famille :** Rétenabilité (maintien de la connectivité 5G secondaire — cause côté gNB).

**Définition.** Variante de la rétenabilité des ressources radio SCG qui **isole les chutes dont
la cause a été localisée au niveau du gNB**. Elle permet de distinguer une dégradation
**intrinsèque à la cellule 5G** (défaut, congestion, couverture propre au gNB) d'une dégradation
liée à d'autres facteurs (mobilité du terminal hors couverture SCG, signalisation côté eNB maître).

**Valeur normale (indicative).** À interpréter conjointement avec
`SCG_Radio_Resource_Retainability_Act` selon la convention de l'opérateur.

**Interprétation croisée.**
- Dégradation **concentrée sur la variante origin_gNb** → cause propre à la cellule 5G
  (défaut matériel, congestion, couverture locale). Diagnostic orienté **côté gNB**.
- Dégradation sur la rétenabilité **globale mais pas** sur origin_gNb → cause plutôt liée à la
  mobilité ou au nœud maître.

**Causes probables (côté gNB) :**
- Défaut matériel ou alarme sur la cellule gNB.
- Congestion de la cellule 5G.
- Trou de couverture 5G propre au secteur.

**Vérifications :**
- Alarmes et état matériel de la cellule gNB.
- Charge (PRB, utilisateurs) de la cellule 5G.
- Couverture / SINR 5G dans le secteur concerné.

**Actions correctives types :**
- Traiter le défaut matériel / lever les alarmes.
- Ajouter de la capacité ou équilibrer la charge.
- Optimiser la couverture du secteur 5G.

**Sources :** 3GPP TS 37.340 (SCG côté gNB) ; TS 28.552 / TS 28.554.
Convention et seuils dépendants de l'opérateur.
