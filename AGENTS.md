# forallthenames (site: For All The Names)

Every place, player, brand and person Drake has ever mentioned, mapped and counted.
Rebuild and extension of niko draca's drizzy.world (places only). Ours adds athletes, musicians, brands, women and other people.

## Run

Pipeline (Python 3, stdlib only, run from `pipeline/`, in this order; each step is resumable and skips what exists):

    python3 01_song_details.py   # Genius API -> data/raw/songs/ (album, date, features). No token needed.
    python3 01b_tracklists.py    # official project tracklists -> data/raw/tracklists.json
    python3 01_song_details.py   # again: details for joint-album tracks found in the tracklists
    python3 02b_filter.py        # song set -> data/songs.json, data/albums.json (needs tracklists.json)
    python3 06_features.py       # guest verses: Drake's sections of popular features -> data/features.json
    python3 02b_filter.py        # again, to fold guest verses in
    python3 02_lyrics.py         # Genius lyric pages, lyrics.ovh fallback -> data/raw/lyrics/
    ./run_all.sh                 # PAID: Sonnet first pass (03_extract.py) + sweep (03b_sweep.py) in batches
    python3 04_geocode.py        # Nominatim, 1 req/s -> data/raw/geocode.json; review data/geocode_review.json
    python3 05a_names.py         # name merges -> data/name_overrides.json
    python3 05_build.py          # -> web/public/data.json (minified; only mentioned lines, no full lyrics)
    python3 05b_women.py         # PAID, one small call: women filed under other categories -> data/women_crosslist.json
    python3 05_build.py          # again, to apply the women cross-list

Web: `cd web && npm run dev` (Vite + React + Leaflet). `npm run build` for `web/dist`.

## Check

`scripts/verify.sh` compiles the pipeline and builds the web app.

## Gotchas

- 2026-11-02: Genius API (`genius.com/api/...`) returns 403 to a browser User-Agent but accepts curl's; lyric pages are the reverse. See `pipeline/common.py`.
- 2026-11-02: Genius lyric containers nest divs; a regex to `</div>` truncates songs. Use the HTMLParser in `02_lyrics.py`.
- 2026-11-02: Python `-I` breaks `from common import *`; run pipeline scripts with plain `python3` from `pipeline/`.
- 2026-11-02: `data/raw/` is gitignored (lyrics are copyrighted). `web/public/data.json` is committed; it holds only the mentioned lines.
