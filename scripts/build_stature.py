"""Phase 4: stature tiers -> data/stature.csv (every guest) and data/stature_review.csv (Ben's Job C sheet).

Tiers were graded by hand against the README rubric, from what the podcasts say about each guest plus the Wikidata
description; the working files are data/raw/stature/grades_*.txt ("index|name|tier|reason", index into sheet.txt).
data/stature_tier_overrides.csv holds later corrections (and Ben's Job C changes, once he returns them).
Stature score: tier 1 -> 0, 2 -> 25, 3 -> 50, 4 -> 75, 5 -> 100.
"""
import glob, re
import pandas as pd

sheet = {int(l.split("|")[0]): l.split("|")[1] for l in open("data/raw/stature/sheet.txt")}
grades = {}
for f in sorted(glob.glob("data/raw/stature/grades_*.txt")):
    for line in open(f):
        parts = line.rstrip("\n").split("|")
        i = int(parts[0])
        tier, reason = (parts[2], parts[3]) if len(parts) == 4 else (parts[1], parts[2])
        grades[sheet[i]] = (int(tier), reason)

# names merged or dropped after grading (see build_guests.py ALIASES / FIX)
alias = dict(l.strip().split(",", 1) for l in open("data/raw/stature/alias_fixes.txt") if l.strip())
for old, new in alias.items():
    g = grades.pop(old, None)
    if new != "DROP" and g and new not in grades:
        grades[new] = (g[0], re.sub(r"\s*\((name parsing artifact|duplicate name)[^)]*\)", "", g[1]))

ov = pd.read_csv("data/stature_tier_overrides.csv").fillna("")
for _, r in ov.iterrows():
    grades[r.guest_name] = (int(r.tier), r.reason)

gd = pd.read_csv("data/guest_data.csv").fillna("")
missing = [n for n in gd.guest_name if n not in grades]
if missing:
    raise SystemExit(f"{len(missing)} guests without a tier, e.g. {missing[:10]}")
gd["tier"] = gd.guest_name.map(lambda n: grades[n][0])
gd["reason"] = gd.guest_name.map(lambda n: grades[n][1])
gd["stature_score"] = (gd.tier - 1) * 25
out = gd[["guest_name", "known_for", "tier", "reason", "stature_score", "shows"]]
out.sort_values(["tier", "guest_name"], ascending=[False, True]).to_csv("data/stature.csv", index=False)

top = out[out.tier >= 4].sort_values(["tier", "guest_name"], ascending=[False, True])
sample = out[out.tier <= 3].sample(100, random_state=42).sort_values(["tier", "guest_name"], ascending=[False, True])
rev = pd.concat([top.assign(section="tier 4-5 (all)"), sample.assign(section="tiers 1-3 (random 100)")])
rev["ben_tier"] = ""
rev[["section", "guest_name", "known_for", "tier", "reason", "ben_tier"]].to_csv("data/stature_review.csv", index=False)
print(out.tier.value_counts().sort_index(ascending=False).to_string())
print("review rows:", len(rev), "(tier 4-5:", len(top), ")")
