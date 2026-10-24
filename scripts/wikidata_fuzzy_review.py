"""Write data/raw/wikidata/review_fuzzy.txt: fuzzy-search hits (not exact-label candidates) worth a manual look."""
import json
import pandas as pd

fz = json.load(open("data/raw/wikidata/fuzzy.json"))
ex = json.load(open("data/raw/wikidata/candidates.json"))
manual = set(pd.read_csv("data/wikidata_manual_matches.csv").guest_name)
g = pd.read_csv("data/guests.csv").fillna("")
info = g.groupby("guest_name").agg(shows=("show", lambda s: "/".join(sorted(x.split()[0] for x in s))),
                                   role=("role", lambda s: max(s, key=len)), titles=("episode_titles", lambda s: " || ".join(s)))
lines, n = [], 0
for name, res in sorted(fz.items()):
    if name in manual: continue
    seen = {c["qid"] for c in ex.get(name, [])}
    hits = [c for c in res if c["qid"] not in seen and (c["article"] or c["sitelinks"] >= 2)]
    # the fuzzy hit must share the surname
    sur = name.split()[-1].lower() if name.split() else ""
    hits = [c for c in hits if sur and sur in c["label"].lower()]
    if not hits: continue
    n += 1
    i = info.loc[name]
    lines.append(f"## {name} [{i.shows}] {i.role[:70]} || {i.titles[:100]}")
    for c in sorted(hits, key=lambda c: -c["sitelinks"])[:8]:
        lines.append(f"   {c['qid']:<11} sl={c['sitelinks']:<3} {'A' if c['article'] else ' '} {c['label'][:30]:<30} {c['desc'][:60]}")
open("data/raw/wikidata/review_fuzzy.txt", "w").write("\n".join(lines) + "\n")
print(n, "guests with fuzzy hits to review")
