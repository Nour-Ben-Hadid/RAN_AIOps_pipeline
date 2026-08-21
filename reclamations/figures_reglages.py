import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import jointure_anomalies as J
from commun import charger_tickets

OUT = "resultats/figures"

# palette validee (validate_palette.js, mode clair : tous les tests passent)
BLEU, ORANGE = "#2a78d6", "#eb6834"
ENCRE, ENCRE2, GRILLE = "#1a1a19", "#5c5b55", "#e5e4df"


def style(ax):
    ax.set_facecolor("white")
    ax.grid(True, color=GRILLE, lw=0.8, zorder=0)
    ax.set_axisbelow(True)
    for cote in ("top", "right"):
        ax.spines[cote].set_visible(False)
    for cote in ("left", "bottom"):
        ax.spines[cote].set_color(GRILLE)
    ax.tick_params(colors=ENCRE2, labelsize=9, length=0)


def evaluer(tk, anom, rayon, k):
    """(taux de restitution du site en %, secteurs a inspecter par piste remontee)"""
    bons = nref = 0
    secteurs = pistes = 0
    for x in tk.itertuples():
        t = {"cat_eff": x.cat_eff, "adresse": x.adresse, "date": x.date}
        node, sect, _, _ = J.localiser_detail(t, anom, 0, rayon, k)
        if x.est_positif:                      # reference connue -> restitution mesurable
            nref += 1
            bons += node == x.vrai_node
        if node is not None:                   # cout paye sur TOUT le jeu
            pistes += 1
            secteurs += len(sect)
    return 100 * bons / nref, secteurs / max(pistes, 1)


def courbe(x, bon, cout, xlabel, titre, sous_titre, choisi, fichier):
    """gain (restitution, %) contre cout (secteurs par piste) -- deux unites, deux axes"""
    fig, ax = plt.subplots(figsize=(7.2, 4.4), dpi=200)
    style(ax)
    l1, = ax.plot(x, bon, color=BLEU, lw=2, marker="o", ms=6, zorder=3,
                  label="Site restitue (%)")

    ax2 = ax.twinx()
    ax2.grid(False)
    for cote in ("top", "left"):
        ax2.spines[cote].set_visible(False)
    ax2.spines["right"].set_color(GRILLE)
    ax2.tick_params(colors=ENCRE2, labelsize=9, length=0)
    l2, = ax2.plot(x, cout, color=ORANGE, lw=2, marker="o", ms=6, zorder=3,
                   label="Secteurs a inspecter par piste")
    ax2.set_ylabel("secteurs / piste", fontsize=10, color=ENCRE2, labelpad=8)
    ax2.set_ylim(0, max(cout) * 1.25)

    # marque la valeur retenue, avec sa justification lisible directement
    if choisi is not None:
        i = list(x).index(choisi)
        ax.axvline(choisi, color=ENCRE2, lw=1, ls="--", zorder=1, alpha=0.5)
        ax.scatter([choisi], [bon[i]], s=150, facecolor="white",
                   edgecolor=BLEU, lw=2.5, zorder=4)
        ax.annotate(f"retenu : {bon[i]:.1f} %", (choisi, bon[i]),
                    textcoords="offset points", xytext=(0, 16),
                    ha="center", fontsize=9.5, color=ENCRE, fontweight="bold")

    ax.set_xlabel(xlabel, fontsize=10, color=ENCRE2, labelpad=8)
    ax.set_ylabel("% des tickets a reference", fontsize=10, color=ENCRE2, labelpad=8)
    ax.set_ylim(0, max(bon) * 1.25)
    ax.set_xticks(list(x))
    ax.set_title(titre, fontsize=13, color=ENCRE, fontweight="bold", loc="left", pad=18)
    ax.text(0, 1.03, sous_titre, transform=ax.transAxes, fontsize=9.5,
            color=ENCRE2, va="bottom")
    leg = ax.legend(handles=[l1, l2], frameon=False, fontsize=9.5, loc="upper left",
                    bbox_to_anchor=(0, -0.16), ncol=2)
    for t in leg.get_texts():
        t.set_color(ENCRE2)
    fig.tight_layout()
    fig.savefig(f"{OUT}/{fichier}", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  -> {OUT}/{fichier}")


def progression(etapes, fichier):
    """une seule serie (le gain) ; le cout, d'unite differente, est annote en clair"""
    labels = [e[0] for e in etapes]
    bon = [e[1] for e in etapes]
    cout = [e[2] for e in etapes]
    y = range(len(labels))
    fig, ax = plt.subplots(figsize=(7.6, 3.2), dpi=200)
    style(ax)
    ax.grid(axis="y", visible=False)
    ax.barh(list(y), bon, height=0.45, color=BLEU, zorder=3)
    for i, (b, c) in enumerate(zip(bon, cout)):
        ax.text(b + 1, i, f"{b:.1f} %", va="center", fontsize=9,
                color=ENCRE, fontweight="bold")
        ax.text(b + 1, i - 0.26, f"{c:.1f} secteurs / piste", va="center",
                fontsize=8.5, color=ENCRE2)
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=9.5, color=ENCRE)
    ax.set_xlabel("site restitue (% des tickets a reference)", fontsize=10,
                  color=ENCRE2, labelpad=8)
    ax.set_xlim(0, max(bon) * 1.30)
    ax.set_title("Rayon fixe contre selection adaptative", fontsize=13, color=ENCRE,
                 fontweight="bold", loc="left", pad=22)
    ax.text(0, 1.04, "500 tickets — meme a son meilleur reglage, le rayon fixe fait moins bien",
            transform=ax.transAxes, fontsize=9.5, color=ENCRE2, va="bottom")
    fig.tight_layout()
    fig.savefig(f"{OUT}/{fichier}", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"  -> {OUT}/{fichier}")


def main():
    os.makedirs(OUT, exist_ok=True)
    tk = charger_tickets()
    anom = J.charger_anomalies()

    print("balayage de k (rayon max 8 km)...")
    ks = list(range(2, 13))
    res_k = [evaluer(tk, anom, 8.0, k) for k in ks]

    print("balayage du rayon fixe (k = 0)...")
    rayons = [1, 2, 3, 4, 5, 6, 8, 10]
    res_r = [evaluer(tk, anom, float(r), 0) for r in rayons]

    print("\nfigures :")
    courbe(ks, [a for a, _ in res_k], [b for _, b in res_k],
           "k = nombre de sites candidats retenus",
           "Choix de k : le pic est mesure, pas suppose",
           "500 tickets — au-dela de k=7 la restitution se degrade, a cout d'inspection inchange",
           7, "fig_k.png")

    courbe(rayons, [a for a, _ in res_r], [b for _, b in res_r],
           "rayon fixe (km)",
           "Pourquoi un rayon fixe ne suffit pas",
           "Aucune valeur n'atteint ce que donne la selection des k plus proches",
           None, "fig_rayon.png")

    # baseline : le MEILLEUR rayon fixe, pas celui calibre sur l'ancien jeu
    i_best = max(range(len(rayons)), key=lambda i: res_r[i][0])
    b_fixe, f_fixe = res_r[i_best]
    b_k, f_k = evaluer(tk, anom, 8.0, 7)
    print(f"\nmeilleur rayon fixe : {rayons[i_best]} km -> {b_fixe:.1f} %")

    progression([
        (f"Meilleur rayon fixe ({rayons[i_best]} km)", b_fixe, f_fixe),
        ("Selection des k=7 plus proches", b_k, f_k),
    ], "fig_progression.png")

    print("\nrelancer ce script suffit a reproduire les figures")


if __name__ == "__main__":
    main()
