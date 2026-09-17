import argparse
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold
import os
os.environ["HF_HUB_OFFLINE"] = "1"
from sentence_transformers import SentenceTransformer
from ran_aiops.chemins import PRED_EMBEDDINGS, TICKETS, prevoir
from ran_aiops.commun.texte import est_correct


MODELE = "OrdalieTech/Solon-embeddings-large-0.1"

# 4 prototypes par categorie ; pas d'INDETERMINE : l'abstention vient du seuil
PROTOTYPES = {
    "A_accessibilite": [
        "Je n'arrive pas du tout a me connecter, aucune connexion ne s'etablit.",
        "Impossible d'etablir une connexion, ca echoue a chaque tentative.",
        "J'ai pas d'internet du tout, sa charge et sa veut pas marcher.",
        "Mes appels ne passent jamais, aucun acces au reseau.",
    ],
    "B_retenabilite": [
        "Mes appels coupent tout le temps en pleine conversation.",
        "La connexion tombe toutes les 5 minutes, je dois toujours relancer.",
        "L'appel coupe tout le temps, meme quand je suis assis chez moi.",
        "Ca se deconnecte sans arret et sans raison, meme quand je reste immobile.",
    ],
    "C_mobilite": [
        "Le reseau lache completement des que je prends la voiture.",
        "Quand je me deplace ca perd le reseau, mais chez moi ca va.",
        "Des que je marche dans la rue internet coupe, mais chez moi c'est bien.",
        "En changeant de quartier je perds systematiquement la connexion.",
    ],
    "D_debit_5g": [
        "Internet est devenu tres lent, les videos ne chargent plus.",
        "Je n'ai plus la 5G, seulement la 4G alors que j'ai un forfait 5G.",
        "Le debit est tres faible, la video charge pas du tout, ca rame enormement.",
        "La connexion marche mais elle est devenue extremement lente.",
    ],
    "HORS_RESEAU": [
        "Ma facture de ce mois est trop elevee, je veux une explication.",
        "Comment resilier mon abonnement internet ?",
        "Ma carte SIM ne fonctionne plus, je veux la remplacer.",
        "Le service client ne repond jamais quand j'appelle.",
    ],
}


def encoder(modele, textes):
    """encode une liste de textes en vecteurs normalises (cosinus = produit scalaire)"""
    emb = modele.encode(textes, normalize_embeddings=True,
                        show_progress_bar=False)
    return np.asarray(emb)


def seuil_optimal(sims, cats, attendu):
    """seuil d'abstention qui maximise l'exactitude sur ce sous-ensemble"""
    candidats = np.unique(np.concatenate([[-1.0], sims, [1.0]]))
    meilleur_s, meilleure_acc = 0.0, -1.0
    for s in candidats:
        preds = np.where(sims >= s, cats, "INDETERMINE")
        acc = np.mean([est_correct(p, a) for p, a in zip(preds, attendu)])
        if acc > meilleure_acc:
            meilleure_acc, meilleur_s = acc, s
    return meilleur_s


def predire_cv(sims, cats, attendu, strate):
    """seuil choisi par validation croisee (5 plis), hors echantillon"""
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=0)
    preds = np.empty(len(sims), dtype=object)
    seuils = []
    attendu = np.asarray(attendu)
    for idx_train, idx_test in skf.split(sims, strate):
        s = seuil_optimal(sims[idx_train], cats[idx_train], attendu[idx_train])
        seuils.append(s)
        preds[idx_test] = np.where(
            sims[idx_test] >= s, cats[idx_test], "INDETERMINE")
    return preds, seuils


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickets", default=TICKETS)
    ap.add_argument("--out", default=PRED_EMBEDDINGS)
    args = ap.parse_args()

    df = pd.read_csv(args.tickets)
    # 'negatif_reseau' n'a pas de categorie_attendue : teste la jointure, pas le NLP
    ev = df[df["categorie_attendue"].notna()].copy()
    print(
        f"Tickets evalues : {len(ev)} / {len(df)}  (negatif_reseau exclus)\n")

    modele = SentenceTransformer(MODELE, device="cpu")

    protos = [t for textes in PROTOTYPES.values() for t in textes]
    cats_protos = np.array(
        [cat for cat, textes in PROTOTYPES.items() for _ in textes])
    sim = encoder(modele, ev["texte_plainte"].tolist()
                  ) @ encoder(modele, protos).T
    best = sim.argmax(axis=1)
    cats, sims = cats_protos[best], sim.max(axis=1)

    preds, seuils = predire_cv(
        sims, cats, ev["categorie_attendue"], ev["difficulte"])
    ev["pred_embed"] = preds
    ev["similarite"] = sims
    ev["ok"] = [est_correct(p, a)
                for p, a in zip(preds, ev["categorie_attendue"])]

    print(
        f"Seuil moyen retenu : {np.mean(seuils):.3f} (ecart-type {np.std(seuils):.3f})")
    print(f"Exactitude globale (hors echantillon) : {ev['ok'].mean():.3f}\n")
    print("Par difficulte :")
    print(ev.groupby("difficulte")["ok"].agg(
        ["mean", "count"]).round(3).to_string())
    print(
        f"\nAbstentions (INDETERMINE) : {(ev['pred_embed'] == 'INDETERMINE').sum()} / {len(ev)}")

    ev[["ticket_id", "pred_embed", "similarite"]].to_csv(prevoir(args.out), index=False)
    print(f"\nPredictions -> {args.out}")


if __name__ == "__main__":
    main()
