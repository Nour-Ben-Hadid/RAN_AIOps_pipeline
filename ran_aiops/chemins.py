"""Tous les chemins du projet, ancres sur la racine : aucun script ne depend du CWD."""

from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------- entrees
ENV = RACINE / ".env"
DATA = RACINE / "data"
BASE_CONNAISSANCE = RACINE / "base_connaissance"

KPI_TABLE = DATA / "KPI Table(1).csv"
NODES_COORDS = DATA / "nodes_coordonnees.csv"
LIEUX_TUNISIE = DATA / "lieux_tunisie.txt"
CACHE_GEOCODAGE_LIEUX = DATA / "geocode_lieux_cache.json"
CACHE_GEOCODAGE_NODES = DATA / "geocode_cache.json"

# ---------------------------------------------------------------- sorties
RESULTATS = RACINE / "resultats"

# etape 1 : detection d'anomalies (notebook)
ANOMALIES = RESULTATS / "anomalies"
ANOMALIES_JOURNALIERES = ANOMALIES / "anomalies_journalieres.csv"
CELLULES_CHRONIQUES = ANOMALIES / "cellules_chroniques.csv"

# etapes 2-4 : reclamations, classification, localisation
RECLAMATIONS = RESULTATS / "reclamations"
TICKETS = RECLAMATIONS / "tickets_synthetiques.csv"
POSITIONS_REELLES = RECLAMATIONS / "positions_reelles.csv"
PRED_LLM = RECLAMATIONS / "predictions_llm_api.csv"
PRED_EMBEDDINGS = RECLAMATIONS / "predictions_embeddings.csv"
CACHE_CLASSIFICATION = RECLAMATIONS / "cache_llm.csv"
COMPARAISON = RECLAMATIONS / "comparaison_predictions.csv"
JOINTURE = RECLAMATIONS / "jointure_anomalies.csv"
FIGURES = RECLAMATIONS / "figures"

# etape 5 : recommandation
RECOMMANDATION = RESULTATS / "recommandation"
RECOMMANDATIONS = RECOMMANDATION / "recommandations.csv"
EVALUATION = RECOMMANDATION / "evaluation_ab.csv"
CACHE_RECOMMANDATION = RECOMMANDATION / "cache_llm.json"


def prevoir(chemin):
    """cree le dossier parent si besoin, et renvoie le chemin -- a appeler avant d'ecrire"""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    return chemin
