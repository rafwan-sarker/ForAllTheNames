"""Fetch lyrics for every song in data/raw/songs/. Genius page (browser headers) first, lyrics.ovh fallback."""
import json, re, html, time, sys, urllib.parse
from common import *
from html.parser import HTMLParser
class _LyricsHTML(HTMLParser):
    """Collect text inside every div[data-lyrics-container=true], tracking nested depth; <br> -> newline."""
    def __init__(self):
        super().__init__(convert_charrefs=True); self.depth = 0; self.blocks = []; self.cur = []; self.skip = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if self.depth == 0 and tag == "div" and a.get("data-lyrics-container") == "true":
            self.depth = 1; self.cur = []; return
        if self.depth:
            if tag == "div": self.depth += 1
            if tag == "br": self.cur.append("\n")
            # header chips ("768 Contributors", translations) live in a div with data-exclude-from-selection
            if a.get("data-exclude-from-selection") == "true": self.skip = self.depth
    def handle_endtag(self, tag):
        if self.depth and tag == "div":
            if self.skip == self.depth: self.skip = 0
            self.depth -= 1
            if self.depth == 0: self.blocks.append("".join(self.cur)); self.cur = []
    def handle_data(self, data):
        if self.depth and not self.skip: self.cur.append(data)
def genius_lyrics(url):
    b = get(url, headers=WEB_H, tries=3)
    if not b: return None
    p = _LyricsHTML(); p.feed(b.decode("utf-8", "ignore"))
    if not p.blocks: return None
    txt = "\n".join(p.blocks)
    txt = re.sub(r"^\d+\s*Contributors?[^\n]*\n", "", txt.strip())
    txt = re.sub(r"[ \t]+\n", "\n", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
    return txt or None
def ovh_lyrics(title):
    t = re.sub(r"\s*\(.*?\)\s*", " ", title).strip()
    b = get("https://api.lyrics.ovh/v1/Drake/" + urllib.parse.quote(t), headers=API_H, tries=2, timeout=40)
    if not b: return None
    try: return json.loads(b).get("lyrics") or None
    except Exception: return None
if __name__ == "__main__":
    songs_p = DATA / "songs.json"  # filtered set from 02b when present, else everything fetched
    files = [RAW / "songs" / f"{s['id']}.json" for s in jload(songs_p)] if songs_p.exists() else sorted((RAW / "songs").glob("*.json"))
    only = set(sys.argv[1:])
    n = 0
    for f in files:
        if only and f.stem not in only: continue
        out = RAW / "lyrics" / f"{f.stem}.json"
        if out.exists(): continue
        s = jload(f)
        src, txt = "genius", None
        try: txt = genius_lyrics(s["url"])
        except Exception as e:
            print("genius err (will retry next run)", s["id"], e, flush=True); continue
        if not txt:
            src = "ovh"
            try: txt = ovh_lyrics(s["title"])
            except Exception as e: print("ovh err", s["id"], e, flush=True)
        if not txt: src = None; print("NO LYRICS", s["id"], s["title"], flush=True)
        jdump({"id": s["id"], "source": src, "lyrics": txt}, out)
        n += 1
        if n % 25 == 0: print(n, flush=True)
        time.sleep(0.8)
    print("finished", n)
