import json
import os
import re
import sys
import unicodedata
from functools import cache

from geopy.exc import GeopyError
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from commun import charger_env
from lieux_tunisie import corriger

CACHE_PATH = "../data/geocode_adresses_cache.json"

LANGUE = "fr"          
PAYS = "tn"
# bornes nationales :si Nominatim renvoie un point hors Tunisie
TN_BBOX = (30.20, 37.60, 7.45, 11.65)  

# une panne reseau ne doit jamais etre mise en cache comme "introuvable"
ERREURS_RESEAU = (GeopyError,)


def _norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def _norm_cp(code_postal):
    #code postal tunisien = 4 chiffres. Tout le reste est ignore
    if code_postal is None:
        return None
    cp = re.sub(r"\D", "", str(code_postal))
    if not cp:
        return None
    if len(cp) != 4:
        print(f"[geocode] code postal ignore (4 chiffres attendus) : {code_postal!r}",
              file=sys.stderr)
        return None
    return cp


def _cle(adresse, code_postal):
    base = _norm(adresse)
    cp = _norm_cp(code_postal)
    return f"{base}|{cp}" if cp else base


@cache
def _charger_cache():
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _sauver_cache():
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(_charger_cache(), f, ensure_ascii=False, indent=0)


@cache
def _moteur(inverse=False):
    geoloc = Nominatim(user_agent="ran-aiops-adresses/1.0")
    return RateLimiter(geoloc.reverse if inverse else geoloc.geocode,
                       min_delay_seconds=1.1, max_retries=2, swallow_exceptions=False)


def _dans_tunisie(lat, lon):
    a, b, c, d = TN_BBOX
    return a <= lat <= b and c <= lon <= d


def _interroger(requete, inverse=False):
    if inverse:
        res = _moteur(True)(requete, language=LANGUE, addressdetails=False)
        return [res.latitude, res.longitude, res.address] if res else None
    res = _moteur()(requete, country_codes=PAYS, addressdetails=False, language=LANGUE)
    if res and _dans_tunisie(res.latitude, res.longitude):
        return [res.latitude, res.longitude, res.address]
    return None


def geocoder_adresse(adresse, code_postal=None):
    if adresse is None or not _norm(adresse):
        return None
    cle = _cle(adresse, code_postal)

    cache = _charger_cache()
    if cle in cache:
        v = cache[cle]
        return (v[0], v[1]) if v else None

    cp = _norm_cp(code_postal)
    base = re.sub(r"[,\s]+tunisi[ae]\s*$", "", str(adresse), flags=re.I).strip(" ,")
    requete = f"{base}, {cp}, Tunisie" if cp else f"{base}, Tunisie"
    try:
        val = _interroger(requete)
    except ERREURS_RESEAU as e:
        # reseau/API indisponible : on ne cache rien, l'adresse reste a tenter
        print(f"[geocode] echec reseau sur '{adresse}' : {e}", file=sys.stderr)
        return None
    
    if val is None:
        propre = corriger(base)
        if propre != base:
            try:
                val = _interroger(f"{propre}, {cp}, Tunisie" if cp else f"{propre}, Tunisie")
            except ERREURS_RESEAU:
                return None

    cache[cle] = val          # None = adresse reellement introuvable
    _sauver_cache()
    return (val[0], val[1]) if val else None


def adresse_depuis_coords(lat, lon):    
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return None
    if not _dans_tunisie(lat, lon):
        return None

    cle = f"rev|{lat:.6f},{lon:.6f}"
    cache = _charger_cache()
    if cle in cache:
        v = cache[cle]
        return v[2] if v else None

    try:
        res = _interroger((lat, lon), inverse=True)
    except ERREURS_RESEAU as e:
        print(f"[geocode] echec reseau sur reverse ({lat}, {lon}) : {e}", file=sys.stderr)
        return None

    # on garde le point interroge, pas celui renvoye par le fournisseur
    val = [lat, lon, res[2]] if res else None
    cache[cle] = val
    _sauver_cache()
    return val[2] if val else None


def dans_cache(adresse, code_postal=None):
    return _cle(adresse, code_postal) in _charger_cache()


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("adresse")
    ap.add_argument("code_postal", nargs="?", default=None)
    a = ap.parse_args()

    origine = "cache" if dans_cache(a.adresse, a.code_postal) else "reseau"
    r = geocoder_adresse(a.adresse, a.code_postal)
    print(f"{a.adresse!r} (cp {a.code_postal or '-'}) -> {r}  ({origine})")
