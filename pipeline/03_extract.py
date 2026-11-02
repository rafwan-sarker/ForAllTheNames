"""Extract mentions from each song via headless `claude -p` (Sonnet, on the plan).
Overhead trimmed: custom system prompt, no tools, no MCP, no settings (default overhead is ~110k tokens/call; this is ~1k).
Usage: python3 03_extract.py [--model sonnet] [--jobs 4] [--out mentions] [--limit N] [song_id ...]"""
import json, subprocess, sys, time, re
from concurrent.futures import ThreadPoolExecutor
from common import *

SYSTEM = """You annotate Drake song lyrics for a data project that counts every proper-noun reference in his songs. Reply with JSON only.

Categories:
- place: cities, countries, states/provinces, neighbourhoods, streets, highways, venues, clubs, restaurants, hotels, stores at a location, landmarks, schools, airports, islands, regions, bodies of water. Resolve slang: "the 6"/"6ix"/"the six" = Toronto; "the A" = Atlanta; "H-Town"/"the H" = Houston; "the Chi" = Chicago; "LA" = Los Angeles; "NY"/"the Big Apple" = New York City; "the States" = United States; "the UK" = United Kingdom; "the Bridle Path", "Yorkville", "Weston Road" etc. are Toronto places. Skip generic words ("the club", "the city", "downtown", "overseas", "the islands") unless they clearly name one specific place.
- athlete: any sports figure, and sports teams. Resolve nicknames ("Bron" = LeBron James, "KD" = Kevin Durant, "Steph" = Stephen Curry, "Kobe" = Kobe Bryant, "Mike"/"MJ" in a basketball sense = Michael Jordan).
- musician: rappers, singers, producers, DJs, bands. Resolve nicknames ("Ye" = Kanye West, "Weezy"/"Tunechi" = Lil Wayne, "Hov"/"Hova" = Jay-Z, "Dot" = Kendrick Lamar, "40" = Noah "40" Shebib).
- brand: companies and products: cars, fashion labels and designers, drinks and liquor, jewellers, watches, phones and tech, apps and social platforms, stores and restaurant chains, sports brands, record labels (kind "label"), named weapons (kind "weapon"). Only proper nouns: "rosé" or "champagne" alone are not brands; "Dom Pérignon", "Ace of Spades", "Hennessy" are.
- woman: a woman named in the lyric who is not referenced as a musician: exes, love interests, strippers, models, actresses, fictional women, first names ("Courtney from Hooters", "Jodie", "Becky"). A female musician referenced romantically (e.g. Rihanna as a love interest) is a woman; referenced for her music or career, a musician.
- person: anyone else named: actors, TV/film characters, politicians, businesspeople, streamers, historical figures, religious figures, Drake's friends/crew/family (Chubbs, Baka, Niko, his mom Sandi, his son Adonis).

Do NOT count:
- Drake himself or his aliases (Drake, Drizzy, Aubrey, Champagne Papi, 6 God, Heartbreak Drake, October's Very Own as his own crew name unless used as a brand/label).
- Section headers like [Verse 1: Drake] or [Chorus: 21 Savage]; producer tags and ad-libs unless they are the lyric itself.
- Song titles, album titles, or the words "God"/"Jesus" used as exclamations (count Jesus/God only when referenced as a figure, as person).

Output one object per OCCURRENCE (a chorus that repeats Houston three times = three objects, each with its own line):
{"text": exact words as they appear on that line, "category": "place|athlete|musician|brand|woman|person", "name": canonical full name, "kind": subtype, "line": line number, "speaker": "drake" if the section is Drake's or unattributed, "feature" if the section header names another artist}
For place, also: "country": the country it is in (English name, e.g. "United States", "Canada"), "query": a geocodable string like "Yonge Street, Toronto, Canada" or "Houston, Texas, United States".

kind values:
- place: city | country | state | neighbourhood | street | landmark | region | island | water
- athlete: nba | nfl | mlb | nhl | soccer | boxing | mma | tennis | golf | track | other_sport | nba_team | nfl_team | other_team
- musician: rapper | singer | producer | group | dj | other
- brand: car | fashion | drink | jewellery | watch | tech | app | retail | food | sports | label | weapon | aircraft | boat | other
- woman: ex | love_interest | celebrity | first_name | fictional | other
- person: actor | character | politician | business | streamer | athlete_adjacent | historical | religious | crew | family | other

Be exhaustive: niche references (a street, a restaurant, a backup point guard, a designer) are the point of this project. When a reference is ambiguous, include your best reading. Reply exactly: {"mentions": [...]}"""

RATE_RE = re.compile(r"usage limit|rate limit|rate_limit|\b429\b|limit reached|out of extra usage", re.I)

USER = 'Song: "{title}" ({album}, {year}). Lines are numbered.\n\n{lyrics}'
FLAGS = ["--tools", "", "--no-session-persistence", "--strict-mcp-config", "--disable-slash-commands", "--setting-sources", "", "--output-format", "json"]

def numbered(lyr):
    return "\n".join(f"{i+1}. {l}" if l.strip() else "" for i, l in enumerate(lyr.split("\n")))

def fix_lines(mentions, lines):
    """Make sure each mention's text is on its cited line; if not, move it to the nearest line that contains it."""
    norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    bad = 0
    for m in mentions:
        t = norm(m.get("text", ""))
        mm = re.match(r"\s*(\d+)", str(m.get("line") or "0")); ln = int(mm.group(1)) if mm else 0  # model may write "4-5"
        m["line"] = ln
        if t and 0 < ln <= len(lines) and t in norm(lines[ln - 1]): continue
        cands = [i + 1 for i, l in enumerate(lines) if t and t in norm(l)]
        if cands: m["line"] = min(cands, key=lambda i: abs(i - ln)); m["line_fixed"] = True
        else: m["unverified"] = True; bad += 1
    return bad

def run(song, model, outdir):
    out = RAW / outdir / f"{song['id']}.json"
    if out.exists(): return "skip"
    lyr = jload(RAW / "lyrics" / f"{song['id']}.json")["lyrics"]
    if not lyr:
        jdump({"id": song["id"], "model": None, "mentions": [], "note": "no lyrics"}, out)
        return "nolyrics"
    msg = USER.format(title=song["title"], album=song.get("album_name") or "single", year=song.get("album_year") or song.get("year") or "?", lyrics=numbered(lyr))
    err = ""
    for attempt in range(3):
        r = None
        try:
            r = subprocess.run(["claude", "-p", "--model", model, "--system-prompt", SYSTEM, *FLAGS], input=msg,
                               capture_output=True, text=True, timeout=600, cwd=str(ROOT))
            res = json.loads(r.stdout)
            if res.get("is_error"): raise RuntimeError(res.get("result", "")[:300])
            txt = res.get("result", "")
            data = json.loads(re.search(r"\{.*\}", txt, flags=re.S).group(0))
            assert isinstance(data.get("mentions"), list)
            bad = fix_lines(data["mentions"], lyr.split("\n"))
            u = res.get("usage", {})
            jdump({"id": song["id"], "model": model, "cost_usd": res.get("total_cost_usd"),
                   "tokens": {k: u.get(k) for k in ["input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"]},
                   "unverified": bad, "mentions": data["mentions"]}, out)
            return f"ok {len(data['mentions'])}" + (f" ({bad} unverified)" if bad else "")
        except Exception as e:
            out_txt = ((r.stdout or "") + (r.stderr or "")) if r else ""
            err = f"{type(e).__name__}: {str(e)[:200]} | {out_txt[-200:]}"
            if RATE_RE.search(out_txt) or RATE_RE.search(str(e)): return "RATE_LIMIT " + err
            time.sleep(10)
    return "FAIL " + err

if __name__ == "__main__":
    args = sys.argv[1:]
    def opt(name, default):
        if name in args: i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return v
        return default
    model, jobs, outdir, limit = opt("--model", "sonnet"), int(opt("--jobs", "4")), opt("--out", "mentions"), int(opt("--limit", "0"))
    (RAW / outdir).mkdir(parents=True, exist_ok=True)
    songs = jload(DATA / "songs.json")
    if args: songs = [s for s in songs if str(s["id"]) in args]
    songs = [s for s in songs if not (RAW / outdir / f"{s['id']}.json").exists() and (RAW / "lyrics" / f"{s['id']}.json").exists()]
    if limit: songs = songs[:limit]
    print(len(songs), "songs to do, model", model, "->", outdir, flush=True)
    stop = False
    def task(s):
        if stop: return "skipped (stopped)"
        return run(s, model, outdir)
    with ThreadPoolExecutor(jobs) as ex:
        for s, r in zip(songs, ex.map(task, songs)):
            print(s["id"], s["title"][:40], "->", r, flush=True)
            if r.startswith("RATE_LIMIT"): stop = True
    print("batch done", flush=True)
