"""One Sonnet call: which named musicians / athletes / people are women? -> data/women_crosslist.json
05_build copies their mentions into the Women category too (they stay in their own category)."""
import json, subprocess, re
from common import *
d = jload(ROOT / "web" / "public" / "data.json")
names = sorted({f'{m["category"]}|{m["name"]}' for m in d["mentions"] if m["category"] in ("musician", "athlete", "person")})
listing = "\n".join(n.split("|", 1)[1] + "  [" + n.split("|", 1)[0] + "]" for n in names)
system = "You classify names from Drake lyrics. Reply with JSON only."
msg = ("Below are names Drake mentions, each with a category. Return every one that refers to a woman or girl "
       "(female artists, athletes, actresses, models, politicians, characters, relatives, friends). Skip groups and bands unless all-female. "
       "Skip anything you are unsure about. Copy each name exactly as written, without the [category].\n"
       'Reply exactly: {"women": ["Name", ...]}\n\n' + listing)
r = subprocess.run(["claude", "-p", "--model", "sonnet", "--system-prompt", system, "--tools", "", "--no-session-persistence",
                    "--strict-mcp-config", "--disable-slash-commands", "--setting-sources", "", "--output-format", "json"],
                   input=msg, capture_output=True, text=True, timeout=600, cwd=str(ROOT))
res = json.loads(r.stdout)
women = set(json.loads(re.search(r"\{.*\}", res["result"], re.S).group(0))["women"])
keep = [n for n in names if n.split("|", 1)[1] in women]
jdump(keep, DATA / "women_crosslist.json")
print(len(names), "names checked,", len(keep), "women; cost", res.get("total_cost_usd"))
print(keep[:60])
