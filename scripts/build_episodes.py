"""Phase 1: merge RSS episodes with YouTube-only uploads into data/episodes.csv.

YouTube rows are long (>= 15 min) uploads that could not be matched to any RSS episode
(see compare_youtube.py). Excluded: other series on the same channel and anything uploaded
before the podcast's first RSS episode (except TBPN, whose pre-RSS "Technology Brothers"
episodes are the same show). Duplicates of RSS episodes are harmless downstream because a
repeat guest counts once per show.
"""
import json, re
import pandas as pd

rss = pd.read_csv("data/raw/feed_episodes.csv", dtype=str).fillna("")
yt = pd.read_csv("data/raw/youtube_vs_rss.csv").fillna("")
det = json.load(open("data/raw/youtube_details.json"))

OTHER_SERIES = re.compile(r"Hustle Con|Exit Strategy|Pizza & 40s|Behind [Tt]he Hustle|founder @ |"
                          r"How to write emails that don't suck|Creating (a World-Class|High-Value) Content|"
                          r"Penny Hoarder|My First Million - February 19, 2020", re.I)
first = rss[rss.date != ""].groupby("show").date.min()

# YouTube blocks per-video metadata from this server for most videos, so upload dates are
# often missing. Channel listings are newest-first; anything listed below the oldest
# high-confidence title match (score >= 85) predates the podcast on that channel.
yt["pre_show"] = False
for show, g in yt.groupby("show", sort=False):
    conf = [i for i in g.index if g.at[i, "matched"] and g.at[i, "title_score"] >= 85]
    if conf:
        yt.loc[[i for i in g.index if i > max(conf)], "pre_show"] = True

rows, dropped = [], []
for _, r in yt[(yt.duration_min >= 15) & ~yt.matched].iterrows():
    d = det.get(r.yt_id, {})
    ud = d.get("upload_date", "")
    date = f"{ud[:4]}-{ud[4:6]}-{ud[6:]}" if re.fullmatch(r"\d{8}", ud) else ""
    reason = ""
    if OTHER_SERIES.search(r.yt_title):
        reason = "other series on channel"
    elif r.show != "TBPN" and ((date and date < first[r.show]) or (not date and r.pre_show)):
        reason = f"before podcast's first RSS episode ({first[r.show]})"
    rec = {"show": r.show, "date": date, "title": r.yt_title, "description": d.get("description", ""),
           "link": f"https://www.youtube.com/watch?v={r.yt_id}", "episode_number": "",
           "episode_type": "", "duration": str(int(round(r.duration_min * 60))), "source": "youtube"}
    (dropped if reason else rows).append({**rec, **({"drop_reason": reason} if reason else {})})

eps = pd.concat([rss, pd.DataFrame(rows)], ignore_index=True)
eps = eps.sort_values(["show", "date"], ascending=[True, False])
eps.insert(0, "episode_id", [f"{re.sub(r'[^a-z0-9]', '', s.lower())[:12]}-{i:05d}" for i, s in enumerate(eps.show)])
eps.to_csv("data/episodes.csv", index=False)
pd.DataFrame(dropped).to_csv("data/raw/youtube_dropped.csv", index=False)

order = pd.read_csv("data/shows.csv").show
summ = eps.groupby(["show", "source"]).size().unstack(fill_value=0).reindex(order)
summ["first"] = eps[eps.date != ""].groupby("show").date.min()
summ["last"] = eps[eps.date != ""].groupby("show").date.max()
print(summ.to_string())
print("total", len(eps), "| youtube kept", len(rows), "| youtube dropped", len(dropped))
