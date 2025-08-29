import re
from .utils import strip_accents

def detect_topic(text: str) -> str | None:
    """
    Renvoie un label simple: 'grossesse_allaitement' | 'interactions' | 'posologies' | None
    (tu peux étendre au fil du temps)
    """
    t = strip_accents(text.lower())
    if re.search(r"\b(grossesse|enceinte|trimestre|allait|lactation|lait maternel)\b", t):
        return "grossesse_allaitement"
    if re.search(r"\b(interaction|assoc(i|)ation|contre[- ]?indiqu|cyp|inducteur|inhibiteur)\b", t):
        return "interactions"
    if re.search(r"\b(posologie|dosage|dose|comprime|gelule|automedication|otc|(?:\d+mg\b)|\bmg\b)\b", t):
        return "posologies"
    return None
