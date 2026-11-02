"""Fetch Genius song detail (album, release date, features) for every song where Drake is primary artist."""
import json, time, sys
from common import *
songs = [s for s in jload(RAW / "genius_songs.json") if s["primary_artist"]["id"] == 130 and s["lyrics_state"] == "complete"]
# plus every track on an official project (joint albums credit e.g. PARTYNEXTDOOR as primary)
if (RAW / "tracklists.json").exists():
    have = {s["id"] for s in songs}
    songs += [{"id": t["id"], "title": t["title"]} for p in jload(RAW / "tracklists.json") for t in p["tracks"] if t["id"] not in have]
print(len(songs), "songs", flush=True)
done = 0
for s in songs:
    p = RAW / "songs" / f"{s['id']}.json"
    if p.exists(): continue
    b = get(f"https://genius.com/api/songs/{s['id']}")
    if b is None: print("404", s["id"], s["title"]); continue
    d = json.loads(b)["response"]["song"]
    keep = {k: d.get(k) for k in ["id","title","title_with_featured","full_title","url","path","release_date","release_date_components","song_art_image_url","primary_artist","featured_artists","album","lyrics_state","annotation_count","pyongs_count","stats","language","instrumental"]}
    jdump(keep, p); done += 1
    if done % 25 == 0: print(done, flush=True)
    time.sleep(0.45)
print("finished", done)
