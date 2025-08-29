import re
import unicodedata
from urllib.parse import urlparse

def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")

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

MG_RE = re.compile(r"(?:(\d+)\s*mg\b)|\bmg\b", re.I)
