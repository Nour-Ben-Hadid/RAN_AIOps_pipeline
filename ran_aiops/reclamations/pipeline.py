"""Point d'entree unitaire : une plainte en argument -> node, secteurs et KPI en cause.

Usage : python -m ran_aiops.reclamations.pipeline --texte "..." --date ... --gouvernorat ...
"""

import argparse
import sys

import pandas as pd

from ran_aiops.commun.env import cle_api
from ran_aiops.commun.gemini import MODELE, appeler_gemini
from ran_aiops.commun.tickets import SEUIL_CONFIANCE
from ran_aiops.reclamations.classification_llm import construire_prompt, extraire_json
from ran_aiops.reclamations.jointure import (CHAMPS_LIEU, K_NODES, RAYON_KM,
                                             charger_anomalies, localiser_detail)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--texte", required=True, help="texte de la plainte")
    ap.add_argument("--date", required=True, help="date de la panne (JJ/MM/AAAA ou AAAA-MM-JJ)")
    ap.add_argument("--gouvernorat", required=True, help="seul champ obligatoire")
    ap.add_argument("--delegation", default=None)
    ap.add_argument("--localite", default=None)
    ap.add_argument("--adresse-libre", default=None, help="rue ou repere, optionnel")
    ap.add_argument("--code-postal", default=None, help="optionnel, 4 chiffres")
    ap.add_argument("--fenetre", type=int, default=0)
    ap.add_argument("--rayon", type=float, default=RAYON_KM,
                    help="rayon maximum de recherche en km")
    ap.add_argument("--k", type=int, default=K_NODES,
                    help="nombre de sites candidats retenus (0 = rayon fixe)")
    args = ap.parse_args()

    cle = cle_api()
    try:
        date = pd.to_datetime(args.date, dayfirst=True).strftime("%Y-%m-%d")
    except ValueError:
        sys.exit(f"Date illisible : {args.date} (attendu JJ/MM/AAAA ou AAAA-MM-JJ)")

    # 1. classification du texte par le LLM
    brut = appeler_gemini(construire_prompt(args.texte), cle, MODELE)
    cat, conf = extraire_json(brut)
    conf = conf if conf is not None else 0.0

    lieu = {c: getattr(args, c) for c in CHAMPS_LIEU}
    print(f"Plainte : \"{args.texte}\"")
    print(f"Date : {date} | Lieu : " + ", ".join(v for v in lieu.values() if v))
    print("-" * 60)
    print(f"Categorie (LLM) : {cat}  (confiance {conf:.2f})")

    if cat == "HORS_RESEAU":
        # inutile de geocoder : la demande ne concerne pas le reseau
        print("-> Demande hors reseau (facturation / SIM / forfait). Aucun site a verifier.")
        return

    # 2. localisation puis jointure avec les anomalies KPI
    cat_eff = cat if conf >= SEUIL_CONFIANCE else "INDETERMINE"
    ticket = {"cat_eff": cat_eff, "date": date, **lieu}
    node, secteurs, kpis, dist, niveau = localiser_detail(
        ticket, charger_anomalies(), args.fenetre, args.rayon, args.k)
    print(f"Precision de la localisation : {niveau}")

    print("-" * 60)
    if node is None:
        print("Aucune anomalie reseau trouvee autour de ce lieu a cette date.")
        print("(probleme peut-etre cote client, ou anomalie non detectee)")
    else:
        proximite = "region" if dist is None else f"a {dist:.2f} km du client"
        print("PROBLEME A VERIFIER")
        print(f"  Site      : {node}  ({proximite})")
        print(f"  Secteurs  : {', '.join(secteurs)}")
        print(f"  KPI       : {', '.join(kpis)}")


if __name__ == "__main__":
    main()
