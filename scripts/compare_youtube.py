"""Phase 1: find long YouTube uploads with no matching RSS episode.

A YouTube video counts as already in RSS if any of:
  - fuzzy title match >= 75
  - >= 60% (and >= 2) of the capitalised name-like words in the YT title appear in one RSS episode's title+description
  - duration within 2 min of an RSS episode AND title match >= 50 AND >= 1/3 name overlap with that episode
"""
import csv, glob, os, re
import pandas as pd
from rapidfuzz import fuzz, process

rss = pd.read_csv("data/raw/feed_episodes.csv", dtype=str).fillna("")

STOP = set("""The A An And Of On In To For With From How Why What Who When Where Is Are Was Were Be Its It's This That
These Those Your You We I My Our His Her Their Inside Building Build Interview Full Episode Podcast Live CEO CTO Founder
AI US U.S. America American New Future Next Best World Billion Million Every Most Can Will Not No All About Into Has Have
Ep Part Why Here Here's Just Real Truth Secret Big Top One Two Three Biggest Lessons""".split())

def norm(t):
    t = t.lower()
    t = re.sub(r"\|\s*(lex fridman podcast|diet tbpn|jack neel|uncapped|my first million|lenny'?s podcast|how i write).*$", "", t)
    t = re.sub(r"(#|ep\.?|episode)\s*\d+", " ", t)
    return re.sub(r"[^a-z0-9 ]+", " ", t).strip()

def names(t):
    return {w.strip("'’\".,:;!?()|") for w in re.findall(r"\b[A-Z][\w'’.-]{2,}", t)} - STOP

def secs(d):
    d = str(d).strip()
    if not d: return None
    if ":" in d:
        s = 0
        for p in d.split(":"): s = s * 60 + float(p or 0)
        return s
    try: return float(d)
    except ValueError: return None

rows = []
for path in sorted(glob.glob("data/raw/youtube/*.tsv")):
    yt = pd.read_csv(path, sep="\t", header=None, names=["id", "duration", "title"],
                     dtype=str, quoting=csv.QUOTE_NONE).fillna("")
    key = os.path.basename(path)[:-4]
    show = next(s for s in rss.show.unique() if re.sub(r"[^A-Za-z0-9_-]", "", s.replace(" ", "_")) == key)
    sub = rss[rss.show == show]
    choices = {i: norm(t) for i, t in sub.title.items()}
    text = {i: (r.title + " " + r.description).lower() for i, r in sub.iterrows()}
    durs = {i: secs(d) for i, d in sub.duration.items()}
    for _, v in yt.iterrows():
        dur = float(v.duration) if v.duration not in ("", "NA") else 0
        m = process.extractOne(norm(v.title), choices, scorer=fuzz.token_set_ratio)
        nm = names(v.title)
        cov, cov_i, hits = 0, None, 0
        covs = {}
        for i, tx in text.items():
            h = sum(n.lower() in tx for n in nm)
            covs[i] = h / len(nm) if nm else 0
            if covs[i] > cov: cov, cov_i, hits = covs[i], i, h
        dur_hit = any(d and abs(d - dur) <= 120 and covs[i] >= 1 / 3
                      and fuzz.token_set_ratio(norm(v.title), choices[i]) >= 50
                      for i, d in durs.items()) if dur else False
        matched = (m and m[1] >= 75) or (cov >= 0.6 and hits >= 2) or dur_hit
        rows.append({"show": show, "yt_id": v.id, "duration_min": round(dur / 60, 1), "yt_title": v.title,
                     "title_score": round(m[1]) if m else 0, "name_cov": round(cov, 2),
                     "dur_hit": dur_hit, "matched": bool(matched),
                     "best_rss_title": sub.title[cov_i if cov >= 0.6 else m[2]] if m else "",
                     "rss_date": sub.date[cov_i if (cov >= 0.6 and hits >= 2) else m[2]] if (m and matched) else ""})

df = pd.DataFrame(rows)
df.to_csv("data/raw/youtube_vs_rss.csv", index=False)
long = df[df.duration_min >= 15]
for s, g in long.groupby("show"):
    print(f"{s:27} yt>=15min={len(g):4}  unmatched={(~g.matched).sum():4}")
