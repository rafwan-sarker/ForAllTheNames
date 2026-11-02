"""Guest verses: popular songs where Drake is featured (>= 100k Genius pageviews).
Fetches details + lyrics, keeps only sections whose header names Drake, writes:
  data/raw/lyrics_full/<id>.json (whole song), data/raw/lyrics/<id>.json (Drake's sections only), data/features.json (selected list).
02b_filter.py then adds them to songs.json as the project "Guest Verses"."""
import json, re, time, importlib.util
from common import *
spec = importlib.util.spec_from_file_location("ly", ROOT / "pipeline" / "02_lyrics.py"); ly = importlib.util.module_from_spec(spec); spec.loader.exec_module(ly)

MIN_PAGEVIEWS = 100_000
X = re.compile(r"\b(remix|live|snippet|leak|demo|instrumental|reference|mixed|edit|version|sped up|slowed)\b|\*|\[", re.I)
own = {s["id"] for s in jload(DATA / "songs.json") if s.get("album_name") != "Guest Verses"}
cands = []
for s in jload(RAW / "genius_songs.json"):
    if s["id"] in own or s["primary_artist"]["id"] == 130 or s.get("lyrics_state") != "complete": continue
    if X.search(s["title"]) or "kidz bop" in s["primary_artist"]["name"].lower(): continue
    if ((s.get("stats") or {}).get("pageviews") or 0) >= MIN_PAGEVIEWS: cands.append(s)
print(len(cands), "candidates", flush=True)

def drake_sections(lyr):
    out, keep = [], False
    for l in lyr.split("\n"):
        if l.startswith("[") and l.rstrip().endswith("]"):
            keep = bool(re.search(r"\bdrake\b", l, re.I))
        if keep: out.append(l)
    return "\n".join(out).strip()

(RAW / "lyrics_full").mkdir(exist_ok=True)
picked, none = [], []
for s in cands:
    i = s["id"]
    dp = RAW / "songs" / f"{i}.json"
    if not dp.exists():
        d = json.loads(get(f"https://genius.com/api/songs/{i}") or b'{"response":{"song":null}}')["response"]["song"]
        if d is None: print("404, skipped:", s["title"]); continue
        jdump({k: d.get(k) for k in ["id","title","title_with_featured","full_title","url","path","release_date","release_date_components","song_art_image_url","primary_artist","featured_artists","album","lyrics_state","annotation_count","pyongs_count","stats","language","instrumental"]}, dp)
        time.sleep(0.45)
    d = jload(dp)
    fp = RAW / "lyrics_full" / f"{i}.json"
    if not fp.exists():
        txt = ly.genius_lyrics(d["url"]); time.sleep(0.8)
        jdump({"id": i, "source": "genius" if txt else None, "lyrics": txt}, fp)
    full = jload(fp)["lyrics"] or ""
    mine = drake_sections(full)
    if len(mine) < 80: none.append(f'{d["title"]} — {d["primary_artist"]["name"]}'); continue
    jdump({"id": i, "source": "genius-drake-sections", "lyrics": mine}, RAW / "lyrics" / f"{i}.json")
    picked.append({"id": i, "title": d["title"], "primary": d["primary_artist"]["name"], "pageviews": (s.get("stats") or {}).get("pageviews"), "chars": len(mine)})
jdump(sorted(picked, key=lambda x: -(x["pageviews"] or 0)), DATA / "features.json")
print(len(picked), "with Drake sections;", len(none), "without:", none)
