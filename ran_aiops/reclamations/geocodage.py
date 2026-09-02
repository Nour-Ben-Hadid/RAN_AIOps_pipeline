import json
import os
import re
import sys
from functools import cache

from geopy.exc import GeopyError
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from ran_aiops.chemins import CACHE_GEOCODAGE_LIEUX, prevoir
from ran_aiops.commun.texte import normaliser
from ran_aiops.reclamations.lieux_tunisie import corriger

CACHE_PATH = CACHE_GEOCODAGE_LIEUX

LANGUE, PAYS = "fr", "tn"
TN_BBOX = (30.20, 37.60, 7.45, 11.65)

# du plus fin au plus grossier, avec le champ Nominatim correspondant.
# le gouvernorat seul n'est pas geocode : la jointure filtre alors par region.
NIVEAUX = ["rue", "localite", "delegation"]
CLES = ["street", "city", "county"]


@cache
def _cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _sauver():
    with open(prevoir(CACHE_PATH), "w", encoding="utf-8") as f:
        json.dump(_cache(), f, ensure_ascii=False, indent=0)


@cache
def _moteur(inverse=False):
    g = Nominatim(user_agent="ran-aiops-adresses/1.0")
    return RateLimiter(g.reverse if inverse else g.geocode,
                       min_delay_seconds=1.1, max_retries=2, swallow_exceptions=False)


def _dans_tunisie(lat, lon):
    a, b, c, d = TN_BBOX
    return a <= lat <= b and c <= lon <= d


def _sans_prefixe(nom):
    """Nominatim renvoie 'Gouvernorat Sousse' ; les nodes portent 'Sousse'"""
    if not nom:
        return None
    return re.sub(r"^(gouvernorat|d[eé]l[eé]gation)\s+", "", nom, flags=re.I).strip()


def _resoudre(requete):
    """requete Nominatim (structuree ou texte libre) -> (lat, lon), avec cache disque"""
    cle = ("|".join(f"{k}={normaliser(v)}" for k, v in sorted(requete.items()))
           if isinstance(requete, dict) else normaliser(requete))
    cache = _cache()
    if cle in cache:
        v = cache[cle]
        return tuple(v) if v else None

    try:
        res = _moteur()(requete, country_codes=PAYS, language=LANGUE, addressdetails=False)
    except GeopyError as e:
        # panne reseau : on ne cache rien, la requete reste a retenter
        print(f"[geocode] echec reseau sur {requete} : {e}", file=sys.stderr)
        return None

    val = [res.latitude, res.longitude] if res and _dans_tunisie(res.latitude, res.longitude) else None
    cache[cle] = val
    _sauver()
    return tuple(val) if val else None


def geocoder_lieu(gouvernorat, delegation=None, localite=None, adresse_libre=None,
                  code_postal=None):
    """(lat, lon, niveau) en retirant les champs les plus fins jusqu'a obtenir un point.

    (None, None, None) si rien n'est resolu au-dessus du gouvernorat."""
    valeurs = [corriger(adresse_libre) if adresse_libre else None, localite, delegation]
    for i, niveau in enumerate(NIVEAUX):
        if not valeurs[i]:
            continue
        structuree = {c: v for c, v in zip(CLES[i:], valeurs[i:]) if v}
        structuree["state"] = gouvernorat
        if code_postal and i < 2:
            structuree["postalcode"] = code_postal
        # city= ne matche pas les quartiers (suburb) : repli en texte libre au meme niveau
        texte = ", ".join([*(v for v in valeurs[i:] if v), gouvernorat, "Tunisie"])
        pos = _resoudre(structuree) or _resoudre(texte)
        if pos:
            return pos[0], pos[1], niveau
    return None, None, None


def lieu_depuis_coords(lat, lon):
    """champs de localisation d'un point (geocodage inverse), ou None"""
    lat, lon = float(lat), float(lon)
    if not _dans_tunisie(lat, lon):
        return None

    cle = f"rev|{lat:.6f},{lon:.6f}"
    cache = _cache()
    if cle not in cache:
        try:
            res = _moteur(True)((lat, lon), language=LANGUE, addressdetails=True)
        except GeopyError as e:
            print(f"[geocode] echec reseau sur reverse ({lat}, {lon}) : {e}", file=sys.stderr)
            return None
        cache[cle] = res.raw.get("address") if res else None
        _sauver()

    a = cache[cle]
    if not a:
        return None
    return {
        "gouvernorat": _sans_prefixe(a.get("state")),
        "delegation": _sans_prefixe(a.get("county") or a.get("state_district")),
        "localite": a.get("city") or a.get("town") or a.get("village") or a.get("suburb"),
        "adresse_libre": a.get("road"),
        "code_postal": a.get("postcode"),
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("gouvernorat")
    ap.add_argument("--delegation")
    ap.add_argument("--localite")
    ap.add_argument("--adresse")
    ap.add_argument("--code-postal")
    a = ap.parse_args()

    print(geocoder_lieu(a.gouvernorat, a.delegation, a.localite, a.adresse, a.code_postal))
