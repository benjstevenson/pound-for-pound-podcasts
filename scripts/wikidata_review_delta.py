"""List guests whose Wikidata picture changed after adding "mul" labels, for manual review.

Covers: unmatched guests (not yet hand-checked) that gained candidates, and automatic picks that changed.
"""
import json
import pandas as pd

old_c = json.load(open("data/raw/wikidata/candidates_en_only.json"))
new_c = json.load(open("data/raw/wikidata/candidates.json"))
old_m = pd.read_csv("data/raw/wikidata/matches_en_only.csv").fillna("").set_index("guest_name")
new_m = pd.read_csv("data/raw/wikidata/matches.csv").fillna("").set_index("guest_name")
manual = set(pd.read_csv("data/wikidata_manual_matches.csv").guest_name)
g = pd.read_csv("data/guests.csv").fillna("")
info = g.groupby("guest_name").agg(shows=("show", lambda s: "/".join(sorted(x.split()[0] for x in s))),
                                   role=("role", lambda s: max(s, key=len)), titles=("episode_titles", lambda s: " || ".join(s)))
out = []
for name in new_m.index:
    if name in manual: continue
    oq = old_m.qid.get(name, "") if name in old_m.index else ""
    nq = new_m.loc[name, "qid"]
    gained = {c["qid"] for c in new_c.get(name, [])} - {c["qid"] for c in old_c.get(name, [])}
    if (oq != nq) or (not nq and gained):
        cands = sorted(new_c.get(name, []), key=lambda c: -c["sitelinks"])
        if not nq and not any(c["article"] or c["sitelinks"] >= 2 for c in cands): continue
        i = info.loc[name] if name in info.index else None
        out.append(f"## {name} [{i.shows if i is not None else ''}] {i.role[:70] if i is not None else ''} || "
                   f"{(i.titles[:90] if i is not None else '')}  ##old={oq} new={nq}")
        for c in cands[:12]:
            out.append(f"   {c['qid']:<11} sl={c['sitelinks']:<3} {'A' if c['article'] else ' '} {c['desc'][:70]}")
open("data/raw/wikidata/review_delta.txt", "w").write("\n".join(out) + "\n")
print(sum(1 for l in out if l.startswith("##")), "guests to review")
