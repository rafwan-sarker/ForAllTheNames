"""Assemble web/public/data.json.
Merges first pass (mentions/) + sweep (sweep/), drops duplicates, then copies mentions onto repeated identical lines
(choruses/hooks) so repeats are counted exactly. Applies data/name_overrides.json (canonical merges) and geocodes."""
import re, datetime, sys, json
from collections import Counter
from common import *

MDIR = sys.argv[1] if len(sys.argv) > 1 else "mentions"
SDIR = sys.argv[2] if len(sys.argv) > 2 else "sweep"
CATS = ("place", "athlete", "musician", "brand", "woman", "person")
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
def line_key(l):
    k = norm(re.sub(r"\(.*?\)", "", l))  # ignore ad-libs in parentheses
    return k or norm(l)  # a line that is all ad-lib keeps its own text (never an empty key)

songs = jload(DATA / "songs.json"); albums = jload(DATA / "albums.json")
geo = jload(RAW / "geocode.json") if (RAW / "geocode.json").exists() else {}
geo_ov = jload(DATA / "geocode_overrides.json") if (DATA / "geocode_overrides.json").exists() else {}
name_ov = jload(DATA / "name_overrides.json") if (DATA / "name_overrides.json").exists() else {}
aid = {a["name"]: a["id"] for a in albums}
out_songs, out_m, places = [], [], {}
stats = Counter()
for s in songs:
    lp = RAW / "lyrics" / f"{s['id']}.json"
    if not lp.exists(): continue
    lines = (jload(lp)["lyrics"] or "").split("\n")
    out_songs.append({"id": s["id"], "title": s["title"], "album": aid.get(s["album_name"], "other"), "year": s["album_year"] or s["year"],
                      "url": s["url"], "art": s["art"], "features": s["features"], "primary": s.get("primary")})
    raw = []
    for d in (MDIR, SDIR):
        p = RAW / d / f"{s['id']}.json"
        if p.exists(): raw += [dict(m, _src=d) for m in jload(p)["mentions"]]
    ms, seen = [], set()
    for m in raw:  # first pass comes before sweep in `raw`
        if m.get("category") not in CATS or not m.get("name"): continue
        if m.get("unverified"): stats["dropped_unverified"] += 1; continue
        nk = name_ov.get(f'{m["category"]}|{m["name"].strip()}')
        if nk: m["category"], m["name"] = nk.split("|", 1)
        m["name"] = m["name"].strip()
        k = (int(m.get("line") or 0), m["category"], norm(m["name"]))
        if m["_src"] == SDIR and k in seen: continue  # sweep only adds what the first pass missed
        seen.add(k); ms.append(m); stats["from_" + m["_src"]] += 1
    # chorus repeats: copy onto identical lines that lack the mention
    by_key = {}
    for i, l in enumerate(lines):
        if l.strip() and not l.startswith("["): by_key.setdefault(line_key(l), []).append(i + 1)
    for m in list(ms):
        ln = int(m.get("line") or 0)
        if not (0 < ln <= len(lines)): continue
        key = line_key(lines[ln - 1])
        if not key: continue
        for other in by_key.get(key, []):
            k = (other, m["category"], norm(m["name"]))
            if k in seen: continue
            if norm(m.get("text", "")) not in norm(lines[other - 1]): continue  # the words must really be on that line
            seen.add(k); ms.append(dict(m, line=other, repeat=True)); stats["repeat_added"] += 1
    for m in ms:
        ln = int(m.get("line") or 0)
        lt = lines[ln - 1] if 0 < ln <= len(lines) else ""
        out_m.append({"song": s["id"], "category": m["category"], "name": m["name"], "kind": m.get("kind") or "other", "text": m.get("text", ""),
                      "line": ln, "lineText": lt, "speaker": "feature" if m.get("speaker") == "feature" else "drake"})
        if m["category"] == "place":
            p = places.setdefault(m["name"], {"kinds": Counter(), "countries": Counter(), "queries": Counter()})
            p["kinds"][m.get("kind") or "other"] += 1
            if m.get("country"): p["countries"][m["country"]] += 1
            if m.get("query"): p["queries"][m["query"]] += 1
out_places = {}
for name, p in places.items():
    g = geo_ov.get(name) or geo.get(name) or {}
    out_places[name] = {"name": name, "kind": p["kinds"].most_common(1)[0][0], "country": g.get("country") or (p["countries"].most_common(1) or [(None,)])[0][0],
                        "lat": g.get("lat"), "lng": g.get("lng")}
# women named in other categories (Rihanna as an artist, Serena as an athlete) also count under Women
cross = set(jload(DATA / "women_crosslist.json")) if (DATA / "women_crosslist.json").exists() else set()
have = {(m["song"], m["line"], m["name"]) for m in out_m if m["category"] == "woman"}
extra = [dict(m, category="woman", crossListed=True) for m in out_m if f'{m["category"]}|{m["name"]}' in cross and (m["song"], m["line"], m["name"]) not in have]
out_m += extra; stats["women_crosslisted"] = len(extra)

# tighten quotes: Sonnet sometimes quotes the whole line; highlight only the name or a short alias found on that line
aliases = {}
KNOWN = {  # well-known nicknames the highlighter may always look for
    ("place", "Toronto"): ["T-Dot", "T-dot", "T.O.", "T.O", "the 6ix", "the 6", "the Six", "6ix", "Toronto", "416"],
    ("place", "Houston"): ["H-Town", "Houston", "the H"], ("place", "Atlanta"): ["ATL", "the A", "Atlanta"],
    ("place", "Los Angeles"): ["L.A.", "LA", "Los Angeles"], ("place", "New York City"): ["New York", "NYC", "N.Y."],
    ("place", "Memphis"): ["Memphis"], ("place", "Miami"): ["Miami", "the 305", "305"],
}
for k, v in KNOWN.items(): aliases.setdefault(k, set()).update(v)
for m in out_m:
    t = m["text"].strip()
    if 0 < len(t) <= 25: aliases.setdefault((m["category"], m["name"]), set()).add(t)
tight = 0
for m in out_m:
    t, lt = m["text"].strip(), m["lineText"]
    if t and len(t) <= 3:  # tiny quote ("To", "6"): prefer a longer known alias that is really on the line ("T-Dot")
        for c in sorted(aliases.get((m["category"], m["name"]), set()), key=len, reverse=True):
            if len(c) <= len(t): break
            mm = re.search(r"(?<![A-Za-z0-9])" + re.escape(c) + r"(?![A-Za-z0-9])", lt, re.I)
            if mm: m["text"] = lt[mm.start():mm.end()]; tight += 1; break
        continue
    if len(t) <= 25 and t: continue
    cands = sorted(aliases.get((m["category"], m["name"]), set()) | {m["name"]} | {w for w in re.split(r"[\s,()]+", m["name"]) if len(w) >= 3}, key=len, reverse=True)
    for c in cands:
        mm = re.search(r"(?<![A-Za-z0-9])" + re.escape(c) + r"(?![A-Za-z0-9])", lt, re.I)
        if mm: m["text"] = lt[mm.start():mm.end()]; tight += 1; break
stats["quotes_tightened"] = tight
stats["quotes_still_long"] = sum(1 for m in out_m if len(m["text"]) > 25)
out_m.sort(key=lambda m: (m["song"], m["line"]))
data = {"albums": albums, "songs": out_songs, "mentions": out_m, "places": out_places, "built": datetime.date.today().isoformat()}
json.dump(data, open(ROOT / "web" / "public" / "data.json", "w"), ensure_ascii=False, separators=(",", ":"))  # minified
c = Counter(m["category"] for m in out_m)
print(len(out_songs), "songs,", len(out_m), "mentions:", dict(c), "| places", len(out_places), "geocoded", sum(1 for p in out_places.values() if p["lat"] is not None))
print(dict(stats))
