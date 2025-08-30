from scripts.lexicon import charge_lexicon, match_lexicon
from scripts.scraping import find_crat_url, fetch_crat_sections
from scripts.topic import detect_grossesse_allaitement
from scripts.pplx_client import pplx_call_structured
from scripts.utils  import render_response
from scripts.allowlist import ALLOWLIST_GLOBAL

# Charger le lexique une seule fois au démarrage
lexicon = charge_lexicon("LISTE_MEDICAMENT_CLEAN_FINAL.csv")


def process_user_question(q: str):
    """
    Orchestration :
    - détecte le topic (grossesse / allaitement / autre)
    - détecte le médicament dans la question
    - si grossesse/allaitement + médicament trouvé -> CRAT (fetch_crat_sections)
      -> si pas d'URL CRAT trouvée, fallback Perplexity
    - sinon -> Perplexity direct
    """
    topic = detect_grossesse_allaitement(q) # "grossesse", "allaitement" ou None
    med = match_lexicon(q, lexicon)

    print(topic)
    print(med)

    # Cas CRAT
    if topic in ("grossesse", "allaitement") and med:
        url = find_crat_url(med, topic)
        if url:  # succès CRAT
            crat_data = fetch_crat_sections(url)
            if crat_data : # a voir ce quon considere comme echec
                return {
                    "topic": topic,
                    "med": med,
                    "source": "CRAT",
                    "data": crat_data,
                }
        else:    # échec CRAT → fallback Perplexity
            data = pplx_call_structured(q,ALLOWLIST_GLOBAL)
            return {
                "source": "perplexity",
                "data": render_response(data, ALLOWLIST_GLOBAL),
            }

    # Cas par défaut → Perplexity
    data = pplx_call_structured(q,ALLOWLIST_GLOBAL)
    return {
        "source": "perplexity",
        "data": render_response(data, ALLOWLIST_GLOBAL)
    }
