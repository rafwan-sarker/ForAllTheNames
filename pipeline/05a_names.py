"""Build data/name_overrides.json: {"category|Name": "category|Canonical"}.
1) brand make/model fold: "Rolls-Royce Phantom" -> "Rolls-Royce" when the parent brand also appears (the lyric text keeps the model).
2) manual merges below (spelling variants, wrong category). Re-run after every extraction; 05_build applies it."""
import json, glob, re
from collections import Counter
from common import *

KEEP_SEPARATE = {"Maybach Music Group", "Young Money Cash Money Billionaires", "Cash Money Billionaires", "Young Money Records",
                 "Nike Air Force 1"}  # not a model of the shorter brand, or worth its own row
MANUAL = {
 # labels / crews
 "brand|Young Money Entertainment": "brand|Young Money", "brand|Young Money Records": "brand|Young Money",
 "brand|Young Money Cash Money Billionaires": "brand|YMCMB", "brand|Cash Money Billionaires": "brand|YMCMB",
 "brand|October's Very Own (OVO)": "brand|OVO", "brand|OVO (October's Very Own)": "brand|OVO", "brand|OVO Sound": "brand|OVO",
 "brand|Jumpman (Jordan Brand)": "brand|Jordan Brand", "brand|Air Jordan": "brand|Jordan Brand", "brand|Jordan": "brand|Jordan Brand",
 "brand|Swisher": "brand|Swisher Sweets", "brand|Dior": "brand|Christian Dior", "brand|Gulfstream G5": "brand|Gulfstream",
 "brand|Armand de Brignac Ace of Spades Rosé": "brand|Ace of Spades", "brand|Audi TT": "brand|Audi", "brand|Don Julio 1942": "brand|Don Julio", "brand|iPhone": "brand|Apple",
 # musicians
 "musician|PartyNextDoor": "musician|PARTYNEXTDOOR", "musician|Young Jeezy": "musician|Jeezy", "musician|Sean 'Diddy' Combs": "musician|Sean \"Diddy\" Combs",
 "musician|P Reign": "musician|P. Reign", "person|Vo": "musician|Voyce", "musician|Vert": "musician|Lil Uzi Vert",
 # people
 "person|Charlamagne Tha God": "person|Charlamagne tha God", "person|Jesus Christ": "person|Jesus", "person|Baka": "person|Baka Not Nice",
 "person|Saint Nick (Santa Claus)": "person|Santa Claus", "person|The Fresh Prince (Will Smith)": "person|Will Smith", "person|Will Smith (The Fresh Prince)": "person|Will Smith",
 "person|J Prince": "person|J. Prince", "person|Jas": "person|Jas Prince", "person|Winslow Family (Steve Urkel)": "person|Steve Urkel", "person|Kai": "person|Kai Cenat",
 "person|C.J. Gibson": "person|CJ", "musician|Will Smith": "person|Will Smith",
 "woman|Diana, Princess of Wales": "woman|Princess Diana", "woman|Aleshia": "woman|Alisha", "woman|'Resha": "woman|Resha", "woman|Diana": "woman|Princess Diana",
 # places
 "place|Turks and Caicos": "place|Turks and Caicos Islands", "place|East End Toronto": "place|East End, Toronto", "place|East End": "place|East End, Toronto",
 "place|West End": "place|West End, Toronto", "place|LIV": "place|LIV Nightclub", "place|Tao Nightclub": "place|TAO", "place|The Ritz-Carlton": "place|Ritz-Carlton",
 "place|Augusta": "place|Augusta, Georgia", "place|San Francisco Bay": "place|San Francisco Bay Area",
}

if __name__ == "__main__":
    c = Counter()
    for d in ("mentions", "sweep"):
        for f in (RAW / d).glob("*.json"):
            for m in jload(f)["mentions"]:
                if m.get("category") and m.get("name"): c[(m["category"], m["name"].strip())] += 1
    brands = {n for (cat, n) in c if cat == "brand"}
    out = {}
    for n in sorted(brands, key=len):
        if n in KEEP_SEPARATE: continue
        parents = [p for p in brands if p != n and n.startswith(p + " ") and p not in KEEP_SEPARATE]
        if parents:
            p = max(parents, key=len)
            out[f"brand|{n}"] = f"brand|{p}"
    out.update(MANUAL)
    # resolve chains (a -> b -> c)
    for k in list(out):
        seen = {k}
        while out[k] in out and out[k] not in seen: seen.add(out[k]); out[k] = out[out[k]]
    out = {k: v for k, v in out.items() if k != v}
    jdump(dict(sorted(out.items())), DATA / "name_overrides.json")
    auto = len(out) - len(MANUAL)
    print(len(out), "overrides (", auto, "auto brand folds )")
