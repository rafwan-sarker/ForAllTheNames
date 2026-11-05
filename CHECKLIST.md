# Build checklist

Paid steps (Claude extraction) are marked $. Everything else is free.

## Prep (done 2026-11-02)
- [x] Discography: Genius artist songs + song details
- [x] Song set from official Genius tracklists (`01b_tracklists.py`, 25 projects, deluxe folded in) + Other Songs rule → 477 songs (drizzy.world: 504)
- [x] Lyrics for all 477 (476 Genius, 1 lyrics.ovh)
- [x] Prompt v2: rules for aliases, labels, weapons, nicknames, women vs musicians, `person` category kept
- [x] Per-call overhead cut from ~110k to ~1k tokens (custom system prompt, no tools/MCP/settings)
- [x] v2 pilot vs v1: v1 hallucinated (Red Sox, Harlem, Trump); v2 cleaner. Neither complete alone
- [x] Sweep pass (`03b_sweep.py`): second Sonnet look for misses; rule against inferred names
- [x] Chorus repeats counted exactly in `05_build.py` (copies onto identical lines only)
- [x] Geocoder checks country; regions/water/misses go to `data/geocode_review.json`
- [x] Map tiles: grayscale OSM (CARTO now needs a key)
- [x] Home page with all six categories
- [x] Guest verses: 133 popular songs where Drake is featured (>= 100k Genius views), Drake's sections only (`06_features.py`); 24 dropped with no marked Drake verse. Site toggle on/off
- [x] Songs on two projects counted once (`home_project` in `data/song_overrides.json`) → 606 songs total (473 own + 133 guest)

## Paid run ($, Sonnet) — `pipeline/run_all.sh`, log in `data/raw/run.log`
- [x] First pass + sweep for all 606 songs, 0 failures (2026-11-02, ~40 min)

## After
- [x] Name cleanup: `05a_names.py` → `data/name_overrides.json` (brand models fold into maker, spelling variants, Vo → Voyce)
- [x] Geocoded 467 places; 106 manual pins/reviews in `data/geocode_overrides.json`; Lovers Lake left off map
- [x] Built data.json: 5,393 mentions. Own-song places: 1,125 (all speakers, every repeat); Drake-only once-per-song 726 vs drizzy.world 676; 426 unique places vs 291; 52 countries vs 50
- [x] Fixed chorus-repeat bug (all-ad-lib lines matched each other); every mention's text verified on its line (0 failures)
- [x] Recall audit: capitalized words not captured across all lyrics; no systematic place/player/brand misses
- [ ] Hand spot-check ~10 random songs against lyrics
- [x] Redesign (late-night gold, ranking-first, project strip, ⌘K search, song pages); browser-checked home, category, map, entity, song, search, mobile (pre-redesign)
- [ ] Mobile pass on the new design
- [ ] `/code-review` in a fresh context
- [ ] GitHub repo `rafwan-sarker/ForAllTheNames` (public); Vercel deploy only if Raf says so
