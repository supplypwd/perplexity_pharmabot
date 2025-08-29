import re, unicodedata
from difflib import get_close_matches
from .utils import strip_accents
import pandas as pd
from difflib import get_close_matches
from typing import List, Optional



def normalize_token(s: str) -> str:
    return strip_accents(s).lower().strip()

# ---------- Chargement du lexique depuis un CSV ----------

def charge_lexicon(path: str, encoding: str = "cp1252") -> List[str]:
    """
    Charge un CSV à 1 seule colonne contenant des noms de médicaments.
    Retourne une liste Python utilisable par match_lexicon().
    """
    df = pd.read_csv(path, encoding=encoding, header=None, names=["medicament"])
    # Supprimer les lignes vides et doublons
    meds = (
        df["medicament"]
        .dropna()
        .astype(str)
        .str.strip()
        .drop_duplicates()
        .tolist()
    )
    return meds

# ---------- Matching dans une question ----------

def match_lexicon(question: str, lexicon: List[str]) -> Optional[str]:
    """
    Retourne le nom du médicament trouvé dans la question,
    ou None si rien n'est détecté.
    """
    q_norm = normalize_token(question)

    # 1) Match exact avec frontière de mot
    for med in lexicon:
        med_norm = normalize_token(med)
        if re.search(rf"\b{re.escape(med_norm)}\b", q_norm):
            return med

    # 2) Fuzzy match (similitude >= 95 %)
    candidates = [normalize_token(m) for m in lexicon]
    close = get_close_matches(q_norm, candidates, n=1, cutoff=0.95)
    if close:
        for med in lexicon:
            if normalize_token(med) == close[0]:
                return med

    return None
