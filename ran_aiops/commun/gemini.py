"""Appel HTTP a l'API Gemini, partage par la classification et la recommandation."""

import requests

MODELE = "gemini-flash-lite-latest"


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
