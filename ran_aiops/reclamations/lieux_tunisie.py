import difflib
import re
from functools import cache

from ran_aiops.chemins import LIEUX_TUNISIE
from ran_aiops.commun.texte import normaliser

FICHIER = LIEUX_TUNISIE
SEUIL = 0.85          # en dessous, on prefere ne rien corriger
VOIE = r"^(rue|avenue|route|impasse|boulevard|av\.|bd|rr|rn|rl|cite|residence)\b"


@cache
def _charger():
    index = {}
    with open(FICHIER, encoding="utf-8") as f:
        for ligne in f:
            n = ligne.strip()
            if n:
                index.setdefault(normaliser(n), n)
    return index


def corriger(adresse, seuil=SEUIL):    
    if not adresse:
        return adresse
    index = _charger()
    sortie = []
    for part in str(adresse).split(","):
        part = part.strip()
        cle = normaliser(part)
        if not cle or re.match(VOIE, part, re.I):
            sortie.append(part)
            continue
        proche = difflib.get_close_matches(cle, index, n=1, cutoff=seuil)
        sortie.append(index[proche[0]] if proche else part)
    return ", ".join(sortie)


if __name__ == "__main__":
    import sys
    for a in sys.argv[1:]:
        print(f"{a!r} -> {corriger(a)!r}")
