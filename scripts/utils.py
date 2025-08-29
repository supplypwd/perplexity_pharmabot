import re
import unicodedata
from urllib.parse import urlparse
import textwrap

def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if not unicodedata.combining(c)
    )

def normalize_host(host: str) -> str:
    h = host.lower().strip()
    if h.startswith("www."): h = h[4:]
    return h

def is_allowed_host(host: str, allowlist: list[str]) -> bool:
    """Autorise aussi les sous-domaines."""
    h = normalize_host(host)
    allowed = {normalize_host(d) for d in allowlist}
    return any(h == d or h.endswith(f".{d}") for d in allowed)

def extract_host(url: str) -> str:
    return normalize_host(urlparse(url).netloc)



# -------------- Affichage standard --------------
def render_response(data, allowlist=None):
    """ Aperçu + sources """

    content = data["choices"][0]["message"]["content"]
    print("=== RÉPONSE (aperçu) ===")
    print(textwrap.shorten(content.replace("\n", " "), width=600, placeholder=" […]"))

    print("\n=== SOURCES ===")
    sr = data.get("search_results") or []

    # search_results structurés
    if sr:
        outside = []
        for i, s in enumerate(sr, start=1):
            url = s.get("url", "") or ""
            host = normalize_host(urlparse(url).netloc)
            title = (s.get("title") or host or "Source").strip()
            date = s.get("date", "")
            print(f"[{i}] {title}\n    {url}\n    {host} — {date}\n")
            if allowlist and not is_allowed_host(host, allowlist):
                outside.append(host)
        if outside:
            print("⚠️ Hors allowlist:", sorted(set(outside)))
        return
