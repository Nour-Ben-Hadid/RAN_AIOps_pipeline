import os
import sys
import argparse
import pandas as pd
from classification_llm_api import construire_prompt, appeler_gemini, extraire_json, MODELE
from jointure_anomalies import charger_anomalies, localiser

SEUIL_CONFIANCE = 0.85  


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--texte", required=True, help="texte de la plainte")
    ap.add_argument("--date", required=True, help="date de la panne (JJ/MM/AAAA ou AAAA-MM-JJ)")
    ap.add_argument("--region", required=True)
    ap.add_argument("--zone", required=True)
    ap.add_argument("--fenetre", type=int, default=0)
    args = ap.parse_args()

    cle = os.environ.get("GEMINI_API_KEY")
    if not cle:
        sys.exit("Variable GEMINI_API_KEY absente. export GEMINI_API_KEY=...")

    try:
        date = pd.to_datetime(args.date, dayfirst=True).strftime("%Y-%m-%d")
    except ValueError:
        sys.exit(f"Date illisible : {args.date} (attendu JJ/MM/AAAA ou AAAA-MM-JJ)")

    # 1. classification du texte par le LLM
    brut = appeler_gemini(construire_prompt(args.texte), cle, MODELE)
    cat, conf = extraire_json(brut)
    conf = conf if conf is not None else 0.0

    print(f"Plainte : \"{args.texte}\"")
    print(f"Date : {date} | Region : {args.region} | Zone : {args.zone}")
    print("-" * 60)
    print(f"Categorie (LLM) : {cat}  (confiance {conf:.2f})")

    if cat == "HORS_RESEAU":
        print("-> Demande hors reseau (facturation / SIM / forfait). Aucun site a verifier.")
        return

    # 2. jointure avec les anomalies KPI
    cat_eff = cat if conf >= SEUIL_CONFIANCE else "INDETERMINE"
    ticket = {"cat_eff": cat_eff, "region": args.region, "zone": args.zone, "date": date}
    node, secteurs, kpis = localiser(ticket, charger_anomalies(), args.fenetre)

    print("-" * 60)
    if node is None:
        print("Aucune anomalie reseau trouvee pour cette zone/date.")
        print("(probleme peut-etre cote client, ou anomalie non detectee)")
    else:
        print(f"PROBLEME A VERIFIER")
        print(f"  Site      : {node}")
        print(f"  Secteurs  : {', '.join(secteurs)}")
        print(f"  KPI       : {', '.join(kpis)}")


if __name__ == "__main__":
    main()
