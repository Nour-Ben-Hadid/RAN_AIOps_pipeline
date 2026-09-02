"""Taxonomie KPI -> famille. La valeur est le suffixe du nom de fiche : famille_<valeur>.md"""

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


def noms_kpi(kpis):
    """['KPI 1', 'KPI 2'] a partir d'une chaine 'KPI 1; KPI 2'"""
    return [k.strip() for k in str(kpis or "").split(";") if k.strip()]


def familles_de(kpis):
    """ensemble des familles concernees par une liste de KPI"""
    return {CATEGORIE_PAR_KPI.get(k) for k in noms_kpi(kpis)} - {None}
