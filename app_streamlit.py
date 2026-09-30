"""Streamlit console for the RAN AIOps prototype.

Run:
    streamlit run app_streamlit.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from ran_aiops.chemins import (
    ANOMALIES_JOURNALIERES,
    BASE_RECLAMATIONS,
    CELLULES_CHRONIQUES,
    TUNISIA_LOCATIONS,
)
from ran_aiops.commun import base
from ran_aiops.reclamations.traitement import traiter_ticket
from ran_aiops.recommandation.generation import recommander


st.set_page_config(
    page_title="RAN AIOps Console",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(show_spinner=False, ttl=10)
def lire_csv(chemin: str) -> pd.DataFrame:
    path = Path(chemin)
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


@st.cache_data(show_spinner=False, ttl=2)
def charger_reclamations() -> pd.DataFrame:
    base.initialiser()
    with base.connexion() as cx:
        return pd.read_sql_query("SELECT * FROM reclamations ORDER BY recu_le DESC", cx)


def vider_cache():
    st.cache_data.clear()


def badge(valeur):
    return "non renseigne" if pd.isna(valeur) or valeur in ("", None) else valeur


def texte_ou_vide(valeur, vide: str = "Non renseigne"):
    if pd.isna(valeur) or valeur in ("", None):
        return vide
    return str(valeur)


def champ_detail(label: str, valeur):
    st.caption(label)
    st.write(texte_ou_vide(valeur))


def afficher_liste_semicolon(valeur, vide: str = "Aucun element"):
    items = [x.strip() for x in str(valeur or "").split(";") if x.strip() and x.strip() != "nan"]
    if not items:
        st.write(vide)
        return
    for item in items:
        st.markdown(f"- {item}")


def colonnes_existantes(df: pd.DataFrame, colonnes: list[str]) -> list[str]:
    return [c for c in colonnes if c in df.columns]


def filtrer_multiselect(df: pd.DataFrame, colonne: str, label: str, prefixe: str = "") -> pd.DataFrame:
    if df.empty or colonne not in df.columns:
        return df
    valeurs = sorted(v for v in df[colonne].dropna().unique())
    choix = st.multiselect(label, valeurs, key=f"filtre_{prefixe}_{label}_{colonne}")
    return df[df[colonne].isin(choix)] if choix else df


def carte_kpi(titre: str, valeur, aide: str | None = None):
    st.metric(titre, "0" if pd.isna(valeur) else valeur, help=aide)


def afficher_recommandation(ligne: pd.Series):
    st.subheader("Recommendation LLM")
    st.markdown("**Diagnostic**")
    st.write(texte_ou_vide(ligne.get("diagnostic"), "Aucun diagnostic genere."))
    if texte_ou_vide(ligne.get("cause_probable"), ""):
        st.markdown("**Cause probable**")
        st.write(ligne["cause_probable"])
    st.markdown("**Actions proposees**")
    afficher_liste_semicolon(ligne.get("actions"), "Aucune action proposee.")
    fiches = texte_ou_vide(ligne.get("fiches"), "")
    if fiches:
        st.caption(f"Fiches utilisees : {ligne['fiches']}")


def afficher_fiche_ticket(ligne: pd.Series):
    tab_plainte, tab_anomalie, tab_reco, tab_validation = st.tabs(
        ["Plainte & adresse", "Anomalie rattachee", "Recommendation", "Validation ingenieur"]
    )

    with tab_plainte:
        st.markdown("**Plainte client**")
        st.write(texte_ou_vide(ligne.get("texte_plainte")))
        c1, c2, c3 = st.columns(3)
        with c1:
            champ_detail("Date de la plainte", ligne.get("date"))
            champ_detail("Gouvernorat", ligne.get("gouvernorat"))
        with c2:
            champ_detail("Delegation", ligne.get("delegation"))
            champ_detail("Localite", ligne.get("localite"))
        with c3:
            champ_detail("Adresse libre", ligne.get("adresse_libre"))
            champ_detail("Code postal", ligne.get("code_postal"))
        st.caption(f"Ticket recu le : {texte_ou_vide(ligne.get('recu_le'))}")

    with tab_anomalie:
        c1, c2, c3 = st.columns(3)
        with c1:
            champ_detail("Node retenu", ligne.get("node_retenu"))
            champ_detail("Precision localisation", ligne.get("precision_loc"))
        with c2:
            dist = ligne.get("distance_km")
            champ_detail("Distance client-node", f"{float(dist):.3f} km" if pd.notna(dist) else None)
            champ_detail("Categorie", ligne.get("categorie"))
        with c3:
            confiance = ligne.get("confiance")
            champ_detail("Confiance classification", f"{float(confiance):.2f}" if pd.notna(confiance) else None)
            champ_detail("Statut", ligne.get("statut"))

        st.markdown("**Secteurs a inspecter**")
        afficher_liste_semicolon(ligne.get("secteurs"), "Aucun secteur rattache.")
        st.markdown("**KPI en cause**")
        afficher_liste_semicolon(ligne.get("kpis"), "Aucun KPI rattache.")
        if ligne.get("erreur"):
            st.error(ligne["erreur"])

    with tab_reco:
        afficher_recommandation(ligne)

    with tab_validation:
        st.markdown("**Avis enregistre**")
        c1, c2 = st.columns(2)
        with c1:
            champ_detail("Decision", ligne.get("decision_ingenieur"))
        with c2:
            champ_detail("Derniere validation", ligne.get("valide_le"))
        st.markdown("**Commentaire ingenieur**")
        st.write(texte_ou_vide(ligne.get("commentaire_ingenieur"), "Aucun commentaire enregistre."))
        st.caption("Ces champs sont sauvegardes dans reclamations.db.")


def generer_recommandation_ticket(ticket_id: str):
    ticket = base.lire(ticket_id)
    if not ticket:
        raise ValueError(f"ticket inconnu : {ticket_id}")
    if not ticket.get("node_retenu"):
        raise ValueError("aucun node retenu : lance d'abord classification + localisation")
    if not ticket.get("kpis"):
        raise ValueError("aucun KPI en cause : impossible de choisir les fiches RAG")

    payload = {
        **ticket,
        "secteurs_a_inspecter": ticket.get("secteurs"),
    }
    reco, fiches = recommander(payload)
    if reco is None:
        raise ValueError("reponse LLM invalide ou inexploitable")

    base.maj(
        ticket_id,
        ticket.get("statut") or "traite",
        fiches="; ".join(f for f, _ in fiches),
        diagnostic=reco["diagnostic"],
        cause_probable=reco["cause_probable"],
        actions="; ".join(reco["actions"]),
    )


@st.cache_data(show_spinner=False)
def charger_referentiel_lieux() -> dict:
    if not TUNISIA_LOCATIONS.exists():
        return {"gouvernorats": [], "delegations": {}}

    with TUNISIA_LOCATIONS.open(encoding="utf-8") as f:
        data = json.load(f)

    gouvernorats = [g["name"] for g in data.get("governorates", [])]
    delegations = {
        g["name"]: [d["name"] for d in g.get("delegations", [])]
        for g in data.get("governorates", [])
    }
    return {
        "gouvernorats": gouvernorats,
        "delegations": delegations,
    }


def afficher_formulaire_nouveau_ticket():
    with st.expander("Nouveau ticket", expanded=False):
        texte_plainte = st.text_area("Plainte client", height=120, key="nouveau_ticket_plainte")
        lieux = charger_referentiel_lieux()
        option_vide = "Non renseigne"

        c1, c2, c3 = st.columns(3)
        with c1:
            date_plainte = st.date_input(
                "Date de la plainte",
                value=None,
                format="YYYY-MM-DD",
                key="nouveau_ticket_date",
            )
            gouvernorats = lieux["gouvernorats"]
            gouvernorat = st.selectbox(
                "Gouvernorat",
                [""] + gouvernorats,
                format_func=lambda valeur: "Choisir un gouvernorat" if not valeur else valeur,
                key="nouveau_ticket_gouvernorat",
            )
        with c2:
            delegations = lieux["delegations"].get(gouvernorat, [])
            delegation = st.selectbox(
                "Delegation",
                [option_vide] + delegations,
                disabled=not gouvernorat or not delegations,
                key=f"nouveau_ticket_delegation_{gouvernorat or 'aucun'}",
            )
            delegation = None if delegation == option_vide else delegation
            localite = st.text_input("Localite / secteur", key="nouveau_ticket_localite")
        with c3:
            adresse_libre = st.text_input("Adresse libre", key="nouveau_ticket_adresse")
            code_postal = st.text_input("Code postal", key="nouveau_ticket_code_postal")

        soumis = st.button("Enregistrer le ticket", type="primary")

        if not soumis:
            return

        texte_plainte = texte_plainte.strip()
        if not texte_plainte:
            st.error("La plainte client est obligatoire.")
            return
        if not gouvernorat:
            st.error("Le gouvernorat est obligatoire.")
            return

        def optionnel(valeur):
            valeur = str(valeur or "").strip()
            return valeur or None

        ticket_id = base.enregistrer(
            texte_plainte,
            date_plainte.isoformat() if date_plainte else None,
            gouvernorat=optionnel(gouvernorat),
            delegation=delegation,
            localite=optionnel(localite),
            adresse_libre=optionnel(adresse_libre),
            code_postal=optionnel(code_postal),
        )
        vider_cache()
        st.session_state["ticket_selection"] = ticket_id
        st.success(f"Ticket {ticket_id} enregistre.")
        st.rerun()


def vue_synthese(tickets: pd.DataFrame, anomalies: pd.DataFrame, chroniques: pd.DataFrame):
    st.title("RAN AIOps Console")
    st.caption("Interface rapide pour le suivi des tickets, anomalies KPI et recommandations LLM.")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        carte_kpi("Tickets", len(tickets))
    with c2:
        carte_kpi("Tickets recus", int((tickets.get("statut") == "recu").sum()) if not tickets.empty else 0)
    with c3:
        carte_kpi("Anomalies journalieres", len(anomalies))
    with c4:
        carte_kpi("Cellules chroniques", len(chroniques))

    left, right = st.columns([1, 1])
    with left:
        st.subheader("Tickets par statut")
        if tickets.empty:
            st.info("Aucun ticket dans la base SQLite.")
        else:
            st.bar_chart(tickets["statut"].fillna("inconnu").value_counts())
    with right:
        st.subheader("Top KPI flagues")
        if anomalies.empty or "kpi_principal" not in anomalies.columns:
            st.info("Aucune anomalie journaliere disponible.")
        else:
            st.bar_chart(anomalies["kpi_principal"].fillna("inconnu").value_counts().head(10))

    st.subheader("Derniers tickets")
    if tickets.empty:
        st.info(f"Base absente ou vide : {BASE_RECLAMATIONS}")
    else:
        cols = colonnes_existantes(
            tickets,
            ["ticket_id", "recu_le", "date", "statut", "categorie", "confiance", "node_retenu", "texte_plainte"],
        )
        st.dataframe(tickets[cols].head(10), use_container_width=True, hide_index=True)


def vue_tickets(tickets: pd.DataFrame):
    st.title("Tickets")
    st.caption("Les nouvelles reclamations arrivent depuis la CLI ou le systeme amont.")

    afficher_formulaire_nouveau_ticket()

    if tickets.empty:
        st.info("Aucun ticket a afficher.")
        return

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        statuts = sorted(tickets["statut"].dropna().unique())
        filtre_statut = st.multiselect("Statut", statuts, default=statuts, key="tickets_filtre_statut")
    with c2:
        cats = sorted(tickets["categorie"].dropna().unique()) if "categorie" in tickets else []
        filtre_cat = st.multiselect("Categorie", cats, key="tickets_filtre_categorie")
    with c3:
        recherche = st.text_input("Recherche texte / ticket / node", key="tickets_recherche")

    df = tickets.copy()
    if filtre_statut:
        df = df[df["statut"].isin(filtre_statut)]
    if filtre_cat:
        df = df[df["categorie"].isin(filtre_cat)]
    if recherche:
        q = recherche.lower()
        masque = pd.Series(False, index=df.index)
        for col in ["ticket_id", "texte_plainte", "node_retenu", "gouvernorat", "localite"]:
            if col in df:
                masque |= df[col].fillna("").astype(str).str.lower().str.contains(q, regex=False)
        df = df[masque]

    st.caption(f"{len(df)} ticket(s) affiches sur {len(tickets)}")
    cols = colonnes_existantes(
        df,
        [
            "ticket_id",
            "date",
            "statut",
            "categorie",
            "confiance",
            "gouvernorat",
            "node_retenu",
            "distance_km",
            "decision_ingenieur",
            "texte_plainte",
        ],
    )
    st.dataframe(df[cols], use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Detail ticket")
    ticket_ids = df["ticket_id"].astype(str).tolist()
    if st.session_state.get("ticket_selection") not in ticket_ids:
        st.session_state.pop("ticket_selection", None)
    selection = st.selectbox(
        "Ticket",
        ticket_ids,
        index=0 if ticket_ids else None,
        key="ticket_selection",
    )
    if not selection:
        return

    ligne = tickets[tickets["ticket_id"].astype(str) == str(selection)].iloc[0]
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        carte_kpi("Statut", badge(ligne.get("statut")))
    with c2:
        carte_kpi("Categorie", badge(ligne.get("categorie")))
    with c3:
        confiance = ligne.get("confiance")
        carte_kpi("Confiance", f"{float(confiance):.2f}" if pd.notna(confiance) else "n/a")
    with c4:
        dist = ligne.get("distance_km")
        carte_kpi("Distance node", f"{float(dist):.2f} km" if pd.notna(dist) else "n/a")

    afficher_fiche_ticket(ligne)

    b1, b2 = st.columns([1, 3])
    statut_ticket = ligne.get("statut")
    pret_reco = bool(texte_ou_vide(ligne.get("node_retenu"), "")) and bool(texte_ou_vide(ligne.get("kpis"), ""))
    with b1:
        if statut_ticket in ("recu", "en_cours", "echec"):
            libelle = "Relancer le traitement" if statut_ticket == "echec" else "Traiter le ticket"
            if st.button(libelle, type="primary"):
                with st.spinner("Traitement du ticket en cours..."):
                    try:
                        traiter_ticket(str(selection))
                    except Exception as exc:
                        st.error(f"Echec du traitement : {type(exc).__name__}: {exc}")
                    else:
                        vider_cache()
                        st.success("Ticket traite.")
                        st.rerun()
        elif pret_reco:
            if st.button("Regenerer la recommandation"):
                with st.spinner("Generation de la recommandation..."):
                    try:
                        generer_recommandation_ticket(str(selection))
                    except Exception as exc:
                        st.error(f"Echec recommandation : {type(exc).__name__}: {exc}")
                    else:
                        vider_cache()
                        st.success("Recommandation enregistree.")
                        st.rerun()
        else:
            st.info("Ticket deja traite sans anomalie rattachee.")
    with b2:
        if ligne.get("erreur"):
            st.error(ligne["erreur"])

    st.markdown("**Validation ingenieur**")
    st.caption("Validee = recommandation acceptable. A revoir = diagnostic incertain. Rejetee = recommandation non pertinente.")
    decisions = ["A revoir", "Validee", "Rejetee"]
    decision_actuelle = ligne.get("decision_ingenieur")
    index_decision = decisions.index(decision_actuelle) if decision_actuelle in decisions else 0
    verdict = st.radio(
        "Avis",
        decisions,
        index=index_decision,
        horizontal=True,
        key=f"decision_ingenieur_{selection}",
    )
    commentaire = st.text_area(
        "Commentaire",
        value="" if pd.isna(ligne.get("commentaire_ingenieur")) else str(ligne.get("commentaire_ingenieur") or ""),
        placeholder="Note terrain, action realisee, doute...",
        key=f"commentaire_ingenieur_{selection}",
    )
    if st.button("Enregistrer l'avis ingenieur"):
        base.valider(str(selection), verdict, commentaire or None)
        vider_cache()
        st.success("Avis enregistre.")
        st.rerun()
    if ligne.get("valide_le"):
        st.caption(f"Derniere validation : {ligne.get('valide_le')}")

    with st.expander("Zone dangereuse"):
        st.warning("La suppression retire definitivement ce ticket de la base SQLite.")
        confirmer = st.checkbox(
            f"Je confirme la suppression du ticket {selection}",
            key=f"confirmer_suppression_{selection}",
        )
        if st.button("Supprimer le ticket", disabled=not confirmer, type="secondary"):
            base.supprimer(str(selection))
            st.session_state.pop("ticket_selection", None)
            vider_cache()
            st.success("Ticket supprime.")
            st.rerun()


def vue_anomalies(anomalies: pd.DataFrame, chroniques: pd.DataFrame):
    st.title("Anomalies flaggees")
    tab1, tab2 = st.tabs(["Journalieres", "Chroniques"])

    with tab1:
        if anomalies.empty:
            st.info(f"Fichier absent ou vide : {ANOMALIES_JOURNALIERES}")
        else:
            df = anomalies.copy()
            if "Date" in df.columns:
                df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
                dmin, dmax = df["Date"].min(), df["Date"].max()
                if pd.notna(dmin) and pd.notna(dmax):
                    plage = st.date_input(
                        "Periode",
                        value=(dmin.date(), dmax.date()),
                        key="anomalies_periode",
                    )
                    if isinstance(plage, tuple) and len(plage) == 2:
                        debut, fin = pd.to_datetime(plage[0]), pd.to_datetime(plage[1])
                        df = df[(df["Date"] >= debut) & (df["Date"] <= fin)]
            df = filtrer_multiselect(df, "Region", "Region", "journalieres")
            df = filtrer_multiselect(df, "Node", "Node", "journalieres")
            df = filtrer_multiselect(df, "kpi_principal", "KPI principal", "journalieres")

            st.caption(f"{len(df)} anomalie(s)")
            c1, c2 = st.columns([1, 1])
            with c1:
                if "kpi_principal" in df:
                    st.bar_chart(df["kpi_principal"].fillna("inconnu").value_counts().head(12))
            with c2:
                if "Node" in df:
                    st.bar_chart(df["Node"].fillna("inconnu").value_counts().head(12))
            cols = colonnes_existantes(
                df,
                ["Date", "Region", "Node", "EUtranCell Id", "score_anomalie", "kpi_principal", "kpis_en_cause"],
            )
            tri = ["score_anomalie"] if "score_anomalie" in df.columns else cols[:1]
            st.dataframe(df.sort_values(tri, ascending=False)[cols], use_container_width=True, hide_index=True)

    with tab2:
        if chroniques.empty:
            st.info(f"Fichier absent ou vide : {CELLULES_CHRONIQUES}")
        else:
            df = chroniques.copy()
            df = filtrer_multiselect(df, "region", "Region", "chroniques")
            df = filtrer_multiselect(df, "Node", "Node", "chroniques")
            df = filtrer_multiselect(df, "kpi_dominant", "KPI dominant", "chroniques")
            st.caption(f"{len(df)} cellule(s) chronique(s)")
            if "kpi_dominant" in df:
                st.bar_chart(df["kpi_dominant"].fillna("inconnu").value_counts().head(12))
            cols = colonnes_existantes(
                df,
                ["region", "Node", "EUtranCell Id", "n_days", "n_flag", "taux_anormal", "kpi_dominant", "kpis_en_cause"],
            )
            tri = ["taux_anormal"] if "taux_anormal" in df.columns else cols[:1]
            st.dataframe(df.sort_values(tri, ascending=False)[cols], use_container_width=True, hide_index=True)


def afficher_page(page):
    tickets = charger_reclamations()
    anomalies = lire_csv(str(ANOMALIES_JOURNALIERES))
    chroniques = lire_csv(str(CELLULES_CHRONIQUES))

    if page == "Synthese":
        vue_synthese(tickets, anomalies, chroniques)
    elif page == "Tickets":
        vue_tickets(tickets)
    else:
        vue_anomalies(anomalies, chroniques)


@st.fragment(run_every="5s")
def afficher_page_auto(page):
    afficher_page(page)


def main():
    base.initialiser()

    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Vue",
        ["Synthese", "Tickets", "Anomalies"],
        key="page_active",
    )
    st.sidebar.divider()
    st.sidebar.caption(f"SQLite : {BASE_RECLAMATIONS.name}")

    afficher_page_auto(page)


if __name__ == "__main__":
    main()
