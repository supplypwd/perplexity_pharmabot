# === Resolver CRAT (tag pages -> recherche -> index) ===

import re, unicodedata, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
import json, sys
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode


BASE = "https://www.lecrat.fr"
UA   = {"User-Agent":"Mozilla/5.0 (CRAT-fetch/1.1)"} #utile de lavoir ici et plus bas ?

# === Finding URL functions ===

# remplir avec la liste de bruno
ALIASES = {
}

def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    return unicodedata.normalize("NFKD", s).encode("ascii","ignore").decode()

def _slugify(s: str) -> str:
    s = _norm(s)
    s = re.sub(r"[^a-z0-9]+","-", s).strip("-")
    return s

def _get(url, **kw):
    r = requests.get(url, headers=UA, timeout=25, **kw)
    r.raise_for_status()
    return r

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
    for u,t in out:
        if u not in seen:
            seen.add(u); uniq.append((u,t))
    return uniq

def _page_text(url: str):
    try:
        return BeautifulSoup(_get(url).text, "lxml").get_text(" ", strip=True)
    except Exception:
        return ""

def _score(url: str, link_text: str, med_tokens, topic_token):
    t = _norm(link_text)
    score = 0
    # topic dans le lien/titre
    if topic_token in t:
        score += 3
    # molécule/marque dans le lien/titre
    if any(tok in t for tok in med_tokens):
        score += 2
    # bonus si le topic est devinable via l'URL
    if "grossesse" in url and topic_token == "grossesse":
        score += 2
    if "allait" in url and topic_token.startswith("allait"):
        score += 2
    # si score insuffisant, lire le corps
    if score < 4:
        body = _norm(_page_text(url))
        if topic_token in body:
            score += 2
        if any(tok in body for tok in med_tokens):
            score += 2
    return score

def _candidate_tags(med_name: str):
    base = [_norm(med_name)]
    base += ALIASES.get(_norm(med_name), [])
    # ajoute une variante sans accents/typos fréquentes (ex: alimémazine -> alimemazine)
    variants = set(base)
    for b in list(base):
        variants.add(_norm(b))
    # retourne slugs
    return [_slugify(v) for v in variants if v]


# ============================

def find_crat_url(med_name: str, topic: str):
    topic_norm = _norm(topic)
    topic_token = "allaitement" if topic_norm.startswith("allait") else "grossesse" if "grossess" in topic_norm else topic_norm

    # 1) TAG PAGES
    tried = []
    candidates = []
    for slug in _candidate_tags(med_name):
        tag_url = f"{BASE}/tag/{slug}/"
        tried.append(("tag", tag_url))
        try:
            html = _get(tag_url).text
            links = _pick_numeric_links(html)
            if links:
                candidates.extend(links)
        except requests.HTTPError as e:
            # 404 tag inexistant = normal
            continue
        except Exception:
            continue

    # 2) RECHERCHE HTML
    if not candidates:
        q_terms = [_norm(med_name)] + ALIASES.get(_norm(med_name), [])
        for q in q_terms:
            if not q: continue
            url = f"{BASE}/?s={quote_plus(q)}"
            tried.append(("search", url))
            try:
                html = _get(url).text
                links = _pick_numeric_links(html)
                if links:
                    candidates.extend(links)
            except Exception:
                continue

    # 3) INDEX (faible proba mais on tente)
    if not candidates:
        for idx in (f"{BASE}/medicaments-allaitement/", f"{BASE}/medicament-grossesse/"):
            tried.append(("index", idx))
            try:
                html = _get(idx).text
                links = _pick_numeric_links(html)
                if links:
                    candidates.extend(links)
            except Exception:
                continue

    # Rien trouvé
    if not candidates:
        print("Aucun candidat trouvé. URLs testées :", tried)
        return None

    # Scoring
    med_tokens = {_norm(med_name)}
    med_tokens.update(_norm(x) for x in ALIASES.get(_norm(med_name), []))
    med_tokens = [m for m in med_tokens if m]

    scored = sorted(
        candidates,
        key=lambda p: _score(p[0], p[1], med_tokens, topic_token),
        reverse=True
    )
    best_url, best_txt = scored[0]

    # Vérification “topic” forte via <title> si besoin
    title = ""
    try:
        soup = BeautifulSoup(_get(best_url).text, "lxml")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
    except Exception:
        pass

    if topic_token == "grossesse" and ("Grossesse" not in title and "grossess" not in _norm(title)):
        # essaie 2e meilleur si le 1er ne colle pas
        for url, txt in scored[1:4]:
            t = ""
            try:
                s = BeautifulSoup(_get(url).text, "lxml")
                t = s.title.get_text(" ", strip=True) if s.title else ""
            except Exception:
                continue
            if "Grossesse" in t or "grossess" in _norm(t):
                return url
    if topic_token.startswith("allait") and ("Allait" not in title and "allait" not in _norm(title)):
        for url, txt in scored[1:4]:
            t = ""
            try:
                s = BeautifulSoup(_get(url).text, "lxml")
                t = s.title.get_text(" ", strip=True) if s.title else ""
            except Exception:
                continue
            if "Allait" in t or "allait" in _norm(t):
                return url

    return best_url

# ============================






# =========================================================================================


# === Final Scraping function ===

UA = {"User-Agent": "Mozilla/5.0", "Accept-Language": "fr"}

def _clean(txt: str) -> str:
    # normalisation douce
    txt = re.sub(r"\s+", " ", (txt or "")).strip()
    # points-virgules et puces -> phrases
    txt = txt.replace("•", "-")
    return txt

def _first(el, sel):
    return el.select_one(sel) if el else None

# ============================

def fetch_crat_sections(url: str, use_print_fallback: bool = True) -> dict:
    """
    Récupère et extrait le contenu CRAT (grossesse/allaitement).
    Retourne un dict: {title, updated, etat, pratique, pdf_url, source_url}
    """
    def _get(url_):
        r = requests.get(url_, headers=UA, timeout=20)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")

    soup = None
    try:
        soup = _get(url)
    except Exception:
        if not use_print_fallback:
            raise

    # Fallback 'print' si besoin
    if soup is None or not soup.select_one("#accordion-1-c1, #accordion-2-c1"):
        try:
            soup = _get(url.rstrip("/") + "/?print=print")
        except Exception:
            soup = None

    if soup is None:
        return {
            "title": None, "updated": None, "etat": None, "pratique": None,
            "pdf_url": None, "source_url": url
        }

    # ---- Titre
    title = None
    for sel in [
        'h2[itemprop="name headline"]',
        "#grve-post-title span",
        "title",
    ]:
        node = _first(soup, sel)
        if node:
            title = _clean(node.get_text())
            break

    # ---- Date maj (ex: "Date de mise à jour : 13.07.21")
    updated = None
    # 1) balise time schema.org si dispo
    t = _first(soup, 'time[itemprop="dateModified"]')
    if t and t.has_attr("datetime"):
        updated = t["datetime"]
    if not updated:
        # 2) texte visible
        txt = soup.get_text(" ")
        m = re.search(r"Date de mise à jour\s*:\s*([0-9]{2}\.[0-9]{2}\.[0-9]{2,4})", txt, flags=re.I)
        if m:
            updated = m.group(1)

    # ---- Blocs accordéon
    etat = pratique = None

    etat_box = _first(soup, "#accordion-1-c1") or _first(soup, "div.accordion-content:has(> ul)")

    if etat_box:
        # concatène puces proprement
        lis = [li.get_text(" ", strip=True) for li in etat_box.select("li")]
        etat = _clean(" ".join(lis)) if lis else _clean(etat_box.get_text(" ", strip=True))

    prat_box = _first(soup, "#accordion-2-c1")
    if prat_box:
        lis = [li.get_text(" ", strip=True) for li in prat_box.select("li")]
        pratique = _clean(" ".join(lis)) if lis else _clean(prat_box.get_text(" ", strip=True))

    # ---- Lien PDF (utile pour audit)
    pdf_url = None
    a_pdf = soup.select_one('a.pdfprnt-button[href*="?print=pdf"]')
    if a_pdf and a_pdf.has_attr("href"):
        pdf_url = a_pdf["href"]

    return {
        "title": title,
        "updated": updated,
        "etat": etat,
        "pratique": pratique,
        "pdf_url": pdf_url,
        "source_url": url,
    }

# ============================
