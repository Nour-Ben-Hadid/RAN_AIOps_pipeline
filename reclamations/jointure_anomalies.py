"""Jointure ticket <-> anomalie KPI.

Pour chaque ticket (date, region, zone, categorie predite par le LLM), cherche
s'il existe une anomalie qui lui correspond :
  - meme region et meme zone (la zone est deduite du Node par node_to_zone)
  - date dans une fenetre (journalieres) ; les chroniques sont permanentes
  - famille KPI compatible avec la categorie (INDETERMINE = toutes ; HORS_RESEAU = aucune)

Usage :
    python jointure_anomalies.py
    python jointure_anomalies.py --fenetre 5
"""

import argparse
import pandas as pd
from commun import node_to_zone

AJ_PATH = "../anomalies/resultats_anomalies/anomalies_journalieres.csv"
CC_PATH = "../anomalies/resultats_anomalies/cellules_chroniques.csv"

# chaque KPI 3GPP appartient a une famille de panne (= une categorie du NLP)
CATEGORIE_PAR_KPI = {
    "Diff_Init_E-Rab_Establish_Succ_Rate (%)": "A_accessibilite",
    "Diff_E-RAB_Retainability (%)": "B_retenabilite",
    "SCG_Radio_Resource_Retainability_Act (%)": "B_retenabilite",
    "SCG_Radio_Resource_Retainability_origin_gNb_Act (%)": "B_retenabilite",
    "Diff_Cell_Mobility_Succ_Rate_LTE (%)": "C_mobilite",
    "EN_DC_intra_sgNB_PSCell_Change_succ_rate (%)": "C_mobilite",
    "EN_DC_inter_sgNB_PSCell_Change_succ_rate (%)": "C_mobilite",
    "EN_DC_SETUP_succ_RATE_gNB (%)": "D_debit_5g",
    "EN_DC_SETUP_succ_RATE_eNB (%)": "D_debit_5g",
}


def charger_anomalies():
    """journalieres + chroniques dans une seule table normalisee (avec zone et famille)"""
    # severite = force de l'anomalie (score_if pour les journalieres, taux_anormal pour
    # les chroniques) : sert a departager les cellules candidates d'un meme ticket
    aj = pd.read_csv(AJ_PATH)
    aj = aj.rename(columns={"EUtranCell Id": "cellule", "Region": "region", "Date": "date",
                            "kpi_principal": "kpi", "score_if": "severite"})
    aj = aj[["Node", "cellule", "region", "date", "kpi", "severite", "kpis_en_cause"]]

    cc = pd.read_csv(CC_PATH)
    cc = cc.rename(columns={"EUtranCell Id": "cellule", "kpi_dominant": "kpi",
                            "taux_anormal": "severite"})
    cc = cc[["Node", "cellule", "region", "kpi", "severite", "kpis_en_cause"]]
    cc["date"] = pd.NaT  # une cellule chronique est degradee en permanence

    anom = pd.concat([aj, cc], ignore_index=True)
    anom["date"] = pd.to_datetime(anom["date"])
    anom["zone"] = anom["Node"].apply(node_to_zone)
    # familles KPI de l'anomalie : deduites de TOUS les kpis_en_cause, pas juste le principal
    anom["familles"] = anom["kpis_en_cause"].apply(
        lambda s: {CATEGORIE_PAR_KPI.get(k.strip()) for k in str(s).split(";")} - {None})
    return anom


def matcher(ticket, anom, fenetre):
    """anomalies compatibles avec un ticket (region + zone + date + famille)"""
    cat = ticket["cat_eff"]
    if cat == "HORS_RESEAU":
        return anom.iloc[0:0]  # pas un probleme reseau -> aucune jointure

    m = anom[(anom["region"] == ticket["region"]) & (anom["zone"] == ticket["zone"])]
    # chroniques (date NaT) toujours valides ; journalieres dans la fenetre autour du ticket
    d = pd.to_datetime(ticket["date"])
    m = m[m["date"].isna() | ((m["date"] - d).abs().dt.days <= fenetre)]
    # INDETERMINE : on accepte toutes les familles ; sinon la categorie doit etre
    # parmi les familles KPI en cause de l'anomalie
    if cat != "INDETERMINE":
        m = m[m["familles"].apply(lambda fs: cat in fs)]
    return m


def localiser(ticket, anom, fenetre=0):
    """site retenu (anomalie la plus forte) + ses secteurs a inspecter + kpis, pour un ticket
    (dict/Series avec region, zone, date, cat_eff). (None, [], []) si rien ne matche."""
    m = matcher(ticket, anom, fenetre)
    if not len(m):
        return None, [], []
    node = m.loc[m["severite"].idxmax(), "Node"]
    sous = m[m["Node"] == node]
    return node, sorted(sous["cellule"].dropna().unique()), sorted(sous["kpi"].unique())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickets", default="resultats/tickets_synthetiques.csv")
    ap.add_argument("--llm", default="resultats/predictions_llm_api.csv")
    # 0 = date exacte : le client donne la vraie date de la panne. Rappel maximal
    # et zero faux positif. Augmenter si les dates clients sont approximatives.
    ap.add_argument("--fenetre", type=int, default=0, help="tolerance en jours (journalieres)")
    # sous ce seuil de confiance, traiter la prediction comme INDETERMINE (accepte
    # toutes les familles) : rattrape les plaintes ambigues. 0 = desactive.
    # 0.85 recupere les cas ambigus (83.6 -> 90.9% bon site) sans faux positif ici.
    ap.add_argument("--seuil-confiance", type=float, default=0.85)
    ap.add_argument("--out", default="resultats/jointure_anomalies.csv")
    args = ap.parse_args()

    tickets = pd.read_csv(args.tickets)
    pred = pd.read_csv(args.llm)[["ticket_id", "pred_llm", "confiance"]]
    tickets = tickets.merge(pred, on="ticket_id", how="left")
    # categorie effective utilisee pour le filtre famille (INDETERMINE si peu confiant)
    tickets["cat_eff"] = tickets["pred_llm"].where(
        tickets["confiance"] >= args.seuil_confiance, "INDETERMINE")
    anom = charger_anomalies()

    lignes = []
    for _, t in tickets.iterrows():
        node, secteurs, kpis = localiser(t, anom, args.fenetre)
        vn, vc = t.get("vrai_node"), t.get("vraie_cellule")
        lignes.append({
            "ticket_id": t["ticket_id"], "date": t["date"], "region": t["region"],
            "zone": t["zone"], "categorie": t["pred_llm"],
            "anomalie_trouvee": node is not None,
            "node_retenu": node,
            "secteurs_a_inspecter": "; ".join(secteurs),
            "kpis": "; ".join(kpis),
            # verite cachee (evaluation seulement)
            "vrai_node": vn,
            "bon_site": pd.notna(vn) and node == vn,                 # le site retenu est le bon
            "vraie_cellule": vc,
            "secteur_couvert": pd.notna(vc) and vc in secteurs,      # le vrai secteur est dans la liste
        })

    res = pd.DataFrame(lignes)
    res["difficulte"] = tickets["difficulte"].values
    res.to_csv(args.out, index=False)

    print(f"{len(res)} tickets traites | anomalie trouvee : {res['anomalie_trouvee'].sum()}\n")

    # est_positif : le ticket pointe vraiment vers une anomalie detectee -> on doit la retrouver
    vrais = res[tickets["est_positif"].values]
    nb_sect = vrais.loc[vrais["anomalie_trouvee"], "secteurs_a_inspecter"].str.count(";").add(1)
    print(f"Tickets a anomalie reelle : {len(vrais)}")
    print(f"  bon site (node retenu)      : {vrais['bon_site'].sum()} ({vrais['bon_site'].mean():.1%})")
    print(f"  vrai secteur dans la liste  : {vrais['secteur_couvert'].sum()} ({vrais['secteur_couvert'].mean():.1%})")
    print(f"  secteurs a inspecter / site : {nb_sect.mean():.1f} en moyenne")
    tab = vrais.groupby("difficulte")[["bon_site", "secteur_couvert"]].mean().round(3)
    tab["n"] = vrais.groupby("difficulte").size()
    print(tab.to_string())

    # negatifs : aucune anomalie ne devrait etre trouvee (faux positifs a minimiser)
    negs = res[~tickets["est_positif"].values]
    print(f"\nTickets sans anomalie reelle : {len(negs)}")
    print(f"  faux positifs (anomalie trouvee a tort) : {negs['anomalie_trouvee'].sum()} "
          f"({negs['anomalie_trouvee'].mean():.1%})")

    print(f"\nDetail par ticket -> {args.out}")


if __name__ == "__main__":
    main()
