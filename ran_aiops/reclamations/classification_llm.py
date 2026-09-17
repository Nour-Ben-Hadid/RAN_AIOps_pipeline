import os
import re
import csv
import json
import time
import argparse
import pandas as pd
import requests
from ran_aiops.chemins import CACHE_CLASSIFICATION, PRED_LLM, TICKETS, prevoir
from ran_aiops.commun.env import cle_api
from ran_aiops.commun.gemini import MODELE, appeler_gemini

CATEGORIES = {
    "A_accessibilite": "Le service ne s'etablit pas du tout : aucune connexion possible, "
                       "l'appel ne passe jamais, echec de connexion.",
    "B_retenabilite": "Le service s'etablit puis tombe : coupures en cours d'appel ou de "
                      "session, deconnexions repetees, SANS lien avec un deplacement.",
    "C_mobilite": "La degradation est liee au deplacement : ca coupe en voiture, en marchant, "
                  "en changeant de quartier ; stable quand l'abonne reste immobile.",
    "D_debit_5g": "Le service fonctionne mais degrade : lenteur, faible debit, videos qui ne "
                  "chargent pas, perte de la 5G au profit de la 4G.",
    "HORS_RESEAU": "La demande ne concerne pas la qualite radio : facturation, forfait, "
                   "recharge, carte SIM, resiliation, service client, agence.",
    "INDETERMINE": "Le texte signale un probleme reseau mais ne donne AUCUN indice permettant "
                   "de choisir entre A, B, C et D (ex: 'internet ne marche pas').",
}

PROMPT = """Tu classes des plaintes de clients d'un operateur telecom tunisien.
Le texte est en francais, souvent avec des fautes d'orthographe.

Categories possibles :
{categories}

Regles :
- Reponds UNIQUEMENT par un objet JSON, sans texte autour, sans bloc de code.
- Format exact : {{"categorie": "<UNE des cles ci-dessus>", "confiance": <nombre entre 0 et 1>}}
- Si le texte peut correspondre a deux categories, choisis la plus probable et baisse la confiance.
- Si le texte ne donne aucun indice sur la nature de la panne, reponds INDETERMINE.
  Ne devine pas : l'abstention est la bonne reponse dans ce cas.

Plainte : "{texte}"
"""

def construire_prompt(texte):
    cats = "\n".join(f"- {k} : {v}" for k, v in CATEGORIES.items())
    return PROMPT.format(categories=cats, texte=texte.replace('"', "'"))


def extraire_json(brut):
    """Le modele ajoute parfois ```json ... ``` autour de la reponse."""
    m = re.search(r"\{.*\}", brut, re.DOTALL)
    if not m:
        return None, None
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None, None
    cat = d.get("categorie")
    if cat not in CATEGORIES:
        return None, d.get("confiance")
    return cat, d.get("confiance")


def charger_cache(chemin):
    """cle = texte de la plainte -> (categorie, confiance) deja obtenues"""
    if not chemin or not os.path.exists(chemin):
        return {}
    with open(chemin, encoding="utf-8") as f:
        return {r["texte_plainte"]: (r["pred_llm"], r["confiance"]) for r in csv.DictReader(f)}


def sauver_cache(chemin, cache):
    if not chemin:
        return
    with open(prevoir(chemin), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["texte_plainte", "pred_llm", "confiance"])
        for t, (c, conf) in cache.items():
            w.writerow([t, c, conf])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modele", default=MODELE)
    ap.add_argument("--tickets", default=TICKETS)
    ap.add_argument("--out", default=PRED_LLM)
    ap.add_argument("--cache", default=CACHE_CLASSIFICATION)
    ap.add_argument("--pause", type=float, default=6.5, help="secondes entre appels")
    args = ap.parse_args()

    cle = cle_api()
    df = pd.read_csv(args.tickets)
    cache = charger_cache(args.cache)
    print(f"{args.modele} | {len(df)} tickets | {len(cache)} deja en cache")

    lignes, echecs = [], 0
    for _, r in df.iterrows():
        texte = r["texte_plainte"]
        if texte in cache:
            cat, conf = cache[texte]
        else:
            # jusqu'a 4 tentatives, backoff exponentiel sur quota/incident passager
            cat, conf = None, None
            for tentative in range(4):
                try:
                    brut = appeler_gemini(construire_prompt(texte), cle, args.modele)
                    cat, conf = extraire_json(brut)
                    if cat:
                        break
                except requests.HTTPError as e:
                    if e.response.status_code in (429, 500, 502, 503):
                        attente = args.pause * (2 ** tentative)
                        print(f"  HTTP {e.response.status_code}, nouvelle tentative dans {attente:.0f}s")
                        time.sleep(attente)
                        continue
                    raise
                except requests.RequestException as e:
                    print(f"  reseau : {type(e).__name__}, on retente")
                    time.sleep(args.pause * (2 ** tentative))
            if cat is None:
                echecs += 1
                cat, conf = "ECHEC_APPEL", None
            cache[texte] = (cat, conf)
            sauver_cache(args.cache, cache)
            time.sleep(args.pause)

        lignes.append({"ticket_id": r["ticket_id"], "pred_llm": cat, "confiance": conf})

    out = pd.DataFrame(lignes)
    out.to_csv(prevoir(args.out), index=False)
    print(f"\n{len(out)} predictions -> {args.out}")
    if echecs:
        print(f"ATTENTION : {echecs} appels ont echoue (ECHEC_APPEL), relance le script.")
    print(out["pred_llm"].value_counts().to_string())


if __name__ == "__main__":
    main()
