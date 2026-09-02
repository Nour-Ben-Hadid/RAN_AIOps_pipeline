"""Normalisation de chaines et comparaison de categories."""

import re
import unicodedata


def normaliser(s):
    """minuscules sans accents ni ponctuation, pour comparer des noms de lieux"""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def est_correct(pred, attendu):
    """un ticket ambigu est juste si la prediction est l'une des 2 categories admises"""
    return pred in str(attendu).split("|")
