"""Base SQLite des reclamations : une ligne par ticket, entree et sortie."""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

from ran_aiops.chemins import BASE_RECLAMATIONS

CHAMPS_LIEU = ["gouvernorat", "delegation", "localite", "adresse_libre", "code_postal"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS reclamations (
    ticket_id      TEXT PRIMARY KEY,
    recu_le        TEXT NOT NULL,
    date           TEXT,
    texte_plainte  TEXT NOT NULL,
    gouvernorat    TEXT,
    delegation     TEXT,
    localite       TEXT,
    adresse_libre  TEXT,
    code_postal    TEXT,
    statut         TEXT NOT NULL DEFAULT 'recu',
    traite_le      TEXT,
    erreur         TEXT,
    categorie      TEXT,
    confiance      REAL,
    node_retenu    TEXT,
    secteurs       TEXT,
    kpis           TEXT,
    precision_loc  TEXT,
    distance_km    REAL,
    fiches         TEXT,
    diagnostic     TEXT,
    cause_probable TEXT,
    actions        TEXT,
    decision_ingenieur TEXT,
    commentaire_ingenieur TEXT,
    valide_le      TEXT
);
CREATE INDEX IF NOT EXISTS idx_statut ON reclamations(statut);
"""

MIGRATIONS = {
    "decision_ingenieur": "TEXT",
    "commentaire_ingenieur": "TEXT",
    "valide_le": "TEXT",
}


def _maintenant():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def connexion():
    cx = sqlite3.connect(BASE_RECLAMATIONS)
    cx.row_factory = sqlite3.Row
    cx.execute("PRAGMA journal_mode=WAL")
    try:
        yield cx
        cx.commit()
    finally:
        cx.close()


def initialiser():
    BASE_RECLAMATIONS.parent.mkdir(parents=True, exist_ok=True)
    with connexion() as cx:
        cx.executescript(SCHEMA)
        colonnes = {r["name"] for r in cx.execute("PRAGMA table_info(reclamations)")}
        for nom, type_sql in MIGRATIONS.items():
            if nom not in colonnes:
                cx.execute(f"ALTER TABLE reclamations ADD COLUMN {nom} {type_sql}")


def enregistrer(texte_plainte, date=None, ticket_id=None, **lieu):
    """insere une reclamation recue et renvoie son ticket_id"""
    initialiser()
    ligne = {"ticket_id": ticket_id or uuid4().hex[:12], "recu_le": _maintenant(),
             "date": date, "texte_plainte": texte_plainte,
             **{c: lieu.get(c) for c in CHAMPS_LIEU}}
    colonnes = ", ".join(ligne)
    with connexion() as cx:
        cx.execute(f"INSERT INTO reclamations ({colonnes}) "
                   f"VALUES ({', '.join('?' * len(ligne))})", tuple(ligne.values()))
    return ligne["ticket_id"]


def en_attente(limite=None):
    with connexion() as cx:
        requete = "SELECT * FROM reclamations WHERE statut = 'recu' ORDER BY recu_le"
        if limite:
            requete += f" LIMIT {int(limite)}"
        return [dict(r) for r in cx.execute(requete)]


def lire(ticket_id):
    with connexion() as cx:
        ligne = cx.execute("SELECT * FROM reclamations WHERE ticket_id = ?",
                           (ticket_id,)).fetchone()
    return dict(ligne) if ligne else None


def maj(ticket_id, statut, **champs):
    champs["statut"] = statut
    if statut in ("traite", "echec"):
        champs["traite_le"] = _maintenant()
    affectations = ", ".join(f"{c} = ?" for c in champs)
    with connexion() as cx:
        cx.execute(f"UPDATE reclamations SET {affectations} WHERE ticket_id = ?",
                   (*champs.values(), ticket_id))


def valider(ticket_id, decision, commentaire=None):
    """persiste l'avis de l'ingenieur sur une recommandation."""
    initialiser()
    with connexion() as cx:
        cx.execute(
            """UPDATE reclamations
               SET decision_ingenieur = ?,
                   commentaire_ingenieur = ?,
                   valide_le = ?
               WHERE ticket_id = ?""",
            (decision, commentaire, _maintenant(), ticket_id),
        )


def supprimer(ticket_id):
    """supprime definitivement un ticket de reclamation."""
    initialiser()
    with connexion() as cx:
        cx.execute("DELETE FROM reclamations WHERE ticket_id = ?", (ticket_id,))
