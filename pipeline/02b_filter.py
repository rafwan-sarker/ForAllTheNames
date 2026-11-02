"""Pick the song set -> data/songs.json, data/albums.json.
Projects: every track on the official Genius tracklists (01b_tracklists.py), deluxe editions folded in.
Other Songs: Drake sole primary artist, has a release date, >= 5,000 Genius pageviews, not on any project,
and not a speech / skit / alternate version / remix / freestyle-cover. Manual include/exclude in data/song_overrides.json."""
import re
from collections import Counter
from common import *

MIN_PAGEVIEWS = 5000
X_TITLE = re.compile(
    r"\b(remix|live|snippet|leak|leaked|demo|instrumental|reference|acapella|a cappella|radio edit|extended|sped up|slowed|unreleased"
    r"|og version|original version|single version|full length|traduction|interview|speaks|statement|apology|comments on|tweets"
    r"|award|juno awards|espys|thank you letter|thank you note|editor.s note|new album titled|new verse|tracklist|mixed)\b"
    r"|^snl\b|\((original|dub|video|ready version|third-person narrative)\)|\bref\.|\*\s*$|\[mixed\]", re.I)
X_ALBUM = re.compile(r"(dj mix|ovo sound radio|tracklist|instrumental|heartbreak drake|demo disc)", re.I)

def slugify(name): return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

if __name__ == "__main__":
    ov_p = DATA / "song_overrides.json"
    ov = jload(ov_p) if ov_p.exists() else {"include": [], "exclude": []}
    tl = jload(RAW / "tracklists.json")
    stats = {s["id"]: s for s in jload(RAW / "genius_songs.json")}
    songs, on_project = [], set()

    def detail(i):
        p = RAW / "songs" / f"{i}.json"
        return jload(p) if p.exists() else None

    def rec(d, album, year):
        return {"id": d["id"], "title": d["title"], "url": d["url"], "art": d.get("song_art_image_url"),
                "album_name": album, "album_year": year, "year": (d.get("release_date_components") or {}).get("year"),
                "release_date": d.get("release_date"), "features": [a["name"] for a in d.get("featured_artists") or []],
                "primary": (d.get("primary_artist") or {}).get("name")}

    missing, placed = [], set()
    home = {int(k): v for k, v in ov.get("home_project", {}).items()}
    for proj in tl:
        for t in proj["tracks"]:
            on_project.add(t["id"])
            if t["id"] in ov["exclude"] or t.get("instrumental"): continue
            if t["id"] in home and home[t["id"]] != proj["name"]: continue
            if t["id"] in placed: print("WARN on two projects, add to home_project:", t["title"], proj["name"]); continue
            placed.add(t["id"])
            d = detail(t["id"])
            if not d: missing.append(t["id"]); continue
            songs.append(rec(d, proj["name"], proj["year"]))

    for i, s in stats.items():
        if i in on_project or i in ov["exclude"]: continue
        forced = i in ov["include"]
        if not forced:
            if s["primary_artist"]["id"] != 130 or s.get("lyrics_state") != "complete": continue
            if ((s.get("stats") or {}).get("pageviews") or 0) < MIN_PAGEVIEWS: continue
            if X_TITLE.search(s["title"]): continue
        d = detail(i)
        if not d: missing.append(i); continue
        if not forced:
            if not d.get("release_date") or d.get("instrumental"): continue
            if X_ALBUM.search((d.get("album") or {}).get("name", "") or ""): continue
        songs.append(rec(d, None, None))

    # guest verses (06_features.py): Drake's sections of popular songs he's featured on
    if (DATA / "features.json").exists():
        have = {r["id"] for r in songs}
        for f in jload(DATA / "features.json"):
            d = detail(f["id"])
            if d and f["id"] not in have and f["id"] not in ov["exclude"]:
                r = rec(d, "Guest Verses", None); r["guest"] = True; songs.append(r)

    # drop exact-title duplicates among Other Songs that already exist on a project
    proj_titles = {re.sub(r"[^a-z0-9]", "", s["title"].lower()) for s in songs if s["album_name"] and not s.get("guest")}
    songs = [s for s in songs if s["album_name"] or re.sub(r"[^a-z0-9]", "", s["title"].lower()) not in proj_titles]
    songs.sort(key=lambda r: (r["album_year"] or r["year"] or 0, r["album_name"] or "zzz", r["title"]))
    jdump(songs, DATA / "songs.json.tmp"); (DATA / "songs.json.tmp").replace(DATA / "songs.json")  # atomic: extraction may be reading it

    c = Counter(r["album_name"] or "Other Songs" for r in songs)
    albums = [{"id": slugify(p["name"]), "name": p["name"], "year": p["year"], "cover": p["cover"], "songCount": c.get(p["name"], 0)} for p in tl]
    albums.append({"id": "other", "name": "Other Songs", "year": None, "cover": None, "songCount": c.get("Other Songs", 0)})
    if c.get("Guest Verses"):
        albums.append({"id": "guest-verses", "name": "Guest Verses", "year": None, "cover": None, "songCount": c["Guest Verses"], "guest": True})
    jdump(albums, DATA / "albums.json")
    print(len(songs), "songs |", c.get("Other Songs", 0), "other |", c.get("Guest Verses", 0), "guest |", len(missing), "missing details", missing[:10])
