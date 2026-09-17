"""Chaine complete pour une reclamation : classification, localisation, recommandation.

Usage : python -m ran_aiops.reclamations.traitement --texte "..." --gouvernorat Monastir
        python -m ran_aiops.reclamations.traitement --texte "..." --traiter
        python -m ran_aiops.reclamations.traitement --en-attente
"""

import argparse

from ran_aiops.commun import base
from ran_aiops.commun.gemini import appeler_cache
from ran_aiops.commun.tickets import SEUIL_CONFIANCE
from ran_aiops.reclamations.classification_llm import construire_prompt, extraire_json
from ran_aiops.reclamations.jointure import charger_anomalies, localiser_detail
from ran_aiops.recommandation.generation import recommander


def traiter(ticket):
    """{colonnes de sortie} pour un ticket ; s'arrete des qu'une etape ne donne rien"""
    brut = appeler_cache(construire_prompt(ticket["texte_plainte"]))
    categorie, confiance = extraire_json(brut)
    sortie = {"categorie": categorie, "confiance": confiance or 0.0}
    if categorie in (None, "HORS_RESEAU"):
        return sortie

    cat_eff = categorie if sortie["confiance"] >= SEUIL_CONFIANCE else "INDETERMINE"
    node, secteurs, kpis, distance, niveau = localiser_detail(
        {**ticket, "cat_eff": cat_eff}, charger_anomalies())
    sortie |= {"node_retenu": node, "precision_loc": niveau, "distance_km": distance,
               "secteurs": "; ".join(secteurs or []), "kpis": "; ".join(kpis or [])}
    if node is None:
        return sortie

    reco, fiches = recommander({**ticket, "categorie": categorie, "node_retenu": node,
                                "kpis": sortie["kpis"],
                                "secteurs_a_inspecter": sortie["secteurs"]})
    sortie["fiches"] = "; ".join(f for f, _ in fiches)
    if reco:
        sortie |= {**reco, "actions": "; ".join(reco["actions"])}
    return sortie


def traiter_ticket(ticket_id):
    ticket = base.lire(ticket_id)
    base.maj(ticket_id, "en_cours")
    try:
        sortie = traiter(ticket)
    except Exception as e:
        base.maj(ticket_id, "echec", erreur=f"{type(e).__name__}: {e}")
        raise
    base.maj(ticket_id, "traite", **sortie)
    return sortie


def traiter_en_attente(limite=None):
    for ticket in base.en_attente(limite):
        try:
            traiter_ticket(ticket["ticket_id"])
            print(f"  {ticket['ticket_id']} traite")
        except Exception as e:
            print(f"  {ticket['ticket_id']} echec : {e}")


def afficher(ticket_id):
    t = base.lire(ticket_id)
    print(f"\nticket {t['ticket_id']} | {t['statut']}")
    print(f"  plainte    : {t['texte_plainte']}")
    print(f"  categorie  : {t['categorie']} ({t['confiance']})")
    if t["node_retenu"]:
        print(f"  site       : {t['node_retenu']} ({t['precision_loc']})")
        print(f"  secteurs   : {t['secteurs']}")
        print(f"  KPI        : {t['kpis']}")
    if t["diagnostic"]:
        print(f"  diagnostic : {t['diagnostic']}")
        print(f"  cause      : {t['cause_probable']}")
        for a in t["actions"].split("; "):
            print(f"  action     : {a}")
    if t["erreur"]:
        print(f"  erreur     : {t['erreur']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--texte", help="plainte a enregistrer dans SQLite")
    ap.add_argument("--date")
    ap.add_argument("--gouvernorat")
    ap.add_argument("--delegation")
    ap.add_argument("--localite")
    ap.add_argument("--adresse-libre", dest="adresse_libre")
    ap.add_argument("--code-postal", dest="code_postal")
    ap.add_argument("--traiter", action="store_true",
                    help="apres creation, lancer classification, localisation et recommandation")
    ap.add_argument("--enregistrer-seulement", action="store_true",
                    help=argparse.SUPPRESS)
    ap.add_argument("--en-attente", action="store_true", help="traiter les tickets recus")
    ap.add_argument("--n", type=int, default=None, help="limite pour --en-attente")
    args = ap.parse_args()

    if args.texte:
        if args.traiter and args.enregistrer_seulement:
            ap.error("--traiter et --enregistrer-seulement sont incompatibles")
        ticket_id = base.enregistrer(
            args.texte, args.date, gouvernorat=args.gouvernorat, delegation=args.delegation,
            localite=args.localite, adresse_libre=args.adresse_libre,
            code_postal=args.code_postal)
        if not args.traiter:
            print(f"ticket {ticket_id} enregistre (statut recu)")
            return
        traiter_ticket(ticket_id)
        afficher(ticket_id)
    elif args.en_attente:
        traiter_en_attente(args.n)
    else:
        ap.error("donner --texte ou --en-attente")


if __name__ == "__main__":
    main()
