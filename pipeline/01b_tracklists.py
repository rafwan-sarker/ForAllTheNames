"""Official tracklists for every Drake project from Genius album API -> data/raw/tracklists.json.
Each entry: display name, year, list of Genius album ids folded in (deluxe/bonus editions)."""
import json, time
from common import *

PROJECTS = [  # (display name, year, [genius album ids])
 ("Room For Improvement", 2006, [2625]), ("Comeback Season", 2007, [2622]), ("So Far Gone", 2009, [2627]),
 ("Thank Me Later", 2010, [2630]), ("Young Sweet Jones 2", 2010, [348688]), ("Take Care", 2011, [10787]),
 ("Nothing Was The Same", 2013, [40475, 1652706]), ("If You're Reading This It's Too Late", 2015, [119674]),
 ("What A Time To Be Alive", 2015, [131405]), ("Views", 2016, [132506]), ("More Life", 2017, [286515]),
 ("Scary Hours", 2018, [391461]), ("Scorpion", 2018, [420582]), ("Care Package", 2019, [549691]),
 ("Dark Lane Demo Tapes", 2020, [630537]), ("Scary Hours 2", 2021, [742624]), ("Certified Lover Boy", 2021, [585647]),
 ("Honestly, Nevermind", 2022, [880669]), ("Her Loss", 2022, [966485]), ("For All The Dogs", 2023, [1052037, 918587]),
 ("100 GIGS", 2024, [1219137]), ("$ome $exy $ongs 4 U", 2025, [1225315]), ("ICEMAN", 2026, [1395699]),
 ("HABIBTI", 2026, [1651590, 1740739]), ("MAID OF HONOUR", 2026, [1650770]),
]

out = []
for name, year, ids in PROJECTS:
    tracks, cover = [], None
    for aid in ids:
        b = get(f"https://genius.com/api/albums/{aid}")
        if b is None: print("album 404, skipped:", aid); continue
        a = json.loads(b)["response"]["album"]
        cover = cover or a.get("cover_art_url")
        page = 1
        while page:
            r = json.loads(get(f"https://genius.com/api/albums/{aid}/tracks?per_page=50&page={page}") or b'{"response":{"tracks":[]}}')["response"]
            for t in r["tracks"]:
                s = t["song"]
                if s["id"] not in {x["id"] for x in tracks}:
                    tracks.append({"id": s["id"], "title": s["title"], "number": t.get("number"), "edition": aid,
                                   "primary": s["primary_artist"]["name"], "instrumental": s.get("instrumental"), "lyrics_state": s.get("lyrics_state")})
            page = r.get("next_page"); time.sleep(0.4)
    out.append({"name": name, "year": year, "genius_ids": ids, "cover": cover, "tracks": tracks})
    print(f"{len(tracks):3d} {name}", flush=True)
jdump(out, RAW / "tracklists.json")
print("total", sum(len(p["tracks"]) for p in out))
