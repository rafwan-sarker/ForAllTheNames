# drizzy-world (site name: For All The Names)

Every place, player, brand and person Drake has ever mentioned, mapped and counted.
Rebuild and extension of niko draca's drizzy.world (places only). Ours adds athletes, musicians, brands, women and other people.

## Run

Pipeline (Python 3, stdlib only, run from `pipeline/`, in order; each step is resumable and skips what exists):

    python3 01_song_details.py   # Genius internal API -> data/raw/songs/*.json (album, date, features). No token needed.
    python3 02b_filter.py        # pick Drake's own releases -> data/songs.json, data/albums.json
    python3 02_lyrics.py         # Genius lyric pages (browser UA), lyrics.ovh fallback -> data/raw/lyrics/
    python3 03_extract.py        # headless `claude -p` (Sonnet, on the plan) -> data/raw/mentions/   ~$0.09 plan-usage per song
    python3 04_geocode.py        # Nominatim, 1 req/s -> data/raw/geocode.json
    python3 05_build.py          # -> web/public/data.json

Web: `cd web && npm run dev` (Vite + React + Leaflet + Recharts). `npm run build` for `web/dist`.

## Check

`scripts/verify.sh` compiles the pipeline and builds the web app.

## Gotchas

- 2026-11-02: Genius API (`genius.com/api/...`) returns 403 to a browser User-Agent but accepts curl's; lyric pages are the reverse. See `pipeline/common.py`.
- 2026-11-02: Genius lyric containers nest divs; a regex to `</div>` truncates songs. Use the HTMLParser in `02_lyrics.py`.
- 2026-11-02: Python `-I` breaks `from common import *`; run pipeline scripts with plain `python3` from `pipeline/`.
- 2026-11-02: `data/raw/` is gitignored (lyrics are copyrighted). `web/public/data.json` is committed; it holds only the mentioned lines plus one line of context.
