import re
import pandas as pd
import unicodedata
from rapidfuzz import process, fuzz
from typing import Optional, Dict

# ------------------------------
# Normalisation
# ------------------------------
def normalize_token(s: str) -> str:
    """
    Met en minuscules, supprime accents et espaces multiples.
    """
    s = (s or "").strip().lower()
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", s)

# ------------------------------
# Chargement lexique
# ------------------------------
def charge_lexicon(path: str) -> Dict[str, str]:
    """
    Charge un CSV à 1 seule colonne contenant des noms de médicaments.
    Retourne un dict {nom_normalisé -> nom_original}.
    """
    df = pd.read_csv(path, header=None, names=["medicament"])
    meds = (
        df["medicament"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
        .drop_duplicates()
        .tolist()
    )
    # dict clé=normalisé, valeur=original
    return {normalize_token(m): m for m in meds}

# ------------------------------
# Matching question ↔ lexique
# ------------------------------
def match_lexicon(question: str, lexicon: Dict[str, str]) -> Optional[str]:
    """
    Retourne le nom du médicament trouvé dans la question,
    ou None si rien n'est détecté.
    1) Match exact par token
    2) Fuzzy match avec RapidFuzz (seuil 80)
    """
    q_tokens = [normalize_token(tok) for tok in re.findall(r"\w+", question)]

    # 1) Match exact (rapide O(1) avec dict)
    for tok in q_tokens:
        if tok in lexicon:
            return lexicon[tok]

    # 2) Fuzzy match (si aucun exact trouvé)
    for tok in q_tokens:
        match = process.extractOne(
            tok,
            lexicon.keys(),
            scorer=fuzz.ratio
        )
        if match:
            best_key, score, _ = match
            if score >= 80:  # seuil ajustable (70-90)
                return lexicon[best_key]

    return None
