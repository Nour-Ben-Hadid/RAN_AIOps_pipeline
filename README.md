# Pipeline AIOps — réseau d'accès radio

Détection d'anomalies de performance RAN, corrélation avec les réclamations clients, et
génération de recommandations pour l'ingénieur réseau.

## Architecture

```
ran_aiops/                     le paquet Python — tout le code
├── chemins.py                 point unique de vérité pour TOUS les chemins
├── commun/                    partagé entre les étapes
│   ├── env.py                 chargement du .env, clé API
│   ├── gemini.py              appel HTTP à l'API Gemini
│   ├── kpi.py                 taxonomie KPI → famille de dégradation
│   ├── texte.py               normalisation de chaînes
│   └── tickets.py             chargement des tickets + catégorie prédite
├── reclamations/              étapes 2–4 : tickets, classification, localisation
│   ├── lieux_tunisie.py       référentiel des lieux, correction orthographique
│   ├── geocodage.py           adresse → coordonnées (Nominatim)
│   ├── geocodage_nodes.py     géocodage du référentiel de nodes
│   ├── classification_llm.py  catégorie de la plainte par LLM
│   ├── classification_embeddings.py   même tâche, par plongements (comparaison)
│   ├── comparaison.py         LLM vs plongements
│   ├── generation_tickets.py  tickets synthétiques ancrés sur les anomalies
│   ├── jointure.py            corrélation ticket → node + secteurs + KPI
│   ├── figures.py             figures de réglage des paramètres
│   └── pipeline.py            entrée unitaire : une plainte → un diagnostic
└── recommandation/            étape 5 : RAG à récupération déterministe
    ├── selection.py           désignation des fiches (déterministe, sans LLM)
    ├── generation.py          prompt ancré + appel Gemini + JSON validé
    └── evaluation.py          protocole A/B noté par LLM-juge

base_connaissance/             13 fiches Markdown : 9 KPI + 4 familles (versionnée)
data/                          entrées brutes (ignorée par git)
resultats/                     sorties de toutes les étapes (ignorée par git)
├── anomalies/  reclamations/  recommandation/
notebooks/                     RAN_anomalies.ipynb — étape 1, détection
```

## Principe : aucun chemin relatif

Tous les chemins vivent dans [`ran_aiops/chemins.py`](ran_aiops/chemins.py) et sont ancrés sur la
racine du dépôt via `Path(__file__).resolve().parents[1]`. **Aucun script ne dépend du répertoire
depuis lequel on le lance.** Les modules s'appellent avec `python -m`, toujours depuis la racine.

## Utilisation

```bash
# étape 1 : détection d'anomalies  →  notebooks/RAN_anomalies.ipynb

# étapes 2-4 : réclamations
python -m ran_aiops.reclamations.generation_tickets
python -m ran_aiops.reclamations.classification_llm
python -m ran_aiops.reclamations.jointure

# étape 5 : recommandation
python -m ran_aiops.recommandation.generation --n 10   # échantillon
python -m ran_aiops.recommandation.generation --n 0    # tous les tickets corrélés
python -m ran_aiops.recommandation.evaluation --n 8    # protocole A/B + LLM-juge

# diagnostic unitaire d'une plainte
python -m ran_aiops.reclamations.pipeline \
    --texte "ca coupe des que je prends la voiture" \
    --date 2026-06-25 --gouvernorat Monastir
```

## Configuration

Un fichier `.env` à la racine, jamais versionné :

```
GEMINI_API_KEY=votre_cle
```
