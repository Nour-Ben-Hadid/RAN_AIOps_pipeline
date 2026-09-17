"""Appels Gemini : requete HTTP brute, et variante memoisee avec backoff."""

import hashlib
import json
import os
import time
from functools import cache

import requests

from ran_aiops.chemins import CACHE_LLM, prevoir
from ran_aiops.commun.env import cle_api

MODELE = "gemini-flash-lite-latest"


class ErreurGeminiTemporaire(RuntimeError):
    """Echec apres backoff : appel a relancer plus tard."""


def appeler_gemini(prompt, cle, modele=MODELE, temperature=0.0):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent"
    r = requests.post(
        url,
        headers={"x-goog-api-key": cle, "Content-Type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": 2048},
        },
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


@cache
def _cache():
    if os.path.exists(CACHE_LLM):
        with open(CACHE_LLM, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _sauver():
    with open(prevoir(CACHE_LLM), "w", encoding="utf-8") as f:
        json.dump(_cache(), f, ensure_ascii=False, indent=0)


def appeler_cache(prompt, modele=MODELE, temperature=0.0, pause=6.5):
    """appel memoise par hash du prompt, avec backoff sur quota, incidents et coupures"""
    cle = hashlib.sha1(f"{modele}|{temperature}|{prompt}".encode()).hexdigest()
    cache = _cache()
    if cle in cache:
        return cache[cle]

    for tentative in range(4):
        try:
            cache[cle] = appeler_gemini(prompt, cle_api(), modele, temperature)
            _sauver()
            time.sleep(pause)
            return cache[cle]
        except (requests.HTTPError, requests.Timeout, requests.ConnectionError) as e:
            code = getattr(e.response, "status_code", None)
            if code is not None and code not in (429, 500, 502, 503):
                raise
            attente = pause * (2 ** tentative)
            print(f"  {code or type(e).__name__}, nouvelle tentative dans {attente:.0f}s")
            time.sleep(attente)
    raise ErreurGeminiTemporaire(
        "appels Gemini en echec : relance plus tard, le cache conserve l'acquis"
    )
