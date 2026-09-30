"""Tous les chemins du projet, ancres sur la racine : aucun script ne depend du CWD."""

from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------- entrees
ENV = RACINE / ".env"
DATA = RACINE / "data"
BASE_CONNAISSANCE = RACINE / "base_connaissance"

# reclamations recues : donnee primaire, ni regenerable ni versionnee
BASE_RECLAMATIONS = RACINE / "reclamations.db"

KPI_TABLE = DATA / "kpi_endc_journalier.csv"
NODES_COORDS = DATA / "nodes_coordonnees.csv"
LIEUX_TUNISIE = DATA / "lieux_tunisie.txt"
CACHE_GEOCODAGE_LIEUX = DATA / "geocode_lieux_cache.json"
TUNISIA_LOCATIONS = RACINE / "ran_aiops" / "reclamations" / "referentiels" / "tunisia_locations.json"

# ---------------------------------------------------------------- sorties
RESULTATS = RACINE / "resultats"
CACHE_LLM = RESULTATS / "cache_llm.json"

# etape 1 : detection d'anomalies (notebook)
ANOMALIES = RESULTATS / "anomalies"
ANOMALIES_JOURNALIERES = ANOMALIES / "anomalies_journalieres.csv"
CELLULES_CHRONIQUES = ANOMALIES / "cellules_chroniques.csv"
CELLULES_HISTORIQUE_COURT = ANOMALIES / "cellules_historique_insuffisant.csv"

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


def prevoir(chemin):
    """cree le dossier parent si besoin, et renvoie le chemin -- a appeler avant d'ecrire"""
    chemin = Path(chemin)
    chemin.parent.mkdir(parents=True, exist_ok=True)
    return chemin
