"""Evaluation A/B (avec vs sans fiches) notee par un LLM-juge, sur grille figee.

Usage : python -m ran_aiops.recommandation.evaluation --n 8
"""

import argparse
import json
import re

import pandas as pd

from ran_aiops.chemins import EVALUATION, JOINTURE, TICKETS, prevoir
from ran_aiops.commun.gemini import MODELE
from ran_aiops.recommandation.generation import (appeler_cache, charger_lot,
                                                 contexte_ticket, generer)
from ran_aiops.recommandation.selection import recuperer

CRITERES = {
    "fidelite_kpi": "la recommandation traite bien les KPI en cause, sans en inventer d'autres",
    "actionnabilite": "les actions sont concretes et executables par un technicien terrain",
    "clarte": "le texte est net, sans jargon inutile ni remplissage",
    "absence_hallucination": "aucune affirmation inventee (seuil chiffre, alarme, equipement) "
                             "non deductible du diagnostic",
}

# meme tache et meme format, mais sans fiches : le bras de comparaison honnete.
PROMPT_SANS_RAG = """Tu es ingenieur radio. Redige une recommandation pour un technicien terrain,
a partir du diagnostic calcule ci-dessous et de tes connaissances en reseaux mobiles.

Regles :
- Ne remets pas en cause le node ni les KPI : ils viennent d'un calcul, pas d'une supposition.
- Reponds UNIQUEMENT par un objet JSON, sans texte autour, sans bloc de code.
- Format exact : {{"diagnostic": "...", "cause_probable": "...", "actions": ["...", "..."]}}
- Au plus 3 actions, de la plus prioritaire a la moins prioritaire.

DIAGNOSTIC CALCULE :
{contexte}
{fiches}"""

PROMPT_JUGE = """Tu evalues la recommandation d'un assistant a un technicien radio.
Note chaque critere de 1 (tres mauvais) a 5 (excellent).

Criteres :
{criteres}

Reponds UNIQUEMENT par un objet JSON, sans texte autour, sans bloc de code :
{{{notes}, "justification": "une phrase"}}

DIAGNOSTIC CALCULE :
{contexte}

RECOMMANDATION A NOTER :
{reco}
"""


def juger(ticket, reco, modele=MODELE):
    """notes du juge sur la grille figee, ou None"""
    prompt = PROMPT_JUGE.format(
        criteres="\n".join(f"- {k} : {v}" for k, v in CRITERES.items()),
        notes=", ".join(f'"{k}": <1-5>' for k in CRITERES),
        contexte=contexte_ticket(ticket),
        reco=json.dumps(reco, ensure_ascii=False, indent=2))
    return _valider_notes(appeler_cache(prompt, modele, 0.0))


def _valider_notes(brut):
    """les 4 notes de la grille, dans [1, 5], sinon None"""
    m = re.search(r"\{.*\}", brut or "", re.DOTALL)
    try:
        d = json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        return None
    if not d or not all(isinstance(d.get(c), (int, float)) and 1 <= d[c] <= 5 for c in CRITERES):
        return None
    return d


def evaluer(ticket):
    """[(bras, reco, notes)] pour les deux bras"""
    fiches = recuperer(ticket.get("kpis"))
    sorties = []
    for bras, reco in [("avec_rag", generer(ticket, fiches)),
                       ("sans_rag", generer(ticket, [], gabarit=PROMPT_SANS_RAG))]:
        sorties.append((bras, reco, juger(ticket, reco) if reco else None))
    return sorties, fiches


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jointure", default=JOINTURE)
    ap.add_argument("--tickets", default=TICKETS)
    ap.add_argument("--n", type=int, default=8, help="taille de l'echantillon")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=EVALUATION)
    args = ap.parse_args()

    print("PROTOCOLE (fige avant generation)")
    print(f"  echantillon : {args.n} tickets correles, seed {args.seed}")
    print("  bras        : avec_rag (fiches selectionnees par cle) vs sans_rag (sans fiches)")
    print(f"  juge        : {MODELE}, temperature 0, notes 1-5")
    for c, d in CRITERES.items():
        print(f"    {c:24} {d}")

    lot = charger_lot(args.jointure, args.tickets).sample(args.n, random_state=args.seed)
    lignes = []
    for t in lot.to_dict("records"):
        sorties, fiches = evaluer(t)
        for bras, reco, notes in sorties:
            lignes.append({"ticket_id": t["ticket_id"], "node": t["node_retenu"],
                           "kpis": t["kpis"], "bras": bras,
                           "fiches": "; ".join(f for f, _ in fiches) if bras == "avec_rag" else "",
                           "diagnostic": reco and reco["diagnostic"],
                           "cause_probable": reco and reco["cause_probable"],
                           "actions": "; ".join(reco["actions"]) if reco else None,
                           **(notes or {c: None for c in CRITERES}),
                           "justification": (notes or {}).get("justification"),
                           "note_experte": ""})
        print(f"  ticket {t['ticket_id']} evalue")

    res = pd.DataFrame(lignes)
    res.to_csv(prevoir(args.out), index=False, encoding="utf-8")

    print("\nSCORES MOYENS PAR BRAS")
    colonnes = list(CRITERES)
    recap = res.groupby("bras")[colonnes].mean().round(2)
    recap["moyenne"] = recap.mean(axis=1).round(2)
    recap["n"] = res.groupby("bras").size()
    print(recap.to_string())

    manquants = res[colonnes].isna().any(axis=1).sum()
    if manquants:
        print(f"\n[!] {manquants} recommandations non notees (reponse LLM invalide)")
    print(f"\nDetail par ticket -> {args.out}  (colonne note_experte a remplir a la main)")


if __name__ == "__main__":
    main()
