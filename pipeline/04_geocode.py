"""Geocode every unique place via Nominatim (free, 1 req/s). Cache: data/raw/geocode.json.
Checks the result's country against the country Sonnet named; mismatches and misses are listed for data/geocode_overrides.json.
Usage: python3 04_geocode.py [mentions_dir sweep_dir]"""
import json, time, urllib.parse, sys
from collections import Counter
from common import *
H = {"User-Agent": "forallthenames/0.1 (rsarker.ai@gmail.com)", "Accept-Language": "en"}
dirs = sys.argv[1:] or ["mentions", "sweep"]
cache_p = RAW / "geocode.json"
cache = jload(cache_p) if cache_p.exists() else {}
ov = jload(DATA / "geocode_overrides.json") if (DATA / "geocode_overrides.json").exists() else {}
name_ov = jload(DATA / "name_overrides.json") if (DATA / "name_overrides.json").exists() else {}
places = {}
for d in dirs:
    for f in (RAW / d).glob("*.json"):
        for m in jload(f)["mentions"]:
            if m.get("category") != "place" or m.get("unverified"): continue
            nk = name_ov.get(f'place|{m["name"].strip()}', f'place|{m["name"].strip()}')
            if not nk.startswith("place|"): continue
            n = nk.split("|", 1)[1]
            p = places.setdefault(n, {"q": Counter(), "c": Counter(), "k": Counter()})
            p["q"][m.get("query") or n] += 1
            if m.get("country"): p["c"][m["country"]] += 1
            p["k"][m.get("kind") or "other"] += 1
print(len(places), "unique places")
ALIASES = {"united states of america": "united states", "usa": "united states", "uk": "united kingdom", "england": "united kingdom"}
canon = lambda c: ALIASES.get((c or "").lower(), (c or "").lower())
for name, p in places.items():
    if name in ov: continue
    q = p["q"].most_common(1)[0][0]
    if name in cache and cache[name].get("query") == q: continue
    hit = None
    for t in [q, name]:
        b = get("https://nominatim.openstreetmap.org/search?format=jsonv2&addressdetails=1&limit=1&q=" + urllib.parse.quote(t), headers=H, tries=2)
        time.sleep(1.1)
        r = json.loads(b or b"[]")
        if r: hit = r[0]; break
    want = p["c"].most_common(1)[0][0] if p["c"] else None
    got = (hit or {}).get("address", {}).get("country") if hit else None
    cache[name] = {"query": q, "lat": float(hit["lat"]) if hit else None, "lng": float(hit["lon"]) if hit else None,
                   "display": hit.get("display_name") if hit else None, "country": got, "expected_country": want,
                   "mismatch": bool(hit and want and canon(got) != canon(want))}
    print(("MISMATCH " if cache[name]["mismatch"] else "") + name, "->", (cache[name]["display"] or "MISS")[:80], flush=True)
    jdump(cache, cache_p)
review = {n: {"query": v["query"], "got": v.get("display"), "expected_country": v.get("expected_country")}
          for n, v in cache.items() if n in places and n not in ov
          and (v["lat"] is None or v.get("mismatch") or places[n]["k"].most_common(1)[0][0] in ("region", "water"))}
jdump(review, DATA / "geocode_review.json")
print("needs review:", len(review), "-> data/geocode_review.json")
