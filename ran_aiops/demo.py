"""Demo fixtures for public Docker runs.

The public repository does not ship private operator data. These helpers copy a
small anonymized dataset only when the expected local runtime files are absent.
"""

from __future__ import annotations

import csv
import os
import shutil
from pathlib import Path

from ran_aiops.chemins import (
    ANOMALIES_JOURNALIERES,
    BASE_RECLAMATIONS,
    CELLULES_CHRONIQUES,
    NODES_COORDS,
    RACINE,
)
from ran_aiops.commun import base

DEMO_ROOT = RACINE / "demo_data"


def _copy_if_missing(src: Path, dst: Path) -> None:
    if dst.exists() or not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


def _seed_tickets_if_empty() -> None:
    seed = DEMO_ROOT / "reclamations_seed.csv"
    if not seed.exists():
        return

    base.initialiser()
    with base.connexion() as cx:
        total = cx.execute("SELECT COUNT(*) FROM reclamations").fetchone()[0]
    if total:
        return

    with seed.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            base.enregistrer(
                row["texte_plainte"],
                row.get("date") or None,
                gouvernorat=row.get("gouvernorat") or None,
                delegation=row.get("delegation") or None,
                localite=row.get("localite") or None,
                adresse_libre=row.get("adresse_libre") or None,
                code_postal=row.get("code_postal") or None,
            )


def ensure_demo_data() -> None:
    """Populate sanitized demo files for a first public run.

    Set RAN_AIOPS_DEMO=0 to disable this behavior.
    """
    if os.getenv("RAN_AIOPS_DEMO", "1").lower() in {"0", "false", "no"}:
        return

    _copy_if_missing(DEMO_ROOT / "data" / "nodes_coordonnees.csv", NODES_COORDS)
    _copy_if_missing(
        DEMO_ROOT / "resultats" / "anomalies" / "anomalies_journalieres.csv",
        ANOMALIES_JOURNALIERES,
    )
    _copy_if_missing(
        DEMO_ROOT / "resultats" / "anomalies" / "cellules_chroniques.csv",
        CELLULES_CHRONIQUES,
    )
    if not BASE_RECLAMATIONS.exists():
        _seed_tickets_if_empty()
