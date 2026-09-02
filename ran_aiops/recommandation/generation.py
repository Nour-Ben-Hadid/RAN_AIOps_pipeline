"""Generation de la recommandation ancree sur les fiches designees (RAG).

Usage : python -m ran_aiops.recommandation.generation --n 10
"""

import argparse
import hashlib
import json
import os
import re
import time
from functools import cache

import pandas as pd
import requests

from ran_aiops.chemins import (CACHE_RECOMMANDATION, JOINTURE, RECOMMANDATIONS, TICKETS,
                               prevoir)
from ran_aiops.commun.env import cle_api
from ran_aiops.commun.gemini import MODELE, appeler_gemini
from ran_aiops.recommandation.selection import recuperer

TEMPERATURE = 0.2
CHAMPS = ["diagnostic", "cause_probable", "actions"]

PROMPT = """Tu es ingenieur radio. Redige une recommandation pour un technicien terrain, a partir
UNIQUEMENT du diagnostic calcule ci-dessous et des fiches de reference fournies.

Regles :
- N'invente rien : chaque cause et chaque action doit provenir des fiches.
- Si les fiches ne permettent pas de conclure, mets "information insuffisante" dans diagnostic
  et une liste actions vide.
- Ne remets pas en cause le node ni les KPI : ils viennent d'un calcul, pas d'une supposition.
- Reponds UNIQUEMENT par un objet JSON, sans texte autour, sans bloc de code.
- Format exact : {{"diagnostic": "...", "cause_probable": "...", "actions": ["...", "..."]}}
- Au plus 3 actions, de la plus prioritaire a la moins prioritaire.

DIAGNOSTIC CALCULE :
{contexte}

FICHES DE REFERENCE :
{fiches}
"""


def contexte_ticket(ticket):
    lignes = [("Node retenu", ticket.get("node_retenu")),
              ("Secteurs a inspecter", ticket.get("secteurs_a_inspecter")),
              ("KPI en cause", ticket.get("kpis")),
              ("Categorie de la plainte", ticket.get("categorie")),
              ("Date", ticket.get("date")),
              ("Plainte du client", ticket.get("texte_plainte"))]
    return "\n".join(f"- {k} : {v}" for k, v in lignes if pd.notna(v) and v)


@cache
def _cache():
    if os.path.exists(CACHE_RECOMMANDATION):
        with open(CACHE_RECOMMANDATION, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _sauver():
    with open(prevoir(CACHE_RECOMMANDATION), "w", encoding="utf-8") as f:
        json.dump(_cache(), f, ensure_ascii=False, indent=0)


def _valider(brut):
    """objet JSON avec les 3 champs attendus, ou None"""
    m = re.search(r"\{.*\}", brut or "", re.DOTALL)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None
    if not all(c in d for c in CHAMPS) or not isinstance(d["actions"], list):
        return None
    return {c: d[c] for c in CHAMPS}


def appeler_cache(prompt, modele=MODELE, temperature=TEMPERATURE, pause=6.5):
    """appel Gemini memoise par hash du prompt, avec backoff sur quota, incidents et coupures"""
    cle = hashlib.sha1(f"{modele}|{temperature}|{prompt}".encode()).hexdigest()
    cache = _cache()
    if cle in cache:
        return cache[cle]

    for tentative in range(4):
        try:
            cache[cle] = appeler_gemini(prompt, cle_api(), modele, temperature)
            _sauver()
            time.sleep(pause)
            return cache[cle]
        except (requests.HTTPError, requests.Timeout, requests.ConnectionError) as e:
            # timeout ou coupure reseau : pas de code HTTP, on retente aussi
            code = getattr(e.response, "status_code", None)
            if code is not None and code not in (429, 500, 502, 503):
                raise
            attente = pause * (2 ** tentative)
            print(f"  {code or type(e).__name__}, nouvelle tentative dans {attente:.0f}s")
            time.sleep(attente)
    raise SystemExit("appels Gemini en echec : relance plus tard, le cache conserve l'acquis")


def generer(ticket, fiches, modele=MODELE, gabarit=PROMPT):
    """recommandation JSON ancree sur les fiches ; None si la reponse est inexploitable"""
    prompt = gabarit.format(contexte=contexte_ticket(ticket),
                            fiches="\n\n---\n\n".join(t for _, t in fiches))
    return _valider(appeler_cache(prompt, modele))


def recommander(ticket):
    """(recommandation, fiches utilisees) pour un ticket deja correle"""
    fiches = recuperer(ticket.get("kpis"))
    return generer(ticket, fiches), fiches


def charger_lot(jointure=JOINTURE, tickets=TICKETS, n=None):
    """tickets correles, enrichis du texte de la plainte"""
    j = pd.read_csv(jointure)
    j = j[j["anomalie_trouvee"]]
    t = pd.read_csv(tickets)[["ticket_id", "texte_plainte"]]
    lot = j.merge(t, on="ticket_id", how="left")
    return lot.head(n) if n else lot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jointure", default=JOINTURE)
    ap.add_argument("--tickets", default=TICKETS)
    ap.add_argument("--n", type=int, default=3, help="nombre de tickets a traiter (0 = tous)")
    ap.add_argument("--out", default=RECOMMANDATIONS)
    args = ap.parse_args()

    lot = charger_lot(args.jointure, args.tickets, args.n)
    lignes = []
    for t in lot.to_dict("records"):
        reco, fiches = recommander(t)
        print(f"\n--- ticket {t['ticket_id']} | {t['node_retenu']} | {t['kpis']}")
        print("  fiches :", ", ".join(f for f, _ in fiches))
        if reco is None:
            print("  [!] reponse LLM invalide")
            continue
        print(f"  diagnostic : {reco['diagnostic']}")
        print(f"  cause      : {reco['cause_probable']}")
        for a in reco["actions"]:
            print(f"  action     : {a}")
        lignes.append({"ticket_id": t["ticket_id"], "node_retenu": t["node_retenu"],
                       "kpis": t["kpis"], "fiches": "; ".join(f for f, _ in fiches),
                       **reco, "actions": "; ".join(reco["actions"])})

    if lignes:
        pd.DataFrame(lignes).to_csv(prevoir(args.out), index=False, encoding="utf-8")
        print(f"\n{len(lignes)} recommandations -> {args.out}")


if __name__ == "__main__":
    main()
