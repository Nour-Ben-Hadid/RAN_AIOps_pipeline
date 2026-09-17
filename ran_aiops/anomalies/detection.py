"""Detection d'anomalies KPI : une ligne = une cellule un jour.

Usage : python -m ran_aiops.anomalies.detection
"""

import argparse
import os

import numpy as np
import pandas as pd
from pyod.models.ecod import ECOD
from sklearn.preprocessing import StandardScaler

from ran_aiops.chemins import (ANOMALIES_JOURNALIERES, CELLULES_CHRONIQUES,
                               CELLULES_HISTORIQUE_COURT, KPI_TABLE, prevoir)

RANDOM_STATE = 42
CONTAMINATION = 0.03
MIN_JOURS = 20
SEUIL_CHRONIQUE = 0.5
MAX_KPI_MANQUANTS = 6
SEUIL_KPI = -np.log(0.05)


def charger(chemin=KPI_TABLE):
    """(df nettoye, colonnes KPI) : #DIV/0 en NaN, lignes trop lacunaires retirees"""
    df = pd.read_csv(chemin, skip_blank_lines=True, low_memory=False)
    df = df.dropna(how="all").reset_index(drop=True)
    kpi_cols = list(df.columns[5:])

    for c in kpi_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df[df[kpi_cols].isna().sum(axis=1) < MAX_KPI_MANQUANTS].reset_index(drop=True)

    df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y")
    return df, kpi_cols


def scores_z(df, kpi_cols, jours):
    """z robuste (mediane / MAD) par region, calcule sur les cellules a historique suffisant"""
    ref = df[df["EUtranCell Id"].isin(jours[jours >= MIN_JOURS].index)]
    z = pd.DataFrame(index=df.index)
    for c in kpi_cols:
        med = df["Region"].map(ref.groupby("Region")[c].median())
        mad = df["Region"].map(ref.groupby("Region")[c].apply(lambda s: (s - s.median()).abs().median()))
        z["z_" + c] = (df[c] - med) / (1.4826 * mad).replace(0, np.nan)
    return z.clip(-10, 10)


def detecter(df, z):
    """(cellules-jours scorees, contributions par KPI) -- ECOD, choisi pour sa stabilite"""
    colonnes = list(z.columns)
    X = StandardScaler().fit_transform(z[colonnes].fillna(0.0).values)
    ecod = ECOD(contamination=CONTAMINATION).fit(X)

    D = df[["EUtranCell Id", "Date", "Region"]].copy()
    D["score_anomalie"] = ecod.decision_scores_
    D["flag"] = D["score_anomalie"] >= np.quantile(D["score_anomalie"], 1 - CONTAMINATION)

    # ECOD score chaque dimension separement et O somme au score total : attribution exacte
    contributions = pd.DataFrame(np.asarray(ecod.O)[D["flag"].values],
                                 index=D.index[D["flag"]],
                                 columns=[c[2:] for c in colonnes])
    return D, contributions


def kpis_en_cause(contribution):
    retenus = contribution[contribution > SEUIL_KPI].sort_values(ascending=False)
    if retenus.empty:
        retenus = contribution.sort_values(ascending=False).head(1)
    return "; ".join(retenus.index)


def separer(D, contributions, jours):
    """(incidents ponctuels, cellules chroniques, cellules a historique court)"""
    g = D.groupby("EUtranCell Id")
    stat = pd.DataFrame({"region": g["Region"].first(), "n_days": jours, "n_flag": g["flag"].sum()})
    stat["taux_anormal"] = stat["n_flag"] / stat["n_days"]
    fiable = stat["n_days"] >= MIN_JOURS
    chronique = fiable & (stat["taux_anormal"] >= SEUIL_CHRONIQUE)

    incidents = D[D["flag"] & D["EUtranCell Id"].isin(stat.index[fiable & ~chronique])].copy()
    incidents["kpi_principal"] = contributions.idxmax(axis=1).reindex(incidents.index)
    incidents["kpis_en_cause"] = contributions.apply(kpis_en_cause, axis=1).reindex(incidents.index)

    chroniques = stat[chronique].copy()
    par_cellule = contributions.groupby(D.loc[contributions.index, "EUtranCell Id"].values).mean()
    chroniques["kpi_dominant"] = par_cellule.idxmax(axis=1).reindex(chroniques.index)
    chroniques["kpis_en_cause"] = par_cellule.apply(kpis_en_cause, axis=1).reindex(chroniques.index)

    return incidents, chroniques[["region", "n_days", "n_flag", "taux_anormal",
                                  "kpi_dominant", "kpis_en_cause"]], jours[jours < MIN_JOURS]


def ecrire(tableau, chemin, **kw):
    """ecriture atomique : un lecteur voit l'ancienne version ou la nouvelle, jamais l'entre-deux"""
    temporaire = chemin.with_suffix(chemin.suffix + ".tmp")
    tableau.to_csv(prevoir(temporaire), encoding="utf-8", **kw)
    os.replace(temporaire, chemin)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kpi", default=KPI_TABLE)
    args = ap.parse_args()

    df, kpi_cols = charger(args.kpi)
    jours = df.groupby("EUtranCell Id").size()
    D, contributions = detecter(df, scores_z(df, kpi_cols, jours))
    incidents, chroniques, historique_court = separer(D, contributions, jours)

    node_de = df.groupby("EUtranCell Id")["Node"].first()

    sortie = df.loc[incidents.index, ["Node", "EUtranCell Id", "Region", "Date"] + kpi_cols]
    sortie = sortie.join(incidents[["score_anomalie", "kpi_principal", "kpis_en_cause"]])
    ecrire(sortie.sort_values(["Date", "score_anomalie"], ascending=[True, False]),
           ANOMALIES_JOURNALIERES, index=False)

    chroniques.insert(0, "Node", node_de.reindex(chroniques.index))
    chroniques = chroniques.join(df.groupby("EUtranCell Id")[kpi_cols].mean().round(2))
    ecrire(chroniques.sort_values("taux_anormal", ascending=False), CELLULES_CHRONIQUES)

    court = historique_court.rename("n_days").to_frame()
    court.insert(0, "Node", node_de.reindex(court.index))
    court["n_jours_flagues"] = D.groupby("EUtranCell Id")["flag"].sum().reindex(court.index)
    ecrire(court, CELLULES_HISTORIQUE_COURT)

    print(f"periode {df['Date'].min().date()} -> {df['Date'].max().date()}")
    print(f"  incidents           : {len(sortie)} -> {ANOMALIES_JOURNALIERES}")
    print(f"  cellules chroniques : {len(chroniques)} -> {CELLULES_CHRONIQUES}")
    print(f"  historique court    : {len(court)} -> {CELLULES_HISTORIQUE_COURT}")


if __name__ == "__main__":
    main()
