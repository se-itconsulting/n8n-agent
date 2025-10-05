from fastapi import FastAPI, Request
import requests, re, json, html
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

app = FastAPI()

# ---------- HTTP ----------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/119.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9,de;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def fetch_html(url: str, timeout=(4, 6)) -> str:
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text

# ---------- Helpers ----------
def load_next_data(html_text: str) -> Optional[dict]:
    soup = BeautifulSoup(html_text, "html.parser")
    tag = soup.find("script", id="__NEXT_DATA__", type="application/json")
    if not tag or not tag.string:
        return None
    try:
        return json.loads(tag.string)
    except Exception:
        try:
            return json.loads(html.unescape(tag.string))
        except Exception:
            return None

def parse_track_detail(html_text: str) -> Dict[str, Any]:
    """Track-Seite → ID, Titel, Artist, URLs"""
    res = {"id": "", "artist": "", "title": "", "url_artist": "", "url_title": ""}

    data = load_next_data(html_text)
    artists, artist_links, title, url = [], [], "", ""

    # --- 1) JSON (__NEXT_DATA__) ---
    if data:
        def walk(node):
            if isinstance(node, dict):
                if "artists" in node and isinstance(node["artists"], list) and ("name" in node or "title" in node):
                    return node
                for v in node.values():
                    r = walk(v)
                    if r:
                        return r
            elif isinstance(node, list):
                for v in node:
                    r = walk(v)
                    if r:
                        return r
            return None

        track_obj = walk(data)
        if track_obj:
            title = (track_obj.get("name") or track_obj.get("title") or "").strip()
            for a in track_obj.get("artists", []):
                nm = (a.get("name") or a.get("title") or "").strip()
                if nm:
                    artists.append(nm)
                href = a.get("url") or a.get("absoluteUrl") or ""
                if href and not href.startswith("http"):
                    href = "https://www.beatport.com" + href
                if href:
                    artist_links.append(href)
            slug = track_obj.get("slug")
            tid = track_obj.get("id") or track_obj.get("trackId")
            url = track_obj.get("absoluteUrl") or track_obj.get("shareUrl") or ""
            if not url and slug and tid:
                url = f"https://www.beatport.com/track/{slug}/{tid}"
            res["id"] = str(tid or "")
            res["title"] = title
            res["artist"] = ", ".join(dict.fromkeys(artists))
            res["url_artist"] = artist_links[0] if artist_links else ""
            res["url_title"] = url

    # --- 2) DOM-Fallback (Artists-DIV etc.) ---
    if not res["artist"]:
        soup = BeautifulSoup(html_text, "html.parser")
        div = soup.find("div", class_=re.compile(r"Artists-styles__Items"))
        if div:
            a = div.find("a", href=re.compile("/artist/"))
            if a:
                res["artist"] = a.get_text(strip=True)
                href = a.get("href", "")
                if href and not href.startswith("http"):
                    href = "https://www.beatport.com" + href
                res["url_artist"] = href

    if not res["title"]:
        soup = BeautifulSoup(html_text, "html.parser")
        h1 = soup.find("h1")
        if h1:
            res["title"] = h1.get_text(strip=True)

    if not res["url_title"]:
        link = soup.find("link", rel="canonical")
        if link:
            res["url_title"] = link.get("href", "")

    if not res["id"] and res["url_title"]:
        m = re.search(r"/(\d+)$", res["url_title"])
        if m:
            res["id"] = m.group(1)

    return res


def extract_track_links(html_text: str) -> List[str]:
    """Alle Track-Links aus Chart-Seite extrahieren."""
    hrefs = re.findall(r'href="(/track/[a-z0-9\-]+/\d+)"', html_text, flags=re.I)
    out, seen = [], set()
    for h in hrefs:
        if h not in seen:
            seen.add(h)
            out.append("https://www.beatport.com" + h)
    return out[:100]

# ---------- Actions ----------
def act_beatport_top(params: dict) -> dict:
    genre = (params.get("genre") or "techno").lower()
    deep_limit = int(params.get("deep_limit", 20))
    if genre not in ("techno", "hard-techno"):
        return {"ok": False, "error": "invalid genre"}

    urls = {
        "techno": "https://www.beatport.com/genre/techno-peak-time-driving/6/top-100?per-page=100",
        "hard-techno": "https://www.beatport.com/genre/hard-techno/8/top-100?per-page=100",
    }

    try:
        html_chart = fetch_html(urls[genre])
        links = extract_track_links(html_chart)
        items = []
        for link in links[:deep_limit]:
            try:
                t_html = fetch_html(link, timeout=(3, 5))
                info = parse_track_detail(t_html)
                if not info["url_title"]:
                    info["url_title"] = link
                if not info["title"]:
                    info["title"] = link.split("/")[-2].replace("-", " ").title()
                items.append(info)
            except Exception:
                title = link.split("/")[-2].replace("-", " ").title()
                m = re.search(r"/(\d+)$", link)
                tid = m.group(1) if m else ""
                items.append({"id": tid, "artist": "", "title": title, "url_artist": "", "url_title": link})

        return {
            "ok": True,
            "source": "beatport",
            "genre": genre,
            "count": len(items),
            "items": items[:100],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

# ---------- API ----------
@app.get("/health")
def health():
    return {"status": "ok"}

ACTIONS = {"beatport_top": act_beatport_top}

@app.post("/execute")
async def execute(request: Request):
    payload = await request.json()
    action = payload.get("action")
    params = payload.get("params", {}) or {}
    if not action or action not in ACTIONS:
        return {
            "ok": False,
            "error": f"unknown action {action}, allowed: {list(ACTIONS.keys())}"
        }
    try:
        result = ACTIONS[action](params)
        return {"ok": True, "action": action, "result": result}
    except Exception as e:
        return {"ok": False, "error": str(e)}
