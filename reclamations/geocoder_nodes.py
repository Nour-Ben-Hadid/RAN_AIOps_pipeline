import argparse
import io
import json
import os
import re
import unicodedata

import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter


LANGUE = "fr"
PREFIX = "B5G4G_"
# jetons techniques a retirer du nom du node (pas des lieux)
STOP = {"tt", "ctt", "coh", "part", "partage", "ssal", "sal", "lgd", "lgdr", "or",
        "i", "ii", "iii", "iv", "vil", "ville", "nlle", "nelle", "zi", "zt", "zb",
        "new", "b5g4g"}


def _norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def parse_lieu(node):
    #nom de lieu interrogeable a partir du Node technique
    body = node[len(PREFIX):] if node.upper().startswith(PREFIX) else node
    toks = [t for t in re.split(r"[_\s]+", body) if t]
    toks = [t for t in toks if _norm(t) not in STOP and not re.fullmatch(r"\d+", t)]
    return _norm(" ".join(toks)) or _norm(body)


# ---------------------------------------------------- bornes des gouvernorats
# (lat_min, lat_max, lon_min, lon_max) : un hit OSM hors de ces bornes est rejete
BBOX = {
    "Gabes": (33.40, 34.10, 9.60, 10.55), "Gafsa": (34.00, 34.80, 8.00, 9.45),
    "Kairouan": (35.15, 36.10, 9.40, 10.45), "Kasserine": (34.80, 35.75, 8.30, 9.45),
    "Kebili": (32.90, 34.05, 7.80, 9.65), "Mahdia": (35.05, 35.75, 10.40, 11.25),
    "Medenine": (32.90, 33.95, 10.10, 11.55), "Monastir": (35.48, 35.90, 10.58, 11.10),
    "Nabeul": (36.28, 37.12, 10.40, 11.25), "Sidi Bouzid": (34.30, 35.35, 9.10, 10.15),
    "Sousse": (35.58, 36.38, 10.18, 10.82), "Tataouine": (31.85, 33.25, 9.95, 11.05),
    "Tozeur": (33.70, 34.55, 7.65, 8.65),
}
# centre de repli quand aucun hit valide (chef-lieu du gouvernorat)
CENTRE = {
    "Gabes": (33.8814, 10.0982), "Gafsa": (34.4250, 8.7842), "Kairouan": (35.6781, 10.0963),
    "Kasserine": (35.1674, 8.8362), "Kebili": (33.7044, 8.9690), "Mahdia": (35.5047, 11.0622),
    "Medenine": (33.3549, 10.5055), "Monastir": (35.7770, 10.8262), "Nabeul": (36.4561, 10.7376),
    "Sidi Bouzid": (35.0382, 9.4849), "Sousse": (35.8256, 10.6360), "Tataouine": (32.9297, 10.4518),
    "Tozeur": (33.9197, 8.1335),
}


def dans_bbox(lat, lon, region):
    b = BBOX.get(region)
    if not b:
        return True
    return b[0] <= lat <= b[1] and b[2] <= lon <= b[3]


def charger_nodes(kpi_path):
    with open(kpi_path, encoding="utf-8-sig") as f:
        lignes = [l for l in f if l.strip() != ""]
    df = pd.read_csv(io.StringIO("".join(lignes)))
    df = df[["Region", "Node"]].dropna().drop_duplicates()
    df["Region"] = df["Region"].str.strip()
    df["Node"] = df["Node"].str.strip()
    return df.sort_values("Node").reset_index(drop=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kpi", default="../data/KPI Table(1).csv")
    # jamais nodes_coordonnees.csv : c'est la source de verite, schema different
    ap.add_argument("--out", default="../data/nodes_geocodage_brut.csv")
    ap.add_argument("--cache", default="../data/geocode_cache.json")
    args = ap.parse_args()

    nodes = charger_nodes(args.kpi)
    print(f"{len(nodes)} nodes, {nodes[['Region']].assign(l=nodes['Node'].map(parse_lieu)).drop_duplicates().shape[0]} lieux uniques a geocoder")

    # cache disque : { "lieu|Region": [lat, lon, display_name] ou null si echec }
    cache = {}
    if os.path.exists(args.cache):
        with open(args.cache, encoding="utf-8") as f:
            cache = json.load(f)

    geoloc = Nominatim(user_agent="ran-aiops-nodes/1.0")
    geocode = RateLimiter(geoloc.geocode, min_delay_seconds=1.1, max_retries=2,
                          swallow_exceptions=True)

    def resoudre(lieu, region):        
        key = f"{lieu}|{region}|{LANGUE}"
        if key in cache:
            v = cache[key]
            return tuple(v) if v else None
        # language= : sans ca Nominatim renvoie le nom local (arabe en Tunisie)
        res = geocode(f"{lieu}, {region}, Tunisie", country_codes="tn", addressdetails=False,
                      language=LANGUE)
        val = None
        if res and dans_bbox(res.latitude, res.longitude, region):
            val = [res.latitude, res.longitude, res.address]
        cache[key] = val
        with open(args.cache, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
        return tuple(val) if val else None

    lignes = []
    for i, r in nodes.iterrows():
        lieu = parse_lieu(r["Node"])
        hit = resoudre(lieu, r["Region"])
        if hit:
            lat, lon, disp = hit
            verifie, source = True, "nominatim"
        else:
            lat, lon = CENTRE.get(r["Region"], (34.0, 9.5))
            disp, verifie, source = "", False, "repli_centre_gouvernorat"
        lignes.append({"Region": r["Region"], "Node": r["Node"],
                       "Latitude": round(lat, 6), "Longitude": round(lon, 6),
                       "lieu_interroge": lieu, "verifie": verifie,
                       "source": source, "osm_match": disp})
        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{len(nodes)}...")

    out = pd.DataFrame(lignes)
    out.to_csv(args.out, index=False, encoding="utf-8")
    n_ok = int(out["verifie"].sum())
    print(f"\nOK -> {args.out}")
    print(f"verifies OSM : {n_ok}/{len(out)}   replis centre : {len(out) - n_ok}")
    print("Colonne `verifie` = True -> coordonnee reelle ; False -> approximative.")


if __name__ == "__main__":
    main()
