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
    - Normalise la question et chaque médicament
    - Match exact par mot
    - Fuzzy match si pas de match exact
    """
    # Index lexique normalisé -> original
    lex_norm = {normalize_token(m): m for m in lexicon}

    # Découper la question en tokens (uniquement mots alphanumériques)
    q_tokens = [normalize_token(tok) for tok in re.findall(r"\w+", question)]

    # 1) Match exact
    for tok in q_tokens:
        if tok in lex_norm:
            return lex_norm[tok]

    # 2) Fuzzy match (cutoff à ajuster entre 0.7 et 0.9 selon tolérance)
    for tok in q_tokens:
        close = get_close_matches(tok, list(lex_norm.keys()), n=1, cutoff=0.85)
        if close:
            return lex_norm[close[0]]

    return None
