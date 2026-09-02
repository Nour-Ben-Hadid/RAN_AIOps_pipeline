# Base de connaissances RAG — fiches KPI → cause → action

Ces fiches constituent le corpus de connaissance du module de génération de recommandations
(RAG). Chaque fiche est un fichier `.md` autonome (une par KPI EN-DC et une par famille de
dégradation), pensé pour être découpé et indexé tel quel par l'embedder.

## Contenu
- `kpi_01` … `kpi_09` : une fiche par KPI EN-DC exploité dans le projet.
- `famille_A` … `famille_D` : une fiche par famille de dégradation (accessibilité,
  rétenabilité, mobilité, débit 5G), qui agrège les KPI concernés et le vocabulaire client.

## Sources
Fiches rédigées à partir des spécifications 3GPP publiques (versions officielles ETSI) :
- **TS 37.340** — Multi-connectivité (EN-DC) : procédures SgNB Addition, PSCell Change, SCG.
- **TS 28.552 / TS 28.554** — Mesures de performance et définitions des KPI 5G.
- **TS 32.450** — Définitions des KPI E-UTRAN (LTE).
- **TS 36.300 / TS 36.331 / TS 38.331** — Architecture E-UTRAN, RRC (établissement, mobilité).

Les guides d'optimisation équipementier (Ericsson/Nokia/Huawei) ont servi de lecture de fond ;
aucune de leurs pages n'est reproduite ici — les fiches sont une reformulation propre.

## Avertissements
- Les **seuils** (« valeur normale ») sont **indicatifs** : ils dépendent de l'opérateur, de
  l'équipementier et de la zone. À ajuster sur les distributions réelles.
- Les KPI préfixés `Diff_` sont des libellés **propres à l'opérateur** (calculés en écart) ;
  leur interprétation ci-dessous est déduite du nom et du contexte 3GPP, à confirmer côté NMS.
- Fiches à **relire et valider** par un ingénieur avant mise en production.

## Intégration
- Ce dossier (fiches rédigées) est **versionné** dans le dépôt.
- Les PDF de spécifications téléchargés et la base vectorielle ne sont **pas** versionnés
  (voir `.gitignore`).
