"""Second pass: show Sonnet the lyrics + everything already found, ask only for what was missed.
Usage: python3 03b_sweep.py [--jobs 4] [--src mentions] [--out sweep] [song_id ...]"""
import json, subprocess, sys, time, re, importlib.util
from concurrent.futures import ThreadPoolExecutor
from common import *
spec = importlib.util.spec_from_file_location("ex", ROOT / "pipeline" / "03_extract.py"); ex = importlib.util.module_from_spec(spec); spec.loader.exec_module(ex)

SYSTEM = ex.SYSTEM + """

SWEEP MODE: a first annotator already produced the list below the lyrics. Your only job is to find references it MISSED: proper nouns in any category, slang place names, nicknames, brands, people, including any occurrence on a line the list does not cover. Re-read every line slowly. Do not repeat items already listed for the same line. Do not invent references that are not in the text: only count a proper noun or nickname actually written in the line, never an inference ("the President" is not a named person; "C4", "Glock" used generically as a weapon are kind weapon only if a make/model is named). If nothing was missed, reply {"mentions": []}."""

def run(song, srcdir, outdir):
    out = RAW / outdir / f"{song['id']}.json"
    if out.exists(): return "skip"
    lyr = jload(RAW / "lyrics" / f"{song['id']}.json")["lyrics"]
    if not lyr:
        jdump({"id": song["id"], "mentions": [], "note": "no lyrics"}, out); return "nolyrics"
    first = jload(RAW / srcdir / f"{song['id']}.json")["mentions"]
    found = "\n".join(f"line {m.get('line')}: {m.get('text')} -> {m.get('category')}: {m.get('name')}" for m in first) or "(nothing)"
    msg = ex.USER.format(title=song["title"], album=song.get("album_name") or "single", year=song.get("album_year") or song.get("year") or "?", lyrics=ex.numbered(lyr)) + "\n\nALREADY FOUND:\n" + found
    err = ""
    for attempt in range(3):
        r = None
        try:
            r = subprocess.run(["claude", "-p", "--model", "sonnet", "--system-prompt", SYSTEM, *ex.FLAGS], input=msg, capture_output=True, text=True, timeout=600, cwd=str(ROOT))
            res = json.loads(r.stdout)
            if res.get("is_error"): raise RuntimeError(res.get("result", "")[:300])
            data = json.loads(re.search(r"\{.*\}", res.get("result", ""), flags=re.S).group(0))
            bad = ex.fix_lines(data["mentions"], lyr.split("\n"))
            jdump({"id": song["id"], "cost_usd": res.get("total_cost_usd"), "unverified": bad, "mentions": data["mentions"]}, out)
            return f"+{len(data['mentions'])}" + (f" ({bad} unverified)" if bad else "")
        except Exception as e:
            out_txt = ((r.stdout or "") + (r.stderr or "")) if r else ""
            err = f"{type(e).__name__}: {str(e)[:200]} | {out_txt[-200:]}"
            if ex.RATE_RE.search(out_txt) or ex.RATE_RE.search(str(e)): return "RATE_LIMIT " + err
            time.sleep(10)
    return "FAIL " + err

if __name__ == "__main__":
    args = sys.argv[1:]
    def opt(n, d):
        if n in args: i = args.index(n); v = args[i + 1]; del args[i:i + 2]; return v
        return d
    jobs, src, outdir = int(opt("--jobs", "4")), opt("--src", "mentions"), opt("--out", "sweep")
    (RAW / outdir).mkdir(parents=True, exist_ok=True)
    songs = [s for s in jload(DATA / "songs.json") if (RAW / src / f"{s['id']}.json").exists() and not (RAW / outdir / f"{s['id']}.json").exists()]
    if args: songs = [s for s in songs if str(s["id"]) in args]
    print(len(songs), "songs to sweep", flush=True)
    stop = False
    with ThreadPoolExecutor(jobs) as pool:
        for s, r in zip(songs, pool.map(lambda s: "skipped" if stop else run(s, src, outdir), songs)):
            print(s["id"], s["title"][:40], "->", r, flush=True)
            if r.startswith("RATE_LIMIT"): stop = True
    print("batch done", flush=True)
