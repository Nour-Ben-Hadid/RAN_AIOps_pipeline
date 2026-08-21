import argparse
from functools import cache

import numpy as np
import pandas as pd

from commun import charger_tickets, PRED_LLM, SEUIL_CONFIANCE, TICKETS
from geocode_adresse import geocoder_adresse

AJ_PATH = "../anomalies/resultats_anomalies/anomalies_journalieres.csv"
CC_PATH = "../anomalies/resultats_anomalies/cellules_chroniques.csv"
COORDS_PATH = "../data/nodes_coordonnees.csv"

K_NODES = 7
RAYON_KM = 8.0   

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

def haversine(lat1, lon1, lat2, lon2):
    """distance en km ; accepte des scalaires ou des tableaux numpy"""
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp = np.radians(np.asarray(lat2, dtype=float) - np.asarray(lat1, dtype=float))
    dl = np.radians(np.asarray(lon2, dtype=float) - np.asarray(lon1, dtype=float))
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


@cache
def charger_coords():
    return pd.read_csv(COORDS_PATH)


def nodes_dans_rayon(lat, lon, rayon, k=K_NODES):    
    c = charger_coords()
    d = haversine(lat, lon, c["Latitude"].to_numpy(), c["Longitude"].to_numpy())
    ordre = np.argsort(d)
    if k:
        ordre = ordre[:k]
    ordre = ordre[d[ordre] <= rayon]
    return dict(zip(c["Node"].to_numpy()[ordre], d[ordre]))


def position_ticket(ticket):    
    adresse = ticket.get("adresse")
    if adresse is None or pd.isna(adresse):
        return None
    return geocoder_adresse(adresse, ticket.get("code_postal"))


def charger_anomalies():
    aj = pd.read_csv(AJ_PATH)    
    aj = aj.rename(columns={"EUtranCell Id": "cellule", "Region": "region", "Date": "date",
                            "kpi_principal": "kpi", "score_anomalie": "severite",
                            "score_if": "severite"})
    aj = aj[["Node", "cellule", "region", "date", "kpi", "severite", "kpis_en_cause"]]

    cc = pd.read_csv(CC_PATH)
    cc = cc.rename(columns={"EUtranCell Id": "cellule", "kpi_dominant": "kpi",
                            "taux_anormal": "severite"})
    cc = cc[["Node", "cellule", "region", "kpi", "severite", "kpis_en_cause"]]
    cc["date"] = pd.NaT  # une cellule chronique est degradee en permanence

    anom = pd.concat([aj, cc], ignore_index=True)
    anom["date"] = pd.to_datetime(anom["date"])

    co = charger_coords().set_index("Node")[["Latitude", "Longitude"]]
    anom = anom.join(co, on="Node")
    sans_coord = anom["Latitude"].isna().sum()
    if sans_coord:
        print(f"[!] {sans_coord} anomalies sans coordonnee de Node (ignorees par la distance)")

    # familles KPI de l'anomalie : deduites de TOUS les kpis_en_cause, pas juste le principal
    anom["familles"] = anom["kpis_en_cause"].apply(
        lambda s: {CATEGORIE_PAR_KPI.get(k.strip()) for k in str(s).split(";")} - {None})
    
    anom["fam_principale"] = anom["kpi"].map(CATEGORIE_PAR_KPI)    
    anom["chronique"] = anom["date"].isna()
    anom["sev_norm"] = anom.groupby("chronique")["severite"].rank(pct=True)
    return anom


def matcher(ticket, anom, fenetre=0, rayon=RAYON_KM, k=K_NODES):
    cat = ticket["cat_eff"]
    if cat == "HORS_RESEAU":
        return anom.iloc[0:0], {}  # pas un probleme reseau -> aucune jointure

    pos = position_ticket(ticket)
    if pos is None:
        return anom.iloc[0:0], {}  

    dist = nodes_dans_rayon(pos[0], pos[1], rayon, k)
    m = anom[anom["Node"].isin(dist)]
    # chroniques (date NaT) toujours valides / journalieres dans la fenetre autour du ticket
    d = pd.to_datetime(ticket["date"])
    m = m[m["date"].isna() | ((m["date"] - d).abs().dt.days <= fenetre)]
    # INDETERMINE : on accepte toutes les familles 
    if cat != "INDETERMINE":        
        m = m[m["familles"].apply(lambda fs: cat in fs).astype(bool)]
    return m, dist


def localiser_detail(ticket, anom, fenetre=0, rayon=RAYON_KM, k=K_NODES):
    """(node, secteurs, kpis, distance_km) ; (None, [], [], None) si rien ne matche"""
    m, dist = matcher(ticket, anom, fenetre, rayon, k)
    if not len(m):
        return None, [], [], None

    choix = m[~m["chronique"]] if (~m["chronique"]).any() else m
    cat = ticket["cat_eff"]
    choix = choix.assign(_dist=choix["Node"].map(dist),
                         _principal=choix["fam_principale"].eq(cat))
    node = choix.sort_values(["_principal", "sev_norm", "_dist"],
                             ascending=[False, False, True]).iloc[0]["Node"]
    
    sous = m[m["Node"] == node]
    return (node,
            sorted(sous["cellule"].dropna().unique()),
            sorted(sous["kpi"].unique()),
            round(float(dist[node]), 3))


def localiser(ticket, anom, fenetre=0, rayon=RAYON_KM, k=K_NODES):
    node, secteurs, kpis, _ = localiser_detail(ticket, anom, fenetre, rayon, k)
    return node, secteurs, kpis


def main():
    global COORDS_PATH          
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickets", default=TICKETS)
    ap.add_argument("--llm", default=PRED_LLM)
    ap.add_argument("--fenetre", type=int, default=0, help="tolerance en jours (journalieres)")
    ap.add_argument("--rayon", type=float, default=RAYON_KM,
                    help="rayon de recherche en km (rayon max si --k est utilise)")
    ap.add_argument("--k", type=int, default=K_NODES,
                    help="0 = rayon fixe ; k>0 = les k nodes les plus proches (adaptatif)")
    ap.add_argument("--coords", default=COORDS_PATH)
    ap.add_argument("--seuil-confiance", type=float, default=SEUIL_CONFIANCE)
    ap.add_argument("--out", default="resultats/jointure_anomalies.csv")
    args = ap.parse_args()

    COORDS_PATH = args.coords
    tickets = charger_tickets(args.tickets, args.llm, args.seuil_confiance)
    anom = charger_anomalies()

    lignes = []
    for _, t in tickets.iterrows():
        node, secteurs, kpis, dist = localiser_detail(t, anom, args.fenetre, args.rayon, args.k)
        vn, vc = t.get("vrai_node"), t.get("vraie_cellule")
        lignes.append({
            "ticket_id": t["ticket_id"], "date": t["date"],
            "adresse": t.get("adresse"), "distance_km": dist,
            "categorie": t["pred_llm"],
            "anomalie_trouvee": node is not None,
            "node_retenu": node,
            "secteurs_a_inspecter": "; ".join(secteurs),
            "kpis": "; ".join(kpis),
            # reference de localisation (evaluation seulement)
            "vrai_node": vn,
            "site_restitue": pd.notna(vn) and node == vn,            # le site d'origine est retrouve
            "vraie_cellule": vc,
            "secteur_restitue": pd.notna(vc) and vc in secteurs,     # le secteur d'origine est dans la liste
        })

    res = pd.DataFrame(lignes)
    res["difficulte"] = tickets["difficulte"].values
    res.to_csv(args.out, index=False)

    mode = f"{args.k} plus proches (max {args.rayon} km)" if args.k else f"rayon fixe {args.rayon} km"
    print(f"{len(res)} tickets traites | {mode} | "
          f"anomalie trouvee : {res['anomalie_trouvee'].sum()}\n")

    # evaluation en RESTITUTION (retrouve-t-on le site d'origine ?), pas en classification
    evaluables = res[tickets["est_positif"].values]
    nb_sect = evaluables.loc[evaluables["anomalie_trouvee"], "secteurs_a_inspecter"].str.count(";").add(1)
    print(f"Tickets evaluables (anomalie de reference connue) : {len(evaluables)}")
    print(f"  site restitue               : {evaluables['site_restitue'].sum()} ({evaluables['site_restitue'].mean():.1%})")
    print(f"  secteur restitue            : {evaluables['secteur_restitue'].sum()} ({evaluables['secteur_restitue'].mean():.1%})")
    print(f"  secteurs a inspecter / site : {nb_sect.mean():.1f} en moyenne")
    tab = evaluables.groupby("difficulte")[["site_restitue", "secteur_restitue"]].mean().round(3)
    tab["n"] = evaluables.groupby("difficulte").size()
    print(tab.to_string())

    # cout d'inspection sur TOUT le jeu, avec ou sans reference
    trouve = res["anomalie_trouvee"]
    cout = res.loc[trouve, "secteurs_a_inspecter"].str.count(";").add(1)
    print(f"\nCout d'inspection (500 tickets) : {trouve.sum()} pistes remontees "
          f"({trouve.mean():.1%}), {cout.mean():.1f} secteurs chacune")

    print(f"\nDetail par ticket -> {args.out}")


if __name__ == "__main__":
    main()
