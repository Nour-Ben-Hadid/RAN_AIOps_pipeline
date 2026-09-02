"""Designation des fiches par cle exacte : aucun modele, aucun reseau, aucune approximation."""

import re
from functools import cache

from ran_aiops.chemins import BASE_CONNAISSANCE
from ran_aiops.commun.kpi import CATEGORIE_PAR_KPI, noms_kpi


def lire(chemin):
    return chemin.read_text(encoding="utf-8")


@cache
def fiche_par_kpi(dossier=BASE_CONNAISSANCE):
    """{nom exact du KPI: chemin}, lu sur la 1re ligne '# KPI : ...' de chaque fiche"""
    index = {}
    for chemin in sorted(dossier.glob("kpi_*.md")):
        with open(chemin, encoding="utf-8") as f:
            m = re.match(r"#\s*KPI\s*:\s*(.+)", f.readline().strip())
        if m:
            index[m.group(1).strip()] = chemin
    return index


def recuperer(kpis, dossier=BASE_CONNAISSANCE):
    """[(fichier, texte)] : fiche de chaque KPI degrade, puis de chaque famille concernee.

    KeyError si un KPI n'a pas de fiche : un arret net vaut mieux qu'un prompt ampute.
    """
    index = fiche_par_kpi(dossier)
    noms = noms_kpi(kpis)
    if inconnus := [n for n in noms if n not in index]:
        raise KeyError(f"aucune fiche pour : {', '.join(inconnus)} (dossier {dossier})")

    # dict.fromkeys : dedoublonne les familles en conservant l'ordre des KPI
    familles = dict.fromkeys(filter(None, (CATEGORIE_PAR_KPI.get(n) for n in noms)))
    chemins = [index[n] for n in noms] + [dossier / f"famille_{f}.md" for f in familles]
    return [(c.name, lire(c)) for c in chemins]
