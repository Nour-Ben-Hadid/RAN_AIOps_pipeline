import argparse
import sys

import pandas as pd

from classification_llm_api import construire_prompt, appeler_gemini, extraire_json, MODELE
from commun import cle_api, SEUIL_CONFIANCE
from geocode_adresse import geocoder_adresse
from jointure_anomalies import (charger_anomalies, localiser_detail,
                                K_NODES, RAYON_KM)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--texte", required=True, help="texte de la plainte")
    ap.add_argument("--date", required=True, help="date de la panne (JJ/MM/AAAA ou AAAA-MM-JJ)")
    ap.add_argument("--adresse", required=True, help="adresse complete du client")
    ap.add_argument("--code-postal", default=None,
                    help="optionnel, 4 chiffres : leve les homonymes de rue (tres recommande)")
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

    print(f"Plainte : \"{args.texte}\"")
    print(f"Date : {date} | Adresse : {args.adresse}"
          + (f" ({args.code_postal})" if args.code_postal else ""))
    print("-" * 60)
    print(f"Categorie (LLM) : {cat}  (confiance {conf:.2f})")

    if cat == "HORS_RESEAU":
        # inutile de geocoder : la demande ne concerne pas le reseau
        print("-> Demande hors reseau (facturation / SIM / forfait). Aucun site a verifier.")
        return

    # 2. adresse -> position du client
    pos = geocoder_adresse(args.adresse, args.code_postal)
    if pos is None:
        print("-" * 60)
        print(f"Adresse introuvable : \"{args.adresse}\"")
        print("Precise la ville et, si possible, le code postal (--code-postal).")
        print("Exemple : --adresse \"Avenue Habib Bourguiba, Sousse\" --code-postal 4000")
        sys.exit(2)
    print(f"Position : {pos[0]:.5f}, {pos[1]:.5f}  ({args.k} sites candidats, max {args.rayon} km)")

    # 3. jointure avec les anomalies KPI
    cat_eff = cat if conf >= SEUIL_CONFIANCE else "INDETERMINE"
    # la jointure regeocode l'adresse, mais le cache est deja rempli par l'appel ci-dessus
    ticket = {"cat_eff": cat_eff, "adresse": args.adresse,
              "code_postal": args.code_postal, "date": date}
    node, secteurs, kpis, dist = localiser_detail(
        ticket, charger_anomalies(), args.fenetre, args.rayon, args.k)

    print("-" * 60)
    if node is None:
        print("Aucune anomalie reseau trouvee autour de cette adresse a cette date.")
        print("(probleme peut-etre cote client, ou anomalie non detectee)")
    else:
        print("PROBLEME A VERIFIER")
        print(f"  Site      : {node}  (a {dist:.2f} km du client)")
        print(f"  Secteurs  : {', '.join(secteurs)}")
        print(f"  KPI       : {', '.join(kpis)}")


if __name__ == "__main__":
    main()
