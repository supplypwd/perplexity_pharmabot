# src/officine_pplx/pplx_client.py

import requests, json
from .config import settings

def pplx_call_structured(
    question: str,
    allowlist: list[str] | None = None,
    recency: str | None = None,
    context_size: str = "low"
):
    """
    Appelle l’API Perplexity et renvoie la réponse brute JSON.
    - question: texte utilisateur
    - allowlist: liste de domaines autorisés (max 20)
    - recency: "day" | "week" | "month" | "year" (ou None)
    - context_size: "low" | "high"
    """

    headers = {
        "Authorization": f"Bearer {settings.PPLX_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.PPLX_MODEL,
        "messages": [
            {"role": "system", "content": (
                "Assistant pour pharmaciens d’officine en France. "
                "Pas de diagnostic ni d'ajustement de traitement. "
                "Si les sources autorisées ne couvrent pas, dis-le. "
                "Réponses courtes et claires. Cite 1–3 sources par paragraphe."
            )},
            {"role": "user", "content": question},
        ],
        "max_tokens": 700,
        "web_search_options": {"search_context_size": context_size},
        "response_format": settings.RESPONSE_FORMAT,  # <- pris de config.py
    }

    if recency:
        payload["search_recency_filter"] = recency
    if allowlist is not None:
        payload["search_domain_filter"] = allowlist[:20]  # API max 20

    r = requests.post(settings.PPLX_ENDPOINT, headers=headers, json=payload, timeout=settings.TIMEOUT)
    r.raise_for_status()
    data = r.json()

    # Selon le response_format, content peut être du texte ou du JSON string
    content = data["choices"][0]["message"]["content"]
    if isinstance(content, str) and settings.RESPONSE_FORMAT == "json":
        try:
            content = json.loads(content)
            data["choices"][0]["message"]["content"] = content
        except json.JSONDecodeError:
            pass  # si l’API a renvoyé du texte malgré "json"

    return data
