import re
import unicodedata
from typing import Optional
from rapidfuzz import process, fuzz


def norm(s: str) -> str:
    # minuscules + accents supprimés
    s = s.lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn") # fonction qui strip les accents
    return s

# — Déclencheurs grossesse

LEXICON = {
    # GROSSESSE
    "grossesse": "grossesse",
    "enceinte": "grossesse",
    "enceintes": "grossesse",

    # ALLAITEMENT
    "allaitement": "allaitement",
    "allaitante": "allaitement",
    "allaitantes": "allaitement",
    "allait": "allaitement",         # "femme allait"
    "allaiter": "allaitement",
    "lait": "allaitement",           # à utiliser avec précaution
    "maternel": "allaitement",       # capté dans "lait maternel"
    "lait_maternel": "allaitement"   # token fusionné
}


def normalize_token(tok: str) -> str:
    """Met en minuscule et supprime accents."""
    tok = tok.lower()
    tok = "".join(c for c in unicodedata.normalize("NFKD", tok) if not unicodedata.combining(c))
    return tok

def detect_grossesse_allaitement(text: str, threshold: int = 82) -> Optional[str]:
    """
    Retourne 'grossesse', 'allaitement' ou None.
    Priorité :
      - grossesse si trouvé
      - sinon allaitement si trouvé
    """
    tokens = [normalize_token(t) for t in re.findall(r"\w+", text)]

    # Fusionner tokens ("lait maternel" → "lait_maternel")
    fused_tokens = []
    i = 0
    while i < len(tokens):
        if i < len(tokens) - 1 and tokens[i] == "lait" and tokens[i+1] == "maternel":
            fused_tokens.append("lait_maternel")
            i += 2
        else:
            fused_tokens.append(tokens[i])
            i += 1

    # Recherche
    best_match = None
    best_score = 0

    for tok in fused_tokens:
        # Exact
        if tok in LEXICON:
            return LEXICON[tok]

        # Fuzzy
        match = process.extractOne(tok, LEXICON.keys(), scorer=fuzz.ratio)
        if match:
            key, score, _ = match
            if score > best_score and score >= threshold:
                best_score = score
                best_match = LEXICON[key]

    return best_match
