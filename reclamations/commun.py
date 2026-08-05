import re

TICKETS = "resultats/tickets_synthetiques.csv"

# node technique -> zone lisible (NODE_0007 -> Ain Zrigue)
PREFIX = "B5G4G_"
# suffixes techniques retires : site partage / batiment / numero de secteur
STOP_HIGH = {"TT", "CTT", "COH", "PART", "PARTAGE", "LGD", "LGDR", "OR", "I", "II", "III", "IV"}


def est_correct(pred, attendu):
    """un ticket ambigu est juste si la prediction est l'une des 2 categories admises"""
    return pred in str(attendu).split("|")


def node_to_zone(node):
    """nom de lieu lisible a partir du Node technique"""
    body = node[len(PREFIX):] if node.startswith(PREFIX) else node
    kept = [t for t in body.split("_") if t.upper() not in STOP_HIGH and not re.fullmatch(r"\d+", t)]
    return " ".join(w.capitalize() for w in (kept or body.split("_")))
