import argparse
import pandas as pd
from scipy import stats
from commun import est_correct, TICKETS


def mcnemar(ok_a, ok_b, label_a, label_b):
    """test apparie : b = a gagne la, c = b gagne la (paires discordantes seulement)"""
    b = int(((ok_a == False) & (ok_b == True)).sum())
    c = int(((ok_a == True) & (ok_b == False)).sum())
    print(f"\n--- McNemar ({label_a} vs {label_b}) : {label_b} gagne {b}x, perd {c}x ---")
    if b + c == 0:
        print("    aucune paire discordante -> test non applicable")
        return
    p = stats.binomtest(b, b + c, 0.5).pvalue
    verdict = "significatif" if p < 0.05 else "NON significatif"
    print(f"    p = {p:.4f}  -> {verdict} a 5%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tickets", default=TICKETS)
    ap.add_argument("--llm", default="resultats/predictions_llm_api.csv")
    ap.add_argument("--embed", default="resultats/predictions_embeddings.csv")
    ap.add_argument("--out", default="resultats/comparaison_predictions.csv")
    args = ap.parse_args()

    df = pd.read_csv(args.tickets)
    # les 'negatif_reseau' n'ont pas de categorie : ils testent la jointure, pas le NLP
    ev = df[df["categorie_attendue"].notna()].copy()

    # 1. embeddings zero-shot (seuil calibre par CV, cf. classification_embeddings.py)
    try:
        pe = pd.read_csv(args.embed)
        ev = ev.merge(pe[["ticket_id", "pred_embed"]], on="ticket_id", how="left")
    except FileNotFoundError:
        print(f"[!] {args.embed} absent -> lance d'abord classification_embeddings.py\n")
        ev["pred_embed"] = None

    # 2. LLM
    try:
        ev = ev.merge(pd.read_csv(args.llm)[["ticket_id", "pred_llm"]], on="ticket_id", how="left")
    except FileNotFoundError:
        print(f"[!] {args.llm} absent -> lance d'abord classification_llm_api.py\n")
        ev["pred_llm"] = None

    for m in ["embed", "llm"]:
        ev[f"ok_{m}"] = [est_correct(p, a) if pd.notna(p) else None
                         for p, a in zip(ev[f"pred_{m}"], ev["categorie_attendue"])]

    print("COMPARAISON DES METHODES DE CLASSIFICATION")
    print(f"{len(ev)} tickets evalues sur {len(df)}\n")
    print(f"{'Methode':<26}{'Exactitude':>12}{'IC95%':>18}{'n':>6}")
    print("-" * 62)
    for m, label in [("embed", "Embeddings (Solon)"),
                     ("llm", "LLM zero-shot (API)")]:
        s = ev[f"ok_{m}"].dropna()
        if len(s) == 0:
            print(f"{label:<26}{'--':>12}")
            continue
        k, n = int(s.sum()), len(s) # k = nb de bonnes réponses, n = nb total de tickets testés
        ci = stats.binomtest(k, n).proportion_ci(method="wilson")
        print(f"{label:<26}{k/n:>12.3f}{f'[{ci.low:.3f}, {ci.high:.3f}]':>18}{n:>6}")

    print("\n--- Exactitude par difficulte ---")
    tab = ev.groupby("difficulte")[["ok_embed", "ok_llm"]].mean().round(3)
    tab["n"] = ev.groupby("difficulte").size()
    print(tab.to_string())

    if ev["ok_llm"].notna().any() and ev["ok_embed"].notna().any():
        sous = ev[ev["ok_embed"].notna() & ev["ok_llm"].notna()]
        mcnemar(sous["ok_embed"], sous["ok_llm"], "embeddings", "LLM")

    ev.to_csv(args.out, index=False)
    print(f"\nDetail par ticket -> {args.out}")


if __name__ == "__main__":
    main()
