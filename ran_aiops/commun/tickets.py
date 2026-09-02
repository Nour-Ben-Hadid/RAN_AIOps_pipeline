"""Chargement des tickets enrichis de la prediction de categorie."""

import pandas as pd

from ran_aiops.chemins import PRED_LLM, TICKETS

SEUIL_CONFIANCE = 0.85   # en dessous, la categorie du LLM n'est pas jugee fiable


def charger_tickets(tickets=TICKETS, llm=PRED_LLM, seuil=SEUIL_CONFIANCE):
    """tickets + prediction LLM ; cat_eff = categorie du LLM si confiant, INDETERMINE sinon"""
    df = pd.read_csv(tickets).merge(
        pd.read_csv(llm)[["ticket_id", "pred_llm", "confiance"]], on="ticket_id", how="left")
    df["cat_eff"] = df["pred_llm"].where(df["confiance"] >= seuil, "INDETERMINE")
    return df
