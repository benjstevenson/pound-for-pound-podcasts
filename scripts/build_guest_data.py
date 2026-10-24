"""Phase 3d: data/guest_data.csv (Wikidata match, Wikipedia article, X handle, 12-month pageviews per guest).

Inputs: data/raw/wikidata/matches.csv (automatic matches), data/wikidata_manual_matches.csv (hand-checked
QIDs, which win over automatic picks), data/raw/wikidata/manual_details.json (article / X handle / description for
the manual QIDs, fetched by SPARQL) and the monthly pageview files in data/raw/pageviews/.

Pageviews = sum of the 12 monthly en.wikipedia user-agent, all-access view counts for the matched article.
Guests with no match get blank fame data, not a guess.
"""
import glob, gzip, json, os, re, subprocess, sys
from urllib.parse import unquote
import pandas as pd

MONTHS = sorted(glob.glob("data/raw/pageviews/en_*.tsv.gz"))
if len(MONTHS) != 12:
    sys.exit(f"expected 12 monthly pageview files, found {len(MONTHS)}")

guests = pd.read_csv("data/guests.csv").fillna("")
auto = pd.read_csv("data/raw/wikidata/matches.csv").fillna("").set_index("guest_name")
manual = pd.read_csv("data/wikidata_manual_matches.csv").fillna("")
manual = manual.drop_duplicates("guest_name", keep="last").set_index("guest_name").qid.to_dict()
details = json.load(open("data/raw/wikidata/manual_details.json"))

rows = []
for name, g in guests.groupby("guest_name"):
    roles = [r for r in g.role if r]
    r = {"guest_name": name, "shows": "; ".join(sorted(g.show)), "n_shows": len(g), "appearances": int(g.appearances.sum()),
         "role_from_podcast": max(roles, key=len) if roles else ""}
    if name in manual:
        q = manual[name]
        if q in ("", "NONE"):
            r.update(match_method="manual_none", qid="", wd_description="", wikipedia_article="", x_handle_wikidata="")
        else:
            d = details[q]
            r.update(match_method="manual", qid=q, wd_description=d["desc"], wikipedia_article=d["article"],
                     x_handle_wikidata=d["x"])
    elif name in auto.index and auto.loc[name, "qid"]:
        a = auto.loc[name]
        r.update(match_method=a.match_method, qid=a.qid, wd_description=a.wd_description,
                 wikipedia_article=a.wikipedia_article, x_handle_wikidata=a.x_handle_wikidata)
    else:
        r.update(match_method="unmatched", qid="", wd_description="", wikipedia_article="", x_handle_wikidata="")
    rows.append(r)
df = pd.DataFrame(rows)
df["article_title"] = df.wikipedia_article.map(lambda u: unquote(u.rsplit("/wiki/", 1)[1]).replace(" ", "_") if u else "")

# 12-month pageviews: filter each monthly file to the titles we need (awk is far faster than Python here)
want = sorted(set(df.article_title) - {""})
open("data/raw/pageviews/wanted_titles.txt", "w").write("\n".join(want) + "\n")
views = {t: 0 for t in want}
months_seen = {t: 0 for t in want}
for f in MONTHS:
    out = subprocess.run(f"zcat {f} | awk -F'\\t' 'NR==FNR{{w[$1];next}} ($1 in w)' data/raw/pageviews/wanted_titles.txt -",
                         shell=True, capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        t, v = line.split("\t")
        views[t] += int(v); months_seen[t] += 1
    print(os.path.basename(f), "titles found:", len(out.splitlines()), flush=True)
df["pageviews_12m"] = df.article_title.map(lambda t: views.get(t, "") if t else "")
df["pageview_months"] = df.article_title.map(lambda t: months_seen.get(t, "") if t else "")
# known_for: the podcast's own description of the guest, else the Wikidata description
df["known_for"] = [r if r else d for r, d in zip(df.role_from_podcast, df.wd_description)]

cols = ["guest_name", "known_for", "qid", "wikipedia_article", "pageviews_12m", "pageview_months", "x_handle_wikidata",
        "wd_description", "match_method", "shows", "n_shows", "appearances"]
df[cols].sort_values("guest_name").to_csv("data/guest_data.csv", index=False)
print(df.match_method.value_counts().to_string())
print("with article:", (df.wikipedia_article != "").sum(), "| with pageviews > 0:",
      (pd.to_numeric(df.pageviews_12m, errors="coerce") > 0).sum())
