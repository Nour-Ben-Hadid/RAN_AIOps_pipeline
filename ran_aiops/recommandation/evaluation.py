"""Evaluation A/B (avec vs sans fiches) notee par un LLM-juge, sur grille figee.

Usage : python -m ran_aiops.recommandation.evaluation --n 30
"""

import argparse
import json
import re

import pandas as pd

from ran_aiops.chemins import EVALUATION, JOINTURE, TICKETS, prevoir
from ran_aiops.commun.gemini import MODELE, appeler_cache
from ran_aiops.recommandation.generation import charger_lot, contexte_ticket, generer
from ran_aiops.recommandation.selection import recuperer

CRITERES = {
    "contextualisation_ticket": "la recommandation cite et exploite correctement le node, les "
                                "secteurs, les KPI, la plainte et la date fournis",
    "utilite_triage_ran": "la recommandation aide un ingenieur radio a prioriser les premieres "
                          "verifications OSS/NMS ou terrain",
    "prudence_diagnostic": "la recommandation distingue clairement anomalie constatee, cause "
                           "probable et hypotheses a verifier",
    "coherence_pipeline": "la recommandation ne contredit pas les sorties du pipeline : node, "
                          "secteurs, KPI, categorie, date et role d'aide au pre-diagnostic",
}

MODELE_JUGE = "gemini-3.6-flash"
NOTE_MAX = 10
PAUSE_JUGE = 20.0

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
Note chaque critere de 1 (tres mauvais) a 10 (excellent).

Criteres :
{criteres}

Echelle :
- 10 = excellent, precis, complet, directement exploitable, aucune faiblesse visible.
- 8 = bon, exploitable, mais perfectible.
- 6 = acceptable, mais trop generique ou incomplet.
- 4 = faible, peu operationnel ou partiellement hors sujet.
- 1 = tres mauvais, non exploitable ou hallucine.
N'utilise pas automatiquement 10 : reserve-le aux reponses vraiment superieures.

Reponds UNIQUEMENT par un objet JSON, sans texte autour, sans bloc de code :
{{{notes}, "justification": "une phrase"}}

DIAGNOSTIC CALCULE :
{contexte}

FICHES DE REFERENCE ATTENDUES :
{fiches}

RECOMMANDATION A NOTER :
{reco}
"""


def juger(ticket, reco, fiches, modele=MODELE_JUGE):
    """notes du juge sur la grille figee, ou None"""
    prompt = PROMPT_JUGE.format(
        criteres="\n".join(f"- {k} : {v}" for k, v in CRITERES.items()),
        notes=", ".join(f'"{k}": <1-{NOTE_MAX}>' for k in CRITERES),
        contexte=contexte_ticket(ticket),
        fiches="\n\n---\n\n".join(t for _, t in fiches),
        reco=json.dumps(reco, ensure_ascii=False, indent=2))
    return _valider_notes(appeler_cache(prompt, modele, 0.0, pause=PAUSE_JUGE))


def _valider_notes(brut):
    """les notes de la grille, dans [1, NOTE_MAX], sinon None"""
    m = re.search(r"\{.*\}", brut or "", re.DOTALL)
    try:
        d = json.loads(m.group(0)) if m else None
    except json.JSONDecodeError:
        return None
    if not d or not all(isinstance(d.get(c), (int, float)) and 1 <= d[c] <= NOTE_MAX
                        for c in CRITERES):
        return None
    return d


def evaluer(ticket):
    """[(bras, reco, notes, erreur)] pour les deux bras"""
    fiches = recuperer(ticket.get("kpis"))
    sorties = []
    for bras, source_fiches, gabarit in [
        ("avec_rag", fiches, None),
        ("sans_rag", [], PROMPT_SANS_RAG),
    ]:
        try:
            reco = generer(ticket, source_fiches, gabarit=gabarit) if gabarit else generer(
                ticket, source_fiches
            )
            notes = juger(ticket, reco, fiches) if reco else None
            sorties.append((bras, reco, notes, None))
        except Exception as e:
            sorties.append((bras, None, None, f"{type(e).__name__}: {e}"))
    return sorties, fiches


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jointure", default=JOINTURE)
    ap.add_argument("--tickets", default=TICKETS)
    ap.add_argument("--n", type=int, default=30, help="taille de l'echantillon")
    ap.add_argument("--ticket-id", help="evaluer un seul ticket correle")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=EVALUATION)
    args = ap.parse_args()

    print("PROTOCOLE (fige avant generation)")
    if args.ticket_id:
        print(f"  echantillon : ticket correle {args.ticket_id}")
    else:
        print(f"  echantillon : {args.n} tickets correles, seed {args.seed}")
    print("  bras        : avec_rag (fiches selectionnees par cle) vs sans_rag (sans fiches)")
    print(f"  generation  : {MODELE}, temperature 0.2")
    print(f"  juge        : {MODELE_JUGE}, temperature 0, notes 1-{NOTE_MAX}, pause {PAUSE_JUGE:.0f}s")
    for c, d in CRITERES.items():
        print(f"    {c:24} {d}")

    lot = charger_lot(args.jointure, args.tickets)
    if args.ticket_id:
        lot = lot[lot["ticket_id"].astype(str) == str(args.ticket_id)]
        if lot.empty:
            raise ValueError(f"ticket correle introuvable : {args.ticket_id}")
    else:
        lot = lot.sample(args.n, random_state=args.seed)
    lignes = []
    for t in lot.to_dict("records"):
        sorties, fiches = evaluer(t)
        for bras, reco, notes, erreur in sorties:
            lignes.append({"ticket_id": t["ticket_id"], "node": t["node_retenu"],
                           "kpis": t["kpis"], "bras": bras,
                           "fiches": "; ".join(f for f, _ in fiches) if bras == "avec_rag" else "",
                           "diagnostic": reco and reco["diagnostic"],
                           "cause_probable": reco and reco["cause_probable"],
                           "actions": "; ".join(reco["actions"]) if reco else None,
                           **(notes or {c: None for c in CRITERES}),
                           "justification": (notes or {}).get("justification"),
                           "note_experte": "",
                           "erreur": erreur or ""})
        print(f"  ticket {t['ticket_id']} evalue")
        pd.DataFrame(lignes).to_csv(prevoir(args.out), index=False, encoding="utf-8")

    res = pd.DataFrame(lignes)
    res.to_csv(prevoir(args.out), index=False, encoding="utf-8")

    print("\nSCORES MOYENS PAR BRAS")
    colonnes = list(CRITERES)
    notes_valides = res.dropna(subset=colonnes)
    recap = notes_valides.groupby("bras")[colonnes].mean().round(2)
    recap["moyenne"] = recap.mean(axis=1).round(2)
    recap["n_notes"] = notes_valides.groupby("bras").size()
    print(recap.to_string())

    manquants = res[colonnes].isna().any(axis=1).sum()
    if manquants:
        print(f"\n[!] {manquants} lignes non notees (reponse LLM invalide ou erreur API)")
    print(f"\nDetail par ticket -> {args.out}  (colonne note_experte a remplir a la main)")


if __name__ == "__main__":
    main()
