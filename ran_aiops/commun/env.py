"""Acces aux secrets : chargement du .env et recuperation de la cle API."""

import os
import re
import sys

from ran_aiops.chemins import ENV


def charger_env(chemin=ENV):
    """charge .env dans os.environ ; une variable deja posee reste prioritaire"""
    if not os.path.exists(chemin):
        return
    with open(chemin, encoding="utf-8-sig") as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith("#"):
                continue
            m = re.match(r"(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)", ligne)
            if m and m.group(1) not in os.environ:
                os.environ[m.group(1)] = m.group(2).strip().strip("\"'")


def cle_api():
    """GEMINI_API_KEY, depuis l'environnement ou le .env. Sort du programme si absente."""
    charger_env()
    cle = os.environ.get("GEMINI_API_KEY")
    if not cle:
        sys.exit("GEMINI_API_KEY introuvable : ni dans l'environnement, ni dans le .env "
                 "a la racine du projet. Ajoute une ligne GEMINI_API_KEY=ta_cle dans .env")
    return cle
