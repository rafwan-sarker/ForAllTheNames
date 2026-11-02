import json, time, urllib.request, urllib.error, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW = DATA / "raw"
API_H = {"User-Agent": "curl/8.7.1", "Accept": "*/*"}
WEB_H = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}
def get(url, headers=API_H, tries=4, timeout=30, sleep=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 404: return None
            last = e
        except Exception as e:
            last = e
        time.sleep(sleep * (i + 1))
    raise last
def jload(p): return json.load(open(p))
def jdump(o, p): json.dump(o, open(p, "w"), indent=1, ensure_ascii=False)
