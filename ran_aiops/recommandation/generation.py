"""Generation de la recommandation ancree sur les fiches designees (RAG).

Usage : python -m ran_aiops.recommandation.generation --n 10
"""

import argparse
import json
import re

import pandas as pd

from ran_aiops.chemins import JOINTURE, RECOMMANDATIONS, TICKETS, prevoir
from ran_aiops.commun.gemini import MODELE, appeler_cache
from ran_aiops.recommandation.selection import recuperer

TEMPERATURE = 0.2
CHAMPS = ["diagnostic", "cause_probable", "actions"]

PROMPT = """Tu es ingenieur radio. Redige une recommandation pour un technicien terrain, a partir
du diagnostic calcule ci-dessous et des fiches de reference fournies.

Regles :
- N'invente rien : chaque cause et chaque action doit etre supportee par les fiches ou par le
  diagnostic calcule.
- Personnalise la reponse : cite le node, les secteurs a inspecter et les KPI quand ils sont
  disponibles.
- Transforme les actions generiques des fiches en controles operationnels appliques au secteur ou
  au node concerne.
- Si une cause n'est pas prouvee par les donnees, formule-la comme une hypothese a verifier, pas
  comme une certitude.
- Si les fiches ne permettent pas de conclure, mets "information insuffisante" dans diagnostic
  et une liste actions vide.
- Ne remets pas en cause le node ni les KPI : ils viennent d'un calcul, pas d'une supposition.
- Reponds UNIQUEMENT par un objet JSON, sans texte autour, sans bloc de code.
- Format exact : {{"diagnostic": "...", "cause_probable": "...", "actions": ["...", "..."]}}
- Au plus 3 actions, de la plus prioritaire a la moins prioritaire. Chaque action doit viser le
  secteur ou le node si cette information est fournie.

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


def generer(ticket, fiches, modele=MODELE, gabarit=PROMPT):
    """recommandation JSON ancree sur les fiches ; None si la reponse est inexploitable"""
    prompt = gabarit.format(contexte=contexte_ticket(ticket),
                            fiches="\n\n---\n\n".join(t for _, t in fiches))
    return _valider(appeler_cache(prompt, modele, TEMPERATURE))


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
