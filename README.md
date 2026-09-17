# RAN AIOps Pipeline

Prototype AIOps pour le reseau d'acces radio : detection d'anomalies KPI,
correlation avec les reclamations client, puis generation de recommandations
explicables pour l'ingenieur reseau.

Le projet est concu comme un outil d'aide a la decision. Les traitements
techniques restent calcules par le pipeline ; le LLM sert uniquement a classifier
les plaintes et a formuler un diagnostic lisible.

## Fonctionnalites

- Detection d'anomalies non supervisee sur les KPI EN-DC.
- Identification des KPI contributeurs et des cellules chroniquement degradees.
- Classification des reclamations par famille de degradation.
- Localisation par adresse client, proximite geographique et coherence KPI/date.
- Generation de recommandations par RAG a recuperation deterministe.
- Interface Streamlit pour consulter les tickets, anomalies et recommandations.
- Validation manuelle par l'ingenieur avec commentaire et decision.

## Structure

```text
ran_aiops/
  anomalies/          detection ECOD et sorties anomalies
  commun/             chemins, base SQLite, API Gemini, taxonomie KPI
  reclamations/       classification, geocodage, jointure, traitement tickets
  recommandation/     selection des fiches, generation RAG, evaluation

base_connaissance/    fiches Markdown KPI/familles utilisees par le RAG
scripts/              outils hors pipeline, dont anonymisation
notebooks/            exploration et validation experimentale
app_streamlit.py      interface web pour l'ingenieur reseau
```

Les donnees brutes, resultats generes, caches, bases SQLite et secrets sont
ignores par Git.

## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Sous Linux/macOS :

```bash
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

Creer un fichier `.env` a la racine :

```text
GEMINI_API_KEY=votre_cle
```

Fichiers d'entree attendus dans `data/` :

```text
data/kpi_endc_journalier.csv
data/nodes_coordonnees.csv
data/lieux_tunisie.txt
```

`data/` n'est pas versionne. Chaque utilisateur doit fournir ses propres
donnees ou des donnees anonymisees.

## Execution

Detection d'anomalies :

```bash
python -m ran_aiops.anomalies.detection
```

Generation de tickets synthetiques pour evaluation :

```bash
python -m ran_aiops.reclamations.generation_tickets
```

Traitement d'un ticket en attente :

```bash
python -m ran_aiops.reclamations.traitement --en-attente
```

Ajouter une reclamation sans declencher le pipeline :

```bash
python -m ran_aiops.reclamations.traitement ^
  --texte "la 5G est tres lente depuis ce matin" ^
  --date 2026-06-25 ^
  --gouvernorat Monastir
```

Generation de recommandations :

```bash
python -m ran_aiops.recommandation.generation --n 10
```

Interface web :

```bash
streamlit run app_streamlit.py
```

## Donnees synthetiques

`ran_aiops/reclamations/generation_tickets.py` sert uniquement a evaluer et
demonstrer la chaine de bout en bout lorsqu'aucun historique de reclamations
reelles annotees n'est disponible. En production, les tickets doivent venir du
systeme amont de l'operateur ou etre inseres dans `reclamations.db`.

## Anonymisation

Avant publication, anonymiser les noms de nodes :

```bash
python scripts/anonymize_nodes.py
```

Le script remplace les noms reels par des identifiants stables (`NODE_0001`,
`NODE_0002`, etc.) et cree `node_mapping_private.csv`. Ce fichier de
correspondance est ignore par Git et ne doit pas etre publie.

Si des donnees sensibles ont deja ete poussees dans un depot distant, il faut
egalement nettoyer l'historique Git avant publication.

## Notes de securite

- Ne pas versionner `.env`.
- Ne pas versionner `data/`, `resultats/`, `reclamations.db` ou les caches LLM.
- Verifier l'absence de donnees sensibles avant chaque push public.
