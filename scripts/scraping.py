import re, unicodedata, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
import json

BASE = "https://www.lecrat.fr"

# === Headers distincts ===
UA_RESOLVER = {"User-Agent": "Mozilla/5.0 (CRAT-fetch/1.1)"}
UA_FETCH    = {"User-Agent": "Mozilla/5.0", "Accept-Language": "fr"}


# ----------------------------
# Utils
# ----------------------------

def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    return unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()

def _slugify(s: str) -> str:
    s = _norm(s)
    s = re.sub(r"[^a-z0-9]+","-", s).strip("-")
    return s

def _get(url, headers, **kw):
    r = requests.get(url, headers=headers, timeout=25, **kw)
    r.raise_for_status()
    return r

# ----------------------------
# Resolver (trouver la bonne URL CRAT)
# ----------------------------

def _pick_numeric_links(html: str):
    soup = BeautifulSoup(html, "lxml")
    out = []
    for a in soup.select("a[href]"):
        href = urljoin(BASE, a["href"])
        if href.startswith(BASE) and re.search(r"/\d+/?$", href):
            text = a.get_text(" ", strip=True) or ""
            out.append((href, text))
    # dédoublonner
    seen, uniq = set(), []
    for u, t in out:
        if u not in seen:
            seen.add(u)
            uniq.append((u, t))
    return uniq

def find_crat_url(med_name: str, topic: str) -> str | None:
    """
    Trouve la meilleure URL CRAT pour un médicament et un topic ("grossesse" ou "allaitement").
    Il existe deux pages différentes selon le contexte, on choisit donc celle qui correspond.
    """
    candidates = []

    # --- 1) Recherche par TAG
    for slug in [_slugify(med_name)]:
        tag_url = f"{BASE}/tag/{slug}/"
        try:
            html = _get(tag_url, headers=UA_RESOLVER).text
            links = _pick_numeric_links(html)
            if links:
                candidates.extend(links)
        except Exception:
            continue

    # --- 2) Recherche plein texte si rien trouvé
    if not candidates:
        url = f"{BASE}/?s={quote_plus(_norm(med_name))}"
        try:
            html = _get(url, headers=UA_RESOLVER).text
            candidates.extend(_pick_numeric_links(html))
        except Exception:
            pass

    if not candidates:
        return None

    # --- 3) Filtrage par topic
    topic_norm = "grossess" if topic == "grossesse" else "allait"
    topic_candidates = [(u, t) for (u, t) in candidates if topic_norm in _norm(u + " " + t)]

    if topic_candidates:
        return topic_candidates[0][0]  # premier lien qui colle au topic

    # --- 4) Fallback : si aucune URL ne contient explicitement le topic, on renvoie le meilleur candidat brut
    return candidates[0][0]



# ----------------------------
# Fetcher (récupérer contenu CRAT)
# ----------------------------

def _clean(txt: str) -> str:
    txt = re.sub(r"\s+", " ", (txt or "")).strip()
    return txt.replace("•", "-")

def _first(el, sel):
    return el.select_one(sel) if el else None

def fetch_crat_sections(url: str, use_print_fallback: bool = True) -> dict:
    def _get_soup(url_):
        r = requests.get(url_, headers=UA_FETCH, timeout=20)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")

    soup = None
    try:
        soup = _get_soup(url)
    except Exception:
        if not use_print_fallback:
            raise

    if soup is None or not soup.select_one("#accordion-1-c1, #accordion-2-c1"):
        try:
            soup = _get_soup(url.rstrip("/") + "/?print=print")
        except Exception:
            soup = None

    if soup is None:
        return {"title": None, "etat": None, "pratique": None, "pdf_url": None, "source_url": url}

    title = None
    for sel in ['h2[itemprop="name headline"]', "#grve-post-title span", "title"]:
        node = _first(soup, sel)
        if node:
            title = _clean(node.get_text())
            break

    etat = pratique = None
    etat_box = _first(soup, "#accordion-1-c1")
    if etat_box:
        lis = [li.get_text(" ", strip=True) for li in etat_box.select("li")]
        etat = _clean(" ".join(lis)) if lis else _clean(etat_box.get_text(" ", strip=True))

    prat_box = _first(soup, "#accordion-2-c1")
    if prat_box:
        lis = [li.get_text(" ", strip=True) for li in prat_box.select("li")]
        pratique = _clean(" ".join(lis)) if lis else _clean(prat_box.get_text(" ", strip=True))

    pdf_url = None
    a_pdf = soup.select_one('a.pdfprnt-button[href*="?print=pdf"]')
    if a_pdf and a_pdf.has_attr("href"):
        pdf_url = a_pdf["href"]

    return {"title": title, "etat": etat, "pratique": pratique, "pdf_url": pdf_url, "source_url": url}


# ------------------------------------------------------------

# ==== EXEMPLES FETCH ====

# TEST_URL = "https://www.lecrat.fr/7691/"  # remplace par n'importe quelle URL CRAT individuelle
# data = fetch_crat_sections(TEST_URL)
# print("=== JSON ===")
# print(json.dumps(data, ensure_ascii=False, indent=2))



# ==== EXEMPLES FIND ====
# print(find_crat_url("Alimémazine", "allaitement"))   # attendu ~ https://www.lecrat.fr/7691/
# print(find_crat_url("Vogalene", "grossesse", synonyms=("Métopimazine","Metopimazine")))
