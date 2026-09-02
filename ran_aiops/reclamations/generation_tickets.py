"""Genere les tickets synthetiques a partir des anomalies detectees.
A relancer a chaque changement de detecteur : les tickets figent la verite terrain.
"""

import argparse
import math
import random

import pandas as pd

from ran_aiops.reclamations.geocodage import lieu_depuis_coords
from ran_aiops.chemins import (ANOMALIES_JOURNALIERES, CELLULES_CHRONIQUES,
                               NODES_COORDS, POSITIONS_REELLES, TICKETS, prevoir)
from ran_aiops.commun.kpi import familles_de
from ran_aiops.reclamations.jointure import CHAMPS_LIEU, haversine

DECALAGE_MIN_KM, DECALAGE_MAX_KM = 0.2, 2.0

# du plus fin au plus grossier, avec le champ qui le caracterise
NIVEAUX = ["rue", "localite", "delegation", "gouvernorat"]
CHAMPS = ["adresse_libre", "localite", "delegation", "gouvernorat"]

# proportions reprises du jeu d'origine, pour rester comparable
PARTS = {"facile": 0.300, "ambigu": 0.286, "vague": 0.143,
         "facile_chronique": 0.057, "hors_sujet": 0.107, "negatif_reseau": 0.107}

# ------------------------------------------------------------------ textes
# modeles de phrases, pas de LLM : sinon la comparaison embeddings/LLM serait faussee
TEXTES = {
    "A_accessibilite": [
        "Je n'arrive pas du tout a me connecter, aucune connexion ne s'etablit.",
        "impossible de me connecter a internet depuis ce matin",
        "aucun acces au reseau, mes appels ne passent jamais",
        "je capte rien du tout, aucune connexion possible",
        "ca refuse de se connecter a chaque tentative",
        "j'ai pas d'internet du tout, sa charge et sa veut pas marcher",
        "Bonjour, je n'ai aucun acces a internet malgre plusieurs tentatives.",
        "mon telephone affiche connecte mais rien ne s'ouvre",
        "impossible d'etablir une connexion, ca echoue a chaque fois",
        "aucune donnee mobile ne fonctionne chez moi",
    ],
    "B_retenabilite": [
        "Mes appels coupent tout le temps en pleine conversation.",
        "la connexion tombe toutes les 5 minutes, je dois relancer",
        "ca se deconnecte sans arret meme quand je reste assis",
        "l'appel coupe tout le temps, meme chez moi",
        "mes communications s'interrompent sans raison",
        "deconnexions repetees toute la journee",
        "je suis coupe en plein appel plusieurs fois par jour",
        "le wifi du telephone se deconnecte du reseau mobile en permanence",
        "ca coupe puis ca revient, sans arret",
        "connexion instable, elle lache toutes les deux minutes",
    ],
    "C_mobilite": [
        "Le reseau lache completement des que je prends la voiture.",
        "quand je me deplace ca perd le reseau, mais chez moi ca va",
        "des que je marche dans la rue internet coupe",
        "en changeant de quartier je perds systematiquement la connexion",
        "ca coupe uniquement quand je bouge, a l'arret aucun probleme",
        "en voiture je n'ai plus rien, des que je m'arrete ca revient",
        "le reseau tombe des que je sors de chez moi",
        "je perds la connexion en me deplacant entre les quartiers",
        "sur la route ca ne tient pas du tout",
        "des que je prends le bus la connexion saute",
    ],
    "D_debit_5g": [
        "Internet est devenu tres lent, les videos ne chargent plus.",
        "Le debit est tres faible, la video charge pas du tout.",
        "je n'ai plus la 5G, seulement la 4G alors que j'ai un forfait 5G",
        "la connexion marche mais elle est extremement lente",
        "ca rame enormement, les pages mettent une eternite",
        "le telechargement est devenu tres lent depuis quelques jours",
        "les videos s'arretent pour charger tout le temps",
        "debit ridicule, impossible de regarder quoi que ce soit",
        "la 5G a disparu, je suis bloque en 4G",
        "internet fonctionne mais tres tres lentement",
    ],
}

# ambigu : le texte laisse hesiter entre deux familles precises
TEXTES_AMBIGUS = {
    ("B_retenabilite", "D_debit_5g"): [
        "La video s'arrete et recommence a charger, puis elle coupe.",
        "ca rame puis ca finit par se deconnecter",
        "lent et ca coupe, je ne sais pas ce qui se passe",
    ],
    ("B_retenabilite", "C_mobilite"): [
        "coupures frequentes, difficile de dire si c'est lie au deplacement",
        "ca coupe souvent, parfois en marchant parfois assis",
        "deconnexions repetees, y compris quand je bouge",
    ],
    ("C_mobilite", "D_debit_5g"): [
        "c'est tres lent quand je me deplace",
        "en voiture le debit devient catastrophique",
        "ca rame surtout quand je bouge",
    ],
    ("A_accessibilite", "B_retenabilite"): [
        "parfois ca ne se connecte pas, parfois ca coupe apres",
        "j'arrive pas a me connecter, et quand j'y arrive ca lache",
        "connexion impossible ou alors elle tombe tout de suite",
    ],
    ("A_accessibilite", "D_debit_5g"): [
        "soit ca ne charge pas du tout, soit c'est infiniment lent",
        "internet ne s'ouvre pas ou alors ca met dix minutes",
        "pas de connexion, ou tellement lente que c'est pareil",
    ],
}

TEXTES_VAGUES = [
    "il y a un souci, je ne sais pas d'ou ca vient",
    "internet i marche pas",
    "ca marche mal chez moi",
    "j'ai un probleme avec le reseau",
    "rien ne fonctionne correctement",
    "probleme de connexion depuis hier",
    "ca marche pas bien, faites quelque chose",
    "le reseau est mauvais dans mon quartier",
    "j'ai des problemes avec mon telephone",
    "ca fonctionne pas comme avant",
]

TEXTES_HORS_RESEAU = [
    "Ma facture de ce mois est trop elevee, je veux une explication.",
    "Je veux changer mon offre, comment faire ?",
    "Comment resilier mon abonnement internet ?",
    "Ma carte SIM ne fonctionne plus, je veux la remplacer.",
    "Le service client ne repond jamais quand j'appelle.",
    "je voudrais connaitre mon solde",
    "comment recharger mon forfait ?",
    "j'ai ete debite deux fois ce mois-ci",
    "je veux passer a un forfait superieur",
    "ou se trouve l'agence la plus proche ?",
]


def niveau_de(champs):
    """niveau de precision atteint par les champs renseignes"""
    return next((n for n, c in zip(NIVEAUX, CHAMPS) if champs.get(c)), None)


def degrader(champs, cible):
    """vide les champs plus fins que le niveau vise (client qui ne sait pas)"""
    i = NIVEAUX.index(cible)
    sortie = {c: (champs.get(c) if j >= i else None) for j, c in enumerate(CHAMPS)}
    sortie["code_postal"] = champs.get("code_postal") if i == 0 else None
    return sortie


def position_autour(lat, lon, rng):
    """point tire dans l'anneau [MIN, MAX] km, uniforme en surface"""
    d = math.sqrt(rng.random() * (DECALAGE_MAX_KM ** 2 - DECALAGE_MIN_KM ** 2)
                  + DECALAGE_MIN_KM ** 2)
    cap = rng.uniform(0, 2 * math.pi)
    return (lat + d * math.cos(cap) / 111.32,
            lon + d * math.sin(cap) / (111.32 * math.cos(math.radians(lat))))


def banque_lieux(nodes, coords, rng, essais, sans_reseau):
    """{node: [(lat, lon, champs), ...]} -- une seule fois par node"""
    banque = {}
    for i, node in enumerate(sorted(nodes), 1):
        n = coords.loc[node]
        entrees = []
        for _ in range(essais):
            lat, lon = position_autour(float(n["Latitude"]), float(n["Longitude"]), rng)
            champs = None if sans_reseau else lieu_depuis_coords(lat, lon)
            if not champs or not champs.get("gouvernorat"):
                champs = {"gouvernorat": n["Region"], "localite": n["lieu_reconnu"]}
            entrees.append((lat, lon, champs))
        banque[node] = entrees
        if i % 25 == 0:
            print(f"  banque de lieux : {i}/{len(nodes)} nodes...")
    return banque


def tirer_lieu(banque, node, rng, cible):
    """une entree de la banque, en privilegiant celles qui atteignent le niveau vise"""
    entrees = banque[node]
    ok = [e for e in entrees if niveau_de(e[2]) == cible]
    return rng.choice(ok or entrees)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=500, help="nombre total de tickets")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--essais", type=int, default=4,
                    help="adresses candidates par node dans la banque")
    ap.add_argument("--parts-niveau", default="0.55,0.25,0.13,0.07",
                    help="proportions visees pour " + ",".join(NIVEAUX))
    ap.add_argument("--rayon", type=float, default=2.0, help="rayon pour n_nodes_proches")
    ap.add_argument("--sans-reseau", action="store_true")
    ap.add_argument("--out", default=TICKETS)
    ap.add_argument("--positions", default=POSITIONS_REELLES)
    args = ap.parse_args()

    rng = random.Random(args.seed)
    coords = pd.read_csv(NODES_COORDS).set_index("Node")

    # --------------------------------------------------------- anomalies
    aj = pd.read_csv(ANOMALIES_JOURNALIERES)
    aj = aj[aj["Node"].isin(coords.index)].copy()
    aj["familles"] = aj["kpis_en_cause"].map(familles_de)
    aj["n_fam"] = aj["familles"].map(len)

    cc = pd.read_csv(CELLULES_CHRONIQUES)
    cc = cc[cc["Node"].isin(coords.index)].copy()
    cc["familles"] = cc["kpis_en_cause"].map(familles_de)

    simples = aj[aj["n_fam"] == 1].index.tolist()          # facile / vague
    multiples = aj[aj["n_fam"] >= 2].index.tolist()        # ambigu
    chroniques = cc.index.tolist()
    dates = sorted(pd.to_datetime(aj["Date"]).dt.strftime("%Y-%m-%d").unique())
    print(f"anomalies : {len(aj)} journalieres ({len(simples)} a 1 famille, "
          f"{len(multiples)} a 2+), {len(chroniques)} chroniques")

    # nombre de tickets par difficulte
    quotas = {k: int(round(v * args.n)) for k, v in PARTS.items()}
    quotas["facile"] += args.n - sum(quotas.values())      # ajustement d'arrondi
    print("quotas :", quotas)

    # ------------------------------------------------- construction des tickets
    lignes = []

    def positif(idx, source, difficulte, categorie, texte, chronique=False):
        r = (cc.loc[idx] if chronique else aj.loc[idx])
        lignes.append({
            "date": rng.choice(dates) if chronique else str(pd.to_datetime(r["Date"]).date()),
            "texte_plainte": texte, "vrai_node": r["Node"],
            # pas r.name : c'est l'index entier, pas l'identifiant de cellule
            "vraie_cellule": r["EUtranCell Id"],
            "vrai_kpi_principal": r["kpi_dominant"] if chronique else r["kpi_principal"],
            "vrais_kpis_en_cause": r["kpis_en_cause"],
            "categorie_attendue": categorie, "difficulte": difficulte,
            "est_positif": True, "source": source,
        })

    for idx in rng.sample(simples, quotas["facile"]):
        fam = next(iter(aj.loc[idx, "familles"]))
        positif(idx, "incident_journalier", "facile", fam, rng.choice(TEXTES[fam]))

    for idx in rng.sample(simples, quotas["vague"]):
        positif(idx, "incident_journalier", "vague", "INDETERMINE", rng.choice(TEXTES_VAGUES))

    for idx in rng.sample(multiples, quotas["ambigu"]):
        fams = sorted(aj.loc[idx, "familles"])
        paire = next((p for p in TEXTES_AMBIGUS if set(p) <= set(fams)), None)
        if paire is None:                      # aucune paire outillee -> deux familles au hasard
            paire = tuple(sorted(rng.sample(fams, 2)))
            textes = TEXTES[paire[0]] + TEXTES[paire[1]]
        else:
            textes = TEXTES_AMBIGUS[paire]
        positif(idx, "incident_journalier", "ambigu", "|".join(paire), rng.choice(textes))

    for idx in rng.sample(chroniques, quotas["facile_chronique"]):
        fams = sorted(cc.loc[idx, "familles"]) or ["B_retenabilite"]
        fam = rng.choice(fams)
        texte = rng.choice(TEXTES[fam]) + " (depuis plusieurs semaines)"
        positif(idx, "cellule_chronique", "facile_chronique", fam, texte, chronique=True)

    # negatifs : un vrai node, mais une date SANS anomalie dessus -> rien a trouver
    jours_par_node = aj.groupby("Node")["Date"].apply(
        lambda s: set(pd.to_datetime(s).dt.strftime("%Y-%m-%d")))
    nodes_dispo = sorted(set(aj["Node"]) | set(cc["Node"]))
    for difficulte, textes, categorie in [
            ("hors_sujet", TEXTES_HORS_RESEAU, "HORS_RESEAU"),
            ("negatif_reseau", sum(TEXTES.values(), []), None)]:
        for _ in range(quotas[difficulte]):
            node = rng.choice(nodes_dispo)
            libres = [d for d in dates if d not in jours_par_node.get(node, set())]
            lignes.append({
                "date": rng.choice(libres or dates), "texte_plainte": rng.choice(textes),
                "vrai_node": node, "vraie_cellule": None, "vrai_kpi_principal": None,
                "vrais_kpis_en_cause": None, "categorie_attendue": categorie,
                "difficulte": difficulte, "est_positif": False, "source": "aucun",
            })

    tk = pd.DataFrame(lignes).sample(frac=1, random_state=args.seed).reset_index(drop=True)
    tk.insert(0, "ticket_id", range(1, len(tk) + 1))

    # ------------------------------------------------------------ localisation
    print(f"\nbanque de lieux ({tk['vrai_node'].nunique()} nodes, "
          f"{args.essais} candidats chacun)...")
    banque = banque_lieux(set(tk["vrai_node"]), coords, rng, args.essais, args.sans_reseau)

    poids = [float(x) for x in args.parts_niveau.split(",")]
    lat_n, lon_n = coords["Latitude"].to_numpy(), coords["Longitude"].to_numpy()
    infos = []
    for node in tk["vrai_node"]:
        cible = rng.choices(NIVEAUX, weights=poids)[0]
        lat, lon, champs = tirer_lieu(banque, node, rng, cible)
        champs = degrader(champs, cible)
        d = haversine(lat, lon, lat_n, lon_n)
        infos.append({"client_lat": round(lat, 6), "client_lon": round(lon, 6),
                      **{c: champs.get(c) for c in CHAMPS_LIEU},
                      "precision_adresse": niveau_de(champs),
                      "n_nodes_proches": int((d <= args.rayon).sum())})
    info = pd.DataFrame(infos)

    # la position reelle ne va PAS dans les tickets : la jointure doit geocoder
    pos = pd.concat([tk[["ticket_id"]], info[["client_lat", "client_lon"]]], axis=1)
    pos.to_csv(prevoir(args.positions), index=False, encoding="utf-8")

    out = pd.concat([tk, info.drop(columns=["client_lat", "client_lon"])], axis=1)
    out = out[["ticket_id", "date", "texte_plainte", "vrai_node", "vraie_cellule",
               "vrai_kpi_principal", "vrais_kpis_en_cause", "categorie_attendue",
               "difficulte", "est_positif", "source",
               *CHAMPS_LIEU, "precision_adresse", "n_nodes_proches"]]
    out.to_csv(prevoir(args.out), index=False, encoding="utf-8")

    # ------------------------------------------------------------------ recap
    print(f"\n{len(out)} tickets -> {args.out}")
    print(f"positions client (diagnostic) -> {args.positions}")
    print(f"\npositifs {int(out.est_positif.sum())} | negatifs {int((~out.est_positif).sum())}")
    print("\npar difficulte :")
    print(out.difficulte.value_counts().to_string())
    print("\nprecision de la localisation :")
    print(out.precision_adresse.value_counts().to_string())
    print(f"\ntextes distincts : {out.texte_plainte.nunique()} "
          f"(le cache LLM est indexe par texte)")
    print(f"nodes distincts  : {out.vrai_node.nunique()}")
    print(f"n_nodes_proches (rayon {args.rayon} km) : mediane "
          f"{out.n_nodes_proches.median():.0f}, max {out.n_nodes_proches.max()}")


if __name__ == "__main__":
    main()
