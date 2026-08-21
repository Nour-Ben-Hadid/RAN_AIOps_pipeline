import os
import re
import sys

import pandas as pd

TICKETS = "resultats/tickets_synthetiques.csv"
PRED_LLM = "resultats/predictions_llm_api.csv"
SEUIL_CONFIANCE = 0.85   # en dessous, la categorie du LLM n'est pas jugee fiable

ENV = "../.env"


def charger_env(chemin=ENV):
    """charge .env dans os.environ ; une variable deja posee reste prioritaire"""
    if not os.path.exists(chemin):
        return
    with open(chemin, encoding="utf-8-sig") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#"):
                continue
            m = re.match(r"(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)", ligne)
            if m and m.group(1) not in os.environ:
                os.environ[m.group(1)] = m.group(2).strip().strip("\"'")


def cle_api():
    """GEMINI_API_KEY, depuis l'environnement ou le .env. Sort du programme si absente."""
    charger_env()
    cle = os.environ.get("GEMINI_API_KEY")
    if not cle:
        sys.exit("GEMINI_API_KEY introuvable : ni dans l'environnement, ni dans le .env "
                 "a la racine du projet. Ajoute une ligne GEMINI_API_KEY=ta_cle dans .env")
    return cle


def charger_tickets(tickets=TICKETS, llm=PRED_LLM, seuil=SEUIL_CONFIANCE):
    """tickets + prediction LLM ; cat_eff = categorie du LLM si confiant, INDETERMINE sinon"""
    df = pd.read_csv(tickets).merge(
        pd.read_csv(llm)[["ticket_id", "pred_llm", "confiance"]], on="ticket_id", how="left")
    df["cat_eff"] = df["pred_llm"].where(df["confiance"] >= seuil, "INDETERMINE")
    return df


def est_correct(pred, attendu):
    """un ticket ambigu est juste si la prediction est l'une des 2 categories admises"""
    return pred in str(attendu).split("|")
