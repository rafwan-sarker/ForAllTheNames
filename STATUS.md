# Status

## Now
- 2026-11-02: LIVE at https://for-all-the-names.vercel.app (Vercel project rsarkerai-8352s-projects/for-all-the-names, deployed from web/ with `vercel deploy --prod`). Code on private repo rafwan-sarker/drizzy-world, branch feature/site-v1.

## Next
1. Raf: check on a real iPhone (Safari); merge feature/site-v1 into main.
2. Optional: feedback link (VITE_FEEDBACK_URL), own domain, map tiles with a key (CARTO/MapTiler) if traffic grows.
3. Data polish: ~250 unhighlighted quotes, ~40 city-level venue pins, long-tail duplicate names. Pipeline helper cleanup.

## Blockers
- none

## Decisions
- 2026-11-02: Project folder renamed drizzy-world -> ~/AI/forallthenames (Raf asked). GitHub repo name unchanged.
- 2026-11-02: Category tabs in Rock Salt (free lookalike of the IYRTITL lettering). The real recreation "With My Woes" is personal-use only, not used.
- 2026-11-02: Wordmark in Oswald 700, spaced caps, blue/red offset glow (ICEMAN promo look, Raf picked B); no subtitle.
- 2026-11-02: Places view rebuilt in drizzy.world's structure (Raf's call): By album / By place rail, overview column (tiles, year chart, top lists), map right; credit line to drizzy.world. Other categories: leaderboard with album covers. Logo: Raf's Starbucks selfie (web/public/logo.jpg, Raf chose it).
- 2026-11-02: Rankings use number of songs, not raw mentions (one chorus put Missy at #1). Women also includes women filed elsewhere (Nicki, Beyoncé, Serena...) via `05b_women.py` (one Sonnet call, 68 names).
- 2026-11-02: Redesign v2 (Raf: v1 read as AI slop, Bodoni lyrics hard to read): one screen. Map (places) or name cloud (other categories) on the left, ranked list / lyrics panel on the right, thin top bar (categories, album filter, search, features toggle). Dark, one sans font (Schibsted Grotesk), minimal copy. State in the URL (?c=&n=&p=).
- 2026-11-02: Non-place categories use bubble clusters (d3-hierarchy pack) grouped by kind (Raf picked over era swarm). Side panel has Names / Albums tabs; album filter shows a cover card. Logo: circular photo, default NWTS cover; drop a photo at web/public/logo.jpg to replace (Raf to choose; no scraped Drake photos).
- 2026-11-02: Site name "For All The Names" (Raf; pun on For All The Dogs). Folder renamed to forallthenames on 2026-11-02 (Raf's request).
- 2026-11-02: Added guest verses (Raf): features with >= 100k Genius views, Drake's own sections only, shown as "Guest Verses" with a site toggle so own-songs numbers stay comparable to drizzy.world.
- 2026-11-02: Extraction = Sonnet first pass + Sonnet sweep for misses + free chorus-repeat counter. `claude -p` with custom system prompt and no tools/MCP (overhead ~1k tokens/call instead of ~110k).
- 2026-11-02: Scope = Drake's own releases (primary artist on Genius), all lyrics on those songs incl. feature verses, tagged `speaker` so Drake-only counts are possible. Guest features on others' songs excluded.
- 2026-11-02: Categories = place, athlete (incl. teams), musician, brand, woman, person. Extraction by Sonnet through headless `claude -p` (on the plan, no API key), same as saved-reels.
- 2026-11-02: Lyrics from Genius pages (no token) with lyrics.ovh fallback; raw lyrics stay out of git, only mentioned lines ship in data.json.
- 2026-11-02: Stack = Vite + React + Leaflet (CARTO light tiles, like the original) + Recharts. No backend; one static data.json.
