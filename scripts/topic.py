import re
import unicodedata


def norm(s: str) -> str:
    # minuscules + accents supprimés
    s = s.lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn") # fonction qui strip les accents
    return s

# — Déclencheurs grossesse
PREGNANCY_PATTERNS = [
    r"\bgrossesse(s)?\b",
    r"\benceinte(s)?\b",
    r"\ballait(e|er|ement|ante|antes)\b",
    r"\blactation\b",
    r"\blait\s+maternel\b",
    r"\btire?-lait|tir(er|age)\s+du?\s+lait\b",
]

PREGNANCY_RX = re.compile("|".join(PREGNANCY_PATTERNS))

def detect_grossesse_allaitement(text: str) -> str | None:
    """Retourne 'grossesse_allaitement' si des termes grossesse ou allaitement sont détectés."""
    t = norm(text)
    is_preg = bool(PREGNANCY_RX.search(t))
    if is_preg:
        return "grossesse_allaitement"
    return None
