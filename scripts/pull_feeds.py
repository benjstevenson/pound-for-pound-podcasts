"""Phase 1: pull every episode from each show's RSS feed into data/raw/feed_episodes.csv."""
import csv, html, re, time
from datetime import datetime, timezone
import feedparser

UA = "Mozilla/5.0 (podcast-p4p research)"

def clean(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()

def date_of(e):
    t = e.get("published_parsed") or e.get("updated_parsed")
    return datetime(*t[:6], tzinfo=timezone.utc).strftime("%Y-%m-%d") if t else ""

rows = []
for f in csv.DictReader(open("data/feeds.csv")):
    d = feedparser.parse(f["feed_url"], agent=UA)
    for e in d.entries:
        rows.append({
            "show": f["show"],
            "date": date_of(e),
            "title": clean(e.get("title")),
            "description": max([clean(e.get("summary") or e.get("description"))]
                               + [clean(c.value) for c in e.get("content", [])], key=len),
            "link": e.get("link", ""),
            "episode_number": e.get("itunes_episode", ""),
            "episode_type": e.get("itunes_episodetype", ""),
            "duration": e.get("itunes_duration", ""),
            "source": "rss",
        })
    n = len(d.entries)
    dates = sorted(r["date"] for r in rows if r["show"] == f["show"] and r["date"])
    print(f"{f['show']:28} n={n:5}  {dates[0] if dates else ''} -> {dates[-1] if dates else ''}  bozo={d.bozo}")
    time.sleep(1)

with open("data/raw/feed_episodes.csv", "w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader(); w.writerows(rows)
print("total", len(rows))
